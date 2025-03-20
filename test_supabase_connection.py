#!/usr/bin/env python
"""
Script de diagnóstico para testar a conexão com o Supabase
"""
import os
import sys
import requests
import json
from datetime import datetime

# Imprimir informações do sistema
print("==== Informações de sistema ====")
print(f"Python versão: {sys.version}")
print(f"Requests versão: {requests.__version__}")
print("===============================")

# Obter configurações do Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

print("\n==== Configurações do Supabase ====")
print(f"SUPABASE_URL: {SUPABASE_URL or 'Não definido'}")
print(f"SUPABASE_KEY: {'Definido (primeiros 10 caracteres: ' + SUPABASE_KEY[:10] + '...)' if SUPABASE_KEY else 'Não definido'}")
print(f"SUPABASE_SERVICE_KEY: {'Definido (primeiros 10 caracteres: ' + SUPABASE_SERVICE_KEY[:10] + '...)' if SUPABASE_SERVICE_KEY else 'Não definido'}")
print("===================================")

# Se alguma configuração estiver faltando, tentar ler do arquivo .env
if not (SUPABASE_URL and SUPABASE_KEY and SUPABASE_SERVICE_KEY):
    print("\nTentando carregar configurações do arquivo .env...")
    try:
        with open('.env', 'r') as env_file:
            for line in env_file:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    if key == 'SUPABASE_URL':
                        SUPABASE_URL = value
                    elif key == 'SUPABASE_KEY':
                        SUPABASE_KEY = value
                    elif key == 'SUPABASE_SERVICE_KEY':
                        SUPABASE_SERVICE_KEY = value
        
        print("Configurações atualizadas após leitura do .env:")
        print(f"SUPABASE_URL: {SUPABASE_URL or 'Não definido'}")
        print(f"SUPABASE_KEY: {'Definido (primeiros 10 caracteres: ' + SUPABASE_KEY[:10] + '...)' if SUPABASE_KEY else 'Não definido'}")
        print(f"SUPABASE_SERVICE_KEY: {'Definido (primeiros 10 caracteres: ' + SUPABASE_SERVICE_KEY[:10] + '...)' if SUPABASE_SERVICE_KEY else 'Não definido'}")
    except Exception as e:
        print(f"Erro ao ler arquivo .env: {str(e)}")

# Verificar se temos as configurações necessárias
if not (SUPABASE_URL and SUPABASE_KEY and SUPABASE_SERVICE_KEY):
    print("\nERRO: Configurações do Supabase incompletas. Não é possível continuar.")
    sys.exit(1)

# Testar conexão com o Supabase
print("\n==== Testando conexão com o Supabase ====")

# Testar API anônima (público)
try:
    print("Testando API anônima (pública)...")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=headers)
    
    if response.status_code == 200:
        print("✅ Conexão anônima bem-sucedida!")
    else:
        print(f"❌ Erro na conexão anônima. Status code: {response.status_code}")
        print(f"Resposta: {response.text}")
except Exception as e:
    print(f"❌ Erro ao testar conexão anônima: {str(e)}")

# Testar API de serviço (admin)
try:
    print("\nTestando API de serviço (admin)...")
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=headers)
    
    if response.status_code == 200:
        print("✅ Conexão de serviço bem-sucedida!")
        
        # Listar tabelas
        print("\nListando tabelas disponíveis:")
        try:
            tables_response = requests.get(
                f"{SUPABASE_URL}/rest/v1/",
                headers=headers
            )
            tables = tables_response.json()
            if tables:
                for table in tables:
                    print(f"- {table}")
            else:
                print("Nenhuma tabela encontrada.")
        except Exception as table_error:
            print(f"Erro ao listar tabelas: {str(table_error)}")
    else:
        print(f"❌ Erro na conexão de serviço. Status code: {response.status_code}")
        print(f"Resposta: {response.text}")
except Exception as e:
    print(f"❌ Erro ao testar conexão de serviço: {str(e)}")

print("\n==== Teste concluído ====") 