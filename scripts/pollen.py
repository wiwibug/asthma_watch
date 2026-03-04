import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from datetime import datetime
import boto3
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PollenDataScraper:
    def __init__(self, bucket_name, s3_key):
        self.bucket_name = bucket_name
        self.s3_key = s3_key
        self.temp_csv_path = '/tmp/pollen.csv'
        self.s3 = boto3.client('s3')
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
        options = [(opt['value'], opt.get_text(strip=True)) for opt in select.find_all('option') if opt.get('value')]
        return pd.DataFrame(options, columns=['Valeur', 'Nom'])

    def fetch_pollen_data(self):
        logger.info("🚀 Début du scraping...")
        today = datetime.today().date()
        all_data = []

        soup = self.get_soup("https://www.pollens.fr/les-risques/risques-par-ville/1/54/2025")
        if not soup:
            return pd.DataFrame()

        city_df = self.fetch_options(soup, "citySelector")
        pollen_df = self.fetch_options(soup, "pollenSelector").iloc[1:]

        for _, city_row in city_df.iterrows():
            for _, pollen_row in pollen_df.iterrows():
                logger.info(f"Scraping {city_row['Nom']} - {pollen_row['Nom']}")
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
                        entry_date = datetime.fromtimestamp(entry[date_key]/1000).date()
                        if entry_date <= today:
                            current_city_data.append({
                                'Ville': city_row['Nom'],
                                'Pollen': pollen_row['Nom'],
                                'date': entry_date.strftime('%Y-%m-%d'),
                                'level': entry.get('level'),
                                'RealLevelValue': entry.get('realLevelValue'),
                                '_date_for_sort': entry_date  # Champ temporaire pour le tri
                            })
                
                # Tri des données pour cette ville/pollen par date décroissante
                current_city_data.sort(key=lambda x: x['_date_for_sort'], reverse=True)
                # Suppression du champ temporaire avant d'ajouter à all_data
                for item in current_city_data:
                    del item['_date_for_sort']
                all_data.extend(current_city_data)

        return pd.DataFrame(all_data)

    def download_existing_data(self):
        try:
            self.s3.download_file(self.bucket_name, self.s3_key, self.temp_csv_path)
            existing_df = pd.read_csv(self.temp_csv_path)
            # Conversion de la colonne Date en datetime pour le tri
            existing_df['date'] = pd.to_datetime(existing_df['Date'])
            return existing_df
        except Exception as e:
            logger.warning(f"Aucun fichier existant: {e}")
            return pd.DataFrame()

    def update_and_upload(self, new_df):
        existing_df = self.download_existing_data()
        
        # Conversion de la colonne Date en datetime pour le nouveau DataFrame
        new_df['date'] = pd.to_datetime(new_df['date'])
        
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        
        # Suppression des doublons en gardant l'entrée la plus récente
        combined_df = combined_df.drop_duplicates(
            subset=['Ville', 'Pollen', 'date'], 
            keep='last'
        )
        
        # Tri final par ville, pollen et date (du plus récent au plus ancien)
        combined_df = combined_df.sort_values(
            by=['Ville', 'Pollen', 'date'],
            ascending=[True, True, False]
        )
        
        # Reconversion de la date en format string pour la sauvegarde
        combined_df['date'] = combined_df['date'].dt.strftime('%Y-%m-%d')
        
        combined_df.to_csv(self.temp_csv_path, index=False)
        
        try:
            self.s3.upload_file(self.temp_csv_path, self.bucket_name, self.s3_key)
            logger.info(f"✅ Fichier {self.s3_key} mis à jour sur S3")
        except Exception as e:
            logger.error(f"❌ Erreur upload: {e}")
        finally:
            if os.path.exists(self.temp_csv_path):
                os.remove(self.temp_csv_path)

    def run(self):
        new_data = self.fetch_pollen_data()
        if not new_data.empty:
            self.update_and_upload(new_data)
        else:
            logger.warning("Aucune nouvelle donnée scrapée.")

if __name__ == "__main__":
    scraper = PollenDataScraper(
        bucket_name="bucket-asthme-scraping",
        s3_key="pollen.csv"
    )
    scraper.run()