# run.py
import os
from src.app_web import create_app, pgdb # Importar pgdb también desde app/__init__.py para usarlo aquí

app = create_app()

if __name__ == '__main__':
    # Esto es solo para crear las tablas si no existen al iniciar la app
    # En producción, esto se haría con un script de migración de base de datos
    with app.app_context():
        pgdb.create_all_tables() 
        print("Base de datos y tablas inicializadas/verificadas.")

    app.run(debug=True, host='localhost', port=5000) # Opcional: configurar host y port