"""
Model Serving API Module

FastAPI 기반 모델 서빙 엔드포인트
"""

import os
import time
import logging
from typing import List, Optional
from datetime import datetime

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PredictionRequest(BaseModel):
    """예측 요청 스키마"""

    instances: List[List[float]] = Field(
        ...,
        description="Input features (list of 8 features per sample)",
        example=[[8.3252, 41.0, 6.984127, 1.023810, 322.0, 2.555556, 37.88, -122.23]]
    )


class PredictionResponse(BaseModel):
    """예측 응답 스키마"""

    predictions: List[float] = Field(
        ...,
        description="Predicted house prices"
    )
    model_version: str = Field(
        default="v1.0",
        description="Model version"
    )
    latency_ms: float = Field(
        ...,
        description="Inference latency in milliseconds"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Prediction timestamp"
    )


class HealthResponse(BaseModel):
    """헬스 체크 응답"""

    status: str = "healthy"
    model_loaded: bool = False
    version: str = "1.0.0"
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


class ModelServer:
    """모델 서버 클래스"""

    def __init__(self, model=None, model_version: str = "v1.0"):
        """
        모델 서버 초기화

        Args:
            model: 학습된 모델 인스턴스
            model_version: 모델 버전
        """
        self.model = model
        self.model_version = model_version
        self.request_count = 0
        self.error_count = 0
        self.total_latency = 0.0

    @property
    def is_ready(self) -> bool:
        """모델 로드 상태 확인"""
        return self.model is not None

    def predict(self, instances: List[List[float]]) -> PredictionResponse:
        """
        예측 수행

        Args:
            instances: 입력 특성 리스트

        Returns:
            예측 응답
        """
        if not self.is_ready:
            raise RuntimeError("Model is not loaded")

        start_time = time.time()

        try:
            X = np.array(instances)
            predictions = self.model.predict(X)
            latency_ms = (time.time() - start_time) * 1000

            self.request_count += 1
            self.total_latency += latency_ms

            return PredictionResponse(
                predictions=predictions.tolist(),
                model_version=self.model_version,
                latency_ms=round(latency_ms, 3)
            )

        except Exception as e:
            self.error_count += 1
            logger.error(f"Prediction error: {e}")
            raise

    def health_check(self) -> HealthResponse:
        """헬스 체크"""
        return HealthResponse(
            status="healthy" if self.is_ready else "not_ready",
            model_loaded=self.is_ready,
            version=self.model_version
        )

    def get_metrics(self) -> dict:
        """서버 메트릭 조회"""
        avg_latency = (
            self.total_latency / self.request_count
            if self.request_count > 0 else 0
        )
        error_rate = (
            self.error_count / (self.request_count + self.error_count)
            if (self.request_count + self.error_count) > 0 else 0
        )

        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": round(error_rate, 4),
            "avg_latency_ms": round(avg_latency, 3),
            "model_version": self.model_version,
            "model_loaded": self.is_ready
        }


def validate_input(instances: List[List[float]]) -> bool:
    """
    입력 데이터 검증

    Args:
        instances: 입력 데이터

    Returns:
        유효성 여부
    """
    if not instances:
        return False

    expected_features = 8  # California Housing 특성 수

    for instance in instances:
        if len(instance) != expected_features:
            logger.warning(
                f"Invalid feature count: expected {expected_features}, "
                f"got {len(instance)}"
            )
            return False

        if not all(isinstance(x, (int, float)) for x in instance):
            logger.warning("Non-numeric values in input")
            return False

    return True


def create_app(model=None, model_version: str = "v1.0"):
    """
    FastAPI 앱 생성 (FastAPI가 설치된 환경에서 사용)

    Args:
        model: 학습된 모델
        model_version: 모델 버전

    Returns:
        FastAPI 앱 인스턴스
    """
    try:
        from fastapi import FastAPI, HTTPException

        app = FastAPI(
            title="California Housing Model API",
            description="House price prediction API",
            version=model_version
        )

        server = ModelServer(model=model, model_version=model_version)

        @app.get("/health", response_model=HealthResponse)
        def health():
            return server.health_check()

        @app.get("/metrics")
        def metrics():
            return server.get_metrics()

        @app.post("/predict", response_model=PredictionResponse)
        def predict(request: PredictionRequest):
            if not validate_input(request.instances):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid input: expected 8 features per instance"
                )
            try:
                return server.predict(request.instances)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        return app

    except ImportError:
        logger.warning("FastAPI not installed. create_app() unavailable.")
        return None
