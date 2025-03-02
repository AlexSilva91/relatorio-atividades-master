import pandas as pd
import logging

global PLANILHA_NOME
PLANILHA_NOME = "Ordens de Serviço"

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

def contar_colunas(caminho_arquivo, planilha_nome):
    """
    Conta o número total de colunas em uma planilha Excel.

    Args:
        caminho_arquivo (str): Caminho do arquivo Excel.
        planilha_nome (str): Nome da planilha a ser lida.

    Returns:
        int: Número total de colunas na planilha.
    """
    logging.info(f"Lendo a planilha: {caminho_arquivo}, Planilha: {planilha_nome}")
    df = pd.read_excel(caminho_arquivo, sheet_name=planilha_nome)
    numero_colunas = df.shape[1]
    logging.info(f"Total de colunas: {numero_colunas}")
    return numero_colunas

def validation_legth_sheet(caminho):
    global PLANILHA_NOME
    number = contar_colunas(caminho, PLANILHA_NOME)
    if number == 22:
        return True
    else:
        return False
    