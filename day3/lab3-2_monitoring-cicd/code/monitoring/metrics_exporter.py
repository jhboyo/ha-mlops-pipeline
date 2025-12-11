#!/usr/bin/env python3
"""
Lab 3-2: Custom Metrics Exporter
모델 성능 메트릭을 Prometheus 형식으로 노출합니다.

환경 변수:
  METRICS_PORT: 메트릭 서버 포트 (기본: 8000)
  UPDATE_INTERVAL: 메트릭 업데이트 주기 (기본: 15초)
  PROMETHEUS_URL: Prometheus 서버 URL (선택)
"""
import time
import random
import os
import logging
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Info, REGISTRY
import numpy as np

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 설정
METRICS_PORT = int(os.getenv('METRICS_PORT', '8000'))
UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', '15'))

# ============================================================
# 메트릭 생성 - 중복 방지
# ============================================================

def get_or_create_metric(metric_class, name, documentation, labelnames=None, **kwargs):
    """
    메트릭 가져오기 또는 생성 (중복 방지)
    컨테이너 재시작 시 메트릭 충돌을 방지합니다.
    """
    # 이미 존재하는지 확인
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name == name:
            logger.info(f"메트릭 '{name}' 재사용")
            return collector
    
    # 없으면 새로 생성
    try:
        if labelnames is not None:
            if kwargs:
                metric = metric_class(name, documentation, labelnames, **kwargs)
            else:
                metric = metric_class(name, documentation, labelnames)
        else:
            metric = metric_class(name, documentation, **kwargs)
        logger.info(f"메트릭 '{name}' 생성")
        return metric
    except ValueError as e:
        logger.warning(f"메트릭 '{name}' 생성 실패, 재시도: {e}")
        # 레지스트리에서 제거 후 재생성
        try:
            if name in REGISTRY._names_to_collectors:
                REGISTRY.unregister(REGISTRY._names_to_collectors[name])
        except:
            pass
        
        if labelnames is not None:
            if kwargs:
                metric = metric_class(name, documentation, labelnames, **kwargs)
            else:
                metric = metric_class(name, documentation, labelnames)
        else:
            metric = metric_class(name, documentation, **kwargs)
        logger.info(f"메트릭 '{name}' 재생성 완료")
        return metric

# ============================================================
# Prometheus Metrics 정의
# ============================================================

# Gauge: 증가/감소 가능한 메트릭
model_mae_score = get_or_create_metric(
    Gauge,
    'model_mae_score',
    'Current Mean Absolute Error of the model',
    ['model_name', 'version']
)

model_r2_score = get_or_create_metric(
    Gauge,
    'model_r2_score',
    'Current R² Score of the model',
    ['model_name', 'version']
)

model_accuracy_score = get_or_create_metric(
    Gauge,
    'model_accuracy_score',
    'Current accuracy score',
    ['model_name', 'version']
)

# Counter: 증가만 가능한 메트릭
model_prediction_total = get_or_create_metric(
    Counter,
    'model_prediction_total',
    'Total number of predictions',
    ['model_name', 'version', 'status']
)

model_prediction_errors = get_or_create_metric(
    Counter,
    'model_prediction_errors_total',
    'Total number of prediction errors',
    ['model_name', 'version', 'error_type']
)

# Histogram: 분포 측정 메트릭
model_prediction_latency = get_or_create_metric(
    Histogram,
    'model_prediction_latency',
    'Prediction latency in seconds',
    ['model_name', 'version'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0)
)

# Info: 정적 정보
model_info = get_or_create_metric(
    Info,
    'model_version_info',
    'Information about the model version'
)

# ============================================================
# 메트릭 시뮬레이션 함수
# ============================================================

def simulate_model_a_metrics():
    """Model A (v1.0) 메트릭 시뮬레이션"""
    # 성능 메트릭 (약간 낮은 성능)
    mae = 0.445 + random.gauss(0, 0.01)
    r2 = 0.798 + random.gauss(0, 0.005)
    accuracy = 0.78 + random.gauss(0, 0.01)
    
    model_mae_score.labels(model_name='california_housing', version='v1.0').set(mae)
    model_r2_score.labels(model_name='california_housing', version='v1.0').set(r2)
    model_accuracy_score.labels(model_name='california_housing', version='v1.0').set(accuracy)
    
    # 예측 수 (90% 성공률)
    if random.random() > 0.1:
        model_prediction_total.labels(model_name='california_housing', version='v1.0', status='success').inc()
    else:
        model_prediction_total.labels(model_name='california_housing', version='v1.0', status='error').inc()
        model_prediction_errors.labels(model_name='california_housing', version='v1.0', error_type='timeout').inc()
    
    # 레이턴시 (평균 50ms)
    latency = abs(random.gauss(0.05, 0.02))
    model_prediction_latency.labels(model_name='california_housing', version='v1.0').observe(latency)
    
    return mae, r2, accuracy, latency


def simulate_model_b_metrics():
    """Model B (v2.0) 메트릭 시뮬레이션"""
    # 성능 메트릭 (더 좋은 성능)
    mae = 0.362 + random.gauss(0, 0.008)
    r2 = 0.885 + random.gauss(0, 0.004)
    accuracy = 0.88 + random.gauss(0, 0.008)
    
    model_mae_score.labels(model_name='california_housing', version='v2.0').set(mae)
    model_r2_score.labels(model_name='california_housing', version='v2.0').set(r2)
    model_accuracy_score.labels(model_name='california_housing', version='v2.0').set(accuracy)
    
    # 예측 수 (95% 성공률)
    if random.random() > 0.05:
        model_prediction_total.labels(model_name='california_housing', version='v2.0', status='success').inc()
    else:
        model_prediction_total.labels(model_name='california_housing', version='v2.0', status='error').inc()
        model_prediction_errors.labels(model_name='california_housing', version='v2.0', error_type='validation_error').inc()
    
    # 레이턴시 (평균 40ms, 더 안정적)
    latency = abs(random.gauss(0.04, 0.01))
    model_prediction_latency.labels(model_name='california_housing', version='v2.0').observe(latency)
    
    return mae, r2, accuracy, latency


def update_model_info():
    """모델 정보 업데이트"""
    model_info.info({
        'model': 'california_housing',
        'framework': 'scikit-learn',
        'training_date': '2024-12-01',
        'features': '8',
        'algorithm': 'RandomForest'
    })


# ============================================================
# 메인 실행
# ============================================================

def main():
    """메트릭 Exporter 메인 함수"""
    logger.info("=" * 70)
    logger.info(" " * 20 + "Metrics Exporter 시작")
    logger.info("=" * 70)
    logger.info(f"포트: {METRICS_PORT}")
    logger.info(f"업데이트 주기: {UPDATE_INTERVAL}초")
    logger.info(f"Metrics Endpoint: http://localhost:{METRICS_PORT}/metrics")
    logger.info("=" * 70)
    
    # HTTP Server 시작
    try:
        start_http_server(METRICS_PORT)
        logger.info("✅ HTTP Server 시작 성공")
    except OSError as e:
        logger.error(f"❌ HTTP Server 시작 실패: {e}")
        logger.info("포트가 이미 사용 중일 수 있습니다. 계속 진행합니다...")
    
    # 모델 정보 설정
    update_model_info()
    logger.info("✅ 모델 정보 초기화 완료")
    
    # 메트릭 업데이트 루프
    logger.info(f"\n메트릭 시뮬레이션 시작 (업데이트 주기: {UPDATE_INTERVAL}초)")
    logger.info("Ctrl+C로 종료\n")
    
    iteration = 0
    try:
        while True:
            iteration += 1
            
            # Model A & B 메트릭 업데이트
            mae_a, r2_a, acc_a, lat_a = simulate_model_a_metrics()
            mae_b, r2_b, acc_b, lat_b = simulate_model_b_metrics()
            
            # 주기적으로 로그 출력
            if iteration % 4 == 0:  # 1분마다 (15초 * 4)
                logger.info(f"[Iteration {iteration}]")
                logger.info(f"  v1.0: MAE={mae_a:.4f}, R²={r2_a:.4f}, Latency={lat_a*1000:.1f}ms")
                logger.info(f"  v2.0: MAE={mae_b:.4f}, R²={r2_b:.4f}, Latency={lat_b*1000:.1f}ms")
            
            time.sleep(UPDATE_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("\n메트릭 Exporter 종료")
        logger.info(f"총 {iteration}회 업데이트 완료")


if __name__ == '__main__':
    main()
