import pandas as pd
import os
from collections import defaultdict, Counter
from datetime import datetime
import logging

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

def ler_planilha(caminho_arquivo, planilha_nome):
    """
    Lê uma planilha Excel e remove as primeiras 7 linhas.

    Args:
        caminho_arquivo (str): Caminho do arquivo Excel.
        planilha_nome (str): Nome da planilha a ser lida.

    Returns:
        DataFrame: DataFrame contendo os dados da planilha a partir da linha 8.
    """
    logging.info(f"Lendo planilha {planilha_nome} do arquivo {caminho_arquivo}")
    df = pd.read_excel(caminho_arquivo, sheet_name=planilha_nome)
    df = df.drop(df.index[:7])
    logging.debug(f"Planilha carregada com {len(df)} registros")
    return df

def extrair_colunas_interesse(df):
    """
    Extrai colunas específicas do DataFrame para análise.

    Args:
        df (DataFrame): DataFrame de onde as colunas serão extraídas.

    Returns:
        Series: Coluna de técnicos.
        Series: Coluna de auxiliares.
        Series: Coluna de atividades.
        Series: Coluna de datas convertidas para formato de data.
    """
    logging.info("Extraindo colunas de interesse")
    atividade = df.iloc[:, 8]
    tecnico = df.iloc[:, 15]
    auxiliar = df.iloc[:, 16]
    data = pd.to_datetime(df.iloc[:, 14], errors='coerce').dt.date
    logging.debug(f"Colunas extraídas: {len(tecnico)} técnicos, {len(auxiliar)} auxiliares, {len(atividade)} atividades, {len(data)} datas")
    return tecnico, auxiliar, atividade, data

def criar_lista_tuplas(tecnico, auxiliar, atividade, data):
    """
    Cria uma lista de tuplas contendo as informações dos técnicos, auxiliares, atividades e datas.

    Args:
        tecnico (Series): Coluna de técnicos.
        auxiliar (Series): Coluna de auxiliares.
        atividade (Series): Coluna de atividades.
        data (Series): Coluna de datas.

    Returns:
        list: Lista de tuplas (tecnico, auxiliar, atividade, data).
    """
    logging.info("Criando lista de tuplas")
    return list(zip(tecnico, auxiliar, atividade, data))

def filtrar_por_datas(lista_tuplas, data_inicial, data_final):
    """
    Filtra a lista de tuplas por um intervalo de datas.

    Args:
        lista_tuplas (list): Lista de tuplas (tecnico, auxiliar, atividade, data).
        data_inicial (date): Data inicial do filtro.
        data_final (date): Data final do filtro.

    Returns:
        list: Lista de tuplas filtradas por data.
    """
    logging.info(f"Filtrando registros entre {data_inicial} e {data_final}")
    filtered = [(tecnico, auxiliar, atividade, data) for tecnico, auxiliar, atividade, data in lista_tuplas if data_inicial <= data <= data_final]
    logging.debug(f"Total de registros filtrados: {len(filtered)}")
    return filtered

def contar_atividades_por_auxiliar(lista_tuplas, tecnicos_a_evitar, auxiliares_a_evitar):
    """
    Conta as atividades realizadas por cada auxiliar, filtrando técnicos e auxiliares a evitar.

    Args:
        lista_tuplas (list): Lista de tuplas (tecnico, auxiliar, atividade, data).
        tecnicos_a_evitar (list): Lista de técnicos a evitar.
        auxiliares_a_evitar (list): Lista de auxiliares a evitar.

    Returns:
        dict: Dicionário com técnicos como chave e conjuntos de auxiliares como valor.
        dict: Dicionário com chaves (tecnico, auxiliar) e contadores de atividades como valor.
    """
    logging.info("Contando atividades por auxiliar, excluindo técnicos e auxiliares a evitar")
    vinculo_tecnico_auxiliares = defaultdict(set)
    contagem_por_auxiliar = defaultdict(Counter)

    for tecnico, auxiliar, atividade, _ in lista_tuplas:
        if not isinstance(tecnico, str) or tecnico.strip() == "":
            continue

        if tecnico in tecnicos_a_evitar or auxiliar in auxiliares_a_evitar:
            continue

        if pd.notna(auxiliar):  # Verifica se o valor não é NaN
            vinculo_tecnico_auxiliares[tecnico].add(auxiliar)
            contagem_por_auxiliar[(tecnico, auxiliar)][atividade] += 1

    logging.debug(f"Vínculos de técnicos e auxiliares: {len(vinculo_tecnico_auxiliares)} técnicos")
    logging.debug(f"Contagem de atividades por auxiliar: {len(contagem_por_auxiliar)} registros")
    return dict(vinculo_tecnico_auxiliares), dict(contagem_por_auxiliar)

def gerar_dicionario_formatado(caminho_arquivo, tecnicos_a_evitar, auxiliares_a_evitar, data_inicial=None, data_final=None):
    """
    Gera um relatório formatado com contagens de atividades realizadas por técnicos e auxiliares.

    Args:
        caminho_arquivo (str): Caminho do arquivo Excel.
        tecnicos_a_evitar (list): Lista de técnicos a evitar.
        auxiliares_a_evitar (list): Lista de auxiliares a evitar.
        data_inicial (date, optional): Data inicial do filtro. Default é None.
        data_final (date, optional): Data final do filtro. Default é None.

    Returns:
        str: Relatório formatado.
        int: Total de serviços.
        dict: Dicionário com técnicos e seus auxiliares.
        dict: Dicionário com contagens de atividades por técnico e auxiliar.
    """
    logging.info(f"Iniciando a geração do relatório para o arquivo {caminho_arquivo}")
    planilha_nome = "Ordens de Serviço"
    df = ler_planilha(caminho_arquivo, planilha_nome)
    tecnico, auxiliar, atividade, data = extrair_colunas_interesse(df)
    list_tuplas = criar_lista_tuplas(tecnico, auxiliar, atividade, data)
    
    if data_inicial and data_final:
        list_tuplas = filtrar_por_datas(list_tuplas, data_inicial, data_final)

    vinculo_tecnico_auxiliares, contagem_por_auxiliar = contar_atividades_por_auxiliar(list_tuplas, tecnicos_a_evitar, auxiliares_a_evitar)

    total_servicos = 0  # Inicializa o total de serviços

    resultado_formatado = ""
    for tecnico, auxiliares in vinculo_tecnico_auxiliares.items():
        resultado_formatado += f"Técnico: {tecnico}\n"
        for auxiliar in auxiliares:
            resultado_formatado += f"  Auxiliar: {auxiliar}\n"
            for atividade, quantidade in contagem_por_auxiliar.get((tecnico, auxiliar), {}).items():
                resultado_formatado += f"    Serviço: {atividade}, Quantidade: {quantidade}\n"
                total_servicos += quantidade  # Adiciona a quantidade ao total
        resultado_formatado += "\n"

    resultado_formatado += f"Total de serviços: {total_servicos}\n"  # Adiciona o total de serviços ao final do relatório

    logging.debug(f"Relatório gerado com {total_servicos} serviços no total")
    return resultado_formatado, total_servicos, vinculo_tecnico_auxiliares, contagem_por_auxiliar

def get_resultado_formatado(caminho, data_inicial=None, data_final=None):
    """
    Obtém o relatório formatado, filtrando por datas e removendo técnicos e auxiliares a evitar.

    Args:
        caminho (str): Caminho do arquivo Excel.
        data_inicial (str, optional): Data inicial do filtro no formato 'YYYY-MM-DD'. Default é None.
        data_final (str, optional): Data final do filtro no formato 'YYYY-MM-DD'. Default é None.

    Returns:
        tuple: Relatório formatado, total de serviços, vínculo entre técnicos e auxiliares, contagem de atividades.
    """
    # Lista de técnicos a evitar
    lista_tecnicos_a_evitar = ["tiago.peres", "eguinailson.nunes", "geimerson.alves", "NOC", "jonatas.thiago"]

    # Lista de auxiliares a evitar
    lista_auxiliares_a_evitar = ["tiago.peres", "eguinailson.nunes", "evandro.zuza", "geimerson.alves", "NOC", "jonatas.thiago"]

    data_init = datetime.strptime(data_inicial, '%Y-%m-%d').date() if data_inicial else None
    data_end = datetime.strptime(data_final, '%Y-%m-%d').date() if data_final else None

    # Uso da função para obter a string formatada
    logging.info("Obtendo resultado formatado com base nas datas e listas de exclusão")
    resultado_formatado, total_servicos, vinculo_tecnico_auxiliares, contagem_por_auxiliar = gerar_dicionario_formatado(caminho, lista_tecnicos_a_evitar, lista_auxiliares_a_evitar, data_init, data_end)
    
    return resultado_formatado, total_servicos, vinculo_tecnico_auxiliares, contagem_por_auxiliar
