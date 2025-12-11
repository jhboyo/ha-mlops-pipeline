# 🍎 macOS 환경 설정 가이드

> **MLOps 파이프라인 구현 [고급]** - 수강 전 사전 설정

## ⚠️ 중요 안내

**이 문서는 교육 시작 전에 반드시 완료해야 합니다.**  
교육 당일에는 환경 설정을 위한 별도의 시간이 제공되지 않습니다.

---

## 📋 목차

1. [시스템 요구사항](#1-시스템-요구사항)
2. [Homebrew 설치](#2-homebrew-설치)
3. [필수 도구 설치](#3-필수-도구-설치)
4. [Docker Desktop 설치](#4-docker-desktop-설치)
5. [Python 환경 설정](#5-python-환경-설정)
6. [VS Code 설치 (권장)](#6-vs-code-설치-권장)
7. [설치 확인](#7-설치-확인)
8. [트러블슈팅](#8-트러블슈팅)

---

## 1. 시스템 요구사항

| 항목 | 최소 사양 | 권장 사양 |
|------|----------|----------|
| **macOS 버전** | macOS 11 (Big Sur) | macOS 13 (Ventura) 이상 |
| **칩셋** | Intel 또는 Apple Silicon (M1/M2/M3) | Apple Silicon (M1/M2/M3) |
| **메모리** | 8GB | 16GB 이상 |
| **디스크 공간** | 20GB 여유 | 50GB 이상 여유 |
| **네트워크** | 인터넷 연결 필수 | 안정적인 인터넷 |

### 시스템 정보 확인

```bash
# macOS 버전 확인
sw_vers

# 칩셋 확인 (Apple Silicon vs Intel)
uname -m
# arm64 → Apple Silicon (M1/M2/M3)
# x86_64 → Intel

# 메모리 확인
sysctl -n hw.memsize | awk '{print $0/1024/1024/1024 " GB"}'

# 디스크 여유 공간 확인
df -h /
```

---

## 2. Homebrew 설치

Homebrew는 macOS의 패키지 관리자로, 대부분의 도구 설치에 사용됩니다.

### Step 2-1: Homebrew 설치

```bash
# Homebrew 설치
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2-2: PATH 설정 (Apple Silicon만 해당)

Apple Silicon (M1/M2/M3) Mac을 사용하는 경우:

```bash
# ~/.zprofile에 PATH 추가
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

### Step 2-3: 설치 확인

```bash
brew --version
```

**예상 출력:**
```
Homebrew 4.x.x
```

---

## 3. 필수 도구 설치

### Step 3-1: 한 번에 설치

```bash
# 모든 필수 도구 설치
brew install awscli kubectl git
```

### Step 3-2: 개별 설치 및 확인

#### AWS CLI

```bash
# 설치
brew install awscli

# 확인
aws --version
```

**예상 출력:**
```
aws-cli/2.x.x Python/3.x.x Darwin/23.x.x source/arm64
```

#### kubectl

```bash
# 설치
brew install kubectl

# 확인
kubectl version --client
```

**예상 출력:**
```
Client Version: v1.28.x
Kustomize Version: v5.x.x
```

#### Git

```bash
# 설치 (대부분 이미 설치되어 있음)
brew install git

# 확인
git --version
```

**예상 출력:**
```
git version 2.x.x
```

---

## 4. Docker Desktop 설치

### Step 4-1: Docker Desktop 다운로드

1. [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) 접속
2. **본인의 칩셋에 맞는 버전 다운로드**:
   - **Apple Silicon (M1/M2/M3)**: "Mac with Apple chip" 선택
   - **Intel**: "Mac with Intel chip" 선택

### Step 4-2: 설치 및 실행

1. 다운로드된 `.dmg` 파일 실행
2. Docker 아이콘을 Applications 폴더로 드래그
3. Applications에서 Docker 실행
4. 메뉴 바에 Docker 아이콘(고래)이 나타날 때까지 대기

### Step 4-3: Docker 설정 최적화

Docker Desktop 실행 후:

1. 메뉴 바의 Docker 아이콘 클릭 → **Settings (⚙️)**
2. **Resources** 탭:
   - **Memory**: 4GB 이상 권장
   - **CPU**: 2 이상 권장
   - **Disk**: 20GB 이상 권장
3. **Apply & Restart** 클릭

### Step 4-4: 설치 확인

```bash
# Docker 버전 확인
docker --version

# Docker 실행 확인
docker info

# 테스트 컨테이너 실행
docker run hello-world
```

**예상 출력:**
```
Docker version 24.x.x, build xxxxxxx
```

---

## 5. Python 환경 설정

### Step 5-1: Python 설치

macOS에는 기본 Python이 있지만, 최신 버전 설치를 권장합니다.

```bash
# Python 3.11 설치 (권장)
brew install python@3.11

# 또는 Python 3.9 설치
brew install python@3.9

# 버전 확인
python3 --version
```

**예상 출력:**
```
Python 3.11.x
```

### Step 5-2: pip 업그레이드

```bash
python3 -m pip install --upgrade pip
pip3 --version
```

### Step 5-3: 가상환경 생성 (권장)

```bash
# 프로젝트 디렉토리 생성
mkdir -p ~/mlops-training
cd ~/mlops-training

# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate

# 프롬프트 변경 확인: (.venv) $
```

### Step 5-4: 필수 Python 패키지 설치

```bash
# 가상환경 활성화 상태에서
pip install --upgrade pip

# 필수 패키지 설치
pip install \
    kfp==1.8.22 \
    mlflow==2.9.2 \
    scikit-learn>=1.3.0 \
    pandas>=2.0.0 \
    numpy>=1.24.0 \
    onnx>=1.14.0 \
    onnxruntime>=1.16.0 \
    skl2onnx>=1.16.0 \
    joblib>=1.3.0 \
    requests \
    boto3
```

### Step 5-5: 패키지 설치 확인

```bash
python -c "import kfp; print(f'KFP: {kfp.__version__}')"
python -c "import mlflow; print(f'MLflow: {mlflow.__version__}')"
python -c "import sklearn; print(f'Scikit-learn: {sklearn.__version__}')"
python -c "import onnxruntime; print(f'ONNX Runtime: {onnxruntime.__version__}')"
```

---

## 6. VS Code 설치 (권장)

### Step 6-1: VS Code 설치

```bash
brew install --cask visual-studio-code
```

또는 [VS Code 공식 사이트](https://code.visualstudio.com/)에서 다운로드

### Step 6-2: 필수 확장 프로그램

VS Code 실행 후 Extensions (⌘+Shift+X)에서 설치:

| 확장 프로그램 | 용도 |
|--------------|------|
| **Python** | Python 개발 |
| **Jupyter** | Notebook 지원 |
| **Docker** | Docker 관리 |
| **YAML** | YAML 파일 편집 |
| **Kubernetes** | K8s 리소스 관리 |

### Step 6-3: 터미널에서 VS Code 열기

```bash
# code 명령어 설치
# VS Code 실행 → Command Palette (⌘+Shift+P) → "Shell Command: Install 'code' command"

# 사용 예시
code ~/mlops-training
```

---

## 7. 설치 확인

### 전체 확인 스크립트

다음 스크립트를 실행하여 모든 설치를 확인합니다:

```bash
#!/bin/bash

echo "========================================"
echo "  MLOps 환경 설정 확인 (macOS)"
echo "========================================"
echo ""

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

check_command() {
    if command -v $1 &> /dev/null; then
        VERSION=$($2 2>&1 | head -1)
        echo -e "${GREEN}✅ $1${NC}: $VERSION"
        return 0
    else
        echo -e "${RED}❌ $1${NC}: 설치되지 않음"
        return 1
    fi
}

# 각 도구 확인
echo "📦 필수 도구 확인"
echo "----------------------------------------"
check_command "brew" "brew --version"
check_command "aws" "aws --version"
check_command "kubectl" "kubectl version --client --short"
check_command "docker" "docker --version"
check_command "python3" "python3 --version"
check_command "git" "git --version"

echo ""
echo "🐳 Docker 상태 확인"
echo "----------------------------------------"
if docker info &> /dev/null; then
    echo -e "${GREEN}✅ Docker Desktop 실행 중${NC}"
else
    echo -e "${RED}❌ Docker Desktop이 실행되지 않음${NC}"
    echo "   Docker Desktop을 실행해주세요"
fi

echo ""
echo "🐍 Python 패키지 확인"
echo "----------------------------------------"
python3 -c "import kfp; print(f'✅ kfp: {kfp.__version__}')" 2>/dev/null || echo "❌ kfp: 설치되지 않음"
python3 -c "import mlflow; print(f'✅ mlflow: {mlflow.__version__}')" 2>/dev/null || echo "❌ mlflow: 설치되지 않음"
python3 -c "import sklearn; print(f'✅ scikit-learn: {sklearn.__version__}')" 2>/dev/null || echo "❌ scikit-learn: 설치되지 않음"
python3 -c "import onnxruntime; print(f'✅ onnxruntime: {onnxruntime.__version__}')" 2>/dev/null || echo "❌ onnxruntime: 설치되지 않음"

echo ""
echo "========================================"
echo "  확인 완료"
echo "========================================"
```

### 스크립트 실행 방법

```bash
# 스크립트 저장
cat > check_env.sh << 'EOF'
[위 스크립트 내용]
EOF

# 실행 권한 부여 및 실행
chmod +x check_env.sh
./check_env.sh
```

### 예상 결과

```
========================================
  MLOps 환경 설정 확인 (macOS)
========================================

📦 필수 도구 확인
----------------------------------------
✅ brew: Homebrew 4.2.0
✅ aws: aws-cli/2.15.0 Python/3.11.6 Darwin/23.2.0 source/arm64
✅ kubectl: Client Version: v1.28.4
✅ docker: Docker version 24.0.7, build afdd53b
✅ python3: Python 3.11.6
✅ git: git version 2.43.0

🐳 Docker 상태 확인
----------------------------------------
✅ Docker Desktop 실행 중

🐍 Python 패키지 확인
----------------------------------------
✅ kfp: 1.8.22
✅ mlflow: 2.9.2
✅ scikit-learn: 1.3.2
✅ onnxruntime: 1.16.3

========================================
  확인 완료
========================================
```

---

## 8. 트러블슈팅

### ❌ Homebrew 설치 실패

**증상**: `curl: command not found` 또는 권한 오류

**해결**:
```bash
# Xcode Command Line Tools 설치
xcode-select --install
```

### ❌ Docker Desktop이 시작되지 않음

**증상**: Docker 아이콘이 회색이거나 에러 표시

**해결**:
1. Docker Desktop 완전 종료 (메뉴 바 → Quit Docker Desktop)
2. 재시작
3. 그래도 안 되면 Docker Desktop 재설치

### ❌ `command not found: kubectl`

**증상**: kubectl 설치 후에도 명령어 인식 안 됨

**해결**:
```bash
# PATH 확인
echo $PATH

# Homebrew PATH 추가 (Apple Silicon)
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 또는 (Intel)
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### ❌ Python 버전 충돌

**증상**: `python` 명령어가 Python 2를 가리킴

**해결**:
```bash
# python3 사용
python3 --version

# 또는 alias 설정
echo 'alias python=python3' >> ~/.zshrc
echo 'alias pip=pip3' >> ~/.zshrc
source ~/.zshrc
```

### ❌ pip 패키지 설치 오류

**증상**: `Could not find a version that satisfies the requirement`

**해결**:
```bash
# pip 업그레이드
python3 -m pip install --upgrade pip

# 개별 패키지 설치 시도
pip install kfp==1.8.22
pip install mlflow==2.9.2
```

### ❌ Apple Silicon에서 ONNX Runtime 설치 오류

**증상**: `Could not build wheels for onnxruntime`

**해결**:
```bash
# Rosetta 2 설치 (Intel 에뮬레이션)
softwareupdate --install-rosetta

# 또는 arm64 전용 버전 설치
pip install onnxruntime-silicon
```

---

## 📞 지원

설정 중 문제가 발생하면:
1. 이 문서의 트러블슈팅 섹션 확인
2. 교육 담당자에게 연락
3. 교육 당일 강사에게 문의

---

## ✅ 체크리스트

교육 시작 전 다음 항목을 모두 확인하세요:

- [ ] Homebrew 설치 완료
- [ ] AWS CLI 설치 완료 (`aws --version`)
- [ ] kubectl 설치 완료 (`kubectl version --client`)
- [ ] Docker Desktop 설치 및 실행 확인 (`docker info`)
- [ ] Python 3.9+ 설치 완료 (`python3 --version`)
- [ ] Git 설치 완료 (`git --version`)
- [ ] Python 패키지 설치 완료 (kfp, mlflow, scikit-learn, onnxruntime)
- [ ] 전체 확인 스크립트 실행 - 모든 항목 ✅

---

© 2025 현대오토에버 MLOps Training
