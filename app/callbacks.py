from dash import Input, Output, html, dcc
import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.layout import create_overview, df_long, intervalles_couleurs, mapper_intervalle, geojson_url
from app.pages.about import create_about
from app.pages.pollen import create_pollen
from app.data_loader import load_pollen_data_from_s3
from app.components.card_ import df, load_and_prepare_data, color_map
from app.components.carte_pollen import (
    load_pollen_data_from_s3, prepare_pollen_data, load_geojson,
    get_city_coordinates, classify_level, format_date_fr
)
from app.pages.polluant import (
    df_daily, df_weekly, df_indices, df_iqa, semaine_to_dates,
    unique_polluants, unites_polluants, color_map, get_polluants_layout
)

def register_callbacks(app):
    # Callback pour la navigation entre pages
    @app.callback(
        Output("page-content", "children"),
        [
            Input("overview-link", "n_clicks"),
            Input("polluants-link", "n_clicks"),
            Input("pollen-link", "n_clicks"),
            Input("about-link", "n_clicks")
        ]
    )
    def render_page_content(overview_clicks, polluant_clicks, pollen_clicks, about_clicks):
        ctx = dash.callback_context
        if not ctx.triggered:
            return create_overview()
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "overview-link":
            return create_overview()
        elif button_id == "polluants-link":
            return get_polluants_layout()  # Utilisation du nouveau layout
        elif button_id == "pollen-link":
            return create_pollen()
        elif button_id == "about-link":
            return create_about()
        return create_overview()

    # Callback pour mettre à jour les semaines en fonction de l'année et du mois (pour d'autres pages)
    @app.callback(
        [Output("semaine-dropdown", "options"),
         Output("semaine-dropdown", "value")],
        [Input("annee-dropdown", "value"),
         Input("mois-dropdown", "value")]
    )
    def update_semaines(annee, mois):
        semaines = df_long[
            (df_long["Annee"] == annee) & (df_long["Mois"] == mois)
        ]["Semaine"].unique()
        options = [
            {"label": f"Semaine {i+1}", "value": semaine}
            for i, semaine in enumerate(sorted(semaines))
        ]
        return options, options[-1]["value"] if options else None

    # Callback pour mettre à jour la carte choroplèthe
    @app.callback(
        Output("carte-urgence", "figure"),
        [Input("semaine-dropdown", "value")]
    )
    def update_map(semaine_selectionnee):
        df_filtered = df_long[df_long["Semaine"] == semaine_selectionnee].copy()
        df_filtered["Intervalle"] = df_filtered["Passages"].apply(mapper_intervalle)
        couleurs = [couleur for _, _, couleur in intervalles_couleurs]
        intervalle_labels = [
            f"{debut} à {fin}" if fin != float('inf') else "261 et plus"
            for debut, fin, _ in intervalles_couleurs
        ]
        fig = px.choropleth_mapbox(
            df_filtered,
            geojson=geojson_url,
            locations="Département",
            featureidkey="properties.nom",
            color="Intervalle",
            color_discrete_sequence=couleurs,
            category_orders={"Intervalle": intervalle_labels},
            mapbox_style="carto-positron",
            hover_name="Département",
            hover_data={"Passages": True, "Département": False},
            center={"lat": 46.603354, "lon": 2.333333},
            zoom=5.5,
            opacity=0.7
        )
        fig.update_traces(
            hovertemplate="<b>%{hovertext}</b><br>Passages pour 10 000 passages : %{customdata[0]}<extra></extra>"
        )
        fig.update_layout(
            mapbox_layers=[
                {
                    "below": "traces",
                    "sourcetype": "geojson",
                    "source": geojson_url,
                    "type": "line",
                    "color": "black",
                    "opacity": 0.5
                }
            ],
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            legend_title_text="Passages pour 10 000 passages"
        )
        return fig

    # Callback pour mettre à jour l'indice moyen (card)
    @app.callback(
        Output('indice-moyen', 'children'),
        [Input('semaine-dropdown1', 'value')]
    )
    def update_indice(selected_semaine):
        try:
            mean = df.loc[df['Semaine'] == selected_semaine, 'mean_indice'].values[0]
            return f"{mean:.2f}"
        except IndexError:
            return "N/A"

    # Callback pour la card de classement
    @app.callback(
        Output("classement-container", "children"),
        [Input("semaine-dropdown2", "value"),
         Input("classement-radio", "value")]
    )
    def update_classement(semaine_selectionnee, classement_type):
        df_filtered = df_long[df_long["Semaine"] == semaine_selectionnee].copy()
        df_filtered["Passages"] = pd.to_numeric(df_filtered["Passages"], errors="coerce")
        if classement_type == "pires3":
            df_classement = df_filtered.nlargest(3, "Passages")
            fig = px.bar(
                df_classement,
                x="Passages",
                y="Département",
                orientation="h",
                text="Passages",
                color_discrete_sequence=["#FF4444"],
                labels={"Passages": "Nombre de diagnostics d'asthme par 10 000 passages aux urgences"}
            )
            fig.update_layout(
                title_x=0.5,
                xaxis_range=[0, df_classement["Passages"].max() * 1.1],
                xaxis_showgrid=False,
                yaxis={"categoryorder": "total ascending"},
                plot_bgcolor="white",
                margin={"t": 40}
            )
            fig.update_traces(
                texttemplate="%{x:.0f}",
                textposition="outside",
                textfont_size=14
            )
            return html.Div([
                html.H3(
                    "Départements avec le plus de diagnostics d'asthme pour 10 000 passages aux urgences",
                    style={"textAlign": "center"}
                ),
                dcc.Graph(figure=fig)
            ])
        else:
            df_classement = df_filtered.nsmallest(3, "Passages")
            return html.Div([
                html.H3(
                    "Départements avec le moins de diagnostics d'asthme pour 10 000 passages aux urgences",
                    style={"textAlign": "center"}
                ),
                html.Ul([
                    html.Li(
                        f"{row['Département']}: {row['Passages']}",
                        style={
                            "color": "darkgreen",
                            "margin": "10px",
                            "padding": "15px",
                            "backgroundColor": "#e8f5e9",
                            "borderRadius": "10px",
                            "listStyle": "none",
                        }
                    ) for _, row in df_classement.iterrows()
                ])
            ])

    # Callback pour synchroniser les sélecteurs de département
    @app.callback(
        [Output('dropdown-departement-nom', 'value'),
         Output('dropdown-departement-code', 'value')],
        [Input('dropdown-departement-nom', 'value'),
         Input('dropdown-departement-code', 'value')]
    )
    def sync_departement(dropdown_nom_value, dropdown_code_value):
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id == 'dropdown-departement-nom':
            if dropdown_nom_value:
                code = df_daily[df_daily['departement'] == dropdown_nom_value]['code_departement'].iloc[0]
                return dropdown_nom_value, code
            else:
                return None, None
        elif trigger_id == 'dropdown-departement-code':
            if dropdown_code_value:
                nom = df_daily[df_daily['code_departement'] == dropdown_code_value]['departement'].iloc[0]
                return nom, dropdown_code_value
            else:
                return None, None
        else:
            return dash.no_update, dash.no_update

    # Callback pour synchroniser les sélecteurs de ville et de site de prélèvement
    @app.callback(
        [Output('dropdown-commune', 'options'),
         Output('dropdown-commune', 'value'),
         Output('dropdown-site', 'options'),
         Output('dropdown-site', 'value')],
        [Input('dropdown-departement-nom', 'value'),
         Input('dropdown-commune', 'value'),
         Input('dropdown-site', 'value')]
    )
    def sync_commune_and_site(departement, commune, site):
        if departement:
            communes = df_weekly[df_weekly['departement'] == departement]['commune'].unique()
            commune_options = [{'label': c, 'value': c} for c in sorted(communes)]
            if len(communes) >= 2:
                commune_options.append({'label': 'TOTAL', 'value': 'TOTAL'})
            if not commune:
                commune_value = 'TOTAL' if len(communes) >= 2 else (communes[0] if len(communes)==1 else None)
            else:
                commune_value = commune
        else:
            commune_options = []
            commune_value = None

        if commune and commune != 'TOTAL':
            sites = df_weekly[df_weekly['commune'] == commune]['nom_site'].unique()
            site_options = [{'label': s, 'value': s} for s in sorted(sites)]
            if len(sites) >= 2:
                site_options.append({'label': 'TOTAL', 'value': 'TOTAL'})
            if not site:
                site_value = 'TOTAL' if len(sites) >= 2 else (sites[0] if len(sites)==1 else None)
            else:
                site_value = site
        else:
            site_options = []
            site_value = None

        return commune_options, commune_value, site_options, site_value

    # Callback pour afficher la période sélectionnée
    @app.callback(
        Output('periode-selectionnee', 'children'),
        [Input('dropdown-debut', 'value'),
         Input('dropdown-fin', 'value')]
    )
    def update_periode_selectionnee(semaine_debut, semaine_fin):
        try:
            date_debut, _ = semaine_to_dates(semaine_debut)
            _, date_fin = semaine_to_dates(semaine_fin)
            return f"Période du {date_debut.strftime('%d/%m/%y')} au {date_fin.strftime('%d/%m/%y')}"
        except ValueError as e:
            return f"Erreur : {str(e)}"

    # Callback pour mettre à jour le graphique des indices d'asthme
    @app.callback(
        Output('graph-indices', 'figure'),
        [Input('dropdown-departement-nom', 'value'),
         Input('dropdown-debut', 'value'),
         Input('dropdown-fin', 'value')]
    )
    def update_indices(departement, semaine_debut, semaine_fin):
        if not departement:
            return px.line(title="Veuillez sélectionner un département.")
        df_filtered = df_indices.copy()
        df_filtered = df_filtered[(df_filtered['semaine'] >= semaine_debut) &
                                  (df_filtered['semaine'] <= semaine_fin)]
        if df_filtered.empty:
            return px.line(title="Aucune donnée disponible pour les filtres sélectionnés")
        df_filtered['semaine_format'] = df_filtered['semaine'].apply(
            lambda x: f"{str(x)[:4]} S{str(x)[4:]}"
        )
        if departement not in df_filtered.columns:
            return px.line(title=f"Le département '{departement}' n'est pas présent dans les données.")
        fig = px.line(
            df_filtered,
            x='semaine_format',
            y=departement,
            markers=True,
        )
        fig.update_traces(hovertemplate=f"{departement}<br>Indice %{{y}}")
        fig.update_layout(
            xaxis_title="Semaine",
            yaxis_title="Indice",
            xaxis=dict(type='category', tickangle=-45),
            hovermode="x unified",
            title_x=0.5
        )
        return fig

    # Callback pour mettre à jour le graphique des polluants
    @app.callback(
        Output('graph-polluants', 'figure'),
        [Input('dropdown-departement-nom', 'value'),
         Input('dropdown-debut', 'value'),
         Input('dropdown-fin', 'value')]
    )
    def update_pollutants(departement, semaine_debut, semaine_fin):
        if not departement:
            return px.line(title="Veuillez sélectionner un département.")
        df_filtered = df_weekly[df_weekly['departement'] == departement]
        df_filtered = df_filtered[(df_filtered['semaine'] >= semaine_debut) &
                                  (df_filtered['semaine'] <= semaine_fin)]
        if df_filtered.empty:
            return px.line(title="Aucune donnée disponible pour les filtres sélectionnés")
        df_grouped = df_filtered.groupby(['semaine', 'polluant'], as_index=False)['max_week'].max()
        df_grouped['semaine_format'] = df_grouped['semaine'].apply(
            lambda x: f"{str(x)[:4]} S{str(x)[4:]}"
        )
        df_grouped['polluant_avec_unite'] = df_grouped['polluant'].apply(
            lambda x: f"{x} ({unites_polluants[x]})"
        )
        fig = px.line(
            df_grouped,
            x="semaine_format",
            y="max_week",
            color="polluant_avec_unite",
            color_discrete_map=color_map,
            markers=True,
            line_shape='linear',
        )
        fig.update_traces(hovertemplate="<br>Concentration = %{y}<br>")
        fig.update_layout(
            xaxis_title="Semaine",
            yaxis_title="Concentration",
            xaxis=dict(type='category', tickangle=-45),
            legend_title=None,
            hovermode="x unified",
            title_x=0.5
        )
        return fig

    # Callback pour mettre à jour les concentrations journalières (avec données IQA)
    @app.callback(
        [Output('titre-concentrations-journalieres', 'children'),
         Output('output-graphs', 'children')],
        [Input('dropdown-departement-nom', 'value'),
         Input('date-picker', 'date')]
    )
    def update_concentrations(departement, selected_date):
        if not departement or not selected_date:
            return "Pic de pollution journalier", html.Div("Sélectionnez un département et une date.", style={"color": "red", "text-align": "center"})
        selected_date = pd.to_datetime(selected_date)
        titre = f"Pic de pollution journalier du {selected_date.strftime('%d/%m/%Y')}"
        df_filtered_day = df_daily[
            (df_daily['departement'] == departement) &
            (df_daily['date_de_debut'] == selected_date)
        ]
        df_filtered_iqa = df_iqa[
            (df_iqa['departement'] == departement) &
            (df_iqa['date_de_debut'] == selected_date)
        ]
        if df_filtered_day.empty and df_filtered_iqa.empty:
            return titre, html.Div("Aucune donnée disponible pour les filtres sélectionnés.", style={"color": "red", "text-align": "center"})
        cards = []
        # Carte pour l'IQA
        if not df_filtered_iqa.empty:
            iqa_value = df_filtered_iqa['valeur'].iloc[0]
            iqa_gravite = df_filtered_iqa['risque'].iloc[0]
            iqa_card = html.Div([
                html.H3("IQA", style={'text-align': 'center'}),
                html.P(f"{iqa_value}", style={'text-align': 'center'}),
                html.P(f"{iqa_gravite}", style={'text-align': 'center'}),
            ], style={"border": "1px solid black", "border-radius": "10px", "padding": "10px", "width": "200px", "text-align": "center"})
            cards.append(iqa_card)
        # Cartes pour les polluants
        for pollutant in unique_polluants:
            value_day = df_filtered_day[df_filtered_day['polluant'] == pollutant]['valeur'].max()
            unite = unites_polluants.get(pollutant, "N/A")
            card = html.Div([
                html.H3(f"{pollutant}", style={'text-align': 'center'}),
                html.P(f"{value_day:.2f} {unite}" if pd.notna(value_day) else "Données non disponibles", style={'text-align': 'center'}),
            ], style={"border": "1px solid black", "border-radius": "10px", "padding": "10px", "width": "200px", "text-align": "center"})
            cards.append(card)
        return titre, html.Div(cards, style={"display": "flex", "justify-content": "center", "flex-wrap": "wrap", "gap": "20px"})

def register_callbacks_pol(app):
    @app.callback(
        [Output("map-graph", "figure"), Output("info-div", "children")],
        [Input("date-dropdown", "value"), Input("pollen-dropdown", "value")]
    )
    def update_map_pol(selected_date, selected_pollen):
        if not selected_date or not selected_pollen:
            return {}, "Veuillez sélectionner une date et un type de pollen."
        df = load_pollen_data_from_s3()
        df = prepare_pollen_data(df)
        geojson_data = load_geojson()
        dff = df[(df["date_str"] == selected_date) & (df["Pollen"] == selected_pollen)]
        if dff.empty:
            fig = px.scatter_mapbox(lat=[46.5], lon=[2.5], zoom=5, height=600)
            fig.update_layout(
                mapbox=dict(style="open-street-map"),
                margin={"r": 0, "t": 50, "l": 0, "b": 0}
            )
            dt = pd.to_datetime(selected_date, format="%Y/%m/%d")
            return fig, f"Aucune donnée pour {format_date_fr(dt)} et pollen {selected_pollen}."
        dff_grouped = dff.groupby(["Ville", "Pollen"], as_index=False).agg({"level": "mean"})
        dff_grouped["Niveaux de risque"] = dff_grouped["level"].apply(classify_level)
        coords_dict = {}
        for city, group in dff_grouped.groupby("Ville"):
            if city not in coords_dict:
                coords_dict[city] = get_city_coordinates(city, geojson_data)
            base_lat, base_lon = coords_dict[city] if coords_dict[city][0] else (46.5, 2.5)
            n = len(group)
            for idx, (i, row) in enumerate(group.iterrows()):
                offset = 0.005 * (idx - (n - 1) / 2)
                dff_grouped.at[i, "lat"] = base_lat + offset
                dff_grouped.at[i, "lon"] = base_lon + offset
        color_map_local = {
            "nul": "#008000",
            "Risque faible": "#FFFF00",
            "Risque modéré": "#FF8C00",
            "Risque élevé": "#FF0000",
            "non classé": "#CCCCCC"
        }
        fig = px.scatter_mapbox(
            dff_grouped,
            lat="lat",
            lon="lon",
            color="Niveaux de risque",
            color_discrete_map=color_map_local,
            size_max=15,
            zoom=5,
            hover_name="Ville",
            hover_data={'lat': False, 'lon': False, "Niveaux de risque": False},
            category_orders={"Niveaux de risque": ["nul", "Risque faible", "Risque modéré", "Risque élevé", "non classé"]}
        )
        fig.update_traces(marker=dict(size=20))
        expected_categories = ["nul", "Risque faible", "Risque modéré", "Risque élevé"]
        present_categories = dff_grouped["Niveaux de risque"].unique().tolist()
        for cat in expected_categories:
            if cat not in present_categories:
                fig.add_trace(
                    go.Scattermapbox(
                        lat=[None],
                        lon=[None],
                        mode="markers",
                        marker=dict(size=20, color=color_map_local[cat]),
                        name=cat,
                        showlegend=True,
                        hoverinfo="none"
                    )
                )
        first_city = dff_grouped["Ville"].iloc[0]
        center_lat, center_lon = coords_dict.get(first_city, (46.5, 2.5))
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center={"lat": center_lat, "lon": center_lon}
            ),
            margin={"r": 0, "t": 50, "l": 0, "b": 0}
        )
        dt = pd.to_datetime(selected_date, format="%Y/%m/%d")
        info_text = f"Date sélectionnée : {format_date_fr(dt)} | Pollen : {selected_pollen}"
        return fig, info_text

def register_barplot_callbacks(app):
    df = load_and_prepare_data()
    @app.callback(
        [Output("pollen-barplot", "figure"), Output("message", "children")],
        [Input("ville-dropdown", "value"), Input("date-picker", "date")]
    )
    def update_barplot(selected_ville, selected_date):
        filtered_df = df[(df["Ville"] == selected_ville) & (df["date"] == selected_date)]
        if filtered_df.empty:
            return (
                px.bar(title="", labels={"Pollen": "Type de Pollen", "level": "Niveau"}),
                f"Aucune donnée disponible pour {selected_ville} le {selected_date}."
            )
        filtered_df = filtered_df.sort_values(by="level", ascending=True)
        fig = px.bar(
            filtered_df,
            x="level",
            y="Pollen",
            orientation="h",
            color="Niveau",
            color_discrete_map=color_map,
            labels={"level": "Niveau", "Pollen": "Type de Pollen"},
            title=f"Niveau de pollen à {selected_ville}"
        )
        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis=dict(range=[0, 3])
        )
        return fig, ""
