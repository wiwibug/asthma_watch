from dash import html
import dash_bootstrap_components as dbc

def create_about():
    return html.Div([
        # Section About
        dbc.Card(
            dbc.CardBody([
                html.H1("À PROPOS DE ASTHMAWATCH", className="intro-title text-center text-white mb-4"),
                html.P([
                    "👋 Bienvenue sur le dashboard ", 
                    html.Span("Asthmawatch", style={"fontWeight": "600"}),
                    " !"
                ], className="intro-text text-white mb-4"),
                html.P(
                    "Ce dashboard est un outil qui présente la prévalence et les tendances de l'asthme ainsi que "
                    "l'utilisation des services de santé associés au niveau départemental en France. Il intègre "
                    "également des données sur la qualité de l'air et les niveaux de pollens. Notre équipe a développé "
                    "cette ressource pour fournir aux chercheurs, décideurs et journalistes un outil pour mieux comprendre "
                    "les enjeux de santé publique.",
                    className="intro-text text-white mb-4"
                ),
                html.Ul([
                    html.Li("Suivre la prévalence et comparer les tendances de l'asthme par région", className="intro-text text-white"),
                    html.Li("Comparer la distribution géographique des passages aux urgences", className="intro-text text-white"),
                    html.Li("Observer l'influence des pollens sur les crises d'asthme", className="intro-text text-white")
                ], className="mb-4", style={"textAlign": "left"}),
                html.P(
                    "Le dashboard permet principalement de suivre les tendances des passages aux urgences pour asthme. "
                    "Cette mesure standardisée permet de comparer le volume de cas entre différentes populations. "
                    "Les utilisateurs peuvent filtrer les données par département et période temporelle.",
                    className="intro-text text-white"
                )
            ]),
            className="intro-card mb-4"
        ),
        
        # Section Sources
        dbc.Card(
            dbc.CardBody([
                html.H2("SOURCES DES DONNÉES", className="intro-title text-center mb-4", style={"color": "#1d2951"}),
                html.P(
                    "Les données utilisées dans ce dashboard proviennent de plusieurs sources officielles :",
                    className="intro-text mb-4"
                ),
                html.Ul([
                    html.Li([
                        html.Strong("Géodes Santé Publique France : "), 
                        "Extraction des données depuis le site ", 
                        html.A("Géodes Santé Publique France", href="https://geodes.santepubliquefrance.fr/", target="_blank"),
                        ". Ce site est une plateforme interactive qui permet d'explorer des indicateurs de santé publique sous forme de cartes, tableaux et graphiques."
                    ], className="intro-text"),
                    html.Li([
                        html.Strong("GeodAir : "), 
                        "Données sur la qualité de l'air issues de ", 
                        html.A("GeodAir", href="https://www.geodair.fr/", target="_blank"),
                        ", la plateforme nationale de surveillance de la qualité de l'air."
                    ], className="intro-text"),
                    html.Li([
                        html.Strong("pollens.fr : "), 
                        "Consultation des niveaux de pollens sur le site ", 
                        html.A("pollens.fr", href="https://www.pollens.fr/", target="_blank")
                    ], className="intro-text")
                ], className="mb-4", style={"textAlign": "left"}),
                html.P(
                    "Note : Les données sont mises à jour périodiquement selon la disponibilité des sources.",
                    className="intro-text fst-italic"
                )
            ]),
            className="bg-white mb-4 rounded-3"
        ),
        
        # Section Contact
        dbc.Card(
            dbc.CardBody([
                html.H2("CONTACTEZ-NOUS", className="intro-title text-center mb-4", style={"color": "#1d2951"}),
                html.P(
                    "Ce projet académique est réalisé dans le cadre du Master Data Science en Santé à l'Université de Lille, département UFR3S - ILIS par Abdou DOSSOU, Belkis ABDELATIF, Dylan PIN, Hiba AZZOUZI et Saad OMAR ABDILLAHI",
                    className="intro-text text-center mb-4"
                ),
                html.Div([
                    html.P([
                        html.Span("GitLab : ", style={"fontWeight": "600"}),
                        html.A("Voir le projet", href="https://gitlab.com/Abd2k27/asthme-dashboard", target="_blank")
                    ], className="intro-text text-center")
                ], style={"marginTop": "20px"})
            ]),
            className="bg-white rounded-3"
        )
    ], className="container-fluid py-4")