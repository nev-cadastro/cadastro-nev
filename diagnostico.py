import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User
from werkzeug.security import generate_password_hash

print("=" * 60)
print("DIAGNÓSTICO DO SISTEMA NEV")
print("=" * 60)

with app.app_context():
    # 1. Verificar banco
    print("1. Verificando banco de dados...")
    try:
        db.create_all()
        print("   ✅ Banco OK")
    except Exception as e:
        print(f"   ❌ Erro no banco: {e}")
    
    # 2. Verificar tabela de usuários
    print("\n2. Verificando tabela de usuários...")
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"   Tabelas encontradas: {tables}")
    
    if 'usuarios' in tables:
        print("   ✅ Tabela 'usuarios' existe")
        
        # 3. Verificar se tem usuários
        print("\n3. Verificando usuários...")
        try:
            users = User.query.all()
            print(f"   Total de usuários: {len(users)}")
            for user in users:
                print(f"   - {user.username} ({user.nome_completo})")
        except Exception as e:
            print(f"   ❌ Erro ao buscar usuários: {e}")
    else:
        print("   ❌ Tabela 'usuarios' NÃO existe!")
        
        # Tentar criar manualmente
        print("\n4. Tentando criar tabela manualmente...")
        try:
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    senha_hash VARCHAR(200) NOT NULL,
                    nome_completo VARCHAR(100) NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    nivel_acesso VARCHAR(20) DEFAULT 'colaborador',
                    ativo BOOLEAN DEFAULT 1,
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultimo_login TIMESTAMP,
                    senha_alterada BOOLEAN DEFAULT 0
                )
            """))
            db.session.commit()
            print("   ✅ Tabela criada manualmente")
        except Exception as e:
            print(f"   ❌ Erro ao criar tabela: {e}")
    
    # 5. Verificar/criar admin
    print("\n5. Verificando administrador...")
    try:
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"   ✅ Admin encontrado: {admin.username}")
            print(f"   Testando senha...")
            # Criar senha se não tiver
            if not admin.senha_hash or len(admin.senha_hash) < 10:
                admin.set_password('AdminNEV2024')
                db.session.commit()
                print("   ✅ Senha definida para admin")
        else:
            print("   ❌ Admin NÃO encontrado")
            print("   Criando admin...")
            admin = User(
                username='admin',
                nome_completo='Administrador NEV',
                email='admin@nev.usp.br',
                nivel_acesso='administrador',
                ativo=True
            )
            admin.set_password('AdminNEV2024')
            db.session.add(admin)
            db.session.commit()
            print("   ✅ Admin criado com sucesso!")
    except Exception as e:
        print(f"   ❌ Erro com admin: {e}")
    
    print("\n" + "=" * 60)
    print("FIM DO DIAGNÓSTICO")
    print("=" * 60)