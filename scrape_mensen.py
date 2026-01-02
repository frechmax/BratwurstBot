"""
Bratwurst Frühwarnsystem - Mensen Scraper für GitHub Actions
Scrapt tägliche Speisepläne verschiedener Mensen und generiert eine HTML-Seite
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import json

# Mensa-URLs
MENSEN = {
    "HU Nord": "https://www.stw.berlin/mensen/einrichtungen/humboldt-universität-zu-berlin/mensa-hu-nord.html",
    "HU Süd": "https://www.stw.berlin/mensen/einrichtungen/humboldt-universität-zu-berlin/mensa-hu-süd.html",
    "TU Hardenbergstraße": "https://www.stw.berlin/mensen/einrichtungen/technische-universität-berlin/mensa-tu-hardenbergstraße.html",
}

def setup_driver():
    """Konfiguriert Chrome WebDriver für GitHub Actions (headless)"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.page_load_strategy = 'normal'
    chrome_options.set_capability('timeouts', {'implicit': 30000, 'pageLoad': 60000, 'script': 60000})
    return webdriver.Chrome(options=chrome_options)

def scrape_mensa(driver, url, mensa_name, days=14):
    """Scrapt Speiseplan einer Mensa für die nächsten 'days' Tage - nur Kategorien Aktionen und Essen"""
    print(f"\n🍽️  Scrape {mensa_name}...")
    
    # Mehrere Versuche mit erhöhtem Timeout
    max_retries = 3
    for attempt in range(max_retries):
        try:
            driver.set_page_load_timeout(60)
            driver.get(url)
            break
        except Exception as e:
            print(f"⚠️  Versuch {attempt + 1}/{max_retries} fehlgeschlagen: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                print(f"❌ Konnte {mensa_name} nach {max_retries} Versuchen nicht laden")
                return {}
    
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "spltag1"))
        )
    except Exception as e:
        print(f"❌ Konnte Speiseplan für {mensa_name} nicht laden: {e}")
        return {}
    
    heute = datetime.today()
    speiseplan = {}
    
    for day_offset in range(days):
        aktuelles_datum = heute + timedelta(days=day_offset)
        date_str = aktuelles_datum.strftime('%Y-%m-%d')
        
        try:
            driver.execute_script(f"loadSpeiseplanWochentag('{date_str}');")
            time.sleep(0.8)  # Kurze Pause für Content-Update
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Nur Kategorien "Aktionen" und "Essen" extrahieren
            gerichte_kategorien = {'Aktionen': [], 'Essen': []}
            
            # Finde alle splGroupWrapper divs
            group_wrappers = soup.find_all("div", class_="splGroupWrapper")
            
            for wrapper in group_wrappers:
                # Kategorie-Name finden
                group_div = wrapper.find("div", class_="splGroup")
                if group_div:
                    kategorie = group_div.text.strip()
                    
                    # Nur wenn Kategorie Aktionen oder Essen ist
                    if kategorie in ['Aktionen', 'Essen']:
                        # Alle Gerichte in dieser Kategorie finden
                        meals = wrapper.find_all("div", class_="splMeal")
                        for meal in meals:
                            gericht_span = meal.find("span", class_="bold")
                            if gericht_span:
                                gericht_name = gericht_span.text.strip()
                                
                                # Preis extrahieren (im Format "€ 3,65/7,30/8,40")
                                preis = ""
                                preis_div = meal.find("div", class_="text-right")
                                if preis_div:
                                    preis_text = preis_div.get_text(strip=True)
                                    if '€' in preis_text:
                                        preis = preis_text.split('\n')[0].strip()
                                
                                gerichte_kategorien[kategorie].append({
                                    'name': gericht_name,
                                    'preis': preis
                                })
            
            # Nur speichern wenn mindestens ein Gericht gefunden wurde
            if gerichte_kategorien['Aktionen'] or gerichte_kategorien['Essen']:
                speiseplan[date_str] = gerichte_kategorien
                total = len(gerichte_kategorien['Aktionen']) + len(gerichte_kategorien['Essen'])
                print(f"  ✓ {date_str}: {total} Gerichte (Aktionen: {len(gerichte_kategorien['Aktionen'])}, Essen: {len(gerichte_kategorien['Essen'])})")
            else:
                print(f"  - {date_str}: Keine Gerichte")
                
        except Exception as e:
            print(f"  ❌ Fehler bei {date_str}: {str(e)}")
    
    return speiseplan

def generate_html(all_data):
    """Generiert HTML-Seite als Tabelle mit Suchfunktion"""
    now = datetime.now().strftime('%d.%m.%Y %H:%M')
    
    # Sammle alle Daten nach Datum organisiert
    dates_data = {}
    total_dishes = 0
    bratwurst_count = 0
    
    for mensa_name, dates in all_data.items():
        for date_str, kategorien in dates.items():
            if date_str not in dates_data:
                dates_data[date_str] = {}
            
            dates_data[date_str][mensa_name] = kategorien
            
            # Statistiken
            total_dishes += len(kategorien['Aktionen']) + len(kategorien['Essen'])
            
            # Bratwurst zählen
            all_gerichte = kategorien['Aktionen'] + kategorien['Essen']
            for gericht in all_gerichte:
                # Unterstütze beide Formate: dict und string
                gericht_name = gericht['name'] if isinstance(gericht, dict) else gericht
                if 'bratwurst' in gericht_name.lower():
                    bratwurst_count += 1
    
    total_days = len(dates_data)
    mensen_namen = sorted(all_data.keys())
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌭 Bratwurst Frühwarnsystem</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 95%;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 40px;
            text-align: center;
            color: white;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .subtitle {{
            font-size: 1em;
            opacity: 0.95;
        }}
        
        .search-box {{
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .search-container {{
            max-width: 600px;
            margin: 0 auto;
            position: relative;
        }}
        
        #searchInput {{
            width: 100%;
            padding: 12px 45px 12px 15px;
            font-size: 16px;
            border: 2px solid #dee2e6;
            border-radius: 50px;
            outline: none;
            transition: all 0.3s;
        }}
        
        #searchInput:focus {{
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        
        .search-icon {{
            position: absolute;
            right: 18px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 18px;
        }}
        
        .content {{
            padding: 20px;
            overflow-x: auto;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-around;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            color: #6c757d;
            margin-top: 5px;
            font-size: 0.9em;
        }}
        
        .table-wrapper {{
            overflow-x: auto;
            margin-top: 20px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            min-width: 800px;
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        th:first-child {{
            border-radius: 8px 0 0 0;
        }}
        
        th:last-child {{
            border-radius: 0 8px 0 0;
        }}
        
        td {{
            padding: 10px 8px;
            border-bottom: 1px solid #e9ecef;
            vertical-align: top;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        tr.hidden {{
            display: none;
        }}
        
        .date-cell {{
            font-weight: bold;
            color: #495057;
            white-space: nowrap;
            min-width: 120px;
        }}
        
        .weekday {{
            color: #667eea;
            display: block;
            font-size: 0.9em;
        }}
        
        .mensa-cell {{
            padding: 8px;
        }}
        
        .kategorie-title {{
            font-weight: bold;
            color: #667eea;
            font-size: 0.85em;
            margin-bottom: 5px;
            text-transform: uppercase;
        }}
        
        .dish {{
            padding: 6px 8px;
            margin: 4px 0;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 3px solid #667eea;
            font-size: 0.95em;
            line-height: 1.3;
        }}
        
        .dish .price {{
            float: right;
            color: #a3a3a3;
            font-weight: bold;
            font-size: 0.85em;
            margin-left: 8px;
        }}
        
        .dish.bratwurst {{
            background: #fff3cd;
            border-left-color: #ff6b6b;
            font-weight: bold;
        }}
        
        .dish.bratwurst::before {{
            content: '🌭 ';
        }}
        
        .dish.highlight-search {{
            background: #d4edda;
            border-left-color: #28a745;
            font-weight: bold;
            box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
            transform: scale(1.02);
            transition: all 0.3s;
        }}
        
        .dish.bratwurst.highlight-search {{
            background: #ffeb3b;
            border-left-color: #ff6b6b;
            box-shadow: 0 2px 8px rgba(255, 107, 107, 0.4);
        }}
        
        .empty-cell {{
            color: #adb5bd;
            font-style: italic;
            text-align: center;
        }}
        
        footer {{
            background: #343a40;
            color: white;
            text-align: center;
            padding: 15px;
            font-size: 0.85em;
        }}
        
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #6c757d;
            font-size: 1.2em;
            display: none;
        }}
        
        @media (max-width: 768px) {{
            h1 {{ font-size: 1.8em; }}
            .stat-number {{ font-size: 1.5em; }}
            table {{ font-size: 12px; }}
            th, td {{ padding: 8px 5px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌭 Bratwurst Frühwarnsystem</h1>
            <div class="subtitle">Berliner Mensen-Speiseplan (Aktionen & Essen) | Aktualisiert: {now}</div>
        </header>
        
        <div class="search-box">
            <div class="search-container">
                <input 
                    type="text" 
                    id="searchInput" 
                    placeholder="Suche nach Gerichten... (z.B. 'Bratwurst', 'Schnitzel', 'vegan')"
                    autocomplete="off"
                >
                <span class="search-icon">🔍</span>
            </div>
        </div>
        
        <div class="content">
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number">{total_dishes}</div>
                    <div class="stat-label">Gerichte gesamt</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{total_days}</div>
                    <div class="stat-label">Tage</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{bratwurst_count}</div>
                    <div class="stat-label">🌭 Bratwürste</div>
                </div>
            </div>
            
            <div class="table-wrapper">
                <table id="mensaTable">
                    <thead>
                        <tr>
                            <th>Datum</th>
"""
    
    # Spaltenüberschriften für Mensen
    for mensa in mensen_namen:
        html += f'                            <th>{mensa}</th>\n'
    
    html += """                        </tr>
                    </thead>
                    <tbody>
"""
    
    # Tabellen-Zeilen generieren
    for date_str in sorted(dates_data.keys()):
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
        weekday = weekdays[date_obj.weekday()]
        formatted_date = date_obj.strftime('%d.%m.%Y')
        
        # Sammle alle Gerichte dieser Zeile für die Suche
        all_dishes_in_row = []
        for mensa in mensen_namen:
            if mensa in dates_data[date_str]:
                kategorien = dates_data[date_str][mensa]
                # Gerichte sind jetzt Dicts mit 'name' und 'preis'
                all_dishes_in_row.extend([g['name'] if isinstance(g, dict) else g for g in kategorien['Aktionen']])
                all_dishes_in_row.extend([g['name'] if isinstance(g, dict) else g for g in kategorien['Essen']])
        
        search_text = ' '.join(all_dishes_in_row).lower()
        
        html += f'                        <tr data-search="{search_text}">\n'
        html += f'                            <td class="date-cell"><span class="weekday">{weekday}</span>{formatted_date}</td>\n'
        
        # Zellen für jede Mensa
        for mensa in mensen_namen:
            if mensa in dates_data[date_str]:
                kategorien = dates_data[date_str][mensa]
                html += '                            <td class="mensa-cell">\n'
                
                # Aktionen
                if kategorien['Aktionen']:
                    html += '                                <div class="kategorie-title">Aktionen</div>\n'
                    for gericht in kategorien['Aktionen']:
                        # Unterstütze beide Formate: dict und string
                        if isinstance(gericht, dict):
                            gericht_name = gericht['name']
                            gericht_preis = gericht.get('preis', '')
                        else:
                            gericht_name = gericht
                            gericht_preis = ''
                        
                        is_bratwurst = 'bratwurst' in gericht_name.lower()
                        css_class = 'dish bratwurst' if is_bratwurst else 'dish'
                        
                        if gericht_preis:
                            html += f'                                <div class="{css_class}">{gericht_name} <span class="price">{gericht_preis}</span></div>\n'
                        else:
                            html += f'                                <div class="{css_class}">{gericht_name}</div>\n'
                
                # Essen
                if kategorien['Essen']:
                    html += '                                <div class="kategorie-title" style="margin-top: 8px;">Essen</div>\n'
                    for gericht in kategorien['Essen']:
                        # Unterstütze beide Formate: dict und string
                        if isinstance(gericht, dict):
                            gericht_name = gericht['name']
                            gericht_preis = gericht.get('preis', '')
                        else:
                            gericht_name = gericht
                            gericht_preis = ''
                        
                        is_bratwurst = 'bratwurst' in gericht_name.lower()
                        css_class = 'dish bratwurst' if is_bratwurst else 'dish'
                        
                        if gericht_preis:
                            html += f'                                <div class="{css_class}">{gericht_name} <span class="price">{gericht_preis}</span></div>\n'
                        else:
                            html += f'                                <div class="{css_class}">{gericht_name}</div>\n'
                
                html += '                            </td>\n'
            else:
                html += '                            <td class="empty-cell">-</td>\n'
        
        html += '                        </tr>\n'
    
    html += """                    </tbody>
                </table>
            </div>
            
            <div id="noResults" class="no-results">
                😕 Keine Gerichte gefunden. Versuche eine andere Suche!
            </div>
        </div>
        
        <footer>
            <p>Daten von www.stw.berlin</p>
        </footer>
    </div>
    
    <script>
        // Suchfunktion mit Highlighting
        const searchInput = document.getElementById('searchInput');
        const tableRows = document.querySelectorAll('#mensaTable tbody tr');
        const allDishes = document.querySelectorAll('.dish');
        const noResults = document.getElementById('noResults');
        const tableWrapper = document.querySelector('.table-wrapper');
        
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();
            let visibleRows = 0;
            
            // Entferne alle Highlights
            allDishes.forEach(dish => {
                dish.classList.remove('highlight-search');
            });
            
            tableRows.forEach(row => {
                if (searchTerm === '') {
                    // Keine Suche: Alle Zeilen anzeigen
                    row.classList.remove('hidden');
                    visibleRows++;
                } else {
                    // Finde alle Gerichte in dieser Zeile
                    const dishes = row.querySelectorAll('.dish');
                    let hasMatch = false;
                    
                    dishes.forEach(dish => {
                        const dishText = dish.textContent.toLowerCase();
                        if (dishText.includes(searchTerm)) {
                            // Gericht gefunden: highlighten
                            dish.classList.add('highlight-search');
                            hasMatch = true;
                        }
                    });
                    
                    // Zeile nur anzeigen, wenn mindestens ein Gericht matched
                    if (hasMatch) {
                        row.classList.remove('hidden');
                        visibleRows++;
                    } else {
                        row.classList.add('hidden');
                    }
                }
            });
            
            if (visibleRows === 0) {
                noResults.style.display = 'block';
                tableWrapper.style.display = 'none';
            } else {
                noResults.style.display = 'none';
                tableWrapper.style.display = 'block';
            }
        });
        
        // Enter-Taste
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
            }
        });
    </script>
</body>
</html>
"""
    
    return html

def main():
    print("🌭 Bratwurst Frühwarnsystem gestartet!")
    print("=" * 60)
    
    driver = setup_driver()
    all_data = {}
    
    try:
        for mensa_name, url in MENSEN.items():
            speiseplan = scrape_mensa(driver, url, mensa_name, days=31)
            all_data[mensa_name] = speiseplan
    finally:
        driver.quit()
    
    # HTML generieren
    print("\n📝 Generiere HTML-Seite...")
    html_content = generate_html(all_data)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ index.html erfolgreich erstellt!")
    
    # JSON für später speichern (optional)
    with open("mensen_data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print("✅ mensen_data.json gespeichert!")
    print("\n🎉 Bratwurst Frühwarnsystem beendet!")

if __name__ == "__main__":
    main()
