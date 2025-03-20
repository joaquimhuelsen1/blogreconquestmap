#!/usr/bin/env python3
"""
Script simplificado para configurar o Supabase usando a biblioteca oficial
"""
import os
import sys
from supabase import create_client, Client
import requests
import json
from datetime import datetime

# Cores para melhorar legibilidade
VERDE = "\033[92m"
AMARELO = "\033[93m"
VERMELHO = "\033[91m"
RESET = "\033[0m"

# Configuração do Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")  # Chave anônima
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")  # Chave de serviço

def verificar_configuracao():
    """Verifica se as variáveis de ambiente estão configuradas."""
    if not SUPABASE_URL or not SUPABASE_KEY or not SUPABASE_SERVICE_KEY:
        print(f"{VERMELHO}Erro: Configurações do Supabase não encontradas.{RESET}")
        print("\nPor favor, configure as seguintes variáveis de ambiente:")
        print("  SUPABASE_URL - URL do seu projeto Supabase")
        print("  SUPABASE_KEY - Chave anônima (public) do seu projeto")
        print("  SUPABASE_SERVICE_KEY - Chave de serviço (secreta) do seu projeto")
        return False
    return True

def executar_sql(sql):
    """Executa SQL diretamente no Supabase usando a API REST."""
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    # A API SQL usa o caminho /rest/v1/
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/",
        headers=headers,
        data=json.dumps({"query": sql})
    )
    
    if response.status_code in [200, 201, 204]:
        return True
    else:
        print(f"{VERMELHO}Erro ao executar SQL: {response.status_code} - {response.text}{RESET}")
        return False

def main():
    print(f"{VERDE}=== CONFIGURAÇÃO DO SUPABASE PARA O BLOG ==={RESET}")
    
    if not verificar_configuracao():
        return 1
    
    try:
        print(f"\n{VERDE}Conectando ao Supabase: {SUPABASE_URL}{RESET}")
        
        # Inicializa o cliente Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Criando tabelas diretamente no Dashboard do Supabase
        print(f"{AMARELO}Para criar tabelas, siga estas instruções:{RESET}")
        print("1. Acesse o Dashboard do Supabase: https://supabase.com/dashboard")
        print("2. Selecione seu projeto")
        print("3. Vá para SQL Editor")
        print("4. Execute o seguinte SQL:\n")
        
        # SQL completo para criar as tabelas
        sql_criar_tabelas = """
-- Tabela de usuários
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    age INTEGER,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_premium BOOLEAN NOT NULL DEFAULT FALSE,
    ai_credits INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de posts
CREATE TABLE IF NOT EXISTS public.posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    summary VARCHAR(200),
    image_url VARCHAR(255) DEFAULT 'https://via.placeholder.com/1200x400',
    premium_only BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
);

-- Tabela de comentários
CREATE TABLE IF NOT EXISTS public.comments (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved BOOLEAN NOT NULL DEFAULT FALSE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE
);

-- Trigger para atualizar o updated_at dos posts
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS posts_updated_at ON posts;
CREATE TRIGGER posts_updated_at
BEFORE UPDATE ON posts
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();
        """
        
        print(sql_criar_tabelas)
        print("\n5. Depois de criar as tabelas, volte para executar este script novamente")
        
        # Verificar se as tabelas já existem
        print(f"\n{AMARELO}Verificando se as tabelas já existem...{RESET}")
        
        try:
            # Tentar obter um registro da tabela de usuários
            response = supabase.table("users").select("id").limit(1).execute()
            print(f"{VERDE}  ✅ As tabelas já existem, continuando com a inserção de dados...{RESET}")
            
            # Inserindo usuário admin inicial
            print(f"{AMARELO}Criando usuário admin...{RESET}")
            
            # Verificar se o usuário admin já existe
            response = supabase.table("users").select("id").eq("username", "admin").execute()
            if response.data:
                print(f"  O usuário 'admin' já existe, pulando...")
                admin_id = response.data[0]["id"]
            else:
                # Dados do usuário admin
                admin_user = {
                    "username": "admin",
                    "email": "admin@exemplo.com",
                    "password_hash": "pbkdf2:sha256:150000$lQQxzRWx$2db7b9d72c262466810eda3ecdee83a2d61c18ac693c7d19eb3ab528f4a7b3b9",  # admin123
                    "is_admin": True,
                    "is_premium": True,
                    "age": 35,
                    "ai_credits": 5
                }
                
                # Inserir o usuário admin
                response = supabase.table("users").insert(admin_user).execute()
                print(f"{VERDE}  ✅ Usuário 'admin' criado com sucesso!{RESET}")
                admin_id = response.data[0]["id"]
            
            # Criar um post de exemplo
            print(f"{AMARELO}Criando post de exemplo...{RESET}")
            
            # Verificar se já existe o post de exemplo
            response = supabase.table("posts").select("id").eq("title", "Bem-vindo ao Blog").execute()
            if response.data:
                print(f"  O post 'Bem-vindo ao Blog' já existe, pulando...")
            else:
                post_exemplo = {
                    "title": "Bem-vindo ao Blog",
                    "content": "Este é o primeiro post do blog usando Supabase como banco de dados.",
                    "summary": "Post de boas-vindas ao blog",
                    "premium_only": False,
                    "user_id": admin_id
                }
                
                response = supabase.table("posts").insert(post_exemplo).execute()
                print(f"{VERDE}  ✅ Post de exemplo criado com sucesso!{RESET}")
            
        except Exception as e:
            print(f"{VERMELHO}  As tabelas ainda não existem ou ocorreu um erro: {str(e)}{RESET}")
            print("  Por favor, crie as tabelas manualmente no Dashboard do Supabase usando o SQL fornecido acima.")
            return 1
        
        print(f"\n{VERDE}=== CONFIGURAÇÃO CONCLUÍDA COM SUCESSO! ==={RESET}")
        print(f"\n{AMARELO}PRÓXIMOS PASSOS:{RESET}")
        print("1. Certifique-se de que sua aplicação esteja configurada com as credenciais do Supabase no arquivo .env")
        print("2. Use o arquivo supabase_models.py para interagir com o Supabase em sua aplicação")
        print("3. Adapte suas rotas e controllers para usar os novos modelos")
        
        return 0
        
    except Exception as e:
        print(f"{VERMELHO}Erro durante a configuração: {str(e)}{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 