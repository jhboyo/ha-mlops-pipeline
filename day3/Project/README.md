# 🎯 조별 프로젝트: E2E MLOps Pipeline

## 개요

3일간 학습한 MLOps 기술을 종합하여 **완전한 E2E(End-to-End) ML 파이프라인**을 구축하는 조별 프로젝트입니다.

### 학습 목표

- Kubeflow Pipelines을 활용한 ML 워크플로우 자동화
- MLflow를 통한 실험 추적 및 모델 관리
- 피처 엔지니어링을 통한 모델 성능 개선
- KServe를 활용한 모델 배포 (선택)

### 실습 시간

| 파트 | 내용 | 시간 |
|------|------|------|
| Part 1 | E2E Pipeline 이해 및 실행 | 50분 |
| Part 2 | 조별 프로젝트 구현 | 50분 |
| Part 3 | 발표 및 피드백 | 40분 |
| **총** | | **140분** |

---

## 📋 평가 기준

### 필수 요구사항 (70점)

| 항목 | 배점 | 기준 |
|------|------|------|
| Kubeflow Pipeline | 40점 | 최소 5개 컴포넌트, Succeeded 상태 |
| MLflow Tracking | 20점 | 최소 2회 Run, 파라미터/메트릭 기록 |
| Feature Engineering | 10점 | 1개 이상 파생 피처 생성 |

### 선택 요구사항 (30점)

| 항목 | 배점 | 기준 |
|------|------|------|
| KServe 배포 | 25점 | InferenceService 생성 및 API 테스트 |
| Canary 배포 | 5점 (보너스) | 트래픽 분할 적용 |

---

## 🏗️ 파이프라인 아키텍처

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│  Load Data  │────▶│ Preprocess  │────▶│ Feature Engineer │
│  (sklearn)  │     │ (split/scale)│     │ (파생변수 생성)   │
└─────────────┘     └─────────────┘     └──────────────────┘
                                                  │
                                                  ▼
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│   Deploy    │◀────│  Evaluate   │◀────│   Train Model    │
│  (KServe)   │     │ (threshold) │     │ (RF + MLflow)    │
└─────────────┘     └─────────────┘     └──────────────────┘
       │                  │
       │                  ▼
       │            ┌─────────────┐
       │            │ Send Alert  │
       │            │ (성능 미달)  │
       │            └─────────────┘
       ▼
  ┌─────────────────────────────────────┐
  │  InferenceService (REST API)        │
  │  POST /v1/models/{name}:predict     │
  └─────────────────────────────────────┘
```

---

## 🚀 실습 가이드

### 사전 준비

```bash
# 1. 환경 변수 설정
export USER_NUM="01"  # 본인 번호로 변경
export NAMESPACE="kubeflow-user${USER_NUM}"

# 2. MLflow URI 설정
export MLFLOW_TRACKING_URI="http://mlflow-server-service.mlflow-system.svc.cluster.local:5000"

# 3. 패키지 설치
cd project
pip install -r requirements.txt
```

### Part 1: E2E Pipeline 이해 (50분)

#### Step 1: 예제 파이프라인 컴파일

```bash
cd scripts
python 1_e2e_pipeline.py
```

생성된 파일: `e2e_pipeline.yaml`

#### Step 2: Kubeflow UI에서 실행

1. Kubeflow UI 접속 → **Pipelines** → **Upload pipeline**
2. `e2e_pipeline.yaml` 업로드
3. **Create Run** → Parameters 설정:

| Parameter | 값 |
|-----------|-----|
| data_source | sklearn |
| experiment_name | e2e-pipeline-user01 |
| model_name | california-model-user01 |
| namespace | ⚠️ **현재 Kubeflow 프로필 네임스페이스와 동일하게 설정** |
| n_estimators | 100 |
| max_depth | 10 |
| r2_threshold | 0.75 |

> ⚠️ **중요**: `namespace` 파라미터는 현재 로그인한 Kubeflow 프로필의 네임스페이스와 **동일해야** 합니다. 
> 예: `kubeflow-user-example-com` 프로필이면 namespace도 `kubeflow-user-example-com`

#### Step 3: 실행 모니터링

- **Kubeflow UI** → Runs → 파이프라인 그래프 확인
- **MLflow UI** → Experiments → 메트릭/파라미터 확인

---

### Part 2: 조별 프로젝트 (50분)

#### Step 1: 프로젝트 파이프라인 복사

```bash
cp scripts/2_project_pipeline.py my_team_pipeline.py
```

#### Step 2: 팀 설정 변경

```bash
# macOS
sed -i '' 's/team-XX/team-01/g' my_team_pipeline.py

# Linux
sed -i 's/team-XX/team-01/g' my_team_pipeline.py
```

또는 직접 파일 수정:
```python
TEAM_NAME = "team-01"           # 팀명으로 변경
USER_NAMESPACE = "kubeflow-user-example-com"  # 본인 네임스페이스
```

#### Step 3: 피처 엔지니어링 구현 ⭐

`feature_engineering` 함수에서 창의적인 파생 변수를 추가하세요:

```python
def add_features(df):
    df = df.copy()
    
    # 예시 1: 방당 침실 비율
    df['bedroom_ratio'] = df['AveBedrms'] / (df['AveRooms'] + 1e-6)
    
    # 예시 2: 가구당 인구
    df['people_per_household'] = df['Population'] / (df['AveOccup'] + 1e-6)
    
    # 예시 3: Bay Area까지 거리 (위치 기반)
    bay_lat, bay_long = 37.77, -122.42
    df['dist_to_bay'] = np.sqrt(
        (df['Latitude'] - bay_lat)**2 + 
        (df['Longitude'] - bay_long)**2
    )
    
    # TODO: 팀에서 추가 피처 구현!
    
    return df
```

#### Step 4: 컴파일 및 실행

```bash
python my_team_pipeline.py
# 생성: team-01_pipeline.yaml

# Kubeflow UI에서 업로드 및 실행
```

---

### Part 3: 발표 (40분)

#### 발표 형식 (팀당 15분)

1. **팀 소개** (1분)
2. **아키텍처** (2분) - 파이프라인 구조 설명
3. **구현 하이라이트** (4분) - Feature Engineering 중심
4. **데모** (4분)
   - Kubeflow UI 결과
   - MLflow UI 결과
   - (선택) API 테스트
5. **트러블슈팅** (1분) - 겪은 문제와 해결 방법
6. **Q&A** (3분)

---

## 🔧 트러블슈팅 가이드

### 1. S3 Bucket 관련 오류

#### 증상
```
botocore.errorfactory.NoSuchBucket: The specified bucket does not exist
```

또는

```
AccessDenied: User is not authorized to perform: s3:PutObject
```

#### 원인
MLflow가 artifact(모델, 피처 중요도 등)를 S3에 저장하려 할 때 버킷이 없거나 권한이 없는 경우

#### 해결 방법

**방법 1**: S3 artifact 저장 비활성화 (권장)

본 실습 코드는 이미 S3 저장을 비활성화했습니다:
```python
# 아래 코드들은 S3 권한이 필요하므로 제거됨
# mlflow.log_dict(feature_importance, "feature_importance.json")
# mlflow.sklearn.log_model(model, "model")

# 대신 메트릭으로 기록
for feat, imp in sorted_importance[:5]:
    mlflow.log_metric(f"importance_{feat}", imp)
```

**방법 2**: IAM 정책 추가 (관리자용)
```bash
aws iam put-role-policy \
    --role-name <EKS_NODE_ROLE_NAME> \
    --policy-name MLflowS3Access \
    --policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
            "Resource": "arn:aws:s3:::YOUR-BUCKET/*"
        }]
    }'
```

---

### 2. RBAC 권한 오류 (KServe 배포 실패)

#### 증상
```
Forbidden: User "system:serviceaccount:kubeflow-user-example-com:default-editor" 
cannot delete/create resource "inferenceservices" in namespace "kubeflow-user01"
```

#### 원인
파이프라인 실행 네임스페이스와 KServe 배포 대상 네임스페이스가 다른 경우

#### 해결 방법

**방법 1**: 같은 네임스페이스 사용 (권장)

파이프라인 실행 시 `namespace` 파라미터를 **현재 Kubeflow 프로필 네임스페이스**와 동일하게 설정:

```
현재 프로필: kubeflow-user-example-com
→ namespace 파라미터: kubeflow-user-example-com
```

**방법 2**: RBAC 권한 추가 (관리자용)
```bash
# KServe 권한 ClusterRole 생성
kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kserve-admin
rules:
- apiGroups: ["serving.kserve.io"]
  resources: ["inferenceservices"]
  verbs: ["*"]
EOF

# RoleBinding 생성
kubectl create rolebinding kserve-access \
  --clusterrole=kserve-admin \
  --serviceaccount=kubeflow-user-example-com:default-editor \
  --namespace=kubeflow-user01
```

---

### 3. 컴포넌트 데이터 전달 오류

#### 증상
```
TypeError: expected string or bytes-like object
```

#### 원인
컴포넌트 간 output 연결 시 `.output` 또는 `.outputs["name"]` 누락

#### 해결 방법
```python
# ❌ 잘못된 방법
train_task = train_model(X_train=preprocess_task)

# ✅ 올바른 방법
train_task = train_model(X_train=preprocess_task.outputs["X_train_out"])
```

---

### 4. MLflow 연결 오류

#### 증상
```
ConnectionError: HTTPConnectionPool
```

#### 해결 방법
```python
# 컴포넌트 내부에서 환경 변수 설정
import os
os.environ['MLFLOW_TRACKING_URI'] = mlflow_tracking_uri
mlflow.set_tracking_uri(mlflow_tracking_uri)
```

---

### 5. 파이프라인 부분 재실행

#### 방법: Retry 버튼
- Kubeflow UI → Runs → 실패한 Run 선택 → **Retry** 클릭
- 캐싱이 활성화된 경우, 성공한 단계는 건너뜀

#### 방법: Clone Run
- 실패한 Run에서 **Clone run** 클릭
- 파라미터 수정 후 재실행

---

## 📁 파일 구조

```
project/
├── README.md                    # 이 파일
├── requirements.txt             # Python 패키지
├── scripts/
│   ├── 1_e2e_pipeline.py       # E2E 파이프라인 (예제)
│   ├── 2_project_pipeline.py   # 프로젝트 템플릿
│   └── 3_test_deployment.py    # 배포 테스트
├── notebooks/
│   └── project_pipeline.ipynb  # Jupyter Notebook 버전
└── solution/
    └── project_solution.py     # 솔루션 (발표 후 공개)
```

---

## 📊 데이터셋: California Housing

| 피처 | 설명 | 단위 |
|------|------|------|
| MedInc | 중위 소득 | $10,000 |
| HouseAge | 중위 주택 연령 | 년 |
| AveRooms | 평균 방 수 | 개 |
| AveBedrms | 평균 침실 수 | 개 |
| Population | 블록 그룹 인구 | 명 |
| AveOccup | 평균 거주자 수 | 명 |
| Latitude | 위도 | 도 |
| Longitude | 경도 | 도 |
| **MedHouseVal** | 중위 주택 가격 (타겟) | $100,000 |

- 총 샘플 수: 20,640개
- Train/Test 분할: 80/20

---

## ✅ 체크리스트

### 파이프라인 실행 전
- [ ] 팀명 설정 완료 (TEAM_NAME)
- [ ] 네임스페이스 설정 확인 (현재 프로필과 동일)
- [ ] 피처 엔지니어링 구현 (최소 1개)

### 파이프라인 실행 후
- [ ] 모든 컴포넌트 Succeeded 상태
- [ ] MLflow에 Run 기록 확인
- [ ] (선택) KServe InferenceService 생성 확인

### 발표 전
- [ ] 데모 시나리오 준비
- [ ] 트러블슈팅 경험 정리
- [ ] Q&A 예상 질문 준비

---

## 🔗 참고 자료

- [Kubeflow Pipelines v2 Documentation](https://www.kubeflow.org/docs/components/pipelines/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [KServe Documentation](https://kserve.github.io/website/)
- [California Housing Dataset](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_california_housing.html)

---

**현대오토에버 MLOps Training**
