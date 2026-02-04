import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User
from werkzeug.security import check_password_hash

print("=" * 60)
print("TESTE DETALHADO DE LOGIN")
print("=" * 60)

with app.app_context():
    # Testar cada usuário
    usuarios = User.query.all()
    
    for user in usuarios:
        print(f"\n{'='*40}")
        print(f"Usuário: {user.username}")
        print(f"Nome: {user.nome_completo}")
        print(f"Email: {user.email}")
        print(f"Ativo: {user.ativo}")
        print(f"Hash (30 chars): {user.senha_hash[:30]}...")
        
        # Testar métodos
        print("\nTestando métodos:")
        
        # 1. Tem método check_password?
        if hasattr(user, 'check_password'):
            print("  ✅ Tem método check_password")
            try:
                # Testar senha correta (supondo 'AdminNEV2024' para admin)
                if user.username == 'admin':
                    senha_teste = 'AdminNEV2024'
                else:
                    senha_teste = 'senha123'  # senha padrão para outros
                
                resultado = user.check_password(senha_teste)
                print(f"  - check_password('{senha_teste}'): {resultado}")
            except Exception as e:
                print(f"  ❌ Erro no check_password: {e}")
        else:
            print("  ❌ NÃO tem método check_password")
        
        # 2. Testar diretamente com werkzeug
        print("  Testando com check_password_hash direto:")
        try:
            from werkzeug.security import check_password_hash
            
            if user.username == 'admin':
                senha_teste = 'AdminNEV2024'
                resultado = check_password_hash(user.senha_hash, senha_teste)
                print(f"  - check_password_hash(hash, '{senha_teste}'): {resultado}")
            
            # Testar senha errada
            resultado_errado = check_password_hash(user.senha_hash, 'SENHA_ERRADA_123')
            print(f"  - check_password_hash(hash, 'SENHA_ERRADA_123'): {resultado_errado}")
            
        except Exception as e:
            print(f"  ❌ Erro no check_password_hash: {e}")
        
        # 3. Verificar se hash parece válido
        print(f"  Hash parece válido? {len(user.senha_hash) > 20 and '$' in user.senha_hash}")
    
    print("\n" + "=" * 60)
    print("CONCLUSÃO:")
    
    # Verificar se admin tem senha hash correta
    admin = User.query.filter_by(username='admin').first()
    if admin and len(admin.senha_hash) < 20:
        print("❌ PROBLEMA: Hash do admin muito curto!")
        print("   A senha pode estar em texto puro.")
        print("\nSOLUÇÃO:")
        print("1. Vou te mostrar como corrigir o hash")
        print("2. Ou podemos resetar a senha do admin")
    
    print("=" * 60)