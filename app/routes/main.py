from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify, session, current_app
from flask_login import current_user
from app import db
from app.models import User, Post, Comment
from app.forms import CommentForm, ChatMessageForm
import os
import requests
import json
import traceback  # Adicionar para debug
import logging  # Adicionar para logs
from datetime import datetime

# Configurar logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("app_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('blog_app')

# Blueprint principal
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Rota para a página inicial"""
    try:
        logger.info("==== ACESSANDO PÁGINA INICIAL ====")
        logger.info(f"Hora da solicitação: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Usuário autenticado: {current_user.is_authenticated}")
        
        if current_user.is_authenticated:
            logger.info(f"ID do usuário: {current_user.id}, Nome: {current_user.username}")
        
        # Obter parâmetros da solicitação
        page = request.args.get('page', 1, type=int)
        logger.info(f"Parâmetro de página: {page}")
        
        try:
            # Verificar configuração do banco de dados
            db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', 'Não definido')
            logger.info(f"String de conexão BD (parcial): {db_uri.split('@')[0].split(':')[0]}:***@{db_uri.split('@')[1] if '@' in db_uri else '(formato desconhecido)'}")
        except Exception as db_config_err:
            logger.error(f"Erro ao verificar config BD: {str(db_config_err)}")
            
        # Registrar informações da sessão
        logger.info(f"Cookie de sessão presente: {'session' in request.cookies}")
        logger.info(f"CSRF token em sessão: {session.get('csrf_token', 'Não encontrado')}")
        
        # Verificar quantidade de posts (antes da paginação)
        try:
            with current_app.app_context():
                total_posts = Post.query.count()
                logger.info(f"Total de posts no banco de dados: {total_posts}")
                
                # Listar IDs dos primeiros 5 posts
                first_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
                post_ids = [p.id for p in first_posts]
                logger.info(f"IDs dos primeiros posts: {post_ids}")
                
                # Consultar posts paginados
                logger.info("Executando consulta paginada de posts...")
                posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=5)
                
                logger.info(f"Paginação: page={posts.page}, per_page={posts.per_page}, total={posts.total}, pages={posts.pages}")
                logger.info(f"Itens retornados: {len(posts.items)}")
                
                # Renderizar template
                logger.info("Renderizando template 'public/index.html'")
                return render_template('public/index.html', posts=posts)
        except Exception as query_err:
            logger.error(f"ERRO NA CONSULTA: {str(query_err)}")
            logger.exception("Detalhes do erro na consulta:")
            raise  # Re-lançar para ser capturado pelo try/except externo
            
    except Exception as e:
        # Imprimir erro detalhado para debug
        logger.error(f"ERRO NA RENDERIZAÇÃO DA PÁGINA INICIAL: {str(e)}")
        logger.exception("Detalhes completos do erro:")
        
        # Tentar renderizar uma página mínima com informações do erro
        return render_template('errors/500.html', error=str(e)), 500

@main_bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Verificar se é o post 4 e usar a URL específica
    if post.id == 4:
        post.image_url = "https://img.freepik.com/free-photo/side-view-couple-holding-each-other_23-2148735555.jpg?t=st=1742409398~exp=1742412998~hmac=59e342a62de1c61aedc5a53c00356ab4406ded130e98eca884480d2d68360910&w=900"
        db.session.commit()
    # Verificar se a imagem do post existe, caso contrário, usar placeholder
    elif not post.image_url or not post.image_url.strip() or (not post.image_url.startswith(('http://', 'https://')) and post.image_url.startswith('/static/')):
        # Tentar garantir que mesmo URLs locais funcionem
        static_path = os.path.join('app', post.image_url[1:] if post.image_url.startswith('/') else '')
        if not os.path.exists(static_path):
            post.image_url = 'https://via.placeholder.com/1200x400?text=Post+' + str(post.id)
    
    # Verificar se o post é premium e se o usuário NÃO tem acesso premium
    can_access_premium = current_user.is_authenticated and (current_user.is_premium or current_user.is_admin)
    
    if post.premium_only and not can_access_premium:
        flash('This content is exclusive for premium users.', 'info')
    
    # Obter os últimos 4 posts (diferentes do atual) para exibir no final da página
    recent_posts = Post.query.filter(
        Post.id != post_id
    ).order_by(Post.created_at.desc()).limit(4).all()
    
    # Inicializar formulário de comentário
    form = CommentForm()
    
    # Processar envio de comentário
    if form.validate_on_submit():
        if current_user.is_authenticated:
            comment = Comment(
                content=form.content.data,
                author=current_user,
                post=post,
                approved=current_user.is_admin  # Aprovação automática para admins
            )
            db.session.add(comment)
            db.session.commit()
            
            # Verifica se é uma requisição AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Your comment has been submitted'})
            
            # Método tradicional com redirecionamento (fallback)
            if current_user.is_admin:
                flash('Your comment has been published.', 'success')
            else:
                flash('Your comment has been submitted.', 'info')
            return redirect(url_for('main.post', post_id=post.id))
        else:
            # Verifica se é uma requisição AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'You need to log in to comment.'})
            
            flash('You need to log in to comment.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
    
    # Obter comentários aprovados para o post
    comments = Comment.query.filter_by(post_id=post.id, approved=True).order_by(Comment.created_at.desc()).all()
    
    return render_template('public/post.html', post=post, recent_posts=recent_posts, form=form, comments=comments)

@main_bp.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'You need to log in to comment.'})
        
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            author=current_user,
            post=post,
            approved=current_user.is_admin  # Aprovação automática para admins
        )
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Your comment has been submitted'})
    
    return jsonify({'success': False, 'message': 'An error occurred while processing your comment'})

@main_bp.route('/posts')
def all_posts():
    """
    Lista todos os posts com opção de filtrar por tipo (gratuito ou premium)
    e ordenar por data ou tempo de leitura
    """
    page = request.args.get('page', 1, type=int)
    post_type = request.args.get('type', 'all')  # all, free, premium
    sort_by = request.args.get('sort', 'recent')  # recent, read_time_asc, read_time_desc
    
    # Filtrar baseado no tipo selecionado
    query = Post.query
    
    if post_type == 'free':
        query = query.filter_by(premium_only=False)
    elif post_type == 'premium':
        query = query.filter_by(premium_only=True)
    
    # Ordenar baseado no parâmetro sort_by
    if sort_by == 'recent':
        query = query.order_by(Post.created_at.desc())
    elif sort_by == 'read_time_asc':
        # Não podemos ordenar diretamente pelo tempo de leitura, pois é calculado dinamicamente
        # Então usamos o comprimento do conteúdo como estimativa
        query = query.order_by(db.func.length(Post.content).asc())
    elif sort_by == 'read_time_desc':
        query = query.order_by(db.func.length(Post.content).desc())
    else:
        # Padrão: ordenar por data (mais recentes)
        query = query.order_by(Post.created_at.desc())
    
    posts = query.paginate(
        page=page, per_page=10, error_out=False)
    
    # Obter contagem para os diferentes tipos de posts
    posts_count = {
        'all': Post.query.count(),
        'free': Post.query.filter_by(premium_only=False).count(),
        'premium': Post.query.filter_by(premium_only=True).count()
    }
    
    return render_template('public/all_posts.html', 
                          posts=posts, 
                          active_filter=post_type,
                          active_sort=sort_by,
                          posts_count=posts_count,
                          title="All Posts")

@main_bp.route('/coaching')
def coaching():
    """Render the coaching page."""
    return render_template('public/coaching.html')

@main_bp.route('/teste-de-reconquista')
def teste_de_reconquista():
    """Render the reconquest test page."""
    return render_template('public/coaching.html')

@main_bp.route('/enviar-teste', methods=['POST'])
def enviar_teste():
    """Processa o envio do teste de reconquista e envia para o webhook externo."""
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            form_data = request.json
            
            # Log dos dados recebidos
            print(f"Dados do teste recebidos: {form_data}")
            
            # URL do webhook
            webhook_url = 'https://primary-production-eefe.up.railway.app/webhook/5d75cf8b-dbf8-4be6-afdc-25bc764cc55c'
            
            # Enviar dados para o webhook externo
            response = requests.post(
                webhook_url,
                json=form_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Verificar resposta
            if response.ok:
                try:
                    # Tentar processar a resposta como JSON
                    result = response.json()
                    return jsonify({'success': True, 'data': result})
                except:
                    # Se a resposta não for JSON, retornar sucesso simples
                    return jsonify({'success': True, 'message': 'Dados enviados com sucesso'})
            else:
                return jsonify({
                    'success': False, 
                    'message': f'Erro no webhook: {response.status_code} - {response.text}'
                }), 500
                
        except Exception as e:
            print(f"Erro ao processar teste: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': False, 'message': 'Método não permitido'}), 405

@main_bp.route('/premium')
def premium_subscription():
    """Página para mostrar informações sobre a assinatura premium"""
    return render_template('public/premium.html') 