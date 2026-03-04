#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import csv
import pandas as pd
from datetime import datetime, date
import boto3
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

class AsthmeDataScraper:
    def __init__(self, headless=True, output_dir='../../data/raw/'):
        chrome_options = Options()
        chrome_options.add_argument('--user-data-dir=/tmp/chrome-data-{}'.format(os.getpid()))
        if headless:
            chrome_options.add_argument('--headless')
        # Options supplémentaires pour EC2
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
    
        service = Service('/usr/lib/chromium-browser/chromedriver')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.output_dir = output_dir

    def setup_driver(self):
        self.driver.get("https://geodes.santepubliquefrance.fr/#c=indicator&view=map2")
        print("Waiting for page load...")
        WebDriverWait(self.driver, 40).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print(f"Page loaded - Title: {self.driver.title}")
        self.driver.save_screenshot("/home/ubuntu/page_load.png")

    def search_asthme(self):
        # Saisir "asthme" dans la barre de recherche et valider
        search_box = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.NAME, "search"))
        )
        search_box.clear()
        search_box.send_keys("asthme")
        
        ok_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'OK')]")
        ok_button.click()
        time.sleep(5)

    def find_urgences_section(self):
        # Faire défiler le panneau jusqu'à trouver la section "Taux de passages aux urgences"
        scrollable_panel = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@class='ui-collapsible-set vertical-scrollable indic-container']")
            )
        )
        
        taux_passages_xpath = (
            "//h3[contains(@class, 'ui-collapsible-heading')]"
            "//a[starts-with(normalize-space(), 'Taux de passages aux urgences')]"
        )
        
        for _ in range(20):  # Limiter à 20 tentatives
            try:
                taux_passages_element = self.driver.find_element(By.XPATH, taux_passages_xpath)
                if taux_passages_element.is_displayed():
                    actions = ActionChains(self.driver)
                    actions.move_to_element(taux_passages_element).click().perform()
                    break
            except Exception:
                self.driver.execute_script("arguments[0].scrollBy(0, 100);", scrollable_panel)
                time.sleep(0.5)

    def select_filters(self):
        # Attendre que le modal disparaisse
        WebDriverWait(self.driver, 20).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "modalFreezeWindow2"))
        )
    
        # Sélectionner "tous âges"
        tous_ages_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'tous âges')]"))
        )
        tous_ages_button.click()
    
        # Cliquer sur tableau via JavaScript
        tableau_button = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.ID, "tm_table"))
        )
        self.driver.execute_script("arguments[0].click();", tableau_button)
        time.sleep(5)


    def extract_data(self):
        # Localiser le tableau et extraire les données
        table = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//table[@id='tm_datatable']"))
        )
        rows = table.find_elements(By.XPATH, ".//tbody/tr")
        data = []
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:
                data.append({
                    "Code": cells[0].text,
                    "Département": cells[1].text,
                    "Chiffre": cells[2].text
                })
        return data

    def save_data(self, data):
        # Création du dossier de sortie s'il n'existe pas
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        # Nommer le fichier CSV avec la date du jour
        filename = f'asthme_data_{datetime.now().strftime("%Y%m%d")}.csv'
        filepath = os.path.join(self.output_dir, filename)
        
        # Enregistrer les données dans le CSV avec les colonnes dans l'ordre souhaité
        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            fieldnames = ["Département", "Code", "Chiffre"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow({
                    "Département": row.get("Département", ""),
                    "Code": row.get("Code", ""),
                    "Chiffre": row.get("Chiffre", "")
                })
        return filepath

    def run_scraping(self):
        try:
            self.setup_driver()
            self.search_asthme()
            self.find_urgences_section()
            self.select_filters()
            data = self.extract_data()
            csv_filepath = self.save_data(data)
            print(f"Scraping terminé. Données sauvegardées dans : {csv_filepath}")
            return csv_filepath
        except Exception as e:
            print(f"Erreur lors du scraping : {e}")
            raise
        finally:
            self.driver.quit()


def update_excel(csv_path, excel_path=None):
    """
    Cette fonction lit le CSV produit par le scraper et met à jour le fichier Excel.
    Si le fichier Excel n'existe pas, il sera créé avec une structure de base.
    """
    # Calculer le chemin absolu du fichier Excel s'il n'est pas fourni
    if excel_path is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        excel_path = os.path.join(project_root, "data", "processed", "geodes_complet.xlsx")
    
    # Générer les informations temporelles
    aujourdhui = date.today()
    annee = aujourdhui.year
    numero_semaine = aujourdhui.isocalendar()[1]  # Numéro de semaine ISO
    mois = aujourdhui.strftime('%b')              # Mois abrégé (ex. 'Feb')
    semaine = f"{annee}-S{numero_semaine:02d}"

    # Lecture du CSV contenant les données scrappées
    try:
        df_csv = pd.read_csv(csv_path, encoding="utf-8")
    except Exception as e:
        print(f"Erreur lors de la lecture du CSV : {e}")
        return

    # Créer un dictionnaire associant chaque département à son chiffre
    donnees_scrap = {}
    for _, row in df_csv.iterrows():
        dept = str(row["Département"]).strip()
        try:
            chiffre = float(str(row["Chiffre"]).replace(",", "."))
        except Exception:
            chiffre = 0
        donnees_scrap[dept] = chiffre

    # Si le fichier Excel n'existe pas, on le crée avec des colonnes de base
    if not os.path.exists(excel_path):
        print(f"Le fichier Excel {excel_path} n'existe pas. Création d'un nouveau fichier.")
        # On crée les colonnes : temporelles + départements présents dans les données scrappées
        departements = sorted(donnees_scrap.keys())
        colonnes = ["Semaine", "Annee", "Mois"] + departements
        df_excel = pd.DataFrame(columns=colonnes)
    else:
        try:
            df_excel = pd.read_excel(excel_path, engine="openpyxl")
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier Excel : {e}")
            return

    # Colonnes temporelles attendues dans le fichier Excel
    colonnes_temporaires = ["Semaine", "Annee", "Mois"]
    # Colonnes départementales = toutes celles qui ne sont pas temporelles
    colonnes_departements = [col for col in df_excel.columns if col not in colonnes_temporaires]

    # Si le fichier Excel est vide (pas de colonnes départementales définies), on en déduit les départements depuis les données scrappées
    if not colonnes_departements:
        colonnes_departements = sorted(donnees_scrap.keys())
        colonnes_finales = colonnes_temporaires + colonnes_departements
        df_excel = pd.DataFrame(columns=colonnes_finales)

    # Création de la nouvelle ligne
    nouvelle_ligne = {
        "Semaine": semaine,
        "Annee": annee,
        "Mois": mois
    }
    for dept in colonnes_departements:
        nouvelle_ligne[dept] = donnees_scrap.get(dept, 0)

    # Reconstruire le dictionnaire pour respecter l'ordre souhaité
    colonnes_finales = colonnes_temporaires + [col for col in df_excel.columns if col not in colonnes_temporaires]
    nouvelle_ligne_reord = {col: nouvelle_ligne.get(col, 0) for col in colonnes_finales}

    # Vérifier si les données départementales ont changé par rapport à la dernière ligne du fichier Excel
    if not df_excel.empty:
        last_row = df_excel.iloc[-1]
        doublon = True
        for dept in colonnes_departements:
            val_last = last_row.get(dept, 0)
            if pd.isna(val_last):
                val_last = 0
            if float(val_last) != float(nouvelle_ligne_reord.get(dept, 0)):
                doublon = False
                break
        if doublon:
            print("Les données départementales n'ont pas changé par rapport à la dernière ligne. Aucune nouvelle ligne n'a été ajoutée.")
            return

    # Ajout de la nouvelle ligne et sauvegarde du fichier Excel
    df_nouvelle_ligne = pd.DataFrame([nouvelle_ligne_reord])
    df_resultat = pd.concat([df_excel, df_nouvelle_ligne], ignore_index=True)
    try:
        # Assurer que le dossier de destination existe
        os.makedirs(os.path.dirname(excel_path), exist_ok=True)
        df_resultat.to_excel(excel_path, index=False, engine="openpyxl")
        print(f"Nouvelle ligne ajoutée avec succès dans le fichier {excel_path}.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du fichier Excel : {e}")


def upload_to_s3(local_file, bucket_name, s3_file_name):
    """
    Upload un fichier local vers un bucket S3.
    """
    if not os.path.exists(local_file):
        print(f"❌ Erreur : Le fichier {local_file} n'existe pas. Upload annulé.")
        return
    
    s3 = boto3.client('s3')

    try:
        print(f"📤 Upload en cours : {local_file} vers s3://{bucket_name}/{s3_file_name}...")
        s3.upload_file(local_file, bucket_name, s3_file_name)
        print(f"✅ Upload réussi : {s3_file_name} dans le bucket {bucket_name}.")
    except Exception as e:
        print(f"❌ Erreur lors de l'upload vers S3 : {e}")

def update_excel_s3(csv_path, bucket_name, excel_key):
    """
    Met à jour le fichier Excel stocké dans S3 en ajoutant une nouvelle ligne.
    """
    s3 = boto3.client('s3')
    
    # Télécharger le fichier Excel existant depuis S3
    temp_excel_path = '/tmp/temp_geodes.xlsx'
    try:
        s3.download_file(bucket_name, excel_key, temp_excel_path)
        df_excel = pd.read_excel(temp_excel_path, engine="openpyxl")
    except s3.exceptions.NoSuchKey:
        print(f"Fichier Excel non trouvé dans S3, création d'un nouveau fichier")
        df_excel = pd.DataFrame()
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier Excel : {e}")
        return

    # Reste de votre logique de mise à jour existante
    aujourdhui = date.today()
    annee = aujourdhui.year
    numero_semaine = aujourdhui.isocalendar()[1]
    mois = aujourdhui.strftime('%b')
    semaine = f"{annee}-S{numero_semaine:02d}"

    df_csv = pd.read_csv(csv_path, encoding="utf-8")
    donnees_scrap = {
        str(row["Département"]).strip(): float(
            str(row["Chiffre"])
            .replace(",", ".")
            .replace("\u202f", "")
            .strip()
        ) if "N/A" not in str(row["Chiffre"]) else 0
        for _, row in df_csv.iterrows()
    }

    # Configuration des colonnes
    colonnes_temporaires = ["Semaine", "Annee", "Mois"]
    if df_excel.empty:
        colonnes_departements = sorted(donnees_scrap.keys())
        df_excel = pd.DataFrame(columns=colonnes_temporaires + colonnes_departements)
    else:
        colonnes_departements = [col for col in df_excel.columns if col not in colonnes_temporaires]

    # Création nouvelle ligne
    nouvelle_ligne = {
        "Semaine": semaine,
        "Annee": annee,
        "Mois": mois,
        **{dept: donnees_scrap.get(dept, 0) for dept in colonnes_departements}
    }

    # Vérification des doublons
    if not df_excel.empty:
        last_row = df_excel.iloc[-1]
        if not any(float(last_row.get(dept, 0)) != float(nouvelle_ligne.get(dept, 0)) 
                  for dept in colonnes_departements):
            print("Données identiques à la dernière ligne, pas de mise à jour nécessaire")
            return

    # Ajout et sauvegarde
    df_excel = pd.concat([df_excel, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
    df_excel.to_excel(temp_excel_path, index=False, engine="openpyxl")
    
    # Upload vers S3
    try:
        s3.upload_file(temp_excel_path, bucket_name, excel_key)
        print(f"Fichier Excel mis à jour avec succès dans S3: {excel_key}")
    except Exception as e:
        print(f"Erreur lors de l'upload vers S3: {e}")
    finally:
        if os.path.exists(temp_excel_path):
            os.remove(temp_excel_path)



def verify_s3_changes(bucket_name, excel_key):
    """Affiche les 3 dernières lignes du fichier Excel avant et après modification"""
    s3 = boto3.client('s3')
    temp_path = '/tmp/verify_geodes.xlsx'
    
    try:
        # Lecture avant modification
        s3.download_file(bucket_name, excel_key, temp_path)
        df_before = pd.read_excel(temp_path)
        print("\n=== AVANT MODIFICATION ===")
        print(df_before.tail(3))
        
        # Attendre la fin des modifications
        time.sleep(5)
        
        # Lecture après modification
        s3.download_file(bucket_name, excel_key, temp_path)
        df_after = pd.read_excel(temp_path)
        print("\n=== APRÈS MODIFICATION ===")
        print(df_after.tail(3))
        
        if len(df_after) > len(df_before):
            print("\n✅ Nouvelle ligne ajoutée")
        else:
            print("\n❌ Pas de nouvelle ligne")
            
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_scraping_pipeline():
    try:
        bucket_name = "bucket-asthme-scraping"
        excel_key = "geodes_complet.xlsx"
        
        verify_s3_changes(bucket_name, excel_key)
        
        logger.info("🚀 Début du scraping...")
        # Ajout de plus d'options pour Chrome
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        scraper = AsthmeDataScraper(headless=True, output_dir='./data/raw')
        csv_filepath = scraper.run_scraping()
        
        if not csv_filepath:
            logger.error("❌ Échec du scraping")
            return
            
        # Vérifier si le CSV a été créé et contient des données
        if os.path.exists(csv_filepath):
            df_check = pd.read_csv(csv_filepath)
            if df_check.empty:
                logger.error("❌ Le CSV est vide")
                return
            logger.info(f"✅ CSV créé avec {len(df_check)} lignes")
            
        logger.info("🛠 Mise à jour du fichier Excel dans S3...")
        update_excel_s3(csv_filepath, bucket_name, excel_key)
        
        time.sleep(5)
        verify_s3_changes(bucket_name, excel_key)

    except Exception as e:
        logger.error(f"❌ Erreur détaillée: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run_scraping_pipeline()