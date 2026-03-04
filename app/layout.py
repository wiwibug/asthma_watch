from dash import html
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from app.data_loader import load_data_from_s3_excel
from app.components.card_ import create_mean_index_card, create_classement_card
from app.components.carte_asthme import build_carte_urgences


# Chargement et préparation des données
df = load_data_from_s3_excel()
df_long = df.melt(id_vars=["Semaine", "Annee", "Mois"], var_name="Département", value_name="Passages")
df_long["Num_semaine_mois"] = df_long.groupby(["Annee", "Mois"]).cumcount() + 1
semaines_disponibles = sorted(df_long["Semaine"].unique())
# Générer les options pour le dropdown
dropdown_options = [{'label': semaine, 'value': semaine} for semaine in semaines_disponibles]
default_week = semaines_disponibles[-1] if semaines_disponibles else None

# Configuration de la carte
geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
intervalles_couleurs = [
    (0, 57, "#FFCCCB"), (58, 111, "#FF6666"),
    (112, 168, "#FF3333"), (169, 260, "#CC0000"),
    (261, float('inf'), "#800000")
]

def mapper_intervalle(passages):
    for debut, fin, _ in intervalles_couleurs:
        if debut <= passages <= fin:
            return f"{debut} à {fin}" if fin != float('inf') else "261 et plus"
    return "Non classé"

def create_sidebar():
    return html.Div(
        children=[
            html.Div(
                className="logo-container",
                children=[
                    html.Img(src="/assets/logo.png", className="logo"),
                    html.H1("Asthmawatch", className="logo-text")
                ]
            ),
            dbc.Nav(
                [
                    dbc.NavLink(
                        [html.I(className="fas fa-chart-bar"), "Asthme"],
                        href="/overview",
                        id="overview-link",
                        active="exact"
                    ),
                    dbc.NavLink(
                        [html.I(className="fas fa-map"), "Polluants"],
                        href="/polluants",
                        id="polluants-link",
                        active="exact" 
                    ),
                    dbc.NavLink(
                        [html.I(className="fas fa-hospital"), "Pollen"],
                        href="/pollen",
                        id="pollen-link",
                        active="exact" 
                    ),
                    dbc.NavLink(
                        [html.I(className="fas fa-info-circle"), "A Propos"],
                        href="/about",
                        id="about-link",
                        active="exact" 
                    ),
                ],
                vertical=True,
            ),
        ]
    )


def create_stat_card(title, value, subtitle, className=""):
    return dbc.Card(
        dbc.CardBody([
            html.H2(title, className="stat-card-title"),
            html.Div(value, className="stat-card-value"),
            html.P(subtitle, className="stat-card-subtitle")
        ]),
        className=f"stat-card {className}"
    )

def create_overview():
    return html.Div(
        dbc.Container(
            [
                # Première ligne (intro card)
                dbc.Row(
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody([
                                html.H1(
                                    "Vue globale des données sur l'Asthme en France",
                                    className="intro-title"
                                ),
                                html.P(
                                    "Ce dashboard offre une vue complète et interactive des données sur l'asthme en France. "
                                    "Grâce à des menus déroulants et des graphiques intuitifs, vous pouvez explorer les tendances "
                                    "annuelles et mensuelles ainsi que la répartition régionale. L'objectif est de fournir aux "
                                    "décideurs et aux professionnels de santé un outil puissant pour mieux comprendre et anticiper "
                                    "les besoins en matière de santé publique.",
                                    className="intro-text"
                                )
                            ]),
                            className="intro-card"
                        ),
                        width=12
                    ),
                    className="first-row mb-2"
                ),

                # Deuxième ligne avec deux colonnes
                dbc.Row([
                    dbc.Col(
                        create_mean_index_card(),
                        width=2,
                        className="pe-2"
                    ),
                    dbc.Col(
                        build_carte_urgences(),
                        width=10
                    )
                ], className="second-row g-0"),

                # Troisième ligne : une card pleine largeur
                dbc.Row(
                    dbc.Col(
                        create_classement_card(dropdown_options, default_week),
                        width=12
                    ),
                    className="third-row mt-2"
                )
            ],
            fluid=True,
            className="h-100 p-3"
        ),
        className="h-100"
    )

def create_layout():
    return html.Div(
        className="dashboard-container",
        children=[
            dcc.Location(id='url', pathname="/overview"),
            html.Div(create_sidebar(), className="container-left"),
            html.Div(id="page-content", className="container-right")
        ]
    )