"""
Test cases for monitoring module
"""

import pytest
import numpy as np

from src.monitoring.drift import (
    DriftDetector,
    DriftResult,
    DriftLevel,
    ModelMetrics,
    ModelMonitor,
    calculate_drift_score
)


class TestDriftDetector:
    """DriftDetector 테스트"""

    @pytest.fixture
    def reference_data(self):
        """기준 데이터 fixture"""
        np.random.seed(42)
        return np.random.randn(1000, 4)

    def test_detector_initialization(self):
        """감지기 초기화 테스트"""
        detector = DriftDetector(significance_level=0.05)

        assert detector.significance_level == 0.05
        assert detector.reference_data is None

    def test_set_reference(self, reference_data):
        """기준 데이터 설정 테스트"""
        detector = DriftDetector()
        detector.set_reference(reference_data)

        assert detector.reference_data is not None
        assert len(detector.feature_names) == 4

    def test_set_reference_with_names(self, reference_data):
        """특성 이름과 함께 기준 데이터 설정"""
        detector = DriftDetector()
        feature_names = ["A", "B", "C", "D"]
        detector.set_reference(reference_data, feature_names)

        assert detector.feature_names == feature_names

    def test_detect_no_drift(self, reference_data):
        """드리프트 없는 경우 테스트"""
        detector = DriftDetector()
        detector.set_reference(reference_data)

        # 같은 분포에서 샘플링
        np.random.seed(43)
        current_data = np.random.randn(500, 4)

        has_drift, results = detector.detect_drift(current_data)

        # 같은 분포에서 샘플링했으므로 드리프트가 적어야 함
        assert len(results) == 4
        assert all(isinstance(r, DriftResult) for r in results)

    def test_detect_drift(self, reference_data):
        """드리프트 있는 경우 테스트"""
        detector = DriftDetector()
        detector.set_reference(reference_data)

        # 다른 분포에서 샘플링 (평균 이동)
        np.random.seed(43)
        current_data = np.random.randn(500, 4) + 3  # 평균을 3만큼 이동

        has_drift, results = detector.detect_drift(current_data)

        assert has_drift is True
        assert any(r.drift_detected for r in results)

    def test_detect_without_reference(self):
        """기준 데이터 없이 감지 시 오류"""
        detector = DriftDetector()

        with pytest.raises(RuntimeError) as exc_info:
            detector.detect_drift(np.random.randn(100, 4))

        assert "Reference data not set" in str(exc_info.value)

    def test_feature_count_mismatch(self, reference_data):
        """특성 수 불일치 테스트"""
        detector = DriftDetector()
        detector.set_reference(reference_data)

        with pytest.raises(ValueError) as exc_info:
            detector.detect_drift(np.random.randn(100, 3))  # 3 features

        assert "Feature count mismatch" in str(exc_info.value)

    def test_get_drift_summary(self, reference_data):
        """드리프트 요약 테스트"""
        detector = DriftDetector()
        detector.set_reference(reference_data)

        np.random.seed(43)
        current_data = np.random.randn(500, 4) + 3

        _, results = detector.detect_drift(current_data)
        summary = detector.get_drift_summary(results)

        assert "total_features" in summary
        assert "drifted_features" in summary
        assert "drift_score" in summary
        assert "max_severity" in summary
        assert summary["total_features"] == 4


class TestDriftLevel:
    """DriftLevel 테스트"""

    def test_drift_levels(self):
        """드리프트 레벨 값 테스트"""
        assert DriftLevel.NONE.value == "none"
        assert DriftLevel.LOW.value == "low"
        assert DriftLevel.MEDIUM.value == "medium"
        assert DriftLevel.HIGH.value == "high"
        assert DriftLevel.CRITICAL.value == "critical"


class TestDriftResult:
    """DriftResult 테스트"""

    def test_result_to_dict(self):
        """결과를 딕셔너리로 변환 테스트"""
        result = DriftResult(
            feature_name="test_feature",
            drift_detected=True,
            p_value=0.001,
            statistic=0.5,
            drift_level=DriftLevel.HIGH
        )

        d = result.to_dict()

        assert d["feature_name"] == "test_feature"
        assert d["drift_detected"] is True
        assert d["p_value"] == 0.001
        assert d["drift_level"] == "high"


class TestModelMetrics:
    """ModelMetrics 테스트"""

    def test_metrics_creation(self):
        """메트릭 생성 테스트"""
        metrics = ModelMetrics(
            mae=0.35,
            mse=0.15,
            rmse=0.387,
            r2=0.85
        )

        assert metrics.mae == 0.35
        assert metrics.r2 == 0.85

    def test_metrics_to_dict(self):
        """메트릭 딕셔너리 변환 테스트"""
        metrics = ModelMetrics(mae=0.35, mse=0.15, rmse=0.387, r2=0.85)
        d = metrics.to_dict()

        assert d["mae"] == 0.35
        assert d["r2"] == 0.85


class TestModelMonitor:
    """ModelMonitor 테스트"""

    def test_monitor_initialization(self):
        """모니터 초기화 테스트"""
        monitor = ModelMonitor(mae_threshold=0.45, r2_threshold=0.75)

        assert monitor.mae_threshold == 0.45
        assert monitor.r2_threshold == 0.75
        assert len(monitor.metrics_history) == 0

    def test_record_metrics(self):
        """메트릭 기록 테스트"""
        monitor = ModelMonitor()
        metrics = ModelMetrics(mae=0.35, mse=0.15, rmse=0.387, r2=0.85)

        monitor.record_metrics(metrics)

        assert len(monitor.metrics_history) == 1

    def test_check_performance_healthy(self):
        """건강한 성능 확인 테스트"""
        monitor = ModelMonitor(mae_threshold=0.45, r2_threshold=0.75)
        metrics = ModelMetrics(mae=0.35, mse=0.15, rmse=0.387, r2=0.85)

        is_healthy, warnings = monitor.check_performance(metrics)

        assert is_healthy is True
        assert len(warnings) == 0

    def test_check_performance_mae_warning(self):
        """MAE 경고 테스트"""
        monitor = ModelMonitor(mae_threshold=0.45, r2_threshold=0.75)
        metrics = ModelMetrics(mae=0.50, mse=0.25, rmse=0.5, r2=0.80)

        is_healthy, warnings = monitor.check_performance(metrics)

        assert is_healthy is False
        assert len(warnings) >= 1
        assert any("MAE" in w for w in warnings)

    def test_check_performance_r2_warning(self):
        """R² 경고 테스트"""
        monitor = ModelMonitor(mae_threshold=0.45, r2_threshold=0.75)
        metrics = ModelMetrics(mae=0.35, mse=0.15, rmse=0.387, r2=0.65)

        is_healthy, warnings = monitor.check_performance(metrics)

        assert is_healthy is False
        assert any("R²" in w for w in warnings)

    def test_should_retrain(self):
        """재학습 필요 여부 테스트"""
        monitor = ModelMonitor(mae_threshold=0.45, r2_threshold=0.75)

        healthy_metrics = ModelMetrics(mae=0.35, mse=0.15, rmse=0.387, r2=0.85)
        unhealthy_metrics = ModelMetrics(mae=0.50, mse=0.25, rmse=0.5, r2=0.65)

        assert monitor.should_retrain(healthy_metrics) is False
        assert monitor.should_retrain(unhealthy_metrics) is True

    def test_get_statistics(self):
        """통계 조회 테스트"""
        monitor = ModelMonitor()

        # 여러 메트릭 기록
        for mae, r2 in [(0.35, 0.85), (0.38, 0.82), (0.40, 0.80)]:
            monitor.record_metrics(
                ModelMetrics(mae=mae, mse=mae**2, rmse=mae, r2=r2)
            )

        stats = monitor.get_statistics()

        assert stats["count"] == 3
        assert "mae" in stats
        assert "r2" in stats
        assert stats["mae"]["mean"] == pytest.approx(0.3767, rel=0.01)

    def test_get_statistics_empty(self):
        """빈 통계 조회 테스트"""
        monitor = ModelMonitor()
        stats = monitor.get_statistics()

        assert "message" in stats


class TestCalculateDriftScore:
    """calculate_drift_score 함수 테스트"""

    def test_no_drift_score(self):
        """드리프트 없는 경우 점수"""
        np.random.seed(42)
        reference = np.random.randn(1000, 4)

        np.random.seed(43)
        current = np.random.randn(500, 4)

        score = calculate_drift_score(reference, current)

        assert 0 <= score <= 1

    def test_high_drift_score(self):
        """높은 드리프트 점수"""
        np.random.seed(42)
        reference = np.random.randn(1000, 4)

        # 모든 특성에 큰 드리프트 추가
        current = np.random.randn(500, 4) + 5

        score = calculate_drift_score(reference, current)

        assert score > 0.5  # 대부분의 특성에서 드리프트 발생해야 함
