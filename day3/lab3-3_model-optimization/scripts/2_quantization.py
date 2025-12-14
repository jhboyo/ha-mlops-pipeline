#!/usr/bin/env python3
"""
Lab 3-3: Quantization
동적 양자화를 적용하여 모델 크기 및 추론 속도 최적화

실행: python scripts/2_quantization.py
사전 요구: python scripts/1_onnx_conversion.py 실행 완료
"""

import os
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

import onnx
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType

def main():
    print("=" * 60)
    print("Lab 3-3: Quantization (동적 양자화)")
    print("=" * 60)
    
    # =========================================================================
    # Step 1: ONNX 모델 로드
    # =========================================================================
    print("\n📂 Step 1: ONNX 모델 로드")
    print("-" * 40)
    
    onnx_path = 'outputs/model_optimized.onnx'
    
    if not os.path.exists(onnx_path):
        print(f"   ❌ 오류: {onnx_path} 파일이 없습니다.")
        print("   먼저 python scripts/1_onnx_conversion.py를 실행하세요.")
        return
    
    onnx_model = onnx.load(onnx_path)
    onnx_size = os.path.getsize(onnx_path) / 1024
    
    print(f"   ✅ ONNX 모델 로드 완료")
    print(f"   모델 크기: {onnx_size:.2f} KB")
    
    # =========================================================================
    # Step 2: 동적 양자화 적용
    # =========================================================================
    print("\n⚡ Step 2: 동적 양자화 적용")
    print("-" * 40)
    
    print("   양자화 유형: 동적 양자화 (Dynamic Quantization)")
    print("   데이터 타입: UINT8")
    print("   대상: 모델 가중치")
    
    # 양자화 적용
    quantized_path = 'outputs/model_quantized.onnx'
    
    quantize_dynamic(
        model_input=onnx_path,
        model_output=quantized_path,
        weight_type=QuantType.QUInt8  # 8비트 정수로 양자화
    )
    
    quant_size = os.path.getsize(quantized_path) / 1024
    size_change = ((quant_size - onnx_size) / onnx_size) * 100
    
    print(f"\n   ✅ 양자화 완료")
    print(f"   양자화 모델 크기: {quant_size:.2f} KB")
    print(f"   크기 변화: {size_change:+.1f}%")
    
    # 참고: RandomForest의 경우 크기 변화가 크지 않음
    # 딥러닝 모델(CNN, Transformer 등)에서 4배 이상 감소 효과
    if abs(size_change) < 10:
        print("\n   💡 참고: RandomForest 모델은 양자화 효과가 작습니다.")
        print("      딥러닝 모델에서는 4배 이상 크기 감소 가능")
    
    # =========================================================================
    # Step 3: 양자화 모델 검증
    # =========================================================================
    print("\n🔍 Step 3: 양자화 모델 검증")
    print("-" * 40)
    
    # 테스트 데이터 준비
    iris = load_iris()
    X, y = iris.data, iris.target
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # ONNX 원본 모델 추론
    sess_original = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
    input_name = sess_original.get_inputs()[0].name
    onnx_pred = sess_original.run(None, {input_name: X_test.astype(np.float32)})[0]
    
    # 양자화 모델 추론
    sess_quantized = ort.InferenceSession(quantized_path, providers=['CPUExecutionProvider'])
    quant_pred = sess_quantized.run(None, {input_name: X_test.astype(np.float32)})[0]
    
    # 정확도 계산
    onnx_accuracy = accuracy_score(y_test, onnx_pred)
    quant_accuracy = accuracy_score(y_test, quant_pred)
    match_rate = np.mean(onnx_pred == quant_pred) * 100
    
    print(f"   ONNX 원본 정확도: {onnx_accuracy:.4f}")
    print(f"   양자화 모델 정확도: {quant_accuracy:.4f}")
    print(f"   예측 일치율: {match_rate:.1f}%")
    
    accuracy_diff = (quant_accuracy - onnx_accuracy) * 100
    if accuracy_diff == 0:
        print("\n   ✅ 양자화 후 정확도 손실 없음!")
    elif accuracy_diff > -1:
        print(f"\n   ✅ 양자화 후 정확도 변화: {accuracy_diff:+.2f}% (허용 범위)")
    else:
        print(f"\n   ⚠️ 양자화 후 정확도 변화: {accuracy_diff:+.2f}%")
    
    # =========================================================================
    # 결과 요약
    # =========================================================================
    print("\n" + "=" * 60)
    print("📋 결과 요약")
    print("=" * 60)
    print(f"   {'항목':<20} {'ONNX 원본':<15} {'양자화 모델':<15}")
    print(f"   {'-' * 50}")
    print(f"   {'파일 크기':<20} {onnx_size:.2f} KB{'':<8} {quant_size:.2f} KB")
    print(f"   {'테스트 정확도':<20} {onnx_accuracy:.4f}{'':<10} {quant_accuracy:.4f}")
    print(f"   {'양자화 타입':<20} {'-':<15} {'UINT8':<15}")
    print("=" * 60)
    
    print("\n✅ 양자화 실습 완료!")
    print("   다음 단계: python scripts/3_benchmark.py")

if __name__ == "__main__":
    main()
