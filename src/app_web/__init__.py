from flask import Flask, redirect, url_for, flash, session
from .config import Config
from .routes import auth_bp, productos_bp, compras_bp
from .postgres_db import pgdb

def create_app():
    app = Flask(__name__)

    # Cargar configuración desde Config
    app.config.from_object(Config)

    # Configurar strict_slashes (comportamiento de barras finales en URL)
    app.url_map.strict_slashes = False

    # Inicializar la extensión de la base de datos con la aplicación Flask
    pgdb.init_app(app)

    # Registrar Blueprints para modularizar las rutas
    app.register_blueprint(auth_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(compras_bp)

    # Ruta raíz que redirige al login de cliente por defecto
####!!La razón es que esa línea nunca se ejecuta porque la función que la contiene está comentada en el código fuente. Es decir, el endpoint '/' que debería redirigir a auth_bp.login_cliente usando esa línea de código está deshabilitado (comentado), por lo que ningún test la alcanza. Para que un test la cubra, habría que habilitar (descomentar) esa ruta en el archivo fuente.
    @app.route('/')
    def root_redirect():
        return redirect(url_for('auth_bp.login_cliente'))  #ES AQUI PERRIN

    # Manejo de errores 404 (página no encontrada)
    @app.errorhandler(404)
    def page_not_found(e):
        flash("La página que buscas no existe o no tienes permiso para acceder.", "warning")
        if 'cliente_id' in session:
            return redirect(url_for('compras_bp.inicio_home'))
        return redirect(url_for('auth_bp.login_cliente'))

    return app