# Lab 3-2: Troubleshooting Guide

## 🔧 일반적인 문제 해결

### 목차
1. [Prometheus 연결 문제](#1-prometheus-연결-문제)
2. [Grafana 문제](#2-grafana-문제)
3. [메트릭 수집 문제](#3-메트릭-수집-문제)
4. [Alert 문제](#4-alert-문제)
5. [GitHub Actions 문제](#5-github-actions-문제)
6. [KServe 배포 문제](#6-kserve-배포-문제)

---

## 1. Prometheus 연결 문제

### 증상: "Prometheus 연결 실패" 메시지

**원인**: 포트포워딩이 설정되지 않음

**해결**:
```bash
# 터미널에서 포트포워딩 실행
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# 백그라운드 실행
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &

# 연결 확인
curl http://localhost:9090/-/healthy
```

### 증상: Prometheus Pod이 실행되지 않음

**확인**:
```bash
kubectl get pods -n monitoring -l app=prometheus
kubectl describe pod -n monitoring -l app=prometheus
kubectl logs -n monitoring -l app=prometheus
```

**일반적인 원인**:
1. ConfigMap 오류
2. 리소스 부족
3. RBAC 권한 문제

**해결**:
```bash
# ConfigMap 확인
kubectl get configmap prometheus-config -n monitoring -o yaml

# 재배포
kubectl rollout restart deployment/prometheus -n monitoring
```

---

## 2. Grafana 문제

### 증상: 로그인 실패

**계정 정보**:
- Admin: `admin` / `admin123`
- 수강생: `user01`~`user15` / `mlops2025!`
- 강사: `user20` / `mlops2025!`

**비밀번호 재설정**:
```bash
# 포트포워딩
kubectl port-forward -n monitoring svc/grafana 3000:3000

# API로 비밀번호 변경 (admin 권한 필요)
curl -X PUT http://localhost:3000/api/admin/users/2/password \
  -u admin:admin123 \
  -H "Content-Type: application/json" \
  -d '{"password": "mlops2025!"}'
```

### 증상: 대시보드에 데이터가 표시되지 않음

**확인 사항**:
1. Datasource 연결 확인
2. 시간 범위 확인 (Last 30 minutes 등)
3. User ID 필터 확인

**Datasource 연결 테스트**:
```bash
# Grafana UI에서
# Configuration → Data Sources → Prometheus → Test
```

**직접 쿼리 테스트**:
```bash
curl "http://localhost:9090/api/v1/query?query=model_mae_score"
```

---

## 3. 메트릭 수집 문제

### 증상: 메트릭이 Prometheus에 없음

**단계별 확인**:

```bash
# 1. Metrics Exporter Pod 확인
kubectl get pods -n kubeflow-user01 -l app=metrics-exporter

# 2. Pod 로그 확인
kubectl logs -n kubeflow-user01 -l app=metrics-exporter -c exporter

# 3. 직접 메트릭 확인
kubectl port-forward -n kubeflow-user01 svc/metrics-exporter 8000:8000
curl http://localhost:8000/metrics | grep model_mae_score

# 4. Prometheus 타겟 확인
# http://localhost:9090/targets
```

### 증상: Metrics Exporter Pod이 CrashLoopBackOff

**일반적인 원인**:
1. Python 패키지 설치 실패
2. 포트 충돌
3. ConfigMap 마운트 문제

**해결**:
```bash
# 로그 확인
kubectl logs -n kubeflow-user01 -l app=metrics-exporter -c exporter --tail=50

# Pod 재시작
kubectl rollout restart deployment/metrics-exporter -n kubeflow-user01

# ConfigMap 확인
kubectl get configmap metrics-exporter-script -n kubeflow-user01 -o yaml
```

### 증상: Prometheus가 타겟을 스크랩하지 못함

**확인**:
```bash
# Prometheus UI → Status → Targets
# http://localhost:9090/targets

# 또는 API로 확인
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health=="down")'
```

**해결**:
```bash
# Prometheus ConfigMap 확인
kubectl get configmap prometheus-config -n monitoring -o yaml | grep -A 30 "user-metrics-exporters"

# 네임스페이스가 포함되어 있는지 확인
# kubeflow-user01 ~ kubeflow-user15, kubeflow-user20
```

---

## 4. Alert 문제

### 증상: Alert가 발생하지 않음

**확인**:
```bash
# Prometheus Alert Rules 확인
curl http://localhost:9090/api/v1/rules | jq '.data.groups'

# Active Alerts 확인
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts'
```

**Alert Rule 테스트**:
```promql
# Prometheus UI에서 직접 쿼리
model_mae_score > 0.45
```

### 증상: Alert Manager가 알림을 보내지 않음

**확인**:
```bash
# Alert Manager 상태
kubectl port-forward -n monitoring svc/alertmanager 9093:9093
curl http://localhost:9093/api/v2/alerts

# 로그 확인
kubectl logs -n monitoring -l app=alertmanager
```

---

## 5. GitHub Actions 문제

### 증상: Workflow가 트리거되지 않음

**확인 사항**:
1. GitHub Token 권한 확인
2. Workflow 파일 문법 확인
3. Branch 설정 확인

**수동 트리거 테스트**:
```bash
# GitHub API로 workflow_dispatch
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/retrain-model.yaml/dispatches \
  -d '{"ref":"main","inputs":{"user_id":"user01","drift_score":"0.5"}}'
```

### 증상: AWS 자격증명 오류

**GitHub Secrets 확인**:
- `AWS_ACCESS_KEY_ID`: AWS Access Key
- `AWS_SECRET_ACCESS_KEY`: AWS Secret Key

**테스트**:
```yaml
# 워크플로우에 디버그 step 추가
- name: Test AWS credentials
  run: |
    aws sts get-caller-identity
```

### 증상: Docker 빌드 실패

**일반적인 원인**:
1. Dockerfile 문법 오류
2. 베이스 이미지 접근 문제
3. 빌드 컨텍스트 문제

**로컬 테스트**:
```bash
docker build -t test-image .
```

---

## 6. KServe 배포 문제

### 증상: InferenceService가 Ready 상태가 아님

**확인**:
```bash
kubectl get inferenceservice -n kubeflow-user01
kubectl describe inferenceservice california-housing -n kubeflow-user01
```

**일반적인 원인**:
1. 이미지 풀 실패
2. 리소스 부족
3. Istio sidecar 문제

**해결**:
```bash
# Istio sidecar 비활성화
# InferenceService에 annotation 추가:
# sidecar.istio.io/inject: "false"

# Pod 이벤트 확인
kubectl get events -n kubeflow-user01 --sort-by='.lastTimestamp'
```

### 증상: 추론 요청 실패

**테스트**:
```bash
# 서비스 URL 확인
kubectl get inferenceservice california-housing -n kubeflow-user01 -o jsonpath='{.status.url}'

# 포트포워딩으로 테스트
kubectl port-forward -n kubeflow-user01 svc/california-housing-predictor 8080:80

# 추론 요청
curl -X POST http://localhost:8080/v1/models/california-housing:predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [[8.3252, 41.0, 6.984127, 1.023810, 322.0, 2.555556, 37.88, -122.23]]}'
```

---

## 🆘 긴급 복구 절차

### 전체 모니터링 스택 재배포

```bash
# 1. 기존 리소스 삭제
kubectl delete deployment prometheus grafana alertmanager -n monitoring

# 2. ConfigMap 재적용
kubectl apply -f manifests/prometheus/
kubectl apply -f manifests/grafana/
kubectl apply -f manifests/alertmanager/

# 3. 대기
kubectl wait --for=condition=ready pod -l app=prometheus -n monitoring --timeout=180s
kubectl wait --for=condition=ready pod -l app=grafana -n monitoring --timeout=180s

# 4. 확인
kubectl get pods -n monitoring
```

### 특정 사용자 Metrics Exporter 재배포

```bash
USER_NUM="01"
NAMESPACE="kubeflow-user${USER_NUM}"

# 삭제
kubectl delete deployment metrics-exporter -n $NAMESPACE

# 재배포
kubectl apply -f manifests/metrics-exporter/metrics-exporter-user${USER_NUM}.yaml

# 확인
kubectl get pods -n $NAMESPACE -l app=metrics-exporter
```

---

## 📞 추가 지원

문제가 해결되지 않으면:
1. `kubectl describe` 출력 저장
2. Pod 로그 저장 (`kubectl logs`)
3. 강사에게 문의

```bash
# 디버깅 정보 수집
kubectl get pods -A > pods.txt
kubectl get events -A --sort-by='.lastTimestamp' > events.txt
kubectl logs -n monitoring -l app=prometheus --tail=100 > prometheus.log
```
