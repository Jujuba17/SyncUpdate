# -*- coding: utf-8 -*-
"""
Cliente para API do Jira
"""
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict, Optional

class JiraClient:
    """Cliente para acessar API do Jira"""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {"Content-Type": "application/json"}
    
    def test_connection(self) -> bool:
        """Testa conexão com Jira"""
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/myself",
                headers=self.headers,
                auth=self.auth,
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_issue(self, issue_key: str) -> Optional[Dict]:
        """Busca issue no Jira"""
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/issue/{issue_key}",
                headers=self.headers,
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception:
            return None
    
    def transition_issue(self, issue_key: str, transition_id: str) -> bool:
        """Executa transição de status"""
        try:
            data = {"transition": {"id": transition_id}}
            
            response = requests.post(
                f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions",
                headers=self.headers,
                auth=self.auth,
                json=data,
                timeout=10
            )
            
            return response.status_code == 204
            
        except Exception:
            return False