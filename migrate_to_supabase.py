#!/usr/bin/env python3
"""
Script para migrar dados de SQLite para PostgreSQL/Supabase
"""

import os
import sys
import time
import json
from flask import Flask
from app import create_app, db
from sqlalchemy import text
import pandas as pd

# Número de registros a serem processados por vez
BATCH_SIZE = 100

def backup_data(app):
    """Backup dos dados de SQLite antes da migração"""
    print("Realizando backup dos dados atuais...")
    
    with app.app_context():
        # Obter todas as tabelas do banco de dados
        tables = []
        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        for row in result:
            if not row[0].startswith('sqlite_') and not row[0].startswith('alembic_'):
                tables.append(row[0])
        
        # Criar diretório para backup se não existir
        backup_dir = 'backup_data'
        os.makedirs(backup_dir, exist_ok=True)
        
        # Salvar dados de cada tabela
        for table in tables:
            print(f"Fazendo backup da tabela: {table}")
            result = db.session.execute(text(f"SELECT * FROM {table};"))
            
            # Converter para DataFrame e salvar como CSV
            columns = result.keys()
            df = pd.DataFrame(result.fetchall(), columns=columns)
            df.to_csv(f"{backup_dir}/{table}.csv", index=False)
            
            # Também salvar como JSON para estruturas mais complexas
            df.to_json(f"{backup_dir}/{table}.json", orient='records')
    
    print(f"Backup concluído! Os dados foram salvos no diretório '{backup_dir}'")

def switch_to_postgres():
    """Configurar variáveis de ambiente para PostgreSQL/Supabase"""
    print("Configurando conexão com PostgreSQL/Supabase...")
    
    # Verificar se as variáveis do Supabase estão definidas
    required_vars = [
        'SUPABASE_DB_USER', 
        'SUPABASE_DB_PASSWORD', 
        'SUPABASE_DB_HOST', 
        'SUPABASE_DB_NAME'
    ]
    
    missing = [var for var in required_vars if not os.environ.get(var)]
    
    if missing:
        print("ERRO: As seguintes variáveis de ambiente são necessárias:")
        for var in missing:
            print(f"  - {var}")
        print("\nConfigurações não encontradas. Verifique o arquivo .env")
        return False
    
    print("Todas as variáveis necessárias estão configuradas.")
    return True

def run_migration():
    """Executa o processo de migração para PostgreSQL/Supabase"""
    
    # Configurar conexão
    if not switch_to_postgres():
        print("Abortando migração devido a configurações incompletas.")
        return
    
    # Criar a aplicação com as novas configurações
    app = create_app()
    
    # Fazer backup dos dados atuais
    backup_data(app)
    
    # Executar migração completa
    print("\nExecutando a migração para PostgreSQL/Supabase...")
    
    # Limpar o banco de dados PostgreSQL (opcional, mas pode ser necessário)
    # Cuidado: isso apaga todos os dados no PostgreSQL!
    if input("Deseja limpar o banco de dados PostgreSQL antes de migrar? (s/N): ").lower() == 's':
        with app.app_context():
            db.drop_all()
            print("Tabelas PostgreSQL apagadas.")
    
    # Executar comandos de migração
    print("\nMarcando a versão atual do banco de dados...")
    os.system("flask db stamp head")
    
    print("\nGerando migração para PostgreSQL...")
    os.system("flask db migrate -m 'Migração para PostgreSQL'")
    
    print("\nAplicando migrações...")
    os.system("flask db upgrade")
    
    print("\nMigração para PostgreSQL/Supabase concluída com sucesso!")
    print("\nObservação: Os dados foram exportados para o diretório 'backup_data'")
    print("Você pode importar os dados manualmente ou usar ferramentas como:")
    print(" - pgAdmin")
    print(" - psql (através da ferramenta psql ou equivalente)")
    print(" - sqlalchemy (criando um script de importação)")

if __name__ == "__main__":
    print("=== Migração de SQLite para PostgreSQL/Supabase ===")
    
    if input("Este script migrará seu banco de dados para PostgreSQL/Supabase. Continuar? (s/N): ").lower() != 's':
        print("Migração cancelada.")
        sys.exit(0)
    
    run_migration() 