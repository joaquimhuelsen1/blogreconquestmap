#!/usr/bin/env python
"""
Script para inicializar o banco de dados via Python Runners no cPanel.
Este script instala as dependências necessárias antes de inicializar o banco.
"""
import os
import sys
import subprocess
import glob

# Configurando o ambiente
os.environ['FLASK_ENV'] = 'production'
print("Verificando estrutura do projeto...")

# Verifica a estrutura de diretórios
current_dir = os.getcwd()
print(f"Diretório atual: {current_dir}")

# Lista os diretórios
print("Estrutura de diretórios:")
for root, dirs, files in os.walk(".", topdown=True, maxdepth=2):
    for dir_name in dirs:
        print(f"- {os.path.join(root, dir_name)}")

# Verifica se a pasta app existe
if not os.path.exists('app'):
    print("Pasta 'app' não encontrada. Procurando em outro local...")
    # Procura por potenciais locais da pasta app
    app_dirs = glob.glob("*/app") + glob.glob("*/*/app")
    if app_dirs:
        parent_dir = os.path.dirname(app_dirs[0])
        print(f"Pasta app encontrada em: {app_dirs[0]}")
        os.chdir(parent_dir)
        print(f"Mudando para diretório: {os.getcwd()}")
    else:
        print("ERRO: Pasta 'app' não encontrada em nenhum lugar!")
        sys.exit(1)

# Verifica se app/models existe
if not os.path.exists('app/models'):
    print("ERRO: Pasta 'app/models' não encontrada!")
    sys.exit(1)

# Verifica se __init__.py existe nos diretórios necessários
for dir_path in ['app', 'app/models']:
    init_file = os.path.join(dir_path, '__init__.py')
    if not os.path.exists(init_file):
        print(f"Criando arquivo {init_file}")
        with open(init_file, 'w') as f:
            f.write("# Arquivo de inicialização para estrutura de pacotes Python\n")

print("Instalando dependências...")

# Lista de pacotes essenciais
packages = [
    'flask',
    'flask-sqlalchemy',
    'flask-login',
    'flask-migrate',
    'flask-wtf',
    'pymysql',
    'python-dotenv',
    'flask-session',
    'email_validator',
    'markdown',
    'openai'
]

# Instalar pacotes
for package in packages:
    print(f"Instalando {package}...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print(f"{package} instalado com sucesso.")
    except subprocess.CalledProcessError:
        print(f"Erro ao instalar {package}, tentando continuar...")

print("Dependências instaladas! Inicializando banco de dados...")

# Verifica se user.py existe em app/models
if not os.path.exists('app/models/user.py'):
    print("ERRO: Arquivo 'app/models/user.py' não encontrado!")
    sys.exit(1)

# Adiciona o diretório atual ao path do Python
sys.path.insert(0, os.getcwd())
print(f"Python path: {sys.path}")

# Agora executamos a inicialização do banco de dados
try:
    from app import create_app, db
    from app.models.user import User
    
    app = create_app()
    
    with app.app_context():
        # Criando tabelas
        db.create_all()
        
        # Verificando se já existe um administrador
        admin_user = User.query.filter_by(email='admin@exemplo.com').first()
        
        if not admin_user:
            # Criando usuários iniciais
            admin = User(
                username='admin',
                email='admin@exemplo.com',
                role='admin'
            )
            admin.set_password('senha123')
            
            premium = User(
                username='premium',
                email='premium@exemplo.com',
                role='premium'
            )
            premium.set_password('senha123')
            
            normal = User(
                username='normal',
                email='normal@exemplo.com',
                role='user'
            )
            normal.set_password('senha123')
            
            # Adicionando à sessão e commitando
            db.session.add(admin)
            db.session.add(premium)
            db.session.add(normal)
            db.session.commit()
            
            print("Usuários iniciais criados com sucesso!")
        else:
            print("Administrador já existe, pulando criação de usuários iniciais.")
            
    print("Banco de dados inicializado com sucesso!")
    
except Exception as e:
    print(f"Erro ao inicializar o banco de dados: {str(e)}")
    import traceback
    print(traceback.format_exc())
    sys.exit(1) 