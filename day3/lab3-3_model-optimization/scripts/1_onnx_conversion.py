#!/usr/bin/env python3
"""
Lab 3-3: ONNX Conversion
ONNX 포맷으로 모델 변환하여 프레임워크 독립성 확보

실행: python scripts/1_onnx_conversion.py
"""

import os
import pickle
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# ONNX 관련 라이브러리
import onnx
import onnxruntime as ort
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

def main():
    print("=" * 60)
    print("Lab 3-3: ONNX Conversion")
    print("=" * 60)
    
    # 출력 디렉토리 생성
    os.makedirs('outputs', exist_ok=True)
    
    # =========================================================================
    # Step 1: 데이터 로드 및 모델 학습
    # =========================================================================
    print("\n📊 Step 1: 데이터 로드 및 모델 학습")
    print("-" * 40)
    
    # Iris 데이터셋 로드
    iris = load_iris()
    X, y = iris.data, iris.target
    
    # 학습/테스트 분할
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"   학습 데이터: {X_train.shape[0]}개")
    print(f"   테스트 데이터: {X_test.shape[0]}개")
    print(f"   특성 수: {X_train.shape[1]}개")
    print(f"   클래스 수: {len(np.unique(y))}개")
    
    # RandomForest 모델 학습
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # 정확도 평가
    train_accuracy = accuracy_score(y_train, model.predict(X_train))
    test_accuracy = accuracy_score(y_test, model.predict(X_test))
    
    print(f"\n   ✅ 모델 학습 완료")
    print(f"   학습 정확도: {train_accuracy:.4f}")
    print(f"   테스트 정확도: {test_accuracy:.4f}")
    
    # 원본 모델 저장
    original_path = 'outputs/model_original.pkl'
    with open(original_path, 'wb') as f:
        pickle.dump(model, f)
    
    original_size = os.path.getsize(original_path) / 1024
    print(f"   원본 모델 크기: {original_size:.2f} KB")
    
    # =========================================================================
    # Step 2: ONNX 변환
    # =========================================================================
    print("\n🔄 Step 2: ONNX 변환")
    print("-" * 40)
    
    # 입력 타입 정의
    initial_type = [('float_input', FloatTensorType([None, X_train.shape[1]]))]
    
    # sklearn 모델을 ONNX로 변환
    onnx_model = convert_sklearn(
        model, 
        initial_types=initial_type,
        target_opset=12  # ONNX opset 버전
    )
    
    # ONNX 모델 저장
    onnx_path = 'outputs/model_optimized.onnx'
    onnx.save_model(onnx_model, onnx_path)
    
    onnx_size = os.path.getsize(onnx_path) / 1024
    size_reduction = (1 - onnx_size / original_size) * 100
    
    print(f"   ✅ ONNX 변환 완료")
    print(f"   ONNX 모델 크기: {onnx_size:.2f} KB")
    print(f"   크기 감소: {size_reduction:.1f}%")
    
    # =========================================================================
    # Step 3: ONNX 모델 검증
    # =========================================================================
    print("\n🔍 Step 3: ONNX 모델 검증")
    print("-" * 40)
    
    # ONNX 모델 유효성 검사
    onnx.checker.check_model(onnx_model)
    print("   ✅ ONNX 모델 유효성 검사 통과")
    
    # ONNX Runtime으로 추론 테스트
    sess = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
    
    # 입력/출력 정보
    input_name = sess.get_inputs()[0].name
    output_names = [o.name for o in sess.get_outputs()]
    
    print(f"   입력 이름: {input_name}")
    print(f"   출력 이름: {output_names}")
    
    # ONNX 추론
    onnx_pred = sess.run(None, {input_name: X_test.astype(np.float32)})[0]
    
    # 원본 모델 추론
    sklearn_pred = model.predict(X_test)
    
    # 예측 결과 비교
    match_rate = np.mean(onnx_pred == sklearn_pred) * 100
    onnx_accuracy = accuracy_score(y_test, onnx_pred)
    
    print(f"\n   ✅ 추론 검증 완료")
    print(f"   ONNX 모델 정확도: {onnx_accuracy:.4f}")
    print(f"   원본과 예측 일치율: {match_rate:.1f}%")
    
    # =========================================================================
    # 결과 요약
    # =========================================================================
    print("\n" + "=" * 60)
    print("📋 결과 요약")
    print("=" * 60)
    print(f"   {'항목':<20} {'원본 모델':<15} {'ONNX 모델':<15}")
    print(f"   {'-' * 50}")
    print(f"   {'파일 크기':<20} {original_size:.2f} KB{'':<8} {onnx_size:.2f} KB")
    print(f"   {'테스트 정확도':<20} {test_accuracy:.4f}{'':<10} {onnx_accuracy:.4f}")
    print(f"   {'크기 감소율':<20} {'-':<15} {size_reduction:.1f}%")
    print("=" * 60)
    
    print("\n✅ ONNX 변환 실습 완료!")
    print("   다음 단계: python scripts/2_quantization.py")

if __name__ == "__main__":
    main()
