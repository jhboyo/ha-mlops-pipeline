#!/usr/bin/env python3
"""
Lab 2-1: Iris 분류 모델 학습
=============================

FastAPI 서빙을 위한 Iris 분류 모델을 학습합니다.
"""

import sys
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import numpy as np

def print_header():
    """헤더 출력"""
    print("=" * 60)
    print("  Lab 2-1: Iris 분류 모델 학습")
    print("=" * 60)
    print()

def print_section(title):
    """섹션 제목 출력"""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print('─' * 60)

def load_and_prepare_data():
    """데이터 로드 및 준비"""
    print_section("Step 1: 데이터 로드")
    
    print("  🔄 Iris 데이터셋 로드 중...")
    iris = load_iris()
    
    print(f"  ✅ 데이터 로드 완료")
    print(f"     - 전체 샘플 수: {len(iris.data)}")
    print(f"     - 피처 수: {len(iris.feature_names)}")
    print(f"     - 클래스 수: {len(iris.target_names)}")
    print(f"     - 클래스 이름: {', '.join(iris.target_names)}")
    
    print("\n  📊 피처 정보:")
    for i, feature in enumerate(iris.feature_names, 1):
        print(f"     {i}. {feature}")
    
    # 데이터 분할
    print("\n  🔄 Train/Test 데이터 분할 중...")
    X_train, X_test, y_train, y_test = train_test_split(
        iris.data, iris.target, 
        test_size=0.2, 
        random_state=42,
        stratify=iris.target
    )
    
    print(f"  ✅ 데이터 분할 완료")
    print(f"     - 학습 데이터: {len(X_train)} samples ({len(X_train)/len(iris.data)*100:.1f}%)")
    print(f"     - 테스트 데이터: {len(X_test)} samples ({len(X_test)/len(iris.data)*100:.1f}%)")
    
    # 클래스 분포 확인
    print("\n  📈 클래스 분포:")
    for i, class_name in enumerate(iris.target_names):
        train_count = np.sum(y_train == i)
        test_count = np.sum(y_test == i)
        print(f"     - {class_name}: Train={train_count}, Test={test_count}")
    
    return X_train, X_test, y_train, y_test, iris

def train_model(X_train, y_train):
    """모델 학습"""
    print_section("Step 2: 모델 학습")
    
    print("  🔄 RandomForest 모델 학습 중...")
    print("     - n_estimators: 100")
    print("     - random_state: 42")
    print("     - n_jobs: -1 (모든 CPU 사용)")
    
    model = RandomForestClassifier(
        n_estimators=100, 
        random_state=42,
        n_jobs=-1,
        verbose=0
    )
    
    print("\n  ⏳ 학습 진행 중", end="", flush=True)
    for i in range(5):
        print(".", end="", flush=True)
        if i < 4:
            import time
            time.sleep(0.2)
    
    model.fit(X_train, y_train)
    print(" 완료!")
    
    print(f"\n  ✅ 모델 학습 완료")
    print(f"     - 트리 개수: {model.n_estimators}")
    print(f"     - 피처 중요도 계산됨: {model.feature_importances_ is not None}")
    
    return model

def evaluate_model(model, X_train, X_test, y_train, y_test, iris):
    """모델 평가"""
    print_section("Step 3: 모델 평가")
    
    print("  🔄 모델 성능 평가 중...")
    
    # 학습 데이터 평가
    train_predictions = model.predict(X_train)
    train_accuracy = accuracy_score(y_train, train_predictions)
    
    # 테스트 데이터 평가
    test_predictions = model.predict(X_test)
    test_accuracy = accuracy_score(y_test, test_predictions)
    
    print(f"\n  📊 정확도 (Accuracy):")
    print(f"     - 학습 데이터: {train_accuracy:.4f} ({train_accuracy*100:.2f}%)")
    print(f"     - 테스트 데이터: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
    
    if train_accuracy - test_accuracy > 0.1:
        print(f"     ⚠️  과적합 가능성 (차이: {(train_accuracy-test_accuracy)*100:.2f}%)")
    else:
        print(f"     ✅ 일반화 성능 양호")
    
    # 피처 중요도
    print(f"\n  🎯 피처 중요도:")
    feature_importance = sorted(
        zip(iris.feature_names, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True
    )
    for i, (feature, importance) in enumerate(feature_importance, 1):
        bar = "█" * int(importance * 50)
        print(f"     {i}. {feature:20s} {importance:.4f} {bar}")
    
    # 혼동 행렬
    print(f"\n  📋 혼동 행렬 (Confusion Matrix):")
    cm = confusion_matrix(y_test, test_predictions)
    print("     " + "  ".join([f"{name:12s}" for name in iris.target_names]))
    for i, row in enumerate(cm):
        print(f"     {iris.target_names[i]:12s} ", end="")
        print("  ".join([f"{val:12d}" for val in row]))
    
    # 클래스별 성능
    print(f"\n  📈 클래스별 성능:")
    report = classification_report(
        y_test, test_predictions,
        target_names=iris.target_names,
        output_dict=True
    )
    for class_name in iris.target_names:
        metrics = report[class_name]
        print(f"     - {class_name:12s}: "
              f"Precision={metrics['precision']:.3f}, "
              f"Recall={metrics['recall']:.3f}, "
              f"F1-Score={metrics['f1-score']:.3f}")
    
    return test_accuracy

def save_model(model, filename="model.joblib"):
    """모델 저장"""
    print_section("Step 4: 모델 저장")
    
    print(f"  💾 모델 저장 중: {filename}")
    joblib.dump(model, filename)
    
    # 파일 크기 확인
    import os
    file_size = os.path.getsize(filename)
    if file_size < 1024:
        size_str = f"{file_size} bytes"
    elif file_size < 1024 * 1024:
        size_str = f"{file_size / 1024:.2f} KB"
    else:
        size_str = f"{file_size / (1024 * 1024):.2f} MB"
    
    print(f"  ✅ 모델 저장 완료")
    print(f"     - 파일명: {filename}")
    print(f"     - 파일 크기: {size_str}")
    print(f"     - 저장 위치: {os.path.abspath(filename)}")

def print_next_steps():
    """다음 단계 안내"""
    print("\n" + "=" * 60)
    print("  🎉 모델 학습 완료!")
    print("=" * 60)
    print("\n  📝 다음 단계:")
    print("     1. FastAPI 서버 실행:")
    print("        uvicorn app.main:app --reload --port 8000")
    print()
    print("     2. API 테스트:")
    print("        curl http://localhost:8000/health")
    print()
    print("     3. Docker 빌드:")
    print("        docker build -t user<USER_NUM>:v1 .")
    print()
    print("     4. Kubernetes 배포:")
    print("        ./scripts/build_and_deploy.sh")
    print()
    print("  💡 자세한 내용은 README.md를 참조하세요.")
    print("=" * 60)
    print()

def main():
    """메인 함수"""
    try:
        # 헤더 출력
        print_header()
        
        # Step 1: 데이터 로드
        X_train, X_test, y_train, y_test, iris = load_and_prepare_data()
        
        # Step 2: 모델 학습
        model = train_model(X_train, y_train)
        
        # Step 3: 모델 평가
        accuracy = evaluate_model(model, X_train, X_test, y_train, y_test, iris)
        
        # Step 4: 모델 저장
        save_model(model)
        
        # 다음 단계 안내
        print_next_steps()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
