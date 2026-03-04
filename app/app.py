from dash import Dash
import dash_bootstrap_components as dbc
from app.layout import create_layout
from app.callbacks import register_callbacks, register_callbacks_pol, register_barplot_callbacks

app = Dash(__name__, 
          external_stylesheets=[
              dbc.themes.BOOTSTRAP,
              "assets/styles.css",
          ], suppress_callback_exceptions=True
          )

app.layout = create_layout()
register_callbacks(app)
register_callbacks_pol(app)
register_barplot_callbacks(app)

server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)