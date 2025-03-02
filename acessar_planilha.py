import pandas as pd
import os
from datetime import datetime
from collections import Counter, OrderedDict
from auxiliar_por_atividade import get_resultado_formatado
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
    logging.info(f"Lendo a planilha: {caminho_arquivo}, Planilha: {planilha_nome}")
    df = pd.read_excel(caminho_arquivo, sheet_name=planilha_nome)
    df = df.drop(df.index[:7])
    logging.info("Planilha lida com sucesso")
    return df

def extrair_colunas_interesse(df):
    """
    Extrai colunas específicas do DataFrame para análise.

    Args:
        df (DataFrame): DataFrame de onde as colunas serão extraídas.

    Returns:
        Series: Coluna de técnicos.
        Series: Coluna de atividades.
        Series: Coluna de datas convertidas para formato de data.
    """
    logging.info("Extraindo colunas de interesse (Técnico, Atividade, Data)")
    atividade = df.iloc[:, 8]
    data = pd.to_datetime(df.iloc[:, 14], errors='coerce').dt.date
    tecnico = df.iloc[:, 15]
    return tecnico, atividade, data

def criar_lista_tuplas(tecnico, atividade, data):
    """
    Cria uma lista de tuplas contendo as informações dos técnicos, atividades e datas.

    Args:
        tecnico (Series): Coluna de técnicos.
        atividade (Series): Coluna de atividades.
        data (Series): Coluna de datas.

    Returns:
        list: Lista de tuplas (tecnico, atividade, data).
    """
    logging.info("Criando lista de tuplas (Técnico, Atividade, Data)")
    return list(zip(tecnico, atividade, data))

def filtrar_atividades_por_data(data_inicial, data_final, lista_tuplas):
    """
    Filtra a lista de tuplas por um intervalo de datas.

    Args:
        data_inicial (date): Data inicial do filtro.
        data_final (date): Data final do filtro.
        lista_tuplas (list): Lista de tuplas (tecnico, atividade, data).

    Returns:
        list: Lista de tuplas filtradas por data.
    """
    logging.info(f"Filtrando atividades entre {data_inicial} e {data_final}")
    data_inicial_com_horario = datetime.combine(data_inicial, datetime.min.time())
    data_final_com_horario = datetime.combine(data_final, datetime.max.time())

    atividades_filtradas = []
    for tupla in lista_tuplas:
        data_tupla = datetime.combine(tupla[2], datetime.min.time())
        if data_inicial_com_horario <= data_tupla <= data_final_com_horario:
            nome_tecnico, atividade, _ = tupla
            atividades_filtradas.append((nome_tecnico, atividade))
    
    logging.info(f"Encontradas {len(atividades_filtradas)} atividades dentro do intervalo de datas")
    return atividades_filtradas

def contar_atividades_repetidas(lista):
    """
    Conta as ocorrências de cada atividade na lista.

    Args:
        lista (list): Lista de tuplas (tecnico, atividade).

    Returns:
        Counter: Contador de ocorrências de cada atividade.
    """
    logging.info("Contando atividades repetidas")
    return Counter(lista)

def processar_tecnicos_atividades(contagem_atividades, tecnicos_a_evitar):
    """
    Processa as contagens de atividades por técnico, excluindo técnicos a evitar.

    Args:
        contagem_atividades (Counter): Contador de atividades por técnico.
        tecnicos_a_evitar (list): Lista de técnicos a evitar.

    Returns:
        OrderedDict: Dicionário ordenado de técnicos e suas atividades.
    """
    logging.info("Processando atividades por técnico, excluindo técnicos a evitar")
    tecnicos_atividades = {}
    for (tecnico, atividade), contagem in contagem_atividades.items():
        if not isinstance(tecnico, str) or tecnico.strip() == "":
            continue
        if tecnico not in tecnicos_a_evitar:
            if tecnico not in tecnicos_atividades:
                tecnicos_atividades[tecnico] = {}
            tecnicos_atividades[tecnico][atividade] = contagem

    tecnicos_atividades = OrderedDict(sorted(tecnicos_atividades.items()))
    logging.info(f"Encontrados {len(tecnicos_atividades)} técnicos com atividades processadas")
    return tecnicos_atividades

def atualizar_tecnico_atividades(contagem_por_auxiliar, tecnico_atividades):
    """
    Atualiza as contagens de atividades por técnico com base em dados adicionais.

    Args:
        contagem_por_auxiliar (dict): Contagem de atividades por auxiliar.
        tecnico_atividades (dict): Contagem de atividades por técnico.

    Returns:
        dict: Dicionário atualizado de atividades por técnico.
    """
    logging.info("Atualizando atividades por técnico com dados adicionais de auxiliares")
    for auxiliar, atividades in contagem_por_auxiliar.items():
        tecnico = auxiliar[-1]
        if tecnico in tecnico_atividades:
            for atividade, quantidade in atividades.items():
                if atividade in tecnico_atividades[tecnico]:
                    tecnico_atividades[tecnico][atividade] += quantidade
                else:
                    tecnico_atividades[tecnico][atividade] = quantidade
        else:
            tecnico_atividades[tecnico] = atividades

    return tecnico_atividades

def salvar_em_txt(tecnicos_atividades, data_inicial, data_final, resultado_formatado, total_servicos):
    """
    Salva o relatório de atividades por técnico em um arquivo de texto.

    Args:
        tecnicos_atividades (dict): Dicionário de atividades por técnico.
        data_inicial (date): Data inicial do relatório.
        data_final (date): Data final do relatório.
        resultado_formatado (str): String formatada com informações adicionais.
        total_servicos (int): Total de serviços computados.
    """
    logging.info(f"Salvando relatório de atividades de {data_inicial} a {data_final} em arquivo TXT")
    data_init_str = data_inicial.strftime('%Y-%m-%d')
    data_end_str = data_final.strftime('%Y-%m-%d')

    with open(f"Relatório_{data_init_str}_{data_end_str}.txt", "w") as arquivo_saida:
        total_geral = 0
        arquivo_saida.write("-------------------------------------------------\n")
        arquivo_saida.write("-----> Relatório de Atividades por Técnico <-----\n")
        arquivo_saida.write("-------------------------------------------------\n")
        for tecnico, atividades in tecnicos_atividades.items():
            arquivo_saida.write(f"\n********************************\nTécnico: {tecnico}\n********************************\n")
            total_atividades_tecnico = sum(atividades.values())
            total_geral += total_atividades_tecnico
            arquivo_saida.write(f"\n++++++++++++++++++++++++\nTotal de atividades: {total_atividades_tecnico}\n++++++++++++++++++++++++\n")
            for atividade, contagem in atividades.items():
                arquivo_saida.write(f"- Atividade: {atividade} = {contagem}\n")
            arquivo_saida.write("\n")

        arquivo_saida.write(f"********************************\nTotal geral de atividades: {total_geral-total_servicos}\n********************************\n")
        arquivo_saida.write("--------------------------------------------\n")
        arquivo_saida.write("-----> Relatório de ajuda por Técnico <-----\n")
        arquivo_saida.write("--------------------------------------------\n")
        arquivo_saida.write(f"{resultado_formatado}\n")
    logging.info("Relatório salvo com sucesso")

def processar_dados_planilha(caminho, data_init, data_end):
    """
    Processa os dados da planilha para gerar um relatório de atividades por técnico.

    Args:
        caminho (str): Caminho do arquivo Excel.
        data_init (str): Data inicial do filtro no formato 'YYYY-MM-DD'.
        data_end (str): Data final do filtro no formato 'YYYY-MM-DD'.
    """
    logging.info(f"Iniciando o processamento dos dados da planilha {caminho} para o intervalo de {data_init} a {data_end}")
    data_inicial = datetime.strptime(data_init, '%Y-%m-%d')
    data_final = datetime.strptime(data_end, '%Y-%m-%d')

    resultado_formatado, total_servicos, vinculo_tecnico_auxiliares, contagem_por_auxiliar = get_resultado_formatado(caminho, data_init, data_end)

    lista_tecnicos_a_evitar = ["tiago.peres", "eguinailson.nunes", "evandro.zuza", "geimerson.alves", "NOC", "jonatas.thiago"]

    df = ler_planilha(caminho, "Ordens de Serviço")
    tecnico, atividade, data = extrair_colunas_interesse(df)
    lista_tuplas = criar_lista_tuplas(tecnico, atividade, data)
    
    tupla_result = filtrar_atividades_por_data(data_inicial, data_final, lista_tuplas)
    
    contagem_atividades = contar_atividades_repetidas(tupla_result)

    tecnicos_atividades = processar_tecnicos_atividades(contagem_atividades, lista_tecnicos_a_evitar)

    tecnico_atividades_atualizado = atualizar_tecnico_atividades(contagem_por_auxiliar, tecnicos_atividades)

    salvar_em_txt(tecnico_atividades_atualizado, data_inicial, data_final, resultado_formatado, total_servicos)

    logging.info("Processamento concluído com sucesso")

