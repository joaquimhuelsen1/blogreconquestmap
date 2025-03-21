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
        if current_user.is_authenticated:
            logger.info(f"Usuário já autenticado ({current_user.username}), redirecionando...")
            return redirect(url_for('main.index'))
        
        form = LoginForm()
        
        # Para requisições POST, verificar se há problemas com CSRF
        if request.method == 'POST':
            # Garantir que a sessão existe
            if 'csrf_token' not in session:
                logger.warning("Sessão sem token CSRF - inicializando nova sessão")
                # Forçar uma regeneração do token na sessão
                generate_csrf()
                session.modified = True
                session.permanent = True  # Tornar a sessão permanente
                
            # Se o formulário tem erro de validação e for por causa do CSRF, tentar tratar
            if not form.validate_on_submit() and form.errors and 'csrf_token' in form.errors:
                logger.warning(f"Erro de validação CSRF: {form.errors['csrf_token']} - tentando recuperar")
                # Em vez de mostrar erro, tentar com um novo token
                new_token = generate_csrf()
                return render_template('auth/login.html', form=form, csrf_token=new_token)
        
        if form.validate_on_submit():
            logger.info(f"Tentativa de login: {form.email.data}")
            
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
        
        if current_user.is_authenticated:
            logger.info("Usuário já autenticado, redirecionando para página inicial")
            return redirect(url_for('main.index'))
        
        form = RegistrationForm()
        
        # Para requisições POST, verificar se há problemas com CSRF
        if request.method == 'POST':
            # Garantir que a sessão existe
            if 'csrf_token' not in session:
                logger.warning("Sessão sem token CSRF - inicializando nova sessão")
                # Forçar uma regeneração do token na sessão
                generate_csrf()
                session.modified = True
                session.permanent = True  # Tornar a sessão permanente
                
            # Verificar token CSRF explicitamente, mas ser mais tolerante
            logger.info("Verificando token CSRF...")
            csrf_token = request.form.get('csrf_token')
            if not csrf_token:
                logger.warning("Token CSRF ausente no formulário - tentando continuar mesmo assim")
                # Gerar um novo token e continuar
                new_token = generate_csrf()
                return render_template('auth/register.html', form=form, csrf_token=new_token)
            
            # Se o formulário tem erro de validação e for por causa do CSRF
            if not form.validate_on_submit() and form.errors and 'csrf_token' in form.errors:
                logger.warning(f"Erro de validação CSRF: {form.errors['csrf_token']} - tentando recuperar")
                # Em vez de mostrar um erro, tentar com um novo token
                new_token = generate_csrf()
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
                
                # Garantir que não há transação ativa
                db.session.rollback()
                logger.info("Sessão limpa de transações anteriores")
                
                # Adicionar usuário e commitar em uma operação simples
                try:
                    logger.info("Adicionando usuário à sessão")
                    db.session.add(user)
                    logger.info("Tentando commit direto")
                    db.session.commit()
                    logger.info("✅ Commit realizado com sucesso")
                    
                    # Garantir que o ID foi atribuído corretamente
                    logger.info(f"✅ Usuário criado com sucesso: ID={user.id}")
                    flash('Your account has been created! You can now log in.', 'success')
                    
                    # Limpar e regenerar sessão para CSRF token fresco
                    session.clear()
                    generate_csrf() 
                    session.modified = True
                    session.permanent = True
                    
                    return redirect(url_for('auth.login'))
                    
                except Exception as commit_error:
                    db.session.rollback()
                    logger.error(f"❌ Erro no commit: {str(commit_error)}")
                    
                    # Se for erro SSL, tentar método alternativo
                    if 'SSL' in str(commit_error) or 'OperationalError' in str(commit_error):
                        logger.warning("Tentando método alternativo para criar usuário...")
                        
                        # Tentar inserção direta via SQL
                        try:
                            from sqlalchemy import text
                            with db.engine.connect() as conn:
                                # Começar uma nova transação
                                with conn.begin():
                                    # SQL para inserir usuário diretamente
                                    sql = text("""
                                    INSERT INTO "user" (username, email, password_hash, is_admin, is_premium, created_at)
                                    VALUES (:username, :email, :password_hash, :is_admin, :is_premium, :created_at)
                                    """)
                                    
                                    conn.execute(
                                        sql, 
                                        {
                                            'username': form.username.data,
                                            'email': form.email.data,
                                            'password_hash': user.password_hash,
                                            'is_admin': False,
                                            'is_premium': False,
                                            'created_at': datetime.utcnow()
                                        }
                                    )
                            
                            logger.info("✅ Usuário criado com SQL direto com sucesso!")
                            flash('Your account has been created! You can now log in.', 'success')
                            
                            # Limpar e regenerar sessão
                            session.clear()
                            generate_csrf()
                            session.modified = True
                            session.permanent = True
                            
                            return redirect(url_for('auth.login'))
                        except Exception as sql_error:
                            logger.error(f"❌ Erro no SQL direto: {str(sql_error)}")
                            flash('An error occurred while creating your account. Please try again.', 'danger')
                    else:
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