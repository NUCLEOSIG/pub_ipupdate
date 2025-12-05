import requests
import time
from datetime import datetime
import logging
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Configuración de Notificaciones (Telegram) ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- Configuración de Notificaciones (Email) ---
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

def send_email_notification(subject, body):
    """Envía una notificación por correo electrónico usando Gmail."""
    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, RECIPIENT_EMAIL]):
        print("Faltan credenciales de correo. No se enviará email.")
        return

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = RECIPIENT_EMAIL
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("Notificación por correo enviada.")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

def send_telegram_notification(message):
    """Envía un mensaje a un chat de Telegram a través de un bot."""
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("Faltan credenciales de Telegram. No se enviará notificación.")
        return
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(api_url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': message})
        response.raise_for_status()
        print("Notificación de Telegram enviada.")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar notificación de Telegram: {e}")
    

IP_FILE = "ip.txt"
URLS_FILE = "urls.txt"

# Configuración de logging para ver la salida en Docker
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_current_ip():
    """Obtiene la IP pública actual."""
    try:
        response = requests.get('https://ident.me', timeout=10)
        response.raise_for_status()  # Lanza un error para respuestas no exitosas (ej. 4xx, 5xx)
        return response.text.strip()
    except requests.RequestException as e:
        logging.error(f"Error al obtener la IP: {e}")
        return None

def read_last_ip():
    """Lee la última IP guardada del archivo."""
    if not os.path.exists(IP_FILE):
        return None
    with open(IP_FILE, "r") as f:
        return f.read().strip()

def write_current_ip(ip):
    """Escribe la IP actual en el archivo."""
    with open(IP_FILE, "w") as f:
        f.write(ip)

def update_dns_records():
    """Llama a las URLs de cPanel para actualizar los registros DNS."""
    if not os.path.exists(URLS_FILE):
        logging.warning(f"El archivo de URLs '{URLS_FILE}' no fue encontrado. Saltando actualización de DNS.")
        return

    with open(URLS_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    for i, url in enumerate(urls, 1):
        try:
            response = requests.get(url, timeout=10)
            logging.info(f"Actualización de URL #{i}: {response.status_code}")
        except requests.RequestException as e:
            logging.error(f"Error al actualizar URL #{i} ({url}): {e}")
    # Enviar notificaciones
    summary_message = "🚨 ¡Alerta! Se actualizaron los registros DNS.:\n\n"
    send_telegram_notification(summary_message)
    send_email_notification("🚨 Alerta Se actualizaron los registros DNS", summary_message)

last_ip = read_last_ip()
logging.info(f"IP inicial guardada: {last_ip}")

while True:
    current_ip = get_current_ip()
    if current_ip:
        logging.info(f"IP actual: {current_ip}")
        if last_ip != current_ip:
            logging.info("La IP ha cambiado. Actualizando registros DNS...")
            update_dns_records()
            write_current_ip(current_ip)
            last_ip = current_ip
        else:
            logging.info("La IP no ha cambiado.")
    else:
        logging.warning("No se pudo obtener la IP actual. Reintentando en 10 minutos.")

    time.sleep(600) # Espera 10 minutos
