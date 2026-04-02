import os
import smtplib
from dotenv import load_dotenv

load_dotenv()

user = os.getenv('EMAIL_HOST_USER')
password = os.getenv('EMAIL_HOST_PASSWORD')
host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
port = int(os.getenv('EMAIL_PORT', 587))

print(f"Connecting to {host}:{port} with {user}...")

try:
    server = smtplib.SMTP(host, port)
    server.starttls()
    server.login(user, password)
    print("LOGIN SUCCESSFUL!")
    server.quit()
except Exception as e:
    print(f"LOGIN FAILED: {e}")
