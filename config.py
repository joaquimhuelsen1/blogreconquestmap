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
        
        # Corrigir URL do Supabase para usar postgres.* em vez de db.* (IPv4 compatibility)
        if 'db.mqyasfpbtcdrxccuhchv.supabase.co' in DATABASE_URL:
            DATABASE_URL = DATABASE_URL.replace('db.mqyasfpbtcdrxccuhchv.supabase.co', 
                                              'postgres.mqyasfpbtcdrxccuhchv.supabase.co')
            print("URL do Supabase corrigida: db.* -> postgres.* (compatibilidade IPv4)")
            
        # Usar a URL de conexão diretamente
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        print(f"Usando string de conexão do DATABASE_URL: {DATABASE_URL[:20]}...")
    else:
        # Fallback para as variáveis separadas do Supabase
        SUPABASE_DB_USER = os.environ.get('SUPABASE_DB_USER')
        SUPABASE_DB_PASSWORD = os.environ.get('SUPABASE_DB_PASSWORD')
        SUPABASE_DB_HOST = os.environ.get('SUPABASE_DB_HOST')
        SUPABASE_DB_PORT = os.environ.get('SUPABASE_DB_PORT', '5432')
        SUPABASE_DB_NAME = os.environ.get('SUPABASE_DB_NAME')
        
        # Corrigir host do Supabase para usar postgres.* em vez de db.* (IPv4 compatibility)
        if SUPABASE_DB_HOST and 'db.mqyasfpbtcdrxccuhchv.supabase.co' in SUPABASE_DB_HOST:
            SUPABASE_DB_HOST = SUPABASE_DB_HOST.replace('db.mqyasfpbtcdrxccuhchv.supabase.co', 
                                                      'postgres.mqyasfpbtcdrxccuhchv.supabase.co')
            print("Host do Supabase corrigido: db.* -> postgres.* (compatibilidade IPv4)")
        
        POSTGRES_CONFIGURED = all([
            SUPABASE_DB_USER, 
            SUPABASE_DB_PASSWORD, 
            SUPABASE_DB_HOST, 
            SUPABASE_DB_NAME
        ])
        
        if POSTGRES_CONFIGURED:
            # Formar a URL de conexão com o PostgreSQL
            SQLALCHEMY_DATABASE_URI = f'postgresql://{SUPABASE_DB_USER}:{SUPABASE_DB_PASSWORD}@{SUPABASE_DB_HOST}:{SUPABASE_DB_PORT}/{SUPABASE_DB_NAME}'
            print("Usando conexão PostgreSQL via variáveis separadas")
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