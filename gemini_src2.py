import json
import os
import re
from typing import List

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# --- KONFIGURACJA ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


# --- MODELE DANYCH ---
class MarketMetric(BaseModel):
    name: str = Field(description="Nazwa parametru (np. Arabica Futures, ICE Stocks)")
    value: str = Field(description="Aktualna wartość")
    trend: str = Field(description="Kierunek: Bullish/Bearish/Neutral")


class MarketReport(BaseModel):
    executive_summary: str = Field(
        description="Dlaczego cena się zmienia? Główne powody (drivers)."
    )
    metrics: List[MarketMetric]
    confidence_score: float = Field(description="Ufność analizy (0.0-1.0)")


# --- POBIERANIE DANYCH (JINA.AI) ---
def fetch_jina_market_info(query="coffee arabica ice futures market today 2026"):
    """Przeszukuje sieć przez Jina.ai i zwraca skondensowaną treść Markdown."""
    headers = {"Authorization": f"Bearer {JINA_API_KEY}"}
    url = f"https://s.jina.ai/{query}"
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Błąd Jina.ai: {str(e)}"


# --- ANALIZA Z GEMINI 2.5 FLASH ---
def analyze_with_thinking_and_search(raw_context):
    """Analizuje dane, używa Google Search do weryfikacji i zwraca JSON."""

    schema_text = json.dumps(MarketReport.model_json_schema(), indent=2)

    prompt = f"""
    ZADANIE: Wygeneruj rzetelny raport rynkowy kawy zielonej.
    KONTEKST Z JINA.AI:
    {raw_context}

    INSTRUKCJE:
    1. Użyj narzędzia Google Search, aby zweryfikować powyższe ceny i zapasy (szukaj danych z kwietnia 2026).
    2. Znajdź przyczyny zmian (tzw. drivers/narrative).
    3. Zwróć wynik WYŁĄCZNIE jako czysty JSON według schematu:
    {schema_text}
    """

    # Konfiguracja narzędzi (Search) i procesu myślowego (Thinking)
    search_tool = types.Tool(google_search=types.GoogleSearch())

    config = types.GenerateContentConfig(
        tools=[search_tool],
        thinking_config=types.ThinkingConfig(include_thoughts=True),
        temperature=1.0,  # Zalecane przy korzystaniu z grounding
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt, config=config
        )

        # Bezpieczne wyciąganie myśli i tekstu (Poprawiony AttributeError)
        ai_final_text = ""
        candidate = response.candidates

        for part in candidate.content.parts:
            if part.thought:
                print(f"--- PROCES MYŚLOWY AI ---\n{part.text}\n")
            if part.text:
                ai_final_text += part.text

        return ai_final_text

    except Exception as e:
        return f"Błąd Gemini API: {str(e)}"


# --- GŁÓWNA LOGIKA ---
def run_market_audit():
    print("1. Pobieranie danych z Jina.ai (Ground Truth Layer)...")
    context = fetch_jina_market_info()

    print("2. Analiza Gemini (Thinking + Google Search Verification)...")
    raw_output = analyze_with_thinking_and_search(context)

    # Oczyszczanie tekstu z ewentualnych znaczników ```json... ```
    clean_json = re.sub(r"```json\s*|```", "", raw_output).strip()

    try:
        validated_report = MarketReport.model_validate_json(clean_json)
        print("\n=== FINALNY RAPORT RYNKOWY (JSON) ===\n")
        print(validated_report.model_dump_json(indent=2))
        return validated_report
    except Exception as e:
        print(f"Błąd walidacji JSON: {e}")
        print(f"Surowy tekst od AI: {raw_output}")


if __name__ == "__main__":
    run_market_audit()
