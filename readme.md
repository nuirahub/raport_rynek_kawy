Dlaczego taki podział?
Cena giełdowa (ICE/Investing): To Twój główny wskaźnik. Jeśli giełda skacze o 3%, raport powinien zostać wygenerowany automatycznie.

Pogoda (Climatetempo/AccuWeather): Brazylia (Minas Gerais) to serce produkcji Arabiki. Wietnam to Robusta. Szukaj słów kluczowych: frost (mróz), drought (susza), excessive rain (nadmierne opady).

Porty i Logistyka (Cecafe/Datamar): Kawa jest towarem fizycznym. Blokada w porcie Santos (Brazylia) lub problem w kanale Sueskim drastycznie wpływa na dostępność zielonego ziarna w Europie.

Wiadomości (Comunicaffe/GCR): Tu znajdziesz kontekst "miękki", np. zmiany w certyfikacji EUDR (deforestacja), które mogą zablokować transporty niezależnie od ceny giełdowej.

- Użyj biblioteki trafilatura do wyciągnięcia samej treści tekstowej z artykułów.

- Dla cen giełdowych przesyłaj tylko tabelkę lub słownik Python.

---

USDA (Commodity Coffee): To źródło publikuje raporty rzadziej (półroczne/kwartalne). Do codziennej wysyłki może być mało dynamiczne, ale stanowi świetny "fundament" dla Gemini, żeby rozumiało szerszy kontekst (np. przewidywany deficyt w skali roku).

Investing/ICE: Jeśli chcesz pobierać ceny, najłatwiej będzie użyć biblioteki yfinance (jeśli dany kontrakt tam jest) lub dedykowanego API, zamiast scrapować surowy HTML, który często się zmienia.

Język: Źródła takie jak climatetempo.com.br są po portugalsku. To akurat super, bo Gemini świetnie tłumaczy i analizuje teksty w różnych językach, co da Ci przewagę nad raportami dostępnymi tylko po angielsku.
