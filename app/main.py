"""
FastAPI 메인 애플리케이션
PostgreSQL 데이터베이스 연결 및 기본 엔드포인트 제공
"""
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# FastAPI 앱 인스턴스 생성
app = FastAPI(title="Livbee Backend API", version="1.0.0")


@app.get("/")
async def root():
    """기본 라우트 - Hello 메시지 반환"""
    return {"message": "Hello Livbee"}


@app.get("/db-test")
async def db_test():
    """데이터베이스 연결 테스트 엔드포인트"""
    # 환경변수에서 DB 연결 정보 가져오기
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    
    # 필수 환경변수 검증
    if not all([db_host, db_name, db_user, db_password]):
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "데이터베이스 연결 정보가 환경변수에 설정되지 않았습니다."
            }
        )
    
    try:
        # PostgreSQL 연결 시도
        connection = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        # 연결 성공 시 쿼리 실행하여 확인
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return {
            "status": "success",
            "message": "데이터베이스 연결 성공",
            "database_version": db_version[0] if db_version else "Unknown"
        }
        
    except OperationalError as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"데이터베이스 연결 실패: {str(e)}"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"예상치 못한 오류 발생: {str(e)}"
            }
        )

