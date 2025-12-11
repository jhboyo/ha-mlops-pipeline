# 🚀 Kubeflow Jupyter Notebook 실행 가이드

## ✅ 실제 환경 정보

귀하의 Kubernetes 클러스터 환경:

```bash
Namespace: monitoring
Service: prometheus (ClusterIP: 10.100.37.232)
Port: 9090/TCP
Endpoint: 192.168.4.236:9090
```

### 완전한 Prometheus URL

```
http://prometheus.monitoring.svc.cluster.local:9090
```

---

## 📝 Kubeflow에서 Notebook 실행하기

### Step 1: Notebook Server 접속

1. **Kubeflow Dashboard** 접속
2. **Notebooks** 메뉴 선택
3. **본인의 Notebook Server** 선택
4. **CONNECT** 클릭

### Step 2: Notebook Upload

1. Jupyter 인터페이스에서 **Upload** 버튼 클릭
2. `monitoring_interactive.ipynb` 파일 선택
3. Upload 완료 후 파일 클릭하여 열기

### Step 3: Notebook 실행

**Cell → Run All** 클릭

모든 셀이 자동으로 실행됩니다:
- ✅ 환경 자동 감지 (Kubeflow/로컬)
- ✅ Prometheus 연결 (실제 환경 URL 사용)
- ✅ 메트릭 생성 (중복 방지)
- ✅ 메트릭 시각화

---

## 🎯 자동 환경 감지

Notebook은 **자동으로 환경을 감지**합니다:

```python
# Kubernetes 환경 확인
is_kubernetes = os.path.exists('/var/run/secrets/kubernetes.io')

if is_kubernetes:
    # Kubeflow: Service DNS 사용
    PROMETHEUS_URL = 'http://prometheus.monitoring.svc.cluster.local:9090'
else:
    # 로컬: Port-forward 사용
    PROMETHEUS_URL = 'http://localhost:9090'
```

**Kubeflow에서 실행 시 → 자동으로 올바른 URL 사용!** ✅

---

## 🔧 메트릭 중복 방지

Notebook 셀을 **여러 번 재실행**해도 에러가 발생하지 않습니다:

```python
# 중복 방지 헬퍼 함수
def get_or_create_metric(metric_class, name, documentation, labelnames, **kwargs):
    # 이미 존재하는지 확인
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name') and collector._name == name:
            return collector  # 재사용
    
    # 없으면 생성
    return metric_class(name, documentation, labelnames, **kwargs)

# 사용
counter = get_or_create_metric(Counter, 'my_counter', 'description', ['label'])
```

**이제 셀을 몇 번을 실행해도 OK!** ✅

---

## 📊 예상 출력

### 연결 테스트 성공 시

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

======================================================================
✅ 설정 완료! 이제 메트릭 실습을 시작할 수 있습니다
======================================================================
```

### Counter 실습 출력

```
======================================================================
                         Counter 실습
======================================================================

Counter: 단조 증가하는 값 (0에서 시작, 증가만 가능)
예: 요청 수, 에러 수, 완료된 작업 수

10개 예측 시뮬레이션...
  1. ✅ 예측 성공
  2. ✅ 예측 성공
  3. ❌ 예측 실패
  4. ✅ 예측 성공
  ...

✅ Counter 증가 완료!
```

---

## 🔧 문제 해결

### 문제 1: 연결 실패

**증상:**
```
❌ 연결 실패: Connection refused
```

**해결:**
```bash
# Prometheus 확인
kubectl get svc -n monitoring
kubectl get pods -n monitoring

# 예상 출력:
# NAME         TYPE        CLUSTER-IP      PORT(S)
# prometheus   ClusterIP   10.100.37.232   9090/TCP

# Pod 상태 확인
kubectl get pods -n monitoring | grep prometheus
# prometheus-xxx   1/1   Running
```

### 문제 2: 메트릭 중복 에러

**증상:**
```
ValueError: Duplicated timeseries in CollectorRegistry
```

**해결:**

이 Notebook은 **이미 중복 방지 로직이 내장**되어 있습니다!

만약 에러가 발생하면:
1. **Kernel → Restart Kernel** 실행
2. **Cell → Run All** 다시 실행

### 문제 3: PromQL 쿼리 No Data

**증상:**
```
ℹ️  No data (메트릭이 Prometheus에 수집되지 않았을 수 있습니다)
```

**원인:**

이 Notebook이 생성한 메트릭(`model_mae_score` 등)은 **로컬 HTTP Server(포트 8000)**에서만 노출됩니다. Prometheus가 이를 scrape하려면 별도 설정이 필요합니다.

**해결:**

Notebook에서 생성한 메트릭을 Prometheus가 수집하도록 하려면:

```bash
# Prometheus에 scrape 설정 추가 (선택적)
# 또는 manifests/monitoring/metrics-exporter 배포 사용
kubectl apply -f manifests/monitoring/metrics-exporter/
```

**참고**: 기본 메트릭(up, prometheus_build_info 등)은 항상 조회 가능합니다.

---

## 💡 유용한 팁

### Tip 1: 환경 변수로 URL 오버라이드

```bash
# Notebook 시작 전 설정
export PROMETHEUS_URL='http://custom-prometheus:9090'
jupyter notebook
```

### Tip 2: Kernel 재시작

메트릭 충돌이 발생하면:
- Jupyter: **Kernel → Restart Kernel**
- JupyterLab: **Kernel → Restart Kernel**

### Tip 3: 로그 확인

문제 발생 시 Notebook 출력을 자세히 확인하세요:
- 연결 테스트 결과
- 에러 메시지
- Hint 메시지

---

## ✅ 체크리스트

- [ ] Prometheus 서비스 배포 완료 (`kubectl get svc -n monitoring`)
- [ ] Prometheus Pod Running (`kubectl get pods -n monitoring`)
- [ ] Kubeflow Notebook Server 접속
- [ ] `monitoring_interactive.ipynb` 업로드 완료
- [ ] **Cell → Run All** 실행
- [ ] 연결 테스트 성공 확인
- [ ] 메트릭 생성 및 시각화 확인

---

## 📚 추가 리소스

### Prometheus UI 접속 (선택)

로컬에서 Prometheus UI를 보려면:

```bash
# Port-forward
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# 브라우저에서
http://localhost:9090
```

### Grafana 접속 (선택)

```bash
# Port-forward
kubectl port-forward -n monitoring svc/grafana 3000:3000

# 브라우저에서
http://localhost:3000
# ID: admin / PW: (kubectl get secret 확인)
```

---

## 🎉 완료!

이제 Kubeflow Notebook에서 **완벽하게 작동하는** 모니터링 실습을 진행할 수 있습니다!

### 핵심 포인트

1. ✅ **자동 환경 감지** - Kubeflow/로컬 자동 판별
2. ✅ **실제 URL 사용** - `http://prometheus.monitoring.svc.cluster.local:9090`
3. ✅ **중복 방지** - 셀 재실행 가능
4. ✅ **명확한 에러 메시지** - 문제 발생 시 해결 방법 제시

---

© 2024 현대오토에버 MLOps Training - Lab 3-2  
**Environment**: Kubeflow Jupyter Notebook (Kubernetes 클러스터 내부)  
**Prometheus**: http://prometheus.monitoring.svc.cluster.local:9090  
**Status**: ✅ Production Ready
