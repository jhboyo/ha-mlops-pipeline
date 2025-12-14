#!/usr/bin/env python3
"""
Model Serving Entry Point

KServe/Knative 환경에서 모델 서빙을 위한 진입점
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """서버 시작"""
    try:
        import uvicorn
        from src.model.trainer import train_model
        from src.serving.api import create_app
        
        # 환경 변수에서 설정 읽기
        port = int(os.environ.get("PORT", 8080))
        model_name = os.environ.get("MODEL_NAME", "california-housing")
        model_version = os.environ.get("MODEL_VERSION", "v1.0")
        
        logger.info(f"=" * 50)
        logger.info(f"Starting Model Server")
        logger.info(f"  Model: {model_name}")
        logger.info(f"  Version: {model_version}")
        logger.info(f"  Port: {port}")
        logger.info(f"=" * 50)
        
        # 모델 학습
        logger.info("Training model...")
        model, metrics = train_model(model_type="random_forest")
        logger.info(f"Model trained successfully!")
        logger.info(f"  MAE: {metrics['mae']:.4f}")
        logger.info(f"  R²: {metrics['r2']:.4f}")
        
        # FastAPI 앱 생성
        logger.info("Creating FastAPI application...")
        app = create_app(model=model, model_version=model_version)
        
        if app is None:
            logger.error("Failed to create FastAPI app")
            sys.exit(1)
        
        # 서버 시작
        logger.info(f"Starting uvicorn server on 0.0.0.0:{port}...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        logger.error(f"Missing dependencies: {e}")
        logger.error("Please ensure all requirements are installed")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
