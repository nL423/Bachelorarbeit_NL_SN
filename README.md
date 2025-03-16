# Iconographic Search

## Beschreibung

Iconographic Search ist eine fortschrittliche Suchmaschine, die speziell dafür entwickelt wurde, ikonografische Inhalte effizient zu durchsuchen. Nutzer können mithilfe detaillierter Beschreibungen und spezifischer Schlüsselwörter nach speziellen Merkmalen von Münzen und Typen suchen. Hierbei können einzelne Beschreibungsmerkmale durch das leichte Navigieren in der Daten-Hierarchie schnell durch spezialisierte / generalisierte / equivalente Elemente ausgetauscht werden. Diese Plattform ist ideal für Forscher, Historiker und Enthusiasten im Bereich der Numismatik und Typologie.

## Voraussetzungen

Stellen Sie sicher, dass Sie folgende Software installiert haben:

- Python 3.8 oder höher
- pip (Python-Paketmanager)
- Microsoft Edge Browser (Es wird kein reibungsloser Ablauf bei Verwendung eines anderen Browsers garantiert!)
- Windows verwenden (Es wurde nur auf Windows 10/11 getestet. Es wird kein reibungsloser Ablauf auf anderen Betriebssytemen garantiert!)
- Apache-Jena-Fuseki-5.0.0

Die Installation von Apache-Jena-Fuseki-5.0.0 steht im Zusammenhang mit der Beschaffung des Corpus Nummorum Dumps.
Hierzu wenden Sie sich bitte an https://www.corpus-nummorum.eu/contact. (Punkt 5: Möglichkeit A)

Dies ist obsolet, sobald am Corpus Nummorum der Generic Rule Reasoner integriert wurde. (Punkt 5: Möglichkeit B)


## Installation

Folgen Sie diesen Schritten, um das Projekt lokal auf Ihrem Computer einzurichten:

### Schritt 1: Repository klonen

Öffnen sie die Kommandozentrale beziehungsweise die Eingabeaufforderung. <br /> 
Klonen Sie das Git-Repository auf Ihren lokalen Computer:
<br />
`git clone https://github.com/nL423/Bachelorarbeit_NL_SN.git`

### Schritt 2: Projektverzeichnis

Wechseln Sie in der Kommandozentrale in das Projektverzeichnis.<br />
Beispiel: 
<br />
`cd C:/Bachelorarbeit_NL_SN`

### Schritt 3: Virtuelle Umgebung

Es wird empfohlen, eine virtuelle Umgebung zu verwenden, um Konflikte mit anderen Python-Projekten zu vermeiden:
<br />
`python -m venv venv`

Aktivieren Sie die virtuelle Umgebung:

- **Windows:**
  <br />
  `.\venv\Scripts\activate`


- **Unix oder MacOS:**
  <br />
  `source venv/bin/activate`

Benutzen Sie wenn möglich Windows! <br />
Es wurde nur auf Windows 10/11 getestet. Es wird kein reibungsloser Ablauf auf anderen Betriebssytemen garantiert! <br />
(Siehe Vorraussetzungen!)

### Schritt 4: Abhängigkeiten installieren 

Installieren Sie die erforderlichen Pakete über pip:
<br />
`pip install -r requirements.txt`

Sie können nun die Eingabeaufforderung / Kommandozentralen schliessen.

### Schritt 5: Fuseki Datenbank anbinden

#### Möglichkeit A: Unter der Verwendung von Apache-Jena-Fuseki-5.0.0

Legen Sie die sich im `apache` Ordner des Projekts befindende `config.ttl` und `rules.ttl` in den `run` Ordner ihrer installierten Apache-Jena-Fuseki Version ab

Öffnen Sie eine neue Eingabeaufforderung / Kommandozentrale und navigieren Sie zu der Apache-Jena-Fuseki Version 5.0.0 <br />
Beispiel: 
<br /> 
`cd C:/apache-jena-fuseki-5.0.0`

Starten Sie nun Fuseki mit dem Befehl: 
<br /> 
`fuseki-server`

Öffnen Sie Fuseki unter `http://localhost:3030/#/` um die den zuvor beschaffenen Dump vom Corpus Nummorum hinzuzufügen: <br /> 
Hierzu klicken Sie auf `add data` und laden den zuvor beschaffenen CN Dump hinein.

Sie können nun die Eingabeaufforderung / Kommandozentrale schliessen.

#### Möglichkeit B: Unter der Verwendung des Corpus Nummorum Endpunktes 

Stellen Sie sicher, dass der Generic Rule Reasoner am Corpus Nummorum integriert wurde!

Öffnen Sie `CoinSearchHandler.py`. Die Datei finden Sie unter `Bachelorarbeit_NL_SN/igc/services/`
<br /> 
Folgen Sie den Anweisungen in Zeile 27 und 28 der `CoinSearchHandler.py` Datei

## Anwendung starten

Wenn Sie sich bei der Installation in Schritt 5 für Möglichkeit B entschieden haben, dann überspringen Sie Schritt 1!!!! <br/>
Während der gesamten Nutzung des Programmes darf keine in "Anwendung Starten" geöffnete Kommandozentrale / Eingabeaufforderung geschlossen werden !!!!

### Schritt 1: Fuseki Endpunkt starten

Öffnen Sie eine Eingabeaufforderung / Kommandozentrale und navigieren Sie zu der Apache-Jena-Fuseki Version 5.0.0 <br />
Beispiel: 
<br /> 
`cd C:/apache-jena-fuseki-5.0.0`

Starten Sie nun Fuseki mit dem Befehl: 
<br /> 
`fuseki-server`

### Schritt 2: Python Server starten

Öffnen Sie eine neue Eingabeaufforderung / Kommandozentrale und navigieren Sie zum Projekt `Bachelorarbeit_NL_SN`:<br /> 
Beispiel: 
<br /> 
`cd C:/Beispielordner/Bachelorarbeit_NL_SN`

Aktivieren Sie die virtuelle Umgebung:

- **Windows:**
  <br />
  `.\venv\Scripts\activate`


- **Unix oder MacOS:**
  <br />
  `source venv/bin/activate`

Navigieren Sie in das Verzeichnis, das `manage.py` enthält:
<br />
`cd igc`

Führen Sie die folgenden Befehle aus, um den Server zu starten:
<br />
`python manage.py runserver`

Nach dem Start des Servers ist die Anwendung unter `http://127.0.0.1:8000/` in Ihrem Webbrowser erreichbar.

## Entwickler

### Vorarbeit / Code auf dem wir aufgebaut haben
**Entwickler:** Mohammed Sayed Mahmod, Danilo Pantic  <br />
**Projekt-Link:** [GitHub Repository](https://github.com/Danilopa/Bachelorthesis.git)

### Aktuelles Projekt
**Entwickler:** Nico Lambert, Steven Jerome Nowak <br />
**Projekt-Link:** [GitHub Repository](https://github.com/nL423/Bachelorarbeit_NL_SN.git)

## Lizenz

Dieses Projekt ist lizenziert unter der Creative Commons Attribution - NonCommercial - ShareAlike 3.0 Germany License. Um eine Kopie dieser Lizenz zu sehen, besuchen Sie [Creative Commons Lizenz](http://creativecommons.org/licenses/by-nc-sa/3.0/de/).
