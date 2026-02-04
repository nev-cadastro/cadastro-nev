# teste_registrar_log.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, registrar_log

print("Testando registrar_log...")
with app.app_context():
    try:
        # Criar contexto de request fake
        from flask import request
        
        class FakeRequest:
            remote_addr = '127.0.0.1'
            user_agent = 'Test'
        
        # Testar sem current_user
        print("1. Testando sem usuário...")
        resultado = registrar_log('Teste sem usuário', 'Teste')
        print(f"   Resultado: {resultado}")
        
        # Testar em contexto de request
        print("\n2. Testando em contexto...")
        with app.test_request_context():
            resultado = registrar_log('Teste com contexto', 'Teste')
            print(f"   Resultado: {resultado}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()