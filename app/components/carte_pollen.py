import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import boto3
from io import StringIO
from dash import dcc, html
import dash_bootstrap_components as dbc

BUCKET_NAME = "bucket-asthme-scraping"
POLLEN_FILE_KEY = "pollen.csv"

def load_pollen_data_from_s3():
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=BUCKET_NAME, Key=POLLEN_FILE_KEY)
    return pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')))

def prepare_pollen_data(df):
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    df["date_str"] = df["date"].dt.strftime("%Y/%m/%d")
    df["Ville"] = df["Ville"].str.title()
    return df

def load_geojson():
    geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson"
    response = requests.get(geojson_url)
    return response.json() if response.status_code == 200 else None

def format_date_fr(dt):
    jours = {0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi", 4: "Vendredi", 5: "Samedi", 6: "Dimanche"}
    mois = {1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
            7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"}
    jour_str = "1er" if dt.day == 1 else str(dt.day)
    return f"{jours[dt.weekday()]} {jour_str} {mois[dt.month]}"

def geocode_city(city):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": f"{city}, France", "format": "json", "limit": 1}
    headers = {"User-Agent": "my-app"}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200 and response.json():
        result = response.json()[0]
        return float(result["lat"]), float(result["lon"])
    return None, None

def get_city_coordinates(city, geojson_data):
    if geojson_data is not None:
        for feature in geojson_data["features"]:
            if feature.get("properties", {}).get("nom", "").strip().lower() == city.strip().lower():
                geom = feature.get("geometry", {})
                coords = geom.get("coordinates", None)
                if coords:
                    if geom.get("type") == "Polygon":
                        ring = coords[0]
                    elif geom.get("type") == "MultiPolygon":
                        ring = coords[0][0]
                    else:
                        continue
                    return (sum(pt[1] for pt in ring) / len(ring),
                            sum(pt[0] for pt in ring) / len(ring))
    return geocode_city(city)

def classify_level(level):
    try:
        lvl = float(level)
        if lvl <= 0.1: return "nul"
        elif lvl <= 1.2: return "Risque faible"
        elif lvl < 3: return "Risque modéré"
        else: return "Risque élevé"
    except:
        return "non classé"

def create_map_card():
    df = load_pollen_data_from_s3()
    df = prepare_pollen_data(df)
    unique_dates = sorted(df["date_str"].dropna().unique())
    unique_pollens = sorted(df["Pollen"].dropna().unique())

    return dbc.Card([
        dbc.CardBody([
            html.H4("Carte des niveaux de pollen en France", className="text-center mb-3"),
            dbc.Row([
                dbc.Col(
                    dcc.Dropdown(
                        id="date-dropdown",
                        options=[{"label": d, "value": d} for d in unique_dates],
                        value=unique_dates[0] if unique_dates else None,
                        clearable=False
                    ),
                    width=5
                ),
                dbc.Col(
                    dcc.Dropdown(
                        id="pollen-dropdown",
                        options=[{"label": p, "value": p} for p in unique_pollens],
                        value=unique_pollens[0] if unique_pollens else None,
                        clearable=False
                    ),
                    width=5
                )
            ], justify="center", className="mb-3"),
            html.Div(id="info-div", className="text-center fs-5 mb-3"),
            dcc.Loading(
                id="loading-map",
                type="default",
                children=[dcc.Graph(id="map-graph", style={"height": "80vh"})]
            )
        ])
    ], className="shadow")
