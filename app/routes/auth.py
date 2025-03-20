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

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("auth_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('auth_debug')

# Blueprint de autenticação
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            logger.info(f"Usuário já autenticado ({current_user.username}), redirecionando...")
            return redirect(url_for('main.index'))
        
        form = LoginForm()
        
        if form.validate_on_submit():
            logger.info(f"Tentativa de login: {form.email.data}")
            
            user = User.query.filter_by(email=form.email.data).first()
            
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                logger.info(f"Login bem-sucedido para: {user.email} (ID: {user.id})")
                
                # Registrar a sessão para garantir que o CSRF token seja salvo
                session.modified = True
                
                next_page = request.args.get('next')
                if not next_page or urlparse(next_page).netloc != '':
                    next_page = url_for('main.index')
                return redirect(next_page)
            else:
                logger.warning(f"Falha de login para email: {form.email.data}")
                flash('Invalid email or password', 'danger')
        
        return render_template('auth/login.html', form=form)
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
        
        if request.method == 'POST':
            # Verificar token CSRF explicitamente
            logger.info("Verificando token CSRF...")
            csrf_token = request.form.get('csrf_token')
            if not csrf_token:
                logger.error("Token CSRF ausente no formulário")
                flash('CSRF token missing', 'danger')
                return render_template('auth/register.html', form=form)
        
        if form.validate_on_submit():
            logger.info(f"Formulário validado: username={form.username.data}, email={form.email.data}")
            
            # Verificar se usuário ou email já existem
            existing_user = User.query.filter_by(username=form.username.data).first()
            existing_email = User.query.filter_by(email=form.email.data).first()
            
            if existing_user:
                logger.warning(f"Username já existe: {form.username.data}")
                flash('Username already taken', 'danger')
                return render_template('auth/register.html', form=form)
                
            if existing_email:
                logger.warning(f"Email já existe: {form.email.data}")
                flash('Email already registered', 'danger')
                return render_template('auth/register.html', form=form)
            
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
                    
                    return redirect(url_for('auth.login'))
                else:
                    logger.error("❌ Falha ao criar usuário após múltiplas tentativas")
                    flash('An error occurred while creating your account. Please try again.', 'danger')
            except Exception as user_creation_error:
                logger.error(f"❌ Erro na criação do usuário: {str(user_creation_error)}")
                logger.exception("Detalhes completos do erro:")
                flash('An error occurred while creating your account. Please try again.', 'danger')
        
        return render_template('auth/register.html', form=form)
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