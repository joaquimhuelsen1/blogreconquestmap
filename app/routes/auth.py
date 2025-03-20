from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm, ProfileUpdateForm, PasswordChangeForm
from urllib.parse import urlsplit
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
            return redirect(url_for('main.index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            logger.info(f"Tentativa de login: email={form.email.data}")
            
            # Buscar usuário pelo email
            user = User.query.filter_by(email=form.email.data).first()
            
            # Verificar se o usuário existe
            if user is None:
                logger.warning(f"Usuário não encontrado: {form.email.data}")
                flash('Invalid email or password', 'danger')
                return redirect(url_for('auth.login'))
            
            # Verificar a senha
            password_ok = user.check_password(form.password.data)
            logger.info(f"Verificação de senha para {user.username}: {password_ok}")
            
            if not password_ok:
                flash('Invalid email or password', 'danger')
                return redirect(url_for('auth.login'))
            
            # Login do usuário
            login_user(user, remember=form.remember_me.data)
            logger.info(f"Login bem-sucedido: {user.username}")
            
            next_page = request.args.get('next')
            if not next_page or urlsplit(next_page).netloc != '':
                next_page = url_for('main.index')
            return redirect(next_page)
        
        return render_template('auth/login.html', form=form)
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        logger.error(traceback.format_exc())
        flash('An error occurred during login. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    logout_user()
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
            
            # Criar novo usuário
            logger.info("Criando novo objeto de usuário")
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            
            try:
                logger.info("Adicionando usuário à sessão")
                db.session.add(user)
                
                # Definir timeout para o commit para evitar travamentos
                MAX_RETRIES = 3
                retry_count = 0
                commit_success = False
                
                while retry_count < MAX_RETRIES and not commit_success:
                    try:
                        logger.info(f"Tentativa {retry_count+1} de commit na sessão")
                        # Definir timeout de 10 segundos para o commit
                        db.session.commit()
                        commit_success = True
                        logger.info("✅ Commit realizado com sucesso")
                    except Exception as commit_err:
                        retry_count += 1
                        logger.error(f"Erro no commit (tentativa {retry_count}): {str(commit_err)}")
                        
                        # Rollback e espera antes de tentar novamente
                        db.session.rollback()
                        if retry_count < MAX_RETRIES:
                            wait_time = 1 * retry_count  # Aumenta o tempo de espera a cada tentativa
                            logger.info(f"Aguardando {wait_time}s antes de tentar novamente...")
                            time.sleep(wait_time)
                
                if not commit_success:
                    logger.error("❌ Falha após todas as tentativas de commit")
                    flash('There was a problem creating your account. Please try again.', 'danger')
                    return render_template('auth/register.html', form=form)
                
                # Verificar se o usuário foi realmente criado
                created_user = User.query.filter_by(email=form.email.data).first()
                if created_user:
                    logger.info(f"✅ Usuário criado com sucesso: ID={created_user.id}")
                else:
                    logger.error("❌ Usuário não encontrado após commit!")
                    
                flash('Congratulations, you are now registered!', 'success')
                return redirect(url_for('auth.login'))
            except Exception as db_error:
                db.session.rollback()
                logger.error(f"❌ ERRO AO SALVAR USUÁRIO NO BANCO: {str(db_error)}")
                logger.error(traceback.format_exc())
                # Tentar acessar detalhes do erro do PostgreSQL
                pgcode = getattr(db_error, 'pgcode', None)
                if pgcode:
                    logger.error(f"Código de erro PostgreSQL: {pgcode}")
                
                # Mensagem específica para o usuário
                error_msg = "An error occurred during registration."
                if hasattr(db_error, 'orig') and db_error.orig is not None:
                    if 'timeout' in str(db_error.orig).lower():
                        error_msg = "The database connection timed out. Please try again."
                    elif 'permission' in str(db_error.orig).lower():
                        error_msg = "Permission error. Please contact the administrator."
                
                flash(error_msg, 'danger')
                return render_template('auth/register.html', form=form)
        
        return render_template('auth/register.html', form=form)
    except Exception as e:
        logger.error(f"❌ ERRO GERAL NO REGISTRO: {str(e)}")
        logger.error(traceback.format_exc())
        flash('An error occurred. Please try again.', 'danger')
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