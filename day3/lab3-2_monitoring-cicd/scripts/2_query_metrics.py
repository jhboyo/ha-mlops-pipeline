#!/usr/bin/env python3
"""
Lab 3-2: Prometheus 메트릭 조회 스크립트

사용법:
    export USER_NUM="01"
    python scripts/2_query_metrics.py
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta

# 설정
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
USER_NUM = os.getenv("USER_NUM", "01")
USER_ID = f"user{USER_NUM}"

# 임계값
MAE_THRESHOLD = 0.45
R2_THRESHOLD = 0.75


def query_prometheus(query):
    """Prometheus instant query"""
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
    except Exception as e:
        print(f"Query error: {e}")
    return []


def query_prometheus_range(query, duration_minutes=30, step="30s"):
    """Prometheus range query"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=duration_minutes)
    
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query_range",
            params={
                "query": query,
                "start": start_time.isoformat() + "Z",
                "end": end_time.isoformat() + "Z",
                "step": step
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "success":
                return data["data"]["result"]
    except Exception as e:
        print(f"Range query error: {e}")
    return []


def print_metric(name, results, threshold=None, higher_is_better=True):
    """메트릭 출력"""
    print(f"\n📊 {name}:")
    if not results:
        print("   (데이터 없음)")
        return
    
    for r in results[:15]:  # 최대 15개
        user_id = r["metric"].get("user_id", "unknown")
        value = float(r["value"][1])
        
        if threshold:
            if higher_is_better:
                status = "⚠️" if value < threshold else "✅"
            else:
                status = "⚠️" if value > threshold else "✅"
        else:
            status = "  "
        
        print(f"   {status} {user_id}: {value:.4f}")


def main():
    print("=" * 60)
    print("  Model Metrics Query")
    print("=" * 60)
    print(f"\n👤 대상 사용자: {USER_ID}")
    print(f"📡 Prometheus URL: {PROMETHEUS_URL}")
    
    # 연결 테스트
    try:
        response = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=5)
        if response.status_code != 200:
            print("\n❌ Prometheus 연결 실패")
            print("   포트포워딩 확인: kubectl port-forward -n monitoring svc/prometheus 9090:9090")
            return 1
    except:
        print("\n❌ Prometheus 연결 실패")
        print("   포트포워딩 확인: kubectl port-forward -n monitoring svc/prometheus 9090:9090")
        return 1
    
    print("\n✅ Prometheus 연결 성공")
    
    # 1. MAE Score (전체)
    mae_results = query_prometheus('model_mae_score')
    print_metric("model_mae_score (MAE - 낮을수록 좋음)", mae_results, MAE_THRESHOLD, higher_is_better=False)
    
    # 2. R² Score (전체)
    r2_results = query_prometheus('model_r2_score')
    print_metric("model_r2_score (R² - 높을수록 좋음)", r2_results, R2_THRESHOLD, higher_is_better=True)
    
    # 3. Prediction Rate
    print("\n📊 model_prediction_total (예측 처리량):")
    rate_results = query_prometheus('rate(model_prediction_total{status="success"}[5m])')
    if rate_results:
        for r in rate_results[:10]:
            user_id = r["metric"].get("user_id", "unknown")
            value = float(r["value"][1])
            print(f"   {user_id}: {value:.2f} req/sec")
    else:
        print("   (데이터 없음)")
    
    # 4. 본인 메트릭 상세
    print("\n" + "=" * 60)
    print(f"  {USER_ID} 상세 메트릭")
    print("=" * 60)
    
    # MAE
    my_mae = query_prometheus(f'model_mae_score{{user_id="{USER_ID}"}}')
    if my_mae:
        mae_value = float(my_mae[0]["value"][1])
        status = "⚠️ Drift!" if mae_value > MAE_THRESHOLD else "✅ Normal"
        print(f"\n📉 MAE: {mae_value:.4f} ({status})")
    else:
        print(f"\n📉 MAE: 데이터 없음")
    
    # R²
    my_r2 = query_prometheus(f'model_r2_score{{user_id="{USER_ID}"}}')
    if my_r2:
        r2_value = float(my_r2[0]["value"][1])
        status = "⚠️ Drift!" if r2_value < R2_THRESHOLD else "✅ Normal"
        print(f"📈 R²:  {r2_value:.4f} ({status})")
    else:
        print(f"📈 R²:  데이터 없음")
    
    # RPS
    my_rps = query_prometheus(f'rate(model_prediction_total{{user_id="{USER_ID}", status="success"}}[5m])')
    if my_rps:
        rps_value = float(my_rps[0]["value"][1])
        print(f"⚡ RPS: {rps_value:.2f} req/sec")
    
    # Latency
    my_latency = query_prometheus(f'histogram_quantile(0.95, rate(model_prediction_latency_bucket{{user_id="{USER_ID}"}}[5m]))')
    if my_latency:
        latency_value = float(my_latency[0]["value"][1]) * 1000  # ms
        print(f"⏱️ Latency (p95): {latency_value:.2f} ms")
    
    # 5. Drift 판정
    print("\n" + "=" * 60)
    print("  Drift 판정")
    print("=" * 60)
    
    drift_detected = False
    if my_mae and my_r2:
        mae_val = float(my_mae[0]["value"][1])
        r2_val = float(my_r2[0]["value"][1])
        
        print(f"\n현재 값:")
        print(f"   MAE: {mae_val:.4f} (임계값: {MAE_THRESHOLD})")
        print(f"   R²:  {r2_val:.4f} (임계값: {R2_THRESHOLD})")
        
        if mae_val > MAE_THRESHOLD:
            print(f"\n🚨 MAE가 임계값을 초과했습니다!")
            drift_detected = True
        if r2_val < R2_THRESHOLD:
            print(f"🚨 R²가 임계값 미만입니다!")
            drift_detected = True
        
        if drift_detected:
            print(f"\n⚠️ 결론: DRIFT 감지됨 - 재학습 권장")
        else:
            print(f"\n✅ 결론: 모델 성능 정상")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
