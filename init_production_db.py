"""
Script para inicializar o banco de dados no ambiente de produção.
Este script deve ser executado apenas uma vez após a configuração inicial.
"""

import os
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_db():
    """Inicializa o banco de dados em produção."""
    print("Iniciando configuração do banco de dados em produção...")
    
    # Forçar a utilização das configurações de produção
    os.environ['FLASK_ENV'] = 'production'
    
    app = create_app()
    
    with app.app_context():
        # Criar todas as tabelas
        print("Criando tabelas do banco de dados...")
        db.create_all()
        
        # Verificar se já existe um usuário administrador
        admin = User.query.filter_by(username="admin").first()
        
        if not admin:
            print("Criando usuário administrador...")
            admin = User(
                username="admin",
                email="admin@exemplo.com",
                password_hash=generate_password_hash("adminsenha"),
                is_admin=True,
                is_premium=True,
                created_at=datetime.utcnow(),
                ai_credits=100
            )
            db.session.add(admin)
            
            # Criar usuário premium
            premium_user = User(
                username="premium",
                email="premium@exemplo.com",
                password_hash=generate_password_hash("premiumsenha"),
                is_admin=False,
                is_premium=True,
                created_at=datetime.utcnow(),
                ai_credits=50
            )
            db.session.add(premium_user)
            
            # Criar usuário normal
            normal_user = User(
                username="usuario",
                email="usuario@exemplo.com",
                password_hash=generate_password_hash("usuariosenha"),
                is_admin=False,
                is_premium=False,
                created_at=datetime.utcnow(),
                ai_credits=10
            )
            db.session.add(normal_user)
            
            # Commit das alterações
            db.session.commit()
            print("Usuários iniciais criados com sucesso!")
        else:
            print("Usuário administrador já existe. Pulando criação de usuários.")
        
        print("Configuração do banco de dados em produção concluída!")

if __name__ == "__main__":
    init_db() 