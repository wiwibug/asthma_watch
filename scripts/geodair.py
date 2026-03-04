## Library ##
import requests
import time
import os
from datetime import datetime, timedelta
import pandas as pd
import io
import unidecode
import boto3

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

## Setting ##

# Clé API
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
    print("En-têtes nettoyés.")
    
    return df

def deduplicate_csv(csv):
    """
    Supprime les doublons dans un fichier csv en conservant :
    - En priorité, la ligne avec validite = 1
    - Sinon, la ligne avec la date_de_fin la plus récente
    - Si deux lignes sont strictement identiques, une seule est conservée.

    Entrée 
        csv (str) : chemin du fichier CSV à traiter
    Sortie
        Le fichier csv est mis à jour sans doublons.
    """
    if not os.path.exists(csv):
        raise FileNotFoundError(f"Le fichier {csv} n'existe pas.")

    # Charger le fichier CSV
    df = pd.read_csv(csv, sep=";", low_memory=False, encoding="utf-8")

    # Colonnes de date à convertir
    date_columns = ['date_de_debut', 'date_de_fin']

    # Convertir les colonnes de date en datetime
    for col in date_columns:
        if col in df.columns:
            # Gestion des formats de date multiples
            df[col] = pd.to_datetime(df[col], errors='coerce', format='%Y/%m/%d %H:%M:%S')

    # Vérifier si les colonnes nécessaires existent
    if 'validite' not in df.columns or 'date_de_fin' not in df.columns:
        raise ValueError("Les colonnes 'validite' ou 'date_de_fin' sont manquantes dans le fichier CSV.")

    # Tri prioritaire : validite = 1, puis date_de_fin la plus récente
    df = df.sort_values(by=['validite', 'date_de_fin'], ascending=[False, False])

    # Suppression des doublons sur les colonnes clés (date_de_debut, code_site, polluant)
    df = df.drop_duplicates(subset=['date_de_debut', 'code_site', 'polluant'], keep='first')

    # Suppression stricte des doublons restants (toutes colonnes identiques)
    df = df.drop_duplicates(keep='first')

    # Reconvertir les dates au format souhaité avant sauvegarde
    for col in date_columns:
        if col in df.columns:
            df[col] = df[col].dt.strftime('%Y/%m/%d %H:%M:%S')  # Format uniforme YYYY/MM/DD HH:MM:SS

    # Sauvegarde du fichier mis à jour
    df.to_csv(csv, sep=";", index=False, encoding="utf-8")
    print(f"Fichier {csv} dédupliqué.")

def reorder_csv(csv):
    """
    Trie un fichier csv :
    - Par date_de_debut (ordre chronologique)
    - Puis par organisme, code_zas, zas, code_site, nom_site et polluant (ordre alphabétique)

    Entrée 
        csv (str) chemin du fichier CSV à traiter
        
    Sortie 
        Le fichier csv est mis à jour et trié
    """
    if not os.path.exists(csv):
        raise FileNotFoundError(f"Le fichier {csv} n'existe pas.")

    # Charger le fichier CSV
    df = pd.read_csv(csv, sep=";", low_memory=False, encoding="utf-8")

    # Colonnes de date à convertir
    date_columns = ['date_de_debut', 'date_de_fin']

    # Convertir les colonnes de date en datetime
    for col in date_columns:
        if col in df.columns:
            # Gestion des formats de date multiples
            df[col] = pd.to_datetime(df[col], errors='coerce', format='%Y/%m/%d %H:%M:%S')

    # Vérification de la présence des colonnes nécessaires
    # Vérification de la présence des colonnes nécessaires
    required_columns = ["date_de_debut", "organisme", "code_zas", "zas", "code_site", "nom_site", "polluant"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Colonnes manquantes : {', '.join(missing_columns)}")

    # Tri du dataframe
    df = df.sort_values(by=required_columns, ascending=True)

    # Reconvertir les dates au format souhaité avant sauvegarde
    for col in date_columns:
        if col in df.columns:
            df[col] = df[col].dt.strftime('%Y/%m/%d %H:%M:%S')  # Format uniforme YYYY/MM/DD HH:MM:SS

    # Sauvegarde du fichier mis à jour
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
    else:
        print(f"Erreur lors de la génération du fichier : {response.status_code} - {response.reason} - {response.text}")

    return

def merge_polluant_station(csv_polluant):
    """
    Ajoute les informations géographiques aux fichiers de polluant horaire
    
    Entrée
        csv_polluant (str) chemin du fichier de polluant à compléter avec les données géographiques de la station
    
    Sortie
        Le fichier csv des polluants est mis à jour avec les informations géographiques des stations de prélévement
    """
    # Charger les fichiers csv
    df_polluant = pd.read_csv(csv_polluant, sep=";", low_memory=False, encoding="utf-8")
    csv_station = "geodair_station.csv"
    df_station = pd.read_csv(csv_station, sep=";", low_memory=False, encoding="utf-8")

    # Définir les colonnes à ajouter
    cols_to_add = ["code_commune", "commune", "longitude", "latitude", "code_departement", "departement"]

    # Ajouter une colonne 'code_departement' depuis les 2 premiers chiffres de 'code_commune'
    df_station['code_departement'] = df_station['code_commune'].dropna().astype(str).str[:2]
    
    # Ajouter une colonne 'departement' à partir du dictionnaire des départements
    df_station['departement'] = df_station['code_departement'].map(departements).fillna("Inconnu")

    # Supprimer les colonnes existantes dans df_polluant pour éviter les doublons
    df_polluant.drop(columns=[col for col in cols_to_add if col in df_polluant.columns], inplace=True)

    # Faire la jointure
    df_merged = df_polluant.merge(
        df_station[['code'] + cols_to_add], 
        left_on='code_site', 
        right_on='code', 
        how='left'
    ).drop(columns=['code'])  # Supprime la colonne 'code' dupliquée

    # Remplacer les valeurs manquantes par celles du dataframe joint
    for col in cols_to_add:
        if col in df_polluant.columns:
            df_merged[col] = df_polluant[col].fillna(df_merged[col])

    # Sauvegarder le fichier
    df_merged.to_csv(csv_polluant, sep=";", header=True, index=False, encoding='utf-8', lineterminator="\n")

    print(f"Fichier {csv_polluant} complété à partir de {csv_station}.")

    return

def fetch_hour_today(date=datetime.today()):
    """
    Récupère les valeurs horaires des polluants via l'API Geodair
    - Met à jour les données des stations de prélévements
    
    Entrée
        date (datetime, optionnel) date des données à récupérer (par défaut, aujourd’hui)
        
    Sortie
        Le fichier csv horaire des polluants est mise à jour par réécriture 
    """
    gen_url = "https://www.geodair.fr/api-ext/MoyH/export"  # URL de l'API pour les moyennes horaires par date et par polluant
    dwl_url = "https://www.geodair.fr/api-ext/download"  # URL de l'API pour le téléchargement des données
    date_str = date.strftime("%Y-%m-%d")  # mise au format nécessaire pour adresser la requête d'id
    csv = "geodair_hour.csv"  # nom du fichier csv à mettre à jour
    file_exists = False  # variable de différenciation de la boucle pour initialiser les en-têtes
    
    # Supprime le fichier précédent s'il existe
    if os.path.exists(csv):
        os.remove(csv)
        print(f"Fichier {csv} supprimé.")

    # Mise à jour des données liées aux stations
    fetch_station()
    
    print(f"Traitement des données horaires : {date_str}")
    for i in range(len(polluants['code'])):
        code = polluants['code'][i]
        name = polluants['name'][i]

        headers = {"apikey": api_key}
        params = {"date": date_str, "polluant": code}

        print(f"Demande de génération du fichier : {name}")
        response = requests.get(gen_url, headers=headers, params=params)  # paramétrage de l'accès à l'API

        if response.status_code == 200:
            file_id = response.text.strip()
            print(f"Génération du lien d'accès aux données : {name}")

            while True:
                download_response = requests.get(dwl_url, headers=headers, params={"id": file_id})
                if download_response.status_code == 200:
                    df = pd.read_csv(io.StringIO(download_response.text), sep=";", encoding="utf-8", low_memory=False)
                    df = clean_header(df)
                    print(f"Récupération des données : {name}")
                    # Ecrire dans le csv avec l'en-tête seulement pour la première itération
                    df.to_csv(csv, sep=';', mode='a', header=not file_exists, index=False, encoding='utf-8', lineterminator="\n")
                    # Mise à jour du flag après la première écriture
                    file_exists = True
                    print(f"Fichier {csv} complété pour {name}.")                        
                    break
                elif download_response.status_code == 202:
                    print("Le fichier n'est pas encore prêt. Nouvelle tentative dans 5 secondes...")
                    time.sleep(5)
                else:
                    print(f"Erreur lors de la récupération du fichier {name} : {download_response.status_code} - {download_response.reason} - {download_response.text}")
                    break
        else:
            print(f"Erreur lors de la génération du lien : {name} : {response.status_code} - {response.reason} - {download_response.text}")
    
    # Fusion avec données de localisation
    merge_polluant_station(csv)
    # Vérification des doublons
    deduplicate_csv(csv)
    # Ordonnement des données
    reorder_csv(csv)  
    # Calcul de l'IQA par site de prélévement
    update_iqa(csv) 
    
    return

def fetch_max_yesterday(date = datetime.today()-timedelta(days=1)):
    """Récupère le pic horaire de chaque polluant d'intérêt via l'API geodair
    - Ajoute les données à l'historique journalier

    Entrée
        date (datetime, optionnel) date de recueil des données à collecter (par défaut la veille) = datetime(year, month, day)
        
    Sortie
        Le fichier csv journalier des polluants est mis à jour par ajout de ligne de donnée
    """   
    gen_url = "https://www.geodair.fr/api-ext/MaxJH/export"  # URL de l'API pour valeurs moyennes horaire des polluants
    dwl_url = "https://www.geodair.fr/api-ext/download"  # URL de l'API pour le téléchargement des données
    date_str = date.strftime("%Y-%m-%d")  # date du jour au format YYYY-MM-DD
    csv = "geodair_max_daily.csv"  # nom du fichier de travail (pics d'enregistrement de polluant journalier à mettre à jour)

    # Mise à jour des données liées aux stations
    fetch_station()

    print(f"Traitement des données journalière : {date_str}")
    for i in range(len(polluants['code'])):
        code = polluants['code'][i]
        name = polluants['name'][i]

        headers = {"apikey": api_key}
        params = {"date": date_str, "polluant": code}

        print(f"Demande de génération du fichier : {name}")
        response = requests.get(gen_url, headers=headers, params=params)  # paramétrage de l'accès à l'API

        if response.status_code == 200:
            file_id = response.text.strip()
            print(f"Génération du lien d'accès aux données : {name}")

            while True:
                download_response = requests.get(dwl_url, headers=headers, params={"id": file_id})

                if download_response.status_code == 200:
                    df = pd.read_csv(io.StringIO(download_response.text), sep=";", encoding="utf-8", low_memory=False)
                    df = clean_header(df)                    
                    print(f"Récupération des données : {name}")   
                    df.to_csv(csv, sep=";", mode='a', header=not os.path.exists(csv), index=False, encoding='utf-8')
                    print(f"Fichier {csv} renseigné pour {name}.")
                    break
                elif download_response.status_code == 202:
                    print("Le fichier n'est pas encore prêt. Nouvelle tentative dans 5 secondes...")
                    time.sleep(5)
                else:
                    print(f"Erreur lors de la récupération du fichier {name} : {download_response.status_code} - {download_response.reason} - {download_response.text}")
                    break
        else:
            print(f"Erreur lors de la récupération du fichier {name} : {response.status_code} - {response.reason} - {response.text}")

    # Fusion avec données de localisation
    merge_polluant_station(csv)
    # Vérification des doublons
    deduplicate_csv(csv)
    # Ordonnement des données
    reorder_csv(csv)  
    # Calcul de l'IQA par site de prélévement
    update_iqa(csv)
    # Met à jour les données hebdomadaires
    aggregate_weekly()
    
    return

def aggregate_weekly():
    """
    Aggrège les valeurs journalières de la semaine passée en maximum hebdomadaire pour chaque site et chaque polluant
    - Ajoute les données à l'historique hebdomadaire au format csv
    
    Sortie
        Le fichier csv hedomadaire des polluants est mis à jour à partir du fichier csv journalier
    """
    csv_daily = "geodair_max_daily.csv"  # nom du fichier de travail (pics d'enregistrement de polluant journalier à aggréger)
    csv_weekly = "geodair_max_weekly.csv"  # nom du fichier de travail (pics d'enregistrement de polluant hebdomadaire à mettre à jour)
    df = pd.read_csv(csv_daily, sep=";", parse_dates=['date_de_debut'], low_memory=False, encoding="utf-8")  # chargement csv > dataFrame
    
    # Mettre au format la colonne 'date_de_debut' en datetime
    df['date_de_debut'] = pd.to_datetime(df['date_de_debut'], format="%Y/%m/%d %H:%M:%S")  

    # Ajouter la colonne 'semaine' au format année-semaine
    df['semaine'] = df['date_de_debut'].dt.strftime('%Y-S%U')

    # Définir les colonnes à conserver lors du regroupement
    groupby_cols = [
        "semaine", "organisme", "code_zas", "zas", "code_site", "nom_site",
        "type_d'implantation", "polluant", "type_d'influence", "discriminant",
        "reglementaire", "type_d'evaluation", "procedure_de_mesure", "type_de_valeur",
        "unite_de_mesure", "taux_de_saisie", "couverture_temporelle", "couverture_de_donnees",
        "code_qualite", "validite", "code_commune", "commune", "longitude", "latitude", "code_departement", "departement"
    ]

    # Agréger les données par semaine et par site avec la valeur maximale
    df_weekly = df.groupby(groupby_cols, as_index=False).agg(
        max_week=('valeur', 'max')
    )

    # Vérifier si l'historique hebdomadaire existe déjà
    if os.path.exists(csv_weekly):
        df_hist = pd.read_csv(csv_weekly, sep=";", low_memory=False, encoding="utf-8")
        # Concaténer et éviter les doublons
        df_final = pd.concat([df_hist, df_weekly], ignore_index=True)
        df_final = df_final.drop_duplicates(subset=["semaine", "code_site", "nom_site", "polluant"], keep='last')
    else:
        df_final = df_weekly

    # Réécriture de l'historique
    df_final.to_csv(csv_weekly, sep=";", mode='w', header=True, index=False, encoding='utf-8', lineterminator="\n")
    print(f"Fichier {csv_weekly} complété à partir de {csv_daily}.")

    return

def update_iqa(csv_polluant="geodair_max_daily.csv"):
    """
    Calcule l'IQA pour chaque couple date/site et génère un nouveau fichier CSV avec l'IQA ajouté.

    Entrée:
        csv_polluant (str): Chemin du fichier CSV à traiter (`geodair_hour.csv` ou `geodair_max_daily.csv` par défaut).

    Sortie:
        Un nouveau fichier CSV est créé avec une ligne par date/station pour l'IQA.
    """
    # Vérifier si le fichier existe
    if not os.path.exists(csv_polluant):
        raise FileNotFoundError(f"Le fichier {csv_polluant} n'existe pas.")

    # Déterminer le nom du fichier de sortie en fonction du fichier d'entrée
    if "daily" in csv_polluant:
        csv_iqa = csv_polluant.replace("max", "iqa")
    elif "weekly" in csv_polluant:
        csv_iqa = csv_polluant.replace("max", "iqa")
    else:
        csv_iqa = csv_polluant.replace(".csv", "_iqa.csv")

    # Charger le fichier CSV
    df = pd.read_csv(csv_polluant, sep=";", low_memory=False, encoding="utf-8")

    # Colonnes de date
    date_columns = ['date_de_debut', 'date_de_fin']

    # Convertir les colonnes de date en datetime pour traitement
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', format='%Y/%m/%d %H:%M:%S')

    # Convertir 'valeur' en float pour éviter les erreurs de calcul
    df['valeur'] = pd.to_numeric(df['valeur'], errors='coerce')
    df = df.dropna(subset=['valeur'])  # Supprimer les lignes où 'valeur' est NaN

    # Définition des seuils IQA pour chaque polluant
    IQA_THRESHOLDS = {
        "PM10": [0, 20, 40, 50, 100, 150, 200],
        "PM2.5": [0, 10, 20, 25, 50, 75, 100],
        "NO2": [0, 40, 90, 120, 230, 340, 400],
        "O3": [0, 50, 100, 130, 240, 380, 500],
        "SO2": [0, 50, 100, 150, 200, 300, 400],
    }

    # Fonction pour calculer l'IQA
    def get_iqa(value, thresholds):
        for i in range(len(thresholds) - 1):
            if value <= thresholds[i + 1]:
                return i * 50
        return 300

    # Fonction pour obtenir la gravité de l'IQA
    def get_gravite(iqa):
        if iqa <= 50:
            return "Bon"
        elif iqa <= 100:
            return "Modéré"
        elif iqa <= 150:
            return "Mauvais"
        elif iqa <= 200:
            return "Très mauvais"
        elif iqa <= 300:
            return "Dangereux"
        return "Très dangereux"

    # Calculer l'IQA pour chaque groupe de données
    df_iqa = df.groupby(
        ['date_de_fin', 'code_departement']
    ).apply(lambda group: pd.Series({
        **{col: group[col].iloc[0] for col in group.columns if col not in ['polluant', 'valeur', 'unite_de_mesure']},  # Conserver toutes les colonnes sauf polluant, valeur, unité
        'indice_qualite_air': 'IQA',
        'valeur': max(get_iqa(row['valeur'], IQA_THRESHOLDS.get(row['polluant'].upper(), [0, 50, 100, 150, 200, 300, 400]))
                      for _, row in group.iterrows()),
        'risque': get_gravite(max(get_iqa(row['valeur'], IQA_THRESHOLDS.get(row['polluant'].upper(), [0, 50, 100, 150, 200, 300, 400])) for _, row in group.iterrows())) 
    }), include_groups=False).reset_index(drop=True) 

    # Réintégration du format de date original
    for col in date_columns:
        if col in df_iqa.columns:
            df_iqa[col] = df_iqa[col].dt.strftime('%Y/%m/%d %H:%M:%S')

    # Sauvegarder le fichier mis à jour dans un nouveau fichier CSV
    df_iqa.to_csv(csv_iqa, sep=";", mode='w', header=True, index=False, encoding='utf-8', lineterminator="\n")
    print(f"Fichier {csv_iqa} complété à partir de {csv_polluant}.")
    
    return

def load_data_from_s3(BUCKET_NAME="bucket-asthme-scraping", FILE_KEY=None, file_type="csv", parse_dates=None):
    """Fonction pour charger les données depuis le serveur S3"""
    s3 = boto3.client('s3')
    
    if file_type == "csv":
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_KEY)
        df = pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')), sep=";", parse_dates=parse_dates)
    elif file_type == "excel":
        local_file = "/tmp/geodes_complet.xlsx"
        s3.download_file(BUCKET_NAME, FILE_KEY, local_file)
        df = pd.read_excel(local_file, engine="openpyxl")
    else:
        raise ValueError("Type de fichier non supporté. Utilisez 'csv' ou 'excel'.")
    
    return df

def get_max_daily_from_s3(csv = "geodair_max_daily.csv"):
    """Chargement des données"""
    df = load_data_from_s3(FILE_KEY=csv, file_type="csv", parse_dates=["date_de_debut", "date_de_fin"])
    df.to_csv(csv, sep=";", mode='w', header=not os.path.exists(csv), index=False, encoding='utf-8')
    
## Application ##

fetch_max_yesterday() #1/j à 12h

# Upload des fichiers générés vers AWS S3
files_to_upload = [
    "geodair_station.csv",
    "geodair_max_daily.csv",
    "geodair_max_weekly.csv",
    "geodair_iqa_daily.csv"
]

bucket_name = "bucket-asthme-scraping"

for local_file in files_to_upload:
    upload_to_s3(local_file, bucket_name, local_file)