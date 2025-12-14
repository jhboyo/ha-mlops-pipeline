#!/usr/bin/env python3
"""
Lab 1-3 Part 1: ETL Pipeline
AWS S3 기반 Data Lake 구축 및 데이터 정제 파이프라인

이 스크립트는 다음을 수행합니다:
1. S3 Data Lake 구조 생성 (Bronze/Silver/Gold Layer)
2. 샘플 고객 데이터 생성 (1000명, 의도적인 품질 이슈 포함)
3. ETL 프로세스 실행 (Extract-Transform-Load)
4. 데이터 품질 검증 및 정제
5. Silver Layer에 정제된 데이터 저장
"""

import os
import pandas as pd
import numpy as np
import boto3
from datetime import datetime, timedelta
import awswrangler as wr

# ============================================================
# 환경 설정
# ============================================================

print("=" * 60)
print("ETL 파이프라인")
print("=" * 60)

# 환경 변수 읽기
USER_NUM = os.getenv('USER_NUM', '01')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'ap-northeast-2')

# S3 버킷 이름 생성
BUCKET_NAME = f"mlops-training-user{USER_NUM}"

print(f"\n사용자: {USER_NUM}")
print(f"버킷: {BUCKET_NAME}")
print(f"리전: {AWS_REGION}")

# ============================================================
# STEP 1: S3 Data Lake 구조 생성
# ============================================================

print("\n" + "=" * 60)
print("STEP 1: S3 Data Lake 생성")
print("=" * 60)

# boto3 S3 클라이언트 생성
s3_client = boto3.client('s3', region_name=AWS_REGION)

# Data Lake 레이어 정의
BRONZE_LAYER = f"s3://{BUCKET_NAME}/raw/"  # 원본 데이터
SILVER_LAYER = f"s3://{BUCKET_NAME}/processed/"  # 정제된 데이터
GOLD_LAYER = f"s3://{BUCKET_NAME}/curated/"  # 집계된 데이터

print("\nData Lake 구조:")
print(f"  Bronze Layer (원본): {BRONZE_LAYER}")
print(f"  Silver Layer (정제): {SILVER_LAYER}")
print(f"  Gold Layer (집계):   {GOLD_LAYER}")

# ============================================================
# STEP 2: 샘플 데이터 생성
# ============================================================

print("\n" + "=" * 60)
print("STEP 2: 샘플 데이터 생성")
print("=" * 60)

# 랜덤 시드 고정 (재현 가능성)
np.random.seed(42)

# 고객 데이터 생성
num_customers = 1000
customer_ids = list(range(1, num_customers + 1))
names = [f"Customer_{i}" for i in customer_ids]
ages = np.random.randint(18, 70, num_customers)
emails = [f"user{i}@example.com" for i in customer_ids]
cities = np.random.choice(['Seoul', 'Busan', 'Incheon', 'Daegu'], num_customers)

# 가입일 생성 (최근 1년 내)
join_dates = [
    datetime.now() - timedelta(days=np.random.randint(1, 365))
    for _ in range(num_customers)
]

# ⚠️ 의도적으로 데이터 품질 이슈 추가 (10%)
issue_indices = np.random.choice(num_customers, size=100, replace=False)

# 1. Null 값 추가 (33개)
for idx in issue_indices[:33]:
    emails[idx] = None

# 2. 중복 추가 (33개)
for idx in issue_indices[33:66]:
    customer_ids[idx] = customer_ids[0]  # 첫 번째 ID와 동일하게

# 3. 잘못된 이메일 형식 추가 (34개)
for idx in issue_indices[66:]:
    emails[idx] = f"invalid_{idx}"  # @ 없는 잘못된 형식

# DataFrame 생성
df_customers = pd.DataFrame({
    'customer_id': customer_ids,
    'name': names,
    'age': ages,
    'email': emails,
    'city': cities,
    'join_date': join_dates
})

print(f"✅ {len(df_customers)}명 고객 데이터 생성 완료")
print(f"\n데이터 품질 이슈 (의도적으로 추가됨):")
print(f"  - Null 값: {df_customers['email'].isnull().sum()}개")
print(f"  - 중복: {df_customers['customer_id'].duplicated().sum()}개")
print(f"  - 잘못된 형식: {len([e for e in emails if e and '@' not in str(e)])}개")

# Bronze Layer에 저장
bronze_path = BRONZE_LAYER + "customers_raw/"
wr.s3.to_parquet(
    df=df_customers,
    path=bronze_path,
    dataset=True,
    mode='overwrite'
)
print(f"\n✅ Bronze Layer 저장 완료: {bronze_path}")

# ============================================================
# STEP 3: ETL 프로세스
# ============================================================

print("\n" + "=" * 60)
print("STEP 3: ETL 처리")
print("=" * 60)

# 3-1. Extract (추출): Bronze Layer에서 데이터 읽기
df_raw = wr.s3.read_parquet(bronze_path)
print(f"📥 Bronze Layer에서 {len(df_raw)}행 로드")

# 3-2. Transform (변환): 데이터 정제 및 변환

print("🔍 데이터 검증 중...")

# 품질 이슈 카운트
null_emails = df_raw['email'].isnull().sum()
duplicate_ids = df_raw['customer_id'].duplicated().sum()
invalid_emails = len(df_raw[df_raw['email'].notna() & ~df_raw['email'].str.contains('@', na=False)])

print(f"\n품질 이슈 발견:")
print(f"  - Null 이메일: {null_emails}개")
print(f"  - 중복 ID: {duplicate_ids}개")
print(f"  - 잘못된 이메일 형식: {invalid_emails}개")
print(f"  - 총 이슈: {null_emails + duplicate_ids + invalid_emails}개")

print(f"\n🔧 데이터 정제 중:")

# 데이터 정제
df_clean = df_raw.copy()

# 1) Null 이메일 제거
before_count = len(df_clean)
df_clean = df_clean[df_clean['email'].notna()]
print(f"  ✅ Null 이메일 제거: {before_count - len(df_clean)}행")

# 2) 중복 제거 (customer_id 기준)
before_count = len(df_clean)
df_clean = df_clean.drop_duplicates(subset=['customer_id'])
print(f"  ✅ 중복 제거: {before_count - len(df_clean)}행")

# 3) 잘못된 이메일 형식 제거
before_count = len(df_clean)
df_clean = df_clean[df_clean['email'].str.contains('@', na=False)]
print(f"  ✅ 잘못된 이메일 형식 제거: {before_count - len(df_clean)}행")

print(f"  ✅ 정제된 데이터: {len(df_clean)}행")

# 데이터 변환: 새로운 컬럼 추가
print(f"\n📊 데이터 변환:")

# 1) 이메일 도메인 추출
df_clean['email_domain'] = df_clean['email'].str.split('@').str[1]
print(f"  ✅ email_domain 컬럼 추가")

# 2) 나이대 그룹 생성
def age_to_group(age):
    """나이를 나이대 그룹으로 변환"""
    if age < 30:
        return '20-29'
    elif age < 40:
        return '30-39'
    elif age < 50:
        return '40-49'
    elif age < 60:
        return '50-59'
    else:
        return '60+'

df_clean['age_group'] = df_clean['age'].apply(age_to_group)
print(f"  ✅ age_group 컬럼 추가")

# 3-3. Load (적재): Silver Layer에 저장
silver_path = SILVER_LAYER + "customers_cleaned/"
print(f"\n💾 Silver Layer에 저장 중...")

wr.s3.to_parquet(
    df=df_clean,
    path=silver_path,
    dataset=True,
    mode='overwrite'
)
print(f"✅ 저장 완료: {silver_path}")

# ============================================================
# 데이터 품질 리포트
# ============================================================

print("\n" + "=" * 60)
print("데이터 품질 리포트")
print("=" * 60)

# 품질 점수 계산
total_rows = len(df_raw)
cleaned_rows = len(df_clean)
quality_score = (cleaned_rows / total_rows) * 100

print(f"데이터 품질 점수: {quality_score:.1f}%")
print(f"\n원본 데이터: {total_rows}행")
print(f"정제된 데이터: {cleaned_rows}행")
print(f"제거된 데이터: {total_rows - cleaned_rows}행")

# 품질 이슈 요약
print(f"\n품질 이슈 해결:")
print(f"  ✅ Null 값 처리 완료")
print(f"  ✅ 중복 제거 완료")
print(f"  ✅ 데이터 형식 검증 완료")

print("\n" + "=" * 60)
print("✅ ETL 파이프라인 완료!")
print("=" * 60)

print(f"\n다음 단계:")
print(f"  - Silver Layer 데이터 확인:")
print(f"    aws s3 ls {silver_path} --recursive")
print(f"\n  - Part 2 실행:")
print(f"    python scripts/2_batch_processing/pandas_batch_job.py")
