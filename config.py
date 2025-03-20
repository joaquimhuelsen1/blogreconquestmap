import os
from dotenv import load_dotenv
from datetime import timedelta

# Carrega variáveis de ambiente do arquivo .env, se existir
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Configurações básicas
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'uma-chave-secreta-dificil-de-adivinhar'
    
    # Caminho absoluto para o arquivo do banco de dados
    INSTANCE_PATH = os.path.join(basedir, 'instance')
    if not os.path.exists(INSTANCE_PATH):
        os.makedirs(INSTANCE_PATH)
    
    # Configuração do banco de dados - Priorizar DATABASE_URL
    # Usar DATABASE_URL diretamente se estiver disponível (prioridade)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        # Correção para URLs do Railway: substituir postgres:// por postgresql://
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
            print("URL de banco de dados corrigida: postgres:// -> postgresql://")
        
        # Corrigir URL do Supabase para usar o host correto do pooler
        # Qualquer host que termina com supabase.co é substituído pelo valor correto
        if '.supabase.co' in DATABASE_URL and 'pooler.supabase.com' not in DATABASE_URL:
            # Extrair user, password e o resto da URL
            import re
            match = re.match(r'postgresql://([^:]+):([^@]+)@[^/]+/([^?]+)(.*)', DATABASE_URL)
            if match:
                user, password, dbname, params = match.groups()
                # Reconstruir a URL com o host correto do pooler
                DATABASE_URL = f"postgresql://{user}:{password}@aws-0-us-west-1.pooler.supabase.com:5432/{dbname}{params}"
                print("URL do Supabase corrigida para usar o host correto do pooler")
            
        # Adicionar SSL mode se necessário
        if '?' not in DATABASE_URL:
            DATABASE_URL += '?sslmode=require'
        elif 'sslmode=' not in DATABASE_URL:
            DATABASE_URL += '&sslmode=require'
            
        # Usar a URL de conexão diretamente
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        print(f"Usando string de conexão do DATABASE_URL: {DATABASE_URL.split('@')[0]}@****")
    else:
        # Fallback para as variáveis separadas do Supabase
        SUPABASE_DB_USER = os.environ.get('SUPABASE_DB_USER')
        SUPABASE_DB_PASSWORD = os.environ.get('SUPABASE_DB_PASSWORD')
        SUPABASE_DB_HOST = os.environ.get('SUPABASE_DB_HOST', 'aws-0-us-west-1.pooler.supabase.com')
        SUPABASE_DB_PORT = os.environ.get('SUPABASE_DB_PORT', '5432')
        SUPABASE_DB_NAME = os.environ.get('SUPABASE_DB_NAME')
        
        # Forçar o host correto independentemente do que estiver configurado
        SUPABASE_DB_HOST = 'aws-0-us-west-1.pooler.supabase.com'
        print("Host do Supabase configurado para usar o pooler correto")
        
        POSTGRES_CONFIGURED = all([
            SUPABASE_DB_USER, 
            SUPABASE_DB_PASSWORD, 
            SUPABASE_DB_NAME
        ])
        
        if POSTGRES_CONFIGURED:
            # Formar a URL de conexão com o PostgreSQL
            SQLALCHEMY_DATABASE_URI = f'postgresql://{SUPABASE_DB_USER}:{SUPABASE_DB_PASSWORD}@{SUPABASE_DB_HOST}:{SUPABASE_DB_PORT}/{SUPABASE_DB_NAME}?sslmode=require'
            print(f"Usando conexão PostgreSQL via variáveis separadas: {SQLALCHEMY_DATABASE_URI.split('@')[0]}@****")
        else:
            # Fallback para SQLite
            print("AVISO: Usando SQLite como fallback. Configure DATABASE_URL para usar PostgreSQL.")
            SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(INSTANCE_PATH, 'blog.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Configurações da API OpenAI
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_ASSISTANT_ID = os.environ.get('OPENAI_ASSISTANT_ID')
    
    # Configurações de Email (para implementação futura)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['seu-email@exemplo.com']
    
    # Configurações de Debug
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = False 