import gspread
import requests
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import os
import json

# Config
WHATSAPP_PHONE = "5541997319873"
WHATSAPP_APIKEY = os.environ.get("CALLMEBOT_APIKEY")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
GOOGLE_CREDS = os.environ.get("GOOGLE_CREDS")  # JSON string

def get_sheet():
    creds_dict = json.loads(GOOGLE_CREDS)
    scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

def send_whatsapp(message):
    url = "https://api.callmebot.com/whatsapp.php"
    params = {
        "phone": WHATSAPP_PHONE,
        "text": message,
        "apikey": WHATSAPP_APIKEY
    }
    response = requests.get(url, params=params)
    print(f"WhatsApp enviado: {response.status_code}")

def check_billing():
    sheet = get_sheet()
    records = sheet.get_all_records()
    hoje = date.today()
    vencimentos_hoje = []

    for row in records:
        if not row.get("Nome") or row.get("Status", "").upper() == "CANCELADO":
            continue
        try:
            vencimento = datetime.strptime(str(row["Proximo Vencimento"]), "%d/%m/%Y").date()
            if vencimento == hoje:
                vencimentos_hoje.append(row)
        except:
            continue

    if not vencimentos_hoje:
        print("Nenhum vencimento hoje.")
        return

    mensagem = f"🔔 LORD OF BARBA - COBRANÇAS DO DIA {hoje.strftime('%d/%m/%Y')}\n\n"
    for cliente in vencimentos_hoje:
        mensagem += f"👤 {cliente['Nome']}\n"
        mensagem += f"📱 {cliente['Telefone']}\n"
        mensagem += f"💈 Plano: {cliente.get('Plano', 'Assinatura')}\n"
        mensagem += f"💰 Valor: R$ {cliente.get('Valor', '---')}\n"
        mensagem += "─────────────────\n"

    mensagem += f"\nTotal: {len(vencimentos_hoje)} cobrança(s) hoje."
    send_whatsapp(mensagem)
    print(mensagem)

if __name__ == "__main__":
    check_billing()
