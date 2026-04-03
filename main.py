import json
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import google.generativeai as genai
import markdown
from dotenv import load_dotenv
from jinja2 import Template

from scrape import extract_article, scrape_for_report

load_dotenv()

# --- KONFIGURACJA ---
GENAI_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")
RECIPIENTS = [
    r.strip()
    for r in os.getenv("RECIPIENTS", "").split(",")
    if r.strip()
]
SENDER = os.getenv("SENDER_EMAIL")

genai.configure(api_key=GENAI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


# --- KLASA POBIERAJĄCA DANE ---
class CoffeeScraper:
    def __init__(self, sources_file):
        with open(sources_file, "r", encoding="utf-8") as f:
            self.sources = json.load(f)

    DIR_INPUT = "data/input"

    def scrape_all(self):
        os.makedirs(self.DIR_INPUT, exist_ok=True)
        full_data = {}
        # 1. Iteracja po głównych kategoriach (np. "goverment_and_orgs")
        for category, details in self.sources.items():
            if not isinstance(details, dict):
                continue

            print(f"--- Processing Category: {category} ---")
            category_text = ""

            # 2. Iteracja po typach zasobów (pdf, html) z pominięciem opisu
            for content_type in ["pdf", "html"]:
                if content_type in details:
                    urls = details[content_type]  # To jest lista adresów URL

                    for url in urls:
                        print(f"Scraping {content_type.upper()}: {url}")

                        # Wywołanie Twojej funkcji (zakładam, że przyjmuje url i type)
                        text = extract_article(url, content_type) or ""

                        # Dodanie do zbiorczego tekstu dla Gemini
                        category_text += f"\nŹRÓDŁO ({content_type.upper()} - {url}):\n{text[:1500]}\n"

                        # 3. Zapis do pliku lokalnego (czyszczenie URL dla nazwy pliku)
                        safe_url = (
                            url.replace("https://", "")
                            .replace("/", "_")
                            .replace(".", "_")[:50]
                        )
                        filename = (
                            f"{self.DIR_INPUT}/{category}_{content_type}_{safe_url}.txt"
                        )

                        try:
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write(text)
                        except Exception as e:
                            print(f"Błąd zapisu pliku {filename}: {e}")

            # Zapisanie zebranych danych z kategorii do słownika wynikowego
            full_data[category] = category_text

        return full_data


def _normalize_for_prompt(data):
    if isinstance(data, str):
        raw = data.strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines)
        try:
            return json.dumps(json.loads(raw), ensure_ascii=False)
        except json.JSONDecodeError:
            return data
    return json.dumps(data, ensure_ascii=False)


# --- LOGIKA ANALIZY ---
def analyze_data(today_data, yesterday_file):
    yesterday_data = "Brak danych z wczoraj."
    if os.path.exists(yesterday_file):
        with open(yesterday_file, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            yesterday_data = json.dumps(
                json.loads(content), ensure_ascii=False, indent=2
            )
        except json.JSONDecodeError:
            yesterday_data = content

    today_str = _normalize_for_prompt(today_data)

    prompt = f"""
    Jesteś analitykiem rynku kawy. Porównaj dzisiejsze dane z wczorajszymi.
    DZISIAJ: {today_str}
    WCZORAJ: {yesterday_data}

    Jeśli zaszły istotne zmiany (cena > 2%, pogoda, logistyka), przygotuj raport Markdown.
    Zacznij od 'TRIGGER_TRUE' lub 'TRIGGER_FALSE'.
    """

    response = model.generate_content(prompt)
    return response.text


# # --- WYSYŁKA ---
def send_report(md_content):
    if not SENDER or not EMAIL_PASS or not RECIPIENTS:
        raise ValueError(
            "Brak SENDER_EMAIL, EMAIL_PASSWORD lub RECIPIENTS — nie można wysłać maila."
        )

    html_body = markdown.markdown(md_content)
    with open("email_template.html", "r", encoding="utf-8") as f:
        template = Template(f.read())

    final_html = template.render(
        date=datetime.now().strftime("%Y-%m-%d"), report_body=html_body
    )

    msg = MIMEMultipart()
    msg["Subject"] = f"☕ Alert Rynkowy Kawa: {datetime.now().strftime('%d/%m/%y')}"
    msg["From"] = SENDER
    msg["To"] = ", ".join(RECIPIENTS)
    msg.attach(MIMEText(final_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER, EMAIL_PASS)
        server.sendmail(SENDER, RECIPIENTS, msg.as_string())


def _parse_snapshot_payload(raw: str):
    """Zapisujemy spójny JSON; model czasem owija odpowiedź w ```json ... ```."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_model_output": raw}


# --- MAIN ---
if __name__ == "__main__":
    scraper = CoffeeScraper("sources.json")
    today_results = scrape_for_report(scraper)

    today_filename = f"snapshot_{datetime.now().strftime('%Y%m%d')}.json"
    yesterday_filename = (
        f"snapshot_{(datetime.now() - timedelta(days=1)).strftime('%Y%m%d')}.json"
    )

    snapshot_payload = _parse_snapshot_payload(today_results)
    print(today_results)
    with open(today_filename, "w", encoding="utf-8") as f:
        json.dump(snapshot_payload, f, ensure_ascii=False, indent=2)

    # 2. Analizuj przez Gemini (porównanie z wczoraj)
    analysis_result = analyze_data(snapshot_payload, yesterday_filename)

    # 3. Jeśli AI zdecyduje - wyślij
    if "TRIGGER_TRUE" in analysis_result:
        report_md = analysis_result.replace("TRIGGER_TRUE", "").strip()
        try:
            send_report(report_md)
            print("✅ Raport wysłany!")
        except ValueError as e:
            print(f"⚠️ Wysyłka pominięta: {e}")
    else:
        print("ℹ️ Brak istotnych zmian. Raport nie został wysłany.")
