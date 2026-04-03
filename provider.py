import os

import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")


def analyze_market_changes(yesterday_data, today_data, prompt_template):
    """
    Porównuje dane i decyduje o wysyłce.
    """
    full_prompt = f"""
    {prompt_template}
    
    OTOTO DANE Z WCZORAJ:
    {yesterday_data}
    
    OTO DANE Z DZISIAJ:
    {today_data}
    
    ZADANIE:
    1. Czy wystąpiły znaczące zmiany (cena > 2%, ekstremalna pogoda, blokady portów)? 
    2. Jeśli tak, przygotuj raport w Markdown.
    3. Na początku napisz słowo 'TRIGGER: TRUE' lub 'TRIGGER: FALSE'.
    """

    response = model.generate_content(full_prompt)
    return response.text
