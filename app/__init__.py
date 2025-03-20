from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from config import Config
from datetime import datetime, timedelta
import os
import traceback

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
sess = Session()
csrf = CSRFProtect()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Certifique-se de que o diretório instance existe
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Garantir que existe uma chave secreta para sessões
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.urandom(24).hex()
    print(f"SECRET_KEY: {app.config.get('SECRET_KEY')[:8]}...")
    
    # Configurações da sessão
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
    app.config['SESSION_FILE_DIR'] = os.path.join(app.instance_path, 'flask_session')
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'reconquest_'
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # Configuração CSRF
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hora
    
    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    sess.init_app(app)
    csrf.init_app(app)  # Inicializa proteção CSRF
    
    # Configurar login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Handler para requisições AJAX retornarem JSON em caso de erro
    @app.errorhandler(Exception)
    def handle_exception(e):
        print(f"ERRO NA APLICAÇÃO: {str(e)}")
        traceback.print_exc()  # Imprime o traceback completo para debugging
        
        # Verificar se a requisição é AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            app.logger.error(f"Erro na requisição AJAX: {str(e)}")
            # Se for AJAX, retornar erro como JSON
            response = jsonify({
                'success': False,
                'error': str(e)
            })
            response.headers['Content-Type'] = 'application/json'
            return response, 500
        
        # Página de erro customizada
        return render_template('errors/500.html', error=str(e)), 500
    
    # Registrar blueprints - Verificar se o módulo ou o pacote existe
    try:
        # Tentar importar do pacote app.routes (pasta)
        from app.routes import main_bp, auth_bp, admin_bp, ai_chat_bp
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(ai_chat_bp)
        print("Blueprints registrados da pasta app/routes/")
    except ImportError as e:
        print(f"Erro ao importar do pacote app.routes: {str(e)}")
        # Caso falhe, tentar importar do arquivo app/routes.py
        try:
            from app.routes import main_bp, auth_bp, admin_bp
            app.register_blueprint(main_bp)
            app.register_blueprint(auth_bp, url_prefix='/auth')
            app.register_blueprint(admin_bp, url_prefix='/admin')
            
            # Tentar importar o ai_chat_bp separadamente, pois pode não existir no arquivo
            try:
                from app.routes import ai_chat_bp
                app.register_blueprint(ai_chat_bp)
            except ImportError:
                print("Blueprint ai_chat_bp não encontrado")
            
            print("Blueprints registrados do arquivo app/routes.py")
        except ImportError as e:
            print(f"ERRO FATAL: Não foi possível importar os blueprints: {str(e)}")
            traceback.print_exc()
    
    with app.app_context():
        # Importações que dependem do contexto da aplicação
        from app.models import User, Post
        
        # Criar tabelas do banco de dados se não existirem
        try:
            db.create_all()
            print("Tabelas do banco de dados criadas com sucesso")
        except Exception as e:
            print(f"Erro ao criar tabelas do banco de dados: {str(e)}")
            traceback.print_exc()
    
    # Página de erro para 404
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    # Página de erro para 500
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html', error=str(e)), 500
    
    # Adicionar variável now para os templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    return app

# Importar models para que sejam visíveis quando app é importado
from app import models

# Tornar a função create_app disponível para importação diretamente de app
__all__ = ['create_app', 'db'] 