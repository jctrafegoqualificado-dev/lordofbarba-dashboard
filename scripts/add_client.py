import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import json
import sys

# Config
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDS")

# Inputs via variáveis de ambiente (GitHub Actions)
NOME = os.environ.get("CLIENTE_NOME")
TELEFONE = os.environ.get("CLIENTE_TELEFONE")
DATA_INICIO = os.environ.get("CLIENTE_DATA")  # formato DD/MM/AAAA
PLANO = os.environ.get("CLIENTE_PLANO", "Mensal")
VALOR = os.environ.get("CLIENTE_VALOR", "99.90")

def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDS)
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

def calcular_proximo_vencimento(data_inicio_str):
    data_inicio = datetime.strptime(data_inicio_str, "%d/%m/%Y")
    proximo = data_inicio + relativedelta(months=1)
    return proximo.strftime("%d/%m/%Y")

def add_client():
    sheet = get_sheet()

    # Verifica se é a primeira linha (adiciona cabeçalho se necessário)
    existing = sheet.get_all_values()
    if not existing or existing[0] != ["Nome", "Telefone", "Data Inicio", "Proximo Vencimento", "Plano", "Valor", "Status"]:
        sheet.insert_row(["Nome", "Telefone", "Data Inicio", "Proximo Vencimento", "Plano", "Valor", "Status"], 1)

    proximo_vencimento = calcular_proximo_vencimento(DATA_INICIO)

    nova_linha = [
        NOME,
        TELEFONE,
        DATA_INICIO,
        proximo_vencimento,
        PLANO,
        VALOR,
        "ATIVO"
    ]

    sheet.append_row(nova_linha)
    print(f"✅ Cliente adicionado: {NOME} | Vence em: {proximo_vencimento}")

if __name__ == "__main__":
    add_client()
