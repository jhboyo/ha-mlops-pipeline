#!/bin/bash
# ============================================================
# Lab 2-1: FastAPI 모델 서빙 - 빌드 및 배포 스크립트
# ============================================================
#
# 사용법:
#   # 1. 환경 변수 설정
#   export USER_NUM="01"  # 본인 번호로 변경
#
#   # 2. 스크립트 실행
#   ./scripts/build_and_deploy.sh
#
# ============================================================

set -e  # 오류 발생 시 즉시 종료

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

echo "============================================================"
echo "  Lab 2-1: FastAPI 모델 서빙 - 빌드 및 배포"
echo "============================================================"
echo ""

# ============================================================
# 환경 변수 확인
# ============================================================
log_step "환경 변수 확인"

# USER_NUM 확인 및 기본값 설정
if [ -z "$USER_NUM" ]; then
    USER_NUM="01"
    log_warn "USER_NUM not set, using default: ${USER_NUM}"
fi

# ECR_REGISTRY 확인
if [ -z "$ECR_REGISTRY" ]; then
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        log_error "AWS 자격 증명을 확인할 수 없습니다."
        echo ""
        echo "다음 명령어를 실행하세요:"
        echo "  aws configure"
        exit 1
    fi
    ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.ap-northeast-2.amazonaws.com"
    log_warn "ECR_REGISTRY not set, using: ${ECR_REGISTRY}"
fi

# NAMESPACE 확인
if [ -z "$NAMESPACE" ]; then
    NAMESPACE="kubeflow-user${USER_NUM}"
    log_warn "NAMESPACE not set, using: ${NAMESPACE}"
fi

log_info "User Number: ${USER_NUM}"
log_info "ECR Registry: ${ECR_REGISTRY}"
log_info "Namespace: ${NAMESPACE}"
echo ""

# ============================================================
# 모델 파일 확인
# ============================================================
log_step "모델 파일 확인"

if [ ! -f "model.joblib" ]; then
    log_error "model.joblib 파일을 찾을 수 없습니다."
    echo ""
    echo "다음 명령어로 모델을 먼저 학습하세요:"
    echo "  python train_model.py"
    exit 1
fi

log_info "✅ model.joblib 파일 확인됨"
echo ""

# ============================================================
# [1/6] Docker 이미지 빌드
# ============================================================
log_step "[1/6] Docker 이미지 빌드"

IMAGE_NAME="user$USER_NUM"
IMAGE_TAG="v1"

log_info "이미지 빌드 중..."
log_info "  이미지: ${IMAGE_NAME}:${IMAGE_TAG}"
log_info "  플랫폼: linux/amd64"

docker build --platform linux/amd64 -t ${IMAGE_NAME}:${IMAGE_TAG} . || {
    log_error "Docker 이미지 빌드 실패"
    exit 1
}

log_info "✅ Docker 이미지 빌드 완료"
echo ""

# ============================================================
# [2/6] ECR 로그인
# ============================================================
log_step "[2/6] ECR 로그인"

log_info "ECR에 로그인 중..."
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin $ECR_REGISTRY || {
    log_error "ECR 로그인 실패"
    exit 1
}

log_info "✅ ECR 로그인 성공"
echo ""

# ============================================================
# [3/6] 이미지 태깅
# ============================================================
log_step "[3/6] 이미지 태깅"

# 사용자별 ECR 레포지토리 경로 (변경됨!)
ECR_REPO="mlops-training/${IMAGE_NAME}"
FULL_IMAGE_NAME="${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}"

log_info "사용자별 ECR 레포지토리: ${ECR_REPO}"
log_info "전체 이미지 경로: ${FULL_IMAGE_NAME}"

docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${FULL_IMAGE_NAME} || {
    log_error "이미지 태깅 실패"
    exit 1
}

log_info "✅ 이미지 태깅 완료"
echo ""

# ============================================================
# [4/6] 이미지 푸시
# ============================================================
log_step "[4/6] ECR에 이미지 푸시"

log_info "이미지 푸시 중..."
docker push ${FULL_IMAGE_NAME} || {
    log_error "이미지 푸시 실패"
    echo ""
    echo "ECR 레포지토리가 존재하는지 확인하세요:"
    echo "  aws ecr describe-repositories --repository-names ${ECR_REPO}"
    exit 1
}

log_info "✅ 이미지 푸시 완료"
echo ""

# ============================================================
# [5/6] Kubernetes 배포
# ============================================================
log_step "[5/6] Kubernetes 배포"

# 환경 변수 설정 (envsubst용)
export ECR_REGISTRY
export NAMESPACE
export USER_NUM
export ECR_REPO

log_info "Deployment 배포 중..."
envsubst < manifests/deployment.yaml | kubectl apply -f - || {
    log_error "Deployment 배포 실패"
    exit 1
}

log_info "Service 배포 중..."
envsubst < manifests/service.yaml | kubectl apply -f - || {
    log_error "Service 배포 실패"
    exit 1
}

log_info "✅ Kubernetes 리소스 배포 완료"
echo ""

# ============================================================
# [6/6] 배포 확인
# ============================================================
log_step "[6/6] 배포 상태 확인"

log_info "배포 완료 대기 중..."
kubectl wait --for=condition=available --timeout=300s \
  deployment/iris-api -n $NAMESPACE || {
    log_error "Deployment 준비 실패"
    echo ""
    echo "Pod 상태 확인:"
    kubectl get pods -n $NAMESPACE -l app=iris-api
    echo ""
    echo "Pod 로그 확인:"
    kubectl logs -n $NAMESPACE -l app=iris-api --tail=50
    exit 1
}

log_info "✅ 배포 준비 완료"
echo ""

# ============================================================
# 배포 결과 출력
# ============================================================
echo "============================================================"
echo "  ✅ 배포 완료!"
echo "============================================================"
echo ""
echo "  👤 User Number: ${USER_NUM}"
echo "  📁 Namespace: ${NAMESPACE}"
echo "  🐳 Image: ${FULL_IMAGE_NAME}"
echo ""

echo "📦 Deployment 상태:"
kubectl get deployment iris-api -n $NAMESPACE
echo ""

echo "🏃 Pod 상태:"
kubectl get pods -n $NAMESPACE -l app=iris-api
echo ""

echo "🌐 Service 상태:"
kubectl get svc iris-api-svc -n $NAMESPACE
echo ""

# ============================================================
# 다음 단계 안내
# ============================================================
echo "============================================================"
echo "  🚀 다음 단계: API 테스트"
echo "============================================================"
echo ""
echo "1️⃣  Port Forward 시작 (새 터미널에서):"
echo "   kubectl port-forward -n $NAMESPACE svc/iris-api-svc 8000:80"
echo ""
echo "2️⃣  API 테스트 (다른 터미널에서):"
echo "   # Health Check"
echo "   curl http://localhost:8000/health"
echo ""
echo "   # 예측 테스트"
echo "   curl -X POST http://localhost:8000/predict \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"sepal_length\":5.1,\"sepal_width\":3.5,\"petal_length\":1.4,\"petal_width\":0.2}'"
echo ""
echo "============================================================"
