"""
Lab 1-2: Hello World Pipeline
간단한 덧셈과 곱셈을 수행하는 Kubeflow Pipeline 예제

이 파이프라인은 다음을 수행합니다:
1. 두 숫자를 더함 (add)
2. 결과에 factor를 곱함 (multiply)
3. 최종 결과를 출력 (print_result)

계산식: (a + b) * factor
예시: (10 + 20) * 3 = 90
"""

from kfp import dsl
from kfp import compiler


# ============================================================
# Component 1: add (덧셈)
# ============================================================

@dsl.component(base_image='python:3.11')
def add(a: int, b: int) -> int:
    result = a + b
    print(f"Add: {a} + {b} = {result}")
    return result


# ============================================================
# Component 2: multiply (곱셈)
# ============================================================

@dsl.component(base_image='python:3.11')
def multiply(x: int, factor: int = 2) -> int:
    result = x * factor
    print(f"Multiply: {x} * {factor} = {result}")
    return result


# ============================================================
# Component 3: print_result (결과 출력)
# ============================================================

@dsl.component(base_image='python:3.11')
def print_result(value: int):
    print("=" * 50)
    print(f"Final Result: {value}")
    print("=" * 50)


# ============================================================
# Pipeline 정의
# ============================================================

@dsl.pipeline(
    name='Hello World Pipeline',
    description='Simple addition and multiplication pipeline'
)
def hello_pipeline(
    a: int = 3,
    b: int = 5,
    factor: int = 2
):
    
    # Step 1: a + b 계산
    add_task = add(a=a, b=b)
    
    # Step 2: (a + b) * factor 계산
    # add_task.output을 multiply의 x 파라미터로 전달
    multiply_task = multiply(
        x=add_task.output,
        factor=factor
    )
    
    # Step 3: 최종 결과 출력
    # multiply_task.output을 print_result의 value 파라미터로 전달
    print_result(value=multiply_task.output)


# ============================================================
# 파이프라인 컴파일
# ============================================================

if __name__ == '__main__':
    # YAML 파일로 컴파일
    output_file = 'hello_pipeline.yaml'
    
    compiler.Compiler().compile(
        pipeline_func=hello_pipeline,
        package_path=output_file
    )
    
    print("=" * 60)
    print("✅ 파이프라인 컴파일 완료!")
    print("=" * 60)
    print(f"\n생성된 파일: {output_file}")
    print(f"\n다음 단계:")
    print(f"  1. Kubeflow Dashboard 접속")
    print(f"  2. Pipelines → Upload pipeline")
    print(f"  3. {output_file} 파일 업로드")
    print(f"  4. Create run → 파라미터 설정 → Start")
    print(f"\n권장 테스트 파라미터:")
    print(f"  - a=10, b=20, factor=3 → 예상 결과: 90")
    print(f"  - a=7, b=3, factor=5 → 예상 결과: 50")
    print("=" * 60)
