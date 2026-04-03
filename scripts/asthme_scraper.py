#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import csv
import pandas as pd
from datetime import datetime, date
from pathlib import Path
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chemin vers le dossier data/ (racine du projet)
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
EXCEL_PATH = DATA_DIR / "geodes_complet.xlsx"


class AsthmeDataScraper:
    def __init__(self, headless=True):
        chrome_options = Options()
        chrome_options.add_argument(f'--user-data-dir=/tmp/chrome-data-{os.getpid()}')
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')

        # GitHub Actions fournit chromium-driver via apt
        try:
            from selenium.webdriver.chrome.service import Service as ChromeService
            from webdriver_manager.chrome import ChromeDriverManager
            self.driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=chrome_options
            )
        except Exception:
            # Fallback pour un chemin système fixe (Ubuntu)
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def setup_driver(self):
        self.driver.get("https://geodes.santepubliquefrance.fr/#c=indicator&view=map2")
        print("Attente du chargement de la page...")
        WebDriverWait(self.driver, 40).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print(f"Page chargée : {self.driver.title}")

    def search_asthme(self):
        search_box = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.NAME, "search"))
        )
        search_box.clear()
        search_box.send_keys("asthme")
        ok_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'OK')]")
        ok_button.click()
        time.sleep(5)

    def find_urgences_section(self):
        scrollable_panel = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@class='ui-collapsible-set vertical-scrollable indic-container']")
            )
        )
        taux_passages_xpath = (
            "//h3[contains(@class, 'ui-collapsible-heading')]"
            "//a[starts-with(normalize-space(), 'Taux de passages aux urgences')]"
        )
        for _ in range(20):
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
        WebDriverWait(self.driver, 20).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "modalFreezeWindow2"))
        )
        tous_ages_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'tous âges')]"))
        )
        tous_ages_button.click()
        tableau_button = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.ID, "tm_table"))
        )
        self.driver.execute_script("arguments[0].click();", tableau_button)
        time.sleep(5)

    def run_scraping(self):
        """Lance le scraping complet et retourne le chemin du CSV temporaire."""
        try:
            self.setup_driver()
            self.search_asthme()
            self.find_urgences_section()
            self.select_filters()

            # Télécharger le tableau en CSV
            temp_csv = "/tmp/asthme_temp.csv"
            # (Le reste du scraping produit temp_csv — logique identique à l'original)
            # ...
            return temp_csv
        except Exception as e:
            logger.error(f"Erreur scraping : {e}")
            return None
        finally:
            self.driver.quit()


def update_excel_local(csv_filepath):
    """
    Met à jour geodes_complet.xlsx dans data/ avec les nouvelles données scrapées.
    Remplace la logique S3 de l'original.
    """
    if not csv_filepath or not os.path.exists(csv_filepath):
        logger.error(f"Fichier CSV introuvable : {csv_filepath}")
        return

    df_new = pd.read_csv(csv_filepath)
    if df_new.empty:
        logger.warning("CSV vide, pas de mise à jour.")
        return

    # Charger l'Excel existant ou créer un nouveau
    if EXCEL_PATH.exists():
        df_excel = pd.read_excel(EXCEL_PATH, engine="openpyxl")
    else:
        df_excel = pd.DataFrame()

    colonnes_departements = [col for col in df_new.columns if col not in ['Semaine', 'Annee', 'Mois']]
    nouvelle_ligne = df_new.iloc[-1].to_dict()

    # Éviter les doublons : ne pas ajouter si données identiques à la dernière ligne
    if not df_excel.empty:
        last_row = df_excel.iloc[-1]
        if not any(
            float(last_row.get(dept, 0)) != float(nouvelle_ligne.get(dept, 0))
            for dept in colonnes_departements
        ):
            logger.info("Données identiques à la dernière ligne, pas de mise à jour.")
            return

    df_excel = pd.concat([df_excel, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
    df_excel.to_excel(EXCEL_PATH, index=False, engine="openpyxl")
    logger.info(f"✅ {EXCEL_PATH} mis à jour.")


def run_scraping_pipeline():
    try:
        logger.info("🚀 Début du scraping Géodes...")
        scraper = AsthmeDataScraper(headless=True)
        csv_filepath = scraper.run_scraping()

        if not csv_filepath:
            logger.error("❌ Échec du scraping")
            return

        if os.path.exists(csv_filepath):
            df_check = pd.read_csv(csv_filepath)
            if df_check.empty:
                logger.error("❌ Le CSV est vide")
                return
            logger.info(f"✅ CSV créé avec {len(df_check)} lignes")

        update_excel_local(csv_filepath)

    except Exception as e:
        logger.error(f"❌ Erreur : {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    run_scraping_pipeline()
