Narzędzie do wysyłki raportów o stanie rynku kawy zielonej.
Python, jinja, markdawn.

Chodzi o codzienną wysylkę informacji - czy "status" uległ znacząco zmianie.
Pobieranie wartościowych informacje z kilku stron. Na podstawie tych danych (info w plikach lokalnych?) i pliku md z promptem (definicja szablonu raportu) będzie generowany dzienny raport z najważniejszymi informacjami.
Na pierwszy plan - pobranie "raportu" przez model gemini poprzez specjalne zapytanie.

Raport z dnia bieżącego będzie porównywany z raportem z dnia poprzedniego. Jeśli wystąpią znaczące różnice dzień po dniu - zmiany ceny na giełdzie, zmiana warunków atmosferycznych w mniejscach plantacji, zmiana stany transportu, zaminy w przeływie produktów przez porty / cieśniny itp. to wtedy będzie do listy odbiorców przesyłany raport.
