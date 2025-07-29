# -*- coding: utf-8 -*-
"""
Configuração de logging
"""
import logging
import sys
from datetime import datetime

def get_logger(name: str = "sync") -> logging.Logger:
    """Configura e retorna logger"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Configurar handler
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger