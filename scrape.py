# https://jina.ai/
# playwright
# Gemini
import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def get_pdf_with_ai(url: str) -> str:
    """
    Get data with AI
    """
    PROMPT_TEMPLATE = f"""
Act as a Senior Coffee Market Analyst specializing in global supply chains and Brazilian exports. 
Your task is to provide a comprehensive, executive summary based on the provided text/image from the Cecafé report.

### CONTEXT:
The user is a green coffee trader. The goal is to identify market shifts that could affect prices in the next 30 days.

### REQUIRED ANALYSIS SECTIONS:
1. **Executive Summary**: A high-level overview of the current month's performance.
2. **Volume Dynamics**: 
   - Compare current month exports vs. previous year (YoY).
   - Analyze the split between Arabica and Robusta (Conilon).
3. **Logistics & Port Infrastructure**: 
   - Identify any mentions of vessel delays (rollovers), container shortages, or congestion in the Port of Santos and Rio de Janeiro.
4. **Market Destinations**: 
   - Highlight significant growth or decline in key markets (USA, Germany, Belgium, China).
5. **Sustainability & Specialty**: 
   - Summarize the performance of certified and differentiated coffees.
6. **Risk Assessment (Critical)**: 
   - List 3 potential risks or opportunities derived from this data.

### FORMATTING RULES:
- Use Markdown (headers, bold text, bullet points).
- If specific numbers/percentages are available, always include them.
- If the data suggests a significant market shift (>5% change or logistics crisis), start the response with the tag: [MARKET_ALERT].

### SOURCE DATA:
{url}
"""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(PROMPT_TEMPLATE)
    return response.text


def get_html_with_ai(url: str) -> str:
    """
    Get data with AI
    """
    PROMPT_TEMPLATE = f"""
Act as a Senior Coffee Market Analyst specializing in global supply chains and Brazilian exports. 
Your task is to provide a comprehensive, executive summary based on the provided text/image from the Cecafé report.

### CONTEXT:
The user is a green coffee trader. The goal is to identify market shifts that could affect prices in the next 30 days.

### REQUIRED ANALYSIS SECTIONS:
1. **Executive Summary**: A high-level overview of the current month's performance.
2. **Volume Dynamics**: 
   - Compare current month exports vs. previous year (YoY).
   - Analyze the split between Arabica and Robusta (Conilon).
3. **Logistics & Port Infrastructure**: 
   - Identify any mentions of vessel delays (rollovers), container shortages, or congestion in the Port of Santos and Rio de Janeiro.
4. **Market Destinations**: 
   - Highlight significant growth or decline in key markets (USA, Germany, Belgium, China).
5. **Sustainability & Specialty**: 
   - Summarize the performance of certified and differentiated coffees.
6. **Risk Assessment (Critical)**: 
   - List 3 potential risks or opportunities derived from this data.

### FORMATTING RULES:
- Use Markdown (headers, bold text, bullet points).
- If specific numbers/percentages are available, always include them.
- If the data suggests a significant market shift (>5% change or logistics crisis), start the response with the tag: [MARKET_ALERT].

### SOURCE DATA:
{url}
"""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(PROMPT_TEMPLATE)
    return response.text


def extract_article(url: str, type: str) -> str:
    """
    Extract article from a url
    """
    if type == "pdf":
        scrapai = get_pdf_with_ai(url)
    elif type == "html":
        scrapai = get_html_with_ai(url)
    else:
        print(f"Błąd: Nieprawidłowy typ: {type}")
        return ""

    return scrapai


def scrape_for_report(scraper) -> str:
    os.makedirs(scraper.DIR_INPUT, exist_ok=True)

    urls_list: list[str] = []
    for _category, details in scraper.sources.items():
        if not isinstance(details, dict):
            continue
        for content_type in ("pdf", "html"):
            urls = details.get(content_type)
            if isinstance(urls, list):
                urls_list.extend(urls)

    #  full_data = scraper.scrape_all()
    #  collected_data_text = json.dumps(full_data, ensure_ascii=False)
    #  max_context = 100_000
    #  if len(collected_data_text) > max_context:
    #      collected_data_text = (
    #          collected_data_text[:max_context] + "\n...[truncated for context limit]"
    #      )

    # Podwójne {{ }} — literały dla str.format; jedyny placeholder: {urls}
    SYSTEM_PROMPT = """
Act as a Coffee Market Data Architect. 
Analyze the provided text/PDF inputs and extract key metrics into a strictly structured JSON.

### CRITICAL RULES:
1. OUTPUT ONLY VALID JSON. No prose, no explanations.
2. If data for a field is missing, use null.
3. Use the exact keys provided in the schema.
4. Language: English for keys, Polish/English for content (as specified).

### SCHEMA STRUCTURE:
{{
  "report_metadata": {{"date": "string", "source_count": "number"}},
  "market_indicators": {{
    "price_ny_ice": {{"value": "number", "change_pct": "number"}},
    "internal_price_colombia": {{"value": "number", "currency": "string"}}
  }},
  "logistics_alerts": [{{"port": "string", "status": "critical|stable|warning", "issue": "string"}}],
  "production_updates": [{{"country": "string", "forecast_change": "string"}}],
  "trigger_alert": "boolean"
}}

### MONITORED SOURCE URLS:
{urls}
"""
    genai.configure(api_key=GEMINI_API_KEY)
    #  model = genai.GenerativeModel(
    #      model_name="gemini-3-flash",
    #      system_instruction=SYSTEM_PROMPT
    #  )
    search_tool = types.Tool(google_search=types.GoogleSearch())

    model = genai.GenerativeModel(
        model_name="gemini-3-flash",
        tools_config=my_tools,
        system_instruction=SYSTEM_PROMPT.format(urls=", ".join(urls_list)),
    )

    user_prompt = (
        f"Extract data from these sources into the defined JSON schema: {urls_list}"
    )

    response = model.generate_content(
        user_prompt,
        generation_config={
            "response_mime_type": "application/json",  # WYMUSZENIE JSON
            "temperature": 0.1,
        },
    )
    return response.text
