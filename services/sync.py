
# -*- coding: utf-8 -*-
"""
Serviço de sincronização automática - COM MAPEAMENTO INTELIGENTE
"""
import time
import requests
from typing import Dict, Optional, Any
from datetime import datetime
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
        self.jira_project_key = config.get('JIRA_PROJECT_KEY', 'LOGBEE')
        self.dry_run = True
        
        self._validate_config()
        self._test_connections()
    
    def _validate_config(self):
        """Valida configuração"""
        required = ['FRESHDESK_TO_JIRA_TRANSITIONS', 'JIRA_PROJECT_KEY']
        for key in required:
            if key not in self.config:
                raise ValueError(f"Configuração inválida: {key} não encontrado")
        
        transitions = self.config.get('FRESHDESK_TO_JIRA_TRANSITIONS', {})
        if not transitions:
            raise ValueError("Nenhuma transição configurada")
        
        logger.info(f"✅ Configuração validada - {len(transitions)} transições")
        logger.info(f"🎯 Projeto Jira: {self.jira_project_key}")
    
    def _test_connections(self):
        """Testa conexões"""
        logger.info("🔌 Testando conexões...")
        
        if not self.freshdesk.test_connection():
            raise ConnectionError("Falha na conexão Freshdesk")
        logger.info("✅ Conexão Freshdesk OK")
        
        if not self.jira.test_connection():
            raise ConnectionError("Falha na conexão Jira")
        logger.info("✅ Conexão Jira OK")
    
    def set_dry_run(self, dry_run: bool):
        """Define modo de execução"""
        self.dry_run = dry_run
        mode = "🧪 SIMULAÇÃO" if dry_run else "🚀 EXECUÇÃO REAL"
        logger.info(f"🎯 Modo definido: {mode}")
    
    def find_corresponding_jira_issue(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """Encontra issue Jira correspondente usando múltiplas estratégias"""
        logger.info(f"🔍 Buscando issue Jira para ticket #{ticket_id}")
        
        # ESTRATÉGIA 1: Buscar por padrão [FD-X] (para tickets 6, 7, 8)
        try:
            jql = f'project = {self.jira_project_key} AND summary ~ "[FD-{ticket_id}]"'
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
                    issue = issues[0]
                    logger.info(f"✅ Encontrado por padrão [FD-{ticket_id}]: {issue['key']}")
                    return issue
        except Exception as e:
            logger.error(f"❌ Erro na busca por padrão: {e}")
        
        # ESTRATÉGIA 2: Buscar por data de criação (para tickets novos)
        try:
            ticket_data = self.freshdesk.get_ticket_by_id(ticket_id)
            if ticket_data and ticket_data.get('created_at'):
                ticket_datetime = datetime.fromisoformat(ticket_data['created_at'].replace('Z', '+00:00'))
                search_date = ticket_datetime.strftime('%Y-%m-%d')
                
                logger.info(f"🗓️ Buscando issues do dia {search_date} para ticket #{ticket_id}")
                
                # Buscar todas as issues criadas no mesmo dia
                jql = f'project = {self.jira_project_key} AND created >= "{search_date}" AND created <= "{search_date} 23:59" ORDER BY created DESC'
                response = requests.get(
                    f'{self.jira.base_url}/rest/api/3/search',
                    headers=self.jira.headers,
                    auth=self.jira.auth,
                    params={'jql': jql, 'maxResults': 20},
                    timeout=10
                )
                
                if response.status_code == 200:
                    issues = response.json().get('issues', [])
                    logger.info(f"📋 Encontradas {len(issues)} issues no dia {search_date}")
                    
                    # Filtrar issues que NÃO têm padrão [FD-X] (são issues "novas")
                    new_issues = []
                    for issue in issues:
                        summary = issue['fields']['summary']
                        if '[FD-' not in summary:
                            new_issues.append(issue)
                            logger.info(f"   📄 Issue sem padrão FD: {issue['key']} - {summary}")
                    
                    if new_issues:
                        # Por agora, mapear para a mais recente
                        issue = new_issues[0]
                        logger.info(f"✅ Mapeado por data: #{ticket_id} → {issue['key']}")
                        return issue
                    else:
                        logger.warning(f"⚠️ Nenhuma issue nova encontrada no dia {search_date}")
                else:
                    logger.error(f"❌ Erro na busca por data: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Erro na busca por data: {e}")
        
        # ESTRATÉGIA 3: Buscar por título genérico
        try:
            logger.info(f"🔍 Buscando por título genérico...")
            jql = f'project = {self.jira_project_key} AND summary ~ "Ticket criado" AND summary !~ "[FD-" ORDER BY created DESC'
            response = requests.get(
                f'{self.jira.base_url}/rest/api/3/search',
                headers=self.jira.headers,
                auth=self.jira.auth,
                params={'jql': jql, 'maxResults': 10},
                timeout=10
            )
            
            if response.status_code == 200:
                issues = response.json().get('issues', [])
                if issues:
                    issue = issues[0]
                    logger.info(f"✅ Encontrado por título genérico: #{ticket_id} → {issue['key']}")
                    return issue
        except Exception as e:
            logger.error(f"❌ Erro na busca por título: {e}")
        
        logger.warning(f"❌ NENHUMA issue encontrada para ticket #{ticket_id}")
        return None
    
    def _should_sync_ticket(self, ticket_data: Dict) -> tuple[bool, str]:
        """Verifica se deve sincronizar"""
        freshdesk_status = ticket_data['status']
        transitions = self.config.get('FRESHDESK_TO_JIRA_TRANSITIONS', {})
        
        if freshdesk_status not in transitions:
            return False, f"Status {freshdesk_status} não configurado"
        
        return True, "OK para sincronizar"
    
    def _get_available_transitions(self, issue_key: str) -> Dict[str, str]:
        """Obtém transições disponíveis"""
        try:
            response = requests.get(
                f'{self.jira.base_url}/rest/api/3/issue/{issue_key}/transitions',
                headers=self.jira.headers,
                auth=self.jira.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                transitions_data = response.json().get('transitions', [])
                return {t['id']: t['name'] for t in transitions_data}
            return {}
        except Exception as e:
            logger.error(f"❌ Erro ao obter transições: {e}")
            return {}
    
    def sync_single_ticket(self, ticket_data: Dict) -> bool:
        """Sincroniza um ticket"""
        ticket_id = ticket_data['id']
        freshdesk_status = ticket_data['status']
        
        logger.info(f"🎫 Processando ticket #{ticket_id}")
        logger.info(f"📊 Status Freshdesk: {freshdesk_status}")
        
        should_sync, reason = self._should_sync_ticket(ticket_data)
        if not should_sync:
            logger.info(f"⏭️ PULANDO: {reason}")
            return True
        
        jira_issue = self.find_corresponding_jira_issue(ticket_id)
        if not jira_issue:
            logger.error(f"❌ Issue não encontrada para #{ticket_id}")
            return False
        
        issue_key = jira_issue['key']
        transitions = self.config.get('FRESHDESK_TO_JIRA_TRANSITIONS', {})
        target_transition = transitions[freshdesk_status]
        
        logger.info(f"🎯 Transição: {target_transition} para {issue_key}")
        
        if self.dry_run:
            logger.info(f"🧪 [DRY RUN] Simularia transição '{target_transition}'")
            return True
        else:
            success = self.jira.transition_issue(issue_key, target_transition)
            if success:
                logger.info(f"✅ SUCESSO! {issue_key} sincronizada")
            else:
                logger.error(f"❌ FALHA na transição de {issue_key}")
            return success
    
    def sync_all_tickets(self, hours_back: int = 24) -> Dict[str, int]:
        """Sincroniza todos os tickets"""
        logger.info(f"🚀 Sincronização - últimas {hours_back}h")
        
        try:
            tickets = self.freshdesk.get_tickets(updated_since_hours=hours_back)
        except Exception as e:
            logger.error(f"❌ Erro ao buscar tickets: {e}")
            return {"success": 0, "failed": 0, "skipped": 0}
        
        if not tickets:
            logger.info("⚠️ Nenhum ticket encontrado")
            return {"success": 0, "failed": 0, "skipped": 0}
        
        logger.info(f"📋 Processando {len(tickets)} tickets")
        
        stats = {"success": 0, "failed": 0, "skipped": 0}
        delay = self.config.get('RATE_LIMIT_DELAY', 1.0)
        
        for i, ticket in enumerate(tickets, 1):
            logger.info(f"\n[{i}/{len(tickets)}] Ticket #{ticket['id']}")
            
            try:
                success = self.sync_single_ticket(ticket)
                if success:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                logger.error(f"❌ Erro: {e}")
                stats["failed"] += 1
            
            if i < len(tickets):
                time.sleep(delay)
        
        logger.info(f"\n🏁 Concluído! {stats}")
        return stats
    
    def test_mapping(self, ticket_ids: list = None) -> Dict[str, Any]:
        """Testa mapeamento"""
        if ticket_ids is None:
            try:
                tickets = self.freshdesk.get_tickets(updated_since_hours=48)
                ticket_ids = [t['id'] for t in tickets[:5]]
            except:
                return {}
        
        logger.info(f"🧪 Testando mapeamento: {ticket_ids}")
        
        results = {}
        for ticket_id in ticket_ids:
            jira_issue = self.find_corresponding_jira_issue(ticket_id)
            if jira_issue:
                results[ticket_id] = {
                    'success': True,
                    'jira_key': jira_issue['key'],
                    'jira_summary': jira_issue['fields']['summary']
                }
            else:
                results[ticket_id] = {'success': False, 'error': 'Não encontrada'}
        
        return results
