import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
import os
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
# Chemin vers le dossier data/ (racine du projet)
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
POLLEN_CSV = DATA_DIR / "pollen.csv"
 
 
class PollenDataScraper:
    def __init__(self):
        self.session = requests.Session()
 
    def get_soup(self, url):
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            logger.error(f"Erreur requête {url}: {e}")
            return None
 
    def fetch_options(self, soup, selector_id):
        select = soup.find(id=selector_id) if soup else None
        if not select:
            return pd.DataFrame()
        options = [
            (opt['value'], opt.get_text(strip=True))
            for opt in select.find_all('option') if opt.get('value')
        ]
        return pd.DataFrame(options, columns=['Valeur', 'Nom'])
 
    def fetch_pollen_data(self):
        logger.info("🚀 Début du scraping pollens.fr...")
        today = datetime.today().date()
        all_data = []
 
        year = datetime.today().year
        soup = self.get_soup(f"https://www.pollens.fr/les-risques/risques-par-ville/1/54/{year}")
        if not soup:
            logger.error("Impossible de charger la page pollens.fr")
            return pd.DataFrame()
 
        city_df = self.fetch_options(soup, "citySelector")
        pollen_df = self.fetch_options(soup, "pollenSelector").iloc[1:]
 
        for _, city_row in city_df.iterrows():
            for _, pollen_row in pollen_df.iterrows():
                logger.info(f"  Scraping {city_row['Nom']} - {pollen_row['Nom']}")
                url = f"https://www.pollens.fr/les-risques/risques-par-ville/{city_row['Valeur']}/{pollen_row['Valeur']}"
                soup = self.get_soup(url)
                if not soup:
                    continue
 
                script_data = {}
                for var_name in ["graphData", "previousYearGraphData"]:
                    script = soup.find('script', string=re.compile(fr'var {var_name} ='))
                    if script:
                        match = re.search(fr'var {var_name}\s*=\s*(\[.*?\])', script.string, re.DOTALL)
                        if match:
                            try:
                                script_data[var_name] = json.loads(match.group(1))
                            except json.JSONDecodeError as e:
                                logger.error(f"Erreur JSON {var_name}: {e}")
 
                current_city_data = []
                for var_name in ["graphData", "previousYearGraphData"]:
                    for entry in script_data.get(var_name, []):
                        date_key = 'realDate' if var_name == "previousYearGraphData" else 'date'
                        entry_date = datetime.fromtimestamp(entry[date_key] / 1000).date()
                        if entry_date <= today:
                            current_city_data.append({
                                'Ville': city_row['Nom'],
                                'Pollen': pollen_row['Nom'],
                                'date': entry_date.strftime('%Y-%m-%d'),
                                'level': entry.get('level'),
                                'RealLevelValue': entry.get('realLevelValue'),
                                '_date_for_sort': entry_date
                            })
 
                current_city_data.sort(key=lambda x: x['_date_for_sort'], reverse=True)
                for item in current_city_data:
                    del item['_date_for_sort']
                all_data.extend(current_city_data)
 
        return pd.DataFrame(all_data)
 
    def load_existing_data(self):
        """Charge le CSV existant depuis data/ si présent."""
        if POLLEN_CSV.exists():
            try:
                existing_df = pd.read_csv(POLLEN_CSV)
                existing_df['date'] = pd.to_datetime(existing_df['date'], errors='coerce')
                return existing_df
            except Exception as e:
                logger.warning(f"Impossible de lire le CSV existant : {e}")
        return pd.DataFrame()
 
    def update_and_save(self, new_df):
        """Fusionne les nouvelles données avec l'existant et sauvegarde dans data/."""
        existing_df = self.load_existing_data()
        new_df['date'] = pd.to_datetime(new_df['date'])
 
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(
            subset=['Ville', 'Pollen', 'date'],
            keep='last'
        )
        combined_df = combined_df.sort_values(
            by=['Ville', 'Pollen', 'date'],
            ascending=[True, True, False]
        )
        combined_df['date'] = combined_df['date'].dt.strftime('%Y-%m-%d')
        combined_df.to_csv(POLLEN_CSV, index=False)
        logger.info(f"✅ {POLLEN_CSV} mis à jour ({len(combined_df)} lignes).")
 
    def run(self):
        new_data = self.fetch_pollen_data()
        if not new_data.empty:
            self.update_and_save(new_data)
        else:
            logger.warning("⚠️ Aucune nouvelle donnée scrapée.")
 
 
if __name__ == "__main__":
    scraper = PollenDataScraper()
    scraper.run()
 
