# -*- coding: utf-8 -*-
"""
Serviço de sincronização automática - VERSÃO LIMPA
"""
import time
from typing import Dict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.freshdesk import FreshdeskClient
from providers.jira import JiraClient
from utils.logger import get_logger

logger = get_logger()

class SyncService:
    """Serviço de sincronização Freshdesk → Jira"""
    
    def __init__(self, freshdesk_client: FreshdeskClient, jira_client: JiraClient, config: Dict):
        self.freshdesk = freshdesk_client
        self.jira = jira_client
        self.config = config
        self.dry_run = True
    
    def set_dry_run(self, dry_run: bool):
        """Define se é execução real ou simulação"""
        self.dry_run = dry_run
    
    def ticket_to_issue_key(self, ticket_id: int) -> str:
        """Converte ID do ticket para chave da issue"""
        prefix = self.config.get('TICKET_TO_ISSUE_PREFIX', 'PROJ-')
        return f"{prefix}{ticket_id}"
    
    def sync_single_ticket(self, ticket_data: Dict) -> bool:
        """Sincroniza um ticket específico"""
        ticket_id = ticket_data['id']
        freshdesk_status = ticket_data['status']
        ticket_subject = ticket_data.get('subject', 'Sem título')
        
        logger.info(f"Processando ticket {ticket_id}: {ticket_subject}")
        
        # Verificar se status precisa sincronização
        transitions = self.config.get('FRESHDESK_TO_JIRA_TRANSITIONS', {})
        if freshdesk_status not in transitions:
            logger.info(f"Status {freshdesk_status} não requer sincronização")
            return True
        
        # Buscar issue correspondente
        issue_key = self.ticket_to_issue_key(ticket_id)
        jira_issue = self.jira.get_issue(issue_key)
        
        if not jira_issue:
            logger.error(f"Issue {issue_key} não encontrada no Jira")
            return False
        
        # Verificar se já está no status correto
        current_status_id = jira_issue['fields']['status']['id']
        target_transition = transitions[freshdesk_status]
        
        # Executar transição
        if self.dry_run:
            logger.info(f"[DRY RUN] Simularia transição {target_transition} para {issue_key}")
            return True
        else:
            success = self.jira.transition_issue(issue_key, target_transition)
            if success:
                logger.info(f"✅ Sucesso! {issue_key} sincronizada")
            else:
                logger.error(f"❌ Falha na transição de {issue_key}")
            return success
    
    def sync_all_tickets(self, hours_back: int = 24) -> Dict[str, int]:
        """Sincroniza todos os tickets recentes"""
        logger.info(f"Iniciando sincronização - últimas {hours_back}h")
        
        # Buscar tickets
        tickets = self.freshdesk.get_tickets(hours_back)
        if not tickets:
            return {"success": 0, "failed": 0, "skipped": 0}
        
        # Processar tickets
        stats = {"success": 0, "failed": 0, "skipped": 0}
        delay = self.config.get('RATE_LIMIT_DELAY', 1.0)
        
        for i, ticket in enumerate(tickets, 1):
            logger.info(f"[{i}/{len(tickets)}] Processando...")
            
            try:
                success = self.sync_single_ticket(ticket)
                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                logger.error(f"Erro no processamento: {e}")
                stats["failed"] += 1
            
            time.sleep(delay)
        
        logger.info(f"Sincronização concluída: {stats}")
        return stats