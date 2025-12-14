# Lab 2-1: FastAPI 모델 서빙

## 📋 실습 개요

| 항목 | 내용 |
|------|------|
| **소요시간** | 50분 |
| **난이도** | ⭐⭐ |
| **목표** | FastAPI로 ML 모델 REST API 구축 및 Kubernetes 배포 |

## 🎯 학습 목표

1. **Scikit-learn 모델 학습**
   - Iris 데이터셋 활용
   - RandomForest 분류 모델 구축
   - 모델 평가 및 저장

2. **FastAPI REST API 구현**
   - Pydantic을 활용한 데이터 검증
   - 단일/배치 예측 엔드포인트 구현
   - Swagger UI 자동 생성

3. **Docker 컨테이너화**
   - 멀티 아키텍처 이미지 빌드
   - ECR에 이미지 푸시

4. **Kubernetes 배포**
   - Deployment와 Service 리소스 생성
   - Health check 설정
   - Port Forward를 통한 테스트

## 📁 디렉토리 구조

```
lab2-1_fastapi-serving/
├── README.md                   # 이 파일
├── requirements.txt            # Python 의존성
├── train_model.py              # 모델 학습 스크립트
├── model.joblib                # 학습된 모델 (생성됨)
│
├── app/                        # FastAPI 애플리케이션
│   ├── __init__.py
│   └── main.py                 # API 엔드포인트
│
├── scripts/                    # 실행 스크립트
│   ├── build_and_deploy.sh    # 빌드 및 배포
│   └── test_api.sh             # API 테스트
│
├── Dockerfile                  # Docker 이미지 정의
├── .dockerignore              # Docker 빌드 제외 파일
├── deployment.yaml            # Kubernetes Deployment
└── service.yaml               # Kubernetes Service
```

## 🚀 실습 단계

### Prerequisites

실습 시작 전 필요한 환경:

```bash
# 1. Python 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 2. 환경 변수 설정
export ECR_REGISTRY="<YOUR_ECR_REGISTRY>"   # 예: 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com
export NAMESPACE="<YOUR_NAMESPACE>"         # 본인의 네임스페이스
export USER_NUM="<YOUR_USER_NUM>"           # 본인의 번호 (01 ~ 15)

# 3. AWS CLI 로그인 확인
aws sts get-caller-identity

# 4. kubectl 설정 확인
kubectl get nodes
```

---

### Step 1: 로컬 개발 및 테스트

#### 1-1. 의존성 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**예상 출력:**
```
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 scikit-learn-1.5.2 ...
```

#### 1-2. 모델 학습

```bash
python train_model.py
```

**예상 출력:**
```
============================================================
  Lab 2-1: Iris 분류 모델 학습
============================================================

────────────────────────────────────────────────────────────
  Step 1: 데이터 로드
────────────────────────────────────────────────────────────
  🔄 Iris 데이터셋 로드 중...
  ✅ 데이터 로드 완료
     - 전체 샘플 수: 150
     - 피처 수: 4
     - 클래스 수: 3
     - 클래스 이름: setosa, versicolor, virginica

  📊 피처 정보:
     1. sepal length (cm)
     2. sepal width (cm)
     3. petal length (cm)
     4. petal width (cm)

  🔄 Train/Test 데이터 분할 중...
  ✅ 데이터 분할 완료
     - 학습 데이터: 120 samples (80.0%)
     - 테스트 데이터: 30 samples (20.0%)

────────────────────────────────────────────────────────────
  Step 2: 모델 학습
────────────────────────────────────────────────────────────
  🔄 RandomForest 모델 학습 중...
     - n_estimators: 100
     - random_state: 42
     - n_jobs: -1 (모든 CPU 사용)

  ⏳ 학습 진행 중..... 완료!

  ✅ 모델 학습 완료

────────────────────────────────────────────────────────────
  Step 3: 모델 평가
────────────────────────────────────────────────────────────
  🔄 모델 성능 평가 중...

  📊 정확도 (Accuracy):
     - 학습 데이터: 1.0000 (100.00%)
     - 테스트 데이터: 1.0000 (100.00%)
     ✅ 일반화 성능 양호

  🎯 피처 중요도:
     1. petal length (cm)  0.4532 ██████████████████████
     2. petal width (cm)   0.4201 █████████████████████
     3. sepal length (cm)  0.0802 ████
     4. sepal width (cm)   0.0465 ██

────────────────────────────────────────────────────────────
  Step 4: 모델 저장
────────────────────────────────────────────────────────────
  💾 모델 저장 중: model.joblib
  ✅ 모델 저장 완료
     - 파일명: model.joblib
     - 파일 크기: 127.45 KB
     - 저장 위치: /path/to/model.joblib

============================================================
  🎉 모델 학습 완료!
============================================================

  📝 다음 단계:
     1. FastAPI 서버 실행:
        uvicorn app.main:app --reload --port 8000

     2. API 테스트:
        curl http://localhost:8000/health

     3. Docker 빌드:
        docker build -t iris-api:v1 .

     4. Kubernetes 배포:
        ./scripts/build_and_deploy.sh

  💡 자세한 내용은 README.md를 참조하세요.
============================================================
```

#### 1-3. FastAPI 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

**예상 출력:**
```
INFO:     Will watch for changes in these directories: ['/path/to/lab2-1']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
2025-12-09 10:00:00 - app.main - INFO - ============================================================
2025-12-09 10:00:00 - app.main - INFO -   Iris Classification API 시작
2025-12-09 10:00:00 - app.main - INFO - ============================================================
2025-12-09 10:00:00 - app.main - INFO - 모델 로드 상태: ✅ 성공
2025-12-09 10:00:00 - app.main - INFO - API 문서: http://localhost:8000/docs
2025-12-09 10:00:00 - app.main - INFO - ============================================================
INFO:     Application startup complete.
```

#### 1-4. API 테스트

**터미널을 하나 더 열어서** 다음 명령 실행:

```bash
# Health Check
curl http://localhost:8000/health

# 단일 예측 (Setosa)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
  }'

# 배치 예측
curl -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2},
    {"sepal_length":6.7,"sepal_width":3.0,"petal_length":5.2,"petal_width":2.3}
  ]'
```

#### 1-5. Swagger UI 확인

브라우저에서 접속:
- Swagger UI: http://localhost:8000/docs

---

### Step 2: Docker 빌드 및 로컬 테스트

#### 2-1. Docker 이미지 빌드

```bash
docker build --platform linux/amd64 -t user<USER_NUM>:v1 .
```

**예상 출력:**
```
[+] Building 45.2s (12/12) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 537B
 => [internal] load .dockerignore
 ...
 => => naming to docker.io/library/iris-api:v1
```

#### 2-2. Docker 컨테이너 실행

```bash
# 컨테이너 실행
docker run -d -p 8000:8000 --name iris-api-test user<USER_NUM>:v1

# 로그 확인
docker logs iris-api-test

# API 테스트
curl http://localhost:8000/health

# 컨테이너 정리
docker stop iris-api-test
docker rm iris-api-test
```

---

### Step 3: Kubernetes 배포

#### 3-1. 환경 변수 확인

```bash
echo "ECR_REGISTRY: $ECR_REGISTRY"
echo "NAMESPACE: $NAMESPACE"
```

환경 변수가 설정되지 않았다면:
```bash
export ECR_REGISTRY="<YOUR_ECR_REGISTRY>"
export NAMESPACE="kubeflow-user01"
```

#### 3-2. 빌드 및 배포 스크립트 실행

```bash
./scripts/build_and_deploy.sh
```

**예상 출력:**
```
============================================================
  Lab 2-1: FastAPI 모델 서빙 - 빌드 및 배포
============================================================

[INFO] ECR Registry: 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com
[INFO] Namespace: kubeflow-user01

[STEP] [1/6] Docker 이미지 빌드
[INFO] 이미지 빌드 중...
[INFO] ✅ Docker 이미지 빌드 완료

[STEP] [2/6] ECR 로그인
[INFO] ECR에 로그인 중...
Login Succeeded
[INFO] ✅ ECR 로그인 성공

[STEP] [3/6] 이미지 태깅
[INFO] ✅ 이미지 태깅 완료

[STEP] [4/6] ECR에 이미지 푸시
[INFO] 이미지 푸시 중...
[INFO] ✅ 이미지 푸시 완료

[STEP] [5/6] Kubernetes 배포
[INFO] Deployment 배포 중...
deployment.apps/iris-api created
[INFO] Service 배포 중...
service/iris-api-svc created
[INFO] ✅ Kubernetes 리소스 배포 완료

[STEP] [6/6] 배포 상태 확인
[INFO] 배포 완료 대기 중...
deployment.apps/iris-api condition met
[INFO] ✅ 배포 준비 완료

============================================================
  ✅ 배포 완료!
============================================================

📦 Deployment 상태:
NAME       READY   UP-TO-DATE   AVAILABLE   AGE
iris-api   2/2     2            2           30s

🏃 Pod 상태:
NAME                        READY   STATUS    RESTARTS   AGE
iris-api-76d55ccf8f-p24q7   1/1     Running   0          30s
iris-api-76d55ccf8f-t9nzq   1/1     Running   0          30s

🌐 Service 상태:
NAME           TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
iris-api-svc   ClusterIP   10.100.201.199   <none>        80/TCP    30s
```

#### 3-3. 배포 확인

```bash
# Pod 상태 확인
kubectl get pods -n $NAMESPACE -l app=iris-api

# Service 확인
kubectl get svc iris-api-svc -n $NAMESPACE

# Pod 로그 확인
kubectl logs -n $NAMESPACE -l app=iris-api --tail=50
```

---

### Step 4: API 테스트 (Kubernetes)

#### 4-1. Port Forward 시작

**새 터미널을 열고** 다음 명령 실행:

```bash
kubectl port-forward -n $NAMESPACE svc/iris-api-svc 8000:80
```

**예상 출력:**
```
Forwarding from 127.0.0.1:8000 -> 8000
Forwarding from [::1]:8000 -> 8000
```

**✅ 이 터미널은 그대로 열어두세요!**

#### 4-2. API 테스트 스크립트 실행

**다른 터미널을 열고** 다음 명령 실행:

```bash
./scripts/test_api.sh
```

**예상 출력:**
```
============================================================
  Lab 2-1: Iris Classification API 테스트
============================================================

[INFO] API URL: http://localhost:8000

[TEST] API 연결 확인 중...
[PASS] API 연결 성공

============================================================
[TEST] [1/6] GET / - API 정보 확인
============================================================

{
  "message": "Iris Classification API",
  "version": "1.0.0",
  "model_loaded": true
}

[PASS] API 정보 확인 성공

============================================================
[TEST] [2/6] GET /health - Health Check
============================================================

{
  "status": "healthy",
  "model_loaded": true
}

[PASS] Health Check 성공

============================================================
[TEST] [3/6] POST /predict - Setosa 예측
============================================================

[INFO] 입력 데이터:
{
  "sepal_length": 5.1,
  "sepal_width": 3.5,
  "petal_length": 1.4,
  "petal_width": 0.2
}

[INFO] 예측 결과:
{
  "prediction": "setosa",
  "confidence": 0.98
}

[PASS] Setosa 예측 성공

...

============================================================
  ✅ 모든 테스트 완료!
============================================================

📊 테스트 결과 요약:
  ✅ [1/6] API 정보 확인
  ✅ [2/6] Health Check
  ✅ [3/6] Setosa 예측
  ✅ [4/6] Versicolor 예측
  ✅ [5/6] Virginica 예측
  ✅ [6/6] 배치 예측

🎉 모든 테스트가 성공적으로 완료되었습니다!
```

#### 4-3. 수동 API 테스트

```bash
# Health Check
curl http://localhost:8000/health

# 예측 테스트
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'

# Swagger UI 열기
open http://localhost:8000/docs
```

---

## 📊 API 명세

### GET /

**설명:** API 기본 정보 반환

**응답:**
```json
{
  "message": "Iris Classification API",
  "version": "1.0.0",
  "model_loaded": true
}
```

---

### GET /health

**설명:** Health check 엔드포인트 (Kubernetes liveness/readiness probe용)

**응답:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

---

### POST /predict

**설명:** 단일 샘플 예측

**요청 Body:**
```json
{
  "sepal_length": 5.1,
  "sepal_width": 3.5,
  "petal_length": 1.4,
  "petal_width": 0.2
}
```

**응답:**
```json
{
  "prediction": "setosa",
  "confidence": 0.98
}
```

**가능한 예측 값:**
- `setosa` - Iris Setosa
- `versicolor` - Iris Versicolor
- `virginica` - Iris Virginica

---

### POST /predict/batch

**설명:** 배치 예측 (여러 샘플을 한 번에 예측)

**요청 Body:**
```json
[
  {
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2
  },
  {
    "sepal_length": 6.7,
    "sepal_width": 3.0,
    "petal_length": 5.2,
    "petal_width": 2.3
  }
]
```

**응답:**
```json
{
  "predictions": [
    {
      "prediction": "setosa",
      "confidence": 0.98
    },
    {
      "prediction": "virginica",
      "confidence": 0.95
    }
  ]
}
```

---

## 🐛 트러블슈팅

### 문제 1: Python 3.12에서 의존성 설치 오류

**증상:**
```
ModuleNotFoundError: No module named 'distutils'
```

**원인:** Python 3.12에서 numpy 1.24.3은 지원되지 않음

**해결:**
```bash
# 최신 requirements.txt 사용 (이미 Python 3.12 지원)
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 문제 2: model.joblib 파일이 없다는 오류

**증상:**
```
FileNotFoundError: model.joblib not found
```

**해결:**
```bash
# 모델을 먼저 학습
python train_model.py
```

---

### 문제 3: Port 8000이 이미 사용 중

**증상:**
```
Error: [Errno 48] Address already in use
```

**해결:**
```bash
# 다른 포트 사용
uvicorn app.main:app --reload --port 8001

# 또는 기존 프로세스 종료
lsof -ti:8000 | xargs kill -9
```

---

### 문제 4: Docker 이미지 빌드 실패

**증상:**
```
ERROR: failed to solve: process "/bin/sh -c pip install ..." did not complete successfully
```

**해결:**
```bash
# 캐시 없이 빌드
docker build --no-cache --platform linux/amd64 -t iris-api:v1 .

# 또는 requirements.txt 버전 확인
cat requirements.txt
```

---

### 문제 5: Pod가 ImagePullBackOff 상태

**증상:**
```
NAME                        READY   STATUS             RESTARTS   AGE
iris-api-xxxxx-yyyyy        0/1     ImagePullBackOff   0          2m
```

**해결:**
```bash
# ECR 레지스트리 주소 확인
echo $ECR_REGISTRY

# 이미지가 ECR에 푸시되었는지 확인
aws ecr describe-images --repository-name mlops-training/user<USER_NUM>

# Pod 상세 정보 확인
kubectl describe pod -n $NAMESPACE <pod-name>
```

---

### 문제 6: Port Forward 연결 실패

**증상:**
```
curl: (7) Failed to connect to localhost port 8000: Connection refused
```

**해결:**
```bash
# Port Forward 프로세스 확인
ps aux | grep "port-forward"

# 실행 중이 아니면 다시 시작
kubectl port-forward -n $NAMESPACE svc/iris-api-svc 8000:80
```

---

### 문제 7: "Address already in use" (Port Forward)

**증상:**
```
Unable to listen on port 8000: Listeners failed to create
```

**해결:**
```bash
# 기존 프로세스 종료
lsof -ti:8000 | xargs kill -9

# 또는 다른 포트 사용
kubectl port-forward -n $NAMESPACE svc/iris-api-svc 8001:80
```

---

## 💡 추가 팁

### 백그라운드로 Port Forward 실행

```bash
# 백그라운드 실행
nohup kubectl port-forward -n $NAMESPACE svc/iris-api-svc 8000:80 > /tmp/pf-iris.log 2>&1 &

# 프로세스 ID 확인
echo $!

# 종료
pkill -f "port-forward.*iris-api"
```

### Pod 로그 실시간 확인

```bash
# 모든 Pod 로그
kubectl logs -n $NAMESPACE -l app=iris-api -f --tail=100

# 특정 Pod 로그
kubectl logs -n $NAMESPACE <pod-name> -f
```

### 리소스 사용량 확인

```bash
# CPU/Memory 사용량
kubectl top pods -n $NAMESPACE -l app=iris-api

# 상세 정보
kubectl describe pod -n $NAMESPACE -l app=iris-api | grep -A 5 "Limits\|Requests"
```

---

## 🧹 정리 (실습 종료 시)

```bash
# Port Forward 종료
pkill -f "port-forward.*iris-api"

# Kubernetes 리소스 삭제
kubectl delete deployment iris-api -n $NAMESPACE
kubectl delete service iris-api-svc -n $NAMESPACE

# 확인
kubectl get all -n $NAMESPACE -l app=iris-api

# Docker 이미지 정리 (선택사항)
docker rmi iris-api:v1
docker rmi ${ECR_REGISTRY}/mlops-training/user<USER_NUM>:v1
```

---

## ✅ 완료 체크리스트

### 로컬 개발
- [ ] Python 가상환경 생성 및 활성화
- [ ] 의존성 설치 완료
- [ ] 모델 학습 성공 (model.joblib 생성됨)
- [ ] FastAPI 서버 로컬 실행 성공
- [ ] API 테스트 성공 (/health, /predict)
- [ ] Swagger UI 접속 확인

### Docker
- [ ] Docker 이미지 빌드 완료
- [ ] Docker 컨테이너 실행 및 테스트 성공

### Kubernetes
- [ ] 환경 변수 설정 완료
- [ ] ECR에 이미지 푸시 완료
- [ ] Kubernetes 배포 성공
- [ ] Pod가 Running 상태
- [ ] Service 생성 확인
- [ ] Port Forward 설정 성공
- [ ] Kubernetes에서 API 테스트 성공

---

## 📚 참고 자료

### 공식 문서
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Scikit-learn 공식 문서](https://scikit-learn.org/)
- [Uvicorn 공식 문서](https://www.uvicorn.org/)
- [Pydantic 공식 문서](https://docs.pydantic.dev/)
- [Docker 공식 문서](https://docs.docker.com/)
- [Kubernetes 공식 문서](https://kubernetes.io/)

### MLOps 관련
- [Kubeflow 공식 문서](https://www.kubeflow.org/)
- [MLflow 공식 문서](https://mlflow.org/)
- [AWS ECR 문서](https://docs.aws.amazon.com/ecr/)

---

## 🎓 다음 단계

Lab 2-1을 완료했다면 다음 실습으로 진행하세요:

- **Lab 2-2**: MLflow Tracking & Model Registry
  - MLflow로 실험 추적
  - Model Registry 활용
  - S3에 모델 저장

- **Lab 2-3**: KServe를 활용한 고급 모델 서빙
  - InferenceService 배포
  - 자동 스케일링
  - 카나리 배포

---

© 2025 현대오토에버 MLOps Training
