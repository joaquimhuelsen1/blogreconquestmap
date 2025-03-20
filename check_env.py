#!/usr/bin/env python3
"""
Script para verificar as variáveis de ambiente do Supabase
"""

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Variáveis do Supabase
supabase_vars = {
    'SUPABASE_URL': os.environ.get('SUPABASE_URL'),
    'SUPABASE_KEY': os.environ.get('SUPABASE_KEY'),
    'SUPABASE_DB_USER': os.environ.get('SUPABASE_DB_USER'),
    'SUPABASE_DB_PASSWORD': os.environ.get('SUPABASE_DB_PASSWORD'),
    'SUPABASE_DB_HOST': os.environ.get('SUPABASE_DB_HOST'),
    'SUPABASE_DB_PORT': os.environ.get('SUPABASE_DB_PORT'),
    'SUPABASE_DB_NAME': os.environ.get('SUPABASE_DB_NAME'),
    'DATABASE_URL': os.environ.get('DATABASE_URL')
}

print("=== Verificação de Variáveis do Supabase ===")
all_configured = True

for key, value in supabase_vars.items():
    if value:
        # Ocultar senhas e chaves, mostrar apenas os primeiros 5 caracteres
        if 'PASSWORD' in key or 'KEY' in key:
            masked_value = value[:5] + '******'
            print(f"{key}: {masked_value}")
        else:
            print(f"{key}: {value}")
    else:
        print(f"{key}: NÃO CONFIGURADO")
        if key in ['SUPABASE_DB_USER', 'SUPABASE_DB_PASSWORD', 'SUPABASE_DB_HOST', 'SUPABASE_DB_NAME']:
            all_configured = False

print("\nStatus da Configuração:")
if all_configured:
    print("✅ Todas as variáveis necessárias estão configuradas!")
    
    # Criar string de conexão PostgreSQL para teste
    if not os.environ.get('DATABASE_URL'):
        conn_string = f"postgresql://{os.environ.get('SUPABASE_DB_USER')}:{os.environ.get('SUPABASE_DB_PASSWORD')}@{os.environ.get('SUPABASE_DB_HOST')}:{os.environ.get('SUPABASE_DB_PORT', '5432')}/{os.environ.get('SUPABASE_DB_NAME')}"
        print(f"\nString de conexão PostgreSQL: {conn_string[:10]}...**************...{conn_string[-10:]}")
else:
    print("❌ Algumas variáveis necessárias NÃO estão configuradas!")
    print("\nVerifique seu arquivo .env e certifique-se de que as variáveis estão configuradas corretamente.")
    print("Exemplo de configuração:")
    print("""
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-de-api-supabase
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=sua-senha-db
SUPABASE_DB_HOST=db.seu-projeto.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
    """) 