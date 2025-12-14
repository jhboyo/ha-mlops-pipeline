"""
Monitoring and Drift Detection Module

모델 성능 모니터링 및 데이터 드리프트 감지
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class DriftLevel(Enum):
    """드리프트 수준"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DriftResult:
    """드리프트 감지 결과"""
    feature_name: str
    drift_detected: bool
    p_value: float
    statistic: float
    drift_level: DriftLevel

    def to_dict(self) -> Dict:
        return {
            "feature_name": self.feature_name,
            "drift_detected": self.drift_detected,
            "p_value": round(self.p_value, 6),
            "statistic": round(self.statistic, 6),
            "drift_level": self.drift_level.value
        }


@dataclass
class ModelMetrics:
    """모델 성능 메트릭"""
    mae: float
    mse: float
    rmse: float
    r2: float
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "mae": round(self.mae, 4),
            "mse": round(self.mse, 4),
            "rmse": round(self.rmse, 4),
            "r2": round(self.r2, 4),
            "timestamp": self.timestamp
        }


class DriftDetector:
    """데이터 드리프트 감지기"""

    def __init__(
        self,
        significance_level: float = 0.05,
        method: str = "ks"
    ):
        """
        드리프트 감지기 초기화

        Args:
            significance_level: 유의 수준 (기본 0.05)
            method: 검정 방법 ('ks' - Kolmogorov-Smirnov)
        """
        self.significance_level = significance_level
        self.method = method
        self.reference_data = None
        self.feature_names = None

    def set_reference(
        self,
        data: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> None:
        """
        기준 데이터 설정

        Args:
            data: 기준 데이터 (n_samples, n_features)
            feature_names: 특성 이름 리스트
        """
        self.reference_data = np.asarray(data)
        self.feature_names = feature_names or [
            f"feature_{i}" for i in range(data.shape[1])
        ]
        logger.info(
            f"Reference data set: {data.shape[0]} samples, "
            f"{data.shape[1]} features"
        )

    def detect_drift(
        self,
        current_data: np.ndarray
    ) -> Tuple[bool, List[DriftResult]]:
        """
        드리프트 감지

        Args:
            current_data: 현재 데이터

        Returns:
            (전체 드리프트 여부, 특성별 결과 리스트)
        """
        if self.reference_data is None:
            raise RuntimeError("Reference data not set. Call set_reference() first.")

        current_data = np.asarray(current_data)

        if current_data.shape[1] != self.reference_data.shape[1]:
            raise ValueError(
                f"Feature count mismatch: reference={self.reference_data.shape[1]}, "
                f"current={current_data.shape[1]}"
            )

        results = []
        overall_drift = False

        for i, feature_name in enumerate(self.feature_names):
            ref_feature = self.reference_data[:, i]
            cur_feature = current_data[:, i]

            # KS Test
            statistic, p_value = stats.ks_2samp(ref_feature, cur_feature)

            drift_detected = p_value < self.significance_level
            drift_level = self._get_drift_level(p_value)

            if drift_detected:
                overall_drift = True

            results.append(DriftResult(
                feature_name=feature_name,
                drift_detected=drift_detected,
                p_value=p_value,
                statistic=statistic,
                drift_level=drift_level
            ))

        logger.info(
            f"Drift detection completed: "
            f"{sum(1 for r in results if r.drift_detected)}/{len(results)} "
            f"features drifted"
        )

        return overall_drift, results

    def _get_drift_level(self, p_value: float) -> DriftLevel:
        """p-value에 따른 드리프트 수준 결정"""
        if p_value >= 0.1:
            return DriftLevel.NONE
        elif p_value >= 0.05:
            return DriftLevel.LOW
        elif p_value >= 0.01:
            return DriftLevel.MEDIUM
        elif p_value >= 0.001:
            return DriftLevel.HIGH
        else:
            return DriftLevel.CRITICAL

    def get_drift_summary(
        self,
        results: List[DriftResult]
    ) -> Dict:
        """
        드리프트 요약 생성

        Args:
            results: 드리프트 감지 결과 리스트

        Returns:
            요약 딕셔너리
        """
        drifted_features = [r for r in results if r.drift_detected]
        drift_score = len(drifted_features) / len(results) if results else 0

        return {
            "total_features": len(results),
            "drifted_features": len(drifted_features),
            "drift_score": round(drift_score, 4),
            "drifted_feature_names": [r.feature_name for r in drifted_features],
            "max_severity": max(
                (r.drift_level.value for r in results),
                key=lambda x: ["none", "low", "medium", "high", "critical"].index(x),
                default="none"
            )
        }


class ModelMonitor:
    """모델 성능 모니터"""

    def __init__(
        self,
        mae_threshold: float = 0.45,
        r2_threshold: float = 0.75
    ):
        """
        모델 모니터 초기화

        Args:
            mae_threshold: MAE 임계값 (초과 시 경고)
            r2_threshold: R² 임계값 (미만 시 경고)
        """
        self.mae_threshold = mae_threshold
        self.r2_threshold = r2_threshold
        self.metrics_history: List[ModelMetrics] = []

    def record_metrics(self, metrics: ModelMetrics) -> None:
        """메트릭 기록"""
        self.metrics_history.append(metrics)
        logger.info(f"Metrics recorded: MAE={metrics.mae:.4f}, R²={metrics.r2:.4f}")

    def check_performance(
        self,
        metrics: ModelMetrics
    ) -> Tuple[bool, List[str]]:
        """
        성능 확인

        Args:
            metrics: 현재 메트릭

        Returns:
            (정상 여부, 경고 메시지 리스트)
        """
        warnings = []
        is_healthy = True

        if metrics.mae > self.mae_threshold:
            warnings.append(
                f"MAE ({metrics.mae:.4f}) exceeds threshold ({self.mae_threshold})"
            )
            is_healthy = False

        if metrics.r2 < self.r2_threshold:
            warnings.append(
                f"R² ({metrics.r2:.4f}) below threshold ({self.r2_threshold})"
            )
            is_healthy = False

        return is_healthy, warnings

    def should_retrain(self, metrics: ModelMetrics) -> bool:
        """
        재학습 필요 여부 판단

        Args:
            metrics: 현재 메트릭

        Returns:
            재학습 필요 여부
        """
        is_healthy, _ = self.check_performance(metrics)
        return not is_healthy

    def get_statistics(self) -> Dict:
        """기록된 메트릭 통계"""
        if not self.metrics_history:
            return {"message": "No metrics recorded"}

        mae_values = [m.mae for m in self.metrics_history]
        r2_values = [m.r2 for m in self.metrics_history]

        return {
            "count": len(self.metrics_history),
            "mae": {
                "mean": round(np.mean(mae_values), 4),
                "std": round(np.std(mae_values), 4),
                "min": round(min(mae_values), 4),
                "max": round(max(mae_values), 4)
            },
            "r2": {
                "mean": round(np.mean(r2_values), 4),
                "std": round(np.std(r2_values), 4),
                "min": round(min(r2_values), 4),
                "max": round(max(r2_values), 4)
            }
        }


def calculate_drift_score(
    reference: np.ndarray,
    current: np.ndarray
) -> float:
    """
    간단한 드리프트 점수 계산

    Args:
        reference: 기준 데이터
        current: 현재 데이터

    Returns:
        드리프트 점수 (0-1)
    """
    detector = DriftDetector()
    detector.set_reference(reference)

    _, results = detector.detect_drift(current)
    summary = detector.get_drift_summary(results)

    return summary["drift_score"]
