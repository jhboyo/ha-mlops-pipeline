# Lab 3-3: Model Optimization (ONNX & Quantization)

## 📋 실습 개요

| 항목 | 내용 |
|------|------|
| **소요시간** | 40분 |
| **난이도** | ⭐⭐⭐ |
| **목표** | ONNX 변환과 양자화를 통한 모델 최적화 및 추론 성능 향상 |

## 🎯 학습 목표

이 실습을 통해 다음을 학습합니다:
- **ONNX 포맷** 이해 및 Scikit-learn 모델 변환
- **동적 양자화(Dynamic Quantization)** 적용
- 모델 **크기 최적화** 및 **추론 속도 향상**
- **MLflow**를 통한 최적화 결과 추적
- **엣지 디바이스 배포**를 위한 모델 경량화 기법

---

## 🏗️ 실습 구조

```
Lab 3-3: Model Optimization (40분)
├── Part 1: ONNX Conversion (15분)
│   ├── Scikit-learn 모델 학습
│   ├── ONNX 포맷 변환
│   ├── 모델 크기 비교
│   └── 예측 결과 검증
├── Part 2: Quantization (10분)
│   ├── 동적 양자화 적용
│   ├── 크기 추가 감소 확인
│   └── 정확도 손실 검증
└── Part 3: Benchmark (15분)
    ├── 추론 속도 벤치마크
    ├── MLflow 메트릭 기록
    └── 최적화 결과 분석
```

---

## 📁 파일 구조

```
lab3-3_model-optimization/
├── README.md                         # ⭐ 이 파일 (실습 가이드)
├── requirements.txt                  # Python 패키지
├── scripts/
│   ├── 1_onnx_conversion.py         # Part 1: ONNX 변환 (15분)
│   ├── 2_quantization.py            # Part 2: 양자화 (10분)
│   └── 3_benchmark.py               # Part 3: 벤치마크 (15분)
├── notebooks/
│   └── model_optimization.ipynb     # Jupyter Notebook 실습
└── outputs/                          # 생성된 모델 파일
    ├── model_original.joblib        # 원본 sklearn 모델
    ├── model_optimized.onnx         # ONNX 변환 모델
    └── model_quantized.onnx         # 양자화 모델
```

---

## 🔧 사전 요구사항

### 필수 조건
- ✅ Lab 3-1 완료 (Drift Monitoring)
- ✅ Lab 3-2 완료 (E2E Pipeline)
- ✅ Kubeflow Jupyter Notebook 접속 가능
- ✅ MLflow Server 접속 가능
- ✅ Python 3.9+ 환경

### 환경 변수 설정

```bash
# 터미널에서 실행 (Kubeflow Jupyter 환경)
export MLFLOW_TRACKING_URI=http://mlflow-server-service.mlflow-system.svc.cluster.local:5000
```

---

## 📦 패키지 설치

```bash
cd lab3-3_model-optimization
pip install -r requirements.txt
```

**requirements.txt 내용:**
```
scikit-learn>=1.3.0
onnx>=1.14.0
onnxruntime>=1.16.0
skl2onnx>=1.16.0
mlflow>=2.9.0
joblib>=1.3.0
numpy>=1.24.0
```

---

## 🚀 Part 1: ONNX Conversion (15분)

### 학습 목표
- ONNX (Open Neural Network Exchange) 포맷 이해
- Scikit-learn 모델을 ONNX로 변환
- 변환 전후 모델 크기 및 예측 결과 비교

### Step 1-1: ONNX 변환 실행

```bash
python scripts/1_onnx_conversion.py
```

### 예상 결과

```
============================================================
  Lab 3-3 Part 1: ONNX Conversion
============================================================

Step 1: 데이터 로드 및 모델 학습
────────────────────────────────────────
  📊 Iris 데이터셋 로드 중...
  📊 학습 데이터: 120개
  📊 테스트 데이터: 30개
  🏋️ RandomForest 모델 학습 중...
  📈 테스트 정확도: 1.0000

Step 2: ONNX 변환
────────────────────────────────────────
  🔄 Scikit-learn → ONNX 변환 중...
  ✅ ONNX 모델 유효성 검사 통과

Step 3: 모델 크기 비교
────────────────────────────────────────
  📦 원본 모델 크기:  171.38 KB
  📦 ONNX 모델 크기:  72.17 KB
  📉 크기 감소율:     57.9%

Step 4: 예측 검증
────────────────────────────────────────
  🎯 예측 일치: 30/30 (100.0%)
  ✅ 모든 예측이 일치합니다!
```

### ONNX 핵심 개념

| 개념 | 설명 |
|------|------|
| **ONNX** | Open Neural Network Exchange - ML 모델 표준 포맷 |
| **프레임워크 독립** | PyTorch, TensorFlow, Scikit-learn 등 다양한 프레임워크 지원 |
| **ONNX Runtime** | 최적화된 고성능 추론 엔진 |
| **opset** | ONNX 연산자 버전 (target_opset=12 권장) |

---

## 🔄 Part 2: Quantization (10분)

### 학습 목표
- 양자화(Quantization) 개념 이해
- FP32 → INT8 변환을 통한 모델 경량화
- 정확도 손실 없이 크기 최적화

### Step 2-1: 양자화 실행

```bash
python scripts/2_quantization.py
```

### 예상 결과

```
============================================================
  Lab 3-3 Part 2: Quantization
============================================================

Step 1: ONNX 모델 검증 및 opset 정리
────────────────────────────────────────
  🔍 ONNX 모델 검증 중...
  📋 현재 opset 정보:
     - Domain: ai.onnx.ml, Version: 1
     - Domain: ai.onnx (default), Version: 12

Step 2: 동적 양자화 적용
────────────────────────────────────────
  🔄 ONNX Runtime Quantization 적용 중...
  ✅ 양자화 완료

Step 3: 모델 크기 비교
────────────────────────────────────────
  📦 ONNX 모델 크기:     72.16 KB
  📦 양자화 모델 크기:   72.20 KB
  📉 크기 감소율:        -0.1%

Step 4: 정확도 검증
────────────────────────────────────────
  📈 ONNX 모델 정확도:    1.0000 (100.00%)
  📈 양자화 모델 정확도:  1.0000 (100.00%)
  ✅ 정확도 손실: 0.00% (허용 범위 내)
```

### 양자화 종류

| 종류 | 설명 | 장점 | 단점 |
|------|------|------|------|
| **동적 양자화** | 추론 시 가중치만 양자화 | 쉬운 적용, 재학습 불필요 | 효과 제한적 |
| **정적 양자화** | 가중치 + 활성화 양자화 | 최고 성능 | 캘리브레이션 데이터 필요 |
| **QAT** | 학습 중 양자화 시뮬레이션 | 정확도 최소 손실 | 재학습 필요 |

---

## ⚡ Part 3: Benchmark (15분)

### 학습 목표
- 원본/ONNX/양자화 모델 추론 속도 비교
- MLflow에 최적화 메트릭 기록
- 최적화 효과 분석

### Step 3-1: 벤치마크 실행

```bash
# 환경변수 설정 (Kubeflow 환경에서)
export MLFLOW_TRACKING_URI=http://mlflow-server-service.mlflow-system.svc.cluster.local:5000

# 벤치마크 실행
python scripts/3_benchmark.py
```

### 예상 결과

```
============================================================
  Lab 3-3 Part 3: Benchmark
============================================================

Step 4: 추론 속도 벤치마크
────────────────────────────────────────
  ⏱️ 각 모델 1000회 추론 수행 중...
  
  ⏱️ 추론 시간 (평균, 1000회):
     • 원본 sklearn: 8.6389 ms (1.0x)
     • ONNX:         0.1263 ms (68.4x)
     • 양자화:       0.1270 ms (68.0x)

Step 6: MLflow 기록
────────────────────────────────────────
  🔗 MLflow Tracking URI: http://mlflow-server-service.mlflow-system.svc.cluster.local:5000
  📁 새 실험 생성: lab3-3-model-optimization
  ✅ MLflow에 결과 기록 완료
     Run ID: 84fec924f3f747df85bff8bc625387e8
     실험: lab3-3-model-optimization

Step 7: 최종 결과 요약
────────────────────────────────────────

  ┌─────────────────────────────────────────────────────────────────┐
  │                      벤치마크 결과 요약                          │
  ├─────────────────────────────────────────────────────────────────┤
  │  모델          │ 크기 (KB) │ 추론 (ms) │ 속도향상 │ 정확도    │
  ├─────────────────────────────────────────────────────────────────┤
  │  원본 sklearn │    171.33 │    8.6389 │     1.0x │  100.00% │
  │  ONNX         │     72.16 │    0.1263 │    68.4x │  100.00% │
  │  양자화       │     72.20 │    0.1270 │    68.0x │  100.00% │
  └─────────────────────────────────────────────────────────────────┘

  🎯 핵심 성과:
     • 모델 크기: 171.3 KB → 72.2 KB (57.9% 감소)
     • 추론 속도: 8.64 ms → 0.13 ms (68.0x 향상)
     • 정확도 유지: 100.00% (손실 없음)
```

---

## 🏭 자동차 업계 적용 사례

### 현대오토에버 활용 예시

| 적용 분야 | 설명 | 요구사항 |
|----------|------|----------|
| **운전자 상태 모니터링** | 졸음/주의력 분산 감지 | 30fps 실시간 추론 |
| **ADAS** | 차선 이탈, 충돌 경고 | 저지연 추론 |
| **예측 유지보수** | 엔진 이상 감지 | 엣지 디바이스 배포 |

### 엣지 배포 장점

```
Cloud (학습)                    Edge (추론)
┌─────────────┐                ┌─────────────┐
│ PyTorch     │  ──ONNX변환──▶ │ ONNX Runtime│
│ 500MB 모델  │  ──양자화────▶ │ 50MB 모델   │
└─────────────┘                └─────────────┘
      │                              │
      └── 90% 크기 감소 ─────────────┘
```

---

## ✅ 실습 완료 체크리스트

### Part 1: ONNX Conversion
- [ ] `1_onnx_conversion.py` 실행 완료
- [ ] `outputs/model_original.joblib` 파일 생성 확인
- [ ] `outputs/model_optimized.onnx` 파일 생성 확인
- [ ] 모델 크기 ~58% 감소 확인
- [ ] 예측 결과 100% 일치 확인

### Part 2: Quantization
- [ ] `2_quantization.py` 실행 완료
- [ ] `outputs/model_quantized.onnx` 파일 생성 확인
- [ ] 정확도 손실 없음 확인

### Part 3: Benchmark
- [ ] `3_benchmark.py` 실행 완료
- [ ] 추론 속도 향상 확인 (60x 이상)
- [ ] MLflow에 메트릭 기록 확인
- [ ] MLflow UI에서 `lab3-3-model-optimization` 실험 확인

---

## 🔧 문제 해결 (Troubleshooting)

### 문제 1: `ModuleNotFoundError: No module named 'skl2onnx'`

**해결:**
```bash
pip install skl2onnx onnxruntime
```

### 문제 2: `ValueError: Failed to find proper ai.onnx domain`

**원인:** ONNX 모델의 opset이 중복되었거나 누락됨

**해결:** Part 1을 다시 실행하여 opset이 정리된 모델 생성
```bash
rm -rf outputs/*
python scripts/1_onnx_conversion.py
python scripts/2_quantization.py
```

### 문제 3: MLflow 연결 실패

**원인:** MLflow Tracking URI 미설정

**해결:**
```bash
# Kubeflow Jupyter 환경에서 실행
export MLFLOW_TRACKING_URI=http://mlflow-server-service.mlflow-system.svc.cluster.local:5000
python scripts/3_benchmark.py
```

### 문제 4: `outputs/` 폴더에 파일이 없음

**해결:** Part 1부터 순서대로 실행
```bash
python scripts/1_onnx_conversion.py  # 먼저
python scripts/2_quantization.py     # 다음
python scripts/3_benchmark.py        # 마지막
```

---

## 📚 참고 자료

| 자료 | URL |
|------|-----|
| ONNX 공식 문서 | https://onnx.ai/ |
| ONNX Runtime | https://onnxruntime.ai/ |
| skl2onnx 문서 | https://onnx.ai/sklearn-onnx/ |
| PyTorch ONNX Export | https://pytorch.org/docs/stable/onnx.html |
| TensorRT | https://developer.nvidia.com/tensorrt |
| OpenVINO | https://docs.openvino.ai/ |

---

## 🎯 다음 단계

Lab 3-3 완료 후:
1. **팀 프로젝트**: Lab 3-2에서 학습한 E2E Pipeline에 모델 최적화 적용
2. **KServe 배포**: 최적화된 ONNX 모델을 Triton Inference Server로 서빙
3. **실시간 모니터링**: Prometheus/Grafana로 추론 성능 모니터링

---

© 2025 현대오토에버 MLOps Training
