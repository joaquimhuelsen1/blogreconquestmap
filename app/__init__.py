from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
# Importar Flask-Migrate condicionalmente
import importlib.util
# from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from config import Config
from datetime import datetime, timedelta
import os
import traceback
import logging
from sqlalchemy import text

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("app_init_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('blog_app_init')

db = SQLAlchemy()
# Verificar se Flask-Migrate está disponível
flask_migrate_available = importlib.util.find_spec('flask_migrate') is not None
if flask_migrate_available:
    from flask_migrate import Migrate
    migrate = Migrate()
    logger.info("Flask-Migrate disponível e inicializado")
else:
    migrate = None
    logger.warning("Flask-Migrate não está disponível")

# Verificar se Flask-Session está disponível
flask_session_available = importlib.util.find_spec('flask_session') is not None
if flask_session_available:
    from flask_session import Session
    sess = Session()
    logger.info("Flask-Session disponível e inicializado")
else:
    sess = None
    logger.warning("Flask-Session não está disponível")

login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

def setup_db_event_listeners(app_db):
    """Configura event listeners para o SQLAlchemy dentro do contexto"""
    @app_db.event.listens_for(app_db.engine, 'connect')
    def receive_connect(dbapi_connection, connection_record):
        logger.info("==== CONEXÃO COM BANCO DE DADOS ESTABELECIDA ====")
    
    @app_db.event.listens_for(app_db.engine, 'checkout')
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        logger.info("Conexão retirada do pool")
    
    @app_db.event.listens_for(app_db.engine, 'before_cursor_execute')
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        # Logar apenas as consultas relacionadas a posts para não sobrecarregar o log
        if 'post' in statement.lower():
            logger.info(f"SQL: {statement}")
            logger.info(f"Parâmetros: {parameters}")
    
    logger.info("Event listeners registrados para SQLAlchemy")

def create_app():
    """Create and configure the Flask application."""
    logger.info("==== INICIALIZANDO APLICAÇÃO FLASK ====")
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Log das configurações importantes (sem revelar senhas)
    safe_config = {k: v for k, v in app.config.items() 
                  if not any(secret in k.lower() for secret in ['key', 'password', 'token', 'secret'])}
    logger.info(f"Configurações carregadas: {safe_config}")
    
    # Certifique-se de que o diretório instance existe
    os.makedirs(app.instance_path, exist_ok=True)
    logger.info(f"Diretório instance: {app.instance_path}")
    
    # Garantir que existe uma chave secreta para sessões
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.urandom(24).hex()
        logger.info("Nova SECRET_KEY gerada")
    logger.info(f"SECRET_KEY configurada: {app.config.get('SECRET_KEY')[:5]}...")
    
    # Configurações da sessão
    if flask_session_available:
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_PERMANENT'] = True
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
        app.config['SESSION_FILE_DIR'] = os.path.join(app.instance_path, 'flask_session')
        app.config['SESSION_USE_SIGNER'] = True
        app.config['SESSION_KEY_PREFIX'] = 'reconquest_'
        os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
        logger.info(f"Diretório de sessão: {app.config['SESSION_FILE_DIR']}")
    
    # Configuração CSRF
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hora
    logger.info(f"Proteção CSRF: ATIVADA, Tempo limite: {app.config['WTF_CSRF_TIME_LIMIT']}s")
    
    # Inicializar extensões
    db.init_app(app)
    logger.info("SQLAlchemy inicializado")
    
    # Configurar listeners dentro do contexto da aplicação
    with app.app_context():
        setup_db_event_listeners(db)
    
    # Tentar conectar ao banco de dados
    try:
        # Se estamos usando PostgreSQL, tentar conectar
        if 'postgresql://' in app.config['SQLALCHEMY_DATABASE_URI']:
            logger.info("Tentando conectar ao PostgreSQL...")
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            masked_url = db_url
            if '@' in db_url:
                # Mascarar senha na URL para exibição
                prefix, suffix = db_url.split('@', 1)
                if ':' in prefix and '/' in prefix:
                    user_part, pass_part = prefix.rsplit(':', 1)
                    masked_url = f"{user_part}:***@{suffix}"
            logger.info(f"URL PostgreSQL: {masked_url}")
            
            with app.app_context():
                connection = db.engine.connect()
                # Verificar a versão do PostgreSQL - usar text() para executar SQL
                version = connection.execute(text("SELECT version();")).scalar()
                logger.info(f"✅ Conexão PostgreSQL estabelecida: {version}")
                connection.close()
    except Exception as e:
        logger.error(f"❌ ERRO DE CONEXÃO COM BANCO DE DADOS: {str(e)}")
        logger.exception("Detalhes do erro de conexão:")
        logger.warning("Alterando para SQLite como fallback devido a erro de conexão...")
        # Alterar para SQLite como fallback
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'fallback.db')
        logger.info(f"Novo URI SQLite: {app.config['SQLALCHEMY_DATABASE_URI']}")
        # Reinicializar a conexão mas manter a instância db
        with app.app_context():
            db.create_all()  # Criar as tabelas no SQLite
            logger.info("Tabelas criadas no SQLite de fallback")
    
    if migrate is not None:
        migrate.init_app(app, db)
        logger.info("Flask-Migrate inicializado")
    login_manager.init_app(app)
    logger.info("Flask-Login inicializado")
    if sess is not None:
        sess.init_app(app)
        logger.info("Flask-Session inicializado")
    csrf.init_app(app)  # Inicializa proteção CSRF
    logger.info("CSRF inicializado")
    
    # Configurar login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Handler para requisições AJAX retornarem JSON em caso de erro
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"❌ ERRO NA APLICAÇÃO: {str(e)}")
        logger.exception("Detalhes completos do erro:")
        
        # Verificar se a requisição é AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            logger.error(f"Erro na requisição AJAX: {str(e)}")
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
        app.register_blueprint(main_bp, name='main')  # Explicitar o nome do blueprint
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(ai_chat_bp)
        logger.info("✅ Blueprints registrados da pasta app/routes/")
    except ImportError as e:
        logger.warning(f"Erro ao importar do pacote app.routes: {str(e)}")
        # Caso falhe, tentar importar do arquivo app/routes.py
        try:
            from app.routes import main_bp, auth_bp, admin_bp
            app.register_blueprint(main_bp, name='main')  # Explicitar o nome do blueprint
            app.register_blueprint(auth_bp, url_prefix='/auth')
            app.register_blueprint(admin_bp, url_prefix='/admin')
            
            # Tentar importar o ai_chat_bp separadamente, pois pode não existir no arquivo
            try:
                from app.routes import ai_chat_bp
                app.register_blueprint(ai_chat_bp)
            except ImportError:
                logger.warning("Blueprint ai_chat_bp não encontrado")
            
            logger.info("✅ Blueprints registrados do arquivo app/routes.py")
        except ImportError as e:
            logger.error(f"❌ ERRO FATAL: Não foi possível importar os blueprints: {str(e)}")
            logger.exception("Detalhes do erro de importação:")
    
    with app.app_context():
        # Importações que dependem do contexto da aplicação
        from app.models import User, Post
        
        # Tentar verificar o banco de dados
        try:
            # Verificar se as tabelas já existem
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Tabelas existentes: {tables}")
            
            # Verificar a tabela de posts
            if 'post' in tables:
                post_count = Post.query.count()
                logger.info(f"Tabela 'post' tem {post_count} registros")
                
                # Verificar alguns posts
                if post_count > 0:
                    posts = Post.query.limit(3).all()
                    post_ids = [p.id for p in posts]
                    logger.info(f"Primeiros IDs de posts: {post_ids}")
        except Exception as db_check_error:
            logger.error(f"❌ Erro ao verificar tabelas: {str(db_check_error)}")
        
        # Criar tabelas do banco de dados se não existirem
        try:
            db.create_all()
            logger.info("✅ Tabelas do banco de dados criadas com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabelas do banco de dados: {str(e)}")
            logger.exception("Detalhes do erro ao criar tabelas:")
    
    # Página de erro para 404
    @app.errorhandler(404)
    def page_not_found(e):
        logger.warning(f"Página não encontrada: {request.path}")
        return render_template('errors/404.html'), 404
    
    # Página de erro para 500
    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"Erro interno do servidor: {str(e)}")
        return render_template('errors/500.html', error=str(e)), 500
    
    # Adicionar variável now para os templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    logger.info("==== APLICAÇÃO FLASK INICIALIZADA COM SUCESSO ====")
    return app

# Importar models para que sejam visíveis quando app é importado
from app import models

# Tornar a função create_app disponível para importação diretamente de app
__all__ = ['create_app', 'db'] 