import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from anthropic import Anthropic
import requests
import os
import json

# Config
WHATSAPP_PHONE = "5541997310873"
ZAPI_INSTANCE = "3F09CA3C0ADD02F7678BD2564DAA07CC"
ZAPI_TOKEN = "9B2FBF94E60CBE1FCC516636"
ZAPI_CLIENT_TOKEN = "F4b228d7ef99e40bb966f54882859a555S"
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDS")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Modo de operação: ADD_TRANSACTION ou REPORT
MODE = os.environ.get("MODE", "REPORT")

# Dados da transação (quando MODE=ADD_TRANSACTION)
TIPO = os.environ.get("TIPO", "")           # ENTRADA ou SAIDA
VALOR = os.environ.get("VALOR", "")         # ex: 150.00
DESCRICAO = os.environ.get("DESCRICAO", "") # ex: Cortes do dia
CATEGORIA = os.environ.get("CATEGORIA", "") # ex: Serviços, Produtos, Aluguel

def get_sheet(aba="Financeiro"):
    creds_dict = json.loads(GOOGLE_CREDS)
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    try:
        sheet = spreadsheet.worksheet(aba)
    except:
        sheet = spreadsheet.add_worksheet(title=aba, rows="1000", cols="10")
        sheet.append_row(["Data", "Tipo", "Categoria", "Descricao", "Valor", "Saldo Acumulado"])
    return sheet

def send_whatsapp(message):
    url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}/send-text"
    headers = {"Client-Token": ZAPI_CLIENT_TOKEN}
    payload = {
        "phone": WHATSAPP_PHONE,
        "message": message
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"WhatsApp: {response.status_code} {response.text}")

def add_transaction():
    sheet = get_sheet()
    records = sheet.get_all_records()

    # Calcula saldo acumulado
    saldo = 0
    for r in records:
        try:
            v = float(str(r.get("Valor", "0")).replace(",", "."))
            if r.get("Tipo", "").upper() == "ENTRADA":
                saldo += v
            else:
                saldo -= v
        except:
            continue

    valor_float = float(VALOR.replace(",", "."))
    if TIPO.upper() == "ENTRADA":
        saldo += valor_float
    else:
        saldo -= valor_float

    nova_linha = [
        datetime.now().strftime("%d/%m/%Y %H:%M"),
        TIPO.upper(),
        CATEGORIA or "Geral",
        DESCRICAO,
        f"{valor_float:.2f}",
        f"{saldo:.2f}"
    ]

    sheet.append_row(nova_linha)

    simbolo = "💰" if TIPO.upper() == "ENTRADA" else "💸"
    msg = (
        f"{simbolo} LORD OF BARBA - LANÇAMENTO\n\n"
        f"Tipo: {TIPO.upper()}\n"
        f"Descrição: {DESCRICAO}\n"
        f"Categoria: {CATEGORIA or 'Geral'}\n"
        f"Valor: R$ {valor_float:.2f}\n"
        f"Saldo atual: R$ {saldo:.2f}"
    )
    print(msg)
    send_whatsapp(msg)

def generate_report():
    sheet = get_sheet()
    records = sheet.get_all_records()

    if not records:
        print("Sem dados para gerar relatório.")
        return

    # Filtra o mês atual
    mes_atual = datetime.now().strftime("%m/%Y")
    registros_mes = []
    for r in records:
        try:
            data_str = str(r.get("Data", ""))[:10]
            data = datetime.strptime(data_str, "%d/%m/%Y")
            if data.strftime("%m/%Y") == mes_atual:
                registros_mes.append(r)
        except:
            continue

    # Monta resumo para a IA
    total_entradas = sum(float(str(r["Valor"]).replace(",",".")) for r in registros_mes if r.get("Tipo","").upper() == "ENTRADA")
    total_saidas = sum(float(str(r["Valor"]).replace(",",".")) for r in registros_mes if r.get("Tipo","").upper() == "SAIDA")
    saldo_mes = total_entradas - total_saidas

    # Monta contexto detalhado
    contexto = f"Barbearia: Lord of Barba (Curitiba, bairro Xaxim)\n"
    contexto += f"Período: {mes_atual}\n\n"
    contexto += f"RESUMO DO MÊS:\n"
    contexto += f"Total de entradas: R$ {total_entradas:.2f}\n"
    contexto += f"Total de saídas: R$ {total_saidas:.2f}\n"
    contexto += f"Saldo do mês: R$ {saldo_mes:.2f}\n\n"
    contexto += "LANÇAMENTOS:\n"
    for r in registros_mes:
        tipo = r.get("Tipo","")
        simbolo = "+" if tipo.upper() == "ENTRADA" else "-"
        contexto += f"{r.get('Data','')} | {simbolo} R$ {r.get('Valor','')} | {r.get('Descricao','')} ({r.get('Categoria','')})\n"

    # Chama Claude para análise
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Você é um agente financeiro especializado em barbearias. "
                    f"Analise os dados financeiros abaixo e gere um relatório CURTO e DIRETO "
                    f"(máximo 300 palavras) com: resumo financeiro, pontos de atenção e 1 recomendação prática. "
                    f"Use emojis para facilitar leitura. Responda em português.\n\n{contexto}"
                )
            }
        ]
    )

    analise = response.content[0].text

    msg = f"📊 RELATÓRIO FINANCEIRO - LORD OF BARBA\n{mes_atual}\n\n{analise}"
    print(msg)
    send_whatsapp(msg)

if __name__ == "__main__":
    if MODE == "ADD_TRANSACTION":
        add_transaction()
    else:
        generate_report()
