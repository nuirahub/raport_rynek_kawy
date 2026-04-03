import json
import os
from datetime import datetime, timedelta

import google.generativeai as genai

from scrape import extract_article, scrape_for_report

# --- KONFIGURACJA ---
GENAI_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")
RECIPIENTS = os.getenv("RECIPIENTS", "").split(",")
SENDER = os.getenv("SENDER_EMAIL")

genai.configure(api_key=GENAI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


# --- KLASA POBIERAJĄCA DANE ---
class CoffeeScraper:
    def __init__(self, sources_file):
        with open(sources_file, "r") as f:
            self.sources = json.load(f)

    DIR_INPUT = "data/input"

    def scrape_all(self):
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
                        text = extract_article(url, content_type)

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


# --- LOGIKA ANALIZY ---
# def analyze_data(today_data, yesterday_file):
#     yesterday_data = "Brak danych z wczoraj."
#     if os.path.exists(yesterday_file):
#         with open(yesterday_file, "r") as f:
#             yesterday_data = f.read()

#     prompt = f"""
#     Jesteś analitykiem rynku kawy. Porównaj dzisiejsze dane z wczorajszymi.
#     DZISIAJ: {json.dumps(today_data)}
#     WCZORAJ: {yesterday_data}

#     Jeśli zaszły istotne zmiany (cena > 2%, pogoda, logistyka), przygotuj raport Markdown.
#     Zacznij od 'TRIGGER_TRUE' lub 'TRIGGER_FALSE'.
#     """

#     response = model.generate_content(prompt)
#     return response.text


# # --- WYSYŁKA ---
# def send_report(md_content):
#     html_body = markdown.markdown(md_content)
#     with open("email_template.html", "r") as f:
#         template = Template(f.read())

#     final_html = template.render(
#         date=datetime.now().strftime("%Y-%m-%d"), report_body=html_body
#     )

#     msg = MIMEMultipart()
#     msg["Subject"] = f"☕ Alert Rynkowy Kawa: {datetime.now().strftime('%d/%m/%y')}"
#     msg["From"] = SENDER
#     msg["To"] = ", ".join(RECIPIENTS)
#     msg.attach(MIMEText(final_html, "html"))

#     with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
#         server.login(SENDER, EMAIL_PASS)
#         server.sendmail(SENDER, RECIPIENTS, msg.as_string())


# --- MAIN ---
if __name__ == "__main__":
    scraper = CoffeeScraper("sources.json")
    today_results = scrape_for_report(scraper)

    today_filename = f"snapshot_{datetime.now().strftime('%Y%m%d')}.json"
    yesterday_filename = (
        f"snapshot_{(datetime.now() - timedelta(days=1)).strftime('%Y%m%d')}.json"
    )

    # 1. Zapisz dzisiejszy stan

    print(today_results)
    with open(today_filename, "w") as f:
        json.dump(today_results, f)

    # 2. Analizuj przez Gemini
    # analysis_result = analyze_data(today_results, yesterday_filename)

    # # 3. Jeśli AI zdecyduje - wyślij
    # if "TRIGGER_TRUE" in analysis_result:
    #     report_md = analysis_result.replace("TRIGGER_TRUE", "").strip()
    #     send_report(report_md)
    #     print("✅ Raport wysłany!")
    # else:
    #     print("ℹ️ Brak istotnych zmian. Raport nie został wysłany.")
