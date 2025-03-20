"""
Este script executa a migração do banco de dados para adicionar o campo reading_time à tabela post.
"""
from app import create_app, db
from app.models import Post
import os
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Verificar se o campo reading_time já existe na tabela post
    column_exists = False
    try:
        # Verificar se a coluna existe no esquema de banco de dados
        if 'postgres' in os.environ.get('DATABASE_URL', ''):
            # PostgreSQL
            result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='post' AND column_name='reading_time'"))
            column_exists = result.fetchone() is not None
        else:
            # SQLite
            result = db.session.execute(text("PRAGMA table_info(post)"))
            columns = result.fetchall()
            column_exists = any(col[1] == 'reading_time' for col in columns)
        
        if column_exists:
            print("O campo reading_time já existe na tabela post.")
    except Exception as e:
        print(f"Erro ao verificar esquema: {e}")
    
    # Se o campo não existir, adicionar via migração manual
    if not column_exists:
        try:
            # Adicionar a coluna reading_time à tabela post
            if 'postgres' in os.environ.get('DATABASE_URL', ''):
                # PostgreSQL
                db.session.execute(text("ALTER TABLE post ADD COLUMN reading_time INTEGER"))
            else:
                # SQLite
                db.session.execute(text("ALTER TABLE post ADD COLUMN reading_time INTEGER"))
            
            db.session.commit()
            print("Coluna reading_time adicionada com sucesso!")
            
            # Agora vamos atualizar os modelos para reconhecer a nova coluna
            print("Atualizando modelos...")
            db.session.close()  # Fechar a sessão atual
            
            # Atualizar valores existentes com base no conteúdo
            print("Atualizando valores de tempo de leitura para posts existentes...")
            posts = Post.query.all()
            for post in posts:
                # Calcular o tempo de leitura usando a função existente
                reading_time_value = post.get_reading_time()
                # Atualizar diretamente no banco para evitar erros de atributos
                db.session.execute(
                    text("UPDATE post SET reading_time = :rt WHERE id = :id"),
                    {"rt": reading_time_value, "id": post.id}
                )
            
            db.session.commit()
            count_result = db.session.execute(text("SELECT COUNT(*) FROM post"))
            count = count_result.scalar()
            print(f"Valores de tempo de leitura atualizados para {count} posts.")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao executar migração: {e}")
    
    print("Migração concluída.")

if __name__ == "__main__":
    print("Script de migração executado.") 