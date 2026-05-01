from flask import Flask, redirect, url_for
from .postgres_db import pgdb
from .views import registrar_rutas

def create_app():
    app = Flask(__name__)
   
    app.secret_key = '6164c3803ce91291b25c1484655ad0f35a956514be275e02eea09c28fc720417'  # Debe ser una cadena larga y aleatoria
    app.url_map.strict_slashes = False 
    registrar_rutas(app)
    return app

app = create_app()
pgdb.init_app(app)


if __name__ == "__main__":
    app.run(debug=True)


