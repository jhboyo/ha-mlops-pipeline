# Lab 1-3: Batch 데이터 파이프라인

## 📋 실습 개요

| 항목 | 내용 |
|------|------|
| **소요시간** | 90분 (1.5시간) |
| **난이도** | ⭐⭐⭐ |
| **목표** | AWS S3 기반 Data Lake 구축 및 Batch 데이터 처리 파이프라인 구현 |

## 🎯 학습 목표

이 실습을 통해 다음을 학습합니다:
- **AWS S3 기반 Data Lake 아키텍처** 이해 및 구축
- **ETL Pipeline** 설계 및 구현
- **데이터 품질 관리** 자동화
- **대규모 Batch 데이터 처리** (Pandas/AWS Wrangler 활용)
- **Bronze → Silver → Gold Layer** 데이터 흐름 이해

---

## 🏗️ 실습 구조

```
Lab 1-3: Batch Data Pipeline (90분)
├── Part 1: ETL Pipeline (45분)
│   ├── S3 Data Lake 구축
│   ├── 샘플 데이터 생성 (1000명 고객)
│   ├── ETL 파이프라인 실행
│   └── 데이터 품질 검증
└── Part 2: Batch Processing (45분)
    ├── Silver Layer 데이터 읽기
    ├── Batch 데이터 집계 (Pandas)
    ├── 결과 분석
    └── Gold Layer 저장
```

---

## 📁 파일 구조

```
lab1-3_batch-pipeline/
├── README.md                        # ⭐ 이 파일 (실습 가이드)
├── requirements.txt                 # Python 패키지 목록
├── scripts/
│   ├── 1_etl_pipeline/
│   │   └── etl_pipeline.py         # Part 1: ETL 파이프라인 (45분)
│   └── 2_batch_processing/
│       └── pandas_batch_job.py     # Part 2: Batch 처리 (45분)
└── notebooks/
    └── batch_pipeline.ipynb        # Jupyter Notebook 실습 코드
```

---

## 🚀 Part 1: ETL Pipeline (45분)

### 학습 목표
- S3 Data Lake 구조 이해 (Bronze/Silver/Gold 레이어)
- Extract-Transform-Load 프로세스 구현
- 데이터 품질 검증 자동화

### Step 1-1: 환경 변수 설정

**실습 전 반드시 설정하세요!**

```bash
# 터미널에서 실행
export USER_NUM="01"  # ⚠️ 본인의 사용자 번호로 변경하세요!
export AWS_ACCESS_KEY_ID="your_access_key_here"
export AWS_SECRET_ACCESS_KEY="your_secret_key_here"
export AWS_DEFAULT_REGION="ap-northeast-2"
```

**환경 변수 설명:**
- `USER_NUM`: 사용자 번호 (예: 01, 02, 03...)
- `AWS_ACCESS_KEY_ID`: AWS 액세스 키 (강사가 제공)
- `AWS_SECRET_ACCESS_KEY`: AWS 시크릿 키 (강사가 제공)
- `AWS_DEFAULT_REGION`: AWS 리전 (서울: ap-northeast-2)

### Step 1-2: ETL 파이프라인 실행

```bash
# 스크립트 실행
python scripts/1_etl_pipeline/etl_pipeline.py
```

**또는 Jupyter Notebook에서:**
```python
%run scripts/1_etl_pipeline/etl_pipeline.py
```

### Step 1-3: 실행 결과 확인

**예상 출력:**
```
============================================================
ETL 파이프라인
============================================================

사용자: 01
버킷: mlops-training-user01
리전: ap-northeast-2

============================================================
STEP 1: S3 Data Lake 생성
============================================================
✅ 버킷 생성 완료: mlops-training-user01

Data Lake 구조:
  Bronze Layer (원본): s3://mlops-training-user01/raw/
  Silver Layer (정제): s3://mlops-training-user01/processed/
  Gold Layer (집계):   s3://mlops-training-user01/curated/

============================================================
STEP 2: 샘플 데이터 생성
============================================================
✅ 1000명 고객 데이터 생성 완료

데이터 품질 이슈 (의도적으로 추가됨):
  - Null 값: 33개
  - 중복: 33개
  - 잘못된 형식: 34개

============================================================
STEP 3: ETL 처리
============================================================
📥 Bronze Layer에서 1000행 로드
🔍 데이터 검증 중...

품질 이슈 발견:
  - Null 이메일: 33개
  - 중복 ID: 33개
  - 잘못된 이메일 형식: 34개
  - 총 이슈: 100개

🔧 데이터 정제 중:
  ✅ Null 이메일 제거: 33행
  ✅ 중복 제거: 33행
  ✅ 잘못된 이메일 형식 제거: 34행
  ✅ 정제된 데이터: 900행

📊 데이터 변환:
  ✅ email_domain 컬럼 추가
  ✅ age_group 컬럼 추가

💾 Silver Layer에 저장 중...
✅ 저장 완료: s3://mlops-training-user01/processed/customers_cleaned/

============================================================
데이터 품질 리포트
============================================================
데이터 품질 점수: 97.5%

✅ ETL 파이프라인 완료!
============================================================
```

### Step 1-4: S3 결과 확인

```bash
# Silver Layer 데이터 확인
aws s3 ls s3://mlops-training-user01/processed/customers_cleaned/ --recursive
```

**예상 출력:**
```
2025-12-08 14:00:00    123456 processed/customers_cleaned/part-0.parquet
```

---

## 🚀 Part 2: Batch Processing (45분)

### 학습 목표
- 대규모 데이터 Batch 처리
- Pandas 및 AWS Wrangler 활용
- Gold Layer 데이터 생성

### Step 2-1: Batch Processing 스크립트 이해

**스크립트가 하는 일:**
1. Silver Layer에서 Parquet 데이터 읽기 (AWS Wrangler 사용)
2. 도시별 고객 수 집계
3. 나이대별 분포 분석
4. 이메일 도메인 통계 계산
5. 결과를 Parquet로 Gold Layer에 저장

**왜 Pandas를 사용하나요?**
- ✅ 간단하고 직관적
- ✅ 추가 인프라 불필요
- ✅ AWS Wrangler와 완벽한 통합
- ✅ 1000행 규모에 최적화

### Step 2-2: Batch Processing 실행

```bash
python scripts/2_batch_processing/pandas_batch_job.py
```

**또는 Jupyter Notebook에서:**
```python
%run scripts/2_batch_processing/pandas_batch_job.py
```

### Step 2-3: 실행 결과 확인

**예상 출력:**
```
============================================================
BATCH 데이터 처리 (Pandas)
============================================================

사용자: 01
버킷: mlops-training-user01
리전: ap-northeast-2

============================================================
Silver Layer 데이터 읽기
============================================================
경로: s3://mlops-training-user01/processed/customers_cleaned/
✅ 900행 로드 완료

스키마:
customer_id         int64
name               object
age                 int64
email              object
city               object
join_date          object
email_domain       object
age_group          object
dtype: object

============================================================
데이터 분석
============================================================

1️⃣  도시별 고객 수:
     city  count
    Seoul    450
    Busan    320
  Incheon    100
    Daegu     30

2️⃣  나이대별 분포:
 age_group  count
     20-29    180
     30-39    250
     40-49    280
     50-59    150
       60+     40

3️⃣  이메일 도메인 Top 5:
 email_domain  count
  example.com    850
    gmail.com     30
   naver.com      15
  daum.net        3
  kakao.com       2

4️⃣  통계 요약:
 avg_age  max_age  total_customers
    38.5       69              900

============================================================
Gold Layer에 결과 저장
============================================================
경로: s3://mlops-training-user01/curated/analysis/
✅ 도시별 분석 저장: s3://.../city_analysis/
✅ 나이대별 분석 저장: s3://.../age_analysis/
✅ 도메인별 분석 저장: s3://.../domain_analysis/
✅ 통계 요약 저장: s3://.../statistics/
✅ 메타데이터 저장: s3://.../metadata/

============================================================
✅ BATCH 데이터 처리 완료!
============================================================

결과 위치: s3://mlops-training-user01/curated/analysis/

S3에서 확인:
  aws s3 ls s3://mlops-training-user01/curated/analysis/ --recursive

처리된 데이터:
  - 도시별 분석: 4개 도시
  - 나이대별 분석: 5개 그룹
  - 도메인별 분석: Top 5
  - 통계: 평균 나이 38.5세
```

### Step 2-4: S3 결과 확인

```bash
# 결과 파일 확인
aws s3 ls s3://mlops-training-user01/curated/analysis/ --recursive

# 예상 출력:
# curated/analysis/city_analysis/...parquet
# curated/analysis/age_analysis/...parquet
# curated/analysis/domain_analysis/...parquet
# curated/analysis/statistics/...parquet
# curated/analysis/metadata/...parquet
```

### Step 2-5: Jupyter에서 결과 읽기

```python
import awswrangler as wr

# Gold Layer 결과 읽기
city_df = wr.s3.read_parquet("s3://mlops-training-user01/curated/analysis/city_analysis/")
print("도시별 고객 수:")
print(city_df)

age_df = wr.s3.read_parquet("s3://mlops-training-user01/curated/analysis/age_analysis/")
print("\n나이대별 분포:")
print(age_df)
```

---

## ✅ 완료 체크리스트

### Part 1: ETL Pipeline (45분)
- [ ] S3 버킷 생성 완료
- [ ] 샘플 데이터 생성 완료 (1000명)
- [ ] ETL 파이프라인 실행 성공
- [ ] 데이터 품질 점수 ≥ 95%
- [ ] Silver Layer Parquet 저장 완료

### Part 2: Batch Processing (45분)
- [ ] Batch processing 스크립트 이해
- [ ] pandas_batch_job.py 실행 성공
- [ ] 도시별 분석 결과 확인
- [ ] 나이대별 분석 결과 확인
- [ ] Gold Layer 저장 완료
- [ ] S3에서 결과 파일 확인

---

## 🎯 학습 성과

이 실습을 완료하면:

1. ✅ **Data Lake 아키텍처** 이해 (Bronze/Silver/Gold Layer)
2. ✅ **ETL Pipeline** 완전한 이해
3. ✅ **데이터 품질 관리** 자동화 구현
4. ✅ **Batch 데이터 처리** 실무 경험
5. ✅ **AWS Wrangler** 활용 능력
6. ✅ **프로덕션 데이터 파이프라인** 설계 역량

---

## 💡 문제 해결

### 문제: S3 연결 오류
**해결 방법:**
```bash
# AWS 자격 증명 확인
aws sts get-caller-identity

# S3 접근 테스트
aws s3 ls s3://mlops-training-user01/
```

### 문제: 패키지 설치 오류
**해결 방법:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 문제: 대용량 데이터로 메모리 오류
**해결 방법:**
- 샘플 데이터 크기 줄이기
- 청크 단위로 처리
- 인스턴스 메모리 증설

---

## 📚 다음 단계

**Day 2: 모델 서빙 & 버전 관리**
- Lab 2-1: FastAPI 모델 서빙
- Lab 2-2: MLflow Tracking & Registry
- Lab 2-3: KServe 모델 배포

---

© 2025 현대오토에버 MLOps Training
