import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd
from app.data_loader import load_data_from_s3_excel
import dash
from dash.dependencies import Input, Output
import plotly.express as px
from io import StringIO
import boto3

# Charger les données et préparer les calculs
def load_data():
    # Chargement 
    df = load_data_from_s3_excel()
    
    # Conversion en numérique à partir de la 4ème colonne
    df.iloc[:, 3:] = df.iloc[:, 3:].apply(pd.to_numeric, errors='coerce')
    
    # Extraire l'année depuis la colonne Semaine (ex: "2023-S14" -> 2023)
    df['Annee'] = df['Semaine'].str.split('-').str[0].astype(int)
    
    # Calculer les totaux annuels
    global total_par_annee
    total_par_annee = df.groupby("Annee").sum(numeric_only=True).sum(axis=1)
    
    # Calcul indice moyen (conservé de votre code original)
    df["mean_indice"] = df.iloc[:, 3:-1].mean(axis=1)  # -1 pour exclure la colonne Annee
    
    return df

df = load_data()
def create_mean_index_card():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H1("Indice moyen national", className="card-title"),
                dcc.Dropdown(
                    id='semaine-dropdown1',
                    options=[{'label': semaine, 'value': semaine} for semaine in df['Semaine']],
                    value=df['Semaine'].iloc[-1],
                    className="mb-3"
                ),
                html.H2(id='indice-moyen', className="display-4"),
                html.P("Taux de passages moyen pour asthme", className="card-text text-muted")
            ]
        ),
        className="mb-4 shadow"
    )

def create_classement_card(dropdown_options, default_week):
    """
    Crée et retourne une card pour afficher le classement interactif.
    """
    return dbc.Card(
        dbc.CardBody([
            html.H1("Classement des départements", style={"textAlign": "center"}),
            
            # Sélecteur de semaine
            html.Div([
                html.Label("Choisir une semaine :"),
                dcc.Dropdown(
                    id="semaine-dropdown2",
                    options=dropdown_options,
                    value=default_week,
                    clearable=False,
                    style={"width": "70%", "margin": "auto"}
                )
            ], style={"textAlign": "center", "marginBottom": "20px"}),
            
            # Boutons radio pour le choix du classement
            dcc.RadioItems(
                id="classement-radio",
                options=[
                    {"label": "Top 3 départements", "value": "top3"},
                    {"label": "Pires 3 départements", "value": "pires3"}
                ],
                value="pires3",
                inline=True,
                style={"textAlign": "center", "marginBottom": "20px"}
            ),
            
            # Zone de chargement qui contiendra le résultat
            dcc.Loading(
                id="loading-classement",
                type="default",
                children=[html.Div(id="classement-container", style={"textAlign": "center"})]
            )
        ]),
        className="mb-4 shadow"
    )

##### barplot_pollen --------------------------------------------

BUCKET_NAME = "bucket-asthme-scraping"
POLLEN_FILE_KEY = "pollen.csv"

color_map = {
    "Risque nul": "#008000",
    "Risque faible": "#FFFF00",
    "Risque modéré": "#FF8C00",
    "Risque élevé": "#FF0000",
    "non classé": "#CCCCCC"
}

def load_pollen_data_from_s3():
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=POLLEN_FILE_KEY)
    return pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')))

def classify_level(level):
    try:
        lvl = float(level)
        if lvl <= 0.1: return "Risque nul"
        elif lvl <= 1.2: return "Risque faible"
        elif lvl < 3: return "Risque modéré"
        else: return "Risque élevé"
    except:
        return "non classé"

def load_and_prepare_data():
    df = load_pollen_data_from_s3()
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    df["date_str"] = df["date"].dt.strftime("%Y/%m/%d")
    df["Ville"] = df["Ville"].str.title()
    df = df.sort_values(by="date", ascending=False)
    df["Niveau"] = df["level"].apply(classify_level)
    return df

def create_barplot_card():
    df = load_and_prepare_data()
    return dbc.Card([
        dbc.CardBody([
            html.H4("Niveaux de Pollen par Ville et Date", className="text-center mb-3"),
            dbc.Row([
                dbc.Col(
                    dcc.Dropdown(
                        id="ville-dropdown",
                        options=[{"label": ville, "value": ville} for ville in df["Ville"].unique()],
                        value=df["Ville"].unique()[0],
                        placeholder="Sélectionner une ville"
                    ),
                    className="mb-3"
                ),
                dbc.Col(
                    dcc.DatePickerSingle(
                        id="date-picker",
                        min_date_allowed=df["date"].min(),
                        max_date_allowed=df["date"].max(),
                        date=df["date"].max(),
                        display_format="DD/MM/YYYY",
                        month_format="MMMM YYYY",
                        first_day_of_week=1
                    ),
                    className="mb-3"
                )
            ]),
            html.Div(id="message", className="text-danger fs-5 my-3"),
            dcc.Graph(id="pollen-barplot")
        ])
    ], className="shadow")
