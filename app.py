import threading
import logging
from PyQt5.QtWidgets import QApplication, QDateEdit, QVBoxLayout, QMainWindow, QFileDialog, QPushButton, QLabel, QWidget, QHBoxLayout, QProgressBar
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
import os
from acessar_planilha import processar_dados_planilha
from buscar_reincidencia import buscar_reinicidencia
from bot_module import get_status, start_bot, parar_bot
from utils.validation import validation_legth_sheet

# Criação de um logger centralizado
logger = logging.getLogger(__name__)

# Configuração do logging para salvar em arquivo e exibir no console
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler(".logs.log"),  # Salva logs em 'api_logs.log'
        logging.StreamHandler()  # Exibe logs no console também
    ]
)

# Classe para executar tarefas em um thread separado
class WorkerThread(QThread):
    progress = pyqtSignal(int)  # Sinal para atualizar a barra de progresso
    finished = pyqtSignal()     # Sinal para indicar que a tarefa terminou

    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        self.args = args

    def run(self):
        total_steps = 100  # 100 passos para completar a barra de progresso
        for i in range(total_steps):
            if i == 97:  # Executa a função quando a barra de progresso estiver em 98%
                logging.info(f"Executando tarefa com {self.func.__name__} com argumentos {self.args}")
                self.func(*self.args)
            self.progress.emit(i + 1)  # Atualiza a barra de progresso
            self.msleep(10)  # Preenchimento rápido da barra

        self.finished.emit()

# Definição da classe da janela principal
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configurações da janela principal
        self.setWindowTitle("Selecionar Arquivo")
        self.setGeometry(100, 100, 400, 250)  # Aumentei a altura da janela para acomodar a barra de progresso
        self.setWindowIcon(QIcon('report.ico'))

        # Configuração do widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout principal da janela
        self.central_layout = QHBoxLayout()
        self.central_layout.setAlignment(Qt.AlignCenter)
        self.central_widget.setLayout(self.central_layout)

        # Layout vertical para organizar os widgets
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.central_layout.addLayout(self.layout)

        # Botão para abrir arquivo
        self.button_open = QPushButton("Abrir Arquivo")
        self.button_open.setFixedSize(200, 30)
        self.button_open.setStyleSheet("background-color: #007bff; color: white; border: none;")
        self.button_open.clicked.connect(self.open_file)
        self.layout.addWidget(self.button_open)

        # Widgets para seleção de datas
        self.title_label1 = QLabel("Data Inicial:")
        self.date_edit1 = QDateEdit()
        self.date_edit1.setFixedSize(200, 30)
        self.date_edit1.setCalendarPopup(True)
        self.date_edit1.setDate(QDate.currentDate())
        self.date_edit1.dateChanged.connect(self.check_date1)

        self.title_label2 = QLabel("Data Final:")
        self.date_edit2 = QDateEdit()
        self.date_edit2.setFixedSize(200, 30)
        self.date_edit2.setCalendarPopup(True)
        self.date_edit2.setDate(QDate.currentDate())
        self.date_edit2.dateChanged.connect(self.check_date2)

        self.layout.addWidget(self.title_label1)
        self.layout.addWidget(self.date_edit1)
        self.layout.addWidget(self.title_label2)
        self.layout.addWidget(self.date_edit2)
        

        # Botões para gerar relatórios
        self.button_new_function = QPushButton("Gerar relatório")
        self.button_new_function.setFixedSize(200, 30)
        self.button_new_function.setStyleSheet("background-color: #28a745; color: white; border: none;")
        self.button_new_function.clicked.connect(self.start_processar_dados)
        self.layout.addWidget(self.button_new_function)

        self.button_new_function2 = QPushButton("Gerar relatório de reincidência")
        self.button_new_function2.setFixedSize(200, 30)
        self.button_new_function2.setStyleSheet("background-color: #dc3545; color: white; border: none;")
        self.button_new_function2.clicked.connect(self.start_buscar_reincidencia)
        self.layout.addWidget(self.button_new_function2)

        # Label para exibir informações sobre o arquivo selecionado
        self.label_file = QLabel()
        self.layout.addWidget(self.label_file)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(200, 15)
        self.progress_bar.setValue(0)  # Inicializa com 0%
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #28a745; }")  # Cor verde
        self.progress_bar.setAlignment(Qt.AlignCenter)  # Alinha o texto de porcentagem no centro
        self.layout.addWidget(self.progress_bar)

        # Timer para atualizar o status em tempo real
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_status)
        self.status_timer.start(1000)  # Verifica o status a cada 1000ms (1 segundo)

        # Inicialização das variáveis
        self.caminho_arquivo = None
        self.data_inicial = None
        self.data_final = None
        self.status_anterior = None

        # Inicializa o bot do Telegram
        self.bot_thread = threading.Thread(target=start_bot)
        self.bot_thread.daemon = True
        self.bot_thread.start()

        # Atualiza o status assim que a interface é carregada
        self.check_status()

    def closeEvent(self, event):
        """Quando a janela for fechada, o bot será interrompido também."""
        parar_bot()  # Função para parar o bot
        logging.info("Bot interrompido ao fechar a janela.")
        event.accept()

    def check_status(self):
        # Verifica o status do sistema e ajusta a interface
        status = get_status()  # Pega o status atualizado do sistema

        # Verifica se o status mudou antes de registrar
        if status != self.status_anterior:
            logging.info(f"Status do sistema: {status}")
            self.status_anterior = status  # Atualiza o status anterior

            if status == "desbloqueado":
                self.show_status_message("Acesso liberado!")
                self.label_file.setStyleSheet("color: green;")
                self.label_file.setAlignment(Qt.AlignCenter)  

        if status == "bloqueado":
            # Desabilita os campos e exibe mensagem
            self.date_edit1.setDisabled(True)
            self.date_edit2.setDisabled(True)
            self.button_open.setDisabled(True)
            self.button_new_function.setDisabled(True)
            self.button_new_function2.setDisabled(True)
            self.label_file.setText("Acesso bloqueado!")
            self.label_file.setStyleSheet("color: red;")
            self.label_file.setAlignment(Qt.AlignCenter)  

        else:
            # Habilita os campos se desbloqueado
            self.date_edit1.setEnabled(True)
            self.date_edit2.setEnabled(True)
            self.button_open.setEnabled(True)
            self.button_new_function.setEnabled(True)
            self.button_new_function2.setEnabled(True)

    def show_status_message(self, message):
        """Exibe uma mensagem informando o status ao usuário"""
        self.label_file.setText(message)

    def check_date1(self, new_date):
        # Verifica se a data inicial é maior que a data final
        if new_date.isNull():
            self.data_inicial = QDate.currentDate().toString(Qt.ISODate)
            self.date_edit1.setDate(QDate.currentDate())  # Define a data inicial para a data atual
        else:
            # Verifica se a data inicial é maior que a data final
            if new_date > QDate.currentDate():
                self.date_edit1.setDate(QDate.currentDate())  # Altera para a data atual
                self.data_inicial = QDate.currentDate().toString(Qt.ISODate)
                logging.warning("Data inicial não pode ser maior que a data atual. Data alterada para hoje.")
            else:
                self.data_inicial = new_date.toString(Qt.ISODate)
                logging.info(f"Data inicial atualizada para: {self.data_inicial}")

        # Verifica se a data final é menor que a data inicial
        if self.data_final and QDate.fromString(self.data_final, Qt.ISODate) < new_date:
            self.date_edit2.setDate(new_date)  # Define a data final como a data inicial
            self.data_final = new_date.toString(Qt.ISODate)
            logging.warning("Data final não pode ser anterior à data inicial. Data final ajustada para a data inicial.")

    def check_date2(self, new_date):
        # Verifica se a data final é maior que a data atual
        if new_date.isNull():
            self.data_final = QDate.currentDate().toString(Qt.ISODate)
            self.date_edit2.setDate(QDate.currentDate())  # Define a data final para a data atual
        else:
            # Verifica se a data final é maior que a data atual
            if new_date > QDate.currentDate():
                self.date_edit2.setDate(QDate.currentDate())  # Altera para a data atual
                self.data_final = QDate.currentDate().toString(Qt.ISODate)
                logging.warning("Data final não pode ser maior que a data atual. Data alterada para hoje.")
            else:
                self.data_final = new_date.toString(Qt.ISODate)
                logging.info(f"Data final atualizada para: {self.data_final}")

        # Verifica se a data final é menor que a data inicial
        if self.data_inicial and QDate.fromString(self.data_final, Qt.ISODate) < QDate.fromString(self.data_inicial, Qt.ISODate):
            self.date_edit1.setDate(QDate.fromString(self.data_final, Qt.ISODate))  # Ajusta a data inicial para a data final
            self.data_inicial = self.data_final
            logging.warning("Data inicial não pode ser maior que a data final. Data inicial ajustada para a data final.")

    def open_file(self):
        # Método para abrir o arquivo
        filename, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo")
        if filename:
            if filename.endswith('.xlsx') and validation_legth_sheet(filename):
                self.caminho_arquivo = filename
                file_name = os.path.basename(filename)
                self.label_file.setText(f"{file_name}")
                self.label_file.setAlignment(Qt.AlignCenter)
                logging.info(f"Arquivo selecionado: {file_name}")
            else:
                self.label_file.setText("Arquivo inválido!")
                self.label_file.setStyleSheet("color: red;")
                self.caminho_arquivo = None
                logging.warning("Arquivo selecionado não é um .xlsx. ou o número de colunas é superior a 22")

    def start_processar_dados(self):
        # Inicia o processamento de dados
        if not self.caminho_arquivo:
            self.label_file.setText("Por favor, selecione um arquivo.")
            self.label_file.setStyleSheet("color: red;")
            logging.error("Nenhum arquivo foi selecionado.")
            return

        self.label_file.setText("Gerando...")
        self.label_file.setStyleSheet("color: orange;")
        self.progress_bar.setValue(0)  # Resetando a barra de progresso
        logging.info("Iniciando o processamento de dados...")

        self.thread = WorkerThread(processar_dados_planilha, self.caminho_arquivo, self.data_inicial, self.data_final)
        self.thread.progress.connect(self.update_progress_bar)
        self.thread.finished.connect(self.on_process_finished)
        self.thread.start()

    def start_buscar_reincidencia(self):
        # Inicia a busca por reincidência
        if not self.caminho_arquivo:
            self.label_file.setText("Por favor, selecione um arquivo.")
            self.label_file.setStyleSheet("color: red;")
            logging.error("Nenhum arquivo foi selecionado.")
            return

        self.label_file.setText("Buscando reincidências...")
        self.label_file.setStyleSheet("color: orange;")
        self.progress_bar.setValue(0)  # Resetando a barra de progresso
        logging.info("Iniciando a busca por reincidências...")

        self.thread2 = WorkerThread(buscar_reinicidencia, self.caminho_arquivo, self.data_inicial, self.data_final)
        self.thread2.progress.connect(self.update_progress_bar)
        self.thread2.finished.connect(self.on_process_finished)
        self.thread2.start()

    def update_progress_bar(self, value):
        # Atualiza a barra de progresso com o valor recebido
        self.progress_bar.setValue(value)

    def on_process_finished(self):
        # Avisa que o processo foi concluído
        self.label_file.setText("Processamento Concluído!")
        self.label_file.setStyleSheet("color: green;")
        self.progress_bar.setValue(100)
        logging.info("Processamento concluído com sucesso.")

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
