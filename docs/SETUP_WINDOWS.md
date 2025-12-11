# 🪟 Windows 환경 설정 가이드

> **MLOps 파이프라인 구현 [고급]** - 수강 전 사전 설정

## ⚠️ 중요 안내

**이 문서는 교육 시작 전에 반드시 완료해야 합니다.**  
교육 당일에는 환경 설정을 위한 별도의 시간이 제공되지 않습니다.

---

## 📋 목차

1. [시스템 요구사항](#1-시스템-요구사항)
2. [WSL2 설치 (필수)](#2-wsl2-설치-필수)
3. [Docker Desktop 설치](#3-docker-desktop-설치)
4. [Windows Terminal 설치 (권장)](#4-windows-terminal-설치-권장)
5. [필수 도구 설치](#5-필수-도구-설치)
6. [Python 환경 설정](#6-python-환경-설정)
7. [VS Code 설치 (권장)](#7-vs-code-설치-권장)
8. [설치 확인](#8-설치-확인)
9. [트러블슈팅](#9-트러블슈팅)

---

## 1. 시스템 요구사항

| 항목 | 최소 사양 | 권장 사양 |
|------|----------|----------|
| **Windows 버전** | Windows 10 버전 2004 이상 | Windows 11 |
| **프로세서** | 64비트 CPU (가상화 지원) | Intel i5 / AMD Ryzen 5 이상 |
| **메모리** | 8GB | 16GB 이상 |
| **디스크 공간** | 30GB 여유 | 50GB 이상 여유 |
| **네트워크** | 인터넷 연결 필수 | 안정적인 인터넷 |

### 시스템 정보 확인

1. **Windows 버전 확인**: `Win + R` → `winver` 입력
2. **시스템 정보**: `Win + R` → `msinfo32` 입력

### BIOS 가상화 활성화 확인

WSL2와 Docker를 사용하려면 BIOS에서 가상화가 활성화되어 있어야 합니다.

```powershell
# PowerShell (관리자)에서 실행
systeminfo | findstr "Hyper-V"
```

**예상 출력:**
```
Hyper-V 요구 사항:      VM 모니터 모드 확장: 예
                        펌웨어에서 가상화 사용: 예
                        ...
```

`가상화 사용: 예`가 아니라면 BIOS에서 활성화 필요:
- Intel: Intel VT-x 또는 Intel Virtualization Technology 활성화
- AMD: AMD-V 또는 SVM Mode 활성화

---

## 2. WSL2 설치 (필수)

WSL2 (Windows Subsystem for Linux 2)는 Windows에서 Linux 환경을 실행합니다.

### Step 2-1: WSL2 설치

**PowerShell을 관리자 권한으로 실행** (시작 메뉴 → "PowerShell" 검색 → 우클릭 → "관리자 권한으로 실행")

```powershell
# WSL 설치 (Ubuntu가 기본으로 설치됨)
wsl --install

# 설치 완료 후 재부팅 필요
```

### Step 2-2: 재부팅 후 Ubuntu 설정

1. 재부팅 후 자동으로 Ubuntu 터미널이 열림
2. 새 UNIX 사용자명 입력 (예: `mlops`)
3. 새 비밀번호 입력 (2번)

### Step 2-3: WSL2 버전 확인

```powershell
# PowerShell에서 실행
wsl --list --verbose
```

**예상 출력:**
```
  NAME                   STATE           VERSION
* Ubuntu                 Running         2
```

VERSION이 `2`인지 확인하세요.

### Step 2-4: Ubuntu 업데이트

Ubuntu 터미널에서:

```bash
# 패키지 목록 업데이트
sudo apt update

# 패키지 업그레이드
sudo apt upgrade -y
```

---

## 3. Docker Desktop 설치

### Step 3-1: Docker Desktop 다운로드

1. [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 접속
2. **"Download for Windows"** 클릭
3. 다운로드된 `Docker Desktop Installer.exe` 실행

### Step 3-2: 설치 옵션

설치 중 다음 옵션 선택:
- ✅ **Use WSL 2 instead of Hyper-V** (권장)
- ✅ **Add shortcut to desktop**

### Step 3-3: 재부팅 및 실행

1. 설치 완료 후 재부팅
2. Docker Desktop 실행
3. 시스템 트레이에 Docker 아이콘(고래)이 나타날 때까지 대기

### Step 3-4: WSL2 통합 설정

Docker Desktop에서:
1. Settings (⚙️) 클릭
2. **Resources** → **WSL Integration**
3. **Enable integration with my default WSL distro** 활성화
4. Ubuntu 옆 토글 활성화
5. **Apply & Restart** 클릭

### Step 3-5: Docker 리소스 설정

Settings → Resources → Advanced:
- **Memory**: 4GB 이상 권장
- **CPUs**: 2 이상 권장
- **Disk image size**: 20GB 이상

### Step 3-6: 설치 확인

Ubuntu 터미널에서:

```bash
# Docker 버전 확인
docker --version

# Docker 실행 확인
docker run hello-world
```

**예상 출력:**
```
Docker version 24.x.x, build xxxxxxx
```

---

## 4. Windows Terminal 설치 (권장)

Windows Terminal은 WSL2, PowerShell, CMD를 하나의 앱에서 관리합니다.

### Step 4-1: 설치

**방법 1: Microsoft Store (권장)**
1. Microsoft Store 열기
2. "Windows Terminal" 검색
3. 설치

**방법 2: winget 사용**
```powershell
# PowerShell에서 실행
winget install Microsoft.WindowsTerminal
```

### Step 4-2: 기본 프로필 설정

Windows Terminal 실행 후:
1. 설정 (⚙️ 또는 `Ctrl + ,`)
2. **Startup** → **Default profile** → **Ubuntu** 선택
3. 저장

---

## 5. 필수 도구 설치

**이제부터는 Ubuntu (WSL2) 터미널에서 작업합니다.**

Windows Terminal 실행 → Ubuntu 탭 선택 (또는 시작 메뉴에서 Ubuntu 실행)

### Step 5-1: 기본 도구 설치

```bash
# 필수 패키지 설치
sudo apt update
sudo apt install -y curl wget unzip jq
```

### Step 5-2: AWS CLI 설치

```bash
# AWS CLI v2 다운로드 및 설치
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf awscliv2.zip aws/

# 설치 확인
aws --version
```

**예상 출력:**
```
aws-cli/2.x.x Python/3.x.x Linux/5.x.x-microsoft-standard-WSL2 exe/x86_64.ubuntu.22
```

### Step 5-3: kubectl 설치

```bash
# kubectl 다운로드
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# 설치
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl

# 설치 확인
kubectl version --client
```

**예상 출력:**
```
Client Version: v1.28.x
Kustomize Version: v5.x.x
```

### Step 5-4: Git 설치

```bash
# Git 설치 (대부분 이미 설치됨)
sudo apt install -y git

# 설치 확인
git --version

# Git 사용자 설정 (선택)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## 6. Python 환경 설정

### Step 6-1: Python 설치

Ubuntu에는 Python 3가 기본 설치되어 있습니다:

```bash
# Python 버전 확인
python3 --version

# pip 설치 (없는 경우)
sudo apt install -y python3-pip python3-venv
```

### Step 6-2: 가상환경 생성 (권장)

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

### Step 6-3: pip 업그레이드 및 필수 패키지 설치

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

### Step 6-4: 패키지 설치 확인

```bash
python -c "import kfp; print(f'KFP: {kfp.__version__}')"
python -c "import mlflow; print(f'MLflow: {mlflow.__version__}')"
python -c "import sklearn; print(f'Scikit-learn: {sklearn.__version__}')"
python -c "import onnxruntime; print(f'ONNX Runtime: {onnxruntime.__version__}')"
```

---

## 7. VS Code 설치 (권장)

### Step 7-1: Windows에 VS Code 설치

1. [VS Code 공식 사이트](https://code.visualstudio.com/) 접속
2. **Download for Windows** 클릭
3. 설치 실행

### Step 7-2: WSL 확장 설치

VS Code 실행 후:
1. Extensions (Ctrl+Shift+X) 열기
2. **"WSL"** 검색 → 설치
3. **"Remote - WSL"** 확장 설치

### Step 7-3: WSL에서 VS Code 열기

Ubuntu 터미널에서:

```bash
# VS Code 열기 (WSL 연결)
code .

# 첫 실행 시 VS Code Server 설치됨
```

### Step 7-4: 추가 확장 프로그램

VS Code에서 설치 권장:

| 확장 프로그램 | 용도 |
|--------------|------|
| **Python** | Python 개발 |
| **Jupyter** | Notebook 지원 |
| **Docker** | Docker 관리 |
| **YAML** | YAML 파일 편집 |
| **Kubernetes** | K8s 리소스 관리 |

---

## 8. 설치 확인

### 전체 확인 스크립트

Ubuntu 터미널에서 다음 스크립트를 실행합니다:

```bash
#!/bin/bash

echo "========================================"
echo "  MLOps 환경 설정 확인 (Windows/WSL2)"
echo "========================================"
echo ""

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

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

echo "📦 필수 도구 확인"
echo "----------------------------------------"
check_command "aws" "aws --version"
check_command "kubectl" "kubectl version --client --short"
check_command "docker" "docker --version"
check_command "python3" "python3 --version"
check_command "git" "git --version"

echo ""
echo "🐳 Docker 상태 확인"
echo "----------------------------------------"
if docker info &> /dev/null; then
    echo -e "${GREEN}✅ Docker Desktop 실행 중 (WSL2 통합)${NC}"
else
    echo -e "${RED}❌ Docker Desktop이 실행되지 않음${NC}"
    echo "   Docker Desktop을 실행하고 WSL2 통합을 확인하세요"
fi

echo ""
echo "🐍 Python 패키지 확인"
echo "----------------------------------------"
python3 -c "import kfp; print(f'✅ kfp: {kfp.__version__}')" 2>/dev/null || echo "❌ kfp: 설치되지 않음"
python3 -c "import mlflow; print(f'✅ mlflow: {mlflow.__version__}')" 2>/dev/null || echo "❌ mlflow: 설치되지 않음"
python3 -c "import sklearn; print(f'✅ scikit-learn: {sklearn.__version__}')" 2>/dev/null || echo "❌ scikit-learn: 설치되지 않음"
python3 -c "import onnxruntime; print(f'✅ onnxruntime: {onnxruntime.__version__}')" 2>/dev/null || echo "❌ onnxruntime: 설치되지 않음"

echo ""
echo "🔧 WSL2 정보"
echo "----------------------------------------"
echo "배포판: $(lsb_release -d 2>/dev/null | cut -f2)"
echo "커널: $(uname -r)"

echo ""
echo "========================================"
echo "  확인 완료"
echo "========================================"
```

### 스크립트 실행 방법

```bash
# 스크립트 저장
cat > check_env.sh << 'ENDOFSCRIPT'
[위 스크립트 내용 복사]
ENDOFSCRIPT

# 실행 권한 부여 및 실행
chmod +x check_env.sh
./check_env.sh
```

### 예상 결과

```
========================================
  MLOps 환경 설정 확인 (Windows/WSL2)
========================================

📦 필수 도구 확인
----------------------------------------
✅ aws: aws-cli/2.15.0 Python/3.11.6 Linux/5.15.133.1-microsoft-standard-WSL2
✅ kubectl: Client Version: v1.28.4
✅ docker: Docker version 24.0.7, build afdd53b
✅ python3: Python 3.10.12
✅ git: git version 2.34.1

🐳 Docker 상태 확인
----------------------------------------
✅ Docker Desktop 실행 중 (WSL2 통합)

🐍 Python 패키지 확인
----------------------------------------
✅ kfp: 1.8.22
✅ mlflow: 2.9.2
✅ scikit-learn: 1.3.2
✅ onnxruntime: 1.16.3

🔧 WSL2 정보
----------------------------------------
배포판: Ubuntu 22.04.3 LTS
커널: 5.15.133.1-microsoft-standard-WSL2

========================================
  확인 완료
========================================
```

---

## 9. 트러블슈팅

### ❌ WSL2 설치 실패

**증상**: `wsl --install` 실행 시 오류

**해결**:
```powershell
# 1. Windows 기능 수동 활성화 (관리자 PowerShell)
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 2. 재부팅

# 3. WSL2 커널 업데이트
# https://aka.ms/wsl2kernel 에서 다운로드 및 설치

# 4. WSL2를 기본으로 설정
wsl --set-default-version 2

# 5. Ubuntu 설치
wsl --install -d Ubuntu
```

### ❌ Docker Desktop이 시작되지 않음

**증상**: "Docker Desktop stopped" 또는 WSL2 오류

**해결**:
1. Docker Desktop 완전 종료
2. 작업 관리자에서 Docker 관련 프로세스 모두 종료
3. 재부팅
4. Docker Desktop 재실행

**WSL2 통합 문제**:
```powershell
# WSL2 재시작
wsl --shutdown
# Docker Desktop 재실행
```

### ❌ Docker WSL2 통합이 안 됨

**증상**: Ubuntu에서 `docker` 명령어 인식 안 됨

**해결**:
1. Docker Desktop → Settings → Resources → WSL Integration
2. Ubuntu 토글 활성화 확인
3. Apply & Restart
4. Ubuntu 터미널 재시작

### ❌ kubectl 연결 오류

**증상**: `Unable to connect to the server`

**해결**:
```bash
# kubeconfig 경로 확인
echo $KUBECONFIG

# Windows kubeconfig를 WSL에서 사용
export KUBECONFIG=/mnt/c/Users/[사용자명]/.kube/config

# 또는 WSL에 별도 설정
mkdir -p ~/.kube
cp /mnt/c/Users/[사용자명]/.kube/config ~/.kube/config
```

### ❌ Windows 경로 접근

**팁**: WSL에서 Windows 파일시스템 접근:

```bash
# C 드라이브
cd /mnt/c

# 사용자 폴더
cd /mnt/c/Users/[사용자명]

# 바탕화면
cd /mnt/c/Users/[사용자명]/Desktop
```

### ❌ 줄바꿈 문제 (CRLF vs LF)

**증상**: 스크립트 실행 시 `\r` 오류

**해결**:
```bash
# dos2unix 설치 및 변환
sudo apt install dos2unix
dos2unix script.sh

# 또는 sed 사용
sed -i 's/\r$//' script.sh
```

### ❌ 메모리 부족

**증상**: WSL2가 메모리를 너무 많이 사용

**해결**: `%UserProfile%\.wslconfig` 파일 생성

```ini
[wsl2]
memory=4GB
processors=2
swap=2GB
```

파일 저장 후 `wsl --shutdown` 실행

---

## 📞 지원

설정 중 문제가 발생하면:
1. 이 문서의 트러블슈팅 섹션 확인
2. 교육 담당자에게 연락
3. 교육 당일 강사에게 문의

---

## ✅ 체크리스트

교육 시작 전 다음 항목을 모두 확인하세요:

- [ ] Windows 10 버전 2004 이상 / Windows 11 확인
- [ ] BIOS 가상화 활성화 확인
- [ ] WSL2 설치 완료 (Ubuntu)
- [ ] Docker Desktop 설치 및 WSL2 통합 완료
- [ ] Windows Terminal 설치 (권장)
- [ ] AWS CLI 설치 완료 (`aws --version`)
- [ ] kubectl 설치 완료 (`kubectl version --client`)
- [ ] Git 설치 완료 (`git --version`)
- [ ] Python 3.9+ 설치 완료 (`python3 --version`)
- [ ] Python 패키지 설치 완료 (kfp, mlflow, scikit-learn, onnxruntime)
- [ ] 전체 확인 스크립트 실행 - 모든 항목 ✅

---

© 2025 현대오토에버 MLOps Training
