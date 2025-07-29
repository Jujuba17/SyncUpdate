#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SINCRONIZAÇÃO AUTOMÁTICA FRESHDESK → JIRA
Sistema Multi-Cliente
"""
import sys
import argparse
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from providers.freshdesk import FreshdeskClient
from providers.jira import JiraClient
from services.sync import SyncService
from settings import load_client_config
from utils.logger import get_logger

logger = get_logger()

def create_sync_service(client_name: str) -> SyncService:
    """Cria serviço de sincronização para cliente específico"""
    try:
        config = load_client_config(client_name)
        
        freshdesk_client = FreshdeskClient(
            config['FRESHDESK_DOMAIN'],
            config['FRESHDESK_API_KEY']
        )
        
        jira_client = JiraClient(
            config['JIRA_BASE_URL'],
            config['JIRA_EMAIL'],
            config['JIRA_API_TOKEN']
        )
        
        return SyncService(freshdesk_client, jira_client, config)
        
    except Exception as e:
        logger.error(f"Erro ao criar serviço para cliente {client_name}: {e}")
        sys.exit(1)

def test_connections(sync_service: SyncService) -> bool:
    """Testa conexões com as APIs"""
    logger.info("Testando conexões...")
    
    print("🧪 Testando Freshdesk...")
    if not sync_service.freshdesk.test_connection():
        print("❌ Falha na conexão com Freshdesk")
        return False
    print("✅ Freshdesk OK!")
    
    print("🧪 Testando Jira...")
    if not sync_service.jira.test_connection():
        print("❌ Falha na conexão com Jira")
        return False
    print("✅ Jira OK!")
    
    print("✅ Todas as conexões funcionando!")
    return True

def interactive_menu(client_name: str):
    """Menu interativo"""
    sync_service = create_sync_service(client_name)
    
    while True:
        print(f"\n🤖 SINCRONIZAÇÃO AUTOMÁTICA - Cliente: {client_name.upper()}")
        print("=" * 60)
        print("1. 🧪 Testar conexões")
        print("2. 🔍 Sincronizar (simulação)")
        print("3. 🚨 Sincronizar (execução real)")
        print("4. 📋 Ver configurações")
        print("5. ❌ Sair")
        
        choice = input("\nEscolha uma opção (1-5): ").strip()
        
        if choice == "1":
            test_connections(sync_service)
            
        elif choice == "2":
            hours = input("Horas atrás (padrão: 24): ").strip()
            hours = int(hours) if hours else 24
            
            print(f"\n🔍 MODO SIMULAÇÃO - Buscando tickets das últimas {hours}h")
            sync_service.set_dry_run(True)
            stats = sync_service.sync_all_tickets(hours)
            
            print(f"\n🎯 RESULTADO DA SIMULAÇÃO:")
            print(f"   ✅ Sucessos: {stats['success']}")
            print(f"   ❌ Falhas: {stats['failed']}")
            print(f"   📊 Total: {stats['success'] + stats['failed']}")
            
        elif choice == "3":
            print("\n🚨 MODO EXECUÇÃO REAL")
            print("⚠️  ATENÇÃO: Isso vai alterar issues no Jira DE VERDADE!")
            print("⚠️  As mudanças serão permanentes!")
            
            confirm = input("\nDigite 'SIM' (maiúsculo) para confirmar: ").strip()
            if confirm == "SIM":
                hours = input("Horas atrás (padrão: 24): ").strip()
                hours = int(hours) if hours else 24
                
                print(f"\n🚀 EXECUTANDO SINCRONIZAÇÃO REAL...")
                sync_service.set_dry_run(False)
                stats = sync_service.sync_all_tickets(hours)
                
                print(f"\n🎉 EXECUÇÃO CONCLUÍDA!")
                print(f"   ✅ Sucessos: {stats['success']}")
                print(f"   ❌ Falhas: {stats['failed']}")
                print(f"   📊 Total processado: {stats['success'] + stats['failed']}")
                
                if stats['success'] > 0:
                    config = sync_service.config
                    jira_url = config.get('JIRA_BASE_URL', '')
                    project_key = config.get('JIRA_PROJECT_KEY', '')
                    if jira_url and project_key:
                        print(f"\n🔗 Verificar no Jira: {jira_url}")
            else:
                print("❌ Execução cancelada pelo usuário")
                
        elif choice == "4":
            config = sync_service.config
            print(f"\n📋 CONFIGURAÇÕES - {client_name.upper()}")
            print("=" * 40)
            print(f"🔗 Freshdesk: {config.get('FRESHDESK_DOMAIN', 'N/A')}")
            print(f"🔗 Jira: {config.get('JIRA_BASE_URL', 'N/A')}")
            print(f"🎯 Projeto: {config.get('JIRA_PROJECT_KEY', 'N/A')}")
            print(f"⏰ Sync padrão: {config.get('DEFAULT_SYNC_HOURS', 24)}h")
            print(f"⏱️  Rate limit: {config.get('RATE_LIMIT_DELAY', 1)}s")
            
            print(f"\n📊 Mapeamento de Status:")
            transitions = config.get('FRESHDESK_TO_JIRA_TRANSITIONS', {})
            status_names = config.get('FRESHDESK_STATUS_NAMES', {})
            
            for freshdesk_id, jira_transition in transitions.items():
                freshdesk_name = status_names.get(freshdesk_id, f"Status {freshdesk_id}")
                print(f"   {freshdesk_id} ({freshdesk_name}) → Transição {jira_transition}")
            
        elif choice == "5":
            print("👋 Encerrando sincronizador...")
            break
            
        else:
            print("❌ Opção inválida! Escolha entre 1-5")
        
        input("\n⏳ Pressione Enter para continuar...")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Sistema de Sincronização Multi-Cliente")
    parser.add_argument(
        "client",
        help="Nome do cliente (ex: grupo_multi)",
        nargs="?"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas simular (não executar mudanças)"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Horas atrás para buscar tickets (padrão: 24)"
    )
    
    args = parser.parse_args()
    
    # Se não especificou cliente, perguntar
    if not args.client:
        print("🔧 SISTEMA DE SINCRONIZAÇÃO MULTI-CLIENTE")
        print("=" * 50)
        print("📁 Clientes disponíveis:")
        print("   • grupo_multi")
        print("   • (adicione mais em config/)")
        
        args.client = input("\n💭 Digite o nome do cliente: ").strip()
        if not args.client:
            print("❌ Nome do cliente é obrigatório!")
            sys.exit(1)
    
    # Verificar se é só o nome do cliente (modo interativo)
    if len(sys.argv) == 2 and sys.argv[1] == args.client:
        interactive_menu(args.client)
    else:
        # Execução automática via linha de comando
        print(f"🤖 Execução automática para cliente: {args.client}")
        
        sync_service = create_sync_service(args.client)
        
        if not test_connections(sync_service):
            print("❌ Falha nas conexões. Abortando.")
            sys.exit(1)
        
        sync_service.set_dry_run(args.dry_run)
        
        mode = "SIMULAÇÃO" if args.dry_run else "EXECUÇÃO REAL"
        print(f"\n🚀 {mode} - Últimas {args.hours}h")
        
        stats = sync_service.sync_all_tickets(args.hours)
        
        print(f"\n📊 RESULTADO FINAL:")
        print(f"   ✅ Sucessos: {stats['success']}")
        print(f"   ❌ Falhas: {stats['failed']}")
        print(f"   📈 Taxa de sucesso: {stats['success']/(stats['success']+stats['failed'])*100:.1f}%" if (stats['success']+stats['failed']) > 0 else "   📈 Nenhum ticket processado")

if __name__ == "__main__":
    main()