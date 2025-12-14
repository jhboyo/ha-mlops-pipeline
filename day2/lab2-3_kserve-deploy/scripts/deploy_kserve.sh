#!/bin/bash
# ============================================================
# Lab 2-3: KServe InferenceService 배포 스크립트
# ============================================================
#
# 사용법:
#   # 1. 환경 변수 설정
#   export USER_NUM="01"  # 본인 번호로 변경
#   source ../../scripts/setup-env.sh
#
#   # 2. Storage URI 설정
#   export STORAGE_URI="s3://mlops-training-user${USER_NUM}/mlflow-artifacts/RUN_ID/artifacts/model"
#
#   # 3. 스크립트 실행
#   ./scripts/deploy_kserve.sh
#
# ============================================================
set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "============================================================"
echo "  KServe InferenceService 배포"
echo "============================================================"

# ============================================================
# 환경 변수 설정
# ============================================================

# USER_NUM 확인
if [ -z "$USER_NUM" ]; then
    USER_NUM="01"
    echo -e "${YELLOW}⚠️  USER_NUM이 설정되지 않았습니다. 기본값 사용: ${USER_NUM}${NC}"
fi

# 네임스페이스 설정
if [ -f "/var/run/secrets/kubernetes.io/serviceaccount/namespace" ]; then
    NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
elif [ -n "$NAMESPACE" ]; then
    NAMESPACE="$NAMESPACE"
else
    NAMESPACE="kubeflow-user${USER_NUM}"
fi

# S3 버킷 설정 (사용자별)
S3_BUCKET=${S3_BUCKET:-"mlops-training-user${USER_NUM}"}

# 모델 설정
MODEL_NAME=${MODEL_NAME:-"california-model-user${USER_NUM}"}

echo ""
echo "📋 설정 정보:"
echo "   👤 사용자 번호: ${USER_NUM}"
echo "   📁 네임스페이스: ${NAMESPACE}"
echo "   🪣 S3 버킷: ${S3_BUCKET}"
echo "   🤖 모델명: ${MODEL_NAME}"
echo ""

# ============================================================
# Storage URI 확인
# ============================================================

if [ -z "$STORAGE_URI" ]; then
    echo -e "${YELLOW}⚠️  STORAGE_URI가 설정되지 않았습니다.${NC}"
    echo ""
    echo "S3에서 모델 경로를 확인하세요:"
    echo "  aws s3 ls s3://${S3_BUCKET}/mlflow-artifacts/ --recursive | grep MLmodel"
    echo ""
    echo "그 다음 환경변수를 설정하세요:"
    echo "  export STORAGE_URI='s3://${S3_BUCKET}/mlflow-artifacts/RUN_ID/artifacts/model'"
    echo ""
    
    # S3에서 모델 경로 자동 탐색 시도
    echo "🔍 S3에서 모델 경로 탐색 중..."
    MODEL_PATH=$(aws s3 ls s3://${S3_BUCKET}/mlflow-artifacts/ --recursive 2>/dev/null | grep "MLmodel" | head -1 | awk '{print $4}')
    
    if [ -n "$MODEL_PATH" ]; then
        # MLmodel 파일에서 model 디렉토리 경로 추출
        MODEL_DIR=$(dirname "$MODEL_PATH")
        STORAGE_URI="s3://${S3_BUCKET}/${MODEL_DIR}"
        echo -e "${GREEN}✅ 모델 경로 발견: ${STORAGE_URI}${NC}"
    else
        echo -e "${RED}❌ S3에서 모델을 찾을 수 없습니다.${NC}"
        echo "   먼저 MLflow로 모델을 학습하고 S3에 저장하세요."
        exit 1
    fi
fi

echo "📦 Storage URI: ${STORAGE_URI}"
echo ""

# ============================================================
# 기존 InferenceService 삭제 (있으면)
# ============================================================

echo "🗑️  기존 InferenceService 확인 중..."
if kubectl get inferenceservice $MODEL_NAME -n $NAMESPACE &>/dev/null; then
    echo "  기존 InferenceService 삭제 중..."
    kubectl delete inferenceservice $MODEL_NAME -n $NAMESPACE --wait=true
    sleep 5
fi

# ============================================================
# InferenceService 생성
# ============================================================

echo ""
echo "📝 InferenceService 생성 중..."

cat <<EOF | kubectl apply -f -
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: ${MODEL_NAME}
  namespace: ${NAMESPACE}
  labels:
    user: user${USER_NUM}
  annotations:
    # ⚠️ 중요: Istio sidecar 비활성화 (RBAC 403 에러 방지)
    sidecar.istio.io/inject: "false"
spec:
  predictor:
    model:
      modelFormat:
        name: sklearn
      storageUri: "${STORAGE_URI}"
      resources:
        requests:
          cpu: "500m"
          memory: "1Gi"
        limits:
          cpu: "1"
          memory: "2Gi"
EOF

echo -e "${GREEN}✅ InferenceService 생성 완료${NC}"
echo ""

# ============================================================
# 배포 대기
# ============================================================

echo "⏳ 배포 대기 중 (최대 5분)..."
echo "   (보통 2-3분 소요)"
echo ""

TIMEOUT=300
START_TIME=$(date +%s)

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo -e "${RED}❌ 타임아웃: ${TIMEOUT}초 초과${NC}"
        echo ""
        echo "상태 확인:"
        kubectl describe inferenceservice $MODEL_NAME -n $NAMESPACE | tail -30
        exit 1
    fi
    
    # 상태 확인
    READY=$(kubectl get inferenceservice $MODEL_NAME -n $NAMESPACE -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "Unknown")
    
    if [ "$READY" == "True" ]; then
        break
    fi
    
    # 진행 상황 출력
    printf "\r   경과 시간: %ds / %ds (상태: %s)   " $ELAPSED $TIMEOUT "$READY"
    sleep 5
done

echo ""
echo ""

# ============================================================
# 배포 완료
# ============================================================

echo "============================================================"
echo -e "${GREEN}  ✅ KServe InferenceService 배포 완료!${NC}"
echo "============================================================"
echo ""
echo "📋 InferenceService 상태:"
kubectl get inferenceservice $MODEL_NAME -n $NAMESPACE
echo ""

# URL 확인
ISVC_URL=$(kubectl get inferenceservice $MODEL_NAME -n $NAMESPACE -o jsonpath='{.status.url}' 2>/dev/null || echo "N/A")
echo "🌐 Service URL: ${ISVC_URL}"
echo ""

# ============================================================
# 테스트 안내
# ============================================================

echo "============================================================"
echo "  🚀 다음 단계: 모델 테스트"
echo "============================================================"
echo ""
echo "1️⃣  포트 포워딩 (새 터미널에서):"
echo "   kubectl port-forward -n ${NAMESPACE} svc/${MODEL_NAME}-predictor 8080:80"
echo ""
echo "2️⃣  예측 테스트:"
echo '   curl -X POST http://localhost:8080/v1/models/'${MODEL_NAME}':predict \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '\''{"instances": [[8.3252, 41.0, 6.984127, 1.023810, 322.0, 2.555556, 37.88, -122.23]]}'\'''
echo ""
echo "============================================================"
