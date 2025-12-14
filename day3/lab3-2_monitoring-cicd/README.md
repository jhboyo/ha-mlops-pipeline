# Lab 3-2: Model Monitoring & CI/CD Pipeline

## 📋 실습 개요

| 항목 | 내용 |
|------|------|
| **소요시간** | 90분 (Part 1: 45분 / Part 2: 45분) |
| **난이도** | ⭐⭐⭐⭐ |
| **목표** | 모델 모니터링, Drift 감지, CI/CD 자동화 구현 |
| **사전 조건** | Lab 3-1 완료, GitHub 계정, Monitoring Stack 배포됨 |

## 🎯 학습 목표

1. Prometheus/Grafana를 활용한 모델 성능 모니터링
2. Model Drift 감지 및 Alert 설정
3. GitHub Actions 기반 CI/CD 파이프라인 이해
4. Drift 기반 자동 재학습 트리거 구현

---

## 📁 파일 구조

```
lab3-2_monitoring-cicd/
├── README.md
├── notebooks/
│   ├── part1_monitoring.ipynb    # Part 1 실습 (Notebook)
│   └── part2_cicd.ipynb          # Part 2 실습 (Notebook)
├── scripts/
│   ├── 3_simulate_drift.py       # Drift 시뮬레이션 (Script 필수)
│   └── 4_trigger_retrain.py      # 재학습 트리거 (Script 필수)
└── .github/workflows/
    ├── ci-test.yaml              # CI Pipeline
    ├── cd-deploy.yaml            # CD Pipeline
    └── retrain-model.yaml        # 자동 재학습 Pipeline
```

## 🔄 실습 방식: Notebook + Script

| 실습 내용 | 방식 | 파일 |
|----------|------|------|
| 메트릭 조회 및 시각화 | **Notebook** | `part1_monitoring.ipynb` |
| Alert 상태 확인 | **Notebook** | `part1_monitoring.ipynb` |
| Drift 분석 리포트 | **Notebook** | `part1_monitoring.ipynb` |
| CI/CD 아키텍처 이해 | **Notebook** | `part2_cicd.ipynb` |
| Drift 감지 함수 실행 | **Notebook** | `part2_cicd.ipynb` |
| 통합 테스트 | **Notebook** | `part2_cicd.ipynb` |
| **Drift 시뮬레이션** | **Script** | `3_simulate_drift.py` |
| **GitHub 재학습 트리거** | **Script** | `4_trigger_retrain.py` |

---

## ⚙️ 사전 준비

### 1. 환경 변수 설정

```bash
# 본인의 사용자 번호로 변경
export USER_NUM="07"
export USER_ID="user${USER_NUM}"
export NAMESPACE="kubeflow-${USER_ID}"

echo "사용자: ${USER_ID}"
echo "네임스페이스: ${NAMESPACE}"
```

### 2. 포트포워딩 설정

```bash
# Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &

# Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000 &
```

### 3. 접속 정보

| 서비스 | URL | 계정 |
|--------|-----|------|
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin / mlops2025! |

---

## 📊 Part 1: Model Monitoring (45분)

> **실습 파일**: `notebooks/part1_monitoring.ipynb`

### 학습 내용

1. Prometheus 연결 및 메트릭 조회
2. 시계열 데이터 시각화
3. 전체 사용자 메트릭 비교
4. Alert 상태 확인
5. Drift 리포트 생성

### Step 1-1: Notebook 실행

Kubeflow Jupyter에서 `part1_monitoring.ipynb` 열기

### Step 1-2: 사용자 번호 설정

```python
# ⚠️ 본인의 사용자 번호로 변경
USER_NUM = "07"
```

### Step 1-3: 메트릭 조회 (Notebook)

```python
# Prometheus에서 메트릭 조회
mae_result = query_prometheus(f'model_mae_score{{user_id="{USER_ID}"}}')
r2_result = query_prometheus(f'model_r2_score{{user_id="{USER_ID}"}}')
```

### Step 1-4: Drift 시뮬레이션 (Script 필수)

> ⚠️ **Notebook에서 실행 불가** - kubectl 명령어 필요

**터미널에서 실행:**
```bash
cd day3/lab3-2_monitoring-cicd

# Drift 시뮬레이션 (high 레벨)
python scripts/3_simulate_drift.py --user user${USER_NUM} --drift-level high
```

**예상 출력:**
```
============================================================
  Drift Simulation for user07
============================================================

📉 Before Drift:
   MAE: 0.3850
   R²:  0.8150

🔄 Simulating HIGH drift...

📈 After Drift:
   ⚠️ MAE: 0.5005 (+30.0%)
   ⚠️ R²:  0.6928 (-15.0%)

🚨 Alert 조건 충족!
```

### Step 1-5: Drift 복원 (선택)

```bash
# 정상 상태로 복원
python scripts/3_simulate_drift.py --user user${USER_NUM} --reset
```

### Step 1-6: Grafana 대시보드 확인

1. http://localhost:3000 접속
2. **MLOps Dashboard** 선택
3. User ID 드롭다운에서 본인 선택
4. MAE, R² 변화 확인

---

## 🚀 Part 2: CI/CD Pipeline (45분)

> **실습 파일**: `notebooks/part2_cicd.ipynb`

### 학습 내용

1. GitHub Actions CI/CD 아키텍처 이해
2. CI/CD 워크플로우 구조 분석
3. Drift 감지 함수 실행
4. 재학습 트리거 실행

### 2-1. GitHub 사전 설정

#### Personal Access Token (PAT) 발급

1. GitHub → Settings → Developer settings → Personal access tokens
2. **Tokens (classic)** → Generate new token
3. 권한 설정:
   - ☑️ `repo` (Full control)
   - ☑️ `workflow`
4. 토큰 복사 및 저장

#### Repository Secrets 등록

GitHub Repository → Settings → Secrets and variables → Actions

| Secret Name | 값 |
|-------------|-----|
| `AWS_ACCESS_KEY_ID` | AWS Access Key |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key |
| `PAT_TOKEN` | GitHub Personal Access Token |

### 2-2. 워크플로우 파일 설정

`.github/workflows/retrain-model.yaml` 파일 확인:

```yaml
# prepare-data job의 Install dependencies
- name: Install dependencies
  run: |
    pip install boto3 pandas scikit-learn pyarrow

# trigger-deployment job의 Trigger CD Pipeline
- name: Trigger CD Pipeline
  uses: peter-evans/repository-dispatch@v3
  with:
    token: ${{ secrets.PAT_TOKEN }}
    event-type: model-retrained
    client-payload: |
      {
        "user_id": "${{ github.event.inputs.user_id }}",
        ...
      }
```

### 2-3. Notebook 실습

Kubeflow Jupyter에서 `part2_cicd.ipynb` 열기

**주요 실습 내용:**
- CI/CD 아키텍처 다이어그램 확인
- 워크플로우 YAML 구조 분석
- Drift 감지 함수 (`check_model_drift`) 실행
- 재학습 트리거 시뮬레이션 (실제 호출 아님)

### 2-4. 재학습 트리거 (Script 필수)

> ⚠️ **Notebook에서는 시뮬레이션만 가능** - 실제 GitHub API 호출은 Script 필요

**환경 변수 설정:**
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export GITHUB_REPO="your-org/mlops-repo"
export USER_NUM="07"
```

**트리거 실행:**
```bash
cd day3/lab3-2_monitoring-cicd

# Drift 확인만 (dry-run)
python scripts/4_trigger_retrain.py --check-drift

# 실제 GitHub Actions 트리거
python scripts/4_trigger_retrain.py --check-drift --no-dry-run

# 강제 트리거 (Drift 상관없이)
python scripts/4_trigger_retrain.py --force-trigger --no-dry-run
```

**예상 출력:**
```
============================================================
  Auto-Retrain Trigger Check
============================================================

👤 사용자: user07
📅 시간: 2025-12-14 10:06:42

📊 현재 메트릭:
   MAE: 0.5005
   R²:  0.6928

🔍 Drift 분석:
   Detected: 🚨 YES
   Score: 0.1122
   Reason: MAE(0.5005) > 0.45

🚀 GitHub Actions 트리거...
   Repository: your-org/mlops-repo
   Workflow: retrain-model.yaml

✅ 재학습 트리거 성공!
   확인: https://github.com/your-org/mlops-repo/actions
```

### 2-5. GitHub Actions 실행 확인

1. GitHub Repository → **Actions** 탭
2. **Retrain Model on Drift** 워크플로우 확인
3. 각 Job 실행 상태 확인:
   - `prepare-data`: 데이터 준비
   - `retrain`: 모델 재학습
   - `trigger-deployment`: CD 파이프라인 트리거

---

## 📊 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MLOps Monitoring & CI/CD                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │
│  │   Model     │────►│  Metrics    │────►│ Prometheus  │           │
│  │  Serving    │     │  Exporter   │     │   Server    │           │
│  │  (KServe)   │     │             │     │             │           │
│  └─────────────┘     └─────────────┘     └──────┬──────┘           │
│                                                  │                   │
│                                                  ▼                   │
│                      ┌─────────────┐     ┌─────────────┐           │
│                      │   Grafana   │◄────│    Alert    │           │
│                      │  Dashboard  │     │   Manager   │           │
│                      └─────────────┘     └─────────────┘           │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    Retrain Trigger                             │ │
│  │   python scripts/4_trigger_retrain.py --check-drift --no-dry-run │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐           │
│  │   GitHub    │────►│  CD: Build  │────►│  CD: Deploy │           │
│  │   Actions   │     │  & Push ECR │     │  to KServe  │           │
│  └─────────────┘     └─────────────┘     └─────────────┘           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📈 메트릭 상세

| 메트릭 | 타입 | 설명 | 정상 범위 | Alert 임계값 |
|--------|------|------|-----------|--------------|
| `model_mae_score` | Gauge | Mean Absolute Error | 0.30 ~ 0.45 | > 0.45 |
| `model_r2_score` | Gauge | R² Score | 0.75 ~ 0.95 | < 0.75 |
| `model_prediction_total` | Counter | 누적 예측 횟수 | - | - |
| `model_prediction_latency` | Histogram | 예측 지연시간 | - | P95 > 1s |

### PromQL 예시

```promql
# MAE 조회
model_mae_score{user_id="user07"}

# R² 조회
model_r2_score{user_id="user07"}

# 최근 1시간 평균 MAE
avg_over_time(model_mae_score{user_id="user07"}[1h])

# Drift 감지 (MAE 변화율)
delta(model_mae_score{user_id="user07"}[30m])
```

---

## 🛠️ 문제 해결

### Prometheus 연결 실패

```bash
# 포트포워딩 확인
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Pod 상태 확인
kubectl get pods -n monitoring -l app=prometheus
```

### GitHub Token 권한 오류

**에러**: `Error: Resource not accessible by integration`

**해결**:
1. PAT에 `repo`, `workflow` 권한 있는지 확인
2. Repository Secrets에 `PAT_TOKEN` 등록

### Workflow 트리거 실패

```bash
# 수동 API 테스트
curl -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/retrain-model.yaml/dispatches \
  -d '{"ref":"main","inputs":{"user_id":"user07","drift_score":"0.5"}}'
```

### Drift 시뮬레이션 실패

```bash
# Pod 상태 확인
kubectl get pods -n kubeflow-user${USER_NUM} -l app=metrics-exporter

# 로그 확인
kubectl logs -n kubeflow-user${USER_NUM} -l app=metrics-exporter
```

---

## ✅ 완료 체크리스트

### Part 1: Monitoring (Notebook)
- [ ] `part1_monitoring.ipynb` 실행
- [ ] Prometheus 메트릭 조회 성공
- [ ] 시계열 차트 확인
- [ ] Alert 상태 확인

### Part 1: Monitoring (Script)
- [ ] `3_simulate_drift.py` 실행
- [ ] Drift 시뮬레이션 확인
- [ ] Grafana 대시보드에서 변화 확인

### Part 2: CI/CD (사전 설정)
- [ ] GitHub PAT 발급 완료
- [ ] Repository Secrets 등록 (AWS, PAT_TOKEN)
- [ ] 환경 변수 설정 완료

### Part 2: CI/CD (Notebook)
- [ ] `part2_cicd.ipynb` 실행
- [ ] CI/CD 아키텍처 이해
- [ ] Drift 감지 함수 실행

### Part 2: CI/CD (Script)
- [ ] `4_trigger_retrain.py` 실행
- [ ] GitHub Actions 워크플로우 트리거 성공
- [ ] 각 Job 실행 확인

---

## 📚 참고 자료

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub REST API - Workflow Dispatch](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event)

---

© 2025 현대오토에버 MLOps Training