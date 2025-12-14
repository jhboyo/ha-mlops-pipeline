#!/bin/bash
#
# Lab 3-2: CI/CD End-to-End 테스트 스크립트
#

set -e

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 설정
USER_NUM="${USER_NUM:-01}"
USER_ID="user${USER_NUM}"
NAMESPACE="kubeflow-${USER_ID}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"

echo "============================================================"
echo "  Lab 3-2: CI/CD End-to-End Test"
echo "============================================================"
echo ""
echo "👤 사용자: ${USER_ID}"
echo "📁 네임스페이스: ${NAMESPACE}"
echo ""

PASSED=0
FAILED=0

# 테스트 함수
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "테스트: ${test_name}... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "============================================================"
echo "  Part 1: Monitoring Stack 테스트"
echo "============================================================"
echo ""

# 1. Prometheus Pod
run_test "Prometheus Pod" "kubectl get pods -n monitoring -l app=prometheus | grep Running"

# 2. Grafana Pod
run_test "Grafana Pod" "kubectl get pods -n monitoring -l app=grafana | grep Running"

# 3. Alertmanager Pod
run_test "Alertmanager Pod" "kubectl get pods -n monitoring -l app=alertmanager | grep Running"

# 4. Metrics Exporter Pod
run_test "Metrics Exporter (${USER_ID})" "kubectl get pods -n ${NAMESPACE} -l app=metrics-exporter | grep Running"

# 5. Prometheus 연결
run_test "Prometheus 연결" "curl -s ${PROMETHEUS_URL}/-/healthy | grep -q 'Prometheus Server is Healthy'"

# 6. Grafana 연결
run_test "Grafana 연결" "curl -s ${GRAFANA_URL}/api/health | grep -q ok"

echo ""
echo "============================================================"
echo "  Part 2: 메트릭 수집 테스트"
echo "============================================================"
echo ""

# 7. MAE 메트릭 (빈 배열이 아닌 경우만 통과)
run_test "MAE 메트릭 존재" "curl -s '${PROMETHEUS_URL}/api/v1/query?query=model_mae_score{user_id=\"${USER_ID}\"}' | grep -q '\"result\":\\[{'"

# 8. R² 메트릭 (빈 배열이 아닌 경우만 통과)
run_test "R² 메트릭 존재" "curl -s '${PROMETHEUS_URL}/api/v1/query?query=model_r2_score{user_id=\"${USER_ID}\"}' | grep -q '\"result\":\\[{'"

# 9. Prediction Total 메트릭 (빈 배열이 아닌 경우만 통과)
run_test "Prediction 메트릭" "curl -s '${PROMETHEUS_URL}/api/v1/query?query=model_prediction_total{user_id=\"${USER_ID}\"}' | grep -q '\"result\":\\[{'"

echo ""
echo "============================================================"
echo "  Part 3: CI/CD 구성 요소 테스트"
echo "============================================================"
echo ""

# 10. GitHub Actions 워크플로우 파일
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOWS_DIR="${SCRIPT_DIR}/../.github/workflows"

if [ -d "$WORKFLOWS_DIR" ]; then
    run_test "CI 워크플로우 파일" "test -f ${WORKFLOWS_DIR}/ci-test.yaml"
    run_test "CD 워크플로우 파일" "test -f ${WORKFLOWS_DIR}/cd-deploy.yaml"
else
    echo -e "${YELLOW}⚠️ .github/workflows 디렉토리 없음 (선택 사항)${NC}"
fi

# 11. Python 스크립트
run_test "check_monitoring.py" "test -f ${SCRIPT_DIR}/1_check_monitoring.py"
run_test "query_metrics.py" "test -f ${SCRIPT_DIR}/2_query_metrics.py"
run_test "simulate_drift.py" "test -f ${SCRIPT_DIR}/3_simulate_drift.py"
run_test "trigger_retrain.py" "test -f ${SCRIPT_DIR}/4_trigger_retrain.py"

echo ""
echo "============================================================"
echo "  Part 4: Drift 감지 테스트"
echo "============================================================"
echo ""

# 12. Drift 감지 스크립트 실행
if python3 ${SCRIPT_DIR}/2_query_metrics.py > /dev/null 2>&1; then
    echo -e "테스트: Drift 감지 스크립트... ${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "테스트: Drift 감지 스크립트... ${YELLOW}⚠️ SKIP (Prometheus 연결 필요)${NC}"
fi

# 결과 요약
echo ""
echo "============================================================"
echo "  테스트 결과 요약"
echo "============================================================"
echo ""
echo -e "통과: ${GREEN}${PASSED}${NC}"
echo -e "실패: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 모든 테스트 통과!${NC}"
    echo ""
    echo "📌 다음 단계:"
    echo "   1. Grafana 대시보드 확인: ${GRAFANA_URL}"
    echo "   2. Prometheus 타겟 확인: ${PROMETHEUS_URL}/targets"
    echo "   3. Drift 시뮬레이션: python scripts/3_simulate_drift.py --user ${USER_ID} --drift-level high"
    exit 0
else
    echo -e "${RED}❌ ${FAILED}개 테스트 실패${NC}"
    echo ""
    echo "문제 해결:"
    echo "   1. 포트포워딩 확인:"
    echo "      kubectl port-forward -n monitoring svc/prometheus 9090:9090"
    echo "      kubectl port-forward -n monitoring svc/grafana 3000:3000"
    echo "   2. Pod 상태 확인:"
    echo "      kubectl get pods -n monitoring"
    echo "      kubectl get pods -n ${NAMESPACE}"
    exit 1
fi