import json
import os
import re
from typing import List

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# --- INICJALIZACJA ---
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
JINA_KEY = os.getenv("JINA_API_KEY")


# --- STRUKTURA DANYCH (Gwarancja rzetelności) ---
class MarketMetric(BaseModel):
    name: str = Field(description="Nazwa wskaźnika (np. Arabica Futures, Stocks)")
    current_value: str = Field(description="Wartość z dnia dzisiejszego")
    source_status: str = Field(description="Status weryfikacji: Verified/Corrected/New")


class MarketReport(BaseModel):
    narrative: str = Field(
        description="Wyjaśnienie: dlaczego cena się zmieniła? (Drivers)"
    )
    metrics: List[MarketMetric]
    ground_truth_score: float = Field(
        description="Ocena zgodności danych Jina z Google Search (0-1)"
    )


# --- POBIERANIE DANYCH (JINA.AI) ---
def fetch_jina_data():
    """Pobiera dane rynkowe przez Jina Search."""
    query = "green coffee market prices arabica robusta ice stocks logistics weather today 2026"
    headers = {"Authorization": f"Bearer {JINA_KEY}"}
    url = f"https://s.jina.ai/{query}"

    print("-> Krok 1: Pobieranie surowych danych z Jina.ai...")
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Błąd Jina: {e}"


# --- ANALIZA I WERYFIKACJA (GEMINI 2.5 FLASH) ---
def run_intelligent_audit(raw_context):
    """Analizuje dane, weryfikuje w Google Search i buduje raport."""

    # Schemat JSON przekazany jako tekst (aby uniknąć błędu Tool/JSON Mode Conflict)
    schema_text = json.dumps(MarketReport.model_json_schema(), indent=2)

    prompt = f"""
    ZADANIE: Wygeneruj rzetelny raport rynkowy na dzień 9 kwietnia 2026.
    
    WEJŚCIE (DANE Z JINA.AI):
    {raw_context}
    
    INSTRUKCJE WERYFIKACJI (Ground Truth):
    1. Użyj narzędzia Google Search, aby sprawdzić, czy ceny i zapasy z Jina.ai są aktualne na dzień dzisiejszy.
    2. Jeśli dane z Jina są stare (np. z 2025 roku), zastąp je danymi z wyszukiwarki.
    3. Wyjaśnij 'drivers' - np. czy przyczyną jest susza w Brazylii czy problemy w portach Wietnamu.
    4. Odpowiedz WYŁĄCZNIE w formacie JSON wg schematu:
    {schema_text}
    """

    # Konfiguracja narzędzia Search i Thinking
    search_tool = types.Tool(google_search=types.GoogleSearch())

    config = types.GenerateContentConfig(
        tools=[search_tool],
        thinking_config=types.ThinkingConfig(include_thoughts=True),
        temperature=1.0,
    )

    print("-> Krok 2: Proces myślowy AI + Weryfikacja Google Search...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt, config=config
        )

        # KLUCZOWA NAPRAWA: response.candidates
        if not response.candidates:
            return "Błąd: Model nie zwrócił żadnej odpowiedzi."

        final_text = ""
        # Iterujemy po częściach, aby oddzielić Thinking od JSON
        for part in response.candidates.content.parts:
            if part.thought:
                print(f"\n:\n{part.text}\n")
            if part.text:
                final_text += part.text

        return final_text

    except Exception as e:
        return f"Błąd API Gemini: {str(e)}"


# --- URUCHOMIENIE ---
if __name__ == "__main__":
    # 1. Dane bazowe
    context = fetch_jina_data()

    # 2. Inteligentny Audyt
    ai_raw_output = run_intelligent_audit(context)

    # 3. Czyszczenie JSON (model czasem dodaje ```json... ```)
    clean_json = re.sub(r"```json\s*|```", "", ai_raw_output).strip()

    # 4. Finalna walidacja i wyświetlenie
    try:
        report = MarketReport.model_validate_json(clean_json)
        print("!" * 60)
        print("FINALNY, ZWERYFIKOWANY RAPORT RYNKOWY (JSON)")
        print("!" * 60)
        print(report.model_dump_json(indent=2))
    except Exception as e:
        print(f"\nBłąd walidacji danych: {e}")
        print(f"Surowa treść od AI:\n{ai_raw_output}")
