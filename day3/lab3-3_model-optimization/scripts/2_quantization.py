#!/usr/bin/env python3
"""
Lab 3-3 Part 2: Quantization (양자화)
ONNX 모델에 동적 양자화를 적용하여 모델 크기를 추가로 줄입니다.

실행 방법:
    python scripts/2_quantization.py

사전 요구사항:
    - Part 1 (1_onnx_conversion.py) 실행 완료
    - outputs/model_optimized.onnx 파일 존재
"""

import os
import sys
import numpy as np
from pathlib import Path

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ONNX 관련 임포트
try:
    import onnx
    import onnxruntime as ort
    from onnxruntime.quantization import quantize_dynamic, QuantType
except ImportError as e:
    print(f"❌ 필요한 패키지가 설치되지 않았습니다: {e}")
    print("   pip install onnx onnxruntime 를 실행하세요.")
    sys.exit(1)

# Scikit-learn 임포트
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


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


def clean_onnx_opset(model_path: str, output_path: str) -> bool:
    """
    ONNX 모델의 opset_import를 정리합니다.
    중복된 도메인을 제거하고 깨끗한 상태로 만듭니다.
    """
    try:
        model = onnx.load(model_path)
        
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
        
        # 저장
        onnx.save(model, output_path)
        return True
    except Exception as e:
        print(f"  ⚠️ opset 정리 실패: {e}")
        return False


def main():
    print_header("Lab 3-3 Part 2: Quantization")
    
    # 경로 설정 (outputs 폴더 사용)
    outputs_dir = PROJECT_ROOT / "outputs"
    onnx_model_path = outputs_dir / "model_optimized.onnx"
    cleaned_model_path = outputs_dir / "model_cleaned.onnx"
    quantized_model_path = outputs_dir / "model_quantized.onnx"
    
    # outputs 폴더 생성 (없는 경우)
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    # Part 1 결과물 확인
    if not onnx_model_path.exists():
        print(f"❌ ONNX 모델을 찾을 수 없습니다: {onnx_model_path}")
        print("   먼저 Part 1 (1_onnx_conversion.py)을 실행하세요.")
        sys.exit(1)
    
    # =========================================================
    # Step 1: ONNX 모델 검증 및 opset 정리
    # =========================================================
    print_step(1, "ONNX 모델 검증 및 opset 정리")
    
    print("  🔍 ONNX 모델 검증 중...")
    
    # 모델 로드 및 opset 확인
    model = onnx.load(str(onnx_model_path))
    
    print("  📋 현재 opset 정보:")
    for opset in model.opset_import:
        domain = opset.domain if opset.domain else "ai.onnx (default)"
        print(f"     - Domain: {domain}, Version: {opset.version}")
    
    # 중복 확인
    domains = [op.domain if op.domain else "" for op in model.opset_import]
    has_duplicate = len(domains) != len(set(domains))
    
    if has_duplicate:
        print("  ⚠️ 중복된 도메인 발견! 정리 중...")
        if clean_onnx_opset(str(onnx_model_path), str(cleaned_model_path)):
            model_to_quantize = str(cleaned_model_path)
            print("  ✅ opset 정리 완료")
            
            # 정리된 모델 확인
            cleaned_model = onnx.load(model_to_quantize)
            print("  📋 정리된 opset 정보:")
            for opset in cleaned_model.opset_import:
                domain = opset.domain if opset.domain else "ai.onnx (default)"
                print(f"     - Domain: {domain}, Version: {opset.version}")
        else:
            model_to_quantize = str(onnx_model_path)
    else:
        print("  ✅ opset이 이미 깨끗합니다.")
        model_to_quantize = str(onnx_model_path)
    
    # =========================================================
    # Step 2: 동적 양자화 적용
    # =========================================================
    print_step(2, "동적 양자화 적용")
    
    print("  🔄 ONNX Runtime Quantization 적용 중...")
    
    # WARNING 메시지 숨기기
    import logging
    logging.getLogger().setLevel(logging.ERROR)
    
    try:
        # 동적 양자화 적용 (QUInt8)
        quantize_dynamic(
            model_input=model_to_quantize,
            model_output=str(quantized_model_path),
            weight_type=QuantType.QUInt8,
        )
        print(f"  ✅ 양자화 완료: {quantized_model_path}")
    except Exception as e:
        print(f"  ⚠️ QUInt8 양자화 실패: {e}")
        print("  🔄 QInt8로 재시도 중...")
        
        try:
            quantize_dynamic(
                model_input=model_to_quantize,
                model_output=str(quantized_model_path),
                weight_type=QuantType.QInt8,
            )
            print(f"  ✅ 양자화 완료 (QInt8): {quantized_model_path}")
        except Exception as e2:
            print(f"  ❌ 양자화 실패: {e2}")
            print("\n  💡 onnxruntime 버전 다운그레이드를 시도하세요:")
            print("     pip install onnxruntime==1.16.3")
            sys.exit(1)
    
    # =========================================================
    # Step 3: 크기 비교
    # =========================================================
    print_step(3, "모델 크기 비교")
    
    original_size = get_file_size(onnx_model_path)
    quantized_size = get_file_size(quantized_model_path)
    reduction = (1 - quantized_size / original_size) * 100
    
    print(f"  📦 ONNX 모델 크기:     {original_size:.2f} KB")
    print(f"  📦 양자화 모델 크기:  {quantized_size:.2f} KB")
    print(f"  📉 크기 감소율:       {reduction:.1f}%")
    
    # =========================================================
    # Step 4: 정확도 검증
    # =========================================================
    print_step(4, "정확도 검증")
    
    # 테스트 데이터 준비
    print("  📊 테스트 데이터 로드 중...")
    iris = load_iris()
    X, y = iris.data, iris.target
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    X_test = X_test.astype(np.float32)
    
    # ONNX 모델 추론
    print("  🔮 ONNX 모델 추론 중...")
    onnx_session = ort.InferenceSession(str(onnx_model_path))
    input_name = onnx_session.get_inputs()[0].name
    onnx_output = onnx_session.run(None, {input_name: X_test})
    onnx_pred = onnx_output[0]
    
    # 예측 형식 처리
    if len(onnx_pred.shape) > 1 and onnx_pred.shape[1] > 1:
        onnx_pred = np.argmax(onnx_pred, axis=1)
    
    onnx_accuracy = accuracy_score(y_test, onnx_pred)
    
    # 양자화 모델 추론
    print("  🔮 양자화 모델 추론 중...")
    quant_session = ort.InferenceSession(str(quantized_model_path))
    quant_input_name = quant_session.get_inputs()[0].name
    quant_output = quant_session.run(None, {quant_input_name: X_test})
    quant_pred = quant_output[0]
    
    # 예측 형식 처리
    if len(quant_pred.shape) > 1 and quant_pred.shape[1] > 1:
        quant_pred = np.argmax(quant_pred, axis=1)
    
    quant_accuracy = accuracy_score(y_test, quant_pred)
    
    # 결과 비교
    print(f"\n  📈 ONNX 모델 정확도:    {onnx_accuracy:.4f} ({onnx_accuracy*100:.2f}%)")
    print(f"  📈 양자화 모델 정확도: {quant_accuracy:.4f} ({quant_accuracy*100:.2f}%)")
    
    accuracy_diff = abs(onnx_accuracy - quant_accuracy) * 100
    if accuracy_diff < 1.0:
        print(f"  ✅ 정확도 손실: {accuracy_diff:.2f}% (허용 범위 내)")
    else:
        print(f"  ⚠️ 정확도 손실: {accuracy_diff:.2f}% (주의 필요)")
    
    # 예측 일치율 확인
    predictions_match = np.sum(onnx_pred == quant_pred)
    total_predictions = len(onnx_pred)
    match_rate = predictions_match / total_predictions * 100
    print(f"  🎯 예측 일치율: {predictions_match}/{total_predictions} ({match_rate:.1f}%)")
    
    # =========================================================
    # Step 5: 결과 요약
    # =========================================================
    print_step(5, "결과 요약")
    
    print("""
  ┌─────────────────────────────────────────────────────────┐
  │                    양자화 결과 요약                      │
  ├─────────────────────────────────────────────────────────┤""")
    print(f"  │  • ONNX 모델:     {original_size:>8.2f} KB                       │")
    print(f"  │  • 양자화 모델:   {quantized_size:>8.2f} KB                       │")
    print(f"  │  • 크기 감소:     {reduction:>8.1f}%                         │")
    print(f"  │  • 정확도 유지:   {quant_accuracy*100:>8.2f}%                        │")
    print("""  └─────────────────────────────────────────────────────────┘
    """)
    
    # 출력 파일 확인
    print("  📁 생성된 파일:")
    print(f"     - {quantized_model_path}")
    
    # 중간 파일 정리
    if cleaned_model_path.exists():
        os.remove(cleaned_model_path)
        print(f"     (중간 파일 {cleaned_model_path.name} 삭제됨)")
    
    print("\n" + "=" * 60)
    print("  ✅ Part 2 완료! 다음 단계: python scripts/3_benchmark.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
