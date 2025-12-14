# 🎯 Day 3 조별 프로젝트: E2E MLOps Pipeline

## 📋 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **소요시간** | 2시간 (실습 50분 + 발표 75분) |
| **참여자** | 15명 (5개 팀, 팀당 3명) |
| **목표** | 3일간 학습한 MLOps 기술을 종합하여 완전한 E2E ML 파이프라인 구축 |

---

## 🏆 평가 기준

| 항목 | 배점 | 기준 |
|------|------|------|
| **Kubeflow Pipeline** | 40점 | 최소 5개 컴포넌트, Succeeded 상태 |
| **MLflow Tracking** | 20점 | 최소 2회 Run, 파라미터/메트릭 기록 |
| **Feature Engineering** | 10점 | 1개 이상 파생 피처 생성 |
| **KServe 배포 (선택)** | 25점 | InferenceService 생성 및 API 테스트 |
| **발표** | 5점 | 시연, 코드 설명, Q&A |

---

## 📁 프로젝트 구조 (Notebook 기반)

```
day3/Project/
├── README.md                              # 이 파일
├── requirements.txt                       # Python 패키지
└── notebooks/
    ├── 01_project_pipeline.ipynb          # ⭐ 메인 실습 (템플릿)
    └── 02_project_solution.ipynb          # 솔루션 (발표 후 공개)
```

---

## 🚀 빠른 시작

### Step 1: Jupyter Notebook 열기

1. Kubeflow Dashboard 접속
2. Notebooks → `notebook-user01` 클릭
3. `day3/Project/notebooks/` 폴더로 이동
4. `01_project_pipeline.ipynb` 열기

### Step 2: 팀 설정 변경

노트북 상단에서 팀 설정을 변경합니다:

```python
# ⚠️ TODO: 반드시 변경하세요!
TEAM_NAME = "team-01"  # team-01 ~ team-06
```

### Step 3: 실습 진행

노트북의 셀을 순서대로 실행하며 TODO 부분을 구현합니다.

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

---

## 💡 Feature Engineering 아이디어

```python
# 1. 침실 비율
df['bedroom_ratio'] = df['AveBedrms'] / (df['AveRooms'] + 1e-6)

# 2. 인당 방 수
df['rooms_per_person'] = df['AveRooms'] / (df['AveOccup'] + 1e-6)

# 3. 소득 카테고리
df['income_category'] = pd.cut(df['MedInc'], bins=5, labels=['Low', 'MedLow', 'Med', 'MedHigh', 'High'])

# 4. Bay Area까지 거리
df['dist_to_bay'] = np.sqrt((df['Latitude'] - 37.87)**2 + (df['Longitude'] + 122.27)**2)

# 5. 밀집도
df['density'] = df['Population'] * df['AveOccup']
```

---

## 🎤 발표 형식 (15분)

| 순서 | 내용 | 시간 |
|------|------|------|
| 1 | 팀 소개 | 1분 |
| 2 | 아키텍처 설명 | 2분 |
| 3 | 구현 하이라이트 | 4분 |
| 4 | 시연 (Kubeflow/MLflow/KServe) | 4분 |
| 5 | 트러블슈팅 경험 | 1분 |
| 6 | Q&A | 3분 |

---

## ⏰ 타임라인

| 시간 | 내용 |
|------|------|
| 15:00 ~ 15:50 | 프로젝트 실습 (50분) |
| 15:50 ~ 16:05 | Team 1 발표 |
| 16:05 ~ 16:20 | Team 2 발표 |
| 16:20 ~ 16:35 | Team 3 발표 |
| 16:35 ~ 16:50 | Team 4 발표 |
| 16:50 ~ 17:05 | Team 5 발표 |
| 17:05 ~ 17:20 | Team 6 발표 |
| 17:20 ~ 17:30 | 강사 총평 |

---

## 🔧 트러블슈팅

### 1. Import 에러

```python
# ❌ 에러 발생 시
ImportError: cannot import name 'Input' from 'kfp.dsl'

# ✅ 해결 방법
!pip uninstall kfp -y
!pip install kfp==2.7.0 -q
# Kernel → Restart Kernel
```

### 2. 컴포넌트 연결 오류

```python
# ❌ 잘못된 방법
train_task = train_model(X_train=preprocess_task)

# ✅ 올바른 방법
train_task = train_model(X_train=preprocess_task.outputs["X_train_out"])
```

### 3. MLflow 연결 오류

```python
# 컴포넌트 내부에서 환경 변수 설정
import os
os.environ['MLFLOW_TRACKING_URI'] = mlflow_tracking_uri
mlflow.set_tracking_uri(mlflow_tracking_uri)
```

### 4. Namespace 오류

```bash
# 현재 네임스페이스 확인
kubectl config get-contexts

# 파이프라인 실행 시 namespace 파라미터를 현재 프로필과 동일하게 설정
```

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
- [ ] 화면 공유 준비 (Kubeflow UI, MLflow UI, Jupyter)
- [ ] Q&A 예상 질문 준비

---

## 🔗 참고 자료

- [Kubeflow Pipelines v2 Documentation](https://www.kubeflow.org/docs/components/pipelines/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [KServe Documentation](https://kserve.github.io/website/)
- [California Housing Dataset](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.fetch_california_housing.html)

---

**현대오토에버 MLOps Training**
