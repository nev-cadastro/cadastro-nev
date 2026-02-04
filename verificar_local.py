import os
import sys

print("=" * 60)
print("VERIFICAÇÃO: Onde estou rodando?")
print("=" * 60)

# 1. Diretório atual
current_dir = os.path.dirname(os.path.abspath(__file__))
print(f"📁 Diretório atual: {current_dir}")

# 2. Onde está o app.py que estou executando?
print(f"📄 app.py executado: {__file__}")

# 3. Onde Flask procura templates?
try:
    from flask import Flask
    app_test = Flask(__name__)
    print(f"🔍 Flask procura templates em: {app_test.template_folder}")
except:
    pass

# 4. Templates existem?
templates_path = os.path.join(current_dir, 'templates', 'login.html')
print(f"🔍 login.html existe? {os.path.exists(templates_path)}")
print(f"🔍 Caminho: {templates_path}")

# 5. Recomendação
print("\n" + "=" * 60)
if "nev_backup" in current_dir:
    print("❌ PROBLEMA: Você está rodando do diretório de BACKUP!")
    print("\n✅ SOLUÇÃO:")
    print("cd /c/Users/emerson.silva/Downloads/cadastronev")
    print("python app.py")
else:
    print("✅ Você está no diretório correto!")
print("=" * 60)