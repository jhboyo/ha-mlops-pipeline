#!/bin/bash

# Lab 1-1 Part 3: AWS 스토리지 확인 스크립트
# 이 스크립트는 AWS S3 bucket과 ECR registry가 올바르게 구성되었는지 확인합니다.

echo "============================================================"
echo "Lab 1-1 Part 3: AWS 스토리지 확인"
echo "============================================================"

# 환경 변수 확인
if [ -z "$USER_NUM" ]; then
    echo "⚠️  USER_NUM 환경 변수가 설정되지 않았습니다."
    read -p "사용자 번호를 입력하세요 (예: 01, 02, 03...): " USER_NUM
    export USER_NUM
fi

# AWS 자격 증명 확인
echo ""
echo "============================================================"
echo "Step 0: AWS 자격 증명 확인"
echo "============================================================"

if aws sts get-caller-identity > /dev/null 2>&1; then
    echo "✅ AWS 자격 증명 확인 완료"
    aws sts get-caller-identity --query "Account" --output text | xargs -I {} echo "   AWS Account ID: {}"
else
    echo "❌ AWS 자격 증명이 구성되지 않았습니다."
    echo "   'aws configure' 명령으로 AWS 자격 증명을 설정하세요."
    exit 1
fi

# S3 버킷 및 ECR 레지스트리 이름 설정
S3_BUCKET="mlops-training-user${USER_NUM}"
ECR_REGISTRY_PREFIX="mlops-training/user${USER_NUM}"
AWS_REGION="${AWS_REGION:-ap-northeast-2}"

echo ""
echo "📋 확인할 리소스:"
echo "   🪣 S3 Bucket: ${S3_BUCKET}"
echo "   📦 ECR Registry Prefix: ${ECR_REGISTRY_PREFIX}"
echo "   🌏 AWS Region: ${AWS_REGION}"
echo ""

# Step 1: S3 Bucket 확인
echo ""
echo "============================================================"
echo "Step 1: S3 Bucket 확인"
echo "============================================================"

if aws s3 ls "s3://${S3_BUCKET}" --region ${AWS_REGION} > /dev/null 2>&1; then
    echo "✅ S3 Bucket 존재: s3://${S3_BUCKET}"
    
    # 버킷 생성 날짜 확인
    BUCKET_DATE=$(aws s3api list-buckets --query "Buckets[?Name=='${S3_BUCKET}'].CreationDate" --output text 2>/dev/null)
    if [ -n "$BUCKET_DATE" ]; then
        echo "   생성 날짜: ${BUCKET_DATE}"
    fi
    
    # 버킷 리전 확인
    BUCKET_REGION=$(aws s3api get-bucket-location --bucket ${S3_BUCKET} --output text 2>/dev/null)
    if [ -n "$BUCKET_REGION" ] && [ "$BUCKET_REGION" != "None" ]; then
        echo "   리전: ${BUCKET_REGION}"
    else
        echo "   리전: us-east-1 (기본값)"
    fi
    
    # 버킷 내 객체 수 확인 (선택사항)
    OBJECT_COUNT=$(aws s3 ls "s3://${S3_BUCKET}" --recursive 2>/dev/null | wc -l)
    echo "   저장된 객체 수: ${OBJECT_COUNT}"
    
    # 주요 폴더 구조 확인
    echo ""
    echo "   📁 버킷 구조:"
    aws s3 ls "s3://${S3_BUCKET}/" 2>/dev/null | head -10 | while read -r line; do
        echo "      $line"
    done
    
else
    echo "❌ S3 Bucket을 찾을 수 없습니다: s3://${S3_BUCKET}"
    echo ""
    echo "💡 S3 Bucket 생성 방법:"
    echo "   aws s3 mb s3://${S3_BUCKET} --region ${AWS_REGION}"
    echo ""
fi

# Step 2: ECR Registry 확인
echo ""
echo "============================================================"
echo "Step 2: ECR Registry 확인"
echo "============================================================"

# ECR 레지스트리 목록 조회
ECR_REPOS=$(aws ecr describe-repositories --region ${AWS_REGION} 2>/dev/null | \
    jq -r '.repositories[] | select(.repositoryName | startswith("'${ECR_REGISTRY_PREFIX}'")) | .repositoryName' 2>/dev/null)

if [ -n "$ECR_REPOS" ]; then
    echo "✅ ECR Registry 발견:"
    echo ""
    
    # 각 레포지토리 정보 출력
    while IFS= read -r repo; do
        echo "   📦 Repository: ${repo}"
        
        # 레포지토리 URI
        REPO_URI=$(aws ecr describe-repositories --repository-names ${repo} --region ${AWS_REGION} 2>/dev/null | \
            jq -r '.repositories[0].repositoryUri' 2>/dev/null)
        if [ -n "$REPO_URI" ]; then
            echo "      URI: ${REPO_URI}"
        fi
        
        # 생성 날짜
        CREATED_AT=$(aws ecr describe-repositories --repository-names ${repo} --region ${AWS_REGION} 2>/dev/null | \
            jq -r '.repositories[0].createdAt' 2>/dev/null | cut -d'T' -f1)
        if [ -n "$CREATED_AT" ]; then
            echo "      생성 날짜: ${CREATED_AT}"
        fi
        
        # 이미지 개수
        IMAGE_COUNT=$(aws ecr list-images --repository-name ${repo} --region ${AWS_REGION} 2>/dev/null | \
            jq '.imageIds | length' 2>/dev/null)
        if [ -n "$IMAGE_COUNT" ]; then
            echo "      이미지 개수: ${IMAGE_COUNT}"
        fi
        
        # 최근 이미지 태그 (최대 3개)
        RECENT_TAGS=$(aws ecr list-images --repository-name ${repo} --region ${AWS_REGION} 2>/dev/null | \
            jq -r '.imageIds[].imageTag' 2>/dev/null | grep -v "null" | head -3)
        if [ -n "$RECENT_TAGS" ]; then
            echo "      최근 태그:"
            echo "$RECENT_TAGS" | while IFS= read -r tag; do
                echo "         - ${tag}"
            done
        fi
        
        echo ""
    done <<< "$ECR_REPOS"
else
    echo "❌ ECR Registry를 찾을 수 없습니다."
    echo "   검색 패턴: ${ECR_REGISTRY_PREFIX}"
    echo ""
    echo "💡 ECR Repository 생성 방법:"
    echo "   aws ecr create-repository --repository-name ${ECR_REGISTRY_PREFIX}-app --region ${AWS_REGION}"
    echo ""
fi

# Step 3: MLflow Artifacts 폴더 확인
echo ""
echo "============================================================"
echo "Step 3: MLflow Artifacts 폴더 확인"
echo "============================================================"

MLFLOW_PREFIX="mlflow-artifacts"
if aws s3 ls "s3://${S3_BUCKET}/${MLFLOW_PREFIX}/" --region ${AWS_REGION} > /dev/null 2>&1; then
    echo "✅ MLflow Artifacts 폴더 존재: s3://${S3_BUCKET}/${MLFLOW_PREFIX}/"
    
    # Experiment 수 확인
    EXPERIMENT_COUNT=$(aws s3 ls "s3://${S3_BUCKET}/${MLFLOW_PREFIX}/" --region ${AWS_REGION} 2>/dev/null | wc -l)
    echo "   Experiment 수: ${EXPERIMENT_COUNT}"
    
    # 최근 artifacts 확인
    echo ""
    echo "   📊 최근 Experiments:"
    aws s3 ls "s3://${S3_BUCKET}/${MLFLOW_PREFIX}/" --region ${AWS_REGION} 2>/dev/null | head -5 | while read -r line; do
        echo "      $line"
    done
else
    echo "⚠️  MLflow Artifacts 폴더가 아직 생성되지 않았습니다."
    echo "   첫 번째 MLflow 실험 실행 후 자동으로 생성됩니다."
fi

# Step 4: Kubeflow Pipeline Artifacts 폴더 확인
echo ""
echo "============================================================"
echo "Step 4: Kubeflow Pipeline Artifacts 폴더 확인"
echo "============================================================"

PIPELINE_PREFIX="kubeflow-pipeline-artifacts"
if aws s3 ls "s3://${S3_BUCKET}/${PIPELINE_PREFIX}/" --region ${AWS_REGION} > /dev/null 2>&1; then
    echo "✅ Kubeflow Pipeline Artifacts 폴더 존재: s3://${S3_BUCKET}/${PIPELINE_PREFIX}/"
    
    # Pipeline 실행 수 확인
    PIPELINE_COUNT=$(aws s3 ls "s3://${S3_BUCKET}/${PIPELINE_PREFIX}/" --region ${AWS_REGION} 2>/dev/null | wc -l)
    echo "   Pipeline 실행 수: ${PIPELINE_COUNT}"
else
    echo "⚠️  Kubeflow Pipeline Artifacts 폴더가 아직 생성되지 않았습니다."
    echo "   첫 번째 Pipeline 실행 후 자동으로 생성됩니다."
fi

# Step 5: 전체 스토리지 아키텍처 요약
echo ""
echo "============================================================"
echo "Step 5: AWS 스토리지 아키텍처 요약"
echo "============================================================"

echo ""
echo "📊 AWS 스토리지 구성:"
echo ""
echo "  ┌─────────────────────────────────────────────┐"
echo "  │       AWS MLOps Storage Architecture        │"
echo "  ├─────────────────────────────────────────────┤"
echo "  │                                             │"
echo "  │  S3 Bucket (Object Storage)                 │"
echo "  │  ├─ 버킷명: ${S3_BUCKET}                      │"
echo "  │  ├─ 리전: ${AWS_REGION}                      │"
echo "  │  ├─ MLflow Artifacts (모델, 데이터)            │"
echo "  │  └─ Pipeline Artifacts (실행 결과)            │"
echo "  │                                             │"
echo "  │  ECR (Container Registry)                   │"
echo "  │  ├─ Registry Prefix: ${ECR_REGISTRY_PREFIX} │"
echo "  │  ├─ 리전: ${AWS_REGION}                      │"
echo "  │  └─ 용도: ML 컨테이너 이미지 저장                 │"
echo "  │                                             │"
echo "  └─────────────────────────────────────────────┘"
echo ""

# Step 6: 데이터 흐름 설명
echo ""
echo "============================================================"
echo "Step 6: 데이터 흐름"
echo "============================================================"
echo ""
echo "1. 학습 실행"
echo "   └─▶ MLflow Tracking"
echo "       ├─▶ S3: Model 파일, Artifacts 저장"
echo "       └─▶ Metadata: Parameters, Metrics 기록"
echo ""
echo "2. 모델 배포"
echo "   ├─▶ S3: 모델 파일 조회"
echo "   ├─▶ ECR: 컨테이너 이미지 저장"
echo "   └─▶ KServe: 모델 서빙"
echo ""
echo "3. 파이프라인 실행"
echo "   ├─▶ S3: 입력 데이터 읽기"
echo "   ├─▶ ECR: 컴포넌트 이미지 사용"
echo "   └─▶ S3: 결과 저장"
echo ""

# 완료
echo "============================================================"
echo "✅ AWS 스토리지 확인 완료!"
echo "============================================================"
echo ""
echo "💡 다음 단계:"
echo "   1. S3 버킷이 없다면: aws s3 mb s3://${S3_BUCKET} --region ${AWS_REGION}"
echo "   2. ECR 레포지토리가 없다면: aws ecr create-repository --repository-name ${ECR_REGISTRY_PREFIX}*"
echo "   3. Lab 1-2로 진행: Kubeflow Pipeline 실습"
echo ""
