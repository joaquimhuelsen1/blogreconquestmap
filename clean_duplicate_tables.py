#!/usr/bin/env python3
"""
Script para limpar tabelas duplicadas no banco de dados PostgreSQL
"""

from app import create_app, db
from sqlalchemy import text
import sys

def list_tables():
    """Lista todas as tabelas no banco de dados"""
    app = create_app()
    
    with app.app_context():
        # Verificar o dialeto do banco de dados
        dialect = db.engine.dialect.name
        print(f"Banco de dados atual: {dialect}")
        
        if dialect == 'postgresql':
            # Consulta para PostgreSQL
            query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """)
        elif dialect == 'sqlite':
            # Consulta para SQLite
            query = text("SELECT name FROM sqlite_master WHERE type='table';")
        else:
            print(f"Dialeto não suportado: {dialect}")
            return []
        
        result = db.session.execute(query)
        tables = [row[0] for row in result]
        
        # Imprimir tabelas existentes
        print("\nTabelas existentes:")
        for idx, table in enumerate(tables, 1):
            print(f"{idx}. {table}")
            
        return tables

def clean_duplicate_tables():
    """Limpa tabelas duplicadas (plural) mantendo as tabelas singulares"""
    app = create_app()
    
    with app.app_context():
        tables = list_tables()
        
        # Identificar pares singular/plural
        singular_tables = ['user', 'post', 'comment']
        plural_tables = ['users', 'posts', 'comments']
        duplicates = []
        
        for plural in plural_tables:
            if plural in tables:
                singular = plural[:-1]  # remover 's' para obter o singular
                if singular in tables:
                    duplicates.append((singular, plural))
        
        if not duplicates:
            print("\nNenhuma tabela duplicada encontrada.")
            return
        
        print("\nTabelas duplicadas encontradas:")
        for singular, plural in duplicates:
            print(f"- {singular} / {plural}")
        
        # Confirmar com o usuário
        confirm = input("\nDeseja excluir as tabelas no plural e manter apenas as singulares? (s/n): ")
        if confirm.lower() != 's':
            print("Operação cancelada.")
            return
        
        # Remover tabelas no plural
        for singular, plural in duplicates:
            try:
                print(f"Excluindo tabela '{plural}'...")
                db.session.execute(text(f"DROP TABLE IF EXISTS \"{plural}\";"))
                db.session.commit()
                print(f"✅ Tabela '{plural}' excluída com sucesso!")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro ao excluir tabela '{plural}': {str(e)}")
        
        print("\nTabelas atualizadas:")
        list_tables()

if __name__ == "__main__":
    print("=== Limpeza de Tabelas Duplicadas ===")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        # Apenas listar tabelas
        list_tables()
    else:
        # Limpar tabelas duplicadas
        clean_duplicate_tables() 