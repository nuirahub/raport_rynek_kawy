import os
from typing import List

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()


# --- KONFIGURACJA ---
JINA_API_KEY = os.getenv("JINA_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


# --- SCHEMATY DANYCH (JSON OUTPUT) ---
class MarketMetric(BaseModel):
    name: str = Field(
        description="Nazwa parametru (np. Arabica Futures, Certified Stocks)"
    )
    value: str = Field(description="Aktualna wartość lub cena")
    trend: str = Field(description="Kierunek zmiany: Bullish/Bearish/Neutral")
    impact_factor: float = Field(description="Wpływ na rynek w skali 0-1")


class MarketDriver(BaseModel):
    category: str = Field(description="Kategoria: Pogoda, Logistyka, Makro, Podaż")
    narrative: str = Field(description="Opis mechanizmu wpływu na cenę")
    source_verified: bool = Field(
        description="Czy informacja została potwierdzona w Google Search?"
    )


class CoffeeMarketReport(BaseModel):
    summary: str = Field(
        description="Krótki przegląd sytuacji rynkowej (Executive Summary)"
    )
    metrics: List[MarketMetric]
    drivers: List
    reasoning_summary: str = Field(description="Podsumowanie procesu dedukcji modelu")


# --- MODUŁ POBIERANIA DANYCH (JINA.AI) ---
def fetch_market_context(topic="green coffee market conditions"):
    """Pobiera skondensowany markdown z sieci przy użyciu Jina Search API."""
    headers = {"Authorization": f"Bearer {JINA_API_KEY}"}
    # s.jina.ai przeszukuje sieć i zwraca markdown przyjazny dla LLM
    response = requests.get(f"https://s.jina.ai/{topic}", headers=headers)
    return response.text


# --- MODUŁ ANALIZY I WERYFIKACJI (GEMINI 2.5 FLASH) ---
def analyze_market_with_grounding(raw_context):
    prompt = f"""
    Zanalizuj poniższe dane rynkowe:
    {raw_context}

    Twoim zadaniem jest:
    1. Wyekstrahować kluczowe ceny i wskaźniki (zapasy, kursy walut).
    2. Wykorzystać narzędzie Google Search, aby zweryfikować bieżącą narrację (dlaczego cena rośnie/spada).
    3. Zidentyfikować główne 'drivers' (np. mróz w Brazylii, problemy w Kanale Sueskim).
    4. Przedstawić wynik w ustrukturyzowanym formacie JSON.
    
    W procesie myślowym (thinking) skup się na powiązaniach przyczynowo-skutkowych.
    """

    # Konfiguracja narzędzi (Google Search Grounding)
    search_tool = types.Tool(google_search=types.GoogleSearch())

    # Konfiguracja Thinking i Structured Output
    config = types.GenerateContentConfig(
        tools=[search_tool],
        response_mime_type="application/json",
        response_schema=CoffeeMarketReport.model_json_schema(),
        thinking_config=types.ThinkingConfig(include_thoughts=True),
        temperature=1.0,  # Zalecane dla grounding
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt, config=config
    )

    # Wyświetlenie procesu myślowego (Thoughts)
    for part in response.candidates.content.parts:
        if part.thought:
            print(f"--- PROCES MYŚLOWY MODELU ---\n{part.text}\n")

    return response.text


# --- URUCHOMIENIE ---
if __name__ == "__main__":
    print("Pobieranie danych wejściowych...")
    context = fetch_market_context("coffee green market prices stocks logistics 2026")

    print("Generowanie raportu z weryfikacją Google Search...")
    report_json = analyze_market_with_grounding(context)

    print("--- FINALNY RAPORT JSON ---")
    print(report_json)
