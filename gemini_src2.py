import os
import json
import requests
import re
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv

# --- KONFIGURACJA ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# --- MODELE DANYCH ---
class MarketMetric(BaseModel):
    name: str = Field(description="Nazwa parametru (np. KC Arabica Futures)")
    value: str = Field(description="Dzisiejsza zweryfikowana wartość")
    change_vs_yesterday: str = Field(description="Różnica względem danych historycznych")

class CoffeeAuditReport(BaseModel):
    narrative: str = Field(description="Główny powód zmiany ceny (driver)")
    metrics: List[MarketMetric]
    search_verification: str = Field(description="Co model znalazł w Google Search, czego nie było w Jina?")

# --- MODUŁY POMOCNICZE ---
def load_sources():
    with open('sources.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def fetch_jina_data(sources_dict):
    # Budujemy zapytanie na podstawie domen z sources.json
    all_domains = [domain for group in sources_dict.values() for domain in group]
    query = f"coffee green market ice prices and stocks April 2026 sources: {', '.join(all_domains)}"
    
    headers = {"Authorization": f"Bearer {JINA_API_KEY}"}
    url = f"https://s.jina.ai/{query}"
    print("-> Pobieranie danych z Jina.ai (Ground Truth Layer)...")
    res = requests.get(url, headers=headers, timeout=30)
    return res.text

# --- ANALIZA Z GEMINI (POPRAWIONA STRUKTURA) ---
def analyze_and_ground(raw_data):
    schema_text = json.dumps(CoffeeAuditReport.model_json_schema(), indent=2)
    
    prompt = f"""
    DZISIEJSZA DATA: 9 kwietnia 2026.
    ZADANIE: Stwórz raport rynku kawy zielonej.
    
    DANE WEJŚCIOWE (Z JINA.AI):
    {raw_data}
    
    INSTRUKCJE WERYFIKACJI:
    1. Użyj narzędzia Google Search, aby sprawdzić czy ceny i zapasy są aktualne na dziś (kwiecień 2026).
    2. Znajdź przyczyny (drivers) zmian (np. raporty StoneX o nadwyżce produkcji).
    3. Odpowiedz WYŁĄCZNIE czystym kodem JSON zgodnym ze schematem:
    {schema_text}
    """

    config = types.GenerateContentConfig(
        tools=,
        thinking_config=types.ThinkingConfig(include_thoughts=True),
        temperature=1.0
    )

    print("-> Analiza Gemini 2.5 Flash (Thinking + Google Search Verification)...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config
        )

        # BEZPIECZNE WYCIĄGANIE TREŚCI - Używamy candidates
        if not response.candidates:
            return "Error: Brak odpowiedzi."

        final_text = ""
        # Przechodzimy przez części: myśli (thought) są drukowane, tekst (JSON) zbierany
        # Używamy poprawnego indeksowania candidates dla SDK google-genai
        for part in response.candidates.content.parts:
            if part.thought:
                print(f"\n--- LOGIKA MODELU ---\n{part.text}\n")
            if part.text:
                final_text += part.text
        
        return final_text

    except Exception as e:
        return f"Błąd krytyczny API: {str(e)}"

# --- URUCHOMIENIE ---
if __name__ == "__main__":
    # 1. Wczytaj zaufane źródła
    src_config = load_sources()
    
    # 2. Pobierz dane przez Jina.ai
    context = fetch_jina_data(src_config)
    
    # 3. Analiza i audyt AI
    ai_raw_output = analyze_and_ground(context)
    
    # 4. Oczyszczanie i walidacja JSON
    clean_json = re.sub(r'```json\s*|```', '', ai_raw_output).strip()
    
    try:
        final_report = CoffeeAuditReport.model_validate_json(clean_json)
        print("\n" + "="*60)
        print("ZWERYFIKOWANY RAPORT RYNKOWY (GOLD DATA)")
        print("="*60)
        print(final_report.model_dump_json(indent=2))
        
        # Zapisz jako dzisiejszy raport do przyszłego porównania
        with open('yesterday_report.json', 'w', encoding='utf-8') as f:
            f.write(final_report.model_dump_json(indent=2))
            
    except Exception as e:
        print(f"\nBŁĄD WALIDACJI: {e}")
        print(f"Surowa odpowiedź modelu:\n{ai_raw_output}")