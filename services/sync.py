
import time
import requests
from typing import Dict, Optional, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.freshdesk import FreshdeskClient
from providers.jira import JiraClient
from utils.logger import get_logger

logger = get_logger()

class SyncService:
    """Serviço de sincronização Freshdesk → Jira MELHORADO"""
    
    def __init__(self, freshdesk_client: FreshdeskClient, jira_client: JiraClient, config: Dict):
        self.freshdesk = freshdesk_client
        self.jira = jira_client
        self.config = config
        self.dry_run = True
        
        # Campo customizado para armazenar referência cruzada
        self.cross_reference_field = config.get('CROSS_REFERENCE_FIELD', 'customfield_10001')  # Ajustar conforme seu Jira
    
    def set_dry_run(self, dry_run: bool):
        """Define se é execução real ou simulação"""
        self.dry_run = dry_run
    
    def find_jira_issue_by_freshdesk_id(self, freshdesk_ticket_id: int) -> Optional[str]:
        """
        Encontra issue do Jira usando ID do Freshdesk
        
        Estratégias de busca (em ordem de prioridade):
        1. Campo customizado com ID do Freshdesk
        2. Busca por summary/descrição contendo o ID
        3. Busca por tags/labels
        """
        
        # Estratégia 1: Campo customizado
        jql = f'project = "{self.config["JIRA_PROJECT_KEY"]}" AND "{self.cross_reference_field}" ~ "{freshdesk_ticket_id}"'
        
        try:
            response = requests.get(
                f'{self.jira.base_url}/rest/api/3/search',
                headers=self.jira.headers,
                auth=self.jira.auth,
                params={'jql': jql, 'maxResults': 1},
                timeout=10
            )
            
            if response.status_code == 200:
                issues = response.json().get('issues', [])
                if issues:
                    return issues[0]['key']
        except Exception as e:
            logger.warning(f"Erro na busca por campo customizado: {e}")
        
        # Estratégia 2: Busca por summary
        jql = f'project = "{self.config["JIRA_PROJECT_KEY"]}" AND summary ~ "#{freshdesk_ticket_id}"'
        
        try:
            response = requests.get(
                f'{self.jira.base_url}/rest/api/3/search',
                headers=self.jira.headers,
                auth=self.jira.auth,
                params={'jql': jql, 'maxResults': 1},
                timeout=10
            )
            
            if response.status_code == 200:
                issues = response.json().get('issues', [])
                if issues:
                    return issues[0]['key']
        except Exception as e:
            logger.warning(f"Erro na busca por summary: {e}")
        
        # Estratégia 3: Busca por labels/tags
        jql = f'project = "{self.config["JIRA_PROJECT_KEY"]}" AND labels = "freshdesk-{freshdesk_ticket_id}"'
        
        try:
            response = requests.get(
                f'{self.jira.base_url}/rest/api/3/search',
                headers=self.jira.headers,
                auth=self.jira.auth,
                params={'jql': jql, 'maxResults': 1},
                timeout=10
            )
            
            if response.status_code == 200:
                issues = response.json().get('issues', [])
                if issues:
                    return issues[0]['key']
        except Exception as e:
            logger.warning(f"Erro na busca por labels: {e}")
        
        return None
    
    def create_bidirectional_link(self, jira_issue_key: str, freshdesk_ticket_id: int) -> bool:
        """
        Cria link bidirecional entre Jira e Freshdesk
        """
        if self.dry_run:
            logger.info(f"[DRY RUN] Criaria link: {jira_issue_key} ↔ #{freshdesk_ticket_id}")
            return True
        
        try:
            # Atualizar campo no Jira com ID do Freshdesk
            update_data = {
                "fields": {
                    self.cross_reference_field: str(freshdesk_ticket_id)
                }
            }
            
            response = requests.put(
                f'{self.jira.base_url}/rest/api/3/issue/{jira_issue_key}',
                headers=self.jira.headers,
                auth=self.jira.auth,
                json=update_data,
                timeout=10
            )
            
            if response.status_code == 204:
                logger.info(f"✅ Link criado: {jira_issue_key} ↔ #{freshdesk_ticket_id}")
                return True
            else:
                logger.error(f"❌ Falha ao criar link: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar link: {e}")
            return False
    
    def sync_single_ticket(self, ticket_data: Dict) -> bool:
        """Sincroniza um ticket específico - VERSÃO MELHORADA"""
        ticket_id = ticket_data['id']
        freshdesk_status = ticket_data['status']
        ticket_subject = ticket_data.get('subject', 'Sem título')
        
        logger.info(f"Processando ticket #{ticket_id}: {ticket_subject}")
        
        # Verificar se status precisa sincronização
        transitions = self.config.get('FRESHDESK_TO_JIRA_TRANSITIONS', {})
        if freshdesk_status not in transitions:
            logger.info(f"Status {freshdesk_status} não requer sincronização")
            return True
        
        # NOVA ESTRATÉGIA: Buscar issue correspondente
        jira_issue_key = self.find_jira_issue_by_freshdesk_id(ticket_id)
        
        if not jira_issue_key:
            logger.error(f"❌ Issue correspondente ao ticket #{ticket_id} não encontrada no Jira")
            return False
        
        logger.info(f"✅ Issue encontrada: {jira_issue_key}")
        
        # Buscar detalhes da issue
        jira_issue = self.jira.get_issue(jira_issue_key)
        if not jira_issue:
            logger.error(f"❌ Erro ao buscar detalhes da issue {jira_issue_key}")
            return False
        
        # Verificar se já está no status correto
        current_status_id = jira_issue['fields']['status']['id']
        target_transition = transitions[freshdesk_status]
        
        logger.info(f"Status atual: {current_status_id}, Transição alvo: {target_transition}")
        
        # Executar transição
        if self.dry_run:
            logger.info(f"[DRY RUN] Simularia transição {target_transition} para {jira_issue_key}")
            return True
        else:
            success = self.jira.transition_issue(jira_issue_key, target_transition)
            if success:
                logger.info(f"✅ Sucesso! {jira_issue_key} sincronizada")
                # Criar/atualizar link bidirecional
                self.create_bidirectional_link(jira_issue_key, ticket_id)
            else:
                logger.error(f"❌ Falha na transição de {jira_issue_key}")
            return success
    
    def sync_all_tickets(self, hours_back: int = 24) -> Dict[str, int]:
        """Sincroniza todos os tickets recentes"""
        logger.info(f"Iniciando sincronização MELHORADA - últimas {hours_back}h")
        
        # Buscar tickets
        tickets = self.freshdesk.get_tickets(hours_back)
        if not tickets:
            return {"success": 0, "failed": 0, "skipped": 0, "not_found": 0}
        
        logger.info(f"Encontrados {len(tickets)} tickets para processar")
        
        # Processar tickets
        stats = {"success": 0, "failed": 0, "skipped": 0, "not_found": 0}
        delay = self.config.get('RATE_LIMIT_DELAY', 1.0)
        
        for i, ticket in enumerate(tickets, 1):
            logger.info(f"[{i}/{len(tickets)}] Processando ticket #{ticket['id']}...")
            
            try:
                success = self.sync_single_ticket(ticket)
                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                logger.error(f"Erro no processamento do ticket #{ticket['id']}: {e}")
                stats["failed"] += 1
            
            # Rate limiting
            if i < len(tickets):  # Não fazer delay no último
                time.sleep(delay)
        
        logger.info(f"Sincronização concluída: {stats}")
        return stats
    
    def get_sync_report(self, hours_back: int = 24) -> Dict:
        """Gera relatório de sincronização sem executar mudanças"""
        logger.info(f"Gerando relatório de sincronização - últimas {hours_back}h")
        
        tickets = self.freshdesk.get_tickets(hours_back)
        if not tickets:
            return {"total_tickets": 0, "mappings": [], "issues": []}
        
        report = {
            "total_tickets": len(tickets),
            "mappings": [],
            "issues": []
        }
        
        for ticket in tickets:
            ticket_id = ticket['id']
            jira_issue_key = self.find_jira_issue_by_freshdesk_id(ticket_id)
            
            mapping = {
                "freshdesk_id": ticket_id,
                "freshdesk_subject": ticket.get('subject', 'N/A'),
                "jira_key": jira_issue_key,
                "found": jira_issue_key is not None
            }
            
            if not jira_issue_key:
                report["issues"].append(f"Ticket #{ticket_id} não encontrado no Jira")
            
            report["mappings"].append(mapping)
        
        return report
