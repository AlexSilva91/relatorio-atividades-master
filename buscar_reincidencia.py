import pandas as pd
import logging
from datetime import datetime, timedelta

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
    try:
        logging.info(f"Iniciando leitura do arquivo: {caminho_arquivo}, planilha: {planilha_nome}")
        df = pd.read_excel(caminho_arquivo, sheet_name=planilha_nome)
        df = df.drop(df.index[:7])
        logging.info("Planilha lida com sucesso.")
        return df
    except FileNotFoundError:
        logging.error(f"Erro: O arquivo '{caminho_arquivo}' não pôde ser encontrado.")
        return None
    except Exception as e:
        logging.error(f"Erro ao tentar ler o arquivo: {e}")
        return None

def extrair_colunas_interesse(df):
    try:
        logging.info("Iniciando extração das colunas de interesse.")
        contrato = df.iloc[:, 2]
        atividade = df.iloc[:, 8].str.lower()
        data = pd.to_datetime(df.iloc[:, 14], errors='coerce')
        tecnico = df.iloc[:, 15]
        logging.info("Colunas extraídas com sucesso.")
        return tecnico, contrato, atividade, data
    except Exception as e:
        logging.error(f"Erro ao extrair colunas: {e}")
        return None, None, None, None

def gerar_dicionario(tecnico, contrato, atividade, data):
    dados_contratos = {}
    try:
        logging.info("Iniciando geração do dicionário de contratos.")
        for cont, atv, dt, tec in zip(contrato, atividade, data, tecnico):
            if isinstance(tec, str) and tec.strip() != '':
                if cont not in dados_contratos:
                    dados_contratos[cont] = []
                dados_contratos[cont].append({'atividade': atv, 'data': dt, 'tecnico': tec})
        logging.info("Dicionário de contratos gerado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao gerar o dicionário de contratos: {e}")
    return dados_contratos

def filtrar_atividades(dados_contratos, atividades_a_exibir):
    dados_filtrados = {}
    try:
        logging.info("Iniciando filtragem das atividades dos contratos.")
        for contrato, atividades in dados_contratos.items():
            atividades_filtradas = []
            for atividade in atividades:
                if atividade['atividade'].lower() in atividades_a_exibir:
                    atividades_filtradas.append(atividade)
            if atividades_filtradas:
                dados_filtrados[contrato] = atividades_filtradas
        logging.info("Atividades filtradas com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao filtrar atividades: {e}")
    return dados_filtrados

def consolidar_contratos_funcao(dados_filtrados, atividades_a_exibir):
    contratos_consolidados = {}
    try:
        logging.info("Iniciando consolidação dos contratos.")
        for contrato, atividades in dados_filtrados.items():
            atividades_filtradas = []
            for atividade in atividades:
                if atividade['atividade'].lower() in atividades_a_exibir or atividade['atividade'].lower() == 'corretiva':
                    atividades_filtradas.append(atividade)
            if len(atividades_filtradas) > 1 or any(atividade['atividade'].lower() == 'corretiva' for atividade in atividades_filtradas):
                contratos_consolidados[contrato] = {'atividades': atividades_filtradas}
        logging.info("Contratos consolidados com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao consolidar contratos: {e}")
    return contratos_consolidados

def filtrar_contratos(contratos_consolidados, atividades_a_exibir):
    contratos_filtrados = {}
    try:
        logging.info("Iniciando filtragem dos contratos.")
        for contrato, info in contratos_consolidados.items():
            if len(info['atividades']) > 1 or any(atividade['atividade'].lower() == 'corretiva' for atividade in info['atividades']):
                atividades_filtradas = []
                for atividade in info['atividades']:
                    if atividade['atividade'].lower() in atividades_a_exibir:
                        atividades_filtradas.append(atividade)
                if atividades_filtradas:
                    contratos_filtrados[contrato] = {'atividades': atividades_filtradas}
        logging.info("Contratos filtrados com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao filtrar contratos: {e}")
    return contratos_filtrados

def verificar_e_salvar_contratos(contratos_filtrados):
    contratos_salvos = {}
    try:
        logging.info("Iniciando verificação e salvamento de contratos.")
        for contrato, info in contratos_filtrados.items():
            if any(atividade['atividade'].lower() == 'corretiva' for atividade in info['atividades']):
                contratos_salvos[contrato] = info
            else:
                datas_servico = [servico['data'] for servico in info['atividades']]
                menor_data_servico = min(datas_servico)
                salvar_contrato = True
                for data_servico in datas_servico:
                    if (data_servico - menor_data_servico).days > 30:
                        salvar_contrato = False
                        break
                if salvar_contrato:
                    contratos_salvos[contrato] = info
        logging.info("Contratos verificados e salvos com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao verificar e salvar contratos: {e}")
    return contratos_salvos

def filtrar_contratos_por_data(contratos_salvos, data_inicial, data_final):
    try:
        logging.info(f"Iniciando filtragem dos contratos por data: {data_inicial} a {data_final}.")
        data_inicial = datetime.strptime(data_inicial, '%Y-%m-%d')
        data_final = datetime.strptime(data_final, '%Y-%m-%d')

        contratos_filtrados = {}

        for contrato, info in contratos_salvos.items():
            atividades_filtradas = []
            for atividade in info['atividades']:
                if data_inicial <= atividade['data'] <= data_final:
                    atividades_filtradas.append(atividade)
            if atividades_filtradas:
                contratos_filtrados[contrato] = {'atividades': atividades_filtradas}

        logging.info("Contratos filtrados por data com sucesso.")
        return contratos_filtrados
    except Exception as e:
        logging.error(f"Erro ao filtrar contratos por data: {e}")
        return {}

def salvar_contratos_em_txt(contratos_salvos, nome_arquivo):
    try:
        logging.info(f"Iniciando salvamento dos contratos em {nome_arquivo}.")
        total_contratos_impressos = 0
        with open(nome_arquivo, 'w') as arquivo:
            for contrato, info in contratos_salvos.items():
                if len(info['atividades']) > 1 or any(atividade['atividade'].lower() == 'corretiva' for atividade in info['atividades']):
                    arquivo.write(f"Contrato: {contrato}\n")
                    arquivo.write("Atividades:\n")
                    for atividade in info['atividades']:
                        arquivo.write(f"Atividade: {atividade['atividade']}, Data: {atividade['data']}, Técnico: {atividade['tecnico']}\n")
                    arquivo.write("\n")
                    total_contratos_impressos += 1
            arquivo.write(f"---------------------------------------\nTotal de contratos impressos: {total_contratos_impressos}\n---------------------------------------")
        logging.info(f"Contratos salvos com sucesso no arquivo {nome_arquivo}.")
    except Exception as e:
        logging.error(f"Erro ao salvar as informações dos contratos no arquivo: {e}")

def buscar_reinicidencia(caminho_arq, data_inicial, data_final):
    try:
        logging.info(f"Iniciando processo de busca de reincidências para o arquivo: {caminho_arq}.")
        caminho_arquivo = caminho_arq
        planilha_nome = "Ordens de Serviço"
        atividades_a_exibir = ["revertido", "verificação", "recorrencia", "retirada sem sucesso", "promessa de pagamento", 
                               "recolha de equipamento", "rede interna", "suporte externo", "migração", "infraestrutura",
                                 "retirada", "ourinetv", "transferência", "reativação", "financeiro", "downgrade", "upgrade",
                                   "cancelamento", "ativação", "suporte interno"]

        df = ler_planilha(caminho_arquivo, planilha_nome)
        if df is not None:
            tecnico, contrato, atividade, data = extrair_colunas_interesse(df)
            dados_contratos = gerar_dicionario(tecnico, contrato, atividade, data)
            dados_filtrados = filtrar_atividades(dados_contratos, atividades_a_exibir)
            contratos_consolidados = consolidar_contratos_funcao(dados_filtrados, atividades_a_exibir)
            contratos_filtrados = filtrar_contratos(contratos_consolidados, atividades_a_exibir)
            contratos_salvos = verificar_e_salvar_contratos(contratos_filtrados)
            contratos_filtrados_por_data = filtrar_contratos_por_data(contratos_salvos, data_inicial, data_final)
            salvar_contratos_em_txt(contratos_filtrados_por_data, "contratos_reincidentes.txt")
        logging.info("Processo de busca de reincidências finalizado com sucesso.")
    except Exception as e:
        logging.error(f"Erro no processo geral: {e}")
