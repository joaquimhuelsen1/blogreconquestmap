from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from config import Config
from datetime import datetime, timedelta
import os

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
        # Caso contrário, deixar o Flask lidar normalmente
        return e
    
    # Registrar blueprints
    from app.routes import main_bp, auth_bp, admin_bp, ai_chat_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(ai_chat_bp)
    
    with app.app_context():
        # Importações que dependem do contexto da aplicação
        from app.models import User, Post
        
        # Criar tabelas do banco de dados se não existirem
        db.create_all()
    
    # Adicionar variável now para os templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    return app

# Importar models para que sejam visíveis quando app é importado
from app import models

# Tornar a função create_app disponível para importação diretamente de app
__all__ = ['create_app', 'db'] 