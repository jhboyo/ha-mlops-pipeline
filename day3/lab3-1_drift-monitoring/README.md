# Lab 3-1: Data Drift Monitoring & Auto-Retraining

## 📋 실습 개요

| 항목 | 내용 |
|------|------|
| **소요시간** | 90분 |
| **난이도** | ⭐⭐⭐ |
| **목표** | 프로덕션 모델의 Data Drift 자동 감지 및 재학습 파이프라인 구축 |

## 🎯 학습 목표

이 실습을 통해 다음을 학습합니다:
- **Data Drift 개념** 이해 및 감지 방법
- **Kubeflow Pipeline**을 활용한 Drift 모니터링 자동화
- **MLflow**를 사용한 메트릭 추적
- **조건부 재학습** 파이프라인 구현
- 프로덕션 MLOps 모니터링 시스템 구축

---

## 🏗️ 실습 구조

```
Lab 3-1: Drift Monitoring (90분)
├── Part 1: Drift Detection (30분)
│   ├── 로컬에서 Drift 분석
│   ├── Statistical Test (KS Test)
│   └── HTML 리포트 생성
├── Part 2: Monitoring Pipeline (30분)
│   ├── Drift 감지 자동화
│   ├── MLflow 메트릭 기록
│   └── Alert 시스템
└── Part 3: Auto-Retraining (30분)
    ├── Drift Score 확인
    ├── 조건부 모델 재학습
    └── 자동 배포
```

---

## 📁 파일 구조

```
lab3-1_drift-monitoring/
├── README.md                         # ⭐ 이 파일 (실습 가이드)
├── requirements.txt                  # Python 패키지
├── scripts/
│   ├── 1_detect_drift.py            # Part 1: 로컬 Drift 분석 (30분)
│   ├── 2_monitor_pipeline.py        # Part 2: 모니터링 파이프라인 (30분)
│   └── 3_retrain_pipeline.py        # Part 3: 자동 재학습 (30분)
└── notebooks/
    └── drift_analysis.ipynb         # Jupyter Notebook 실습
```

---

## 🚀 Part 1: Drift Detection (30분)

### 학습 목표
- Data Drift의 개념 이해
- Statistical Test를 사용한 Drift 감지
- HTML 리포트 생성 및 분석

### Step 1-1: 패키지 설치

```bash
cd lab3-1_drift-monitoring
pip install -r requirements.txt
```

### Step 1-2: Drift 분석 실행

```bash
python scripts/1_detect_drift.py
```

**예상 결과:**
```
=== Data Drift Detection ===

Loading California Housing data...
Reference data: 5000 samples
Current data: 3000 samples (with simulated drift)

Performing Drift Detection...
Feature: MedInc     - Drift: Yes (p-value: 0.0000)
Feature: HouseAge   - Drift: No  (p-value: 0.1234)
...

Drift Summary:
- Drifted Features: 1/9
- Drift Score: 0.11

✅ HTML report generated: drift_report.html
```

### Step 1-3: 리포트 확인

브라우저에서 `drift_report.html` 열기
- Feature 분포 비교
- Drift Score 확인
- Statistical Test 결과

---

## 🔄 Part 2: Monitoring Pipeline (30분)

### 학습 목표
- Kubeflow Pipeline으로 Drift 모니터링 자동화
- MLflow에 메트릭 기록
- Alert 시스템 구축

### Step 2-1: Pipeline 컴파일

```bash
python scripts/2_monitor_pipeline.py
```

**출력:**
```
============================================================
Pipeline compiled successfully!
============================================================

Output file: drift_monitoring_pipeline.yaml

Next steps:
  1. Upload pipeline to Kubeflow UI
  2. Click Create Run
  3. Set parameters:
     - sample_size: 1000
     - drift_threshold: 0.3
  4. Click Start to execute
```

### Step 2-2: Kubeflow UI에 업로드

1. Kubeflow UI 접속
2. **Pipelines** → **Upload pipeline**
3. `drift_monitoring_pipeline.yaml` 선택
4. **Create Run**
5. Parameters 설정:
   - `sample_size`: 1000
   - `drift_threshold`: 0.3
6. **Start** 클릭

### Step 2-3: 실행 결과 확인

**Kubeflow UI - Graph:**
```
✓ Collect production data
✓ Detect drift
✓ Log metrics
✓ Send alert
```

**Logs:**
```
Data collection simulated: 1000 samples
Loading data for drift detection...
Drift Score: 0.11
Drifted Features: 1/9
Drift Detected: False
Metrics logged to MLflow
OK: No significant drift detected
```

### Step 2-4: MLflow 확인

```bash
kubectl port-forward -n mlflow-system svc/mlflow-server-service 5000:5000
```

브라우저: `http://localhost:5000`
- Experiment: "drift-monitoring-pipeline"
- Metrics:
  - drift_score: 0.11
  - drift_detected: 0
  - n_drifted: 1

---

## 🔁 Part 3: Auto-Retraining Pipeline (30분)

### 학습 목표
- Drift 감지 시 자동 재학습
- 조건부 파이프라인 실행
- MLflow에 모델 메트릭 기록

### Step 3-1: Pipeline 컴파일

```bash
python scripts/3_retrain_pipeline.py
```

**출력:**
```
============================================================
Pipeline compiled successfully!
============================================================

Output file: auto_retrain_pipeline.yaml
```

### Step 3-2: Kubeflow UI에 업로드

1. Kubeflow UI → **Upload pipeline**
2. `auto_retrain_pipeline.yaml` 선택
3. **Create Run**
4. Parameters:
   - `drift_threshold`: 0.3
   - `train_size`: 5000
5. **Start**

### Step 3-3: 실행 결과 확인

**Kubeflow UI - Graph:**
```
✓ Check drift and decide
✓ Retrain model
✓ Deploy model
```

**Logs:**
```
Drift Score: 0.11
Should Retrain: False

Loading training data...
Training data: 5000 samples
Model trained successfully
Model version: db4b3de4
MAE: 0.3901

Deploying model version: db4b3de4
Model deployed successfully!
```

### Step 3-4: MLflow 확인

- Experiment: "auto-retraining"
- Run name: "retrained_model"
- Metrics:
  - mae: 0.3901
- Parameters:
  - n_estimators: 100
  - train_size: 5000

---

## 📊 전체 워크플로우

### 1. 모니터링 파이프라인 (정기 실행)
```
Collect Data → Detect Drift → Log Metrics → Send Alert
    ↓              ↓              ↓             ↓
  1000샘플      Drift Score    MLflow        Slack/Email
               (0.11 < 0.3)
```

### 2. 자동 재학습 파이프라인 (조건부 실행)
```
Check Drift → Retrain Model → Deploy Model
    ↓              ↓              ↓
MLflow 조회   모델 학습        KServe 배포
(Score > 0.3) MAE: 0.39      (시뮬레이션)
```

---

## 💡 핵심 개념

### Data Drift란?
프로덕션 데이터의 분포가 학습 데이터와 달라지는 현상

**원인:**
- 사용자 행동 패턴 변화
- 시장 트렌드 변화
- 계절적 요인
- 데이터 수집 오류

**영향:**
- 모델 성능 저하
- 예측 정확도 감소
- 비즈니스 지표 악화

### Drift Detection 방법

#### 1. Statistical Tests
```python
from scipy.stats import ks_2samp

# Kolmogorov-Smirnov Test
statistic, p_value = ks_2samp(reference_data, current_data)
drift_detected = p_value < 0.05
```

#### 2. Drift Score
```python
n_drifted_features = 1  # p-value < 0.05인 feature 수
total_features = 9
drift_score = n_drifted_features / total_features  # 0.11
```

#### 3. Threshold
```python
drift_threshold = 0.3  # 30%
if drift_score > drift_threshold:
    trigger_retraining()
```

---

## 🔧 트러블슈팅

### 문제 1: Pipeline 업로드 실패
```bash
# YAML 재생성
python scripts/2_monitor_pipeline.py

# 파일 확인
ls -lh drift_monitoring_pipeline.yaml
```

### 문제 2: MLflow 연결 실패
```bash
# MLflow 서비스 확인
kubectl get svc -n mlflow-system

# Port forward
kubectl port-forward -n mlflow-system svc/mlflow-server-service 5000:5000
```

### 문제 3: 패키지 에러
```bash
# 패키지 재설치
pip install -r requirements.txt --force-reinstall
```

---

## ✅ 완료 체크리스트

### Part 1: Drift Detection
- [ ] 패키지 설치 완료
- [ ] `1_detect_drift.py` 실행 성공
- [ ] `drift_report.html` 생성 확인
- [ ] Drift Score 이해

### Part 2: Monitoring Pipeline
- [ ] `2_monitor_pipeline.py` 컴파일 성공
- [ ] Kubeflow에 업로드 완료
- [ ] Pipeline 실행 성공
- [ ] MLflow 메트릭 확인

### Part 3: Auto-Retraining Pipeline
- [ ] `3_retrain_pipeline.py` 컴파일 성공
- [ ] Pipeline 실행 성공
- [ ] 재학습 로직 이해
- [ ] MLflow에서 결과 확인

---

## 📚 추가 자료

### Drift Detection
- [Evidently AI Documentation](https://docs.evidentlyai.com/)
- [Data Drift in ML](https://www.tensorflow.org/tfx/guide/tfdv)

### Statistical Tests
- [Kolmogorov-Smirnov Test](https://en.wikipedia.org/wiki/Kolmogorov%E2%80%93Smirnov_test)
- [Chi-Square Test](https://en.wikipedia.org/wiki/Chi-squared_test)

### MLOps Monitoring
- [Google MLOps Guide](https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning)
- [AWS SageMaker Model Monitor](https://docs.aws.amazon.com/sagemaker/latest/dg/model-monitor.html)

---

## 🎯 다음 단계

### Lab 3-2: E2E Pipeline
완전한 MLOps 파이프라인 통합
- 데이터 로드 → 전처리 → 학습 → 평가 → 배포

### Project
팀 프로젝트: 실전 MLOps 시스템 구축

---

© 2025 현대오토에버 MLOps Training
