#!/bin/bash

# ============================================================
# Lab 1-1 Part 1: Kubeflow Tenant 검증 스크립트 (최종판)
# ============================================================
# 
# 이 스크립트는 수강생 본인의 Kubeflow 환경이 올바르게 
# 설정되었는지 확인합니다.
#
# 사용법:
#   export USER_NUM="07"  # 본인의 번호
#   ./verify_kubeflow.sh
#
# ============================================================

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "============================================================"
echo "Lab 1-1 Part 1: Kubeflow Tenant 검증"
echo "============================================================"

# ============================================================
# 환경 변수 확인 및 설정
# ============================================================

if [ -z "$USER_NUM" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  USER_NUM 환경 변수가 설정되지 않았습니다.${NC}"
    echo ""
    read -p "사용자 번호를 입력하세요 (예: 01, 02, 03...): " USER_NUM
    export USER_NUM
fi

# 두 자리 숫자로 변환 (01, 02 형식)
USER_NUM=$(printf "%02d" $USER_NUM 2>/dev/null)

if [ -z "$USER_NUM" ] || [ "$USER_NUM" == "00" ]; then
    echo -e "${RED}❌ 올바른 사용자 번호를 입력하세요.${NC}"
    exit 1
fi

NAMESPACE="kubeflow-user${USER_NUM}"
PROFILE_NAME="kubeflow-user${USER_NUM}"
USER_EMAIL="user${USER_NUM}@mlops.local"

echo ""
echo -e "${CYAN}📋 검증 정보:${NC}"
echo "   👤 사용자 번호: ${USER_NUM}"
echo "   📁 네임스페이스: ${NAMESPACE}"
echo "   📋 프로필명: ${PROFILE_NAME}"
echo "   📧 이메일: ${USER_EMAIL}"
echo ""

# 검증 결과 카운터
pass=0
fail=0
warn=0

# ============================================================
# Step 1: Namespace 존재 및 이름 확인 (중요!)
# ============================================================

echo ""
echo "============================================================"
echo "Step 1: Namespace 존재 및 이름 확인"
echo "============================================================"

if kubectl get namespace $NAMESPACE > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Namespace 존재: ${NAMESPACE}${NC}"
    
    # Namespace 생성 날짜 확인
    CREATION_TIME=$(kubectl get namespace $NAMESPACE -o jsonpath='{.metadata.creationTimestamp}')
    echo "   생성 날짜: ${CREATION_TIME}"
    
    # Namespace 레이블 확인
    echo "   주요 레이블:"
    kubectl get namespace $NAMESPACE -o jsonpath='{.metadata.labels}' | \
        jq -r 'to_entries[] | "      \(.key): \(.value)"' 2>/dev/null || \
        kubectl get namespace $NAMESPACE -o jsonpath='{.metadata.labels}'
    
    ((pass++))
else
    echo -e "${RED}❌ Namespace를 찾을 수 없습니다: ${NAMESPACE}${NC}"
    echo ""
    echo -e "${YELLOW}문제 해결:${NC}"
    echo "   1. 사용자 번호가 올바른지 확인하세요."
    echo "   2. 강사에게 Namespace 생성을 요청하세요."
    echo ""
    ((fail++))
fi

# ============================================================
# Step 2: Profile 존재 및 이름 일치 확인 (중요!)
# ============================================================

echo ""
echo "============================================================"
echo "Step 2: Profile 존재 및 이름 일치 확인"
echo "============================================================"

if kubectl get profile $PROFILE_NAME > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Profile 존재: ${PROFILE_NAME}${NC}"
    
    # Profile과 Namespace 이름 일치 확인
    if [ "$PROFILE_NAME" == "$NAMESPACE" ]; then
        echo -e "${GREEN}✅ Profile과 Namespace 이름이 일치합니다.${NC}"
        echo "   Profile: ${PROFILE_NAME}"
        echo "   Namespace: ${NAMESPACE}"
    else
        echo -e "${RED}❌ Profile과 Namespace 이름이 일치하지 않습니다!${NC}"
        echo "   Profile: ${PROFILE_NAME}"
        echo "   Namespace: ${NAMESPACE}"
        echo ""
        echo -e "${YELLOW}문제 해결:${NC}"
        echo "   강사에게 Profile 이름 불일치 문제를 알려주세요."
        ((fail++))
    fi
    
    # Profile 상태 확인
    PROFILE_STATUS=$(kubectl get profile $PROFILE_NAME -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)
    PROFILE_REASON=$(kubectl get profile $PROFILE_NAME -o jsonpath='{.status.conditions[?(@.type=="Ready")].reason}' 2>/dev/null)
    PROFILE_MESSAGE=$(kubectl get profile $PROFILE_NAME -o jsonpath='{.status.conditions[?(@.type=="Ready")].message}' 2>/dev/null)
    
    if [ "$PROFILE_STATUS" == "True" ]; then
        echo -e "   상태: ${GREEN}Ready${NC}"
        ((pass++))
    elif [ -z "$PROFILE_STATUS" ]; then
        echo -e "   상태: ${YELLOW}NO STATUS (Profile Controller가 처리 중)${NC}"
        echo ""
        echo -e "${BLUE}ℹ️  참고:${NC}"
        echo "   Profile Status가 없어도 ServiceAccount와 RoleBinding이 생성되면"
        echo "   실습을 진행할 수 있습니다. 아래 단계를 계속 확인하세요."
        ((warn++))
    else
        echo -e "   상태: ${RED}${PROFILE_STATUS}${NC}"
        echo "   이유: ${PROFILE_REASON}"
        echo "   메시지: ${PROFILE_MESSAGE}"
        echo ""
        echo -e "${YELLOW}문제 해결:${NC}"
        echo "   1. 잠시 후 다시 스크립트를 실행해보세요 (Profile Controller 처리 중)"
        echo "   2. 계속 Not Ready라면 강사에게 문의하세요."
        ((warn++))
    fi
    
    # Owner 확인
    OWNER=$(kubectl get profile $PROFILE_NAME -o jsonpath='{.spec.owner.name}')
    if [ "$OWNER" == "$USER_EMAIL" ]; then
        echo -e "   Owner: ${GREEN}${OWNER}${NC} ✓"
    else
        echo -e "   Owner: ${YELLOW}${OWNER}${NC}"
        echo "   예상: ${USER_EMAIL}"
    fi
    
    # Resource Quota 스펙 확인
    echo "   Resource Quota Spec:"
    kubectl get profile $PROFILE_NAME -o jsonpath='{.spec.resourceQuotaSpec.hard}' | \
        jq -r 'to_entries[] | "      \(.key): \(.value)"' 2>/dev/null || \
        echo "      설정되지 않음"
    
else
    echo -e "${RED}❌ Profile을 찾을 수 없습니다: ${PROFILE_NAME}${NC}"
    echo ""
    echo -e "${YELLOW}문제 해결:${NC}"
    echo "   1. Profile 목록 확인: kubectl get profiles"
    echo "   2. 다른 이름으로 Profile이 생성되었는지 확인하세요."
    echo "      예: profile-user${USER_NUM} (구 이름 형식)"
    echo "   3. 강사에게 Profile 생성을 요청하세요."
    echo ""
    ((fail++))
fi

# ============================================================
# Step 3: ServiceAccount 확인 (필수!)
# ============================================================

echo ""
echo "============================================================"
echo "Step 3: ServiceAccount 확인"
echo "============================================================"

SERVICE_ACCOUNTS=("default-editor" "default-viewer")
SA_FOUND=0

for sa in "${SERVICE_ACCOUNTS[@]}"; do
    if kubectl get serviceaccount $sa -n $NAMESPACE > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ServiceAccount 존재: ${sa}${NC}"
        
        # ServiceAccount 세부 정보
        SA_AGE=$(kubectl get serviceaccount $sa -n $NAMESPACE -o jsonpath='{.metadata.creationTimestamp}')
        echo "   생성 시간: ${SA_AGE}"
        
        ((SA_FOUND++))
    else
        echo -e "${RED}❌ ServiceAccount를 찾을 수 없습니다: ${sa}${NC}"
    fi
done

if [ $SA_FOUND -eq 2 ]; then
    echo ""
    echo -e "${GREEN}✅ 모든 ServiceAccount가 정상적으로 생성되었습니다.${NC}"
    ((pass++))
elif [ $SA_FOUND -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  일부 ServiceAccount가 누락되었습니다.${NC}"
    echo ""
    echo -e "${YELLOW}문제 해결:${NC}"
    echo "   1. Profile이 Ready 상태가 되면 자동으로 생성됩니다."
    echo "   2. 잠시 후 다시 확인해보세요: ./verify_kubeflow.sh"
    echo "   3. 계속 누락되면 강사에게 문의하세요."
    ((warn++))
else
    echo ""
    echo -e "${RED}❌ ServiceAccount가 생성되지 않았습니다.${NC}"
    echo ""
    echo -e "${YELLOW}가능한 원인:${NC}"
    echo "   1. Profile이 아직 Ready 상태가 아님"
    echo "   2. Profile Controller가 처리 중"
    echo "   3. Profile과 Namespace 이름 불일치"
    echo ""
    echo -e "${YELLOW}문제 해결:${NC}"
    echo "   1. 위의 Profile 상태를 확인하세요."
    echo "   2. 5분 후 다시 스크립트를 실행해보세요."
    echo "   3. 강사에게 다음 정보를 전달하세요:"
    echo "      - Profile: ${PROFILE_NAME}"
    echo "      - Namespace: ${NAMESPACE}"
    echo "      - Profile Status: ${PROFILE_STATUS}"
    ((fail++))
fi

# ============================================================
# Step 4: ResourceQuota 확인
# ============================================================

echo ""
echo "============================================================"
echo "Step 4: ResourceQuota 확인"
echo "============================================================"

QUOTA_COUNT=$(kubectl get resourcequota -n $NAMESPACE --no-headers 2>/dev/null | wc -l)

if [ $QUOTA_COUNT -gt 0 ]; then
    echo -e "${GREEN}✅ ResourceQuota 설정됨: ${QUOTA_COUNT}개${NC}"
    echo ""
    echo "   ResourceQuota 상세:"
    kubectl get resourcequota -n $NAMESPACE -o custom-columns=\
NAME:.metadata.name,\
CPU-LIMIT:.spec.hard.cpu,\
CPU-USED:.status.used.cpu,\
MEM-LIMIT:.spec.hard.memory,\
MEM-USED:.status.used.memory
    
    echo ""
    echo "   현재 사용률:"
    CPU_LIMIT=$(kubectl get resourcequota -n $NAMESPACE -o jsonpath='{.items[0].spec.hard.cpu}' 2>/dev/null)
    CPU_USED=$(kubectl get resourcequota -n $NAMESPACE -o jsonpath='{.items[0].status.used.cpu}' 2>/dev/null || echo "0")
    MEM_LIMIT=$(kubectl get resourcequota -n $NAMESPACE -o jsonpath='{.items[0].spec.hard.memory}' 2>/dev/null)
    MEM_USED=$(kubectl get resourcequota -n $NAMESPACE -o jsonpath='{.items[0].status.used.memory}' 2>/dev/null || echo "0")
    
    echo "   CPU: ${CPU_USED:-0} / ${CPU_LIMIT}"
    echo "   Memory: ${MEM_USED:-0} / ${MEM_LIMIT}"
    
    ((pass++))
else
    echo -e "${YELLOW}⚠️  ResourceQuota가 설정되지 않았습니다.${NC}"
    echo ""
    echo -e "${YELLOW}문제 해결:${NC}"
    echo "   1. Profile spec에 resourceQuotaSpec이 정의되어 있는지 확인"
    echo "   2. Profile이 Ready 상태가 되면 자동으로 생성됩니다."
    ((warn++))
fi

# ============================================================
# Step 5: RoleBinding 확인 (필수!)
# ============================================================

echo ""
echo "============================================================"
echo "Step 5: RoleBinding 확인"
echo "============================================================"

RB_COUNT=$(kubectl get rolebinding -n $NAMESPACE --no-headers 2>/dev/null | wc -l)

if [ $RB_COUNT -gt 0 ]; then
    echo -e "${GREEN}✅ RoleBinding 설정됨: ${RB_COUNT}개${NC}"
    echo ""
    echo "   RoleBinding 목록:"
    kubectl get rolebinding -n $NAMESPACE -o custom-columns=\
NAME:.metadata.name,\
ROLE:.roleRef.name,\
SUBJECTS:.subjects[*].name
    
    # 필수 RoleBinding 확인
    REQUIRED_RB=("namespaceAdmin")
    for rb in "${REQUIRED_RB[@]}"; do
        if kubectl get rolebinding $rb -n $NAMESPACE > /dev/null 2>&1; then
            echo -e "   ${GREEN}✓${NC} 필수 RoleBinding 존재: ${rb}"
        else
            echo -e "   ${YELLOW}⚠${NC} 권장 RoleBinding 누락: ${rb}"
        fi
    done
    
    ((pass++))
else
    echo -e "${RED}❌ RoleBinding을 찾을 수 없습니다.${NC}"
    echo ""
    echo -e "${YELLOW}문제 해결:${NC}"
    echo "   1. ServiceAccount가 먼저 생성되어야 RoleBinding이 생성됩니다."
    echo "   2. Profile이 Ready 상태가 되면 자동으로 생성됩니다."
    echo "   3. 강사에게 RBAC 설정을 문의하세요."
    echo ""
    ((fail++))
fi

# ============================================================
# Step 6: PodDefault 확인 (실습 환경)
# ============================================================

echo ""
echo "============================================================"
echo "Step 6: PodDefault 확인 (실습 환경 설정)"
echo "============================================================"

PD_COUNT=$(kubectl get poddefaults -n $NAMESPACE --no-headers 2>/dev/null | wc -l)

if [ $PD_COUNT -gt 0 ]; then
    echo -e "${GREEN}✅ PodDefault 설정됨: ${PD_COUNT}개${NC}"
    echo ""
    echo "   PodDefault 목록:"
    kubectl get poddefaults -n $NAMESPACE -o custom-columns=\
NAME:.metadata.name,\
DESC:.spec.desc
    
    # 필수 PodDefault 확인
    REQUIRED_PD=("access-mlflow" "access-ml-pipeline")
    echo ""
    echo "   실습 환경 체크:"
    for pd in "${REQUIRED_PD[@]}"; do
        if kubectl get poddefault $pd -n $NAMESPACE > /dev/null 2>&1; then
            echo -e "   ${GREEN}✓${NC} ${pd}"
        else
            echo -e "   ${YELLOW}⚠${NC} ${pd} (누락 - 실습에 영향)"
        fi
    done
    
    ((pass++))
else
    echo -e "${YELLOW}⚠️  PodDefault가 설정되지 않았습니다.${NC}"
    echo ""
    echo -e "${BLUE}ℹ️  영향:${NC}"
    echo "   - Jupyter Notebook 생성 시 MLflow, Pipeline 접근 설정이 자동 적용되지 않습니다."
    echo "   - 실습 진행은 가능하지만 일부 기능 사용에 제약이 있을 수 있습니다."
    echo ""
    echo -e "${YELLOW}문제 해결:${NC}"
    echo "   강사에게 PodDefault 생성을 요청하세요."
    ((warn++))
fi

# ============================================================
# Step 7: 네임스페이스 내 리소스 확인
# ============================================================

echo ""
echo "============================================================"
echo "Step 7: 네임스페이스 내 리소스 확인"
echo "============================================================"

POD_COUNT=$(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
SERVICE_COUNT=$(kubectl get services -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
PVC_COUNT=$(kubectl get pvc -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
CONFIGMAP_COUNT=$(kubectl get configmaps -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
SECRET_COUNT=$(kubectl get secrets -n $NAMESPACE --no-headers 2>/dev/null | wc -l)

echo "   현재 리소스 상태:"
echo "   📦 Pods: ${POD_COUNT}개"
echo "   🔧 Services: ${SERVICE_COUNT}개"
echo "   💾 PersistentVolumeClaims: ${PVC_COUNT}개"
echo "   ⚙️  ConfigMaps: ${CONFIGMAP_COUNT}개"
echo "   🔒 Secrets: ${SECRET_COUNT}개"

if [ $POD_COUNT -gt 0 ]; then
    echo ""
    echo "   실행 중인 Pod 목록:"
    kubectl get pods -n $NAMESPACE -o custom-columns=\
NAME:.metadata.name,\
STATUS:.status.phase,\
AGE:.metadata.creationTimestamp
fi

# ============================================================
# Step 8: 권한 격리 테스트
# ============================================================

echo ""
echo "============================================================"
echo "Step 8: 권한 격리 테스트"
echo "============================================================"

# 다른 사용자의 네임스페이스 선택
if [ "$USER_NUM" == "01" ]; then
    TEST_NAMESPACE="kubeflow-user02"
else
    TEST_NAMESPACE="kubeflow-user01"
fi

echo "   테스트: 다른 사용자 네임스페이스 접근 시도"
echo "   대상: ${TEST_NAMESPACE}"

if kubectl get pods -n $TEST_NAMESPACE > /dev/null 2>&1; then
    echo -e "   ${YELLOW}⚠️  다른 네임스페이스에 접근 가능합니다.${NC}"
    echo ""
    echo -e "${BLUE}ℹ️  참고:${NC}"
    echo "   현재 관리자 권한으로 실행 중이거나 RBAC 설정이 완료되지 않았습니다."
    echo "   수강생 환경에서는 접근이 차단되어야 정상입니다."
    ((warn++))
else
    echo -e "   ${GREEN}✅ 다른 네임스페이스 접근이 차단되었습니다 (정상).${NC}"
    ((pass++))
fi

# ============================================================
# Step 9: Kubeflow 주요 컴포넌트 확인
# ============================================================

echo ""
echo "============================================================"
echo "Step 9: Kubeflow 주요 컴포넌트 확인"
echo "============================================================"

echo "   Kubeflow 시스템 컴포넌트 상태:"

# kubeflow namespace 확인
if kubectl get namespace kubeflow > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ kubeflow namespace${NC}"
else
    echo -e "   ${RED}❌ kubeflow namespace 없음${NC}"
    ((fail++))
fi

# Central Dashboard 확인
if kubectl get deployment centraldashboard -n kubeflow > /dev/null 2>&1; then
    DASH_READY=$(kubectl get deployment centraldashboard -n kubeflow -o jsonpath='{.status.readyReplicas}')
    DASH_TOTAL=$(kubectl get deployment centraldashboard -n kubeflow -o jsonpath='{.spec.replicas}')
    if [ "$DASH_READY" == "$DASH_TOTAL" ]; then
        echo -e "   ${GREEN}✅ Central Dashboard (${DASH_READY}/${DASH_TOTAL})${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Central Dashboard (${DASH_READY}/${DASH_TOTAL})${NC}"
    fi
else
    echo -e "   ${YELLOW}⚠️  Central Dashboard 없음${NC}"
fi

# Kubeflow Pipelines UI 확인
if kubectl get service ml-pipeline-ui -n kubeflow > /dev/null 2>&1; then
    PIPELINE_PORT=$(kubectl get service ml-pipeline-ui -n kubeflow -o jsonpath='{.spec.ports[0].port}')
    echo -e "   ${GREEN}✅ Kubeflow Pipelines UI (포트: ${PIPELINE_PORT})${NC}"
else
    echo -e "   ${YELLOW}⚠️  Kubeflow Pipelines UI 없음${NC}"
fi

# Notebook Controller 확인
if kubectl get deployment notebook-controller-deployment -n kubeflow > /dev/null 2>&1; then
    NB_READY=$(kubectl get deployment notebook-controller-deployment -n kubeflow -o jsonpath='{.status.readyReplicas}')
    NB_TOTAL=$(kubectl get deployment notebook-controller-deployment -n kubeflow -o jsonpath='{.spec.replicas}')
    if [ "$NB_READY" == "$NB_TOTAL" ]; then
        echo -e "   ${GREEN}✅ Notebook Controller (${NB_READY}/${NB_TOTAL})${NC}"
        ((pass++))
    else
        echo -e "   ${YELLOW}⚠️  Notebook Controller (${NB_READY}/${NB_TOTAL})${NC}"
        ((warn++))
    fi
else
    echo -e "   ${RED}❌ Notebook Controller 없음${NC}"
    ((fail++))
fi

# ============================================================
# Step 10: 실습 가능 여부 최종 판단
# ============================================================

echo ""
echo "============================================================"
echo "Step 10: 실습 가능 여부 판단"
echo "============================================================"

# 필수 요구사항 체크
READY_FOR_LAB=true

echo "   필수 요구사항 체크:"
echo ""

# 1. Namespace 존재
if kubectl get namespace $NAMESPACE > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} Namespace 존재"
else
    echo -e "   ${RED}✗${NC} Namespace 없음"
    READY_FOR_LAB=false
fi

# 2. ServiceAccount 존재 (최소 1개)
if [ $SA_FOUND -gt 0 ]; then
    echo -e "   ${GREEN}✓${NC} ServiceAccount 생성됨 (${SA_FOUND}/2)"
else
    echo -e "   ${RED}✗${NC} ServiceAccount 없음"
    READY_FOR_LAB=false
fi

# 3. RoleBinding 존재
if [ $RB_COUNT -gt 0 ]; then
    echo -e "   ${GREEN}✓${NC} RoleBinding 설정됨"
else
    echo -e "   ${RED}✗${NC} RoleBinding 없음"
    READY_FOR_LAB=false
fi

# 4. Kubeflow 시스템 정상
if kubectl get deployment notebook-controller-deployment -n kubeflow > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} Kubeflow 시스템 정상"
else
    echo -e "   ${RED}✗${NC} Kubeflow 시스템 문제"
    READY_FOR_LAB=false
fi

echo ""
if [ "$READY_FOR_LAB" = true ]; then
    echo -e "${GREEN}✅ 실습 진행 가능!${NC}"
    echo ""
    echo "   Jupyter Notebook을 생성하여 실습을 시작할 수 있습니다."
else
    echo -e "${RED}❌ 실습 진행 불가${NC}"
    echo ""
    echo "   필수 요구사항이 충족되지 않았습니다."
    echo "   강사에게 문의하여 환경 설정을 완료하세요."
fi

# ============================================================
# Kubeflow Tenant 아키텍처 요약
# ============================================================

echo ""
echo "============================================================"
echo "Kubeflow Tenant 아키텍처 요약"
echo "============================================================"

echo ""
echo "📊 Tenant 구성:"
echo ""
cat <<EOF
  ┌─────────────────────────────────────────────┐
  │       Kubeflow Multi-Tenant Architecture    │
  ├─────────────────────────────────────────────┤
  │                                             │
  │  사용자: user${USER_NUM}                              │
  │  ├─ Namespace: ${NAMESPACE}         │
  │  ├─ Profile: ${PROFILE_NAME}        │
  │  ├─ ServiceAccounts: ${SA_FOUND}/2 (editor, viewer)  │
  │  ├─ ResourceQuota: ${QUOTA_COUNT}개                      │
  │  ├─ RoleBindings: ${RB_COUNT}개                    │
  │  └─ PodDefaults: ${PD_COUNT}개                 │
  │                                             │
  │  리소스:                                    │
  │  ├─ Pods: ${POD_COUNT}개                             │
  │  ├─ Services: ${SERVICE_COUNT}개                        │
  │  ├─ PVCs: ${PVC_COUNT}개                            │
  │  └─ Secrets: ${SECRET_COUNT}개                         │
  │                                             │
EOF

if [ "$READY_FOR_LAB" = true ]; then
    echo "  │  상태: ✅ 실습 가능                          │"
else
    echo "  │  상태: ❌ 실습 불가 (설정 필요)              │"
fi

echo "  │                                             │"
echo "  └─────────────────────────────────────────────┘"

# ============================================================
# 검증 결과 요약
# ============================================================

echo ""
echo ""
echo "============================================================"
echo "검증 결과 요약"
echo "============================================================"
echo ""

total=$((pass + fail + warn))
echo "  ✅ 통과: ${pass}"
echo "  ❌ 실패: ${fail}"
echo "  ⚠️  경고: ${warn}"
echo "  📊 총점: ${pass}/${total}"
echo ""

# 결과에 따른 메시지
if [ $fail -eq 0 ] && [ $warn -eq 0 ]; then
    echo -e "${GREEN}🎉 모든 검증을 완벽하게 통과했습니다!${NC}"
    echo ""
    echo "다음 단계: Lab 1-1 Part 2 (Jupyter Notebook 생성)로 진행하세요."
    
elif [ $fail -eq 0 ]; then
    echo -e "${GREEN}✅ 필수 검증을 모두 통과했습니다!${NC}"
    echo ""
    echo "⚠️  일부 경고 사항이 있지만 실습 진행에는 문제없습니다."
    echo "다음 단계: Lab 1-1 Part 2 (Jupyter Notebook 생성)로 진행하세요."
    
else
    echo -e "${RED}❌ 일부 필수 항목이 충족되지 않았습니다.${NC}"
    echo ""
    echo "문제 해결 가이드:"
    echo ""
    
    # Profile 문제
    if ! kubectl get profile $PROFILE_NAME > /dev/null 2>&1; then
        echo "1. Profile 생성 문제:"
        echo "   - 강사에게 Profile 생성을 요청하세요."
        echo "   - Profile 이름: ${PROFILE_NAME}"
        echo ""
    fi
    
    # ServiceAccount 문제
    if [ $SA_FOUND -eq 0 ]; then
        echo "2. ServiceAccount 생성 문제:"
        echo "   - Profile이 Ready 상태가 되어야 자동 생성됩니다."
        echo "   - 5분 후 다시 검증 스크립트를 실행해보세요."
        echo "   - 계속 실패하면 강사에게 문의하세요."
        echo ""
    fi
    
    # RoleBinding 문제
    if [ $RB_COUNT -eq 0 ]; then
        echo "3. RoleBinding 설정 문제:"
        echo "   - 강사에게 RBAC 설정을 요청하세요."
        echo ""
    fi
    
    echo "🆘 강사 문의 시 제공할 정보:"
    echo "   - 사용자 번호: ${USER_NUM}"
    echo "   - Namespace: ${NAMESPACE}"
    echo "   - Profile: ${PROFILE_NAME}"
    echo "   - 검증 결과: 통과 ${pass}/${total}"
fi

echo ""
echo "============================================================"
echo "추가 명령어"
echo "============================================================"
echo ""
echo "📌 유용한 명령어:"
echo ""
echo "  # Profile 상세 정보 확인"
echo "  kubectl get profile ${PROFILE_NAME} -o yaml"
echo ""
echo "  # Namespace 리소스 전체 보기"
echo "  kubectl get all -n ${NAMESPACE}"
echo ""
echo "  # 이벤트 로그 확인 (문제 진단)"
echo "  kubectl get events -n ${NAMESPACE} --sort-by='.lastTimestamp'"
echo ""
echo "  # Kubeflow Dashboard 접속"
echo "  kubectl port-forward -n istio-system svc/istio-ingressgateway 8080:80"
echo "  # 브라우저: http://localhost:8080"
echo ""
echo "============================================================"

# 스크립트 종료 코드 반환
if [ "$READY_FOR_LAB" = true ]; then
    exit 0
else
    exit 1
fi
