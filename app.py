"""
Sistema NEV USP - Cadastro de Colaboradores
Versão 2.7 (Unified Stability) - Integração v2.2 + v2.6
Autor: NEV USP
Versão: 2.7 (Corrigido e Otimizado - 2026)
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
if IS_PYTHONANYWHERE:
    username = getpass.getuser()
    BASE_DIR = f'/home/{username}/mysite'
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    os.makedirs(DATA_DIR, exist_ok=True)
else:
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

# Configuração do banco de dados
db_path = os.path.join(DATA_DIR, 'nev.db')
if sys.platform == 'win32':
    # Windows usa barras normais
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

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
    """Cálculo eficiente de idade"""
    if not data_nascimento:
        return None
    hoje = date.today()
    return hoje.year - data_nascimento.year - (
        (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day)
    )

# ============================================================================
# SISTEMA DE CACHE DE CEP (PARA PYTHONANYWHERE)
# ============================================================================
def carregar_cache_ceps():
    """Carrega o cache de CEPs do arquivo JSON"""
    cache_file = os.path.join(DATA_DIR, 'ceps_cache.json')
    ceps_frequentes_file = os.path.join(DATA_DIR, 'ceps_frequentes.json')

    cache = {}
    ceps_frequentes = {}

    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
    except Exception as e:
        app.logger.warning(f'Erro ao carregar cache de CEPs: {e}')

    try:
        if os.path.exists(ceps_frequentes_file):
            with open(ceps_frequentes_file, 'r', encoding='utf-8') as f:
                ceps_frequentes = json.load(f)
    except Exception as e:
        app.logger.warning(f'Erro ao carregar CEPs frequentes: {e}')

    return cache, ceps_frequentes

def salvar_no_cache(cep_limpo: str, endereco: dict):
    """Salva um CEP no cache"""
    try:
        cache_file = os.path.join(DATA_DIR, 'ceps_cache.json')
        cache, _ = carregar_cache_ceps()

        cache[cep_limpo] = {
            'logradouro': endereco.get('logradouro', ''),
            'bairro': endereco.get('bairro', ''),
            'cidade': endereco.get('cidade', ''),
            'estado': endereco.get('estado', ''),
            'complemento': endereco.get('complemento', ''),
            'data_cache': datetime.now().strftime('%Y-%m-%d')
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

        return True
    except Exception as e:
        app.logger.error(f'Erro ao salvar CEP no cache: {e}')
        return False

def buscar_endereco_por_cep(cep: str) -> dict:
    """
    Busca endereço usando cache local e estimativa por faixa de CEP
    Solução para PythonAnywhere (sem acesso a APIs externas)
    """
    try:
        # Remove caracteres não numéricos
        cep_limpo = re.sub(r'\D', '', cep)

        if len(cep_limpo) != 8:
            return None

        # Carregar cache
        cache, ceps_frequentes = carregar_cache_ceps()

        # 1. Buscar no cache
        if cep_limpo in cache:
            dados = cache[cep_limpo]
            # Verificar se o cache não expirou (90 dias)
            data_cache_str = dados.get('data_cache', '2000-01-01')
            try:
                data_cache = datetime.strptime(data_cache_str, '%Y-%m-%d')
                if datetime.now() - data_cache < timedelta(days=90):
                    return {
                        'cep': f"{cep_limpo[:5]}-{cep_limpo[5:]}",
                        'logradouro': dados.get('logradouro', ''),
                        'bairro': dados.get('bairro', ''),
                        'cidade': dados.get('cidade', ''),
                        'estado': dados.get('estado', ''),
                        'complemento': dados.get('complemento', '')
                    }
            except ValueError:
                pass

        # 2. Buscar em CEPs frequentes pré-cadastrados
        if cep_limpo in ceps_frequentes:
            dados = ceps_frequentes[cep_limpo]
            return {
                'cep': f"{cep_limpo[:5]}-{cep_limpo[5:]}",
                'logradouro': dados.get('logradouro', ''),
                'bairro': dados.get('bairro', ''),
                'cidade': dados.get('cidade', ''),
                'estado': dados.get('estado', ''),
                'complemento': dados.get('complemento', '')
            }

        # 3. Estimar cidade/estado baseado no CEP (faixas principais)
        cep_num = int(cep_limpo[:5])

        # Faixas aproximadas por região
        if 1000 <= cep_num <= 5999:  # São Paulo (SP)
            cidade, estado = 'São Paulo', 'SP'
        elif 6000 <= cep_num <= 9999:  # Grande SP
            cidade, estado = 'São Paulo', 'SP'
        elif 20000 <= cep_num <= 28999:  # Rio de Janeiro (RJ)
            cidade, estado = 'Rio de Janeiro', 'RJ'
        elif 30000 <= cep_num <= 39999:  # Minas Gerais (MG)
            cidade, estado = 'Belo Horizonte', 'MG'
        elif 40000 <= cep_num <= 48999:  # Bahia (BA)
            cidade, estado = 'Salvador', 'BA'
        elif 50000 <= cep_num <= 56999:  # Pernambuco (PE)
            cidade, estado = 'Recife', 'PE'
        elif 57000 <= cep_num <= 57999:  # Alagoas (AL)
            cidade, estado = 'Maceió', 'AL'
        elif 58000 <= cep_num <= 58999:  # Paraíba (PB)
            cidade, estado = 'João Pessoa', 'PB'
        elif 59000 <= cep_num <= 59999:  # Rio Grande do Norte (RN)
            cidade, estado = 'Natal', 'RN'
        elif 60000 <= cep_num <= 63999:  # Ceará (CE)
            cidade, estado = 'Fortaleza', 'CE'
        elif 64000 <= cep_num <= 64999:  # Piauí (PI)
            cidade, estado = 'Teresina', 'PI'
        elif 65000 <= cep_num <= 65999:  # Maranhão (MA)
            cidade, estado = 'São Luís', 'MA'
        elif 66000 <= cep_num <= 68899:  # Pará (PA)
            cidade, estado = 'Belém', 'PA'
        elif 69000 <= cep_num <= 69299:  # Amazonas (AM)
            cidade, estado = 'Manaus', 'AM'
        elif 70000 <= cep_num <= 73699:  # Distrito Federal (DF)
            cidade, estado = 'Brasília', 'DF'
        elif 74000 <= cep_num <= 74999:  # Goiás (GO)
            cidade, estado = 'Goiânia', 'GO'
        elif 80000 <= cep_num <= 87999:  # Paraná (PR)
            cidade, estado = 'Curitiba', 'PR'
        elif 88000 <= cep_num <= 89999:  # Santa Catarina (SC)
            cidade, estado = 'Florianópolis', 'SC'
        elif 90000 <= cep_num <= 99999:  # Rio Grande do Sul (RS)
            cidade, estado = 'Porto Alegre', 'RS'
        else:
            cidade, estado = '', ''

        # Retornar estrutura básica
        return {
            'cep': f"{cep_limpo[:5]}-{cep_limpo[5:]}",
            'logradouro': '',
            'bairro': '',
            'cidade': cidade,
            'estado': estado,
            'complemento': '',
            'estimado': True
        }

    except Exception as e:
        app.logger.error(f'Erro ao buscar CEP {cep}: {e}')
        return None

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

    # Endereço
    cep = db.Column(db.String(10))
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(50))
    bairro = db.Column(db.String(50))
    cidade = db.Column(db.String(50))
    estado = db.Column(db.String(2))

    # Dados profissionais
    data_ingresso = db.Column(db.Date, nullable=False)
    tipo_vinculo = db.Column(db.String(50), nullable=False)
    programa_projeto = db.Column(db.String(100))
    departamento = db.Column(db.String(100))
    lotacao = db.Column(db.String(100))

    # Horários
    dias_presenciais = db.Column(db.String(100))
    horario_entrada = db.Column(db.Time)
    horario_saida = db.Column(db.Time)
    carga_horaria_semanal = db.Column(db.Integer)

    # Imprensa
    atende_imprensa = db.Column(db.Boolean, default=False)
    tipos_imprensa = db.Column(db.String(200))
    assuntos_especializacao = db.Column(db.Text)
    disponibilidade_contato = db.Column(db.String(100))
    observacoes_imprensa = db.Column(db.Text)

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
# CONTEXT PROCESSOR
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
        'app_version': '2.7',
        'ano_atual': datetime.now().year,
        'formatar_cpf': formatar_cpf,
        'formatar_telefone': formatar_telefone,
        'validar_cpf': validar_cpf,
        'calcular_idade': calcular_idade,
        'buscar_endereco_por_cep': buscar_endereco_por_cep
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

@app.route('/logout')
@login_required
def logout():
    registrar_log('Logout realizado', 'Autenticação')
    logout_user()
    flash('Você saiu do sistema com sucesso.', 'info')
    return redirect(url_for('login'))

# ============================================================================
# ROTA API PARA BUSCAR CEP
# ============================================================================
@app.route('/api/buscar-cep/<cep>')
@login_required
def api_buscar_cep(cep):
    """API para buscar endereço por CEP (com cache local)"""
    app.logger.info(f'Buscando CEP: {cep}')
    try:
        endereco = buscar_endereco_por_cep(cep)
        if endereco:
            # Remover flag 'estimado' se existir
            estimado = endereco.pop('estimado', False)

            resposta = {
                'success': True,
                'endereco': endereco
            }
            if estimado:
                resposta['message'] = 'Cidade/estado estimados pela faixa do CEP'

            app.logger.info(f'CEP {cep} retornado: {endereco}')
            return jsonify(resposta)
        else:
            app.logger.warning(f'CEP {cep} não encontrado')
            return jsonify({
                'success': False,
                'message': 'CEP não encontrado. Preencha os dados manualmente.'
            }), 404

    except Exception as e:
        app.logger.error(f'Erro na API buscar-cep para {cep}: {e}')
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar CEP: {str(e)}'
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
# ROTAS DE COLABORADORES OTIMIZADAS
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
            colaborador.lotacao = sanitize_input(request.form.get('lotacao', ''))

            # Dias presenciais
            dias_presenciais = request.form.getlist('dias_presenciais')
            if dias_presenciais:
                colaborador.dias_presenciais = ','.join(dias_presenciais)
            else:
                colaborador.dias_presenciais = None

            colaborador.atende_imprensa = 'atende_imprensa' in request.form
            colaborador.tipos_imprensa = ', '.join(request.form.getlist('tipos_imprensa'))
            colaborador.assuntos_especializacao = sanitize_input(request.form.get('assuntos_especializacao', ''))
            colaborador.disponibilidade_contato = sanitize_input(request.form.get('disponibilidade_contato', ''))

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

# ============================================================================
# ROTAS DE CONFIGURAÇÕES
# ============================================================================
@app.route('/configuracoes')
@login_required
@admin_required
def configuracoes():
    return render_template('configuracoes.html', title='Configurações')

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
# ROTAS DE ERRO
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
                'app.py',
                'requirements.txt',
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
            if os.path.exists(DATA_DIR):
                for root, dirs, files in os.walk(DATA_DIR):
                    for file in files:
                        if not file.endswith('.db'):  # Não incluir banco grande
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, BASE_DIR)
                            zipf.write(full_path, rel_path)

            # 4. Arquivo README com informações do backup
            info = f"""
            Backup do Sistema NEV USP
            Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Versão: 2.7
            Usuário: {current_user.username}
            Diretório: {BASE_DIR}

            Conteúdo incluído:
            - Código fonte principal (app.py)
            - Templates HTML
            - Arquivos de configuração
            - Dados de cache (CEPs)

            Para restaurar:
            1. Extraia o conteúdo
            2. Execute: pip install -r requirements.txt
            3. Execute: python app.py
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

# ============================================================================
# INICIALIZAÇÃO OTIMIZADA
# ============================================================================
def init_db():
    """Inicialização otimizada do banco de dados"""
    with app.app_context():
        db.create_all()
        app.logger.info('Tabelas criadas/verificadas com sucesso!')

        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                nome_completo='Administrador NEV',
                email='admin@nev.usp.br',
                nivel_acesso='admin',
                ativo=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            app.logger.info('✅ Usuário admin criado (usuário: admin, senha: admin123)')
            app.logger.info('⚠️ ALERTA: Altere a senha do admin no primeiro login!')

        # Criar arquivos de cache de CEPs se não existirem
        if not os.path.exists(os.path.join(DATA_DIR, 'ceps_cache.json')):
            with open(os.path.join(DATA_DIR, 'ceps_cache.json'), 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

        if not os.path.exists(os.path.join(DATA_DIR, 'ceps_frequentes.json')):
            ceps_frequentes = {
                "05508000": {
                    "logradouro": "Cidade Universitária",
                    "bairro": "Butantã",
                    "cidade": "São Paulo",
                    "estado": "SP",
                    "complemento": "USP"
                }
            }
            with open(os.path.join(DATA_DIR, 'ceps_frequentes.json'), 'w', encoding='utf-8') as f:
                json.dump(ceps_frequentes, f, ensure_ascii=False, indent=2)

        app.logger.info('✅ Banco de dados inicializado com sucesso!')

# ============================================================================
# EXECUÇÃO PRINCIPAL
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
    print("  Sistema NEV USP - Cadastro de Colaboradores v2.7")
    print("=" * 60)
    
    print("Modo:", "DESENVOLVIMENTO" if app.config['DEBUG'] else "PRODUÇÃO")
    print("Banco de dados:", app.config['SQLALCHEMY_DATABASE_URI'])
    print("=" * 60)

    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)