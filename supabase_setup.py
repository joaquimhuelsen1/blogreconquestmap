#!/usr/bin/env python
"""
Script para configurar o Supabase com as tabelas necessárias para o blog.
"""
import os
import sys
import requests
import json
from datetime import datetime

# Cores para melhorar legibilidade
VERDE = "\033[92m"
AMARELO = "\033[93m"
VERMELHO = "\033[91m"
RESET = "\033[0m"

# Configuração do Supabase - a ser preenchida pelo usuário
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

def verificar_configuracao():
    """Verifica se as variáveis de ambiente estão configuradas."""
    if not SUPABASE_URL or not SUPABASE_KEY or not SUPABASE_SERVICE_KEY:
        print(f"{VERMELHO}Erro: Configurações do Supabase não encontradas.{RESET}")
        print("\nPor favor, configure as seguintes variáveis de ambiente:")
        print("  SUPABASE_URL - URL do seu projeto Supabase")
        print("  SUPABASE_KEY - Chave anônima (public) do seu projeto")
        print("  SUPABASE_SERVICE_KEY - Chave de serviço (secreta) do seu projeto")
        print("\nVocê pode encontrar essas informações em:")
        print("  1. Acesse o Dashboard do Supabase")
        print("  2. Selecione seu projeto")
        print("  3. Vá para Settings > API")
        print("\nExemplo de configuração:")
        print("  export SUPABASE_URL='https://abcdefghijklm.supabase.co'")
        print("  export SUPABASE_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'")
        print("  export SUPABASE_SERVICE_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'")
        return False
    return True

def criar_tabelas():
    """Cria as tabelas necessárias no Supabase usando a API REST."""
    print(f"{AMARELO}Configurando banco de dados no Supabase...{RESET}")
    
    # Cabeçalhos para as requisições
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # SQL para criar as tabelas
    print("Criando tabelas...")
    sql = """
    -- Tabela de usuários
    CREATE TABLE IF NOT EXISTS users (
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
    CREATE TABLE IF NOT EXISTS posts (
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
    CREATE TABLE IF NOT EXISTS comments (
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
    
    CREATE TRIGGER posts_updated_at
    BEFORE UPDATE ON posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
    
    -- Configuração de RLS (Row Level Security)
    ALTER TABLE users ENABLE ROW LEVEL SECURITY;
    ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
    ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
    
    -- Política para usuários
    CREATE POLICY users_select_policy ON users
    FOR SELECT USING (true);  -- Qualquer um pode ver informações básicas dos usuários
    
    CREATE POLICY users_insert_policy ON users
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);  -- Apenas usuários autenticados podem criar usuários
    
    CREATE POLICY users_update_policy ON users
    FOR UPDATE USING (auth.uid()::text = id::text OR EXISTS (
        SELECT 1 FROM users WHERE id = auth.uid() AND is_admin = true
    ));  -- Usuários podem editar seu próprio perfil, admins podem editar qualquer perfil
    
    -- Política para posts
    CREATE POLICY posts_select_public_policy ON posts
    FOR SELECT USING (premium_only = false OR EXISTS (
        SELECT 1 FROM users WHERE id = auth.uid() AND (is_premium = true OR is_admin = true)
    ));  -- Posts premium são visíveis apenas para usuários premium e admin
    
    CREATE POLICY posts_insert_policy ON posts
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);  -- Apenas usuários autenticados podem criar posts
    
    CREATE POLICY posts_update_policy ON posts
    FOR UPDATE USING (user_id = auth.uid() OR EXISTS (
        SELECT 1 FROM users WHERE id = auth.uid() AND is_admin = true
    ));  -- Autores podem editar seus próprios posts, admins podem editar qualquer post
    
    -- Política para comentários
    CREATE POLICY comments_select_policy ON comments
    FOR SELECT USING (approved = true OR user_id = auth.uid() OR EXISTS (
        SELECT 1 FROM users WHERE id = auth.uid() AND is_admin = true
    ));  -- Comentários aprovados são visíveis para todos, não aprovados apenas para o autor e admins
    
    CREATE POLICY comments_insert_policy ON comments
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);  -- Apenas usuários autenticados podem comentar
    
    CREATE POLICY comments_update_policy ON comments
    FOR UPDATE USING (user_id = auth.uid() OR EXISTS (
        SELECT 1 FROM users WHERE id = auth.uid() AND is_admin = true
    ));  -- Autores podem editar seus próprios comentários, admins podem editar qualquer comentário
    """
    
    try:
        # Executar o SQL
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/execute_sql",
            headers=headers,
            json={"sql": sql}
        )
        
        if response.status_code == 200:
            print(f"{VERDE}✅ Tabelas criadas com sucesso!{RESET}")
        else:
            print(f"{VERMELHO}❌ Erro ao criar tabelas: {response.status_code}{RESET}")
            print(response.text)
            return False
    except Exception as e:
        print(f"{VERMELHO}❌ Erro ao criar tabelas: {str(e)}{RESET}")
        return False
    
    return True

def criar_usuarios_iniciais():
    """Cria usuários iniciais no Supabase."""
    print(f"{AMARELO}Criando usuários iniciais...{RESET}")
    
    # Dados dos usuários iniciais
    admin_user = {
        "username": "admin",
        "email": "admin@exemplo.com",
        "password_hash": "pbkdf2:sha256:150000$lQQxzRWx$2db7b9d72c262466810eda3ecdee83a2d61c18ac693c7d19eb3ab528f4a7b3b9",  # admin123
        "is_admin": True,
        "is_premium": True,
        "age": 35,
        "ai_credits": 5
    }
    
    normal_user = {
        "username": "usuario",
        "email": "usuario@exemplo.com",
        "password_hash": "pbkdf2:sha256:150000$9XynAhAf$f7db3c29bbc1d302f0c373ec34f2b6092fced75a1c17c1f35d5c039e4be061b9",  # usuario123
        "is_admin": False,
        "is_premium": False,
        "age": 28,
        "ai_credits": 1
    }
    
    premium_user = {
        "username": "premium",
        "email": "premium@exemplo.com",
        "password_hash": "pbkdf2:sha256:150000$bCdYkPZX$f7db3c29bbc1d302f0c373ec34f2b6092fced75a1c17c1f35d5c039e4be061b9",  # premium123
        "is_admin": False,
        "is_premium": True,
        "age": 32,
        "ai_credits": 5
    }
    
    users = [admin_user, normal_user, premium_user]
    
    # Cabeçalhos para as requisições
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    for user in users:
        try:
            # Verificar se o usuário já existe
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/users?username=eq.{user['username']}",
                headers=headers
            )
            
            if response.status_code == 200 and response.json():
                print(f"  Usuário {user['username']} já existe, pulando...")
                continue
            
            # Inserir o usuário
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/users",
                headers=headers,
                json=user
            )
            
            if response.status_code in [200, 201]:
                print(f"  Usuário {user['username']} criado com sucesso!")
            else:
                print(f"{VERMELHO}❌ Erro ao criar usuário {user['username']}: {response.status_code}{RESET}")
                print(response.text)
        except Exception as e:
            print(f"{VERMELHO}❌ Erro ao criar usuário {user['username']}: {str(e)}{RESET}")
    
    return True

def criar_posts_exemplo():
    """Cria posts de exemplo no Supabase."""
    print(f"{AMARELO}Criando posts de exemplo...{RESET}")
    
    # Primeiro, precisamos pegar os IDs dos usuários
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Obter ID do admin
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?username=eq.admin",
            headers=headers
        )
        
        if response.status_code != 200 or not response.json():
            print(f"{VERMELHO}❌ Não foi possível encontrar o usuário admin{RESET}")
            return False
        
        admin_id = response.json()[0]["id"]
        
        # Obter ID do usuário premium
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?username=eq.premium",
            headers=headers
        )
        
        if response.status_code != 200 or not response.json():
            print(f"{VERMELHO}❌ Não foi possível encontrar o usuário premium{RESET}")
            return False
        
        premium_id = response.json()[0]["id"]
        
        # Posts de exemplo
        posts = [
            {
                "title": "Bem-vindo ao Blog da Reconquest Map",
                "content": "Este é o primeiro post do blog. Aqui compartilharemos informações sobre nosso projeto e atualizações importantes.",
                "summary": "Post de boas-vindas ao blog",
                "premium_only": False,
                "user_id": admin_id
            },
            {
                "title": "Conteúdo Premium: Estratégias Avançadas",
                "content": "Este é um conteúdo exclusivo para assinantes premium. Aqui discutiremos estratégias avançadas e dicas exclusivas.",
                "summary": "Conteúdo exclusivo para assinantes premium",
                "premium_only": True,
                "user_id": premium_id
            },
            {
                "title": "Novidades do Mês",
                "content": "Confira as novidades deste mês em nosso blog. Muitas atualizações e melhorias foram implementadas.",
                "summary": "Resumo das novidades do mês",
                "premium_only": False,
                "user_id": admin_id
            }
        ]
        
        for post in posts:
            # Verificar se o post já existe
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/posts?title=eq.{post['title']}",
                headers=headers
            )
            
            if response.status_code == 200 and response.json():
                print(f"  Post '{post['title']}' já existe, pulando...")
                continue
            
            # Inserir o post
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/posts",
                headers=headers,
                json=post
            )
            
            if response.status_code in [200, 201]:
                print(f"  Post '{post['title']}' criado com sucesso!")
            else:
                print(f"{VERMELHO}❌ Erro ao criar post '{post['title']}': {response.status_code}{RESET}")
                print(response.text)
        
        return True
    except Exception as e:
        print(f"{VERMELHO}❌ Erro ao criar posts de exemplo: {str(e)}{RESET}")
        return False

def criar_comentarios_exemplo():
    """Cria comentários de exemplo no Supabase."""
    print(f"{AMARELO}Criando comentários de exemplo...{RESET}")
    
    # Cabeçalhos para as requisições
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Obter IDs dos usuários
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers
        )
        
        if response.status_code != 200 or not response.json():
            print(f"{VERMELHO}❌ Não foi possível encontrar usuários{RESET}")
            return False
        
        users = response.json()
        user_ids = {user["username"]: user["id"] for user in users}
        
        # Obter IDs dos posts
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/posts",
            headers=headers
        )
        
        if response.status_code != 200 or not response.json():
            print(f"{VERMELHO}❌ Não foi possível encontrar posts{RESET}")
            return False
        
        posts = response.json()
        
        # Comentários de exemplo
        for post in posts:
            comments = [
                {
                    "content": f"Ótimo post sobre '{post['title']}'! Muito informativo.",
                    "approved": True,
                    "user_id": user_ids.get("usuario", users[0]["id"]),
                    "post_id": post["id"]
                },
                {
                    "content": f"Adorei o conteúdo de '{post['title']}'. Continuem com o bom trabalho!",
                    "approved": True,
                    "user_id": user_ids.get("premium", users[0]["id"]),
                    "post_id": post["id"]
                },
                {
                    "content": f"Este post '{post['title']}' poderia ter mais detalhes.",
                    "approved": False,  # Comentário não aprovado
                    "user_id": user_ids.get("usuario", users[0]["id"]),
                    "post_id": post["id"]
                }
            ]
            
            for comment in comments:
                # Inserir o comentário
                response = requests.post(
                    f"{SUPABASE_URL}/rest/v1/comments",
                    headers=headers,
                    json=comment
                )
                
                if response.status_code in [200, 201]:
                    status = "aprovado" if comment["approved"] else "não aprovado"
                    print(f"  Comentário {status} criado com sucesso para o post '{post['title']}'!")
                else:
                    print(f"{VERMELHO}❌ Erro ao criar comentário: {response.status_code}{RESET}")
                    print(response.text)
        
        return True
    except Exception as e:
        print(f"{VERMELHO}❌ Erro ao criar comentários de exemplo: {str(e)}{RESET}")
        return False

def main():
    print(f"{VERDE}=== CONFIGURAÇÃO DO SUPABASE PARA O BLOG RECONQUEST MAP ==={RESET}")
    
    if not verificar_configuracao():
        return 1
    
    print(f"\n{VERDE}Conectando ao Supabase: {SUPABASE_URL}{RESET}")
    
    # Criar as tabelas
    if not criar_tabelas():
        return 1
    
    # Criar usuários iniciais
    if not criar_usuarios_iniciais():
        return 1
    
    # Criar posts de exemplo
    if not criar_posts_exemplo():
        return 1
    
    # Criar comentários de exemplo
    if not criar_comentarios_exemplo():
        return 1
    
    print(f"\n{VERDE}=== CONFIGURAÇÃO CONCLUÍDA COM SUCESSO! ==={RESET}")
    print(f"\n{AMARELO}PRÓXIMOS PASSOS:{RESET}")
    print("1. Configure o arquivo .env com as credenciais do Supabase")
    print("2. Atualize o código da aplicação para usar o Supabase")
    print("3. Execute a aplicação")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 