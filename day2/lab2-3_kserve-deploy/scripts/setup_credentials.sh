#!/bin/bash
# ============================================================
# Lab 2-3: AWS 자격증명 설정 스크립트
# ============================================================
#
# 사용법:
#   # 1. 환경 변수 설정
#   export USER_NUM="01"  # 본인 번호
#   export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
#   export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
#
#   # 2. 스크립트 실행
#   ./scripts/setup_credentials.sh
#
# ============================================================
set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "  AWS 자격증명 설정"
echo "============================================================"

# ============================================================
# 환경 변수 확인
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

AWS_REGION=${AWS_REGION:-"ap-northeast-2"}

echo ""
echo "📋 설정 정보:"
echo "   👤 사용자 번호: ${USER_NUM}"
echo "   📁 네임스페이스: ${NAMESPACE}"
echo "   🌏 AWS 리전: ${AWS_REGION}"
echo ""

# AWS 환경변수 확인
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo -e "${RED}❌ AWS 환경 변수가 설정되지 않았습니다.${NC}"
    echo ""
    echo "아래 명령어로 환경변수를 설정하세요:"
    echo ""
    echo "  export AWS_ACCESS_KEY_ID='YOUR_ACCESS_KEY'"
    echo "  export AWS_SECRET_ACCESS_KEY='YOUR_SECRET_KEY'"
    echo "  export AWS_REGION='ap-northeast-2'  # 선택사항"
    echo ""
    exit 1
fi

echo "🔑 AWS Access Key: ${AWS_ACCESS_KEY_ID:0:4}****"
echo ""

# ============================================================
# Secret 생성
# ============================================================

echo "📦 Secret 생성 중..."
kubectl create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" \
  --from-literal=AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
  --from-literal=AWS_DEFAULT_REGION="$AWS_REGION" \
  -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✅ Secret 'aws-s3-credentials' 생성 완료${NC}"

# ============================================================
# ConfigMap 생성
# ============================================================

echo ""
echo "📦 ConfigMap 생성 중..."
kubectl create configmap s3-config \
  --from-literal=S3_ENDPOINT="s3.amazonaws.com" \
  --from-literal=S3_USE_HTTPS="1" \
  --from-literal=AWS_REGION="$AWS_REGION" \
  --from-literal=S3_BUCKET="mlops-training-user${USER_NUM}" \
  -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✅ ConfigMap 's3-config' 생성 완료${NC}"

# ============================================================
# 확인
# ============================================================

echo ""
echo "============================================================"
echo "  생성된 리소스 확인"
echo "============================================================"
echo ""
echo "📋 Secret:"
kubectl get secret aws-s3-credentials -n $NAMESPACE
echo ""
echo "📋 ConfigMap:"
kubectl get configmap s3-config -n $NAMESPACE
echo ""
echo -e "${GREEN}✅ 자격증명 설정 완료!${NC}"
echo ""
echo "============================================================"
echo "  다음 단계"
echo "============================================================"
echo ""
echo "1. MLflow로 모델 학습 및 S3에 저장"
echo "2. deploy_kserve.sh 실행하여 모델 배포"
echo ""
