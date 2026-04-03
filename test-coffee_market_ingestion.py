import json
import time
from datetime import datetime

import requests
from trafilatura import extract, fetch_url

"""
Trafilatura: usuwa "śmieci" (reklam, menu, stopki) ze stron internetowych. 
content_snippet: Skrypt wycina pierwsze 2000 znaków tekstu (zazwyczaj to najważniejsze newsy).


snapshot_20260401.json (wczoraj).
snapshot_20260402.json (dzisiaj).
Pytanie: "Co się zmieniło w sekcji market_data?".
"""


# Załadowanie Twojej listy źródeł
SOURCES_JSON = """
{
  "market_data": {
    "sources": ["https://comunicaffe.com/", "https://www.gcrmag.com/news/"]
  },
  "weather_agronomy": {
    "sources": ["https://climatetempo.com.br/previsao-do-tempo/agronegocio/cafe"]
  }
}
"""


class CoffeeDataCollector:
    def __init__(self, sources):
        self.sources = json.loads(sources)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_content(self, url):
        """Pobiera treść strony i zamienia ją na czysty tekst."""
        try:
            downloaded = fetch_url(url)
            # Jeśli trafilatura zawiedzie, próbujemy z requests
            if downloaded is None:
                response = requests.get(url, headers=self.headers, timeout=15)
                downloaded = response.text

            result = extract(downloaded, include_tables=True, no_fallback=False)
            return result if result else "Błąd ekstrakcji treści."
        except Exception as e:
            return f"Błąd połączenia: {str(e)}"

    def run(self):
        print(f"🚀 Rozpoczynam pobieranie danych: {datetime.now()}")
        snapshot = {
            "metadata": {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "status": "success",
            },
            "data": {},
        }

        for category, details in self.sources.items():
            print(f"--- Kategoria: {category} ---")
            snapshot["data"][category] = []

            for url in details["sources"]:
                print(f"Pobieranie: {url}...")
                content = self.fetch_content(url)

                snapshot["data"][category].append(
                    {
                        "url": url,
                        "content_snippet": content[:2000]
                        if content
                        else "",  # Ograniczenie dla LLM
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                # Krótka pauza, by nie zostać zablokowanym
                time.sleep(2)

        self.save_snapshot(snapshot)

    def save_snapshot(self, data):
        filename = f"snapshot_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Zapisano snapshot do pliku: {filename}")


if __name__ == "__main__":
    collector = CoffeeDataCollector(SOURCES_JSON)
    collector.run()
