# migrate.py
import os
import sys

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Tenta importar o app do seu main.py
try:
    from main import app, db
    print("✅ App importado com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar: {e}")
    print("Certifique-se de estar na mesma pasta do main.py")
    sys.exit(1)

with app.app_context():
    print("🔧 Conectando ao banco de dados...")
    
    # Lista de comandos SQL para adicionar colunas
    sql_commands = [
        "ALTER TABLE colaboradores ADD COLUMN IF NOT EXISTS complemento VARCHAR(100)",
        "ALTER TABLE colaboradores ADD COLUMN IF NOT EXISTS foto_perfil VARCHAR(255)",
        "ALTER TABLE colaboradores ADD COLUMN IF NOT EXISTS foto_perfil_miniatura VARCHAR(255)",
        "ALTER TABLE colaboradores ADD COLUMN IF NOT EXISTS foto_data_upload TIMESTAMP"
    ]
    
    print("📋 Executando migração...")
    
    for sql in sql_commands:
        try:
            print(f"   Executando: {sql[:60]}...")
            db.session.execute(db.text(sql))
            print("   ✅ Sucesso!")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")
    
    try:
        db.session.commit()
        print("🎉 Migração concluída com sucesso!")
        
        # Verificar se as colunas foram adicionadas
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = inspector.get_columns('colaboradores')
        print("\n📊 Colunas na tabela colaboradores:")
        for col in columns:
            print(f"   - {col['name']} ({col['type']})")
            
    except Exception as e:
        print(f"❌ Erro ao commitar: {e}")
        db.session.rollback()
