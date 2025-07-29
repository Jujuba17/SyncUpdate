# -*- coding: utf-8 -*-
"""
TEMPLATE de configuração para GRUPO_MULTI
Copie para grupo_multi.py e preencha com suas credenciais
"""
import os

# CREDENCIAIS FRESHDESK - SUBSTITUA PELOS SEUS VALORES
FRESHDESK_DOMAIN = "SEU_DOMINIO_FRESHDESK"  # Ex: "minhaempresa"
FRESHDESK_API_KEY = os.getenv('FRESHDESK_API_KEY', 'COLE_SUA_API_KEY_AQUI')

# CREDENCIAIS JIRA - SUBSTITUA PELOS SEUS VALORES  
JIRA_BASE_URL = "https://SEUDOMINIO.atlassian.net"  # Ex: "https://minhaempresa.atlassian.net"
JIRA_EMAIL = "SEU_EMAIL@EMPRESA.COM"
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', 'COLE_SEU_TOKEN_AQUI')
JIRA_PROJECT_KEY = "SEU_PROJETO"  # Ex: "PROJ"

# MAPEAMENTO DE STATUS (ajuste conforme seu workflow)
FRESHDESK_TO_JIRA_TRANSITIONS = {
    2: "11",   # Open → Primeiro status
    3: "31",   # Pending → Segundo status
    4: "41",   # Resolved → Terceiro status
    5: "41",   # Closed → Status final
    6: "21",   # Waiting on Customer → Em andamento
    7: "21",   # Waiting on Third Party → Em andamento
}

# CONFIGURAÇÕES GERAIS
DEFAULT_SYNC_HOURS = 2
TICKET_TO_ISSUE_PREFIX = f"{JIRA_PROJECT_KEY}-"
RATE_LIMIT_DELAY = 0.5

# Nomes dos status para logs (opcional)
FRESHDESK_STATUS_NAMES = {
    2: "Open",
    3: "Pending", 
    4: "Resolved",
    5: "Closed",
    6: "Waiting on Customer",
    7: "Waiting on Third Party"
}