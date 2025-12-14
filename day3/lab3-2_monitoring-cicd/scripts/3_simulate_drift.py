#!/usr/bin/env python3
"""
Lab 3-2: Drift 시뮬레이션 스크립트

Metrics Exporter의 메트릭 값을 변경하여 Drift를 시뮬레이션합니다.
실제로는 ConfigMap을 업데이트하여 Exporter가 다른 값을 생성하게 합니다.

사용법:
    python scripts/3_simulate_drift.py --user user01 --drift-level high
    python scripts/3_simulate_drift.py --user user01 --reset
"""

import os
import sys
import argparse
import subprocess
import json
import yaml
import time
import requests

# 설정
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")

# Drift 레벨 정의
DRIFT_LEVELS = {
    "none": {"mae_multiplier": 1.0, "r2_multiplier": 1.0},
    "low": {"mae_multiplier": 1.1, "r2_multiplier": 0.95},
    "medium": {"mae_multiplier": 1.2, "r2_multiplier": 0.9},
    "high": {"mae_multiplier": 1.35, "r2_multiplier": 0.8}
}


def run_kubectl(args):
    """kubectl 명령 실행"""
    try:
        result = subprocess.run(
            ["kubectl"] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def query_prometheus(query):
    """Prometheus 쿼리"""
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                return data["data"]["result"]
    except:
        pass
    return []


def get_current_metrics(user_id):
    """현재 메트릭 조회"""
    mae = query_prometheus(f'model_mae_score{{user_id="{user_id}"}}')
    r2 = query_prometheus(f'model_r2_score{{user_id="{user_id}"}}')
    
    return {
        "mae": float(mae[0]["value"][1]) if mae else None,
        "r2": float(r2[0]["value"][1]) if r2 else None
    }


def update_metrics_exporter_config(user_id, drift_level):
    """
    Metrics Exporter ConfigMap 업데이트
    
    실제 환경에서는 ConfigMap의 환경 변수를 변경하여
    Metrics Exporter가 다른 값을 생성하도록 합니다.
    """
    namespace = f"kubeflow-{user_id}"
    user_num = user_id.replace("user", "")
    
    # Drift 설정
    drift = DRIFT_LEVELS.get(drift_level, DRIFT_LEVELS["none"])
    
    # 새 Python 스크립트 생성 (Drift 적용)
    script = f'''#!/usr/bin/env python3
import time
import random
import os
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Info

USER_ID = os.getenv("USER_ID", "{user_id}")
USER_NUM = os.getenv("USER_NUM", "{user_num}")
NAMESPACE = os.getenv("NAMESPACE", "{namespace}")

# Drift 설정
MAE_MULTIPLIER = {drift["mae_multiplier"]}
R2_MULTIPLIER = {drift["r2_multiplier"]}

model_mae_score = Gauge("model_mae_score", "Current MAE", ["model_name", "version", "user_id", "namespace"])
model_r2_score = Gauge("model_r2_score", "Current R2", ["model_name", "version", "user_id", "namespace"])
model_prediction_total = Counter("model_prediction_total", "Total predictions", ["model_name", "version", "user_id", "namespace", "status"])
model_prediction_latency = Histogram("model_prediction_latency", "Latency", ["model_name", "version", "user_id", "namespace"], buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0))
model_info = Info("model_version_info", "Model info")

def simulate_metrics():
    labels = {{"model_name": "california-housing", "version": "v1.0", "user_id": USER_ID, "namespace": NAMESPACE}}
    try:
        user_offset = int(USER_NUM) * 0.005
    except:
        user_offset = 0.01
    base_mae = (0.38 + user_offset) * MAE_MULTIPLIER + random.gauss(0, 0.02)
    base_r2 = (0.85 - user_offset) * R2_MULTIPLIER + random.gauss(0, 0.03)
    model_mae_score.labels(**labels).set(max(0.30, min(0.60, base_mae)))
    model_r2_score.labels(**labels).set(max(0.60, min(0.95, base_r2)))
    model_prediction_total.labels(**labels, status="success").inc(random.randint(1, 5))
    if random.random() < 0.02:
        model_prediction_total.labels(**labels, status="error").inc()
    model_prediction_latency.labels(**labels).observe(random.expovariate(20))

def main():
    print(f"Metrics Exporter for {{USER_ID}} (Drift Level: {drift_level})")
    model_info.info({{"user_id": USER_ID, "namespace": NAMESPACE, "model_name": "california-housing", "drift_level": "{drift_level}"}})
    start_http_server(8000)
    print(f"Server started on port 8000")
    while True:
        simulate_metrics()
        time.sleep(1.0)

if __name__ == "__main__":
    main()
'''
    
    # ConfigMap YAML 생성
    configmap = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": "metrics-exporter-script",
            "namespace": namespace,
            "labels": {
                "app": "metrics-exporter",
                "user_id": user_id,
                "drift_level": drift_level
            }
        },
        "data": {
            "metrics_exporter.py": script
        }
    }
    
    # kubectl apply
    yaml_str = yaml.dump(configmap)
    success, stdout, stderr = run_kubectl(["apply", "-f", "-"])
    
    # stdin으로 YAML 전달
    result = subprocess.run(
        ["kubectl", "apply", "-f", "-"],
        input=yaml_str,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    return result.returncode == 0, result.stdout, result.stderr


def restart_metrics_exporter(user_id):
    """Metrics Exporter Pod 재시작"""
    namespace = f"kubeflow-{user_id}"
    success, stdout, stderr = run_kubectl([
        "rollout", "restart", "deployment/metrics-exporter",
        "-n", namespace
    ])
    return success


def main():
    parser = argparse.ArgumentParser(description="Drift 시뮬레이션")
    parser.add_argument("--user", required=True, help="사용자 ID (예: user01)")
    parser.add_argument("--drift-level", choices=["none", "low", "medium", "high"], default="medium", help="Drift 레벨")
    parser.add_argument("--reset", action="store_true", help="Drift 제거 (정상 상태로 복원)")
    
    args = parser.parse_args()
    
    user_id = args.user
    drift_level = "none" if args.reset else args.drift_level
    
    print("=" * 60)
    print(f"  Drift Simulation for {user_id}")
    print("=" * 60)
    
    # 현재 메트릭 확인
    print("\n📉 Before Drift:")
    current = get_current_metrics(user_id)
    if current["mae"]:
        print(f"   MAE: {current['mae']:.4f}")
    else:
        print("   MAE: (데이터 없음)")
    if current["r2"]:
        print(f"   R²:  {current['r2']:.4f}")
    else:
        print("   R²:  (데이터 없음)")
    
    # Drift 설정
    drift = DRIFT_LEVELS[drift_level]
    
    if args.reset:
        print(f"\n🔄 Resetting to normal state...")
    else:
        print(f"\n🔄 Simulating {drift_level.upper()} drift...")
        print(f"   - MAE multiplier: {drift['mae_multiplier']}")
        print(f"   - R² multiplier: {drift['r2_multiplier']}")
    
    # ConfigMap 업데이트
    success, stdout, stderr = update_metrics_exporter_config(user_id, drift_level)
    if not success:
        print(f"\n❌ ConfigMap 업데이트 실패: {stderr}")
        return 1
    
    print(f"\n✅ ConfigMap 업데이트 완료")
    
    # Pod 재시작
    print(f"\n🔄 Pod 재시작 중...")
    if restart_metrics_exporter(user_id):
        print(f"✅ Pod 재시작 요청 완료")
    else:
        print(f"⚠️ Pod 재시작 실패 (수동 재시작 필요)")
    
    # 대기
    print(f"\n⏳ 메트릭 업데이트 대기 중 (60초)...")
    time.sleep(60)
    
    # 업데이트된 메트릭 확인
    print(f"\n📈 After Drift:")
    updated = get_current_metrics(user_id)
    if updated["mae"]:
        mae_change = ((updated["mae"] / current["mae"]) - 1) * 100 if current["mae"] else 0
        status = "⚠️" if updated["mae"] > 0.45 else "✅"
        print(f"   {status} MAE: {updated['mae']:.4f} ({mae_change:+.1f}%)")
    if updated["r2"]:
        r2_change = ((updated["r2"] / current["r2"]) - 1) * 100 if current["r2"] else 0
        status = "⚠️" if updated["r2"] < 0.75 else "✅"
        print(f"   {status} R²:  {updated['r2']:.4f} ({r2_change:+.1f}%)")
    
    # Alert 예상
    if updated["mae"] and updated["mae"] > 0.45:
        print(f"\n🚨 Alert 조건 충족! (MAE > 0.45)")
    if updated["r2"] and updated["r2"] < 0.75:
        print(f"🚨 Alert 조건 충족! (R² < 0.75)")
    
    if args.reset:
        print(f"\n✅ 정상 상태로 복원 완료")
    else:
        print(f"\n✅ Drift 시뮬레이션 완료")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
