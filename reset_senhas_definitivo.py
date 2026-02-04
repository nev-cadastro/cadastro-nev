import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User
from werkzeug.security import generate_password_hash, check_password_hash

print("=" * 60)
print("RESET DEFINITIVO DE SENHAS - SISTEMA NEV")
print("=" * 60)

with app.app_context():
    # Senhas padrão para cada usuário
    senhas_padrao = {
        'admin': 'AdminNEV2024',
        'comum': 'ComumNEV2024', 
        'mara': 'MaraNEV2024'
    }
    
    print("Resetando senhas para padrão conhecido...")
    print("-" * 40)
    
    for username, senha in senhas_padrao.items():
        user = User.query.filter_by(username=username).first()
        
        if user:
            print(f"\nUsuário: {username}")
            print(f"Senha nova: {senha}")
            
            # Método 1: Usando generate_password_hash diretamente
            novo_hash = generate_password_hash(senha)
            user.senha_hash = novo_hash
            
            print(f"Hash gerado: {novo_hash[:50]}...")
            
            # Testar IMEDIATAMENTE se o hash funciona
            teste = check_password_hash(novo_hash, senha)
            print(f"Teste hash funcionou? {teste}")
            
            if not teste:
                print("⚠️  ALERTA: Hash não está funcionando!")
                # Tentar método alternativo
                from hashlib import sha256
                import binascii
                import os
                
                # Gerar salt
                salt = os.urandom(16)
                # Hash PBKDF2 manual
                import hashlib
                import binascii
                
                # Método mais simples
                dk = hashlib.pbkdf2_hmac('sha256', senha.encode('utf-8'), salt, 600000)
                hash_manual = f"pbkdf2:sha256:600000${binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"
                user.senha_hash = hash_manual
                print(f"Hash manual: {hash_manual[:50]}...")
    
    # Salvar todas as mudanças
    db.session.commit()
    
    print("\n" + "=" * 40)
    print("✅ SENHAS RESETADAS!")
    print("=" * 40)
    
    # Testar TODOS os usuários após reset
    print("\nTESTE FINAL DE TODOS OS USUÁRIOS:")
    print("-" * 50)
    
    for username, senha in senhas_padrao.items():
        user = User.query.filter_by(username=username).first()
        if user:
            # Testar com check_password do modelo
            if hasattr(user, 'check_password'):
                resultado = user.check_password(senha)
                print(f"{username}: check_password = {resultado}")
            else:
                # Testar diretamente
                resultado = check_password_hash(user.senha_hash, senha)
                print(f"{username}: check_password_hash = {resultado}")
    
    print("\n" + "=" * 60)
    print("CREDENCIAIS PARA LOGIN:")
    print("=" * 60)
    for username, senha in senhas_padrao.items():
        print(f"Usuário: {username:10} | Senha: {senha}")
    
    print("\n⚠️  ACESSO AO SISTEMA:")
    print("URL: http://localhost:5000")
    print("Use as credenciais acima")
    print("TROQUE AS SENHAS NO PRIMEIRO LOGIN!")
    print("=" * 60)