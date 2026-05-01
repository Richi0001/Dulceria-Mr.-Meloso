import pytest
from flask import url_for
from src.app_web.__init__ import create_app

# Fixture que crea la app de testing
@pytest.fixture
def app():
    test_app = create_app()
    test_app.config["TESTING"] = True
    # Se pueden configurar otros valores, por ejemplo SECRET_KEY, si se requiere
    return test_app

# Fixture que provee el test client
@pytest.fixture
def client(app):
    return app.test_client()

# --- Tests Unitarios ---

def test_create_app_blueprints(app):
    """
    Verifica que se registren los Blueprints 'auth_bp', 'productos_bp' y 'compras_bp'
    """
    bps = app.blueprints
    assert "auth_bp" in bps
    assert "productos_bp" in bps
    assert "compras_bp" in bps

def test_app_strict_slashes(app):
    """
    Verifica que strict_slashes esté configurado en False.
    """
    assert app.url_map.strict_slashes is False

# --- Tests de Sistema ---

def test_root_redirect(client, app):
    """
    Verifica que la ruta raíz ('/') redirija al endpoint 'auth_bp.login_cliente'.
    """
    # Con follow_redirects=False obtenemos la redirección
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    with app.test_request_context():
        expected = url_for("auth_bp.login_cliente")
    location = response.headers.get("Location")
    assert expected in location

def test_404_error_no_session(client, app):
    """
    Verifica que al acceder a una ruta inexistente sin 'cliente_id' en la sesión,
    se redirija al endpoint 'auth_bp.login_cliente' (mostrando el flash correspondiente).
    """
    response = client.get("/ruta_inexistente", follow_redirects=False)
    # Debido al error 404 se redirige a 'auth_bp.login_cliente'
    assert response.status_code == 302
    with app.test_request_context():
        expected = url_for("auth_bp.login_cliente")
    location = response.headers.get("Location")
    assert expected in location

def test_404_error_with_session(client, app):
    """
    Verifica que al acceder a una ruta inexistente con 'cliente_id' en la sesión,
    se redirija al endpoint 'compras_bp.inicio_home'.
    """
    # Establecer 'cliente_id' en la sesión
    with client.session_transaction() as sess:
        sess["cliente_id"] = 123
    response = client.get("/ruta_inexistente", follow_redirects=False)
    assert response.status_code == 302
    with app.test_request_context():
        expected = url_for("compras_bp.inicio_home")
    location = response.headers.get("Location")
    assert expected in location