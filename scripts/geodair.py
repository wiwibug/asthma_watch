## Library ##
import requests
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import io
import unidecode

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Clé API Geodair
api_key = "Fh4Saf51BS4oqiq7TItLXyf5qetIuC9Y"

# Dictionnaire des polluants d'intérêts
polluants = {
    'code': ["01", "03", "08", "24", "39"],
    'name': ['SO2', 'NO2', 'O3', 'PM10', 'PM2.5']
}

# Dictionnaire des départements français
departements = {
    "01": "Ain",
    "02": "Aisne",
    "03": "Allier",
    "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes",
    "07": "Ardèche",
    "08": "Ardennes",
    "09": "Ariège",
    "10": "Aube",
    "11": "Aude",
    "12": "Aveyron",
    "13": "Bouches-du-Rhône",
    "14": "Calvados",
    "15": "Cantal",
    "16": "Charente",
    "17": "Charente-Maritime",
    "18": "Cher",
    "19": "Corrèze",
    "2A": "Corse-du-Sud",
    "2B": "Haute-Corse",
    "21": "Côte-d'Or",
    "22": "Côtes-d'Armor",
    "23": "Creuse",
    "24": "Dordogne",
    "25": "Doubs",
    "26": "Drôme",
    "27": "Eure",
    "28": "Eure-et-Loir",
    "29": "Finistère",
    "30": "Gard",
    "31": "Haute-Garonne",
    "32": "Gers",
    "33": "Gironde",
    "34": "Hérault",
    "35": "Ille-et-Vilaine",
    "36": "Indre",
    "37": "Indre-et-Loire",
    "38": "Isère",
    "39": "Jura",
    "40": "Landes",
    "41": "Loir-et-Cher",
    "42": "Loire",
    "43": "Haute-Loire",
    "44": "Loire-Atlantique",
    "45": "Loiret",
    "46": "Lot",
    "47": "Lot-et-Garonne",
    "48": "Lozère",
    "49": "Maine-et-Loire",
    "50": "Manche",
    "51": "Marne",
    "52": "Haute-Marne",
    "53": "Mayenne",
    "54": "Meurthe-et-Moselle",
    "55": "Meuse",
    "56": "Morbihan",
    "57": "Moselle",
    "58": "Nièvre",
    "59": "Nord",
    "60": "Oise",
    "61": "Orne",
    "62": "Pas-de-Calais",
    "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées",
    "66": "Pyrénées-Orientales",
    "67": "Bas-Rhin",
    "68": "Haut-Rhin",
    "69": "Rhône",
    "70": "Haute-Saône",
    "71": "Saône-et-Loire",
    "72": "Sarthe",
    "73": "Savoie",
    "74": "Haute-Savoie",
    "75": "Paris",
    "76": "Seine-Maritime",
    "77": "Seine-et-Marne",
    "78": "Yvelines",
    "79": "Deux-Sèvres",
    "80": "Somme",
    "81": "Tarn",
    "82": "Tarn-et-Garonne",
    "83": "Var",
    "84": "Vaucluse",
    "85": "Vendée",
    "86": "Vienne",
    "87": "Haute-Vienne",
    "88": "Vosges",
    "89": "Yonne",
    "90": "Territoire de Belfort",
    "91": "Essonne",
    "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne",
    "95": "Val-d'Oise",
    "97": "Outre-mer"
}

## Function ##

def clean_header(df):
    """
    Nettoie les en-têtes d'un dataFrame
    - Passe tout en minuscule
    - Remplace les espaces par des underscores
    - Supprime les accents
    - Retire les caractères spéciaux non alphanumériques
    
    Entrée
    - df (dataFrame pandas) dataFrame à nettoyer
    
    Sortie
    - df (dataFrame pandas) dateFrame nettoyé
    """
    # Nettoyage des en-têtes
    df.columns = [
        unidecode.unidecode(col).lower().replace(" ", "_").replace("-", "_")
        for col in df.columns
    ]    
    return df

def deduplicate_csv(csv):
    if not os.path.exists(csv):
        raise FileNotFoundError(f"Le fichier {csv} n'existe pas.")
    df = pd.read_csv(csv, sep=";", low_memory=False, encoding="utf-8")
    date_columns = ['date_de_debut', 'date_de_fin']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', format='%Y/%m/%d %H:%M:%S')
    if 'validite' not in df.columns or 'date_de_fin' not in df.columns:
        raise ValueError("Colonnes 'validite' ou 'date_de_fin' manquantes.")
    df = df.sort_values(by=['validite', 'date_de_fin'], ascending=[False, False])
    df = df.drop_duplicates(subset=['date_de_debut', 'code_site', 'polluant'], keep='first')
    df = df.drop_duplicates(keep='first')
    for col in date_columns:
        if col in df.columns:
            df[col] = df[col].dt.strftime('%Y/%m/%d %H:%M:%S')
    df.to_csv(csv, sep=";", index=False, encoding="utf-8")
    print(f"Fichier {csv} dédupliqué.")

def reorder_csv(csv):
    if not os.path.exists(csv):
        raise FileNotFoundError(f"Le fichier {csv} n'existe pas.")
    df = pd.read_csv(csv, sep=";", low_memory=False, encoding="utf-8")
    date_columns = ['date_de_debut', 'date_de_fin']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', format='%Y/%m/%d %H:%M:%S')
    required_columns = ["date_de_debut", "organisme", "code_zas", "zas", "code_site", "nom_site", "polluant"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes : {', '.join(missing)}")
    df = df.sort_values(by=required_columns, ascending=True)
    for col in date_columns:
        if col in df.columns:
            df[col] = df[col].dt.strftime('%Y/%m/%d %H:%M:%S')
    df.to_csv(csv, sep=";", index=False, encoding="utf-8")
    print(f"Fichier {csv} trié.")
 

def fetch_station(date = datetime.today()):
    """
    Récupère les informations à date des stations de mesure de pollution 
    - Crée un csv précisant la date de mise à jour de la base de donnée
    - Fournit les coordonnées GPS, commune et code de commune pour localiser les stations
    - Fournit diverses informations sur les conditions de recueil des concentrations de polluants

    Entrée
        date (datetype, optionnel): date de mise à jour sur l'API de la liste des stations de recueil de données. Defaults to datetime.today()
    
    Sortie
        Le fichier csv est mis à jour à la date 
    """
    gen_url = "https://www.geodair.fr/api-ext/station/export"  # URL de l'API pour les stations
    date_str = date.strftime("%Y-%m-%d")  # date du jour au format YYYY-MM-DD
    csv = "geodair_station.csv"  # nom du fichier csv à mettre à jour par remplacement

    # En-têtes de la requête
    headers = {
        "accept": "text/csv",  # Indiquer qu'on attend un fichier CSV
        "apikey": api_key
    }

    # Envoyer la requête
    response = requests.get(f"{gen_url}?date={date_str}", headers=headers)

    # Vérifier l'état de la requête
    if response.status_code == 200:
        print(f"Fichier téléchargé avec succès : {csv}")
        df = pd.read_csv(io.StringIO(response.text), sep=";", encoding="utf-8", low_memory=False)
        df = clean_header(df)
        df.to_csv(csv, sep=";", header=True, index=False, encoding="utf-8", lineterminator="\n")
        print(f"✅ Fichier station mis à jour : {csv}")
    else:
        print(f"❌ Erreur station : {response.status_code} - {response.reason}")
 

def merge_polluant_station(csv_polluant):
    df_polluant = pd.read_csv(csv_polluant, sep=";", low_memory=False, encoding="utf-8")
    csv_station = str(DATA_DIR / "geodair_station.csv")
    df_station = pd.read_csv(csv_station, sep=";", low_memory=False, encoding="utf-8")
    cols_to_add = ["code_commune", "commune", "longitude", "latitude", "code_departement", "departement"]
    df_station['code_departement'] = df_station['code_commune'].dropna().astype(str).str[:2]
    df_station['departement'] = df_station['code_departement'].map(departements).fillna("Inconnu")
    df_polluant.drop(columns=[col for col in cols_to_add if col in df_polluant.columns], inplace=True)
    df_merged = df_polluant.merge(
        df_station[['code'] + cols_to_add],
        left_on='code_site', right_on='code', how='left'
    ).drop(columns=['code'])
    df_merged.to_csv(csv_polluant, sep=";", header=True, index=False, encoding='utf-8', lineterminator="\n")
    print(f"✅ Données géographiques ajoutées à {csv_polluant}")

def fetch_max_yesterday(date=datetime.today() - timedelta(days=1)):
    gen_url = "https://www.geodair.fr/api-ext/MaxJH/export"
    dwl_url = "https://www.geodair.fr/api-ext/download"
    date_str = date.strftime("%Y-%m-%d")
    csv = str(DATA_DIR / "geodair_max_daily.csv")
 
    fetch_station()
    print(f"📅 Traitement données journalières : {date_str}")
 
    for i in range(len(polluants['code'])):
        code = polluants['code'][i]
        name = polluants['name'][i]
        headers = {"apikey": api_key}
        params = {"date": date_str, "polluant": code}
 
        print(f"  → Demande : {name}")
        response = requests.get(gen_url, headers=headers, params=params)
 
        if response.status_code == 200:
            file_id = response.text.strip()
            while True:
                download_response = requests.get(dwl_url, headers=headers, params={"id": file_id})
                if download_response.status_code == 200:
                    df = pd.read_csv(io.StringIO(download_response.text), sep=";", encoding="utf-8", low_memory=False)
                    df = clean_header(df)
                    df.to_csv(csv, sep=";", mode='a', header=not os.path.exists(csv), index=False, encoding='utf-8')
                    print(f"  ✅ {name} ajouté")
                    break
                elif download_response.status_code == 202:
                    print("     Fichier pas encore prêt, attente 5s...")
                    time.sleep(5)
                else:
                    print(f"  ❌ Erreur {name} : {download_response.status_code}")
                    break
        else:
            print(f"  ❌ Erreur génération {name} : {response.status_code}")
 
    merge_polluant_station(csv)
    deduplicate_csv(csv)
    reorder_csv(csv)
    update_iqa(csv)
    aggregate_weekly()
 
 
def aggregate_weekly():
    csv_daily = str(DATA_DIR / "geodair_max_daily.csv")
    csv_weekly = str(DATA_DIR / "geodair_max_weekly.csv")
 
    df = pd.read_csv(csv_daily, sep=";", parse_dates=['date_de_debut'], low_memory=False, encoding="utf-8")
    df['date_de_debut'] = pd.to_datetime(df['date_de_debut'], format="%Y/%m/%d %H:%M:%S")
    df['semaine'] = df['date_de_debut'].dt.strftime('%Y-S%U')
 
    groupby_cols = [
        "semaine", "organisme", "code_zas", "zas", "code_site", "nom_site",
        "type_d'implantation", "polluant", "type_d'influence", "discriminant",
        "reglementaire", "type_d'evaluation", "procedure_de_mesure", "type_de_valeur",
        "unite_de_mesure", "taux_de_saisie", "couverture_temporelle", "couverture_de_donnees",
        "code_qualite", "validite", "code_commune", "commune", "longitude", "latitude",
        "code_departement", "departement"
    ]
    # Ne garder que les colonnes qui existent
    groupby_cols = [c for c in groupby_cols if c in df.columns]
 
    df_weekly = df.groupby(groupby_cols, as_index=False).agg(max_week=('valeur', 'max'))
 
    if os.path.exists(csv_weekly):
        df_hist = pd.read_csv(csv_weekly, sep=";", low_memory=False, encoding="utf-8")
        df_final = pd.concat([df_hist, df_weekly], ignore_index=True)
        df_final = df_final.drop_duplicates(subset=["semaine", "code_site", "nom_site", "polluant"], keep='last')
    else:
        df_final = df_weekly
 
    df_final.to_csv(csv_weekly, sep=";", mode='w', header=True, index=False, encoding='utf-8', lineterminator="\n")
    print(f"✅ {csv_weekly} mis à jour.")
 
 
def update_iqa(csv_polluant=None):
    if csv_polluant is None:
        csv_polluant = str(DATA_DIR / "geodair_max_daily.csv")
 
    if not os.path.exists(csv_polluant):
        raise FileNotFoundError(f"Fichier introuvable : {csv_polluant}")
 
    if "daily" in csv_polluant:
        csv_iqa = csv_polluant.replace("max", "iqa")
    else:
        csv_iqa = csv_polluant.replace(".csv", "_iqa.csv")
 
    df = pd.read_csv(csv_polluant, sep=";", low_memory=False, encoding="utf-8")
    date_columns = ['date_de_debut', 'date_de_fin']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', format='%Y/%m/%d %H:%M:%S')
 
    df['valeur'] = pd.to_numeric(df['valeur'], errors='coerce')
    df = df.dropna(subset=['valeur'])
 
    IQA_THRESHOLDS = {
        "PM10":  [0, 20, 40, 50, 100, 150, 200],
        "PM2.5": [0, 10, 20, 25,  50,  75, 100],
        "NO2":   [0, 40, 90, 120, 230, 340, 400],
        "O3":    [0, 50, 100, 130, 240, 380, 500],
        "SO2":   [0, 50, 100, 150, 200, 300, 400],
    }
 
    def get_iqa(value, thresholds):
        for i in range(len(thresholds) - 1):
            if value <= thresholds[i + 1]:
                return i * 50
        return 300
 
    def get_gravite(iqa):
        if iqa <= 50:   return "Bon"
        elif iqa <= 100: return "Modéré"
        elif iqa <= 150: return "Mauvais"
        elif iqa <= 200: return "Très mauvais"
        elif iqa <= 300: return "Dangereux"
        return "Très dangereux"
 
    df_iqa = df.groupby(
        ['date_de_fin', 'code_departement']
    ).apply(lambda group: pd.Series({
        **{col: group[col].iloc[0] for col in group.columns if col not in ['polluant', 'valeur', 'unite_de_mesure']},
        'indice_qualite_air': 'IQA',
        'valeur': max(
            get_iqa(row['valeur'], IQA_THRESHOLDS.get(row['polluant'].upper(), [0, 50, 100, 150, 200, 300, 400]))
            for _, row in group.iterrows()
        ),
        'risque': get_gravite(max(
            get_iqa(row['valeur'], IQA_THRESHOLDS.get(row['polluant'].upper(), [0, 50, 100, 150, 200, 300, 400]))
            for _, row in group.iterrows()
        ))
    }), include_groups=False).reset_index(drop=True)
 
    for col in date_columns:
        if col in df_iqa.columns:
            df_iqa[col] = df_iqa[col].dt.strftime('%Y/%m/%d %H:%M:%S')
 
    df_iqa.to_csv(csv_iqa, sep=";", mode='w', header=True, index=False, encoding='utf-8', lineterminator="\n")
    print(f"✅ {csv_iqa} mis à jour.")
 
 
## Application ##
if __name__ == "__main__":
    fetch_max_yesterday()  # Exécuté quotidiennement par GitHub Actions
