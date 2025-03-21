from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm, ProfileUpdateForm, PasswordChangeForm
from urllib.parse import urlsplit, urlparse
import logging
import traceback
from datetime import datetime
import time
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("auth_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('auth_debug')

# Blueprint de autenticação
auth_bp = Blueprint('auth', __name__)

# Instanciar CSRFProtect
csrf = CSRFProtect()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        # Inicializar a sessão se ela não existir
        if not session:
            logger.warning("Sessão não inicializada no login, criando nova")
            session.clear()
            session.permanent = True
        
        # Debug da sessão
        logger.info(f"ID da sessão no login: {session.sid if hasattr(session, 'sid') else 'N/A'}")
        logger.info(f"Chaves na sessão antes: {list(session.keys())}")
        
        # Preservar token CSRF se já existir
        csrf_token = session.get('csrf_token', None)
        if not csrf_token:
            logger.warning("Token CSRF não encontrado na sessão de login, gerando novo token")
            csrf_token = generate_csrf()
            session['csrf_token'] = csrf_token
            logger.info(f"Token CSRF criado e armazenado na sessão: {csrf_token[:8]}...")
        else:
            logger.info(f"Token CSRF existente na sessão: {csrf_token[:8]}...")
            
        # Forçar modificação da sessão para garantir persistência
        session.modified = True
        
        # Log adicionais para depuração
        form_csrf = request.form.get('csrf_token', None) if request.method == 'POST' else None
        if form_csrf:
            logger.info(f"Token CSRF recebido do formulário: {form_csrf[:8]}...")
            if form_csrf != csrf_token:
                logger.warning("TOKENS CSRF DIFERENTES! Formulário ≠ Sessão")
            else:
                logger.info("TOKENS CSRF IGUAIS! Formulário = Sessão")
                
        if current_user.is_authenticated:
            logger.info(f"Usuário já autenticado ({current_user.username}), redirecionando...")
            return redirect(url_for('main.index'))
        
        form = LoginForm()
        
        # Para requisições POST
        if request.method == 'POST':
            # Logar todos os dados do formulário (exceto senha)
            safe_form_data = {k: v for k, v in request.form.items() if k != 'password'}
            logger.info(f"Dados do formulário POST: {safe_form_data}")
            
            # Verificação explícita do token CSRF para depuração
            if not form.validate_on_submit() and form.errors:
                logger.warning(f"Erros de validação do formulário: {form.errors}")
                # Se há erro de CSRF específico
                if 'csrf_token' in form.errors:
                    logger.warning(f"Erro específico de CSRF: {form.errors['csrf_token']}")
            
            # Se o formulário tem erro de validação e for por causa do CSRF, tentar tratar
            if not form.validate_on_submit() and form.errors and 'csrf_token' in form.errors:
                logger.warning(f"Erro de validação CSRF: {form.errors['csrf_token']} - tentando recuperar")
                # Em vez de mostrar erro, tentar com um novo token
                new_token = generate_csrf()
                return render_template('auth/login.html', form=form, csrf_token=new_token)
        
        if form.validate_on_submit():
            logger.info(f"Tentativa de login: {form.email.data}")
            
            # Adicionar tratamento de erro SSL aqui
            try:
                user = User.query.filter_by(email=form.email.data).first()
                
                if user and user.check_password(form.password.data):
                    login_user(user, remember=form.remember_me.data)
                    logger.info(f"Login bem-sucedido para: {user.email} (ID: {user.id})")
                    
                    # Registrar a sessão para garantir que o token CSRF seja salvo
                    session.modified = True
                    session.permanent = True  # Tornar a sessão permanente
                    
                    next_page = request.args.get('next')
                    if not next_page or urlparse(next_page).netloc != '':
                        next_page = url_for('main.index')
                    return redirect(next_page)
                else:
                    logger.warning(f"Falha de login para email: {form.email.data}")
                    flash('Invalid email or password', 'danger')
            except Exception as e:
                # Registrar o erro
                logger.error(f"Erro durante consulta de usuário: {str(e)}")
                
                # Verificar se é um erro SSL
                is_ssl_error = False
                if hasattr(e, 'orig') and isinstance(e.orig, Exception):
                    orig_error = str(e.orig).lower()
                    is_ssl_error = 'ssl error' in orig_error or 'decryption failed' in orig_error
                
                if is_ssl_error:
                    logger.warning("Detectado erro SSL na consulta de usuário, tentando login alternativo")
                    # Opção 1: Tentar encontrar o usuário por email usando SQL direto
                    try:
                        # Usar o mesmo SQL mostrado no erro, mas evitando ORM
                        sql = """
                        SELECT id, username, email, password_hash, is_admin, is_premium
                        FROM "user" 
                        WHERE email = %s 
                        LIMIT 1
                        """
                        # Obter conexão direta
                        connection = db.engine.raw_connection()
                        cursor = connection.cursor()
                        cursor.execute(sql, (form.email.data,))
                        user_row = cursor.fetchone()
                        cursor.close()
                        connection.close()
                        
                        if user_row:
                            # Criar objeto User manualmente
                            manual_user = User(
                                id=user_row[0],
                                username=user_row[1],
                                email=user_row[2],
                                is_admin=user_row[4],
                                is_premium=user_row[5]
                            )
                            manual_user.password_hash = user_row[3]
                            
                            # Verificar senha manualmente
                            if manual_user.check_password(form.password.data):
                                login_user(manual_user, remember=form.remember_me.data)
                                logger.info(f"Login bem-sucedido via método alternativo para: {manual_user.email}")
                                
                                # Registrar a sessão
                                session.modified = True
                                session.permanent = True
                                
                                next_page = request.args.get('next')
                                if not next_page or urlparse(next_page).netloc != '':
                                    next_page = url_for('main.index')
                                return redirect(next_page)
                    except Exception as alt_error:
                        logger.error(f"Falha no método alternativo de login: {str(alt_error)}")
                    
                    # Se chegou aqui, ambos os métodos falharam
                    flash('Unable to connect to the database. Please try again later.', 'danger')
                else:
                    # Outros erros que não são de SSL
                    flash('An error occurred during login. Please try again.', 'danger')
        
        # Sempre gerar um novo token CSRF para o template
        new_csrf_token = generate_csrf()
        logger.info("Novo token CSRF gerado para o formulário de login")
        # Garantir que a sessão seja salva
        session.modified = True
        session.permanent = True  # Tornar a sessão permanente
        
        return render_template('auth/login.html', form=form, csrf_token=new_csrf_token)
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        logger.error(traceback.format_exc())
        flash('An error occurred during login. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    logout_user()
    # Limpar a sessão
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    try:
        logger.info("==== INICIANDO REGISTRO DE NOVO USUÁRIO ====")
        logger.info(f"Data/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Inicializar a sessão se ela não existir
        if not session:
            logger.warning("Sessão não inicializada, criando nova")
            session.clear()
            session.permanent = True
        
        # Inicializar token CSRF na sessão
        if 'csrf_token' not in session:
            logger.warning("Token CSRF não encontrado na sessão, gerando novo token")
            token = generate_csrf()
            session['csrf_token'] = token
            logger.info(f"Token CSRF criado e armazenado na sessão: {token[:8]}...")
            session.modified = True

        if current_user.is_authenticated:
            logger.info("Usuário já autenticado, redirecionando para página inicial")
            return redirect(url_for('main.index'))
        
        form = RegistrationForm()
        
        # Para requisições POST, verificar se há problemas com CSRF
        if request.method == 'POST':
            # Verificar e reparar a sessão CSRF
            csrf_token = request.form.get('csrf_token')
            logger.info(f"Token CSRF recebido: {csrf_token[:8] if csrf_token else 'Nenhum'}")
            logger.info(f"Token CSRF na sessão: {session.get('csrf_token', 'Nenhum')[:8] if session.get('csrf_token') else 'Nenhum'}")
            
            # Se não há token no formulário, regerar
            if not csrf_token:
                logger.warning("Token CSRF ausente no formulário")
                new_token = generate_csrf()
                session.modified = True
                return render_template('auth/register.html', form=form, csrf_token=new_token)
            
            # Verificar erros CSRF no formulário
            if not form.validate_on_submit() and form.errors and 'csrf_token' in form.errors:
                logger.warning(f"Erro de validação CSRF: {form.errors['csrf_token']}")
                # Regenerar token e continuar
                new_token = generate_csrf()
                session.modified = True
                return render_template('auth/register.html', form=form, csrf_token=new_token)
        
        if form.validate_on_submit():
            logger.info(f"Formulário validado: username={form.username.data}, email={form.email.data}")
            
            # Verificar se usuário ou email já existem
            existing_user = User.query.filter_by(username=form.username.data).first()
            existing_email = User.query.filter_by(email=form.email.data).first()
            
            if existing_user:
                logger.warning(f"Username já existe: {form.username.data}")
                flash('Username already taken', 'danger')
                return render_template('auth/register.html', form=form, csrf_token=generate_csrf())
                
            if existing_email:
                logger.warning(f"Email já existe: {form.email.data}")
                flash('Email already registered', 'danger')
                return render_template('auth/register.html', form=form, csrf_token=generate_csrf())
            
            # Criação do novo usuário
            try:
                logger.info("Criando novo objeto de usuário")
                user = User(
                    username=form.username.data, 
                    email=form.email.data,
                    is_admin=False,
                    is_premium=False
                )
                user.set_password(form.password.data)
                
                logger.info("Adicionando usuário à sessão")
                db.session.add(user)
                
                # Commit para o banco de dados com tratamento de erros mais robusto
                attempt = 1
                max_attempts = 3
                success = False
                while attempt <= max_attempts and not success:
                    try:
                        logger.info(f"Tentativa {attempt} de commit na sessão")
                        db.session.commit()
                        success = True
                        logger.info("✅ Commit realizado com sucesso")
                    except Exception as commit_error:
                        db.session.rollback()
                        logger.error(f"Erro no commit (tentativa {attempt}): {str(commit_error)}")
                        attempt += 1
                        if attempt <= max_attempts:
                            logger.info(f"Tentando commit novamente...")
                
                if success:
                    # Garantir que o ID foi atribuído corretamente
                    db.session.refresh(user)
                    logger.info(f"✅ Usuário criado com sucesso: ID={user.id}")
                    flash('Your account has been created! You can now log in.', 'success')
                    
                    # Garantir que a sessão é salva para manter o token CSRF
                    session.modified = True
                    session.permanent = True  # Tornar a sessão permanente
                    
                    return redirect(url_for('auth.login'))
                else:
                    logger.error("❌ Falha ao criar usuário após múltiplas tentativas")
                    flash('An error occurred while creating your account. Please try again.', 'danger')
            except Exception as user_creation_error:
                logger.error(f"❌ Erro na criação do usuário: {str(user_creation_error)}")
                logger.exception("Detalhes completos do erro:")
                flash('An error occurred while creating your account. Please try again.', 'danger')
        
        # Sempre gerar um novo token CSRF para o template
        new_csrf_token = generate_csrf()
        logger.info("Novo token CSRF gerado para o formulário de registro")
        # Garantir que a sessão seja salva
        session.modified = True
        session.permanent = True  # Tornar a sessão permanente
        
        return render_template('auth/register.html', form=form, csrf_token=new_csrf_token)
    except Exception as e:
        logger.error(f"❌ Erro inesperado no registro: {str(e)}")
        logger.exception("Detalhes completos do erro:")
        flash('An unexpected error occurred. Please try again later.', 'danger')
        return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    try:
        form = ProfileUpdateForm(original_username=current_user.username, original_email=current_user.email)
        password_form = PasswordChangeForm()
        
        if form.validate_on_submit():
            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.age = form.age.data
            
            db.session.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('auth.profile'))
        elif request.method == 'GET':
            form.username.data = current_user.username
            form.email.data = current_user.email
            form.age.data = current_user.age
        
        return render_template('auth/profile.html', form=form, password_form=password_form)
    except Exception as e:
        logger.error(f"ERROR in profile route: {str(e)}")
        db.session.rollback()
        flash('An error occurred while updating your profile. Please try again.', 'danger')
        return redirect(url_for('main.index'))

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    try:
        form = PasswordChangeForm()
        
        if form.validate_on_submit():
            # Verificar se a senha atual está correta
            if current_user.check_password(form.current_password.data):
                # Atualizar a senha
                current_user.set_password(form.new_password.data)
                db.session.commit()
                flash('Your password has been updated successfully!', 'success')
            else:
                flash('Current password is incorrect.', 'danger')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", 'danger')
        
        return redirect(url_for('auth.profile'))
    except Exception as e:
        logger.error(f"ERROR in change_password route: {str(e)}")
        db.session.rollback()
        flash('An error occurred while updating your password. Please try again.', 'danger')
        return redirect(url_for('auth.profile'))

@auth_bp.route('/alt-login', methods=['GET', 'POST'])
def alternative_login():
    """
    Rota alternativa de login que não usa CSRF - TEMPORÁRIO APENAS PARA EMERGÊNCIAS
    """
    try:
        logger.info("Usando rota de login alternativa sem CSRF")
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
        
        # Usar um formulário sem CSRF
        from flask_wtf import FlaskForm
        from wtforms import StringField, PasswordField, BooleanField, SubmitField
        from wtforms.validators import DataRequired, Email

        class SimpleLoginForm(FlaskForm):
            class Meta:
                csrf = False  # Desativar CSRF para este formulário
                
            email = StringField('Email', validators=[DataRequired(), Email()])
            password = PasswordField('Password', validators=[DataRequired()])
            remember_me = BooleanField('Remember Me')
            submit = SubmitField('Sign In')
        
        form = SimpleLoginForm()
        
        if request.method == 'POST':
            logger.info(f"Tentativa de login alternativo: {request.form.get('email', 'N/A')}")
            
            # Validar o formulário
            if form.validate_on_submit():
                try:
                    # Tentar encontrar o usuário usando SQL direto
                    email = form.email.data
                    try:
                        # SQL direto para buscar usuário
                        sql = """
                        SELECT id, username, email, password_hash, is_admin, is_premium
                        FROM "user" 
                        WHERE email = %s 
                        LIMIT 1
                        """
                        # Obter conexão direta
                        connection = db.engine.raw_connection()
                        cursor = connection.cursor()
                        cursor.execute(sql, (email,))
                        user_row = cursor.fetchone()
                        cursor.close()
                        connection.close()
                        
                        if user_row:
                            # Criar objeto User manualmente
                            manual_user = User(
                                id=user_row[0],
                                username=user_row[1],
                                email=user_row[2],
                                is_admin=user_row[4],
                                is_premium=user_row[5]
                            )
                            manual_user.password_hash = user_row[3]
                            
                            # Verificar senha manualmente
                            from werkzeug.security import check_password_hash
                            if check_password_hash(manual_user.password_hash, form.password.data):
                                login_user(manual_user, remember=form.remember_me.data)
                                logger.info(f"Login alternativo bem-sucedido para: {manual_user.email}")
                                
                                # Redirecionar para a página inicial
                                return redirect(url_for('main.index'))
                            else:
                                logger.warning(f"Senha incorreta para login alternativo: {email}")
                                flash('Senha incorreta', 'danger')
                        else:
                            logger.warning(f"Usuário não encontrado para login alternativo: {email}")
                            flash('Email não encontrado', 'danger')
                    except Exception as e:
                        logger.error(f"Erro no login alternativo: {str(e)}")
                        flash('Erro ao tentar login. Por favor, tente novamente.', 'danger')
                except Exception as e:
                    logger.error(f"Erro não tratado no login alternativo: {str(e)}")
                    flash('Ocorreu um erro inesperado. Por favor, tente novamente.', 'danger')
        
        # Renderizar template com formulário simples
        return render_template('auth/alt_login.html', form=form)
    except Exception as e:
        logger.error(f"Erro geral no login alternativo: {str(e)}")
        logger.error(traceback.format_exc())
        flash('Erro inesperado. Tente novamente mais tarde.', 'danger')
        return redirect(url_for('main.index')) 