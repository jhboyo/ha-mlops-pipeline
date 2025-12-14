# Lab 2-3 문제 해결 가이드 (Troubleshooting)

이 문서는 KServe 배포 실습 중 발생할 수 있는 문제와 해결 방법을 정리합니다.

---

## 🔴 문제 1: RBAC 403 Forbidden (namespace list)

### 증상

```
❌ 연결 실패: (403)
Reason: Forbidden
HTTP response body: {"message":"namespaces is forbidden: User \"system:serviceaccount:kubeflow-user-example-com:default-editor\" cannot list resource \"namespaces\" in API group \"\" at the cluster scope"...}
```

### 원인

Kubeflow의 `default-editor` ServiceAccount는 **자신의 namespace 내에서만** 권한이 있습니다. 클러스터 전체 namespace 목록을 조회할 권한이 없습니다.

### 해결 방법

환경 감지 시 namespace list 호출을 피하고, **직접 namespace를 지정**하거나 **자동 감지 함수**를 사용합니다:

```python
# ✅ 올바른 방법: namespace 자동 감지
def get_current_namespace():
    try:
        with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "kubeflow-user-example-com"

NAMESPACE = get_current_namespace()
```

---

## 🔴 문제 2: RBAC 403 Forbidden (다른 namespace 접근)

### 증상

```
secrets "aws-s3-credentials" is forbidden: User "system:serviceaccount:kubeflow-user-example-com:default-editor" cannot delete resource "secrets" in API group "" in the namespace "kubeflow-user01"
```

### 원인

Notebook이 실행되는 namespace(`kubeflow-user-example-com`)와 Secret을 생성하려는 namespace(`kubeflow-user01`)가 다릅니다.

### 해결 방법

**항상 자동 감지된 namespace를 사용**합니다:

```python
# ❌ 잘못된 방법: 하드코딩
NAMESPACE = "kubeflow-user01"

# ✅ 올바른 방법: 자동 감지
NAMESPACE = get_current_namespace()
```

---

## 🔴 문제 3: Storage URI 인식 실패

### 증상

```
Exception: Cannot recognize storage type for mlflow-artifacts:/RUN_ID/model
'gs://', 's3://', 'file://', and 'http(s)://' are the current available storage type.
```

### 원인

KServe는 `mlflow-artifacts:` 프로토콜을 지원하지 않습니다.

### 해결 방법

**S3 전체 경로**를 사용합니다:

```python
# ❌ 잘못된 형식
STORAGE_URI = "mlflow-artifacts:/RUN_ID/model"

# ✅ 올바른 형식
STORAGE_URI = "s3://mlops-training-user01/mlflow-artifacts/EXPERIMENT_ID/RUN_ID/artifacts/model"
```

### S3 경로 확인 방법

```bash
# S3에서 모델 파일 찾기
aws s3 ls s3://mlops-training-user01/mlflow-artifacts/ --recursive | grep "MLmodel"

# 출력 예시:
# 2025-12-13 00:18:25  531 mlflow-artifacts/1/8479802f806047b196b1676b763e8f5d/artifacts/model/MLmodel
#                                          ↑ Experiment ID    ↑ Run ID
```

---

## 🔴 문제 4: storage-initializer CrashLoopBackOff

### 증상

```
Pod: california-model-predictor-00001-deployment-xxx    Init:CrashLoopBackOff
```

또는

```
RuntimeError: Failed to fetch model. No model found in mlflow-artifacts/.../model.
```

### 원인

1. S3 경로가 잘못됨
2. AWS 자격증명이 없거나 잘못됨
3. 모델 파일이 S3에 없음

### 해결 방법

#### 1) S3 경로 확인

```bash
# 해당 경로에 모델이 있는지 확인
aws s3 ls s3://mlops-training-user01/mlflow-artifacts/EXPERIMENT_ID/RUN_ID/artifacts/model/
```

#### 2) AWS Secret 확인

```bash
# Secret 존재 확인
kubectl get secret aws-s3-credentials -n $NAMESPACE

# Secret 내용 확인
kubectl get secret aws-s3-credentials -n $NAMESPACE -o jsonpath='{.data.AWS_ACCESS_KEY_ID}' | base64 -d
```

#### 3) storage-initializer 로그 확인

```bash
kubectl logs -n $NAMESPACE -l serving.knative.dev/configuration=california-model-predictor -c storage-initializer
```

---

## 🔴 문제 5: Istio RBAC 403 (추론 시)

### 증상

```
❌ 추론 실패: HTTP 403
   RBAC: access denied
```

### 원인

Istio의 AuthorizationPolicy가 Kubeflow Notebook에서 KServe 서비스로의 접근을 차단합니다.

### 해결 방법

InferenceService에 **Istio sidecar 비활성화** annotation 추가:

```python
isvc_spec = {
    "metadata": {
        "name": MODEL_NAME,
        "namespace": NAMESPACE,
        "annotations": {
            "sidecar.istio.io/inject": "false"  # ← 이 줄 추가!
        }
    },
    ...
}
```

기존 InferenceService 삭제 후 재배포:

```bash
kubectl delete inferenceservice california-model -n $NAMESPACE
# 노트북에서 재배포
```

---

## 🔴 문제 6: sklearn 버전 불일치

### 증상

```
'DecisionTreeRegressor' object has no attribute 'monotonic_cst'
```

또는

```
InconsistentVersionWarning: Trying to unpickle estimator from version 1.3.2 when using version 1.5.2
```

### 원인

모델 학습 시 사용한 sklearn 버전과 KServe 서버의 sklearn 버전이 다릅니다.

### 해결 방법

**Kubeflow Notebook에서 새 모델 학습 후 재배포**:

```python
import mlflow
import mlflow.sklearn
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

# MLflow 설정
MLFLOW_TRACKING_URI = "http://mlflow-server.mlflow-system.svc.cluster.local:5000"
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("california-housing-kserve")

# 데이터 로딩
data = fetch_california_housing()
X_train, X_test, y_train, y_test = train_test_split(
    data.data, data.target, test_size=0.2, random_state=42
)

# 모델 학습 (RandomForestRegressor 권장)
model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
model.fit(X_train, y_train)

# 평가
y_pred = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

# MLflow 로깅
with mlflow.start_run() as run:
    mlflow.log_param("model_type", "RandomForestRegressor")
    mlflow.log_metric("rmse", rmse)
    mlflow.log_metric("r2", r2)
    mlflow.sklearn.log_model(model, "model")
    
    run_id = run.info.run_id
    experiment_id = run.info.experiment_id
    print(f"✅ 새 모델 저장 완료!")
    print(f"   Storage URI: s3://mlops-training-user01/mlflow-artifacts/{experiment_id}/{run_id}/artifacts/model")
```

---

## 🔴 문제 7: Feature 개수 불일치

### 증상

```
X has 11 features, but RandomForestRegressor is expecting 8 features as input.
```

### 원인

테스트 데이터의 특성 개수가 모델 학습 시 사용한 데이터와 다릅니다.

### 해결 방법

**California Housing 데이터셋은 8개 특성**입니다:

| 인덱스 | 특성 | 설명 |
|--------|------|------|
| 0 | MedInc | 중위 소득 |
| 1 | HouseAge | 주택 연령 |
| 2 | AveRooms | 평균 방 수 |
| 3 | AveBedrms | 평균 침실 수 |
| 4 | Population | 인구 |
| 5 | AveOccup | 평균 거주자 수 |
| 6 | Latitude | 위도 |
| 7 | Longitude | 경도 |

```python
# ❌ 잘못된 테스트 데이터 (11개 특성)
test_data = {"instances": [[0.5, 0.2, -0.1, -0.15, 0.3, 0.1, 0.8, -0.5, 1.2, 0.3, 0.5]]}

# ✅ 올바른 테스트 데이터 (8개 특성)
test_data = {"instances": [[3.5, 25.0, 5.5, 1.1, 1500.0, 3.0, 37.5, -122.0]]}
```

---

## 🔴 문제 8: NameError (변수 정의 안됨)

### 증상

```
NameError: name 'core_v1' is not defined
NameError: name 'custom_api' is not defined
NameError: name 'NAMESPACE' is not defined
```

### 원인

Kernel Restart 후 이전에 정의된 변수가 메모리에서 사라졌습니다.

### 해결 방법

**노트북 셀을 처음부터 순서대로 실행**하거나, 각 셀에 필요한 import와 변수 정의를 포함합니다:

```python
# 매 셀 시작 부분에 필요한 경우
from kubernetes import client, config
from kubernetes.client.rest import ApiException

config.load_incluster_config()
core_v1 = client.CoreV1Api()
custom_api = client.CustomObjectsApi()

def get_current_namespace():
    try:
        with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
            return f.read().strip()
    except:
        return "kubeflow-user-example-com"

NAMESPACE = get_current_namespace()
```

---

## 🔴 문제 9: MLflow PostgreSQL 연결 실패

### 증상

```
psycopg2.OperationalError: connection to server at "postgres-service.mlflow-system.svc.cluster.local" 
failed: FATAL:  password authentication failed for user "mlflow"
```

### 원인

MLflow 서버의 DB 설정과 PostgreSQL 실제 설정이 불일치합니다.

### 해결 방법

```bash
# 1. PostgreSQL Pod 확인
kubectl get pods -n mlflow-system | grep postgres

# 2. 비밀번호 동기화 (MLflow가 사용하는 비밀번호로 변경)
kubectl exec -it <postgres-pod> -n mlflow-system -- psql -U mlflow -d postgres -c "ALTER USER mlflow WITH PASSWORD 'mlflow';"

# 3. mlflow 데이터베이스 생성 (없는 경우)
kubectl exec -it <postgres-pod> -n mlflow-system -- psql -U mlflow -d postgres -c "CREATE DATABASE mlflow;"

# 4. MLflow 서버 재시작
kubectl rollout restart deployment mlflow-server -n mlflow-system
```

---

## 🛠️ 진단 스크립트

전체 환경을 빠르게 진단하는 스크립트:

```bash
#!/bin/bash
# USER_NUM 환경 변수 사용 (예: export USER_NUM="01")
USER_NUM=${USER_NUM:-"01"}
NAMESPACE="kubeflow-user${USER_NUM}"
MODEL_NAME="california-model"

echo "사용자: user${USER_NUM}"
echo "네임스페이스: ${NAMESPACE}"

echo "=========================================="
echo "Lab 2-3 진단 스크립트"
echo "=========================================="
echo ""

echo "=== 1. InferenceService 상태 ==="
kubectl get inferenceservice -n $NAMESPACE
echo ""

echo "=== 2. Pod 상태 ==="
kubectl get pods -n $NAMESPACE | grep $MODEL_NAME
echo ""

echo "=== 3. Secret 확인 ==="
kubectl get secret aws-s3-credentials -n $NAMESPACE 2>/dev/null && echo "✅ Secret 존재" || echo "❌ Secret 없음"
echo ""

echo "=== 4. storage-initializer 로그 ==="
POD=$(kubectl get pods -n $NAMESPACE -l serving.knative.dev/configuration=${MODEL_NAME}-predictor -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$POD" ]; then
    kubectl logs -n $NAMESPACE $POD -c storage-initializer --tail=10 2>/dev/null || echo "로그 없음"
else
    echo "Pod 없음"
fi
echo ""

echo "=== 5. kserve-container 로그 ==="
if [ -n "$POD" ]; then
    kubectl logs -n $NAMESPACE $POD -c kserve-container --tail=10 2>/dev/null || echo "로그 없음"
fi
echo ""

echo "=== 6. Events ==="
kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -10
```

---

## 📞 추가 지원

문제가 해결되지 않으면:

1. **강사에게 문의**: 현재 상태 스크린샷과 함께 에러 메시지 공유
2. **로그 수집**: 위 진단 스크립트 실행 결과 공유
3. **환경 정보 제공**: namespace, Pod 상태, kubectl 버전 등
