# -*- coding: utf-8 -*-
"""
Configurações globais do sistema
"""
import os
from typing import Dict, Any

def load_client_config(client_name: str) -> Dict[str, Any]:
    """Carrega configuração específica do cliente"""
    try:
        module = __import__(f"config.{client_name}", fromlist=[client_name])
        
        config = {}
        for attr in dir(module):
            if not attr.startswith('_'):
                config[attr] = getattr(module, attr)
        
        return config
    except ImportError:
        raise ValueError(f"Configuração para cliente '{client_name}' não encontrada")

def get_settings() -> Dict[str, Any]:
    """Retorna configurações do sistema"""
    return {
        'DEFAULT_HOURS_BACK': 24,
        'MAX_RETRIES': 3,
        'TIMEOUT': 30,
        'LOG_LEVEL': 'INFO'
    }