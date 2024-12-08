# utils/logger.py (단순화된 버전)
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from pathlib import Path
from contextvars import ContextVar
from typing import Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json

@dataclass
class RequestContext:
    timestamp: str = None
    request_id: str = '-'
    user_id: str = '-'
    extra: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def as_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

class FastAPILogger:
    """FastAPI를 위한 확장 가능한 로깅 클래스"""
    
    _context_var = ContextVar[RequestContext]('request_context', default=RequestContext())
    
    def __init__(self, name: str = None, log_dir: str = "var/logs"):
        self.name = name or __name__
        self.log_dir = Path(log_dir)
        self.logger = self._configure_logger()

    def _configure_logger(self) -> logging.Logger:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            # 기본 로그 파일
            file_handler = TimedRotatingFileHandler(
                filename=self.log_dir / "app.log",
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8"
            )
            file_handler.setFormatter(self.get_formatter())
            file_handler.setLevel(logging.INFO)
            
            # JSON 로그 파일 (Filebeat용)
            json_handler = TimedRotatingFileHandler(
                filename=self.log_dir / "app.json.log",
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8"
            )
            json_handler.setFormatter(JsonFormatter())
            json_handler.setLevel(logging.INFO)
            
            logger.addHandler(file_handler)
            logger.addHandler(json_handler)

        return logger

    def get_formatter(self):
        return logging.Formatter(
            '%(asctime)s - %(levelname)s - '
            '[REQ:%(request_id)s][USER:%(user_id)s] - '
            '%(name)s - %(message)s'
        )

    def set_context(self, **kwargs):
        context = RequestContext(**kwargs)
        self._context_var.set(context)

    def _get_log_args(self, message: str, *args, **kwargs):
        extra = kwargs.pop('extra', {})
        context = self._context_var.get()
        extra.update(context.as_dict())
        return message, args, extra, kwargs

    async def info(self, message: str, *args, **kwargs):
        message, args, extra, kwargs = self._get_log_args(message, *args, **kwargs)
        self.logger.info(message, *args, extra=extra, **kwargs)

    async def error(self, message: str, *args, **kwargs):
        message, args, extra, kwargs = self._get_log_args(message, *args, **kwargs)
        self.logger.error(message, *args, extra=extra, **kwargs)

    async def debug(self, message: str, *args, **kwargs):
        message, args, extra, kwargs = self._get_log_args(message, *args, **kwargs)
        self.logger.debug(message, *args, extra=extra, **kwargs)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'request_id': getattr(record, 'request_id', '-'),
            'user_id': getattr(record, 'user_id', '-')
        }
        # extra 데이터 추가
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        return json.dumps(log_data)

# 로거 인스턴스 생성
logger = FastAPILogger()