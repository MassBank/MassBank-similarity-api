# Hinweise für Coding-Agents

Diese Datei gilt für das gesamte Repository. Änderungen sollen zur jeweiligen
Aufgabe passen; bestehende, nicht zur Aufgabe gehörende Arbeitsänderungen
erhalten.

## Projekt und Struktur

MassBank-similarity-api berechnet spektrale Ähnlichkeiten über eine REST-API.
Der OpenAPI-Vertrag ist die Grundlage für den generierten Python-Flask-Server.

- `openapi.yaml`: API-Vertrag; Änderungen am öffentlichen Verhalten hier
  abbilden.
- `config-openapi.yaml`, `generate.sh`: OpenAPI-Generator-Konfiguration und
  Aufruf.
- `gen/`: generierter, ignorierter Servercode einschließlich Modellklassen.
  Nicht manuell bearbeiten; Anpassungen gehören in Vertrag, Konfiguration oder
  Implementierung. `generate.sh` löscht und erzeugt dieses Verzeichnis neu.
- `similarity_api_impl/`: eigener Anwendungscode, Controller und Datenloader.
- `similarity_api_impl/packed_similarity.py`: optimierter Berechnungskern und
  gemeinsam verwendete Referenzarrays.
- `test/`: unittest-Tests und kleiner MassBank-Testdatenbestand.

Der aktuelle Stack verwendet Connexion 2, Flask und Waitress.

## Umgebung, Generierung und Tests

Im Repository-Verzeichnis arbeiten. Python 3.13 und uv verwenden; Abhängigkeiten
und Versionsgrenzen stehen in `pyproject.toml`, die Auflösung in `uv.lock`. Die
aktive virtuelle Umgebung ist `.venv/`.

Für die Generierung werden derzeit Java, Maven, curl und jq benötigt. Maven wird
vom Generator-Launcher zum Herunterladen der JAR verwendet, nicht vom
API-Service.

```bash
uv sync --locked
mkdir -p gen && bash generate.sh
uv run --locked python -m unittest discover -s test
```

Die Generierung ist vor dem ersten Testlauf erforderlich. Die Tests verwenden
die generierten Modelle und den Datenbestand in `test/MassBank-test-data`.
Bestehende Assertions zu Scores und Reihenfolge erhalten; Tests nicht durch
schwächere Erwartungen ersetzen, um Änderungen passend zu machen.

Nach Änderungen an Abhängigkeiten `uv lock` ausführen, die Umgebung mit `uv sync
--locked` synchronisieren und das aktualisierte Lockfile mitführen. Aktuelle
Paketversionen direkt beim Paketindex beziehungsweise im offiziellen
Release-Verzeichnis prüfen, nicht allein anhand von Suchmaschinen-Auszügen.
Framework-Upgrades müssen auch mit dem tatsächlich generierten Code kompatibel
sein. Die momentan alten Flask-Grenzen folgen aus Connexion 2.

## Start und Daten

```bash
DATA_DIR=/workspaces/MassBank-data THREADS=2 \
  uv run --locked python -m similarity_api_impl
```

`DATA_DIR` bezeichnet das Referenzdatenverzeichnis. Einen externen
MassBank-data-Checkout als Eingabedaten behandeln und nicht während eines Tests
verändern. Für normale Tests den kleinen mitgelieferten Datenbestand verwenden.

Die API und Swagger UI laufen standardmäßig auf Port 8080 beziehungsweise
`/ui/`. `CONTEXT_PATH` konfiguriert den Anwendungspfad, `VERBOSE=true` die
zusätzliche Anfrageprotokollierung. Der Python-Start verwendet standardmäßig
zwei Waitress-Threads; `THREADS` überschreibt diese Zahl.

Das Dockerfile nutzt denselben Python-Start und dieselbe Variable `THREADS`.
Probes laufen auf demselben Port mit reserviertem Waitress-Worker.
Vor einem lokalen Start prüfen, ob eine vorhandene Instanz den Port verwendet;
einen laufenden Service nicht beiläufig ersetzen.

## Anforderungen an den Berechnungskern

`packed` ist der einzige Laufzeitpfad. matchms bleibt für Spektren,
Normalisierung, Berechnungsbausteine und den Vergleich in Tests eine benötigte
Abhängigkeit.

- Referenzpeaks und Offsets einmal laden und schreibgeschützt zwischen Threads
  teilen. Keine vollständigen Referenzkopien pro Anfrage oder Thread anlegen.
- Der Numba-Kern läuft mit `njit(nogil=True, cache=True)`.
  Python-Objektverarbeitung nicht in die native Vergleichsschleife verschieben.
  GIL-Freigabe bedeutet nicht, dass der gesamte HTTP-Request GIL-frei ist.
- Den vollständigen Snapshot beim Prozessstart aufbauen und erst danach
  veröffentlichen. Datenupdates über einen Pod-Rollout bereitstellen; nicht
  aus einem Request heraus nachladen.
- Die bisherige CosineGreedy-Semantik erhalten: Toleranz 0.1, m/z-Potenz 0,
  Intensitätspotenz 1, Peak-Zuordnung, Normalisierung, Trefferfilter und
  Sortierung. Änderungen daran sind fachliche Änderungen und benötigen passende
  Tests.
- Eine fehlende `reference_spectra_list` bedeutet alle Referenzen. Die API weist
  eine leere Liste mit `400` ab. Eine nicht leere Liste beschränkt die Auswahl;
  unbekannte Accessions werden ignoriert.
- Numerische Änderungen gegen matchms prüfen, einschließlich gleicher Scores,
  überlappender Toleranzfenster, fehlender Treffer und gleichzeitiger Anfragen.
  Exakte Abweichungen, Toleranzabweichungen und andere Trefferreihenfolgen
  getrennt ausweisen. Toleranzen nicht stillschweigend lockern.

## Abschluss

Passende Tests und `git diff --check` ausführen. Bei reinen Dokumentations- oder
Aufräumarbeiten genügt eine entsprechende Prüfung der betroffenen Dateien.
Generierte Artefakte, virtuelle Umgebungen, Logs und lokale Messarchive nicht
versehentlich versionieren. Quellcode und benötigte Projektdaten beim Aufräumen
erhalten. Release-Arbeit separat behandeln: `release.sh` pusht Branches und Tags
und veröffentlicht ein GitHub-Release; es ist kein lokaler Build- oder
Testschritt.

## Markdown-Formatierung

Alle gepflegten Markdown-Dateien im Repository auf höchstens 80 Zeichen pro
Zeile umbrechen. Absätze sinnvoll umbrechen, Listen mit passender Einrückung
fortsetzen und lange Links als Referenzlinks schreiben. Shell-Befehle in
Codeblöcken an syntaktisch gültigen Stellen umbrechen; ihre Ausführbarkeit
bewahren. Generierte Dateien und installierte Abhängigkeiten nicht manuell
formatieren.
