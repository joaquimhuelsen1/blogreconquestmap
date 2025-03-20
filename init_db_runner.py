#!/usr/bin/env python
"""
Script para inicializar o banco de dados via Python Runners no cPanel.
Este script instala as dependências necessárias antes de inicializar o banco.
"""
import os
import sys
import subprocess

# Configurando o ambiente
os.environ['FLASK_ENV'] = 'production'
print("Instalando dependências...")

# Lista de pacotes essenciais
packages = [
    'flask',
    'flask-sqlalchemy',
    'flask-login',
    'flask-migrate',
    'flask-wtf',
    'pymysql',
    'python-dotenv'
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
    sys.exit(1) 