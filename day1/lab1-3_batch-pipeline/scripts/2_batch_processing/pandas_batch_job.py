#!/usr/bin/env python3
"""
Lab 1-3 Part 2: Batch 데이터 처리 (Pandas)
Silver Layer 데이터를 Pandas로 집계하여 Gold Layer에 저장

이 스크립트는 다음을 수행합니다:
1. Silver Layer에서 정제된 데이터 읽기
2. 여러 기준으로 데이터 집계 (도시, 나이대, 이메일 도메인)
3. 통계 계산 (평균, 최대값 등)
4. 결과를 Gold Layer에 Parquet로 저장
"""

import os
import pandas as pd
import awswrangler as wr
from datetime import datetime

print("=" * 60)
print("BATCH 데이터 처리 (Pandas)")
print("=" * 60)

# ============================================================
# 환경 설정
# ============================================================

# 환경 변수 읽기
USER_NUM = os.getenv('USER_NUM', '01')
BUCKET_NAME = f"mlops-training-user{USER_NUM}"
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'ap-northeast-2')

print(f"\n사용자: {USER_NUM}")
print(f"버킷: {BUCKET_NAME}")
print(f"리전: {AWS_REGION}")

# ============================================================
# Silver Layer 데이터 읽기
# ============================================================

silver_path = f"s3://{BUCKET_NAME}/processed/customers_cleaned/"
print(f"\n{'=' * 60}")
print(f"Silver Layer 데이터 읽기")
print(f"{'=' * 60}")
print(f"경로: {silver_path}")

try:
    # AWS Wrangler로 Parquet 읽기
    df = wr.s3.read_parquet(silver_path)
    print(f"✅ {len(df)}행 로드 완료")
    print(f"\n스키마:")
    print(df.dtypes)
    
except Exception as e:
    print(f"❌ 데이터 읽기 실패: {e}")
    print(f"\n가능한 원인:")
    print(f"  1. Silver Layer 데이터가 없음 (Part 1을 먼저 실행하세요)")
    print(f"  2. S3 권한 문제")
    print(f"  3. 경로 오류")
    exit(1)

# ============================================================
# 데이터 분석
# ============================================================

print("\n" + "=" * 60)
print("데이터 분석")
print("=" * 60)

# 1. 도시별 고객 수 집계
print("\n1️⃣  도시별 고객 수:")
city_counts = df.groupby('city').size().reset_index(name='count')
city_counts = city_counts.sort_values('count', ascending=False)
print(city_counts.to_string(index=False))

# 2. 나이대별 분포
print("\n2️⃣  나이대별 분포:")
age_group_counts = df.groupby('age_group').size().reset_index(name='count')
age_group_counts = age_group_counts.sort_values('age_group')
print(age_group_counts.to_string(index=False))

# 3. 이메일 도메인별 분포 (Top 5)
print("\n3️⃣  이메일 도메인 Top 5:")
domain_counts = df.groupby('email_domain').size().reset_index(name='count')
domain_counts = domain_counts.sort_values('count', ascending=False).head(5)
print(domain_counts.to_string(index=False))

# 4. 통계 요약
print("\n4️⃣  통계 요약:")
stats = pd.DataFrame({
    'avg_age': [df['age'].mean()],
    'max_age': [df['age'].max()],
    'total_customers': [len(df)]
})
print(stats.to_string(index=False))

# ============================================================
# Gold Layer에 결과 저장
# ============================================================

gold_path = f"s3://{BUCKET_NAME}/curated/analysis/"
print("\n" + "=" * 60)
print(f"Gold Layer에 결과 저장")
print(f"{'=' * 60}")
print(f"경로: {gold_path}")

try:
    # 1) 도시별 분석 저장
    city_output = gold_path + "city_analysis/"
    wr.s3.to_parquet(
        df=city_counts,
        path=city_output,
        dataset=True,
        mode='overwrite'
    )
    print(f"✅ 도시별 분석 저장: {city_output}")
    
    # 2) 나이대별 분석 저장
    age_output = gold_path + "age_analysis/"
    wr.s3.to_parquet(
        df=age_group_counts,
        path=age_output,
        dataset=True,
        mode='overwrite'
    )
    print(f"✅ 나이대별 분석 저장: {age_output}")
    
    # 3) 도메인별 분석 저장
    domain_output = gold_path + "domain_analysis/"
    wr.s3.to_parquet(
        df=domain_counts,
        path=domain_output,
        dataset=True,
        mode='overwrite'
    )
    print(f"✅ 도메인별 분석 저장: {domain_output}")
    
    # 4) 통계 요약 저장
    stats_output = gold_path + "statistics/"
    wr.s3.to_parquet(
        df=stats,
        path=stats_output,
        dataset=True,
        mode='overwrite'
    )
    print(f"✅ 통계 요약 저장: {stats_output}")
    
    # 5) 메타데이터 저장
    metadata = pd.DataFrame({
        'processed_at': [datetime.now()],
        'total_rows': [len(df)],
        'source': [silver_path]
    })
    metadata_output = gold_path + "metadata/"
    wr.s3.to_parquet(
        df=metadata,
        path=metadata_output,
        dataset=True,
        mode='overwrite'
    )
    print(f"✅ 메타데이터 저장: {metadata_output}")
    
except Exception as e:
    print(f"❌ 저장 실패: {e}")
    exit(1)

# ============================================================
# 완료
# ============================================================

print("\n" + "=" * 60)
print("✅ BATCH 데이터 처리 완료!")
print("=" * 60)

print(f"\n결과 위치: {gold_path}")
print(f"\nS3에서 확인:")
print(f"  aws s3 ls s3://{BUCKET_NAME}/curated/analysis/ --recursive")

print(f"\n처리된 데이터:")
print(f"  - 도시별 분석: {len(city_counts)}개 도시")
print(f"  - 나이대별 분석: {len(age_group_counts)}개 그룹")
print(f"  - 도메인별 분석: Top {len(domain_counts)}")
print(f"  - 통계: 평균 나이 {stats['avg_age'].values[0]:.1f}세")

print(f"\n다음 단계:")
print(f"  - Jupyter Notebook에서 시각화:")
print(f"    notebooks/batch_pipeline.ipynb 수행")
