# 🚀 MLOps 파이프라인 구현 [고급]

> **현대오토에버** - 3일 24시간 MLOps 실습 자료

---

## ⚠️ 필독: 사전 환경 설정

> **🔴 교육 시작 전 반드시 환경 설정을 완료해주세요!**
>
> 교육 당일에는 환경 설정을 위한 별도의 시간이 제공되지 않습니다.  
> 설정이 완료되지 않으면 실습 참여가 어려울 수 있습니다.

### 📋 운영체제별 설정 가이드

| 운영체제 | 설정 가이드 | 예상 소요시간 |
|----------|------------|--------------|
| **macOS** | [📖 SETUP_MACOS.md](docs/SETUP_MACOS.md) | 30~45분 |
| **Windows** | [📖 SETUP_WINDOWS.md](docs/SETUP_WINDOWS.md) | 45~60분 |

### ✅ 사전 설정 체크리스트

다음 항목이 모두 완료되어야 합니다:

- [ ] **Docker Desktop** 설치 및 실행 확인
- [ ] **AWS CLI v2** 설치 (`aws --version`)
- [ ] **kubectl** 설치 (`kubectl version --client`)
- [ ] **Python 3.9+** 설치 (`python3 --version`)
- [ ] **Git** 설치 (`git --version`)
- [ ] **필수 Python 패키지** 설치 (kfp, mlflow, scikit-learn, onnxruntime)

### 🔍 빠른 확인 명령어

```bash
# 모든 도구 버전 확인
aws --version && kubectl version --client && docker --version && python3 --version && git --version

# Python 패키지 확인
python3 -c "import kfp, mlflow, sklearn, onnxruntime; print('✅ 모든 패키지 설치 완료')"
```

---

## 📋 교육 개요

| 항목 | 내용 |
|------|------|
| **교육명** | MLOps 파이프라인 구현 [고급] |
| **기간** | 3일 (24시간) |
| **대상** | 데이터사이언티스트 & 데이터엔지니어 30명 |
| **환경** | AWS EKS + Kubeflow + MLflow + KServe |

### 🎯 학습 목표

- **Kubeflow Pipelines**를 활용한 ML 워크플로우 자동화
- **MLflow**를 통한 실험 추적 및 모델 버전 관리
- **KServe**를 사용한 프로덕션 모델 서빙
- **모니터링 & 재학습** 파이프라인 구축
- **모델 최적화** (ONNX, Quantization) 기법 적용

---

## 📅 교육 일정

### 강의 시간

| 구분 | 시간 | 비고 |
|------|------|------|
| **오전 강의** | 09:00 ~ 11:30 | 쉬는시간: 10:20~10:30 |
| **점심시간** | 11:30 ~ 13:00 | |
| **오후 강의** | 13:00 ~ 17:30 | 쉬는시간: 매 시간 20분~30분 |

### 3일 커리큘럼

#### Day 1: MLOps 기초 & Kubeflow 파이프라인

| 시간 | 내용 | Lab |
|------|------|-----|
| 09:00-11:30 | MLOps 개요, AWS EKS 환경 구축 | Lab 1-1 |
| 13:00-15:30 | Kubeflow 대시보드, Hello Pipeline | Lab 1-2 |
| 15:30-17:30 | Batch 데이터 파이프라인 | Lab 1-3 |

#### Day 2: 모델 서빙 & MLflow

| 시간 | 내용 | Lab |
|------|------|-----|
| 09:00-11:30 | FastAPI 모델 서빙, 컨테이너화 | Lab 2-1 |
| 13:00-15:30 | MLflow Tracking & Registry | Lab 2-2 |
| 15:30-17:30 | KServe 배포, Canary 배포 | Lab 2-3 |

#### Day 3: 모니터링 & 프로젝트

| 시간 | 내용 | Lab |
|------|------|-----|
| 09:00-11:30 | Drift Detection, 자동 재학습 | Lab 3-1 |
| 13:00-15:00 | E2E Pipeline, 모델 최적화 | Lab 3-2, Lab 3-3 |
| 15:00-17:30 | **팀 프로젝트 & 발표** | Project |

---

## 📁 Repository 구조

```
ha-mlops-pipeline/
├── README.md                         # 📌 이 파일 (메인 가이드)
├── docs/                             # 📚 문서
│   ├── SETUP_MACOS.md               # 🍎 macOS 환경 설정
│   ├── SETUP_WINDOWS.md             # 🪟 Windows 환경 설정
│   └── TROUBLESHOOTING.md           # 🔧 트러블슈팅 가이드
│
├── day1/                             # 📅 1일차 실습
│   ├── lab1-1_mlops-environment-setup/
│   ├── lab1-2_hello-pipeline/
│   └── lab1-3_batch-pipeline/
│
├── day2/                             # 📅 2일차 실습
│   ├── lab2-1_fastapi-serving/
│   ├── lab2-2_mlflow-tracking/
│   └── lab2-3_kserve-deployment/
│
├── day3/                             # 📅 3일차 실습
    ├── lab3-1_drift-monitoring/
    ├── lab3-2_e2e-pipeline/
    ├── lab3-3_model-optimization/    # 🆕 ONNX & Quantization
    └── Project/                      # 팀 프로젝트

```

---

## 🚀 시작하기

### 1. Repository 클론

```bash
git clone https://github.com/fastcampusdevmlops/ha-mlops-pipeline.git
cd ha-mlops-pipeline
```

### 2. 환경 변수 설정

```bash
# 본인의 수강생 번호로 변경 (01~30)
export USER_NUM="01"

# 네임스페이스 설정
export NAMESPACE="kubeflow-user${USER_NUM}"

# 확인
echo "사용자: user${USER_NUM}"
echo "네임스페이스: ${NAMESPACE}"
```

### 3. AWS 자격 증명 설정

```bash
aws configure
# AWS Access Key ID: [제공된 Access Key]
# AWS Secret Access Key: [제공된 Secret Key]
# Default region name: ap-northeast-2
# Default output format: json
```

### 4. EKS 클러스터 연결

```bash
aws eks update-kubeconfig \
    --region ap-northeast-2 \
    --name mlops-training-cluster

# 연결 확인
kubectl get nodes
```

### 5. Kubeflow 접속

```bash
# 포트 포워딩
kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80

# 브라우저에서 접속
# http://localhost:8080
```

---

## 📚 실습 가이드

### Day 1 Labs

| Lab | 제목 | 시간 | 난이도 |
|-----|------|------|--------|
| [Lab 1-1](day1/lab1-1_mlops-environment-setup/) | MLOps 환경 구축 | 65분 | ⭐⭐ |
| [Lab 1-2](day1/lab1-2_hello-pipeline/) | Hello World Pipeline | 60분 | ⭐⭐ |
| [Lab 1-3](day1/lab1-3_batch-pipeline/) | Batch 데이터 파이프라인 | 90분 | ⭐⭐⭐ |

### Day 2 Labs

| Lab | 제목 | 시간 | 난이도 |
|-----|------|------|--------|
| [Lab 2-1](day2/lab2-1_fastapi-serving/) | FastAPI 모델 서빙 | 90분 | ⭐⭐⭐ |
| [Lab 2-2](day2/lab2-2_mlflow-tracking/) | MLflow Tracking & Registry | 80분 | ⭐⭐⭐ |
| [Lab 2-3](day2/lab2-3_kserve-deployment/) | KServe 배포 | 80분 | ⭐⭐⭐⭐ |

### Day 3 Labs

| Lab | 제목 | 시간 | 난이도 |
|-----|------|------|--------|
| [Lab 3-1](day3/lab3-1_drift-monitoring/) | Drift Monitoring & Auto-Retraining | 90분 | ⭐⭐⭐ |
| [Lab 3-2](day3/lab3-2_e2e-pipeline/) | E2E MLOps Pipeline | 80분 | ⭐⭐⭐⭐ |
| [Lab 3-3](day3/lab3-3_model-optimization/) | Model Optimization (ONNX & Quantization) | 40분 | ⭐⭐⭐ |

### Day 3 프로젝트

| 항목 | 내용 |
|------|------|
| [Project](day3/Project/) | 팀별 E2E 파이프라인 구축 |
| 시간 | 15:00 ~ 17:30 (2시간 30분) |
| 구성 | 6개 팀 × 5명 |
| 발표 | 팀별 15분 발표 + Q&A |

---

## 🛠️ 기술 스택

### 플랫폼 & 인프라

| 기술 | 버전 | 용도 |
|------|------|------|
| **AWS EKS** | 1.28+ | Kubernetes 클러스터 |
| **Kubeflow** | 1.8+ | ML 파이프라인 플랫폼 |
| **MLflow** | 2.9+ | 실험 추적 & 모델 레지스트리 |
| **KServe** | 0.11+ | 모델 서빙 |
| **Istio** | 1.17+ | 서비스 메시 |

### 스토리지

| 기술 | 용도 |
|------|------|
| **AWS S3** | 데이터 & 아티팩트 저장 |
| **AWS ECR** | 컨테이너 이미지 레지스트리 |
| **PostgreSQL** | MLflow 메타데이터 |
| **MinIO** | 오브젝트 스토리지 (로컬) |

### 개발 도구

| 기술 | 용도 |
|------|------|
| **Python 3.9+** | ML 개발 |
| **KFP SDK** | 파이프라인 정의 |
| **scikit-learn** | ML 모델링 |
| **ONNX Runtime** | 모델 최적화 |

---

## 📞 지원

### 교육 중 문제 발생 시

1. 📖 [트러블슈팅 가이드](docs/TROUBLESHOOTING.md) 확인
2. 🙋 강사에게 질문
3. 💬 옆 수강생과 협력

### 교육 전 환경 설정 문의

- 📧 교육 담당자 이메일
- 📱 교육 담당자 연락처

---

## 📝 참고 자료

### 공식 문서

- [Kubeflow 공식 문서](https://www.kubeflow.org/docs/)
- [MLflow 공식 문서](https://mlflow.org/docs/latest/index.html)
- [KServe 공식 문서](https://kserve.github.io/website/)
- [ONNX Runtime 문서](https://onnxruntime.ai/docs/)

### 추가 학습

- [AWS EKS 워크샵](https://www.eksworkshop.com/)
- [Kubernetes 공식 튜토리얼](https://kubernetes.io/docs/tutorials/)

---

## 📄 라이선스

이 교육 자료는 현대오토에버 내부 교육 목적으로 제작되었습니다.

---

© 2025 현대오토에버 MLOps Training
