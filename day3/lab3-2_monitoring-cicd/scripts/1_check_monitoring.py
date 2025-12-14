#!/usr/bin/env python3
"""
Lab 3-2: Monitoring Stack 상태 확인 스크립트

사용법:
    python scripts/1_check_monitoring.py
"""

import os
import sys
import subprocess
import requests

# 설정
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
NAMESPACE = "monitoring"


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


def check_pod_status(namespace, label):
    """Pod 상태 확인"""
    success, stdout, stderr = run_kubectl([
        "get", "pods", "-n", namespace,
        "-l", label,
        "-o", "jsonpath={.items[*].status.phase}"
    ])
    if success and stdout:
        phases = stdout.split()
        running = phases.count("Running")
        return running, len(phases)
    return 0, 0


def check_prometheus_health():
    """Prometheus 헬스 체크"""
    try:
        response = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=5)
        return response.status_code == 200
    except:
        return False


def check_grafana_health():
    """Grafana 헬스 체크"""
    try:
        response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_prometheus_targets():
    """Prometheus 타겟 목록"""
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/targets", timeout=10)
        if response.status_code == 200:
            data = response.json()
            targets = data.get("data", {}).get("activeTargets", [])
            return [
                {
                    "job": t.get("labels", {}).get("job", "unknown"),
                    "instance": t.get("labels", {}).get("instance", "unknown"),
                    "health": t.get("health", "unknown"),
                    "user_id": t.get("labels", {}).get("user_id", "")
                }
                for t in targets
            ]
    except:
        pass
    return []


def main():
    print("=" * 60)
    print("  Monitoring Stack Status Check")
    print("=" * 60)
    print()
    
    passed = 0
    failed = 0
    
    # 1. Prometheus Pod
    running, total = check_pod_status(NAMESPACE, "app=prometheus")
    if running > 0:
        print(f"✅ Prometheus: Running ({running}/{total})")
        passed += 1
    else:
        print(f"❌ Prometheus: Not Running ({running}/{total})")
        failed += 1
    
    # 2. Grafana Pod
    running, total = check_pod_status(NAMESPACE, "app=grafana")
    if running > 0:
        print(f"✅ Grafana: Running ({running}/{total})")
        passed += 1
    else:
        print(f"❌ Grafana: Not Running ({running}/{total})")
        failed += 1
    
    # 3. Alertmanager Pod
    running, total = check_pod_status(NAMESPACE, "app=alertmanager")
    if running > 0:
        print(f"✅ Alertmanager: Running ({running}/{total})")
        passed += 1
    else:
        print(f"❌ Alertmanager: Not Running ({running}/{total})")
        failed += 1
    
    # 4. Metrics Exporter Pods (사용자별)
    print()
    print("📊 Metrics Exporter Pods:")
    success, stdout, _ = run_kubectl([
        "get", "pods", "-A",
        "-l", "app=metrics-exporter",
        "--no-headers"
    ])
    if success and stdout:
        lines = stdout.strip().split("\n")
        running_count = sum(1 for l in lines if "Running" in l)
        print(f"   Total: {len(lines)} pods, Running: {running_count}")
        if running_count > 0:
            passed += 1
        else:
            failed += 1
    else:
        print("   ⚠️ No metrics-exporter pods found")
    
    # 5. Prometheus 연결 테스트
    print()
    print("🔗 연결 테스트:")
    if check_prometheus_health():
        print(f"   ✅ Prometheus ({PROMETHEUS_URL})")
    else:
        print(f"   ⚠️ Prometheus 연결 실패 - 포트포워딩 확인")
        print(f"      kubectl port-forward -n monitoring svc/prometheus 9090:9090")
    
    if check_grafana_health():
        print(f"   ✅ Grafana ({GRAFANA_URL})")
    else:
        print(f"   ⚠️ Grafana 연결 실패 - 포트포워딩 확인")
        print(f"      kubectl port-forward -n monitoring svc/grafana 3000:3000")
    
    # 6. Prometheus 타겟
    print()
    targets = get_prometheus_targets()
    if targets:
        print("📡 Prometheus Targets:")
        user_targets = [t for t in targets if t["user_id"]]
        up_count = sum(1 for t in user_targets if t["health"] == "up")
        print(f"   User Metrics Exporters: {up_count}/{len(user_targets)} UP")
        
        # 몇 개 샘플 출력
        for t in user_targets[:5]:
            status = "✅" if t["health"] == "up" else "❌"
            print(f"   {status} {t['user_id']}: {t['health']}")
        if len(user_targets) > 5:
            print(f"   ... ({len(user_targets) - 5} more)")
    
    # 결과 요약
    print()
    print("=" * 60)
    print(f"  검증 결과: {passed}/{passed + failed} 통과")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ 모든 컴포넌트가 정상입니다!")
        return 0
    else:
        print(f"\n⚠️ {failed}개 컴포넌트에 문제가 있습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
