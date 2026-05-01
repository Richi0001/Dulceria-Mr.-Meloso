# def test_login_cliente_get(client):
#     response = client.get('/login_cliente')
#     assert response.status_code == 200
#     assert b"<form" in response.data

import pytest
import os
from decimal import Decimal
from flask import Flask, session
from src.app_web.views import registrar_rutas
from src.app_web.models import Cliente, Producto, compra, Detallecompra, AltaProductoException, AltaProductoPrecioException, DBException

# --- Definición de objetos dummy para simular la lógica de negocio ---

class FakeCursor:
    def __init__(self, fetchone_return=(1,)):
        self.queries = []
        self.fetchone_return = fetchone_return

    def execute(self, query, params=None):
        self.queries.append(query)

    def fetchone(self):
        return self.fetchone_return

    def fetchall(self):
        return []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        pass

class DummyCliente:
    def __init__(self, id=1, nombre="Test Cliente"):
        self.id = id
        self.nombre = nombre
        self.email = "test@example.com"

    @classmethod
    def crear(cls, nombre, email, telefono, direccion, password):
        if email == "error@test.com":
            raise ValueError("Error de validación")
        return cls()

    @classmethod
    def autenticar(cls, email, password):
        if email == "error@test.com":
            return None
        return cls()

class DummyProducto:
    def __init__(self, id=1, descripcion="Dummy Producto", precio=100, stock=10, activo=True):
        self.id = id
        self.descripcion = descripcion
        self.precio = precio
        self.stock = stock
        self.activo = activo

    @classmethod
    def consultar_todo(cls):
        return [
            cls(),
            cls(id=2, descripcion="Prod2", precio=50, stock=5, activo=True)
        ]

    @classmethod
    def consultar_id(cls, id):
        if id == 999:
            return None
        return cls()

    def reducir_stock(self, cantidad):
        if self.stock < cantidad:
            raise ValueError("No hay suficiente stock")
        self.stock -= cantidad
        return True

    def actualizar(self):
        if self.precio <= 0:
            raise AltaProductoPrecioException("Precio inválido")
        return 1

class DummyCompra:
    def __init__(self, cliente_id=1, subtotal=100, descuento=0, total=100, metodo_pago="efectivo", id=1):
        self.id = id
        self.cliente_id = cliente_id
        self.subtotal = subtotal
        self.descuento = descuento
        self.total = total
        self.metodo_pago = metodo_pago

    def insertar(self):
        return self.id

    @classmethod
    def consultar_por_id(cls, id):
        if id == 999:
            return None
        return cls()

    @classmethod
    def consultar_por_cliente(cls, cliente_id):
        return [cls(cliente_id=cliente_id)]

class DummyDetalleCompra:
    def __init__(self, compra_id, producto_id, cantidad, precio_unitario):
        self.compra_id = compra_id
        self.producto_id = producto_id
        self.cantidad = cantidad
        self.precio_unitario = precio_unitario

    def insertar(self):
        return True

    @classmethod
    def consultar_por_compra(cls, compra_id):
        return [cls(compra_id, 1, 2, 100)]
    
# --- Fixtures para la app y el cliente de pruebas ---

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.secret_key = 'test_secret'
    app.template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'app_web', 'templates'))
    registrar_rutas(app)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def override_models(monkeypatch):
    monkeypatch.setattr(Cliente, "crear", DummyCliente.crear)
    monkeypatch.setattr(Cliente, "autenticar", DummyCliente.autenticar)
    monkeypatch.setattr(Producto, "consultar_todo", DummyProducto.consultar_todo)
    monkeypatch.setattr(Producto, "consultar_id", DummyProducto.consultar_id)
    monkeypatch.setattr(Producto, "reducir_stock", DummyProducto.reducir_stock)
    monkeypatch.setattr(Producto, "actualizar", DummyProducto.actualizar)
    monkeypatch.setattr(compra, "consultar_por_id", DummyCompra.consultar_por_id)
    monkeypatch.setattr(compra, "consultar_por_cliente", DummyCompra.consultar_por_cliente)
    monkeypatch.setattr(compra, "insertar", DummyCompra.insertar)
    monkeypatch.setattr(Detallecompra, "consultar_por_compra", DummyDetalleCompra.consultar_por_compra)
    monkeypatch.setattr(Detallecompra, "insertar", DummyDetalleCompra.insertar)
    monkeypatch.setattr("src.app_web.views.compra", DummyCompra)

# --- Tests de Autenticación ---

def test_home_redirect(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/login_cliente' in response.headers.get('Location')

def test_registro_cliente_get(client):
    response = client.get('/registro_cliente')
    assert response.status_code == 200
    assert b"<form" in response.data

def test_registro_cliente_post_success(client):
    response = client.post('/registro_cliente', data={
        'nombre': 'Test',
        'email': 'test@example.com',
        'telefono': '1234567890',
        'direccion': 'Test Address',
        'password': 'secret'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Bienvenido" in response.data

def test_registro_cliente_post_error(client):
    response = client.post('/registro_cliente', data={
        'nombre': 'Test',
        'email': 'error@test.com',
        'telefono': '1234567890',
        'direccion': 'Test Address',
        'password': 'secret'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Error de validaci" in response.data

def test_registro_cliente_already_logged_in(client):
    with client.session_transaction() as sess:
        sess['cliente_id'] = 1
    response = client.get('/registro_cliente', follow_redirects=True)
    assert response.status_code == 200
    assert b"inicio" in response.data

def test_login_cliente_get(client):
    response = client.get('/login_cliente')
    assert response.status_code == 200
    assert b"<form" in response.data

def test_login_cliente_post_success(client):
    response = client.post('/login_cliente', data={
        'email': 'test@example.com',
        'password': 'secret'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Bienvenido" in response.data

def test_login_cliente_post_failure(client):
    response = client.post('/login_cliente', data={
        'email': 'error@test.com',
        'password': 'wrong'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"incorrectos" in response.data

def test_login_cliente_already_logged_in(client):
    with client.session_transaction() as sess:
        sess['cliente_id'] = 1
    response = client.get('/login_cliente', follow_redirects=True)
    assert response.status_code == 200
    assert b"inicio" in response.data

def test_logout(client):
    with client.session_transaction() as sess:
        sess['cliente_id'] = 1
        sess['cliente_nombre'] = 'Test'
    response = client.get('/logout', follow_redirects=True)
    with client.session_transaction() as sess:
        assert 'cliente_id' not in sess
    assert response.status_code == 200
    assert b"cerrado sesi" in response.data

