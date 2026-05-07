import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

def setup_logger():
    """
    配置全局的 ultimateDESIGN logger。
    输出到控制台以及按大小轮转的文件中。
    """
    # 获取项目根目录 (假设该文件在 src/utils/ 下)
    project_root = Path(__file__).resolve().parents[2]
    log_dir = project_root / "logs"
    
    # 确保日志目录存在
    if not log_dir.exists():
        os.makedirs(log_dir, exist_ok=True)
        
    log_file = log_dir / "ultimateDESIGN.log"
    
    # 获取 root logger
    logger = logging.getLogger("ultimateDESIGN")
    
    # 防止重复添加 handler
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(logging.INFO)
    
    # 日志格式
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(module)s:%(funcName)s:%(lineno)d] %(message)s"
    )
    
    # 1. 配置文件输出 (RotatingFileHandler: 最大10MB, 保留5个备份)
    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 2. 配置控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
