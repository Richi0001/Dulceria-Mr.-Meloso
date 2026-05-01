import pytest
from flask import url_for
from src.app_web.sistema import create_app

@pytest.fixture
def test_client():
    test_app = create_app()
    test_app.config["TESTING"] = True
    with test_app.test_client() as client:
        yield client

# --- Tests Unitarios ---

def test_create_app_config():
    test_app = create_app()
    assert test_app is not None
    expected_secret = '6164c3803ce91291b25c1484655ad0f35a956514be275e02eea09c28fc720417'
    assert test_app.secret_key == expected_secret
    assert test_app.url_map.strict_slashes is False

def test_app_url_map():
    test_app = create_app()
    rules = list(test_app.url_map.iter_rules())
    assert len(rules) > 0

# --- Tests de Sistema ---

def test_home_route(test_client):
    """
    Verifica que la ruta '/' redirija (302) a la ruta de login, 
    y que la cabecera Location contenga '/login_cliente'.
    """
    response = test_client.get("/", follow_redirects=False)
    # Ahora esperamos el 302 (redirección) en lugar de 404.
    assert response.status_code == 302
    location = response.headers.get("Location", "")
    assert "/login_cliente" in location

#NO SRVE, NO CAMBIA LA EJECUCION HAY Q BORRAR
# def test_login_cliente_route(test_client):
#     """
#     Verifica que al acceder a '/login_cliente' se obtenga 200 o 302.
#     Se evita el uso de url_for ya que se produjo BuildError.
#     """
#     response = test_client.get("/login_cliente")
#     assert response.status_code in [200, 302]