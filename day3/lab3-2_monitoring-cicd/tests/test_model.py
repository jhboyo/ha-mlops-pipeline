"""
Test cases for model training module
"""

import pytest
import numpy as np
import os
import tempfile

from src.model.trainer import CaliforniaHousingModel, train_model


class TestCaliforniaHousingModel:
    """CaliforniaHousingModel 테스트"""

    def test_model_initialization(self):
        """모델 초기화 테스트"""
        model = CaliforniaHousingModel(model_type="random_forest")

        assert model.model_type == "random_forest"
        assert model.is_fitted is False
        assert model.model is None

    def test_invalid_model_type(self):
        """잘못된 모델 유형 테스트"""
        with pytest.raises(ValueError) as exc_info:
            CaliforniaHousingModel(model_type="invalid_model")

        assert "Unsupported model type" in str(exc_info.value)

    def test_load_data(self):
        """데이터 로드 테스트"""
        model = CaliforniaHousingModel()
        X_train, X_test, y_train, y_test = model.load_data(test_size=0.2)

        assert X_train.shape[1] == 8  # 8 features
        assert len(X_train) > len(X_test)
        assert len(y_train) == len(X_train)
        assert len(y_test) == len(X_test)

    def test_train_random_forest(self):
        """Random Forest 학습 테스트"""
        model = CaliforniaHousingModel(
            model_type="random_forest",
            model_params={"n_estimators": 10, "random_state": 42}
        )
        X_train, X_test, y_train, y_test = model.load_data()

        metrics = model.train(X_train, y_train, X_test, y_test)

        assert model.is_fitted is True
        assert "train_mae" in metrics
        assert "train_r2" in metrics
        assert "val_mae" in metrics
        assert metrics["train_mae"] > 0
        assert metrics["train_r2"] > 0

    def test_train_linear_regression(self):
        """Linear Regression 학습 테스트"""
        model = CaliforniaHousingModel(model_type="linear_regression")
        X_train, X_test, y_train, y_test = model.load_data()

        metrics = model.train(X_train, y_train)

        assert model.is_fitted is True
        assert "train_mae" in metrics

    def test_predict(self):
        """예측 테스트"""
        model = CaliforniaHousingModel(
            model_type="random_forest",
            model_params={"n_estimators": 10, "random_state": 42}
        )
        X_train, X_test, y_train, y_test = model.load_data()
        model.train(X_train, y_train)

        predictions = model.predict(X_test[:5])

        assert len(predictions) == 5
        assert all(p > 0 for p in predictions)

    def test_predict_single_sample(self):
        """단일 샘플 예측 테스트"""
        model = CaliforniaHousingModel(
            model_type="random_forest",
            model_params={"n_estimators": 10, "random_state": 42}
        )
        X_train, _, y_train, _ = model.load_data()
        model.train(X_train, y_train)

        sample = [8.3252, 41.0, 6.984127, 1.023810, 322.0, 2.555556, 37.88, -122.23]
        prediction = model.predict(sample)

        assert len(prediction) == 1
        assert prediction[0] > 0

    def test_predict_without_training(self):
        """학습 없이 예측 시 오류 테스트"""
        model = CaliforniaHousingModel()

        with pytest.raises(RuntimeError) as exc_info:
            model.predict([[1, 2, 3, 4, 5, 6, 7, 8]])

        assert "not fitted" in str(exc_info.value)

    def test_predict_wrong_features(self):
        """잘못된 특성 수로 예측 시 오류 테스트"""
        model = CaliforniaHousingModel(
            model_type="random_forest",
            model_params={"n_estimators": 10, "random_state": 42}
        )
        X_train, _, y_train, _ = model.load_data()
        model.train(X_train, y_train)

        with pytest.raises(ValueError) as exc_info:
            model.predict([[1, 2, 3]])  # Only 3 features

        assert "Expected 8 features" in str(exc_info.value)

    def test_evaluate(self):
        """평가 테스트"""
        model = CaliforniaHousingModel(
            model_type="random_forest",
            model_params={"n_estimators": 10, "random_state": 42}
        )
        X_train, X_test, y_train, y_test = model.load_data()
        model.train(X_train, y_train)

        metrics = model.evaluate(X_test, y_test)

        assert "mae" in metrics
        assert "mse" in metrics
        assert "rmse" in metrics
        assert "r2" in metrics
        assert metrics["mae"] > 0
        assert 0 <= metrics["r2"] <= 1

    def test_save_and_load(self):
        """모델 저장 및 로드 테스트"""
        model = CaliforniaHousingModel(
            model_type="random_forest",
            model_params={"n_estimators": 10, "random_state": 42}
        )
        X_train, X_test, y_train, y_test = model.load_data()
        model.train(X_train, y_train)

        original_pred = model.predict(X_test[:5])

        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            filepath = f.name

        try:
            model.save(filepath)
            loaded_model = CaliforniaHousingModel.load(filepath)

            loaded_pred = loaded_model.predict(X_test[:5])

            np.testing.assert_array_almost_equal(original_pred, loaded_pred)
            assert loaded_model.model_type == model.model_type
        finally:
            os.unlink(filepath)

    def test_save_without_training(self):
        """학습 없이 저장 시 오류 테스트"""
        model = CaliforniaHousingModel()

        with pytest.raises(RuntimeError) as exc_info:
            model.save("test.joblib")

        assert "not fitted" in str(exc_info.value)


class TestTrainModel:
    """train_model 함수 테스트"""

    def test_train_model_function(self):
        """train_model 편의 함수 테스트"""
        model, metrics = train_model(model_type="random_forest")

        assert model.is_fitted is True
        assert "mae" in metrics
        assert "r2" in metrics
        assert metrics["mae"] < 1.0
        assert metrics["r2"] > 0.5

    def test_train_model_with_save(self):
        """모델 저장과 함께 학습 테스트"""
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            filepath = f.name

        try:
            model, metrics = train_model(
                model_type="linear_regression",
                save_path=filepath
            )

            assert os.path.exists(filepath)
            loaded = CaliforniaHousingModel.load(filepath)
            assert loaded.is_fitted is True
        finally:
            os.unlink(filepath)
