import os
from datetime import datetime, timedelta

import google.generativeai as genai

# Konfiguracja Gemini
genai.configure(api_key="TWÓJ_KLUCZ_API")
model = genai.GenerativeModel("gemini-1.5-flash")


def get_snapshot_path(date_offset):
    date_str = (datetime.now() - timedelta(days=date_offset)).strftime("%Y%m%d")
    return f"snapshot_{date_str}.json"


def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Brak danych dla tego dnia."


def analyze_and_decide():
    # 1. Wczytaj pliki (dzisiejszy i wczorajszy)
    today_raw = load_data(get_snapshot_path(0))
    yesterday_raw = load_data(get_snapshot_path(1))

    # 2. Przygotuj prompt
    final_prompt = PROMPT_ANALYSIS.format(
        yesterday_data=yesterday_raw[:5000],  # Limity bezpieczeństwa tokenów
        today_data=today_raw[:5000],
    )

    # 3. Wyślij do Gemini
    print("🤖 Analiza Gemini w toku...")
    response = model.generate_content(final_prompt)
    output = response.text

    # 4. Logika decyzji
    if "TRIGGER_TRUE" in output:
        print("🚨 Wykryto istotne zmiany! Generuję raport...")
        report_content = output.replace("TRIGGER_TRUE", "").strip()
        save_report(report_content)
        return True
    else:
        print("😴 Brak znaczących zmian na rynku.")
        return False


def save_report(content):
    filename = f"report_{datetime.now().strftime('%Y%m%d')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📄 Raport zapisany: {filename}")


if __name__ == "__main__":
    should_send = analyze_and_decide()
    if should_send:
        # Tutaj dodasz w przyszłości funkcję wysyłki (np. przez SMTP)
        print("📨 Raport gotowy do wysłania do odbiorców.")
