# 🔧 Prometheus 연결 문제 해결

## ❌ 에러 증상

```
Invalid URL 'prometheus.monitoring.svc.cluster.local/api/v1/query': 
No scheme supplied. Perhaps you meant https://...?
```

## 🔍 문제 원인

Prometheus URL에 `http://` 스킴이 누락되어 있습니다.

## ✅ 해결 방법

### 방법 1: Port-forward 사용 (권장)

**1. 새 터미널에서 Port-forward 실행**
```bash
kubectl port-forward -n monitoring-system svc/prometheus-server 9090:80
```

**2. Notebook의 Prometheus 연결 셀을 다음으로 수정**
```python
# Prometheus 연결 설정
import os
import requests

# 환경 변수 또는 기본값 사용
PROMETHEUS_URL = os.getenv('PROMETHEUS_URL', 'http://localhost:9090')

def query_prometheus(query, timeout=5):
    """Prometheus 쿼리 실행"""
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={'query': query},
            timeout=timeout
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': f'HTTP {response.status_code}'}
    except requests.exceptions.ConnectionError:
        return {
            'error': 'Connection failed', 
            'hint': f'Prometheus가 {PROMETHEUS_URL}에서 실행 중인지 확인하세요'
        }
    except Exception as e:
        return {'error': str(e)}

# 연결 테스트
print(f"📡 Prometheus URL: {PROMETHEUS_URL}")
try:
    test = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={'query': 'up'}, timeout=2)
    if test.status_code == 200:
        print("✅ Prometheus 연결 성공!")
    else:
        print(f"❌ 연결 실패: HTTP {test.status_code}")
except:
    print("❌ Prometheus에 연결할 수 없습니다")
    print("   Port-forward 실행: kubectl port-forward -n monitoring-system svc/prometheus-server 9090:80")
```

**3. PromQL 쿼리 셀 실행**

### 방법 2: 환경 변수 설정

**Kubernetes 클러스터 내부에서 실행하는 경우:**

```python
# Notebook 셀에서
import os
os.environ['PROMETHEUS_URL'] = 'http://prometheus-server.monitoring-system.svc.cluster.local:80'
```

또는 Notebook 시작 전:

```bash
export PROMETHEUS_URL='http://prometheus-server.monitoring-system.svc.cluster.local:80'
jupyter notebook
```

### 방법 3: 직접 URL 수정

**잘못된 코드:**
```python
PROMETHEUS_URL = "prometheus.monitoring.svc.cluster.local"  # ❌ 스킴 없음
```

**올바른 코드:**
```python
PROMETHEUS_URL = "http://prometheus-server.monitoring-system.svc.cluster.local:80"  # ✅
```

---

## 🧪 연결 테스트

Notebook에 다음 셀을 추가하여 연결을 테스트하세요:

```python
import requests

PROMETHEUS_URL = "http://localhost:9090"  # 또는 실제 URL

print("Prometheus 연결 테스트...")
print(f"URL: {PROMETHEUS_URL}")

try:
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={'query': 'up'},
        timeout=3
    )
    
    if response.status_code == 200:
        print("✅ 성공!")
        data = response.json()
        if data.get('status') == 'success':
            results = data.get('data', {}).get('result', [])
            print(f"✅ {len(results)}개 타겟 발견")
            for r in results[:3]:
                print(f"   - {r.get('metric', {})}")
    else:
        print(f"❌ HTTP {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ 연결 실패")
    print("   해결: kubectl port-forward -n monitoring-system svc/prometheus-server 9090:80")
except Exception as e:
    print(f"❌ 에러: {e}")
```

---

## 📝 완전한 예제

```python
# 1. 패키지 import
import requests
import os

# 2. URL 설정 (자동 감지)
PROMETHEUS_URL = os.getenv('PROMETHEUS_URL')

if not PROMETHEUS_URL:
    # Kubernetes 내부인지 확인
    if os.path.exists('/var/run/secrets/kubernetes.io'):
        PROMETHEUS_URL = "http://prometheus-server.monitoring-system.svc.cluster.local:80"
    else:
        # 로컬 개발 환경
        PROMETHEUS_URL = "http://localhost:9090"

print(f"📡 Prometheus URL: {PROMETHEUS_URL}")

# 3. 쿼리 함수
def query_prometheus(query):
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={'query': query},
            timeout=5
        )
        return response.json() if response.status_code == 200 else {'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'error': str(e)}

# 4. 테스트
result = query_prometheus('up')
print(f"결과: {result.get('status', 'error')}")
```

---

## 💡 추가 팁

### Port-forward 유지

Port-forward는 연결이 끊어질 수 있으므로, 백그라운드로 실행하거나 별도 터미널에서 실행하세요:

```bash
# 백그라운드 실행
kubectl port-forward -n monitoring-system svc/prometheus-server 9090:80 &

# 또는 tmux/screen 사용
tmux new -s prometheus
kubectl port-forward -n monitoring-system svc/prometheus-server 9090:80
# Ctrl+B, D로 detach
```

### Jupyter Kernel 재시작

환경 변수를 변경한 경우 Kernel을 재시작해야 적용됩니다:
- Jupyter: Kernel → Restart Kernel
- JupyterLab: Kernel → Restart Kernel

---

## ✅ 확인 체크리스트

- [ ] Port-forward 실행 중
- [ ] PROMETHEUS_URL에 `http://` 또는 `https://` 포함
- [ ] 연결 테스트 셀 실행 성공
- [ ] PromQL 쿼리 셀 실행 성공

---

© 2024 현대오토에버 MLOps Training  
**문제**: Prometheus URL 스킴 누락  
**해결**: `http://` 추가 + Port-forward
