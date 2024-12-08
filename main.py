# uvicorn main:app --port=8081 --reload --host 0.0.0.0
from fastapi import FastAPI
from middleware.logging_middleware import logging_middleware
from utils.logger import logger
from pydantic import BaseModel

app = FastAPI()
app.middleware("http")(logging_middleware)


class TestRequest(BaseModel):
    user_id: str
    message: str


@app.get("/ping")
async def ping():
    """간단한 헬스체크 API"""
    await logger.info("ping 요청 받음")
    return {"status": "ok", "message": "pong"}

@app.post("/test-log")
async def test_logging(request: TestRequest):
    """로깅 테스트를 위한 API"""
    logger.set_context(user_id=request.user_id)
    
    try:
        await logger.info(f"테스트 메시지 수신: {request.message}")
        await logger.debug("디버그 레벨 로그 테스트")
        
        if request.message == "error":
            raise ValueError("테스트 에러 발생")
            
        return {
            "status": "success",
            "message": "로그 테스트 완료",
            "your_message": request.message
        }
    except Exception as e:
        await logger.error(f"에러 발생: {str(e)}", exc_info=True)
        raise