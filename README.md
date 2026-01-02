# 🌭 Bratwurst Frühwarnsystem

Ein automatisiertes System zur täglichen Überwachung von Mensen-Speiseplänen in Berlin mit speziellem Fokus auf Bratwurst-Verfügbarkeit! 

## 🎯 Features

- ✅ **Automatisches tägliches Scraping** von 3 Berliner Mensen (TU Hardenbergstraße, HU Süd, HU Nord)
- ✅ **14-Tage-Vorschau** aller Speisepläne
- ✅ **Bratwurst-Alarm** mit visueller Hervorhebung
- ✅ **Live-Suche** durch alle Gerichte
- ✅ **Responsive Design** für Desktop & Mobile
- ✅ **GitHub Pages Hosting** - kostenlos & automatisch aktualisiert
- ✅ **GitHub Actions** - läuft täglich um 7:00 Uhr

## 🚀 Setup

### 1. Repository erstellen

```bash
# Neues Repository auf GitHub erstellen und dann:
git init
git add .
git commit -m "🌭 Initial commit - Bratwurst Frühwarnsystem"
git branch -M main
git remote add origin https://github.com/DEIN-USERNAME/DEIN-REPO.git
git push -u origin main
```

### 2. GitHub Pages aktivieren

1. Gehe zu deinem Repository auf GitHub
2. Klicke auf **Settings** (Einstellungen)
3. Navigiere zu **Pages** (im linken Menü)
4. Unter **Source** wähle:
   - Branch: `gh-pages`
   - Folder: `/ (root)`
5. Klicke **Save**

Nach wenigen Minuten ist deine Seite verfügbar unter:
```
https://DEIN-USERNAME.github.io/DEIN-REPO/
```

### 3. GitHub Actions aktivieren

Die Actions sollten automatisch aktiviert sein. Falls nicht:

1. Gehe zu **Actions** in deinem Repository
2. Falls nötig, klicke **I understand my workflows, go ahead and enable them**
3. Der Workflow läuft dann:
   - **Täglich um 6:00 UTC** (7:00 MEZ / 8:00 MESZ)
   - **Bei jedem Push** zum main Branch
   - **Manuell** über "Run workflow"

### 4. Ersten Scrape starten

**Option A: Automatisch durch Push**
```bash
git commit --allow-empty -m "🚀 Trigger first scrape"
git push
```

**Option B: Manuell**
1. Gehe zu **Actions** → **Scrape Mensen-Speisepläne**
2. Klicke **Run workflow**
3. Wähle den Branch und klicke **Run workflow**

## 📁 Projektstruktur

```
BratwurstBot/
├── .github/
│   └── workflows/
│       └── scrape-mensen.yml    # GitHub Actions Workflow
├── scrape_mensen.py              # Haupt-Scraping-Script
├── requirements.txt              # Python Dependencies
├── README.md                     # Diese Datei
└── venv/                         # Python Virtual Environment (lokal)
```

**Generierte Dateien (nach Scraping):**
- `index.html` - Hauptseite mit Tabelle & Suche
- `mensen_data.json` - Rohdaten als JSON

## 🧪 Lokales Testen

### Virtual Environment aktivieren:
```bash
venv\Scripts\activate
```

### Dependencies installieren:
```bash
pip install -r requirements.txt
```

### Script ausführen:
```bash
python scrape_mensen.py
```

Die generierte `index.html` kannst du dann lokal im Browser öffnen.

## 🔧 Anpassungen

### Weitere Mensen hinzufügen

Bearbeite [`scrape_mensen.py`](scrape_mensen.py) Zeile 14-18:

```python
MENSEN = {
    "TU Hardenbergstraße": "https://www.stw.berlin/mensen/...",
    "HU Süd": "https://www.stw.berlin/mensen/...",
    "HU Nord": "https://www.stw.berlin/mensen/...",
    "Neue Mensa": "https://www.stw.berlin/mensen/..."  # Hinzufügen
}
```

### Scraping-Zeitraum ändern

In [`scrape_mensen.py`](scrape_mensen.py) Zeile 109:

```python
speiseplan = scrape_mensa(driver, url, mensa_name, days=14)  # Auf z.B. 30 ändern
```

### Zeitplan anpassen

In [`.github/workflows/scrape-mensen.yml`](.github/workflows/scrape-mensen.yml) Zeile 6:

```yaml
schedule:
  - cron: '0 6 * * *'  # 6:00 UTC = 7:00 MEZ
  # Beispiele:
  # '0 */6 * * *'  -> Alle 6 Stunden
  # '0 8 * * 1-5'  -> 8:00 UTC, Montag-Freitag
```

[Cron-Syntax Hilfe](https://crontab.guru/)

## 🎨 Features der Webseite

- **🔍 Live-Suche**: Echtzeit-Filterung aller Gerichte
- **🌭 Bratwurst-Alarm**: Automatische Erkennung & Hervorhebung
- **📊 Statistiken**: Übersicht über Gerichte & Bratwurst-Vorkommen
- **🎨 Modernes Design**: Responsive & ansprechend
- **📱 Mobile-optimiert**: Funktioniert auf allen Geräten

## 📝 Verwendete Technologien

- **Python 3.11**
- **Selenium** - Browser-Automation
- **BeautifulSoup** - HTML-Parsing
- **GitHub Actions** - CI/CD
- **GitHub Pages** - Hosting

## 🐛 Troubleshooting

### Workflow schlägt fehl?

1. Prüfe die **Actions**-Logs in deinem Repository
2. Stelle sicher, dass die Mensen-URLs korrekt sind
3. GitHub Actions benötigt die **Write-Permission** für Pages

### Seite zeigt nicht die neuesten Daten?

1. Warte 2-3 Minuten nach dem Workflow-Abschluss
2. Lösche Browser-Cache
3. GitHub Pages kann bis zu 10 Minuten für Updates brauchen

### Lokal funktioniert es, aber nicht in GitHub Actions?

- Chrome/ChromeDriver wird in Actions automatisch installiert
- Prüfe ob alle Dependencies in `requirements.txt` sind

## 📄 Lizenz

MIT License - Verwende es wie du willst! 🎉

## 🤝 Contributing

Pull Requests sind willkommen! Für größere Änderungen bitte zuerst ein Issue öffnen.

---

**Viel Erfolg bei der Bratwurst-Jagd!** 🌭🎯
