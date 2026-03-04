from dash import html
import dash_bootstrap_components as dbc
from app.components.carte_pollen import create_map_card
from app.components.card_ import create_barplot_card


def create_pollen():
    return html.Div([
        # Première ligne : Card pleine largeur avec titre et texte
        dbc.Card(
            dbc.CardBody([
                html.H1("SECTION SUR LES POLLENS", className="intro-title text-center text-white mb-4"),
                html.P(
                    "Les pollens sont des déclencheurs majeurs des crises d'asthme chez les personnes sensibilisées. "
                    "Cette partie offre une vue d’ensemble sur le pollen et aide à mieux comprendre l’exposition à ce dernier "
                    "selon la localisation et la période.",
                    className="intro-text text-white text-center"
                )
            ]),
            className="intro-card mb-4"
        ),
        # Deuxième ligne : Deux colonnes
        dbc.Row([
            dbc.Col(create_map_card(), width=7),
            dbc.Col(create_barplot_card(), width=5)
        ], className="mb-4"),
        html.Div(id="info-pollen-div", className="text-center fs-5 mb-3")
    ], className="container-fluid py-4")