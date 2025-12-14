"""
Model Training and Inference Module

California Housing 데이터셋을 사용한 회귀 모델 학습 및 추론
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import joblib
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)


class CaliforniaHousingModel:
    """California Housing 가격 예측 모델"""

    SUPPORTED_MODELS = {
        "random_forest": RandomForestRegressor,
        "gradient_boosting": GradientBoostingRegressor,
        "linear_regression": LinearRegression,
    }

    FEATURE_NAMES = [
        "MedInc", "HouseAge", "AveRooms", "AveBedrms",
        "Population", "AveOccup", "Latitude", "Longitude"
    ]

    def __init__(
        self,
        model_type: str = "random_forest",
        model_params: Optional[Dict] = None
    ):
        """
        모델 초기화

        Args:
            model_type: 모델 유형 (random_forest, gradient_boosting, linear_regression)
            model_params: 모델 하이퍼파라미터
        """
        if model_type not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model type: {model_type}. "
                f"Supported: {list(self.SUPPORTED_MODELS.keys())}"
            )

        self.model_type = model_type
        self.model_params = model_params or self._get_default_params(model_type)
        self.model = None
        self.is_fitted = False
        self.metrics = {}

    def _get_default_params(self, model_type: str) -> Dict:
        """모델별 기본 하이퍼파라미터"""
        defaults = {
            "random_forest": {
                "n_estimators": 100,
                "max_depth": 10,
                "random_state": 42,
                "n_jobs": -1
            },
            "gradient_boosting": {
                "n_estimators": 100,
                "max_depth": 5,
                "learning_rate": 0.1,
                "random_state": 42
            },
            "linear_regression": {}
        }
        return defaults.get(model_type, {})

    def load_data(
        self,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        California Housing 데이터 로드 및 분할

        Args:
            test_size: 테스트 세트 비율
            random_state: 랜덤 시드

        Returns:
            X_train, X_test, y_train, y_test
        """
        data = fetch_california_housing()
        X_train, X_test, y_train, y_test = train_test_split(
            data.data, data.target,
            test_size=test_size,
            random_state=random_state
        )
        logger.info(f"Data loaded: train={len(X_train)}, test={len(X_test)}")
        return X_train, X_test, y_train, y_test

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        모델 학습

        Args:
            X_train: 학습 데이터 특성
            y_train: 학습 데이터 타겟
            X_val: 검증 데이터 특성 (선택)
            y_val: 검증 데이터 타겟 (선택)

        Returns:
            학습 메트릭
        """
        model_class = self.SUPPORTED_MODELS[self.model_type]
        self.model = model_class(**self.model_params)

        logger.info(f"Training {self.model_type} model...")
        self.model.fit(X_train, y_train)
        self.is_fitted = True

        # 학습 메트릭 계산
        train_pred = self.model.predict(X_train)
        self.metrics["train_mae"] = mean_absolute_error(y_train, train_pred)
        self.metrics["train_mse"] = mean_squared_error(y_train, train_pred)
        self.metrics["train_r2"] = r2_score(y_train, train_pred)

        # 검증 메트릭 계산 (제공된 경우)
        if X_val is not None and y_val is not None:
            val_pred = self.model.predict(X_val)
            self.metrics["val_mae"] = mean_absolute_error(y_val, val_pred)
            self.metrics["val_mse"] = mean_squared_error(y_val, val_pred)
            self.metrics["val_r2"] = r2_score(y_val, val_pred)

        logger.info(f"Training completed. MAE={self.metrics['train_mae']:.4f}")
        return self.metrics

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        예측 수행

        Args:
            X: 입력 특성 (n_samples, 8)

        Returns:
            예측값 배열
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Call train() first.")

        X = np.asarray(X)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        if X.shape[1] != len(self.FEATURE_NAMES):
            raise ValueError(
                f"Expected {len(self.FEATURE_NAMES)} features, got {X.shape[1]}"
            )

        return self.model.predict(X)

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, float]:
        """
        모델 평가

        Args:
            X_test: 테스트 특성
            y_test: 테스트 타겟

        Returns:
            평가 메트릭
        """
        predictions = self.predict(X_test)

        metrics = {
            "mae": mean_absolute_error(y_test, predictions),
            "mse": mean_squared_error(y_test, predictions),
            "rmse": np.sqrt(mean_squared_error(y_test, predictions)),
            "r2": r2_score(y_test, predictions)
        }

        logger.info(f"Evaluation: MAE={metrics['mae']:.4f}, R²={metrics['r2']:.4f}")
        return metrics

    def save(self, filepath: str) -> None:
        """모델 저장"""
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Cannot save.")

        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        joblib.dump({
            "model": self.model,
            "model_type": self.model_type,
            "model_params": self.model_params,
            "metrics": self.metrics
        }, filepath)
        logger.info(f"Model saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "CaliforniaHousingModel":
        """모델 로드"""
        data = joblib.load(filepath)

        instance = cls(
            model_type=data["model_type"],
            model_params=data["model_params"]
        )
        instance.model = data["model"]
        instance.metrics = data.get("metrics", {})
        instance.is_fitted = True

        logger.info(f"Model loaded from {filepath}")
        return instance


def train_model(
    model_type: str = "random_forest",
    test_size: float = 0.2,
    save_path: Optional[str] = None
) -> Tuple[CaliforniaHousingModel, Dict[str, float]]:
    """
    모델 학습 편의 함수

    Args:
        model_type: 모델 유형
        test_size: 테스트 세트 비율
        save_path: 모델 저장 경로 (선택)

    Returns:
        학습된 모델과 평가 메트릭
    """
    model = CaliforniaHousingModel(model_type=model_type)
    X_train, X_test, y_train, y_test = model.load_data(test_size=test_size)

    model.train(X_train, y_train, X_test, y_test)
    metrics = model.evaluate(X_test, y_test)

    if save_path:
        model.save(save_path)

    return model, metrics
