#!/usr/bin/env python3
"""
Lab 3-3 Part 1: ONNX Conversion
Scikit-learn 모델을 ONNX 포맷으로 변환합니다.

실행 방법:
    python scripts/1_onnx_conversion.py

출력 파일:
    - outputs/model_original.joblib
    - outputs/model_optimized.onnx
"""

import os
import sys
import numpy as np
from pathlib import Path

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 필요한 패키지 임포트
try:
    import joblib
    import onnx
    from onnx import helper
    import onnxruntime as ort
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType
    from sklearn.datasets import load_iris
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
except ImportError as e:
    print(f"❌ 필요한 패키지가 설치되지 않았습니다: {e}")
    print("   pip install -r requirements.txt 를 실행하세요.")
    sys.exit(1)


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


def clean_onnx_opset(model):
    """
    ONNX 모델의 opset_import를 정리합니다.
    중복된 도메인을 제거하고 깨끗한 상태로 만듭니다.
    """
    # 기존 opset 정보 수집 (중복 제거)
    opset_dict = {}
    for opset in model.opset_import:
        domain = opset.domain if opset.domain else ""
        # 같은 도메인이 이미 있으면 더 높은 버전 유지
        if domain not in opset_dict or opset.version > opset_dict[domain]:
            opset_dict[domain] = opset.version
    
    # 기존 opset_import 모두 제거
    while len(model.opset_import) > 0:
        model.opset_import.pop()
    
    # 정리된 opset 다시 추가
    for domain, version in opset_dict.items():
        opset = model.opset_import.add()
        opset.domain = domain
        opset.version = version
    
    return model


def main():
    print_header("Lab 3-3 Part 1: ONNX Conversion")
    
    # 출력 디렉토리 설정
    outputs_dir = PROJECT_ROOT / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    original_model_path = outputs_dir / "model_original.joblib"
    onnx_model_path = outputs_dir / "model_optimized.onnx"
    
    # =========================================================
    # Step 1: 데이터 로드 및 모델 학습
    # =========================================================
    print_step(1, "데이터 로드 및 모델 학습")
    
    # Iris 데이터셋 로드
    print("  📊 Iris 데이터셋 로드 중...")
    iris = load_iris()
    X, y = iris.data, iris.target
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"  📊 학습 데이터: {X_train.shape[0]}개")
    print(f"  📊 테스트 데이터: {X_test.shape[0]}개")
    print(f"  📊 피처 수: {X_train.shape[1]}")
    
    # RandomForest 모델 학습
    print("  🏋️ RandomForest 모델 학습 중...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # 정확도 확인
    train_accuracy = accuracy_score(y_train, model.predict(X_train))
    test_accuracy = accuracy_score(y_test, model.predict(X_test))
    print(f"  📈 학습 정확도: {train_accuracy:.4f}")
    print(f"  📈 테스트 정확도: {test_accuracy:.4f}")
    
    # 원본 모델 저장
    joblib.dump(model, original_model_path)
    print(f"  💾 원본 모델 저장: {original_model_path}")
    
    # =========================================================
    # Step 2: ONNX 변환
    # =========================================================
    print_step(2, "ONNX 변환")
    
    print("  🔄 Scikit-learn → ONNX 변환 중...")
    
    # 입력 타입 정의 (피처 수 = 4)
    initial_type = [('float_input', FloatTensorType([None, X_train.shape[1]]))]
    
    # ONNX 변환
    onnx_model = convert_sklearn(
        model, 
        initial_types=initial_type,
        target_opset=12,
        options={id(model): {'zipmap': False}}
    )
    
    # ⭐ 핵심: opset 중복 제거 및 정리
    print("  🧹 opset 정리 중...")
    onnx_model = clean_onnx_opset(onnx_model)
    
    # 모델 유효성 검사
    onnx.checker.check_model(onnx_model)
    print("  ✅ ONNX 모델 유효성 검사 통과")
    
    # ONNX 모델 저장
    onnx.save(onnx_model, str(onnx_model_path))
    print(f"  💾 ONNX 모델 저장: {onnx_model_path}")
    
    # =========================================================
    # Step 3: 크기 비교
    # =========================================================
    print_step(3, "모델 크기 비교")
    
    original_size = get_file_size(original_model_path)
    onnx_size = get_file_size(onnx_model_path)
    reduction = (1 - onnx_size / original_size) * 100
    
    print(f"  📦 원본 모델 크기:  {original_size:.2f} KB")
    print(f"  📦 ONNX 모델 크기: {onnx_size:.2f} KB")
    print(f"  📉 크기 감소율:    {reduction:.1f}%")
    
    # =========================================================
    # Step 4: 예측 검증
    # =========================================================
    print_step(4, "예측 검증")
    
    print("  🔮 원본 모델 vs ONNX 모델 예측 비교...")
    
    # 원본 모델 예측
    original_pred = model.predict(X_test)
    
    # ONNX 모델 예측
    X_test_float32 = X_test.astype(np.float32)
    onnx_session = ort.InferenceSession(str(onnx_model_path))
    input_name = onnx_session.get_inputs()[0].name
    onnx_output = onnx_session.run(None, {input_name: X_test_float32})
    onnx_pred = onnx_output[0]
    
    # 예측 결과가 레이블이 아닌 경우 처리
    if len(onnx_pred.shape) > 1 and onnx_pred.shape[1] > 1:
        onnx_pred = np.argmax(onnx_pred, axis=1)
    
    # 비교
    predictions_match = np.sum(original_pred == onnx_pred)
    total_predictions = len(original_pred)
    match_rate = predictions_match / total_predictions * 100
    
    print(f"  🎯 예측 일치: {predictions_match}/{total_predictions} ({match_rate:.1f}%)")
    
    if match_rate == 100:
        print("  ✅ 모든 예측이 일치합니다!")
    else:
        print(f"  ⚠️ {total_predictions - predictions_match}개의 예측이 다릅니다.")
    
    # ONNX 모델 정확도
    onnx_accuracy = accuracy_score(y_test, onnx_pred)
    print(f"  📈 ONNX 모델 정확도: {onnx_accuracy:.4f}")
    
    # =========================================================
    # Step 5: 결과 요약
    # =========================================================
    print_step(5, "결과 요약")
    
    print("""
  ┌─────────────────────────────────────────────────────────┐
  │                    ONNX 변환 결과 요약                   │
  ├─────────────────────────────────────────────────────────┤""")
    print(f"  │  • 원본 모델:      {original_size:>8.2f} KB                       │")
    print(f"  │  • ONNX 모델:      {onnx_size:>8.2f} KB                       │")
    print(f"  │  • 크기 감소:      {reduction:>8.1f}%                         │")
    print(f"  │  • 예측 일치율:    {match_rate:>8.1f}%                         │")
    print("""  └─────────────────────────────────────────────────────────┘
    """)
    
    print("  📁 생성된 파일:")
    print(f"     - {original_model_path}")
    print(f"     - {onnx_model_path}")
    
    # opset 정보 출력
    print("\n  📋 ONNX 모델 정보 (정리됨):")
    for opset in onnx_model.opset_import:
        domain = opset.domain if opset.domain else "ai.onnx"
        print(f"     - Domain: {domain}, Version: {opset.version}")
    
    print("\n" + "=" * 60)
    print("  ✅ Part 1 완료! 다음 단계: python scripts/2_quantization.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
