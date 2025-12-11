# 📓 Jupyter Notebook 실습 가이드

## 개요

Lab 3-2의 모니터링 시스템을 **Jupyter Notebook**을 통해 대화형으로 학습합니다.

---

## 📁 파일 목록

| 파일 | 설명 |
|------|------|
| `monitoring_interactive.ipynb` | 메인 실습 Notebook (최적화됨) |
| `KUBEFLOW_SETUP.md` | Kubeflow 환경 완전 가이드 |
| `PROMETHEUS_CONNECTION_FIX.md` | 연결 문제 해결 가이드 |
| `README.md` | 이 파일 |

---

## 🚀 빠른 시작

### Kubeflow Jupyter Notebook에서 (권장)

```
1. Kubeflow Dashboard → Notebooks → CONNECT
2. Upload → monitoring_interactive.ipynb
3. Cell → Run All
```

**자동으로 환경 감지 및 연결!** ✅

### 로컬 Jupyter에서

```bash
# Port-forward 실행 (별도 터미널)
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Notebook 실행
jupyter notebook monitoring_interactive.ipynb
```

---

## ✨ 주요 기능

### 1. 자동 환경 감지

Notebook이 **자동으로 환경을 감지**하고 적절한 Prometheus URL을 사용합니다:

- **Kubeflow**: `http://prometheus.monitoring.svc.cluster.local:9090`
- **로컬**: `http://localhost:9090` (Port-forward 필요)

### 2. 메트릭 중복 방지

Jupyter 셀을 **여러 번 재실행**해도 에러가 발생하지 않습니다:

```python
# 중복 방지 로직 내장
counter = get_or_create_metric(Counter, 'name', 'doc', ['labels'])
```

**더 이상 "Duplicated timeseries" 에러 없음!** ✅

### 3. 실제 환경 반영

실제 클러스터 환경에 맞춘 설정:

```
Namespace: monitoring
Service: prometheus
Port: 9090
```

### 4. 완전한 에러 처리

문제 발생 시 **명확한 해결 방법** 제시:

```
❌ 연결 실패: Connection refused

💡 해결 방법:
   kubectl get svc -n monitoring
   kubectl get pods -n monitoring
```

---

## 📚 실습 내용

### Section 1: 환경 설정
- 패키지 설치
- Prometheus 연결 (자동 환경 감지)
- 연결 테스트

### Section 2: Prometheus 메트릭
- Counter (카운터)
- Gauge (게이지)
- Histogram (히스토그램)

### Section 3: 메트릭 시각화
- MAE & R² 차트
- Latency 분포
- 성능 비교

### Section 4: PromQL 쿼리
- 기본 쿼리
- 집계 함수
- Percentile 계산

---

## 🎯 학습 목표

실습을 완료하면 다음을 할 수 있습니다:

- [ ] Prometheus 메트릭 타입 이해 (Counter, Gauge, Histogram)
- [ ] Custom Metrics 생성 및 노출
- [ ] PromQL 쿼리 작성
- [ ] 메트릭 시각화 (Matplotlib)
- [ ] 모니터링 시스템 구축

---

## 📖 상세 가이드

### Kubeflow 환경

완전한 Kubeflow 설정 가이드:  
👉 **[KUBEFLOW_SETUP.md](KUBEFLOW_SETUP.md)**

### 연결 문제 해결

Prometheus 연결 문제 해결:  
👉 **[PROMETHEUS_CONNECTION_FIX.md](PROMETHEUS_CONNECTION_FIX.md)**

---

## ⚡ 실행 예제

### 예상 출력 (연결 성공)

```
======================================================================
                     Prometheus 연결 설정
======================================================================

🏢 환경: Kubeflow Notebook (Kubernetes 클러스터 내부)
📡 Prometheus URL: http://prometheus.monitoring.svc.cluster.local:9090
📍 Namespace: monitoring
🔌 Service: prometheus
🔢 Port: 9090

======================================================================
                         연결 테스트
======================================================================

✅ Prometheus 연결 성공!
✅ 4개 타겟 발견

타겟 목록:
   1. [🟢 UP] prometheus           @ prometheus:9090
   2. [🟢 UP] grafana              @ grafana:3000
   3. [🟢 UP] alertmanager         @ alertmanager:9093
   4. [🟢 UP] metrics-exporter     @ metrics-exporter:8000
```

---

## 🔧 문제 해결

### "Duplicated timeseries" 에러

**이 Notebook은 이미 해결되어 있습니다!** ✅

만약 에러 발생 시:
1. Kernel → Restart Kernel
2. Cell → Run All

### "Connection refused" 에러

**Kubeflow에서**: Prometheus 배포 확인
```bash
kubectl get svc -n monitoring
kubectl get pods -n monitoring
```

**로컬에서**: Port-forward 실행
```bash
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

---

## 💡 유용한 팁

1. **환경 변수로 URL 변경**
   ```bash
   export PROMETHEUS_URL='http://custom:9090'
   ```

2. **Kernel 재시작**
   - 메트릭 충돌 시 Kernel 재시작

3. **진행 상황 저장**
   - Notebook은 자동 저장됨
   - 중요한 결과는 스크린샷 저장 권장

---

## ✅ 체크리스트

시작 전 확인사항:

- [ ] Prometheus 배포 완료 (`kubectl get svc -n monitoring`)
- [ ] Kubeflow Notebook 접속 완료
- [ ] `monitoring_interactive.ipynb` 업로드 완료

실습 완료 확인:

- [ ] Prometheus 연결 성공
- [ ] Counter/Gauge/Histogram 생성
- [ ] 메트릭 시각화 완료
- [ ] PromQL 쿼리 실행 성공

---

## 🎓 다음 단계

Notebook 실습 완료 후:

1. **Grafana 대시보드 구성** - 실시간 시각화
2. **Alertmanager 설정** - 알림 규칙
3. **프로덕션 배포** - Kubernetes 배포

---

© 2024 현대오토에버 MLOps Training - Lab 3-2  
**Notebook Version**: Optimized v2.0  
**Features**: 자동 환경 감지, 중복 방지, 실제 환경 반영  
**Status**: ✅ Production Ready
