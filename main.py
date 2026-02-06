"""
Sistema NEV USP - Cadastro de Colaboradores
Versão 2.8 (Com alterações solicitadas)
Autor: NEV USP
Versão: 2.8 (Corrigido e Otimizado - 2026)
"""

# ============================================================================
# IMPORTAÇÕES ORGANIZADAS
# ============================================================================
import os
import sys
import re
import csv
import json
import getpass
import logging
from datetime import datetime, date, timedelta, time
from functools import wraps
from io import BytesIO, StringIO
from typing import Optional, Union
from logging.handlers import RotatingFileHandler

# Flask e Extensões
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, send_file, session, Response
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, func, desc

# ============================================================================
# CONFIGURAÇÃO DA APLICAÇÃO OTIMIZADA
# ============================================================================

# Detecção de ambiente simplificada
IS_PYTHONANYWHERE = 'PYTHONANYWHERE_DOMAIN' in os.environ

# Configuração de diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

app = Flask(__name__)

# Configurações básicas
app.config['ENV'] = 'production' if IS_PYTHONANYWHERE else 'development'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sistema-nev-usp-2026-stability-key')
app.config['DEBUG'] = not IS_PYTHONANYWHERE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PER_PAGE'] = 20
app.config['SESSION_COOKIE_SECURE'] = IS_PYTHONANYWHERE
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ============================================================================
# CONFIGURAÇÃO DO BANCO DE DADOS PARA RAILWAY/SUPABASE
# ============================================================================

# Obter DATABASE_URL do ambiente (Railway/Supabase)
DATABASE_URL = os.environ.get('DATABASE_URL')

# Se tiver DATABASE_URL, usar PostgreSQL (Railway/Supabase)
if DATABASE_URL:
    # Substituir início da URL se for necessário
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
    }
    print(f"✅ Usando PostgreSQL (Supabase/Railway)")
    
# Caso contrário, usar SQLite local (desenvolvimento)
else:
    db_path = os.path.join(DATA_DIR, 'nev.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path.replace('\\', '/')
    print(f"✅ Usando SQLite local: {db_path}")

app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============================================================================
# EXTENSÕES
# ============================================================================
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# ============================================================================
# FUNÇÕES DE APOIO OTIMIZADAS (do v2.6)
# ============================================================================
def validar_cpf(cpf: str) -> bool:
    """Validação eficiente de CPF"""
    cpf = ''.join(filter(str.isdigit, str(cpf)))
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(i))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[i]):
            return False
    return True

def formatar_cpf(cpf: str) -> str:
    """Formata CPF de forma eficiente"""
    c = ''.join(filter(str.isdigit, str(cpf)))
    return f'{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}' if len(c) == 11 else c

def formatar_telefone(tel: str) -> str:
    """Formata telefone brasileiro"""
    if not tel:
        return ""
    t = re.sub(r'\D', '', str(tel))
    if len(t) == 11:
        return f'({t[:2]}) {t[2:7]}-{t[7:]}'
    if len(t) == 10:
        return f'({t[:2]}) {t[2:6]}-{t[6:]}'
    return tel

def gerar_matricula() -> str:
    """Geração otimizada de matrícula"""
    ano = datetime.now().year
    try:
        ultimo = Colaborador.query.filter(
            Colaborador.matricula.like(f'NEV{ano}%')
        ).order_by(Colaborador.id.desc()).first()
        num = int(ultimo.matricula[7:]) + 1 if ultimo and ultimo.matricula else 1
        return f'NEV{ano}{num:04d}'
    except Exception:
        return f'NEV{ano}{int(datetime.now().timestamp()) % 1000:04d}'

def sanitize_input(texto: Optional[str]) -> Optional[str]:
    """Sanitização eficiente contra XSS"""
    if not texto or not isinstance(texto, str):
        return texto
    texto = re.sub(r'<script.*?>.*?</script>', '', texto, flags=re.IGNORECASE | re.DOTALL)
    return texto.strip()

def registrar_log(acao: str, modulo: Optional[str] = None,
                 detalhes: Optional[str] = None, nivel: str = 'INFO') -> bool:
    """Registro de log otimizado"""
    try:
        log = Log(
            usuario_id=current_user.id if current_user.is_authenticated else None,
            usuario_nome=current_user.nome_completo if current_user.is_authenticated else 'Sistema',
            acao=acao,
            modulo=modulo,
            detalhes=str(detalhes)[:500] if detalhes else None,
            ip_address=request.remote_addr if request else '',
            user_agent=request.user_agent.string[:200] if request and request.user_agent else "",
            nivel=nivel
        )
        db.session.add(log)
        db.session.commit()
        return True
    except Exception as e:
        app.logger.error(f'Erro ao registrar log: {e}')
        db.session.rollback()
        return False

def calcular_idade(data_nascimento: Optional[date]) -> Optional[int]:
    """Cálculo eficiente de idade (mantida por compatibilidade)"""
    if not data_nascimento:
        return None
    hoje = date.today()
    return hoje.year - data_nascimento.year - (
        (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day)
    )

# ============================================================================
# DECORATORS OTIMIZADOS (do v2.6)
# ============================================================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.nivel_acesso != 'admin':
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def supervisor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.nivel_acesso not in ['admin', 'supervisor']:
            flash('Acesso restrito a supervisores e administradores.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# MODELOS COMPLETOS (mantendo todos os campos)
# ============================================================================
class User(UserMixin, db.Model):
    """Modelo de usuário otimizado"""
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(200), nullable=False)
    nome_completo = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    nivel_acesso = db.Column(db.String(20), default='colaborador')
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime)
    senha_alterada = db.Column(db.Boolean, default=False)

    def set_password(self, password: str) -> None:
        self.senha_hash = generate_password_hash(password)
        self.senha_alterada = True

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.senha_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Colaborador(db.Model):
    """Modelo completo de colaborador com todos os campos"""
    __tablename__ = 'colaboradores'

    # Identificação
    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(20), unique=True, index=True)
    nome_completo = db.Column(db.String(150), nullable=False, index=True)
    nome_social = db.Column(db.String(100))
    rg = db.Column(db.String(20))
    cpf = db.Column(db.String(14), unique=True, nullable=False, index=True)
    data_nascimento = db.Column(db.Date)

    # Contato
    email_institucional = db.Column(db.String(120), nullable=False, index=True)
    celular = db.Column(db.String(20), nullable=False)
    whatsapp = db.Column(db.Boolean, default=False)

    # Endereço (ATUALIZADO: adicionado complemento)
    cep = db.Column(db.String(10))
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(100))  # NOVO CAMPO
    bairro = db.Column(db.String(50))
    cidade = db.Column(db.String(50))
    estado = db.Column(db.String(2))

    # Dados profissionais
    data_ingresso = db.Column(db.Date, nullable=False)
    tipo_vinculo = db.Column(db.String(50), nullable=False)
    programa_projeto = db.Column(db.String(100))
    departamento = db.Column(db.String(100))  # Linha de Pesquisa/Departamento
    lotacao = db.Column(db.String(100))  # Mantido no banco, mas não usado nos formulários

    # Horários
    dias_presenciais = db.Column(db.String(100))
    horario_entrada = db.Column(db.Time)
    horario_saida = db.Column(db.Time)
    carga_horaria_semanal = db.Column(db.Integer)

    # Imprensa
    atende_imprensa = db.Column(db.Boolean, default=False)
    tipos_imprensa = db.Column(db.String(200))  # Tipos de veículos
    assuntos_especializacao = db.Column(db.Text)  # Temas de especialidade
    disponibilidade_contato = db.Column(db.String(100))  # Mantido no banco, mas não usado nos formulários

    # Acadêmico/Profissional
    curriculo_lattes = db.Column(db.String(200))
    orcid = db.Column(db.String(50))
    linkedin = db.Column(db.String(200))
    observacoes = db.Column(db.Text)

    # Status e metadados
    status = db.Column(db.String(20), default='Ativo', index=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cadastrado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    atualizado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    # Relacionamentos
    cadastrado_por_usuario = db.relationship('User', foreign_keys=[cadastrado_por])
    atualizado_por_usuario = db.relationship('User', foreign_keys=[atualizado_por])

    @property
    def idade(self) -> Optional[int]:
        return calcular_idade(self.data_nascimento)

    @property
    def tempo_na_instituicao(self) -> Optional[int]:
        if self.data_ingresso:
            hoje = date.today()
            return hoje.year - self.data_ingresso.year - (
                (hoje.month, hoje.day) < (self.data_ingresso.month, self.data_ingresso.day)
            )
        return None

    def __repr__(self):
        return f'<Colaborador {self.nome_completo} ({self.matricula})>'

class Log(db.Model):
    """Modelo de log otimizado"""
    __tablename__ = 'logs_sistema'
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    usuario_id = db.Column(db.Integer)
    usuario_nome = db.Column(db.String(100))
    acao = db.Column(db.String(200), nullable=False)
    modulo = db.Column(db.String(50))
    detalhes = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.Text)
    nivel = db.Column(db.String(10), default='INFO')

    def __repr__(self):
        return f'<Log {self.acao} at {self.data_hora}>'

class Observacao(db.Model):
    """Modelo de observação"""
    __tablename__ = 'observacoes_colaborador'
    id = db.Column(db.Integer, primary_key=True)
    colaborador_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_nome = db.Column(db.String(100))
    colaborador = db.relationship('Colaborador', backref=db.backref('historico_observacoes', lazy=True, cascade="all, delete-orphan"))

# ============================================================================
# CONTEXT PROCESSOR (ATUALIZADO)
# ============================================================================
@app.context_processor
def inject_globais():
    return {
        'datetime': datetime,
        'date': date,
        'timedelta': timedelta,
        'now': datetime.now,
        'current_user': current_user,
        'app_name': 'Sistema NEV USP',
        'app_version': '2.8',
        'ano_atual': datetime.now().year,
        'formatar_cpf': formatar_cpf,
        'formatar_telefone': formatar_telefone,
        'validar_cpf': validar_cpf,
        # Removida a função buscar_endereco_por_cep do contexto global
    }

# ============================================================================
# CONFIGURAÇÃO DO LOGIN MANAGER
# ============================================================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================================================
# ROTAS DE AUTENTICAÇÃO OTIMIZADAS
# ============================================================================
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        senha = request.form.get('senha', '')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(senha):
            if not user.ativo:
                flash('Usuário desativado. Contate o administrador.', 'warning')
                return render_template('login.html')

            login_user(user)
            user.ultimo_login = datetime.utcnow()
            db.session.commit()

            registrar_log('Login realizado', 'Autenticação')
            flash('Login realizado com sucesso!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))

        flash('Usuário ou senha incorretos', 'danger')
        registrar_log('Tentativa de login falhou', 'Autenticação', nivel='WARNING')

    return render_template('login.html')

@app.route('/alterar-senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')

        if not current_user.check_password(senha_atual):
            flash('Senha atual incorreta.', 'danger')
            return render_template('alterar_senha.html')

        if nova_senha != confirmar_senha:
            flash('As novas senhas não coincidem.', 'danger')
            return render_template('alterar_senha.html')

        if len(nova_senha) < 8:
            flash('A senha deve ter pelo menos 8 caracteres.', 'danger')
            return render_template('alterar_senha.html')

        current_user.set_password(nova_senha)
        db.session.commit()

        registrar_log('Senha alterada', 'Autenticação')
        flash('✅ Senha alterada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('alterar_senha.html')

@app.route('/logout')
@login_required
def logout():
    registrar_log('Logout realizado', 'Autenticação')
    logout_user()
    flash('Você saiu do sistema com sucesso.', 'info')
    return redirect(url_for('login'))

# ============================================================================
# ROTA API PARA BUSCAR CEP (SIMPLIFICADA)
# ============================================================================
@app.route('/api/buscar-cep/<cep>')
@login_required
def api_buscar_cep(cep):
    """API simplificada para buscar endereço por CEP (apenas formatação)"""
    app.logger.info(f'Formatando CEP: {cep}')
    try:
        # Remove caracteres não numéricos
        cep_limpo = re.sub(r'\D', '', cep)
        
        if len(cep_limpo) != 8:
            return jsonify({
                'success': False,
                'message': 'CEP inválido. Digite 8 dígitos.'
            }), 400
        
        # Formata o CEP apenas (xxxxx-xxx)
        cep_formatado = f'{cep_limpo[:5]}-{cep_limpo[5:]}'
        
        # Retorna apenas o CEP formatado, sem dados de endereço
        return jsonify({
            'success': True,
            'cep': cep_formatado,
            'message': 'CEP formatado. Preencha os dados de endereço manualmente.'
        })
        
    except Exception as e:
        app.logger.error(f'Erro ao formatar CEP {cep}: {e}')
        return jsonify({
            'success': False,
            'message': f'Erro ao processar CEP: {str(e)}'
        }), 500

# ============================================================================
# DASHBOARD OTIMIZADO
# ============================================================================
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        total_colabs = Colaborador.query.count()
        total_ativos = Colaborador.query.filter_by(status='Ativo').count()
        total_imprensa = Colaborador.query.filter_by(atende_imprensa=True).count()
        novos_cadastros = Colaborador.query.filter(
            Colaborador.data_cadastro >= (datetime.utcnow() - timedelta(days=7))
        ).count()

        vinculos = db.session.query(
            Colaborador.tipo_vinculo,
            func.count(Colaborador.id).label('total')
        ).group_by(Colaborador.tipo_vinculo).all()

        atividades = Log.query.order_by(Log.data_hora.desc()).limit(10).all()

        p_ativos = (total_ativos / total_colabs * 100) if total_colabs else 0
        p_imprensa = (total_imprensa / total_colabs * 100) if total_colabs else 0

        return render_template('dashboard.html',
            total_colabs=total_colabs,
            total_ativos=total_ativos,
            total_imprensa=total_imprensa,
            novos_cadastros=novos_cadastros,
            vinculos=vinculos,
            atividades=atividades,
            percentual_ativos=round(p_ativos, 1),
            percentual_imprensa=round(p_imprensa, 1))

    except Exception as e:
        app.logger.error(f'Erro no dashboard: {e}')
        return render_template('dashboard.html',
            total_colabs=0, total_ativos=0, total_imprensa=0,
            novos_cadastros=0, vinculos=[], atividades=[],
            percentual_ativos=0, percentual_imprensa=0)

# ============================================================================
# ROTAS DE COLABORADORES OTIMIZADAS (ATUALIZADAS)
# ============================================================================
@app.route('/colaboradores')
@login_required
def listar_colaboradores():
    try:
        pagina = request.args.get('pagina', 1, type=int)
        busca = request.args.get('busca', '')
        status = request.args.get('status', '')
        departamento = request.args.get('departamento', '')

        query = Colaborador.query

        if busca:
            search_term = f'%{busca}%'
            query = query.filter(
                or_(
                    Colaborador.nome_completo.ilike(search_term),
                    Colaborador.cpf.ilike(search_term),
                    Colaborador.email_institucional.ilike(search_term),
                    Colaborador.matricula.ilike(search_term)
                )
            )

        if status:
            query = query.filter_by(status=status)

        if departamento:
            query = query.filter_by(departamento=departamento)

        colaboradores = query.order_by(Colaborador.nome_completo).paginate(
            page=pagina, per_page=app.config['PER_PAGE'], error_out=False
        )

        departamentos = db.session.query(Colaborador.departamento).distinct().all()
        departamentos = [d[0] for d in departamentos if d[0]]

        return render_template('colaboradores.html',
            colaboradores=colaboradores,
            busca=busca,
            status=status,
            departamento=departamento,
            departamentos=departamentos)

    except Exception as e:
        app.logger.error(f'Erro ao listar colaboradores: {e}')
        flash('Erro ao carregar lista de colaboradores.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/colaborador/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_colaborador():
    """Cadastro de colaborador em 5 passos (ATUALIZADO)"""

    if request.method == 'POST':
        # Se for uma requisição AJAX para salvar temporariamente os dados
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            acao = request.form.get('acao')

            if acao == 'salvar_passo':
                passo = int(request.form.get('passo', 1))
                dados = {}

                # Coletar dados do passo atual
                if passo == 1:
                    dados['nome_completo'] = request.form.get('nome_completo', '')
                    dados['nome_social'] = request.form.get('nome_social', '')
                    dados['cpf'] = request.form.get('cpf', '')
                    dados['rg'] = request.form.get('rg', '')
                    dados['data_nascimento'] = request.form.get('data_nascimento', '')

                elif passo == 2:
                    dados['email_institucional'] = request.form.get('email_institucional', '')
                    dados['celular'] = request.form.get('celular', '')
                    dados['whatsapp'] = 'whatsapp' in request.form
                    dados['cep'] = request.form.get('cep', '')
                    dados['endereco'] = request.form.get('endereco', '')
                    dados['numero'] = request.form.get('numero', '')
                    dados['complemento'] = request.form.get('complemento', '')  # NOVO CAMPO
                    dados['bairro'] = request.form.get('bairro', '')
                    dados['cidade'] = request.form.get('cidade', '')
                    dados['estado'] = request.form.get('estado', '')

                elif passo == 3:
                    dados['tipo_vinculo'] = request.form.get('tipo_vinculo', '')
                    dados['departamento'] = request.form.get('departamento', '')
                    # dados['lotacao'] = request.form.get('lotacao', '')  # REMOVIDO
                    dados['data_ingresso'] = request.form.get('data_ingresso', '')
                    dados['dias_presenciais'] = ','.join(request.form.getlist('dias_presenciais'))

                elif passo == 4:
                    dados['atende_imprensa'] = 'atende_imprensa' in request.form
                    dados['tipos_imprensa'] = ', '.join(request.form.getlist('tipos_imprensa'))
                    dados['assuntos_especializacao'] = request.form.get('assuntos_especializacao', '')
                    # dados['disponibilidade_contato'] = request.form.get('disponibilidade_contato', '')  # REMOVIDO

                elif passo == 5:
                    dados['curriculo_lattes'] = request.form.get('curriculo_lattes', '')
                    dados['orcid'] = request.form.get('orcid', '')
                    dados['linkedin'] = request.form.get('linkedin', '')
                    dados['observacoes'] = request.form.get('observacoes', '')

                # Salvar na sessão
                session[f'colaborador_passo_{passo}'] = dados

                return jsonify({
                    'success': True,
                    'message': f'Dados do passo {passo} salvos temporariamente'
                })

            elif acao == 'finalizar_cadastro':
                # Coletar todos os dados dos 5 passos
                dados_finais = {}

                for passo in range(1, 6):
                    dados_passo = session.get(f'colaborador_passo_{passo}', {})
                    dados_finais.update(dados_passo)

                try:
                    # Validar CPF
                    cpf = formatar_cpf(dados_finais.get('cpf', '').strip())
                    if not validar_cpf(cpf):
                        return jsonify({
                            'success': False,
                            'message': 'CPF inválido. Por favor, verifique o número.'
                        }), 400

                    if Colaborador.query.filter_by(cpf=cpf).first():
                        return jsonify({
                            'success': False,
                            'message': 'Erro: Este CPF já está cadastrado no sistema.'
                        }), 400

                    # Validar campos obrigatórios
                    if not dados_finais.get('nome_completo'):
                        return jsonify({
                            'success': False,
                            'message': 'Nome completo é obrigatório.'
                        }), 400

                    if not dados_finais.get('email_institucional'):
                        return jsonify({
                            'success': False,
                            'message': 'Email institucional é obrigatório.'
                        }), 400

                    if not dados_finais.get('celular'):
                        return jsonify({
                            'success': False,
                            'message': 'Celular é obrigatório.'
                        }), 400

                    if not dados_finais.get('tipo_vinculo'):
                        return jsonify({
                            'success': False,
                            'message': 'Tipo de vínculo é obrigatório.'
                        }), 400

                    if not dados_finais.get('data_ingresso'):
                        return jsonify({
                            'success': False,
                            'message': 'Data de ingresso é obrigatória.'
                        }), 400

                    # Preparar dados para o banco
                    dados_db = {
                        'nome_completo': sanitize_input(dados_finais.get('nome_completo', '')).title(),
                        'nome_social': sanitize_input(dados_finais.get('nome_social', '')).title(),
                        'rg': sanitize_input(dados_finais.get('rg', '')),
                        'cpf': cpf,
                        'email_institucional': sanitize_input(dados_finais.get('email_institucional', '')).lower(),
                        'celular': formatar_telefone(sanitize_input(dados_finais.get('celular', ''))),
                        'whatsapp': dados_finais.get('whatsapp', False),
                        'tipo_vinculo': dados_finais.get('tipo_vinculo', ''),
                        'departamento': sanitize_input(dados_finais.get('departamento', '')),
                        # 'lotacao': sanitize_input(dados_finais.get('lotacao', '')),  # REMOVIDO
                        'atende_imprensa': dados_finais.get('atende_imprensa', False),
                        'tipos_imprensa': dados_finais.get('tipos_imprensa', ''),
                        'assuntos_especializacao': sanitize_input(dados_finais.get('assuntos_especializacao', '')),
                        # 'disponibilidade_contato': sanitize_input(dados_finais.get('disponibilidade_contato', '')),  # REMOVIDO
                        'curriculo_lattes': sanitize_input(dados_finais.get('curriculo_lattes', '')),
                        'orcid': sanitize_input(dados_finais.get('orcid', '')),
                        'linkedin': sanitize_input(dados_finais.get('linkedin', '')),
                        'observacoes': sanitize_input(dados_finais.get('observacoes', '')),
                        'status': 'Ativo',
                        'cadastrado_por': current_user.id
                    }

                    # Processar datas
                    try:
                        data_ingresso = dados_finais.get('data_ingresso')
                        if data_ingresso:
                            dados_db['data_ingresso'] = datetime.strptime(data_ingresso, '%Y-%m-%d').date()
                    except ValueError:
                        return jsonify({
                            'success': False,
                            'message': 'Data de ingresso inválida.'
                        }), 400

                    try:
                        data_nascimento = dados_finais.get('data_nascimento')
                        if data_nascimento:
                            dados_db['data_nascimento'] = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
                    except ValueError:
                        pass  # Data de nascimento é opcional

                    # Dias presenciais
                    dias_presenciais = dados_finais.get('dias_presenciais', '')
                    if dias_presenciais:
                        dados_db['dias_presenciais'] = dias_presenciais

                    # Endereço (com complemento)
                    dados_db.update({
                        'cep': sanitize_input(dados_finais.get('cep', '')),
                        'endereco': sanitize_input(dados_finais.get('endereco', '')),
                        'numero': sanitize_input(dados_finais.get('numero', '')),
                        'complemento': sanitize_input(dados_finais.get('complemento', '')),  # NOVO CAMPO
                        'bairro': sanitize_input(dados_finais.get('bairro', '')),
                        'cidade': sanitize_input(dados_finais.get('cidade', '')),
                        'estado': sanitize_input(dados_finais.get('estado', '')),
                    })

                    # Gerar matrícula e criar colaborador
                    dados_db['matricula'] = gerar_matricula()
                    colaborador = Colaborador(**dados_db)
                    db.session.add(colaborador)
                    db.session.commit()

                    # Registrar log
                    registrar_log(f'Cadastrou colaborador {colaborador.nome_completo}',
                                'Colaboradores',
                                f'Matrícula: {colaborador.matricula}')

                    # Limpar dados da sessão
                    for passo in range(1, 6):
                        session.pop(f'colaborador_passo_{passo}', None)

                    return jsonify({
                        'success': True,
                        'message': f'✅ Colaborador {colaborador.nome_completo} cadastrado! Matrícula: {colaborador.matricula}',
                        'redirect_url': url_for('ver_colaborador', id=colaborador.id)
                    })

                except Exception as e:
                    db.session.rollback()
                    app.logger.error(f'Erro crítico ao cadastrar colaborador: {str(e)}')
                    return jsonify({
                        'success': False,
                        'message': f'Erro ao processar cadastro: {str(e)}'
                    }), 500

        # Se não for AJAX, processar o formulário tradicional (fallback)
        try:
            vinculo = request.form.get('tipo_vinculo')
            if not vinculo:
                flash('O campo "Tipo de Vínculo" é obrigatório.', 'danger')
                return render_template('colaborador_form.html', dados=request.form)

            cpf = formatar_cpf(request.form.get('cpf', '').strip())
            if not validar_cpf(cpf):
                flash('CPF inválido. Por favor, verifique o número.', 'danger')
                return render_template('colaborador_form.html', dados=request.form)

            if Colaborador.query.filter_by(cpf=cpf).first():
                flash('Erro: Este CPF já está cadastrado no sistema.', 'danger')
                return render_template('colaborador_form.html', dados=request.form)

            dados = {
                'nome_completo': sanitize_input(request.form.get('nome_completo', '')).title(),
                'nome_social': sanitize_input(request.form.get('nome_social', '')).title(),
                'rg': sanitize_input(request.form.get('rg', '')),
                'cpf': cpf,
                'email_institucional': sanitize_input(request.form.get('email_institucional', '')).lower(),
                'celular': formatar_telefone(sanitize_input(request.form.get('celular', ''))),
                'whatsapp': 'whatsapp' in request.form,
                'tipo_vinculo': vinculo,
                'departamento': sanitize_input(request.form.get('departamento', '')),
                # 'lotacao': sanitize_input(request.form.get('lotacao', '')),  # REMOVIDO
                'atende_imprensa': 'atende_imprensa' in request.form,
                'tipos_imprensa': ', '.join(request.form.getlist('tipos_imprensa')),
                'assuntos_especializacao': sanitize_input(request.form.get('assuntos_especializacao', '')),
                # 'disponibilidade_contato': sanitize_input(request.form.get('disponibilidade_contato', '')),  # REMOVIDO
                'curriculo_lattes': sanitize_input(request.form.get('curriculo_lattes', '')),
                'orcid': sanitize_input(request.form.get('orcid', '')),
                'linkedin': sanitize_input(request.form.get('linkedin', '')),
                'observacoes': sanitize_input(request.form.get('observacoes', '')),
                'status': 'Ativo',
                'cadastrado_por': current_user.id
            }

            # Processar datas
            try:
                data_ingresso = request.form.get('data_ingresso')
                if data_ingresso:
                    dados['data_ingresso'] = datetime.strptime(data_ingresso, '%Y-%m-%d').date()
                else:
                    flash('O campo "Data de Ingresso" é obrigatório.', 'danger')
                    return render_template('colaborador_form.html', dados=request.form)
            except ValueError:
                flash('Data de ingresso inválida.', 'danger')
                return render_template('colaborador_form.html', dados=request.form)

            try:
                data_nascimento = request.form.get('data_nascimento')
                if data_nascimento:
                    dados['data_nascimento'] = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
            except ValueError:
                pass

            # Dias presenciais
            dias_presenciais = request.form.getlist('dias_presenciais')
            if dias_presenciais:
                dados['dias_presenciais'] = ','.join(dias_presenciais)

            # Endereço (com complemento)
            dados.update({
                'cep': sanitize_input(request.form.get('cep', '')),
                'endereco': sanitize_input(request.form.get('endereco', '')),
                'numero': sanitize_input(request.form.get('numero', '')),
                'complemento': sanitize_input(request.form.get('complemento', '')),  # NOVO CAMPO
                'bairro': sanitize_input(request.form.get('bairro', '')),
                'cidade': sanitize_input(request.form.get('cidade', '')),
                'estado': sanitize_input(request.form.get('estado', '')),
            })

            dados['matricula'] = gerar_matricula()
            colaborador = Colaborador(**dados)
            db.session.add(colaborador)
            db.session.commit()

            registrar_log(f'Cadastrou colaborador {colaborador.nome_completo}',
                          'Colaboradores',
                          f'Matrícula: {colaborador.matricula}')
            flash(f'✅ Colaborador {colaborador.nome_completo} cadastrado! Matrícula: {colaborador.matricula}', 'success')
            return redirect(url_for('ver_colaborador', id=colaborador.id))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Erro crítico ao cadastrar colaborador: {str(e)}')
            flash(f'Erro ao processar cadastro: {str(e)}', 'danger')
            return render_template('colaborador_form.html', dados=request.form)

    # GET request - mostrar formulário em etapas
    return render_template('colaborador_form_etapas.html')

@app.route('/colaborador/<int:id>')
@login_required
def ver_colaborador(id):
    colaborador = Colaborador.query.get_or_404(id)
    historico = Log.query.filter(
        or_(
            Log.detalhes.like(f"%{colaborador.matricula}%"),
            Log.detalhes.like(f"%{colaborador.cpf}%"),
            Log.acao.like(f"%{colaborador.nome_completo}%")
        )
    ).order_by(Log.data_hora.desc()).limit(10).all()
    return render_template('colaborador_view.html',
                           colaborador=colaborador,
                           historico=historico)

@app.route('/colaborador/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_colaborador(id):
    colaborador = Colaborador.query.get_or_404(id)

    if request.method == 'POST':
        try:
            cpf_form = request.form.get('cpf', '').strip()
            if cpf_form:
                novo_cpf = formatar_cpf(cpf_form)
                if novo_cpf != colaborador.cpf:
                    if not validar_cpf(novo_cpf) or Colaborador.query.filter(
                        Colaborador.cpf == novo_cpf, Colaborador.id != id
                    ).first():
                        flash('CPF inválido ou já em uso.', 'danger')
                        return render_template('colaborador_edit.html', colaborador=colaborador)
                    colaborador.cpf = novo_cpf

            colaborador.nome_completo = sanitize_input(request.form.get('nome_completo', '')).title()
            colaborador.nome_social = sanitize_input(request.form.get('nome_social', '')).title()
            colaborador.rg = sanitize_input(request.form.get('rg', ''))
            colaborador.email_institucional = sanitize_input(request.form.get('email_institucional', '')).lower()
            colaborador.celular = formatar_telefone(sanitize_input(request.form.get('celular', '')))
            colaborador.whatsapp = 'whatsapp' in request.form

            try:
                data_ingresso = request.form.get('data_ingresso')
                if data_ingresso:
                    colaborador.data_ingresso = datetime.strptime(data_ingresso, '%Y-%m-%d').date()
            except ValueError:
                flash('Data de ingresso inválida.', 'danger')

            try:
                data_nascimento = request.form.get('data_nascimento')
                if data_nascimento:
                    colaborador.data_nascimento = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
            except ValueError:
                pass

            colaborador.tipo_vinculo = request.form.get('tipo_vinculo')
            colaborador.departamento = sanitize_input(request.form.get('departamento', ''))
            # colaborador.lotacao = sanitize_input(request.form.get('lotacao', ''))  # REMOVIDO

            # Dias presenciais
            dias_presenciais = request.form.getlist('dias_presenciais')
            if dias_presenciais:
                colaborador.dias_presenciais = ','.join(dias_presenciais)
            else:
                colaborador.dias_presenciais = None

            colaborador.atende_imprensa = 'atende_imprensa' in request.form
            colaborador.tipos_imprensa = ', '.join(request.form.getlist('tipos_imprensa'))
            colaborador.assuntos_especializacao = sanitize_input(request.form.get('assuntos_especializacao', ''))
            # colaborador.disponibilidade_contato = sanitize_input(request.form.get('disponibilidade_contato', ''))  # REMOVIDO

            # Campos acadêmicos
            colaborador.curriculo_lattes = sanitize_input(request.form.get('curriculo_lattes', ''))
            colaborador.orcid = sanitize_input(request.form.get('orcid', ''))
            colaborador.linkedin = sanitize_input(request.form.get('linkedin', ''))
            colaborador.observacoes = sanitize_input(request.form.get('observacoes', ''))
            colaborador.status = request.form.get('status', 'Ativo')

            colaborador.atualizado_por = current_user.id
            colaborador.data_atualizacao = datetime.utcnow()

            colaborador.cep = sanitize_input(request.form.get('cep', ''))
            colaborador.endereco = sanitize_input(request.form.get('endereco', ''))
            colaborador.numero = sanitize_input(request.form.get('numero', ''))
            colaborador.complemento = sanitize_input(request.form.get('complemento', ''))  # NOVO CAMPO
            colaborador.bairro = sanitize_input(request.form.get('bairro', ''))
            colaborador.cidade = sanitize_input(request.form.get('cidade', ''))
            colaborador.estado = sanitize_input(request.form.get('estado', ''))

            db.session.commit()

            registrar_log(f'Editou colaborador {colaborador.nome_completo}',
                         'Colaboradores',
                         f'ID: {id}, Matrícula: {colaborador.matricula}')

            flash('✅ Colaborador atualizado com sucesso!', 'success')
            return redirect(url_for('ver_colaborador', id=id))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Erro ao editar colaborador {id}: {e}')
            flash(f'Erro ao atualizar colaborador: {str(e)}', 'danger')

    return render_template('colaborador_edit.html', colaborador=colaborador)

@app.route('/colaborador/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_colaborador(id):
    colaborador = Colaborador.query.get_or_404(id)

    try:
        nome = colaborador.nome_completo
        matricula = colaborador.matricula

        colaborador.status = 'Inativo'
        colaborador.data_atualizacao = datetime.utcnow()
        colaborador.atualizado_por = current_user.id

        db.session.commit()

        registrar_log(f'Desativou colaborador {nome}',
                     'Colaboradores',
                     f'Matrícula: {matricula}, ID: {id}')
        flash('✅ Colaborador desativado com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erro ao desativar colaborador {id}: {e}')
        flash(f'Erro ao desativar colaborador: {str(e)}', 'danger')

    return redirect(url_for('listar_colaboradores'))

@app.route('/colaborador/<int:id>/observacao', methods=['POST'])
@login_required
def adicionar_observacao(id):
    texto = request.form.get('observacao_texto')
    if texto:
        nova_obs = Observacao(
            colaborador_id=id,
            texto=sanitize_input(texto),
            usuario_nome=current_user.nome_completo
        )
        db.session.add(nova_obs)
        db.session.commit()
        registrar_log(f"Adicionou observação ao colaborador ID {id}", "Observações", detalhes=texto)
        flash('Observação adicionada!', 'success')
    return redirect(url_for('ver_colaborador', id=id))

@app.route('/observacao/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_observacao(id):
    obs = Observacao.query.get_or_404(id)
    colab_id = obs.colaborador_id
    detalhe_removido = obs.texto

    db.session.delete(obs)
    db.session.commit()

    registrar_log(f"Excluiu observação do colaborador ID {colab_id}", "Observações", detalhes=detalhe_removido)
    flash('Observação removida e registrada no log.', 'info')
    return redirect(url_for('ver_colaborador', id=colab_id))

# ============================================================================
# EXPORTAÇÃO E RELATÓRIOS
# ============================================================================
@app.route('/exportar_colaboradores_csv')
@login_required
def exportar_colaboradores_csv():
    """Exportação rápida de CSV"""
    try:
        colabs = Colaborador.query.all()
        output = StringIO()
        output.write('\ufeff')
        writer = csv.writer(output, delimiter=';')
        writer.writerow(['Matrícula', 'Nome', 'CPF', 'Vínculo', 'Status', 'Departamento', 'Email Principal'])
        for c in colabs:
            writer.writerow([c.matricula, c.nome_completo, c.cpf, c.tipo_vinculo, c.status, c.departamento, c.email_institucional])
        output.seek(0)
        return Response(output.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=export_nev.csv"})
    except Exception as e:
        app.logger.error(f'Erro ao exportar CSV: {e}')
        flash('Erro ao exportar dados.', 'danger')
        return redirect(url_for('listar_colaboradores'))

@app.route('/relatorios', methods=['GET', 'POST'])
@login_required
@supervisor_required
def relatorios():
    """Relatórios personalizados"""

    mapeamento_campos = {
        'matricula': 'Matrícula',
        'nome_completo': 'Nome Completo',
        'nome_social': 'Nome Social',
        'cpf': 'CPF',
        'rg': 'RG',
        'data_nascimento': 'Data de Nascimento',
        'email_institucional': 'Email Principal',
        'celular': 'Celular',
        'whatsapp': 'WhatsApp',
        'tipo_vinculo': 'Vínculo',
        'departamento': 'Linha de Pesquisa/Departamento',
        'lotacao': 'Lotação',
        'data_ingresso': 'Data de Ingresso',
        'status': 'Status',
        'atende_imprensa': 'Atende Imprensa',
        'tipos_imprensa': 'Tipos de Veículos de Imprensa',
        'assuntos_especializacao': 'Temas de Especialidade',
        'orcid': 'ORCID',
        'linkedin': 'LinkedIn',
        'curriculo_lattes': 'Currículo Lattes'
    }

    if request.method == 'POST':
        try:
            f_vinculo = request.form.get('filtro_vinculo')
            f_dep = request.form.get('filtro_departamento')
            f_status = request.form.get('filtro_status')
            campos_selecionados = request.form.getlist('campos')

            if not campos_selecionados:
                flash('Selecione pelo menos um campo para o relatório.', 'warning')
                return redirect(url_for('relatorios'))

            query = Colaborador.query

            if f_vinculo and f_vinculo != 'todos':
                query = query.filter(Colaborador.tipo_vinculo == f_vinculo)
            if f_dep and f_dep != 'todos':
                query = query.filter(Colaborador.departamento == f_dep)
            if f_status and f_status != 'todos':
                query = query.filter(Colaborador.status == f_status)

            colaboradores = query.all()

            output = StringIO()
            output.write('\ufeff')
            writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)

            header = [mapeamento_campos.get(c, c) for c in campos_selecionados]
            writer.writerow(header)

            for colab in colaboradores:
                linha = []
                for campo in campos_selecionados:
                    valor = getattr(colab, campo, '')

                    if valor is None:
                        valor = ''
                    elif isinstance(valor, bool):
                        valor = 'Sim' if valor else 'Não'
                    elif isinstance(valor, (datetime, date)):
                        valor = valor.strftime('%d/%m/%Y')
                    elif isinstance(valor, time):
                        valor = valor.strftime('%H:%M')

                    linha.append(valor)
                writer.writerow(linha)

            output.seek(0)
            filename = f"relatorio_nev_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": "text/csv; charset=utf-8"
                }
            )

        except Exception as e:
            app.logger.error(f'Erro ao gerar relatório: {str(e)}')
            flash(f'Erro ao processar o relatório: {str(e)}', 'danger')
            return redirect(url_for('relatorios'))

    departamentos = db.session.query(Colaborador.departamento).distinct().all()
    vinculos = db.session.query(Colaborador.tipo_vinculo).distinct().all()

    lista_deps = sorted([d[0] for d in departamentos if d[0]])
    lista_vincs = sorted([v[0] for v in vinculos if v[0]])

    categorias_campos = {
        'Identificação': [
            ('matricula', 'Matrícula'), ('nome_completo', 'Nome Completo'),
            ('nome_social', 'Nome Social'), ('cpf', 'CPF'), ('rg', 'RG'),
            ('data_nascimento', 'Data de Nascimento')
        ],
        'Contato': [
            ('email_institucional', 'Email Principal'),
            ('celular', 'Celular'), ('whatsapp', 'WhatsApp')
        ],
        'Institucional': [
            ('tipo_vinculo', 'Tipo de Vínculo'), ('departamento', 'Linha de Pesquisa/Departamento'),
            ('lotacao', 'Lotação'), ('data_ingresso', 'Data de Ingresso'), ('status', 'Status')
        ],
        'Imprensa': [
            ('atende_imprensa', 'Atende Imprensa'), ('tipos_imprensa', 'Tipos de Veículos'),
            ('assuntos_especializacao', 'Temas de Especialidade')
        ],
        'Acadêmico': [
            ('orcid', 'ORCID'), ('linkedin', 'LinkedIn'), ('curriculo_lattes', 'Currículo Lattes')
        ]
    }

    return render_template('relatorios.html',
                           departamentos=lista_deps,
                           vinculos=lista_vincs,
                           categorias_campos=categorias_campos)

# ============================================================================
# ROTAS DE CONFIGURAÇÕES
# ============================================================================
@app.route('/configuracoes')
@login_required
@admin_required
def configuracoes():
    return render_template('configuracoes.html', title='Configurações')

@app.route('/api/info-sistema')
@login_required
def api_info_sistema():
    try:
        total_colaboradores = Colaborador.query.count()
        ativos_colaboradores = Colaborador.query.filter_by(status='Ativo').count()
        imprensa_colaboradores = Colaborador.query.filter_by(atende_imprensa=True).count()
        data_limite = datetime.utcnow() - timedelta(days=30)
        novos_colaboradores = Colaborador.query.filter(
            Colaborador.data_cadastro >= data_limite
        ).count()

        return jsonify({
            'success': True,
            'data': {
                'total_colaboradores': total_colaboradores,
                'ativos_colaboradores': ativos_colaboradores,
                'imprensa_colaboradores': imprensa_colaboradores,
                'novos_colaboradores': novos_colaboradores,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        app.logger.error(f'Erro na API info-sistema: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ROTAS DE GERENCIAMENTO DE USUÁRIOS
# ============================================================================
@app.route('/usuarios')
@login_required
@admin_required
def listar_usuarios():
    try:
        pagina = request.args.get('pagina', 1, type=int)
        busca = request.args.get('busca', '')
        nivel = request.args.get('nivel', '')

        query = User.query

        if busca:
            search_term = f'%{busca}%'
            query = query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.nome_completo.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )

        if nivel:
            query = query.filter_by(nivel_acesso=nivel)

        usuarios = query.order_by(User.nome_completo).paginate(
            page=pagina, per_page=app.config['PER_PAGE'], error_out=False
        )

        return render_template('usuarios.html',
            usuarios=usuarios,
            busca=busca,
            nivel=nivel,
            title='Gerenciar Usuários')

    except Exception as e:
        app.logger.error(f'Erro ao listar usuários: {e}')
        flash('Erro ao carregar lista de usuários.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/usuario/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo_usuario():
    if request.method == 'POST':
        try:
            username = sanitize_input(request.form.get('username', '')).lower()
            nome_completo = sanitize_input(request.form.get('nome_completo', '')).title()
            email = sanitize_input(request.form.get('email', '')).lower()
            nivel_acesso = request.form.get('nivel_acesso', 'colaborador')
            senha = request.form.get('senha', '')
            confirmar_senha = request.form.get('confirmar_senha', '')

            if not username or not nome_completo or not email:
                flash('Todos os campos obrigatórios devem ser preenchidos.', 'danger')
                return render_template('usuario_form.html', dados=request.form)

            if senha != confirmar_senha:
                flash('As senhas não coincidem.', 'danger')
                return render_template('usuario_form.html', dados=request.form)

            if len(senha) < 8:
                flash('A senha deve ter pelo menos 8 caracteres.', 'danger')
                return render_template('usuario_form.html', dados=request.form)

            if User.query.filter_by(username=username).first():
                flash('Nome de usuário já está em uso.', 'danger')
                return render_template('usuario_form.html', dados=request.form)

            if User.query.filter_by(email=email).first():
                flash('Email já está cadastrado.', 'danger')
                return render_template('usuario_form.html', dados=request.form)

            usuario = User(
                username=username,
                nome_completo=nome_completo,
                email=email,
                nivel_acesso=nivel_acesso,
                ativo=True
            )
            usuario.set_password(senha)

            db.session.add(usuario)
            db.session.commit()

            registrar_log(f'Cadastrou usuário {usuario.username}',
                         'Usuários',
                         f'Email: {usuario.email}, Nível: {usuario.nivel_acesso}')
            flash(f'✅ Usuário {usuario.nome_completo} cadastrado com sucesso!', 'success')

            return redirect(url_for('listar_usuarios'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Erro ao cadastrar usuário: {e}')
            flash(f'Erro ao cadastrar usuário: {str(e)}', 'danger')
            return render_template('usuario_form.html', dados=request.form)

    return render_template('usuario_form.html', title='Novo Usuário')

@app.route('/usuario/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    usuario = User.query.get_or_404(id)

    if request.method == 'POST':
        try:
            usuario.nome_completo = sanitize_input(request.form.get('nome_completo', '')).title()
            usuario.email = sanitize_input(request.form.get('email', '')).lower()
            usuario.nivel_acesso = request.form.get('nivel_acesso', 'colaborador')
            usuario.ativo = 'ativo' in request.form

            novo_email = sanitize_input(request.form.get('email', '')).lower()
            if novo_email != usuario.email:
                if User.query.filter_by(email=novo_email).filter(User.id != id).first():
                    flash('Email já está cadastrado para outro usuário.', 'danger')
                    return render_template('usuario_edit.html', usuario=usuario)
                usuario.email = novo_email

            nova_senha = request.form.get('nova_senha', '')
            if nova_senha:
                confirmar_senha = request.form.get('confirmar_senha', '')
                if nova_senha != confirmar_senha:
                    flash('As novas senhas não coincidem.', 'danger')
                    return render_template('usuario_edit.html', usuario=usuario)
                if len(nova_senha) < 8:
                    flash('A senha deve ter pelo menos 8 caracteres.', 'danger')
                    return render_template('usuario_edit.html', usuario=usuario)
                usuario.set_password(nova_senha)

            db.session.commit()

            registrar_log(f'Editou usuário {usuario.username}',
                         'Usuários',
                         f'ID: {id}, Email: {usuario.email}')
            flash('✅ Usuário atualizado com sucesso!', 'success')

            return redirect(url_for('listar_usuarios'))

        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Erro ao editar usuário {id}: {e}')
            flash(f'Erro ao atualizar usuário: {str(e)}', 'danger')

    return render_template('usuario_edit.html', usuario=usuario, title='Editar Usuário')

@app.route('/usuario/<int:id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_usuario(id):
    if id == current_user.id:
        flash('Você não pode excluir sua própria conta.', 'danger')
        return redirect(url_for('listar_usuarios'))

    usuario = User.query.get_or_404(id)

    try:
        username = usuario.username
        nome = usuario.nome_completo

        db.session.delete(usuario)
        db.session.commit()

        registrar_log(f'Excluiu usuário {username}',
                     'Usuários',
                     f'ID: {id}, Nome: {nome}')
        flash('✅ Usuário excluído com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Erro ao excluir usuário {id}: {e}')
        flash(f'Erro ao excluir usuário: {str(e)}', 'danger')

    return redirect(url_for('listar_usuarios'))

# ============================================================================
# ROTA DE DEBUG
# ============================================================================
@app.route('/debug/routes')
@login_required
@admin_required
def debug_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': ', '.join(rule.methods),
            'rule': rule.rule
        })
    return render_template('debug_routes.html', routes=routes, title='Rotas Disponíveis')

# ============================================================================
# ROTA DE PERFIL DO USUÁRIO
# ============================================================================
@app.route('/meu-perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    usuario = current_user

    if request.method == 'POST':
        try:
            nome_completo = sanitize_input(request.form.get('nome_completo', ''))
            email = sanitize_input(request.form.get('email', '')).lower()

            if not nome_completo or not email:
                flash('Nome completo e email são obrigatórios.', 'error')
                return redirect(url_for('meu_perfil'))

            if email != usuario.email:
                usuario_existente = User.query.filter_by(email=email).first()
                if usuario_existente and usuario_existente.id != usuario.id:
                    flash('Este email já está em uso por outro usuário.', 'error')
                    return redirect(url_for('meu_perfil'))

            usuario.nome_completo = nome_completo.title()
            usuario.email = email

            nova_senha = request.form.get('nova_senha')
            if nova_senha:
                if len(nova_senha) < 6:
                    flash('A senha deve ter pelo menos 6 caracteres.', 'error')
                    return redirect(url_for('meu_perfil'))

                confirmar_senha = request.form.get('confirmar_senha')
                if nova_senha != confirmar_senha:
                    flash('As senhas não coincidem.', 'error')
                    return redirect(url_for('meu_perfil'))

                usuario.set_password(nova_senha)

            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('meu_perfil'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar perfil: {str(e)}', 'error')
            return redirect(url_for('meu_perfil'))

    return render_template('meu_perfil.html',
                         usuario=usuario,
                         page_title='Meu Perfil',
                         page_subtitle='Gerencie suas informações pessoais')

# ============================================================================
# ROTAS DE ERRO SIMPLIFICADAS (mantidas)
# ============================================================================
@app.errorhandler(404)
def pagina_nao_encontrada(e):
    app.logger.warning(f'Página não encontrada: {request.url}')
    return render_template('404.html'), 404

@app.errorhandler(500)
def erro_interno(e):
    app.logger.error(f'Erro interno do servidor: {e}')
    return render_template('500.html'), 500

@app.errorhandler(403)
def acesso_negado(e):
    app.logger.warning(f'Acesso negado: {request.url}')
    return render_template('403.html'), 403

# ============================================================================
# ROTA DE BACKUP AUTOMÁTICO
# ============================================================================
@app.route('/admin/backup')
@login_required
@admin_required
def criar_backup():
    """Cria e disponibiliza backup completo do sistema"""
    try:
        import zipfile
        import io

        # Criar arquivo ZIP em memória
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 1. Código fonte
            codigo_files = [
                'main.py',
                'requirements.txt',
                'README.md'  # se existir
            ]

            for file in codigo_files:
                file_path = os.path.join(BASE_DIR, file)
                if os.path.exists(file_path):
                    zipf.write(file_path, f'codigo/{file}')

            # 2. Templates
            templates_dir = os.path.join(BASE_DIR, 'templates')
            if os.path.exists(templates_dir):
                for root, dirs, files in os.walk(templates_dir):
                    for file in files:
                        if file.endswith('.html'):
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, BASE_DIR)
                            zipf.write(full_path, rel_path)

            # 3. Arquivos de dados (exceto banco de dados muito grande)
            data_dir = os.path.join(BASE_DIR, 'data')
            if os.path.exists(data_dir):
                for root, dirs, files in os.walk(data_dir):
                    for file in files:
                        if not file.endswith('.db'):  # Não incluir banco grande
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, BASE_DIR)
                            zipf.write(full_path, rel_path)

            # 4. Arquivo README com informações do backup
            info = f"""
            Backup do Sistema NEV USP
            Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Versão: 2.8
            Usuário: {current_user.username}
            Diretório: {BASE_DIR}

            Conteúdo incluído:
            - Código fonte principal (main.py)
            - Templates HTML
            - Arquivos de configuração
            - Dados de cache (CEPs)

            Para restaurar:
            1. Extraia o conteúdo
            2. Execute: pip install -r requirements.txt
            3. Execute: python main.py
            """

            zipf.writestr('README.txt', info)

        # Preparar resposta para download
        zip_buffer.seek(0)

        # Registrar log
        registrar_log('Backup criado e baixado', 'Sistema',
                     f'Backup gerado por {current_user.username}')

        # Criar nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'nev_backup_{timestamp}.zip'

        return Response(
            zip_buffer.getvalue(),
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'application/zip'
            }
        )

    except Exception as e:
        app.logger.error(f'Erro ao criar backup: {e}')
        flash(f'Erro ao criar backup: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/admin/backup-page')
@login_required
@admin_required
def backup_page():
    """Página de gerenciamento de backups"""
    return render_template('backup.html', title='Backup do Sistema')

@app.route('/admin/backup-db')
@login_required
@admin_required
def backup_database():
    """Faz backup apenas do banco de dados"""
    try:
        import io

        # Caminho do banco de dados
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

        if os.path.exists(db_path):
            # Ler conteúdo do banco de dados
            with open(db_path, 'rb') as f:
                db_content = f.read()

            # Criar nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'nev_database_{timestamp}.db'

            # Registrar log
            registrar_log('Backup do banco de dados criado', 'Sistema',
                         f'Tamanho: {len(db_content)} bytes')

            return Response(
                db_content,
                mimetype='application/octet-stream',
                headers={
                    'Content-Disposition': f'attachment; filename={filename}',
                    'Content-Type': 'application/octet-stream'
                }
            )
        else:
            flash('Arquivo do banco de dados não encontrado.', 'warning')
            return redirect(url_for('dashboard'))

    except Exception as e:
        app.logger.error(f'Erro ao fazer backup do banco: {e}')
        flash(f'Erro ao fazer backup do banco: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
        
@app.route('/health')
def health_check():
    """Health check para monitoramento"""
    try:
        # Verificar se banco responde
        db.session.execute('SELECT 1')
        return 'OK', 200
    except Exception as e:
        app.logger.error(f'Health check falhou: {e}')
        return 'ERRO', 500

# ============================================================================
# ROTAS DE INICIALIZAÇÃO DO BANCO
# ============================================================================
@app.route('/setup')
def setup_database():
    """Rota para configurar banco de dados manualmente"""
    try:
        with app.app_context():
            # Criar todas as tabelas
            db.create_all()
            
            # Criar admin se não existir
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    nome_completo='Administrador NEV',
                    email='admin@nev.usp.br',
                    nivel_acesso='admin',
                    ativo=True
                )
                admin.set_password('AdminNEV2024')
                db.session.add(admin)
                db.session.commit()
            
            return """
            <h1>✅ Banco de dados configurado com sucesso!</h1>
            <p>Tabelas criadas e usuário admin configurado.</p>
            <p>Login: <strong>admin</strong></p>
            <p>Senha: <strong>AdminNEV2024</strong></p>
            <a href="/login">Ir para login</a>
            """
    except Exception as e:
        return f"""
        <h1>❌ Erro na configuração</h1>
        <p>Erro: {str(e)}</p>
        <p>Verifique a DATABASE_URL no Railway.</p>
        """

@app.route('/init-db')
def init_database():
    """Rota para inicializar banco de dados manualmente"""
    try:
        with app.app_context():
            db.create_all()
            
            # Criar admin se não existir
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    nome_completo='Administrador NEV',
                    email='admin@nev.usp.br',
                    nivel_acesso='admin',
                    ativo=True
                )
                admin.set_password('AdminNEV2024')
                db.session.add(admin)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Banco inicializado com sucesso!'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test-db')
def test_database():
    """Testar conexão com banco de dados"""
    try:
        from sqlalchemy import text
        
        with app.app_context():
            # Testar conexão
            result = db.session.execute(text("SELECT version();"))
            version = result.scalar()
            
            # Verificar tabelas
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result]
            
            return f"""
            <h1>✅ Conexão bem sucedida!</h1>
            <p><strong>Banco:</strong> {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...</p>
            <p><strong>PostgreSQL Version:</strong> {version}</p>
            <p><strong>Tabelas existentes:</strong> {', '.join(tables) or 'Nenhuma'}</p>
            """
    except Exception as e:
        return f"""
        <h1>❌ Erro de conexão</h1>
        <p><strong>Erro:</strong> {str(e)}</p>
        <p><strong>DATABASE_URL configurada:</strong> {app.config.get('SQLALCHEMY_DATABASE_URI', 'Não configurada')}</p>
        """

# ============================================================================
# INICIALIZAÇÃO OTIMIZADA
# ============================================================================
def init_db():
    """Inicialização otimizada do banco de dados"""
    with app.app_context():
        try:
            # Verificar se estamos usando PostgreSQL
            if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI']:
                print("📊 Usando PostgreSQL (Supabase)")
                
                # Criar todas as tabelas
                db.create_all()
                
                # Verificar se admin existe
                admin = User.query.filter_by(username='admin').first()
                if not admin:
                    admin = User(
                        username='admin',
                        nome_completo='Administrador NEV',
                        email='admin@nev.usp.br',
                        nivel_acesso='admin',
                        ativo=True
                    )
                    admin.set_password('AdminNEV2024')
                    db.session.add(admin)
                    db.session.commit()
                    print('✅ Usuário admin criado')
                
                app.logger.info('✅ Banco PostgreSQL inicializado!')
            else:
                # SQLite local (desenvolvimento)
                print("📊 Usando SQLite local")
                db.create_all()
                
                admin = User.query.filter_by(username='admin').first()
                if not admin:
                    admin = User(
                        username='admin',
                        nome_completo='Administrador NEV',
                        email='admin@nev.usp.br',
                        nivel_acesso='admin',
                        ativo=True
                    )
                    admin.set_password('AdminNEV2024')
                    db.session.add(admin)
                    db.session.commit()
                    print('✅ Usuário admin criado (SQLite)')
                
                app.logger.info('✅ Banco SQLite inicializado!')
                
        except Exception as e:
            app.logger.error(f'❌ Erro ao inicializar banco: {e}')
            print(f'❌ ERRO CRÍTICO: {e}')
            # Não levantar exceção para não quebrar o app

# ============================================================================
# CONFIGURAÇÃO PARA PRODUÇÃO
# ============================================================================
if __name__ == '__main__':
    # Configurar logging
    if not app.debug:
        handler = RotatingFileHandler('nev_app.log', maxBytes=20000, backupCount=5)
        handler.setLevel(logging.WARNING)
        app.logger.addHandler(handler)

    # Inicializar banco de dados
    init_db()
    
    print("=" * 60)
    print("  Sistema NEV USP - Cadastro de Colaboradores v2.8")
    print("=" * 60)
    
    # Para Railway/Render, use PORT da variável de ambiente
    port = int(os.environ.get("PORT", 5000))
    
    print(f"🚀 Servidor iniciando na porta {port}")
    print(f"📊 Banco: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    print("=" * 60)
    
    # Modo desenvolvimento vs produção
    debug_mode = app.config.get('DEBUG', False)
    
    if debug_mode:
        # Modo desenvolvimento
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        # Modo produção
        app.run(host='0.0.0.0', port=port)