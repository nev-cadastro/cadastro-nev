# railway_migrate.py
import os
import sys

print("🚀 Iniciando migração segura para Railway...")

try:
    from main import app, db
    from sqlalchemy import inspect, text
    
    with app.app_context():
        print("✅ Conectado ao banco de dados")
        
        # Verificar tabelas existentes
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"📊 Tabelas existentes: {tables}")
        
        # Adicionar campos na tabela usuarios
        if 'usuarios' in tables:
            columns = [col['name'] for col in inspector.get_columns('usuarios')]
            print(f"📋 Colunas em usuarios: {columns}")
            
            if 'foto_perfil' not in columns:
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN foto_perfil VARCHAR(255)"))
                print("✅ Adicionado campo foto_perfil em usuarios")
            
            if 'foto_perfil_miniatura' not in columns:
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN foto_perfil_miniatura VARCHAR(255)"))
                print("✅ Adicionado campo foto_perfil_miniatura em usuarios")
            
            if 'foto_data_upload' not in columns:
                db.session.execute(text("ALTER TABLE usuarios ADD COLUMN foto_data_upload TIMESTAMP"))
                print("✅ Adicionado campo foto_data_upload em usuarios")
        
        # Criar tabela de convites
        if 'convites' not in tables:
            db.session.execute(text("""
                CREATE TABLE convites (
                    id SERIAL PRIMARY KEY,
                    codigo VARCHAR(50) UNIQUE NOT NULL,
                    cpf VARCHAR(14) NOT NULL,
                    email VARCHAR(120) NOT NULL,
                    token_confirmacao VARCHAR(100) UNIQUE NOT NULL,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_expiracao TIMESTAMP NOT NULL,
                    usado BOOLEAN DEFAULT FALSE,
                    usado_em TIMESTAMP,
                    criado_por INTEGER REFERENCES usuarios(id)
                )
            """))
            print("✅ Criada tabela convites")
        
        db.session.commit()
        print("🎉 Migração concluída com sucesso!")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)