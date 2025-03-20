#!/usr/bin/env python3
"""
Script para criar um usuário administrador no banco de dados
"""

from app import create_app, db
from app.models import User
from datetime import datetime

def create_admin_user(username, email, password):
    """Cria um usuário com permissões de administrador"""
    
    app = create_app()
    
    with app.app_context():
        # Verificar se o usuário já existe
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if existing_user:
            if existing_user.username == username:
                print(f"ERRO: Usuário com nome '{username}' já existe!")
                return False
            else:
                print(f"ERRO: E-mail '{email}' já está em uso!")
                return False
        
        # Criar novo usuário administrador
        admin = User(
            username=username,
            email=email,
            is_admin=True,
            is_premium=True,
            ai_credits=10,
            created_at=datetime.utcnow()
        )
        admin.set_password(password)
        
        # Adicionar e salvar
        db.session.add(admin)
        db.session.commit()
        
        print(f"✅ Usuário administrador '{username}' criado com sucesso!")
        print("Detalhes do usuário:")
        print(f"Username: {admin.username}")
        print(f"Email: {admin.email}")
        print(f"Admin: {admin.is_admin}")
        print(f"Premium: {admin.is_premium}")
        print(f"AI Credits: {admin.ai_credits}")
        
        return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 4:
        username = sys.argv[1]
        email = sys.argv[2]
        password = sys.argv[3]
        create_admin_user(username, email, password)
    else:
        # Obter dados interativamente
        print("=== Criação de Usuário Administrador ===")
        username = input("Digite o nome de usuário: ")
        email = input("Digite o email: ")
        password = input("Digite a senha: ")
        
        create_admin_user(username, email, password) 