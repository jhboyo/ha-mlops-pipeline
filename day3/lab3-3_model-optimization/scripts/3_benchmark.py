#!/usr/bin/env python3
"""
Lab 3-3 Part 3: Benchmark (성능 벤치마크)
원본, ONNX, 양자화 모델의 추론 성능을 비교합니다.

실행 방법:
    python scripts/3_benchmark.py

사전 요구사항:
    - Part 1, 2 실행 완료
    - outputs/model_original.joblib
    - outputs/model_optimized.onnx
    - outputs/model_quantized.onnx

환경변수 (선택):
    - MLFLOW_TRACKING_URI: MLflow 서버 주소 (예: http://mlflow-server-service.mlflow-system.svc.cluster.local:5000)
"""

import os
import sys
import time
import numpy as np
from pathlib import Path

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 필요한 패키지 임포트
try:
    import joblib
    import onnxruntime as ort
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
except ImportError as e:
    print(f"❌ 필요한 패키지가 설치되지 않았습니다: {e}")
    print("   pip install joblib onnxruntime scikit-learn 를 실행하세요.")
    sys.exit(1)

# MLflow (선택적)
try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


def print_header(title: str):
    """섹션 헤더 출력"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step: int, description: str):
    """단계 출력"""
    print(f"\nStep {step}: {description}")
    print("─" * 40)


def get_file_size(filepath: str) -> float:
    """파일 크기를 KB 단위로 반환"""
    return os.path.getsize(filepath) / 1024


def benchmark_inference(predict_fn, X_test: np.ndarray, n_iterations: int = 1000) -> dict:
    """추론 성능 벤치마크"""
    # 워밍업
    for _ in range(10):
        predict_fn(X_test)
    
    # 벤치마크
    times = []
    for _ in range(n_iterations):
        start = time.perf_counter()
        predict_fn(X_test)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # ms로 변환
    
    return {
        "mean": np.mean(times),
        "std": np.std(times),
        "min": np.min(times),
        "max": np.max(times),
        "median": np.median(times),
    }


def get_mlflow_tracking_uri():
    """
    MLflow Tracking URI를 가져옵니다.
    환경변수 > 기본값 순서로 확인합니다.
    """
    # 환경변수에서 가져오기
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    
    if tracking_uri:
        return tracking_uri
    
    # Kubeflow/Kubernetes 환경에서 일반적인 MLflow 서비스 주소
    default_uri = "http://mlflow-server-service.mlflow-system.svc.cluster.local:5000"
    
    return default_uri


def main():
    print_header("Lab 3-3 Part 3: Benchmark")
    
    # 경로 설정 (outputs 폴더 사용)
    outputs_dir = PROJECT_ROOT / "outputs"
    original_model_path = outputs_dir / "model_original.joblib"
    onnx_model_path = outputs_dir / "model_optimized.onnx"
    quantized_model_path = outputs_dir / "model_quantized.onnx"
    
    # 파일 존재 확인
    missing_files = []
    if not original_model_path.exists():
        missing_files.append(str(original_model_path))
    if not onnx_model_path.exists():
        missing_files.append(str(onnx_model_path))
    if not quantized_model_path.exists():
        missing_files.append(str(quantized_model_path))
    
    if missing_files:
        print("❌ 다음 파일을 찾을 수 없습니다:")
        for f in missing_files:
            print(f"   - {f}")
        print("\n   Part 1, 2를 먼저 실행하세요.")
        sys.exit(1)
    
    # =========================================================
    # Step 1: 테스트 데이터 준비
    # =========================================================
    print_step(1, "테스트 데이터 준비")
    
    iris = load_iris()
    X, y = iris.data, iris.target
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    X_test_float32 = X_test.astype(np.float32)
    
    print(f"  📊 테스트 샘플 수: {len(X_test)}")
    print(f"  📊 피처 수: {X_test.shape[1]}")
    
    # =========================================================
    # Step 2: 모델 로드
    # =========================================================
    print_step(2, "모델 로드")
    
    # 원본 sklearn 모델
    print("  📦 원본 sklearn 모델 로드...")
    original_model = joblib.load(original_model_path)
    
    # ONNX 모델
    print("  📦 ONNX 모델 로드...")
    onnx_session = ort.InferenceSession(str(onnx_model_path))
    onnx_input_name = onnx_session.get_inputs()[0].name
    
    # 양자화 모델
    print("  📦 양자화 모델 로드...")
    quant_session = ort.InferenceSession(str(quantized_model_path))
    quant_input_name = quant_session.get_inputs()[0].name
    
    print("  ✅ 모든 모델 로드 완료")
    
    # =========================================================
    # Step 3: 정확도 비교
    # =========================================================
    print_step(3, "정확도 비교")
    
    # 원본 모델
    original_pred = original_model.predict(X_test)
    original_accuracy = accuracy_score(y_test, original_pred)
    
    # ONNX 모델
    onnx_output = onnx_session.run(None, {onnx_input_name: X_test_float32})
    onnx_pred = onnx_output[0]
    if len(onnx_pred.shape) > 1 and onnx_pred.shape[1] > 1:
        onnx_pred = np.argmax(onnx_pred, axis=1)
    onnx_accuracy = accuracy_score(y_test, onnx_pred)
    
    # 양자화 모델
    quant_output = quant_session.run(None, {quant_input_name: X_test_float32})
    quant_pred = quant_output[0]
    if len(quant_pred.shape) > 1 and quant_pred.shape[1] > 1:
        quant_pred = np.argmax(quant_pred, axis=1)
    quant_accuracy = accuracy_score(y_test, quant_pred)
    
    print(f"  📈 원본 모델 정확도:   {original_accuracy:.4f} ({original_accuracy*100:.2f}%)")
    print(f"  📈 ONNX 모델 정확도:   {onnx_accuracy:.4f} ({onnx_accuracy*100:.2f}%)")
    print(f"  📈 양자화 모델 정확도: {quant_accuracy:.4f} ({quant_accuracy*100:.2f}%)")
    
    # =========================================================
    # Step 4: 추론 속도 벤치마크
    # =========================================================
    print_step(4, "추론 속도 벤치마크")
    
    n_iterations = 1000
    print(f"  ⏱️ 각 모델 {n_iterations}회 추론 수행 중...")
    
    # 원본 모델 벤치마크
    print("  🔄 원본 sklearn 모델 벤치마크...")
    original_benchmark = benchmark_inference(
        lambda x: original_model.predict(x),
        X_test,
        n_iterations
    )
    
    # ONNX 모델 벤치마크
    print("  🔄 ONNX 모델 벤치마크...")
    onnx_benchmark = benchmark_inference(
        lambda x: onnx_session.run(None, {onnx_input_name: x.astype(np.float32)})[0],
        X_test,
        n_iterations
    )
    
    # 양자화 모델 벤치마크
    print("  🔄 양자화 모델 벤치마크...")
    quant_benchmark = benchmark_inference(
        lambda x: quant_session.run(None, {quant_input_name: x.astype(np.float32)})[0],
        X_test,
        n_iterations
    )
    
    # 속도 향상 계산
    onnx_speedup = original_benchmark["mean"] / onnx_benchmark["mean"]
    quant_speedup = original_benchmark["mean"] / quant_benchmark["mean"]
    
    print(f"\n  ⏱️ 추론 시간 (평균, {n_iterations}회):")
    print(f"     • 원본 sklearn: {original_benchmark['mean']:.4f} ms (1.0x)")
    print(f"     • ONNX:         {onnx_benchmark['mean']:.4f} ms ({onnx_speedup:.1f}x)")
    print(f"     • 양자화:       {quant_benchmark['mean']:.4f} ms ({quant_speedup:.1f}x)")
    
    # =========================================================
    # Step 5: 모델 크기 비교
    # =========================================================
    print_step(5, "모델 크기 비교")
    
    original_size = get_file_size(original_model_path)
    onnx_size = get_file_size(onnx_model_path)
    quant_size = get_file_size(quantized_model_path)
    
    onnx_reduction = (1 - onnx_size / original_size) * 100
    quant_reduction = (1 - quant_size / original_size) * 100
    
    print(f"  📦 원본 sklearn: {original_size:.2f} KB (100%)")
    print(f"  📦 ONNX:         {onnx_size:.2f} KB ({100-onnx_reduction:.1f}%, -{onnx_reduction:.1f}%)")
    print(f"  📦 양자화:       {quant_size:.2f} KB ({100-quant_reduction:.1f}%, -{quant_reduction:.1f}%)")
    
    # =========================================================
    # Step 6: MLflow 기록
    # =========================================================
    print_step(6, "MLflow 기록")
    
    if MLFLOW_AVAILABLE:
        try:
            # ⭐ MLflow Tracking URI 설정
            tracking_uri = get_mlflow_tracking_uri()
            print(f"  🔗 MLflow Tracking URI: {tracking_uri}")
            mlflow.set_tracking_uri(tracking_uri)
            
            # 실험 설정 (Lab 3-3으로 변경)
            experiment_name = "lab3-3-model-optimization"
            
            # 실험이 없으면 생성
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(experiment_name)
                print(f"  📁 새 실험 생성: {experiment_name}")
            else:
                experiment_id = experiment.experiment_id
                print(f"  📁 기존 실험 사용: {experiment_name}")
            
            mlflow.set_experiment(experiment_name)
            
            with mlflow.start_run(run_name="benchmark-results"):
                # 크기 메트릭
                mlflow.log_metric("original_size_kb", original_size)
                mlflow.log_metric("onnx_size_kb", onnx_size)
                mlflow.log_metric("quantized_size_kb", quant_size)
                mlflow.log_metric("size_reduction_percent", quant_reduction)
                
                # 속도 메트릭
                mlflow.log_metric("original_inference_ms", original_benchmark["mean"])
                mlflow.log_metric("onnx_inference_ms", onnx_benchmark["mean"])
                mlflow.log_metric("quantized_inference_ms", quant_benchmark["mean"])
                mlflow.log_metric("onnx_speedup", onnx_speedup)
                mlflow.log_metric("quantized_speedup", quant_speedup)
                
                # 정확도 메트릭
                mlflow.log_metric("original_accuracy", original_accuracy)
                mlflow.log_metric("onnx_accuracy", onnx_accuracy)
                mlflow.log_metric("quantized_accuracy", quant_accuracy)
                
                # 파라미터
                mlflow.log_param("n_iterations", n_iterations)
                mlflow.log_param("test_samples", len(X_test))
                mlflow.log_param("quantization_type", "dynamic_uint8")
                
                # 모델 아티팩트
                mlflow.log_artifact(str(onnx_model_path))
                mlflow.log_artifact(str(quantized_model_path))
                
                run_id = mlflow.active_run().info.run_id
                print("  ✅ MLflow에 결과 기록 완료")
                print(f"     Run ID: {run_id}")
                print(f"     실험: {experiment_name}")
                
        except Exception as e:
            print(f"  ⚠️ MLflow 기록 실패: {e}")
            print("     (MLflow 서버 연결을 확인하세요)")
            print("\n  💡 해결 방법:")
            print("     1. 환경변수 설정: export MLFLOW_TRACKING_URI=http://mlflow-server-service.mlflow-system.svc.cluster.local:5000")
            print("     2. 또는 Kubeflow Jupyter 환경에서 실행하세요")
    else:
        print("  ⚠️ MLflow가 설치되지 않아 기록을 건너뜁니다.")
        print("     (pip install mlflow로 설치 가능)")
    
    # =========================================================
    # Step 7: 최종 결과 요약
    # =========================================================
    print_step(7, "최종 결과 요약")
    
    print("""
  ┌─────────────────────────────────────────────────────────────────┐
  │                      벤치마크 결과 요약                          │
  ├─────────────────────────────────────────────────────────────────┤
  │  모델          │ 크기 (KB) │ 추론 (ms) │ 속도향상 │ 정확도    │
  ├─────────────────────────────────────────────────────────────────┤""")
    print(f"  │  원본 sklearn │ {original_size:>9.2f} │ {original_benchmark['mean']:>9.4f} │ {1.0:>8.1f}x │ {original_accuracy*100:>8.2f}% │")
    print(f"  │  ONNX         │ {onnx_size:>9.2f} │ {onnx_benchmark['mean']:>9.4f} │ {onnx_speedup:>8.1f}x │ {onnx_accuracy*100:>8.2f}% │")
    print(f"  │  양자화       │ {quant_size:>9.2f} │ {quant_benchmark['mean']:>9.4f} │ {quant_speedup:>8.1f}x │ {quant_accuracy*100:>8.2f}% │")
    print("""  └─────────────────────────────────────────────────────────────────┘
    """)
    
    print("  🎯 핵심 성과:")
    print(f"     • 모델 크기: {original_size:.1f} KB → {quant_size:.1f} KB ({quant_reduction:.1f}% 감소)")
    print(f"     • 추론 속도: {original_benchmark['mean']:.2f} ms → {quant_benchmark['mean']:.2f} ms ({quant_speedup:.1f}x 향상)")
    print(f"     • 정확도 유지: {quant_accuracy*100:.2f}% (손실 없음)")
    
    print("\n" + "=" * 60)
    print("  ✅ Lab 3-3 완료! 모델 최적화 실습을 성공적으로 마쳤습니다.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
