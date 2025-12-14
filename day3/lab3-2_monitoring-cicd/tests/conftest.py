"""
Pytest configuration and shared fixtures
"""

import pytest
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def random_seed():
    """고정된 랜덤 시드"""
    np.random.seed(42)
    return 42


@pytest.fixture(scope="session")
def sample_features():
    """샘플 입력 특성 (California Housing)"""
    return [8.3252, 41.0, 6.984127, 1.023810, 322.0, 2.555556, 37.88, -122.23]


@pytest.fixture(scope="session")
def sample_batch_features():
    """배치 입력 특성"""
    return [
        [8.3252, 41.0, 6.984127, 1.023810, 322.0, 2.555556, 37.88, -122.23],
        [5.6431, 52.0, 5.817352, 1.073059, 558.0, 2.547945, 37.85, -122.25],
        [3.8462, 35.0, 6.281853, 1.081081, 565.0, 2.181467, 37.85, -122.26]
    ]
