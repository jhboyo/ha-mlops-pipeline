#!/usr/bin/env python3
"""
Lab 3-2: 자동 재학습 트리거 스크립트

Drift가 감지되면 GitHub Actions 워크플로우를 트리거합니다.

사용법:
    export USER_NUM="01"
    python scripts/4_trigger_retrain.py --check-drift
    python scripts/4_trigger_retrain.py --force-trigger
"""

import os
import sys
import argparse
import json
import requests
from datetime import datetime

# 설정
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
USER_NUM = os.getenv("USER_NUM", "01")
USER_ID = f"user{USER_NUM}"

# 임계값
MAE_THRESHOLD = 0.45
R2_THRESHOLD = 0.75


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
    except Exception as e:
        print(f"Query error: {e}")
    return []


def check_model_drift(user_id):
    """모델 Drift 감지"""
    mae_result = query_prometheus(f'model_mae_score{{user_id="{user_id}"}}')
    r2_result = query_prometheus(f'model_r2_score{{user_id="{user_id}"}}')
    
    if not mae_result or not r2_result:
        return {
            'drift_detected': False,
            'mae': None,
            'r2': None,
            'drift_score': 0,
            'reason': 'No metrics available'
        }
    
    current_mae = float(mae_result[0]["value"][1])
    current_r2 = float(r2_result[0]["value"][1])
    
    mae_drift = current_mae > MAE_THRESHOLD
    r2_drift = current_r2 < R2_THRESHOLD
    
    # Drift Score 계산
    mae_score = max(0, (current_mae - MAE_THRESHOLD) / MAE_THRESHOLD) if mae_drift else 0
    r2_score = max(0, (R2_THRESHOLD - current_r2) / R2_THRESHOLD) if r2_drift else 0
    drift_score = (mae_score + r2_score) / 2
    
    reasons = []
    if mae_drift:
        reasons.append(f"MAE({current_mae:.4f}) > {MAE_THRESHOLD}")
    if r2_drift:
        reasons.append(f"R²({current_r2:.4f}) < {R2_THRESHOLD}")
    
    return {
        'drift_detected': mae_drift or r2_drift,
        'mae': current_mae,
        'r2': current_r2,
        'drift_score': drift_score,
        'reason': '; '.join(reasons) if reasons else 'Model performance normal'
    }


def trigger_github_workflow(user_id, drift_score, dry_run=True):
    """GitHub Actions workflow_dispatch 트리거"""
    
    workflow_file = "retrain-model.yaml"
    
    print(f"\n🚀 GitHub Actions 트리거...")
    print(f"   Repository: {GITHUB_REPO}")
    print(f"   Workflow: {workflow_file}")
    print(f"   Inputs:")
    print(f"     - user_id: {user_id}")
    print(f"     - drift_score: {drift_score:.4f}")
    
    if dry_run:
        print(f"\n📝 [DRY RUN] 실제 트리거하지 않음")
        print(f"\n실제 트리거를 위해 필요한 것:")
        print(f"   1. GITHUB_TOKEN 환경 변수 설정")
        print(f"   2. GITHUB_REPO 환경 변수 설정")
        print(f"   3. --no-dry-run 옵션 추가")
        return True
    
    if not GITHUB_TOKEN:
        print(f"\n❌ GITHUB_TOKEN이 설정되지 않았습니다.")
        print(f"   export GITHUB_TOKEN='your-token'")
        return False
    
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{workflow_file}/dispatches"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "ref": "main",
        "inputs": {
            "user_id": user_id,
            "drift_score": str(drift_score)
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 204:
            print(f"\n✅ 재학습 트리거 성공!")
            print(f"   GitHub Actions에서 워크플로우가 실행됩니다.")
            print(f"   확인: https://github.com/{GITHUB_REPO}/actions")
            return True
        else:
            print(f"\n❌ 트리거 실패: {response.status_code}")
            print(f"   {response.text}")
            return False
    except Exception as e:
        print(f"\n❌ 요청 실패: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="자동 재학습 트리거")
    parser.add_argument("--check-drift", action="store_true", help="Drift 확인 후 필요시 트리거")
    parser.add_argument("--force-trigger", action="store_true", help="강제 트리거 (Drift 상관없이)")
    parser.add_argument("--threshold", type=float, default=MAE_THRESHOLD, help="MAE 임계값")
    parser.add_argument("--no-dry-run", action="store_true", help="실제 GitHub API 호출")
    
    args = parser.parse_args()
    
    dry_run = not args.no_dry_run
    
    print("=" * 60)
    print("  Auto-Retrain Trigger Check")
    print("=" * 60)
    print(f"\n👤 사용자: {USER_ID}")
    print(f"📅 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Drift 상태 확인
    drift_status = check_model_drift(USER_ID)
    
    print(f"\n📊 현재 메트릭:")
    if drift_status['mae']:
        print(f"   MAE: {drift_status['mae']:.4f}")
    else:
        print(f"   MAE: (데이터 없음)")
    if drift_status['r2']:
        print(f"   R²:  {drift_status['r2']:.4f}")
    else:
        print(f"   R²:  (데이터 없음)")
    
    print(f"\n🔍 Drift 분석:")
    print(f"   Detected: {'🚨 YES' if drift_status['drift_detected'] else '✅ NO'}")
    print(f"   Score: {drift_status['drift_score']:.4f}")
    print(f"   Reason: {drift_status['reason']}")
    
    # 트리거 결정
    should_trigger = False
    
    if args.force_trigger:
        print(f"\n⚠️ 강제 트리거 모드")
        should_trigger = True
    elif args.check_drift:
        if drift_status['drift_detected']:
            print(f"\n⚠️ Drift 감지됨! 재학습 트리거...")
            should_trigger = True
        else:
            print(f"\n✅ Drift 없음. 재학습 불필요.")
    else:
        print(f"\n📝 옵션을 선택하세요:")
        print(f"   --check-drift: Drift 확인 후 트리거")
        print(f"   --force-trigger: 강제 트리거")
        return 0
    
    # 트리거 실행
    if should_trigger:
        success = trigger_github_workflow(
            USER_ID,
            drift_status['drift_score'] or 0.5,
            dry_run=dry_run
        )
        
        if success:
            print(f"\n" + "=" * 60)
            print(f"  재학습 트리거 {'시뮬레이션 ' if dry_run else ''}완료")
            print("=" * 60)
            
            print(f"\n📌 다음 단계:")
            print(f"   1. GitHub Actions에서 워크플로우 실행 확인")
            print(f"   2. MLflow에서 새 실험 확인")
            print(f"   3. 새 모델 성능 검증")
            print(f"   4. KServe 자동 배포 확인")
        else:
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
