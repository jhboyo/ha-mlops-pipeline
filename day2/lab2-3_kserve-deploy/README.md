# Lab 2-3: KServe 모델 배포

## 📋 실습 개요

| 항목 | 내용 |
|------|------|
| **소요시간** | 50분 |
| **난이도** | ⭐⭐⭐ |
| **목표** | KServe를 사용한 프로덕션 모델 서빙 |
| **사전 조건** | Lab 2-1, Lab 2-2 완료 (MLflow에 모델 저장됨) |

## 🎯 학습 목표

- KServe InferenceService 개념 이해
- S3에서 MLflow 모델 로드
- Kubernetes 환경에서 모델 서빙
- REST API를 통한 추론 테스트

---

## 📁 파일 구조

```
lab2-3_kserve-deploy/
├── README.md                    # 실습 가이드 (현재 문서)
├── TROUBLESHOOTING.md           # 문제 해결 가이드
├── requirements.txt             # Python 패키지
├── notebooks/
│   └── kserve_deploy.ipynb      # ⭐ Kubeflow Notebook 실습 파일
├── scripts/
│   ├── setup_credentials.sh     # AWS 자격증명 설정
│   ├── deploy_kserve.sh         # InferenceService 배포
│   └── test_inference.sh        # 추론 테스트
└── manifests/
    └── inferenceservice.yaml    # InferenceService YAML 템플릿
```

---

## 🚨 주요 주의사항

### ⚠️ 반드시 확인해야 할 사항

1. **네임스페이스 자동 감지 사용**
   - Kubeflow Notebook에서는 `kubeflow-user01`, `kubeflow-user07` 등 각자 다른 네임스페이스 사용
   - 하드코딩 대신 자동 감지 함수 사용 권장

2. **S3 전체 경로 사용**
   - ❌ `mlflow-artifacts:/RUN_ID/model` (KServe 미지원)
   - ✅ `s3://BUCKET/mlflow-artifacts/RUN_ID/artifacts/model`

3. **Istio Sidecar 비활성화**
   - InferenceService에 `sidecar.istio.io/inject: "false"` 추가
   - RBAC 403 에러 방지

4. **sklearn 버전 호환성**
   - 모델 학습 환경과 KServe 서버의 sklearn 버전이 다를 수 있음
   - 문제 발생 시 새 모델 학습 필요

5. **California Housing 데이터셋 특성**
   - **8개** 특성: MedInc, HouseAge, AveRooms, AveBedrms, Population, AveOccup, Latitude, Longitude

---

## 🚀 실습 단계

### 방법 1: Kubeflow Notebook 사용 (권장)

Kubeflow 대시보드에서 Notebook을 열고 `notebooks/kserve_deploy.ipynb`를 업로드하여 실행합니다.

### 방법 2: CLI 스크립트 사용

터미널에서 직접 실행합니다.

---

## 📝 Step 1: 환경 설정

### 1.1 네임스페이스 자동 감지

```python
def get_current_namespace():
    """Kubeflow Notebook의 현재 네임스페이스 자동 감지"""
    try:
        with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "kubeflow-user01"  # 기본값

NAMESPACE = get_current_namespace()
print(f"📁 현재 네임스페이스: {NAMESPACE}")
```

### 1.2 Kubernetes 클라이언트 연결

```python
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# In-cluster 설정 로드
config.load_incluster_config()

# API 클라이언트 생성
core_v1 = client.CoreV1Api()
custom_api = client.CustomObjectsApi()

print("✅ Kubernetes 클라이언트 연결 완료")
```

---

## 📝 Step 2: AWS 자격증명 설정

### 2.1 Secret 생성

```python
# AWS 자격증명 (본인 값으로 수정!)
AWS_ACCESS_KEY_ID = "YOUR_ACCESS_KEY_HERE"
AWS_SECRET_ACCESS_KEY = "YOUR_SECRET_KEY_HERE"
AWS_REGION = "ap-northeast-2"

def create_aws_secret(namespace, access_key, secret_key, region):
    """AWS S3 자격증명 Secret 생성"""
    secret_name = "aws-s3-credentials"
    
    secret = client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=client.V1ObjectMeta(name=secret_name, namespace=namespace),
        type="Opaque",
        string_data={
            "AWS_ACCESS_KEY_ID": access_key,
            "AWS_SECRET_ACCESS_KEY": secret_key,
            "AWS_DEFAULT_REGION": region
        }
    )
    
    try:
        core_v1.delete_namespaced_secret(secret_name, namespace)
        print(f"  🗑️  기존 Secret '{secret_name}' 삭제")
    except ApiException as e:
        if e.status != 404:
            raise
    
    core_v1.create_namespaced_secret(namespace=namespace, body=secret)
    print(f"  ✅ Secret '{secret_name}' 생성 완료")
    return secret_name

create_aws_secret(NAMESPACE, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
```

### 2.2 ConfigMap 생성

```python
def create_s3_config(namespace):
    """S3 설정 ConfigMap 생성"""
    configmap_name = "s3-config"
    
    configmap = client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata=client.V1ObjectMeta(name=configmap_name, namespace=namespace),
        data={
            "S3_ENDPOINT": "s3.amazonaws.com",
            "S3_USE_HTTPS": "1",
            "AWS_REGION": "ap-northeast-2"
        }
    )
    
    try:
        core_v1.delete_namespaced_config_map(configmap_name, namespace)
    except ApiException as e:
        if e.status != 404:
            raise
    
    core_v1.create_namespaced_config_map(namespace=namespace, body=configmap)
    print(f"  ✅ ConfigMap '{configmap_name}' 생성 완료")

create_s3_config(NAMESPACE)
```

---

## 📝 Step 3: InferenceService 배포

### 3.1 S3 모델 경로 확인

MLflow UI 또는 S3에서 모델 경로를 확인합니다:

```bash
# S3에서 모델 찾기
aws s3 ls s3://mlops-training-user01/mlflow-artifacts/ --recursive | grep "MLmodel"
```

### 3.2 InferenceService 생성

```python
import time

MODEL_NAME = "california-model-user<USER_NUM>"

# ⚠️ 중요: S3 전체 경로 사용!
# MLflow UI에서 확인한 Experiment ID와 Run ID로 수정
STORAGE_URI = "s3://mlops-training-user01/mlflow-artifacts/RUN_ID/artifacts/model"

isvc_spec = {
    "apiVersion": "serving.kserve.io/v1beta1",
    "kind": "InferenceService",
    "metadata": {
        "name": MODEL_NAME,
        "namespace": NAMESPACE,
        "annotations": {
            # ⚠️ 중요: Istio sidecar 비활성화로 RBAC 403 에러 방지
            "sidecar.istio.io/inject": "false"
        }
    },
    "spec": {
        "predictor": {
            "model": {
                "modelFormat": {"name": "sklearn"},
                "storageUri": STORAGE_URI,
                "resources": {
                    "requests": {"cpu": "500m", "memory": "1Gi"},
                    "limits": {"cpu": "1", "memory": "2Gi"}
                }
            }
        }
    }
}

def deploy_inferenceservice(spec, namespace):
    """InferenceService 배포"""
    model_name = spec["metadata"]["name"]
    
    # 기존 삭제
    try:
        custom_api.delete_namespaced_custom_object(
            group="serving.kserve.io",
            version="v1beta1",
            namespace=namespace,
            plural="inferenceservices",
            name=model_name
        )
        print(f"  🗑️  기존 InferenceService '{model_name}' 삭제")
        time.sleep(5)
    except ApiException as e:
        if e.status != 404:
            raise
    
    # 생성
    custom_api.create_namespaced_custom_object(
        group="serving.kserve.io",
        version="v1beta1",
        namespace=namespace,
        plural="inferenceservices",
        body=spec
    )
    print(f"  ✅ InferenceService '{model_name}' 생성 완료")

deploy_inferenceservice(isvc_spec, NAMESPACE)
```

### 3.3 배포 상태 모니터링

```python
def wait_for_inferenceservice(model_name, namespace, timeout=300):
    """InferenceService Ready 대기"""
    print(f"  ⏳ InferenceService '{model_name}' Ready 대기 중...")
    print(f"     (최대 {timeout}초, 보통 2-3분 소요)")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            isvc = custom_api.get_namespaced_custom_object(
                group="serving.kserve.io",
                version="v1beta1",
                namespace=namespace,
                plural="inferenceservices",
                name=model_name
            )
            
            conditions = isvc.get("status", {}).get("conditions", [])
            ready = next((c for c in conditions if c.get("type") == "Ready"), None)
            
            if ready:
                status = ready.get("status")
                reason = ready.get("reason", "")
                
                if status == "True":
                    url = isvc.get("status", {}).get("url", "")
                    print(f"\n  ✅ InferenceService Ready!")
                    print(f"     URL: {url}")
                    return True
                else:
                    elapsed = int(time.time() - start_time)
                    print(f"  ⏳ Status: {status} | Reason: {reason} ({elapsed}초)")
            
        except ApiException as e:
            print(f"  ⚠️ 상태 확인 실패: {e.reason}")
        
        time.sleep(10)
    
    print(f"\n  ❌ 타임아웃: {timeout}초 초과")
    return False

wait_for_inferenceservice(MODEL_NAME, NAMESPACE)
```

---

## 📝 Step 4: 추론 테스트

### 4.1 클러스터 내부 추론 테스트

```python
import requests

# ⚠️ California Housing 데이터셋: 8개 특성
# [MedInc, HouseAge, AveRooms, AveBedrms, Population, AveOccup, Latitude, Longitude]
test_data = {
    "instances": [
        [3.5, 25.0, 5.5, 1.1, 1500.0, 3.0, 37.5, -122.0]
    ]
}

def test_inference(model_name, namespace, data):
    """클러스터 내부 추론 테스트"""
    url = f"http://{model_name}-predictor.{namespace}.svc.cluster.local/v1/models/{model_name}:predict"
    
    print(f"  🔗 URL: {url}")
    print(f"  📤 입력 데이터: {data}")
    
    try:
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ 추론 성공!")
            print(f"  📥 예측 결과: {result}")
            
            predictions = result.get("predictions", [])
            if predictions:
                # California Housing 타겟은 $100,000 단위
                print(f"\n  🏠 예측된 주택 가격: ${predictions[0] * 100000:,.0f}")
            return result
        else:
            print(f"  ❌ 추론 실패: HTTP {response.status_code}")
            print(f"      {response.text}")
            return None
            
    except Exception as e:
        print(f"  ❌ 에러: {e}")
        return None

test_inference(MODEL_NAME, NAMESPACE, test_data)
```

### 4.2 다양한 입력 테스트

```python
# 여러 샘플 테스트
test_samples = {
    "instances": [
        [8.3252, 41.0, 6.98, 1.02, 322.0, 2.56, 37.88, -122.23],   # 고가 지역
        [3.5, 25.0, 5.5, 1.1, 1500.0, 3.0, 37.5, -122.0],          # 중간 지역
        [1.5, 10.0, 4.0, 1.0, 3000.0, 4.0, 34.0, -118.0],          # 저가 지역
    ]
}

result = test_inference(MODEL_NAME, NAMESPACE, test_samples)
if result:
    for i, pred in enumerate(result.get("predictions", [])):
        print(f"  샘플 {i+1}: ${pred * 100000:,.0f}")
```

---

## ✅ 완료 체크리스트

- [ ] 네임스페이스 자동 감지 설정
- [ ] AWS Secret 생성 완료
- [ ] S3 ConfigMap 생성 완료
- [ ] InferenceService 배포 완료 (READY=True)
- [ ] Pod Running 확인 (2/2 또는 1/1)
- [ ] 추론 테스트 성공

---

## 🔧 문제 해결

자주 발생하는 문제와 해결 방법은 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)를 참조하세요.

### 빠른 진단 명령어

```bash
# InferenceService 상태
kubectl get inferenceservice -n $NAMESPACE

# Pod 상태
kubectl get pods -n $NAMESPACE | grep california-model

# storage-initializer 로그
kubectl logs -n $NAMESPACE -l serving.knative.dev/configuration=california-model-predictor -c storage-initializer

# kserve-container 로그
kubectl logs -n $NAMESPACE -l serving.knative.dev/configuration=california-model-predictor -c kserve-container

# 상세 정보
kubectl describe inferenceservice california-model -n $NAMESPACE
```

---

## 📚 참고 자료

- [KServe 공식 문서](https://kserve.github.io/website/)
- [MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)
- [California Housing 데이터셋](https://scikit-learn.org/stable/datasets/real_world.html#california-housing-dataset)

---

© 2025 현대오토에버 MLOps Training