#!/bin/bash
# ============================================================
# Lab 2-3: 추론 테스트 스크립트
# ============================================================

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "============================================================"
echo "  KServe 추론 테스트"
echo "============================================================"

# USER_NUM 확인
if [ -z "$USER_NUM" ]; then
    USER_NUM="01"
    echo -e "${YELLOW}⚠️  USER_NUM이 설정되지 않았습니다. 기본값 사용: ${USER_NUM}${NC}"
fi

# 네임스페이스 설정
if [ -f "/var/run/secrets/kubernetes.io/serviceaccount/namespace" ]; then
    NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
elif [ -n "$USER_NAMESPACE" ]; then
    NAMESPACE="$USER_NAMESPACE"
else
    NAMESPACE="kubeflow-user${USER_NUM}"
fi

MODEL_NAME=${MODEL_NAME:-"california-model-user${USER_NUM}4"}

echo "📁 네임스페이스: $NAMESPACE"
echo "🤖 모델명: $MODEL_NAME"
echo ""

# 테스트 방법 선택
echo "============================================================"
echo "  테스트 방법 선택"
echo "============================================================"
echo ""
echo "1. 클러스터 내부 테스트 (curl)"
echo "2. 포트 포워딩 후 로컬 테스트"
echo ""

# 클러스터 내부인지 확인
if [ -f "/var/run/secrets/kubernetes.io/serviceaccount/token" ]; then
    echo -e "${CYAN}🔍 Kubernetes 클러스터 내부 환경 감지${NC}"
    TEST_MODE="internal"
else
    echo -e "${CYAN}🔍 로컬 환경 감지 - 포트 포워딩 사용${NC}"
    TEST_MODE="portforward"
fi

echo ""

# California Housing 테스트 데이터 (8개 특성)
# [MedInc, HouseAge, AveRooms, AveBedrms, Population, AveOccup, Latitude, Longitude]
TEST_DATA='{"instances": [[3.5, 25.0, 5.5, 1.1, 1500.0, 3.0, 37.5, -122.0]]}'

echo "📤 테스트 데이터:"
echo "   $TEST_DATA"
echo ""
echo "   California Housing 특성:"
echo "   [MedInc, HouseAge, AveRooms, AveBedrms, Population, AveOccup, Latitude, Longitude]"
echo ""

if [ "$TEST_MODE" == "internal" ]; then
    # 클러스터 내부 테스트
    URL="http://${MODEL_NAME}-predictor.${NAMESPACE}.svc.cluster.local/v1/models/${MODEL_NAME}:predict"
    
    echo "🔗 URL: $URL"
    echo ""
    echo "📡 추론 요청 중..."
    
    RESPONSE=$(curl -s -X POST "$URL" \
        -H "Content-Type: application/json" \
        -d "$TEST_DATA" \
        --connect-timeout 10 \
        --max-time 30)
    
    if [ $? -eq 0 ] && [ -n "$RESPONSE" ]; then
        echo ""
        echo -e "${GREEN}✅ 추론 성공!${NC}"
        echo ""
        echo "📥 응답:"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
        
        # 가격 계산 (California Housing 타겟은 $100,000 단위)
        PREDICTION=$(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('predictions',[0])[0])" 2>/dev/null)
        if [ -n "$PREDICTION" ]; then
            PRICE=$(python3 -c "print(f'${float($PREDICTION) * 100000:,.0f}')" 2>/dev/null || echo "N/A")
            echo ""
            echo -e "${GREEN}🏠 예측된 주택 가격: \$$PRICE${NC}"
        fi
    else
        echo -e "${RED}❌ 추론 실패${NC}"
        echo "   응답: $RESPONSE"
    fi
    
else
    # 포트 포워딩 테스트
    echo "🔌 포트 포워딩 설정 중..."
    
    # predictor Pod 찾기
    POD=$(kubectl get pods -n $NAMESPACE \
        -l serving.knative.dev/configuration=${MODEL_NAME}-predictor \
        --field-selector=status.phase=Running \
        -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$POD" ]; then
        echo -e "${RED}❌ 실행 중인 Pod를 찾을 수 없습니다.${NC}"
        exit 1
    fi
    
    echo "   Pod: $POD"
    
    # 포트 포워딩 시작
    kubectl port-forward -n $NAMESPACE pod/$POD 8081:8080 &>/dev/null &
    PF_PID=$!
    sleep 3
    
    # 포트 포워딩 확인
    if ! kill -0 $PF_PID 2>/dev/null; then
        echo -e "${RED}❌ 포트 포워딩 실패${NC}"
        exit 1
    fi
    
    echo "   포트 포워딩 활성화 (PID: $PF_PID)"
    echo ""
    
    # 테스트 실행
    URL="http://localhost:8081/v1/models/${MODEL_NAME}:predict"
    echo "🔗 URL: $URL"
    echo ""
    echo "📡 추론 요청 중..."
    
    RESPONSE=$(curl -s -X POST "$URL" \
        -H "Content-Type: application/json" \
        -d "$TEST_DATA" \
        --connect-timeout 10 \
        --max-time 30)
    
    # 포트 포워딩 종료
    kill $PF_PID 2>/dev/null
    
    if [ $? -eq 0 ] && [ -n "$RESPONSE" ]; then
        echo ""
        echo -e "${GREEN}✅ 추론 성공!${NC}"
        echo ""
        echo "📥 응답:"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    else
        echo -e "${RED}❌ 추론 실패${NC}"
        echo "   응답: $RESPONSE"
    fi
fi

echo ""
echo "============================================================"
echo -e "${GREEN}✅ 테스트 완료${NC}"
echo "============================================================"
