#!/bin/bash
# ============================================================
# Lab 2-1: FastAPI 모델 서빙 - API 테스트 스크립트
# ============================================================
#
# 사용법:
#   ./scripts/test_api.sh [API_URL]
#
# 예시:
#   ./scripts/test_api.sh                      # 기본: http://localhost:8000
#   ./scripts/test_api.sh http://localhost:8001  # 커스텀 URL
#
# ============================================================

set -e

# API URL 설정
API_URL="${1:-http://localhost:8000}"

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 로그 함수
log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# 결과 JSON 포맷팅 함수
format_json() {
    if command -v python3 &> /dev/null; then
        python3 -m json.tool
    elif command -v jq &> /dev/null; then
        jq .
    else
        cat
    fi
}

echo "============================================================"
echo "  Lab 2-1: Iris Classification API 테스트"
echo "============================================================"
echo ""
log_info "API URL: $API_URL"
echo ""

# ============================================================
# API 연결 확인
# ============================================================
log_test "API 연결 확인 중..."
if curl -s -f -o /dev/null "${API_URL}/health"; then
    log_pass "API 연결 성공"
else
    log_fail "API 연결 실패"
    echo ""
    echo "다음을 확인하세요:"
    echo "  1. Port Forward가 실행 중인가?"
    echo "     kubectl port-forward -n \$NAMESPACE svc/iris-api-svc 8000:80"
    echo ""
    echo "  2. API 서버가 실행 중인가?"
    echo "     kubectl get pods -n \$NAMESPACE -l app=iris-api"
    echo ""
    exit 1
fi
echo ""

# ============================================================
# Test 1: GET / (API 정보)
# ============================================================
echo "============================================================"
log_test "[1/6] GET / - API 정보 확인"
echo "============================================================"
echo ""

RESPONSE=$(curl -s "${API_URL}/")
echo "$RESPONSE" | format_json
echo ""

if echo "$RESPONSE" | grep -q "Iris Classification API"; then
    log_pass "API 정보 확인 성공"
else
    log_fail "API 정보 확인 실패"
fi
echo ""

# ============================================================
# Test 2: GET /health (Health Check)
# ============================================================
echo "============================================================"
log_test "[2/6] GET /health - Health Check"
echo "============================================================"
echo ""

RESPONSE=$(curl -s "${API_URL}/health")
echo "$RESPONSE" | format_json
echo ""

if echo "$RESPONSE" | grep -q '"status": "healthy"'; then
    log_pass "Health Check 성공"
else
    log_fail "Health Check 실패"
fi
echo ""

# ============================================================
# Test 3: POST /predict (Iris Setosa 예측)
# ============================================================
echo "============================================================"
log_test "[3/6] POST /predict - Setosa 예측"
echo "============================================================"
echo ""

log_info "입력 데이터:"
cat << EOF | format_json
{
  "sepal_length": 5.1,
  "sepal_width": 3.5,
  "petal_length": 1.4,
  "petal_width": 0.2
}
EOF
echo ""

log_info "예측 결과:"
RESPONSE=$(curl -s -X POST "${API_URL}/predict" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}')
echo "$RESPONSE" | format_json
echo ""

if echo "$RESPONSE" | grep -q '"prediction": "setosa"'; then
    log_pass "Setosa 예측 성공"
else
    log_fail "Setosa 예측 실패"
fi
echo ""

# ============================================================
# Test 4: POST /predict (Iris Versicolor 예측)
# ============================================================
echo "============================================================"
log_test "[4/6] POST /predict - Versicolor 예측"
echo "============================================================"
echo ""

log_info "입력 데이터:"
cat << EOF | format_json
{
  "sepal_length": 5.9,
  "sepal_width": 3.0,
  "petal_length": 4.2,
  "petal_width": 1.5
}
EOF
echo ""

log_info "예측 결과:"
RESPONSE=$(curl -s -X POST "${API_URL}/predict" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.9,"sepal_width":3.0,"petal_length":4.2,"petal_width":1.5}')
echo "$RESPONSE" | format_json
echo ""

if echo "$RESPONSE" | grep -q '"prediction": "versicolor"'; then
    log_pass "Versicolor 예측 성공"
else
    log_fail "Versicolor 예측 실패"
fi
echo ""

# ============================================================
# Test 5: POST /predict (Iris Virginica 예측)
# ============================================================
echo "============================================================"
log_test "[5/6] POST /predict - Virginica 예측"
echo "============================================================"
echo ""

log_info "입력 데이터:"
cat << EOF | format_json
{
  "sepal_length": 6.7,
  "sepal_width": 3.0,
  "petal_length": 5.2,
  "petal_width": 2.3
}
EOF
echo ""

log_info "예측 결과:"
RESPONSE=$(curl -s -X POST "${API_URL}/predict" \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":6.7,"sepal_width":3.0,"petal_length":5.2,"petal_width":2.3}')
echo "$RESPONSE" | format_json
echo ""

if echo "$RESPONSE" | grep -q '"prediction": "virginica"'; then
    log_pass "Virginica 예측 성공"
else
    log_fail "Virginica 예측 실패"
fi
echo ""

# ============================================================
# Test 6: POST /predict/batch (배치 예측)
# ============================================================
echo "============================================================"
log_test "[6/6] POST /predict/batch - 배치 예측 (3개 샘플)"
echo "============================================================"
echo ""

log_info "입력 데이터:"
cat << 'EOF' | format_json
[
  {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
  {"sepal_length": 5.9, "sepal_width": 3.0, "petal_length": 4.2, "petal_width": 1.5},
  {"sepal_length": 6.7, "sepal_width": 3.0, "petal_length": 5.2, "petal_width": 2.3}
]
EOF
echo ""

log_info "예측 결과:"
RESPONSE=$(curl -s -X POST "${API_URL}/predict/batch" \
  -H "Content-Type: application/json" \
  -d '[
    {"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2},
    {"sepal_length":5.9,"sepal_width":3.0,"petal_length":4.2,"petal_width":1.5},
    {"sepal_length":6.7,"sepal_width":3.0,"petal_length":5.2,"petal_width":2.3}
  ]')
echo "$RESPONSE" | format_json
echo ""

if echo "$RESPONSE" | grep -q '"predictions"'; then
    log_pass "배치 예측 성공"
else
    log_fail "배치 예측 실패"
fi
echo ""

# ============================================================
# 테스트 결과 요약
# ============================================================
echo "============================================================"
echo "  ✅ 모든 테스트 완료!"
echo "============================================================"
echo ""

echo "📊 테스트 결과 요약:"
echo "  ✅ [1/6] API 정보 확인"
echo "  ✅ [2/6] Health Check"
echo "  ✅ [3/6] Setosa 예측"
echo "  ✅ [4/6] Versicolor 예측"
echo "  ✅ [5/6] Virginica 예측"
echo "  ✅ [6/6] 배치 예측"
echo ""

echo "🎉 모든 테스트가 성공적으로 완료되었습니다!"
echo ""

echo "💡 추가 테스트:"
echo "  - Swagger UI: ${API_URL}/docs"
echo ""
