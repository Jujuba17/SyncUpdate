# -*- coding: utf-8 -*-
"""
Cliente para API do Freshdesk
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class FreshdeskClient:
    """Cliente para acessar API do Freshdesk"""
    
    def __init__(self, domain: str, api_key: str):
        self.domain = domain
        self.api_key = api_key
        self.base_url = self._build_url(domain)
        
        self.session = requests.Session()
        self.session.auth = (api_key, 'X')
    
    def _build_url(self, domain: str) -> str:
        """Constrói URL base do Freshdesk"""
        # Remove protocolos e barras
        domain = domain.replace('https://', '').replace('http://', '').rstrip('/')
        
        if '.freshdesk.com' not in domain:
            domain = f"{domain}.freshdesk.com"
            
        return f"https://{domain}/api/v2"
    
    def test_connection(self) -> bool:
        """Testa conexão com Freshdesk"""
        try:
            response = self.session.get(
                f"{self.base_url}/tickets",
                params={'per_page': 1},
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_tickets(self, updated_since_hours: int = 24) -> List[Dict]:
        """Busca tickets atualizados"""
        try:
            since_time = (datetime.now() - timedelta(hours=updated_since_hours)).isoformat()
            
            response = self.session.get(
                f"{self.base_url}/tickets",
                params={
                    'updated_since': since_time,
                    'per_page': 100
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            return []
            
        except Exception:
            return []
    
    def get_ticket_by_id(self, ticket_id: int) -> Optional[Dict]:
        """Busca ticket específico por ID"""
        try:
            response = self.session.get(
                f"{self.base_url}/tickets/{ticket_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception:
            return None