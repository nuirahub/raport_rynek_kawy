import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(html_content, recipient_list):
    sender_email = "twoj_mail@gmail.com"
    password = "twoje_haslo_aplikacji"

    msg = MIMEMultipart()
    msg["Subject"] = (
        f"☕ Alert Rynkowy: Istotne zmiany - {datetime.now().strftime('%Y-%m-%d')}"
    )
    msg["From"] = f"Coffee AI <{sender_email}>"
    msg["To"] = ", ".join(recipient_list)

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_list, msg.as_string())
        print("🚀 Email wysłany pomyślnie!")
    except Exception as e:
        print(f"❌ Błąd wysyłki: {e}")
