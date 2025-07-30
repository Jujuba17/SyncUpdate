
# -*- coding: utf-8 -*-
"""
TEMPLATE UNIVERSAL de configuração
Este arquivo deve ser copiado para cada cliente: grupo_SEK.py, grupo_multi.py, etc.
"""
import os

# =============================================================================
# CONFIGURAÇÕES QUE PRECISAM SER PERSONALIZADAS POR CLIENTE
# =============================================================================

# DOMÍNIO FRESHDESK (apenas o nome, sem .freshdesk.com)
FRESHDESK_DOMAIN = "jhuliane17"  # Ex: "minhaempresa"

# CONFIGURAÇÕES JIRA
JIRA_BASE_URL = "https://julianesilva.atlassian.net"
JIRA_EMAIL = "jhuliane17@gmail.com"
JIRA_PROJECT_KEY = "LOGBEE"                       # Ex: "SUP", "HELP", "TICKET"

# MAPEAMENTO DE STATUS (ajuste conforme workflow do Jira do cliente)
FRESHDESK_TO_JIRA_TRANSITIONS = {
    2: "11",   # Open → Primeiro status do workflow
    3: "31",   # Pending → Status em andamento
    4: "41",   # Resolved → Status resolvido
    5: "41",   # Closed → Status final
    6: "21",   # Waiting on Customer → Status aguardando
    7: "21",   # Waiting on Third Party → Status terceiros
}

# =============================================================================
# CREDENCIAIS DINÂMICAS (NÃO ALTERAR - PEGA DAS SECRETS DO GITHUB)
# =============================================================================

# Pega das secrets do GitHub Actions ou variáveis de ambiente
FRESHDESK_API_KEY = os.getenv('FRESHDESK_API_KEY')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

# Para desenvolvimento local, você pode usar:
# FRESHDESK_API_KEY = os.getenv('FRESHDESK_API_KEY', 'SUA_KEY_LOCAL_AQUI')
# JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', 'SEU_TOKEN_LOCAL_AQUI')

# Ou pegar secrets específicos por cliente (se preferir):
# FRESHDESK_API_KEY = os.getenv('FRESHDESK_API_KEY') or os.getenv('FRESHDESK_API_KEY_SEK')
# JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN') or os.getenv('JIRA_API_TOKEN_SEK')

# =============================================================================
# CONFIGURAÇÕES GERAIS (NORMALMENTE NÃO PRECISAM ALTERAR)
# =============================================================================

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

# =============================================================================
# VALIDAÇÕES (OPCIONAL - PARA DEBUG)
# =============================================================================

def validate_config():
    """Valida se a configuração está correta"""
    errors = []
    
    if not FRESHDESK_API_KEY:
        errors.append("FRESHDESK_API_KEY não encontrada nas variáveis de ambiente")
    
    if not JIRA_API_TOKEN:
        errors.append("JIRA_API_TOKEN não encontrada nas variáveis de ambiente")
        
    if "SUBSTITUA" in FRESHDESK_DOMAIN:
        errors.append("FRESHDESK_DOMAIN ainda está com valor do template")
        
    if "CLIENTE" in JIRA_BASE_URL:
        errors.append("JIRA_BASE_URL ainda está com valor do template")
        
    if "@DOMINIO.COM" in JIRA_EMAIL:
        errors.append("JIRA_EMAIL ainda está com valor do template")
    
    return errors

if __name__ == "__main__":
    # Teste a configuração
    print("=== Validando Configuração ===")
    errors = validate_config()
    
    if errors:
        print("❌ Erros encontrados:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuração válida!")
        print(f"Domain: {FRESHDESK_DOMAIN}")
        print(f"Jira: {JIRA_BASE_URL}")
        print(f"Project: {JIRA_PROJECT_KEY}")
