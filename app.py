import dash
from app.app import app as application  # Renommer pour éviter les conflits

server = application.server  # 👈 LIGNE OBLIGATOIRE pour Plotly Cloud

if __name__ == "__main__":
    application.run_server(debug=True)
