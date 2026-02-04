import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Criar tabelas se não existirem
    db.create_all()
    
    # Verificar se já existe admin
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            nome_completo='Administrador NEV',
            email='admin@nev.usp.br',
            nivel_acesso='administrador'
        )
        admin.set_password('AdminNEV2024')  # Troque esta senha!
        db.session.add(admin)
        db.session.commit()
        print("✅ Administrador criado:")
        print("   Usuário: admin")
        print("   Senha: AdminNEV2024")
        print("   ⚠️ TROQUE A SENHA NO PRIMEIRO LOGIN!")
    else:
        print("⚠️ Administrador já existe")