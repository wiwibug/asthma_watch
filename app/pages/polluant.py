import dash
from dash import dcc, html
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import StringIO, BytesIO
import boto3
import dash_bootstrap_components as dbc

def load_data_from_s3_polluant(BUCKET_NAME="bucket-asthme-scraping", FILE_KEY=None, file_type="csv", parse_dates=None):
    """Fonction pour charger les données depuis le serveur S3"""
    s3 = boto3.client('s3')
    
    if file_type == "csv":
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_KEY)
        df = pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')), sep=";", parse_dates=parse_dates, low_memory=False)
    elif file_type == "excel":
        obj = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_KEY)
        df = pd.read_excel(BytesIO(obj['Body'].read()), engine="openpyxl")
    else:
        raise ValueError("Type de fichier non supporté. Utilisez 'csv' ou 'excel'.")
    
    return df

# --- Chargement des données ---
df_daily = load_data_from_s3_polluant(FILE_KEY="geodair_max_daily.csv", file_type="csv", parse_dates=["date_de_debut", "date_de_fin"])
df_weekly = load_data_from_s3_polluant(FILE_KEY="geodair_max_weekly.csv", file_type="csv")
df_indices = load_data_from_s3_polluant(FILE_KEY="geodes_complet.xlsx", file_type="excel")
df_iqa = load_data_from_s3_polluant(FILE_KEY="geodair_iqa_daily.csv", file_type="csv", parse_dates=["date_de_debut"])

# Renommage de la colonne pour uniformiser
df_indices.rename(columns={'Semaine': 'semaine'}, inplace=True)

# Nettoyage du format des semaines
df_weekly['semaine'] = df_weekly['semaine'].astype(str).str.replace(r'[^0-9]', '', regex=True).astype(int)
df_indices['semaine'] = df_indices['semaine'].astype(str).str.replace(r'[^0-9]', '', regex=True).astype(int)

# --- Fonction pour convertir une semaine en dates de début et de fin ---
def semaine_to_dates(semaine):
    annee = int(str(semaine)[:4])
    num_semaine = int(str(semaine)[4:])
    
    # Vérifier que le numéro de semaine est valide (1 à 53)
    if num_semaine < 1 or num_semaine > 53:
        raise ValueError(f"Numéro de semaine invalide : {num_semaine}")
    
    # Calculer la date de début de la semaine (lundi)
    date_debut = datetime.fromisocalendar(annee, num_semaine, 1)
    date_fin = date_debut + timedelta(days=6)  # Fin de semaine (dimanche)
    return date_debut, date_fin

# --- Détermination de la période par défaut ---
annee_en_cours = datetime.now().year
premiere_semaine_janvier = int(f"{annee_en_cours}01")  # Première semaine de janvier de l'année en cours
semaine_plus_recente = df_indices['semaine'].max()

# Créer une liste des semaines disponibles au format 'AAAA SX du jour jj/mm au jour jj/mm'
options_semaines = []
for semaine in sorted(df_indices['semaine'].unique()):
    try:
        date_debut, date_fin = semaine_to_dates(semaine)
        label = f"{str(semaine)[:4]} S{str(semaine)[4:]} du {date_debut.strftime('%d/%m')} au {date_fin.strftime('%d/%m')}"
        options_semaines.append({'label': label, 'value': semaine})
    except ValueError:
        continue  # Ignorer les semaines invalides

# --- Extraction des unités de mesure des polluants ---
unites_polluants = df_weekly[['polluant', 'unite_de_mesure']].drop_duplicates().set_index('polluant')['unite_de_mesure'].to_dict()

# --- Définition d'une palette de couleurs fixe pour les polluants ---
unique_polluants = sorted(df_weekly['polluant'].unique())
colors = px.colors.qualitative.Plotly  
color_map = {pollutant: colors[i % len(colors)] for i, pollutant in enumerate(unique_polluants)}

def create_intro_card():
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.I(className="fas fa-wind me-2", style={"fontSize": "2rem"}),
                html.H1("POLLUANTS ATMOSPHÉRIQUES ET ASTHME", 
                       className="intro-title text-center text-white mb-4")
            ], className="d-flex align-items-center justify-content-center"),
            
            html.Div([
                html.P(
                    """La pollution atmosphérique a un impact considérable sur l'asthme, en particulier en aggravant les symptômes et en réduisant le contrôle de la maladie. Les études montrent que les pics de pollution et l'exposition chronique à des niveaux élevés de polluants, tels que les particules fines et l'ozone, sont associés à une augmentation des crises d'asthme et des hospitalisations. Bien que la pollution soit clairement liée à l'aggravation de l'asthme préexistant, l'effet sur l'incidence de nouveaux cas et le risque de sensibilisation allergique nécessite encore des recherches supplémentaires, en particulier chez les jeunes enfants.""",
                    className="intro-text text-white mb-4"
                ),
                html.Div([
                    html.P([
                        "Source : ",
                        "Rochat, T., Bridevaux, P.-O., Gerbase, M., Probst-Hensch, N., & Künzli, N. (2012). ",
                        html.Em("Quel est le rôle de la pollution atmosphérique dans l'asthme ? "),
                        "Revue Médicale Suisse, 8(363), 2233. ",
                        html.A(
                            "DOI: 10.53738/REVMED.2012.8.363.2233",
                            href="https://doi.org/10.53738/REVMED.2012.8.363.2233",
                            className="text-white text-decoration-none",
                            target="_blank"
                        )
                    ], className="text-white-50 small fst-italic text-center")
                ], className="border-top pt-3")
            ], className="px-4")
        ]),
        className="intro-card mb-4 shadow-lg"
    )

def get_polluants_layout():
    return html.Div([
        dbc.Card(create_intro_card()),
        html.H1("Qualité de l'air et asthme", style={'textAlign': 'center'}),
        # Bloc des filtres
        html.Div([
            # Sélecteur de période
            html.Div([
                html.Label("Sélectionnez une période"),
                dcc.Dropdown(
                    id='dropdown-debut',
                    options=options_semaines,
                    value=premiere_semaine_janvier,
                    placeholder="Choisir la semaine de début",
                    style={'width': '100%'}
                ),
                dcc.Dropdown(
                    id='dropdown-fin',
                    options=options_semaines,
                    value=semaine_plus_recente,
                    placeholder="Choisir la semaine de fin",
                    style={'width': '100%'}
                )
            ], style={'width': '25%', 'padding': '0 10px'}),
            # Sélecteur de département
            html.Div([
                html.Label("Sélectionnez un département"),
                dcc.Dropdown(
                    id='dropdown-departement-nom',
                    options=[{'label': dep, 'value': dep} for dep in sorted(df_weekly['departement'].unique())],
                    placeholder="Choisir un département par son nom",
                    style={'width': '100%'}
                ),
                dcc.Dropdown(
                    id='dropdown-departement-code',
                    options=[{'label': code, 'value': code} for code in sorted(df_weekly['code_departement'].unique())],
                    placeholder="Choisir un département par son code",
                    style={'width': '100%'}
                )
            ], style={'width': '20%', 'padding': '0 10px'}),
            # Sélecteur de ville et site de prélèvement
            html.Div([
                html.Label("Sélectionnez une ville et un site de prélèvement"),
                dcc.Dropdown(
                    id='dropdown-commune',
                    options=[],
                    placeholder="Choisir une ville",
                    style={'width': '100%'}
                ),
                dcc.Dropdown(
                    id='dropdown-site',
                    options=[],
                    placeholder="Choisir un site de prélèvement",
                    style={'width': '100%'}
                )
            ], style={'width': '20%', 'padding': '0 10px'})
        ], style={
            'padding': '10px',
            'display': 'flex',
            'justify-content': 'center',
            'align-items': 'center',
            'gap': '10px'
        }),
        html.Div(id='periode-selectionnee', style={'margin-top': '10px', 'font-weight': 'bold', 'text-align': 'center'}),
        # Graphiques
        html.Div([
            html.Div([
                html.H2("Indice de diagnostique d'asthme pour 10.000 consultations aux urgences", style={'textAlign': 'center'}),
                dcc.Graph(id='graph-indices')
            ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
            html.Div([
                html.H2("Concentration hebdomadaire maximale de chaque polluant", style={'textAlign': 'center'}),
                dcc.Graph(id='graph-polluants')
            ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'})
        ], style={'display': 'flex', 'justify-content': 'center', 'padding': '20px'}),
        # Section pour le pic de pollution journalier
        html.Div([
            html.H2(id='titre-concentrations-journalieres', style={'textAlign': 'center', 'width': '100%'}),
            html.Div([
                html.Div([
                    html.Label("Sélectionnez une date"),
                    dcc.DatePickerSingle(
                        id='date-picker',
                        date=None,
                        display_format='DD/MM/YYYY',
                        style={'width': '100%'}
                    ),
                ], style={'margin-right': '20px'}),
                html.Div(id='output-graphs', style={'display': 'flex', 'flex-wrap': 'wrap', 'gap': '20px'})
            ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center', 'width': '100%', 'margin-top': '20px'})
        ], style={'padding': '20px', 'margin': '10px', 'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'})
    ])
