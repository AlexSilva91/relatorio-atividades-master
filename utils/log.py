import os

def get_log_file_path():
    # Determina o diretório adequado dependendo do sistema operacional
    if os.name == 'nt':  # Windows
        log_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'meta_tecnicos')
    else:  # Linux/Mac
        log_dir = os.path.expanduser('~/.local/share/meta_tecnicos')
    
    # Cria o diretório se não existir
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'app.log')

    #C:\Users\Técnico 1\AppData\Roaming\.bot_oculto

    #C:\Users\Técnico 1\AppData\Local\meta_tecnicos\app.log

