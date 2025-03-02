import telebot
import logging
import os
import time
from cryptography.fernet import Fernet
import threading
from utils.log import get_log_file_path

# Configuração
BOT_TOKEN = "8141218115:AAETEpDWeVn3sQ0UgWtPuWUw7BeWMFIAXiM"
CHAT_ID_AUTORIZADO = "-1002447284945"

# Função para criar e retornar o caminho do diretório oculto
def obter_diretorio_oculto():
    """Cria e retorna o caminho do diretório oculto."""
    if os.name == "nt":  # Windows
        diretorio = os.path.join(os.getenv("APPDATA"), ".bot_oculto")
    else:  # Linux/macOS
        diretorio = os.path.expanduser("~/.bot_oculto")
    
    if not os.path.exists(diretorio):
        os.makedirs(diretorio)
    
    return diretorio

# Caminhos para os arquivos ocultos
DIRETORIO_OCULTO = obter_diretorio_oculto()
STATUS_FILE = os.path.join(DIRETORIO_OCULTO, "status_encrypted.txt")
CHAVE_FILE = os.path.join(DIRETORIO_OCULTO, "chave.key")

# Gerar uma chave para criptografia (apenas uma vez)
def gerar_chave():
    return Fernet.generate_key()

# Função para carregar ou gerar a chave
def carregar_chave():
    if os.path.exists(CHAVE_FILE):
        with open(CHAVE_FILE, "rb") as chave_file:
            return chave_file.read()
    else:
        chave = gerar_chave()
        with open(CHAVE_FILE, "wb") as chave_file:
            chave_file.write(chave)
        return chave

# Carregar a chave de criptografia
chave = carregar_chave()
fernet = Fernet(chave)

log_file = get_log_file_path()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Inicializando o bot
bot = telebot.TeleBot(BOT_TOKEN)

# Função para ler o status do arquivo criptografado
def carregar_status():
    """Carrega o status criptografado do arquivo, ou define como 'bloqueado' se não encontrado."""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "rb") as f:
            encrypted_status = f.read()
            status = fernet.decrypt(encrypted_status).decode()
            if status in ["bloqueado", "desbloqueado"]:
                return status
    return "bloqueado"  # Retorna 'bloqueado' caso não haja astatusrquivo ou o conteúdo seja inválido

# Variável global para armazenar o status
status = carregar_status()  # Carrega o status ao iniciar
ultimo_status_logado = None  # Variável para armazenar o último status logado

# Função para salvar o status no arquivo criptografado
def salvar_status():
    """Salva o status atual no arquivo criptografado."""
    encrypted_status = fernet.encrypt(status.encode())
    with open(STATUS_FILE, "wb") as f:
        f.write(encrypted_status)

# Função para obter o status atual
def get_status():
    """Retorna o status atual do sistema."""
    global status
    return status

# Função para verificar o status mais recente do usuário
def atualizar_status(message):
    global status
    if message.chat.id == int(CHAT_ID_AUTORIZADO):
        if "bloquear" in message.text.lower():
            status = "bloqueado"
            salvar_status()  # Salva o novo status criptografado
            logging.info(f"Status alterado para: {status}")
        elif "desbloquear" in message.text.lower():
            status = "desbloqueado"
            salvar_status()  # Salva o novo status criptografado
            logging.info(f"Status alterado para: {status}")
        return status
    else:
        logging.warning(f"Usuário não autorizado tentou enviar mensagem: {message.chat.id}")
        return status  # Retorna o status atual se o usuário não for autorizado

# Função para responder ao comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.id == int(CHAT_ID_AUTORIZADO):
        bot.reply_to(message, "Olá! Você está autorizado a controlar o sistema. Envie 'bloquear' ou 'desbloquear' para controlar o status.")
        mostrar_status_atual(message)  # Exibe o status atual quando o bot é iniciado
    else:
        bot.reply_to(message, "Acesso negado. Você não está autorizado a usar este bot.")
        logging.warning(f"Usuário não autorizado tentou acessar: {message.chat.id}")

# Função para mostrar o status atual
def mostrar_status_atual(message):
    bot.send_message(message.chat.id, f"O status atual do sistema é: {get_status().capitalize()}")

# Função para verificar o status e permitir ou bloquear ações
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global status

    # Se o sistema estiver bloqueado, não permite alteração do status
    if status == "bloqueado":
        if "desbloquear" in message.text.lower():
            status = "desbloqueado"
            salvar_status()  # Salva o novo status criptografado
            bot.reply_to(message, "Sistema desbloqueado com sucesso!")
            logging.info("Sistema desbloqueado pelo usuário.")
        else:
            bot.reply_to(message, "O sistema está bloqueado. Operações não permitidas até ser desbloqueado.")
            logging.info("Tentativa de operação enquanto o sistema está bloqueado.")
    else:  # Sistema desbloqueado, permite qualquer operação
        status = atualizar_status(message)
        bot.reply_to(message, f"O status foi alterado para: {status.capitalize()}.")

# Função para atualizar o status periodicamente em tempo real (logando apenas alterações)
def atualizar_periodicamente():
    """Loga o status inicial e apenas alterações subsequentes."""
    global status, ultimo_status_logado
    logou_inicial = False  # Variável para rastrear se já logamos o status inicial

    while True:
        # Loga o status inicial apenas uma vez
        if not logou_inicial:
            logging.info(f"Status inicial: {status.capitalize()}")
            ultimo_status_logado = status
            logou_inicial = True
        else:
            # Sempre registra que o sistema está funcionando
            logging.info("O bot está ativo e aguardando comandos.")

        if status != ultimo_status_logado:
            logging.info(f"Status atualizado: {status.capitalize()}")
            ultimo_status_logado = status

        time.sleep(5)  # Aguarda 5 segundos antes de verificar novamente

# Função para garantir que as threads estão sendo executadas corretamente
def start_bot():
    try:
        logging.info("Bot iniciado, aguardando comandos...")
        bot.polling()
    except Exception as e:
        logging.error(f"Erro ao iniciar o bot: {e}")

# Função para parar o bot
def parar_bot():
    logging.info("Bot interrompido.")
    bot.stop_polling()


def start():
    """Função para rodar o bot e o status periodicamente ao mesmo tempo"""
    if __name__ == "__main__":
        logging.info("Iniciando o bot e as threads...")

        # Criando threads para executar as funções simultaneamente
        thread_bot = threading.Thread(target=start_bot)
        thread_bot.daemon = True  # Permite que o programa termine mesmo com a thread do bot rodando
        thread_bot.start()

        thread_status = threading.Thread(target=atualizar_periodicamente)
        thread_status.daemon = True  # Permite que o programa termine mesmo com a thread de status rodando
        thread_status.start()

        try:
            # Manter o programa ativo
            while True:
                time.sleep(1)  # Aguarda para manter o programa ativo
        except KeyboardInterrupt:
            logging.info("Interrupção recebida. Finalizando o bot...")
            # Feche qualquer recurso ou finalização necessária
            bot.stop_polling()
            logging.info("Bot finalizado.")

# Adição de verificação de execução principal
if __name__ == "__main__":
    start()
