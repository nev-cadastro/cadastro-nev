import os
import zipfile
import datetime
from flask import send_file

@app.route('/backup')
@login_required
@admin_required
def backup_site():
    """Cria e disponibiliza backup do site"""
    backup_dir = '/home/cadastronev/backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f'nev_backup_{timestamp}.zip'
    zip_path = os.path.join(backup_dir, zip_filename)
    
    # Criar arquivo ZIP
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Adicionar arquivos do projeto
        project_dir = '/home/cadastronev/mysite'
        for root, dirs, files in os.walk(project_dir):
            # Ignorar alguns diretórios/arquivos
            dirs[:] = [d for d in dirs if d not in ['__pycache__', 'venv', '.git']]
            
            for file in files:
                if not file.endswith(('.pyc', '.log', '.tmp')):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, '/home/cadastronev')
                    zipf.write(file_path, arcname)
    
    # Registrar log
    registrar_log('Backup criado', 'Sistema', f'Arquivo: {zip_filename}')
    
    # Oferecer para download
    return send_file(zip_path, as_attachment=True, download_name=zip_filename)