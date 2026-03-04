import pandas as pd
import plotly.express as px
from dash import html, dcc
import dash_bootstrap_components as dbc
from app.data_loader import load_data_from_s3_excel

def build_carte_urgences():
    # Chargement et préparation des données
    df = load_data_from_s3_excel()
    df_long = df.melt(id_vars=["Semaine", "Annee", "Mois"], var_name="Département", value_name="Passages")
    df_long["Num_semaine_mois"] = df_long.groupby(["Annee", "Mois"]).cumcount() + 1
    
    # Création des listes pour les dropdowns
    annees_disponibles = sorted(df_long["Annee"].unique(), reverse=True)
    mois_disponibles = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    derniere_annee = annees_disponibles[0]
    dernier_mois = df_long[df_long["Annee"] == derniere_annee]["Mois"].iloc[-1]

    return dbc.Card(
        dbc.CardBody([
            html.H1("Carte des taux de passage aux urgences pour asthme",
                   style={"textAlign": "center", "fontSize": "24px"}),
            html.Div([
                html.Div([
                    html.Label("Année"),
                    dcc.Dropdown(
                        id="annee-dropdown",
                        options=[{"label": str(annee), "value": annee} for annee in annees_disponibles],
                        value=derniere_annee,
                        clearable=False,
                        style={"width": "100%"}
                    )
                ], style={"width": "30%", "display": "inline-block", "marginRight": "2%"}),
                html.Div([
                    html.Label("Mois"),
                    dcc.Dropdown(
                        id="mois-dropdown",
                        options=[{"label": mois, "value": mois} for mois in mois_disponibles],
                        value=dernier_mois,
                        clearable=False,
                        style={"width": "100%"}
                    )
                ], style={"width": "30%", "display": "inline-block", "marginRight": "2%"}),
                html.Div([
                    html.Label("Semaine du mois"),
                    dcc.Dropdown(
                        id="semaine-dropdown",
                        clearable=False,
                        style={"width": "100%"}
                    )
                ], style={"width": "30%", "display": "inline-block"})
            ], style={"width": "80%", "margin": "20px auto"}),
            dcc.Graph(id="carte-urgence", style={"height": "70vh", "marginTop": "10px"})
        ]),
        className="h-100"
    )