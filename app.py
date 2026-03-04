import dash
from app.app import app as application  

server = application.server 

if __name__ == "__main__":
    application.run_server(debug=True)
