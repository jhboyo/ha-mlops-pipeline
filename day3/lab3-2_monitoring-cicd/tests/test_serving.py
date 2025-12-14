"""
Test cases for serving API module
"""

import pytest
import numpy as np

from src.serving.api import (
    ModelServer,
    PredictionRequest,
    PredictionResponse,
    HealthResponse,
    validate_input
)
from src.model.trainer import CaliforniaHousingModel


class TestValidateInput:
    """입력 검증 테스트"""

    def test_valid_input(self):
        """유효한 입력 테스트"""
        instances = [[8.3252, 41.0, 6.984, 1.023, 322.0, 2.555, 37.88, -122.23]]
        assert validate_input(instances) is True

    def test_valid_multiple_instances(self):
        """여러 샘플 입력 테스트"""
        instances = [
            [8.3252, 41.0, 6.984, 1.023, 322.0, 2.555, 37.88, -122.23],
            [5.1234, 30.0, 5.555, 0.999, 200.0, 1.234, 35.00, -120.00]
        ]
        assert validate_input(instances) is True

    def test_empty_input(self):
        """빈 입력 테스트"""
        assert validate_input([]) is False

    def test_wrong_feature_count(self):
        """잘못된 특성 수 테스트"""
        instances = [[1.0, 2.0, 3.0]]  # Only 3 features
        assert validate_input(instances) is False

    def test_non_numeric_values(self):
        """비숫자 값 테스트"""
        instances = [["a", "b", "c", "d", "e", "f", "g", "h"]]
        assert validate_input(instances) is False


class TestModelServer:
    """ModelServer 테스트"""

    @pytest.fixture
    def trained_model(self):
        """학습된 모델 fixture"""
        model = CaliforniaHousingModel(
            model_type="random_forest",
            model_params={"n_estimators": 10, "random_state": 42}
        )
        X_train, _, y_train, _ = model.load_data()
        model.train(X_train, y_train)
        return model

    def test_server_initialization(self):
        """서버 초기화 테스트"""
        server = ModelServer(model=None, model_version="v1.0")

        assert server.is_ready is False
        assert server.model_version == "v1.0"
        assert server.request_count == 0

    def test_server_with_model(self, trained_model):
        """모델이 있는 서버 테스트"""
        server = ModelServer(model=trained_model, model_version="v1.0")

        assert server.is_ready is True

    def test_health_check_no_model(self):
        """모델 없는 상태의 헬스 체크"""
        server = ModelServer(model=None)
        health = server.health_check()

        assert isinstance(health, HealthResponse)
        assert health.status == "not_ready"
        assert health.model_loaded is False

    def test_health_check_with_model(self, trained_model):
        """모델 있는 상태의 헬스 체크"""
        server = ModelServer(model=trained_model)
        health = server.health_check()

        assert health.status == "healthy"
        assert health.model_loaded is True

    def test_predict_success(self, trained_model):
        """예측 성공 테스트"""
        server = ModelServer(model=trained_model, model_version="v1.0")

        instances = [[8.3252, 41.0, 6.984, 1.023, 322.0, 2.555, 37.88, -122.23]]
        response = server.predict(instances)

        assert isinstance(response, PredictionResponse)
        assert len(response.predictions) == 1
        assert response.predictions[0] > 0
        assert response.model_version == "v1.0"
        assert response.latency_ms > 0

    def test_predict_multiple(self, trained_model):
        """여러 샘플 예측 테스트"""
        server = ModelServer(model=trained_model)

        instances = [
            [8.3252, 41.0, 6.984, 1.023, 322.0, 2.555, 37.88, -122.23],
            [5.1234, 30.0, 5.555, 0.999, 200.0, 1.234, 35.00, -120.00]
        ]
        response = server.predict(instances)

        assert len(response.predictions) == 2

    def test_predict_no_model(self):
        """모델 없이 예측 시 오류 테스트"""
        server = ModelServer(model=None)

        with pytest.raises(RuntimeError) as exc_info:
            server.predict([[1, 2, 3, 4, 5, 6, 7, 8]])

        assert "not loaded" in str(exc_info.value)

    def test_get_metrics(self, trained_model):
        """메트릭 조회 테스트"""
        server = ModelServer(model=trained_model)

        # 몇 개 요청 수행
        for _ in range(3):
            server.predict([[8.3252, 41.0, 6.984, 1.023, 322.0, 2.555, 37.88, -122.23]])

        metrics = server.get_metrics()

        assert metrics["request_count"] == 3
        assert metrics["error_count"] == 0
        assert metrics["error_rate"] == 0
        assert metrics["avg_latency_ms"] > 0
        assert metrics["model_loaded"] is True


class TestPredictionRequest:
    """PredictionRequest 모델 테스트"""

    def test_valid_request(self):
        """유효한 요청 테스트"""
        request = PredictionRequest(
            instances=[[8.3252, 41.0, 6.984, 1.023, 322.0, 2.555, 37.88, -122.23]]
        )

        assert len(request.instances) == 1
        assert len(request.instances[0]) == 8


class TestPredictionResponse:
    """PredictionResponse 모델 테스트"""

    def test_response_creation(self):
        """응답 생성 테스트"""
        response = PredictionResponse(
            predictions=[2.5, 3.0],
            model_version="v1.0",
            latency_ms=10.5
        )

        assert response.predictions == [2.5, 3.0]
        assert response.model_version == "v1.0"
        assert response.latency_ms == 10.5
        assert response.timestamp is not None
