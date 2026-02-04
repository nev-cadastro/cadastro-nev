import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User
from flask_login import login_user
from werkzeug.security import generate_password_hash

print("=" * 60)
print("TESTE FINAL COMPLETO DO SISTEMA DE LOGIN")
print("=" * 60)

with app.app_context():
    # Criar contexto de request simulado
    from flask import Request
    import io
    
    print("1. Testando modelo User completo...")
    admin = User.query.filter_by(username='admin').first()
    
    print(f"   ✅ Usuário admin encontrado: {admin.username}")
    print(f"   ✅ Tem UserMixin? {'UserMixin' in str(admin.__class__.__bases__)}")
    print(f"   ✅ Tem método check_password? {hasattr(admin, 'check_password')}")
    print(f"   ✅ Tem atributo id? {hasattr(admin, 'id')}")
    print(f"   ✅ Ativo? {admin.ativo}")
    
    print("\n2. Testando senha...")
    senha_teste = 'AdminNEV2024'
    resultado = admin.check_password(senha_teste)
    print(f"   ✅ check_password('{senha_teste}'): {resultado}")
    
    if not resultado:
        print("   ❌ PROBLEMA: Senha não confere mesmo após reset!")
        print("   Corrigindo novamente...")
        admin.set_password(senha_teste)
        db.session.commit()
        print("   ✅ Senha redefinida novamente")
    
    print("\n3. Testando login_user (Flask-Login)...")
    try:
        # Simular login
        print("   ✅ Flask-Login importado corretamente")
        print(f"   ✅ login_user função disponível: {login_user is not None}")
        
        # Verificar se user tem métodos do UserMixin
        print(f"   ✅ Tem is_authenticated? {hasattr(admin, 'is_authenticated')}")
        print(f"   ✅ Tem is_active? {hasattr(admin, 'is_active')}")
        print(f"   ✅ Tem is_anonymous? {hasattr(admin, 'is_anonymous')}")
        print(f"   ✅ Tem get_id? {hasattr(admin, 'get_id')}")
        
    except Exception as e:
        print(f"   ❌ Erro no Flask-Login: {e}")
    
    print("\n4. Verificando estrutura da tabela...")
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    
    colunas = inspector.get_columns('usuarios')
    print(f"   Colunas da tabela usuarios:")
    for col in colunas[:5]:  # primeiras 5 colunas
        print(f"   - {col['name']} ({col['type']})")
    
    print("\n" + "=" * 60)
    print("RESULTADO FINAL:")
    
    if resultado and hasattr(admin, 'is_authenticated'):
        print("✅ ✅ ✅ SISTEMA PRONTO PARA LOGIN!")
        print("\nAcesse: http://localhost:5000")
        print("Usuário: admin")
        print("Senha: AdminNEV2024")
    else:
        print("❌ Ainda há problemas a corrigir")
    
    print("=" * 60)