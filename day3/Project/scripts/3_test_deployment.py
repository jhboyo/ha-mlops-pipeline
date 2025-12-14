"""
배포 테스트 스크립트
====================

KServe InferenceService 배포 상태 확인 및 API 테스트

사용법:
    python 3_test_deployment.py --model-name california-model-user01 --namespace kubeflow-user-example-com

현대오토에버 MLOps Training
"""
import os
import argparse
import subprocess
import json
import sys


def check_inferenceservice(model_name: str, namespace: str):
    """InferenceService 상태 확인"""
    print("=" * 60)
    print("  InferenceService Status Check")
    print("=" * 60)
    
    cmd = f"kubectl get inferenceservice {model_name} -n {namespace} -o json"
    
    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  ❌ Error: {result.stderr}")
            return False
        
        isvc = json.loads(result.stdout)
        
        # 상태 확인
        status = isvc.get("status", {})
        conditions = status.get("conditions", [])
        
        print(f"  Model: {model_name}")
        print(f"  Namespace: {namespace}")
        print(f"")
        print(f"  Conditions:")
        
        ready = False
        for condition in conditions:
            ctype = condition.get("type", "Unknown")
            cstatus = condition.get("status", "Unknown")
            symbol = "✅" if cstatus == "True" else "⏳"
            print(f"    {symbol} {ctype}: {cstatus}")
            
            if ctype == "Ready" and cstatus == "True":
                ready = True
        
        # URL 정보
        url = status.get("url", "")
        address = status.get("address", {}).get("url", "")
        
        print(f"")
        print(f"  URLs:")
        if url:
            print(f"    External: {url}")
        if address:
            print(f"    Internal: {address}")
        
        print(f"")
        print(f"  Cluster Endpoint:")
        print(f"    http://{model_name}.{namespace}.svc.cluster.local/v1/models/{model_name}:predict")
        
        return ready
        
    except FileNotFoundError:
        print("  ❌ kubectl not found. Please install kubectl.")
        return False
    except json.JSONDecodeError:
        print(f"  ❌ Failed to parse response")
        return False


def test_prediction_internal(model_name: str, namespace: str):
    """클러스터 내부에서 API 테스트 (kubectl run)"""
    print("\n" + "=" * 60)
    print("  Internal API Test (kubectl run)")
    print("=" * 60)
    
    # 테스트 데이터 (정규화된 11개 피처)
    test_data = {
        "instances": [[0.5, 0.2, -0.1, -0.15, 0.3, 0.1, 0.8, -0.5, 1.2, 0.3, 0.5]]
    }
    
    endpoint = f"http://{model_name}.{namespace}.svc.cluster.local/v1/models/{model_name}:predict"
    
    cmd = [
        "kubectl", "run", "curl-test",
        "--rm", "-it", "--restart=Never",
        "--image=curlimages/curl",
        "--",
        "curl", "-s", "-X", "POST",
        endpoint,
        "-H", "Content-Type: application/json",
        "-d", json.dumps(test_data)
    ]
    
    print(f"  Endpoint: {endpoint}")
    print(f"  Test data: {test_data}")
    print(f"")
    print(f"  Command:")
    print(f"    {' '.join(cmd)}")
    print(f"")
    print(f"  Running test...")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"  ✅ Response: {result.stdout}")
        else:
            print(f"  ⚠️ Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("  ⏱️ Timeout - test took too long")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def print_port_forward_instructions(model_name: str, namespace: str):
    """Port-forward 테스트 방법 출력"""
    print("\n" + "=" * 60)
    print("  Local Test Instructions (Port Forward)")
    print("=" * 60)
    
    print(f"""
  1. 터미널 1 - Port Forward 실행:
     kubectl port-forward svc/{model_name}-predictor -n {namespace} 8080:80

  2. 터미널 2 - API 테스트:
     curl -X POST http://localhost:8080/v1/models/{model_name}:predict \\
       -H "Content-Type: application/json" \\
       -d '{{"instances": [[0.5, 0.2, -0.1, -0.15, 0.3, 0.1, 0.8, -0.5, 1.2, 0.3, 0.5]]}}'

  3. Python으로 테스트:
     import requests
     response = requests.post(
         "http://localhost:8080/v1/models/{model_name}:predict",
         json={{"instances": [[0.5, 0.2, -0.1, -0.15, 0.3, 0.1, 0.8, -0.5, 1.2, 0.3, 0.5]]}}
     )
     print(response.json())
""")


def list_inferenceservices(namespace: str):
    """네임스페이스의 모든 InferenceService 목록"""
    print("=" * 60)
    print(f"  InferenceServices in {namespace}")
    print("=" * 60)
    
    cmd = f"kubectl get inferenceservices -n {namespace}"
    
    try:
        result = subprocess.run(
            cmd.split(),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"  ⚠️ {result.stderr}")
            
    except FileNotFoundError:
        print("  ❌ kubectl not found")


def main():

    USER_NUM = os.getenv('USER_NUM', '01')
    DEFAULT_NAMESPACE = f"kubeflow-user{USER_NUM}"

    parser = argparse.ArgumentParser(
        description="KServe Deployment Test Tool"
    )
    parser.add_argument(
        "--model-name", "-m",
        default="california-model-user01",
        help="InferenceService name"
    )
    parser.add_argument(
        "--namespace", "-n",
        default=DEFAULT_NAMESPACE,
        help=f"Kubernetes namespace (default: {DEFAULT_NAMESPACE})"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all InferenceServices"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Run internal API test"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  KServe Deployment Test Tool")
    print("=" * 60)
    print(f"  Model: {args.model_name}")
    print(f"  Namespace: {args.namespace}")
    print("")
    
    if args.list:
        list_inferenceservices(args.namespace)
        return
    
    # 상태 확인
    ready = check_inferenceservice(args.model_name, args.namespace)
    
    if ready:
        print(f"\n  ✅ InferenceService is READY!")
        
        if args.test:
            test_prediction_internal(args.model_name, args.namespace)
        
        print_port_forward_instructions(args.model_name, args.namespace)
    else:
        print(f"\n  ⏳ InferenceService is not ready yet")
        print(f"     Please wait and try again")


if __name__ == "__main__":
    main()
