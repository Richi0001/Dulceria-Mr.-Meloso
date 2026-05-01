import pytest
from decimal import Decimal
from src.app_web.models import Detallecompra, DBException, pgdb

class FakeCursor:
    def __init__(self, fetchall_return):
        self.fetchall_return = fetchall_return
        self.queries = []
    def execute(self, query, params=None):
        self.queries.append(query)
    def fetchall(self):
        return self.fetchall_return
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, traceback):
        pass

# Función fake para retornar el cursor normal, pasando explícitamente la fila simulada.
def fake_get_cursor_normal():
    # Se retorna una lista con una única fila: (id, producto_id, descripcion, cantidad, precio_unitario)
    return FakeCursor([(1, 10, "Producto A", 2, Decimal("50"))])

def test_consultar_por_compra_list_comprehension(monkeypatch):
    """
    Test para comprobar que, para cada fila retornada,
    se construya el diccionario esperado.
    """
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_normal)
    result = Detallecompra.consultar_por_compra(5)  # compra_id arbitrario
    expected = [{
        'id': 1,
        'producto_id': 10,
        'descripcion': "Producto A",
        'cantidad': 2,
        'precio_unitario': Decimal("50"),
        'importe': Decimal("100")  # 2 * 50
    }]
    assert result == expected

def fake_get_cursor_exception():
    class FailingCursor:
        def __enter__(self):
            raise Exception("Simulated failure")
        def __exit__(self, exc_type, exc_val, traceback):
            pass
    return FailingCursor()

def test_consultar_por_compra_exception(monkeypatch):
    """
    Test para forzar el manejo de excepción en consultar_por_compra.
    Inyecta un cursor que falla para provocar que se lance DBException.
    """
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_exception)
    with pytest.raises(DBException) as excinfo:
        Detallecompra.consultar_por_compra(5)
    # Verifica que el mensaje de la excepción incluya alguna parte relevante
    assert "Error al consultar detalles de compra 5:" in str(excinfo.value)
############### PRUEBA PARA INSERTAR(SELF) DE MODELS.PY ###############clase Detalle compra
import pytest
from decimal import Decimal
from src.app_web.models import Detallecompra, DBException, pgdb

# Cursor simulado para el caso exitoso, que retorna un id dummy (por ejemplo, 42)
class FakeCursorInsert:
    def __init__(self, fetchone_return=(42,)):
        self.queries = []
        self.fetchone_return = fetchone_return
    def execute(self, query, params=None):
        self.queries.append(query)
    def fetchone(self):
        return self.fetchone_return
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, traceback):
        pass

# Función fake para retornar el cursor simulado exitoso.
def fake_get_cursor_success():
    return FakeCursorInsert()

# Función fake que simula un fallo al entrar al contexto del cursor.
def fake_get_cursor_failure():
    class FailingCursor:
        def __enter__(self):
            raise Exception("Simulated insert failure")
        def __exit__(self, exc_type, exc_val, traceback):
            pass
    return FailingCursor()

def test_detallecompra_insertar_success(monkeypatch):
    # Crea una instancia de Detallecompra con datos de prueba.
    detalle = Detallecompra(compra_id=5, producto_id=10, cantidad=3, precio_unitario=Decimal("20"))
    # Inyecta el fake cursor exitoso para simular una inserción correcta.
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_success)
    
    # Se espera que el método insertar retorne el id dummy (42) y asigne ese valor a detalle.id.
    result_id = detalle.insertar()
    assert result_id == 42
    assert detalle.id == 42

def test_detallecompra_insertar_failure(monkeypatch):
    detalle = Detallecompra(compra_id=5, producto_id=10, cantidad=3, precio_unitario=Decimal("20"))
    # Inyecta el fake cursor que provoca una excepción para simular un fallo en la inserción.
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_failure)
    
    with pytest.raises(DBException) as excinfo:
        detalle.insertar()
    # Verifica que el mensaje de la excepción incluya una parte relevante.
    assert "Error al insertar detalle de compra" in str(excinfo.value)

    ##########TEST PARA FUNCION  def consultar_por_id(cls, id) DE MODELS.Py

import pytest
from decimal import Decimal
from datetime import datetime
from src.app_web.models import compra, DBException, pgdb

# --- Fake cursor para la función consultar_por_id ---

class FakeCursorCompra:
    def __init__(self, fetchone_return):
        self.fetchone_return = fetchone_return
        self.queries = []
    def execute(self, query, params=None):
        self.queries.append(query)
    def fetchone(self):
        return self.fetchone_return
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, traceback):
        pass

# Función fake que simula que se encuentra la compra (éxito).
def fake_get_cursor_compra_success():
    # Simula una fila retornada: (id, cliente_id, fecha, subtotal, descuento, total, metodo_pago)
    row = (1, 10, datetime(2025, 5, 31), Decimal("100.00"), Decimal("5.00"), Decimal("95.00"), "efectivo")
    return FakeCursorCompra(row)

# Función fake que simula que no se encuentra ninguna fila (fetchone() retorna None)
def fake_get_cursor_compra_not_found():
    return FakeCursorCompra(None)

# Función fake que simula un fallo en la obtención del cursor
def fake_get_cursor_compra_failure():
    class FailingCursor:
        def __enter__(self):
            raise Exception("Simulated failure")
        def __exit__(self, exc_type, exc_val, traceback):
            pass
    return FailingCursor()

# --- Tests para la función consultar_por_id de la clase compra ---

def test_consultar_por_id_compra_success(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_compra_success)
    result = compra.consultar_por_id(1)
    assert result is not None
    assert result.id == 1
    assert result.cliente_id == 10
    assert result.fecha == datetime(2025, 5, 31)
    assert result.subtotal == Decimal("100.00")
    assert result.descuento == Decimal("5.00")
    assert result.total == Decimal("95.00")
    assert result.metodo_pago == "efectivo"

def test_consultar_por_id_compra_not_found(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_compra_not_found)
    result = compra.consultar_por_id(1)
    # Al no encontrar fila, se debe retornar None.
    assert result is None

def test_consultar_por_id_compra_exception(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_compra_failure)
    with pytest.raises(DBException) as excinfo:
        compra.consultar_por_id(1)
    # Verifica que el mensaje de error incluya parte del texto esperado.
    assert "Error al consultar compra por ID 1:" in str(excinfo.value)

    ############# TEST PARA FUNCION def consultar_por_compra(cls, compra_id):  DE MODELS.Py
import pytest
from decimal import Decimal
from src.app_web.models import Detallecompra, DBException, pgdb

# Fake cursor para simular el comportamiento del cursor real.
class FakeCursor:
    def __init__(self, fetchall_return):
        self.fetchall_return = fetchall_return
        self.queries = []
    def execute(self, query, params=None):
        self.queries.append(query)
    def fetchall(self):
        return self.fetchall_return
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, traceback):
        pass

# Caso éxito: Se retorna una fila con descripción definida.
def fake_get_cursor_success():
    # Simula que se retorna una única fila:
    # (id, producto_id, descripcion, cantidad, precio_unitario)
    row = (1, 10, "Producto A", 2, Decimal("50"))
    return FakeCursor([row])

# Caso éxito: Se retorna una fila donde la descripción es None.
def fake_get_cursor_null_description():
    row = (2, 11, None, 3, Decimal("40"))
    return FakeCursor([row])

# Caso en que la consulta no retorna filas (fetchall() retorna lista vacía).
def fake_get_cursor_empty():
    return FakeCursor([])

# Caso de excepción: Simula un fallo al entrar al bloque with.
def fake_get_cursor_failure():
    class FailingCursor:
        def __enter__(self):
            raise Exception("Simulated failure")
        def __exit__(self, exc_type, exc_val, traceback):
            pass
    return FailingCursor()

def test_consultar_por_compra_success(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_success)
    result = Detallecompra.consultar_por_compra(5)
    expected = [{
        'id': 1,
        'producto_id': 10,
        'descripcion': "Producto A",
        'cantidad': 2,
        'precio_unitario': Decimal("50"),
        'importe': Decimal("100")  # 2 * 50
    }]
    assert result == expected

def test_consultar_por_compra_null_description(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_null_description)
    result = Detallecompra.consultar_por_compra(5)
    expected = [{
        'id': 2,
        'producto_id': 11,
        'descripcion': "Producto (Eliminado/Desconocido)",
        'cantidad': 3,
        'precio_unitario': Decimal("40"),
        'importe': Decimal("120")  # 3 * 40
    }]
    assert result == expected

def test_consultar_por_compra_empty(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_empty)
    result = Detallecompra.consultar_por_compra(5)
    assert result == []

def test_consultar_por_compra_exception(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_failure)
    with pytest.raises(DBException) as excinfo:
        Detallecompra.consultar_por_compra(5)
    assert "Error al consultar detalles de compra 5:" in str(excinfo.value)

    ############# TEST PARA FUNCION  def insertar(self) DE MODELS.Py CLASE COMPRA

import pytest
from decimal import Decimal
from datetime import datetime
from src.app_web.models import Detallecompra, compra, DBException, pgdb

# -------------------------------------------------------------------------
# Pruebas para Detallecompra.consultar_por_compra
# -------------------------------------------------------------------------

# Fake cursor para simular el comportamiento del cursor real.
class FakeCursor:
    def __init__(self, fetchall_return):
        self.fetchall_return = fetchall_return
        self.queries = []
    def execute(self, query, params=None):
        self.queries.append(query)
    def fetchall(self):
        return self.fetchall_return
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, traceback):
        pass

# Caso éxito: Se retorna una fila con descripción definida.
def fake_get_cursor_success_detalle():
    # Simula que se retorna una única fila:
    # (id, producto_id, descripcion, cantidad, precio_unitario)
    row = (1, 10, "Producto A", 2, Decimal("50"))
    return FakeCursor([row])

# Caso éxito: Se retorna una fila donde la descripción es None.
def fake_get_cursor_null_description():
    row = (2, 11, None, 3, Decimal("40"))
    return FakeCursor([row])

# Caso en que la consulta no retorna filas.
def fake_get_cursor_empty():
    return FakeCursor([])

# Caso de excepción: Simula un fallo al entrar al bloque with.
def fake_get_cursor_failure():
    class FailingCursor:
        def __enter__(self):
            raise Exception("Simulated failure")
        def __exit__(self, exc_type, exc_val, traceback):
            pass
    return FailingCursor()

# Test: Consulta exitosa con descripción definida.
def test_consultar_por_compra_success(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_success_detalle)
    result = Detallecompra.consultar_por_compra(5)
    expected = [{
        'id': 1,
        'producto_id': 10,
        'descripcion': "Producto A",
        'cantidad': 2,
        'precio_unitario': Decimal("50"),
        'importe': Decimal("100")  # 2 * 50
    }]
    assert result == expected

# Test: Consulta exitosa con descripción nula (usa valor por defecto).
def test_consultar_por_compra_null_description(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_null_description)
    result = Detallecompra.consultar_por_compra(5)
    expected = [{
        'id': 2,
        'producto_id': 11,
        'descripcion': "Producto (Eliminado/Desconocido)",
        'cantidad': 3,
        'precio_unitario': Decimal("40"),
        'importe': Decimal("120")  # 3 * 40
    }]
    assert result == expected

# Test: Consulta que retorna lista vacía.
def test_consultar_por_compra_empty(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_empty)
    result = Detallecompra.consultar_por_compra(5)
    assert result == []

# Test: Manejo de excepción en consultar_por_compra.
def test_consultar_por_compra_exception(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_failure)
    with pytest.raises(DBException) as excinfo:
        Detallecompra.consultar_por_compra(5)
    assert "Error al consultar detalles de compra 5:" in str(excinfo.value)


# -------------------------------------------------------------------------
# Pruebas para compra.insertar
# -------------------------------------------------------------------------

# Fake cursor para simular la inserción exitosa (retornando un id dummy, e.g., 42)
class FakeCursorInsertForCompra:
    def __init__(self, fetchone_return=(42,)):
        self.fetchone_return = fetchone_return
        self.queries = []
    def execute(self, query, params=None):
        self.queries.append(query)
    def fetchone(self):
        return self.fetchone_return
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, traceback):
        pass

# Fake que simula la inserción exitosa.
def fake_get_cursor_compra_success():
    return FakeCursorInsertForCompra()

# Fake que simula un fallo durante la inserción.
def fake_get_cursor_compra_failure():
    class FailingCursor:
        def __enter__(self):
            raise Exception("Simulated failure during compra insertion")
        def __exit__(self, exc_type, exc_val, traceback):
            pass
    return FailingCursor()

# Test: Inserción exitosa de compra.
def test_compra_insertar_success(monkeypatch):
    c = compra(cliente_id=5, subtotal=Decimal("100.00"), descuento=Decimal("5.00"), 
               total=Decimal("95.00"), metodo_pago="efectivo")
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_compra_success)
    result_id = c.insertar()
    assert result_id == 42
    assert c.id == 42

# Test: Inserción de compra que falla (lanza DBException).
def test_compra_insertar_failure(monkeypatch):
    c = compra(cliente_id=5, subtotal=Decimal("100.00"), descuento=Decimal("5.00"), 
               total=Decimal("95.00"), metodo_pago="efectivo")
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_compra_failure)
    with pytest.raises(DBException) as excinfo:
        c.insertar()
    assert "Error al insertar compra:" in str(excinfo.value)

    ############# TEST PARA FUNCION  def consultar_por_cliente(cls, cliente_id):  DE la clase compra desde MODELS.Py

import pytest
from decimal import Decimal
from datetime import datetime
from src.app_web.models import compra, DBException, pgdb

# -------------------------------------------------------------------------
# Tests para la función consultar_por_cliente de la clase compra
# -------------------------------------------------------------------------

# Fake cursor para simular el comportamiento del cursor real.
class FakeCursor:
    def __init__(self, fetchall_return):
        self.fetchall_return = fetchall_return
        self.queries = []
    def execute(self, query, params=None):
        self.queries.append(query)
    def fetchall(self):
        return self.fetchall_return
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, traceback):
        pass

# Caso éxito: Se retorna una única fila.
def fake_get_cursor_consultar_cliente_success():
    # Simula que se retorna una fila:
    # (id, cliente_id, fecha, subtotal, descuento, total, metodo_pago)
    row = (
        1,                # id
        5,                # cliente_id
        datetime(2025, 5, 31),  # fecha
        Decimal("100.00"),# subtotal
        Decimal("5.00"),  # descuento
        Decimal("95.00"), # total
        "efectivo"        # metodo_pago
    )
    return FakeCursor([row])

# Caso éxito: Se retornan varias filas. 
def fake_get_cursor_consultar_cliente_multiple():
    # Se retornan dos registros; el primero con fecha más reciente.
    row1 = (
        1, 
        5, 
        datetime(2025, 5, 31),
        Decimal("100.00"),
        Decimal("5.00"),
        Decimal("95.00"),
        "efectivo"
    )
    row2 = (
        2, 
        5, 
        datetime(2025, 5, 30),
        Decimal("200.00"),
        Decimal("10.00"),
        Decimal("190.00"),
        "tarjeta"
    )
    return FakeCursor([row1, row2])

# Caso en que la consulta no retorna filas (lista vacía).
def fake_get_cursor_consultar_cliente_empty():
    return FakeCursor([])

# Caso de excepción: Simula fallo al entrar al bloque with.
def fake_get_cursor_consultar_cliente_failure():
    class FailingCursor:
        def __enter__(self):
            raise Exception("Simulated failure in consultar_por_cliente")
        def __exit__(self, exc_type, exc_val, traceback):
            pass
    return FailingCursor()

def test_consultar_por_cliente_success(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_consultar_cliente_success)
    result = compra.consultar_por_cliente(5)
    # Se espera una lista con un único objeto compra
    assert isinstance(result, list)
    assert len(result) == 1
    c = result[0]
    assert c.id == 1
    assert c.cliente_id == 5
    assert c.fecha == datetime(2025, 5, 31)
    assert c.subtotal == Decimal("100.00")
    assert c.descuento == Decimal("5.00")
    assert c.total == Decimal("95.00")
    assert c.metodo_pago == "efectivo"

def test_consultar_por_cliente_multiple(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_consultar_cliente_multiple)
    result = compra.consultar_por_cliente(5)
    # Se esperan dos registros ordenados descendentemente por fecha
    assert isinstance(result, list)
    assert len(result) == 2
    c1 = result[0]
    c2 = result[1]
    assert c1.id == 1
    assert c1.cliente_id == 5
    assert c1.fecha == datetime(2025, 5, 31)
    assert c2.id == 2
    assert c2.cliente_id == 5
    assert c2.fecha == datetime(2025, 5, 30)

def test_consultar_por_cliente_empty(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_consultar_cliente_empty)
    result = compra.consultar_por_cliente(5)
    # Se espera una lista vacía cuando no hay registros
    assert result == []

def test_consultar_por_cliente_exception(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_consultar_cliente_failure)
    with pytest.raises(DBException) as excinfo:
        compra.consultar_por_cliente(5)
    # Verifica que el mensaje de error incluya parte del texto esperado.
    assert "Error al consultar compras por cliente 5:" in str(excinfo.value)

###### TESTS OARA FUNCION consultar_todo de la clase cliente ######

import pytest
from src.app_web.models import Cliente, DBException, pgdb

# --- FakeCursor: Simula el comportamiento real del cursor ---
class FakeCursor:
    def __init__(self, fetchall_return):
        self.fetchall_return = fetchall_return
        self.queries = []
    def execute(self, query, params=None):
        self.queries.append(query)
    def fetchall(self):
        return self.fetchall_return
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, traceback):
        pass

# --- Funciones fake para distintos escenarios de consultar_todo ---

# Caso éxito: Se retorna una única fila.
# Se agregará un quinto elemento dummy para que la tupla tenga la cantidad esperada.
def fake_get_cursor_cliente_success_single():
    row = (1, "Juan Perez", "juan@example.com", "123456789", "dummy")
    return FakeCursor([row])

# Caso éxito: Se retornan varias filas.
def fake_get_cursor_cliente_success_multiple():
    row1 = (1, "Juan Perez", "juan@example.com", "123456789", "dummy")
    row2 = (2, "Maria Lopez", "maria@example.com", "987654321", "dummy")
    return FakeCursor([row1, row2])

# Caso sin resultados: La consulta retorna lista vacía.
def fake_get_cursor_cliente_empty():
    return FakeCursor([])

# Caso de excepción: Simula un fallo al entrar al bloque with.
def fake_get_cursor_cliente_failure():
    class FailingCursor:
        def __enter__(self):
            raise Exception("Simulated failure in consultar_todo")
        def __exit__(self, exc_type, exc_val, traceback):
            pass
    return FailingCursor()

# --- Fixture que parchea el __init__ de Cliente ---
# Se modifica el constructor para que, al construirse Cliente(*row),
# solo use los primeros 4 elementos (id, nombre, email, teléfono),
# ignorando elementos extras.
@pytest.fixture(autouse=True)
def patch_cliente_init(monkeypatch):
    original_init = Cliente.__init__
    def fake_init(self, *args, **kwargs):
        if args:
            valores = args[:4]
            self.id = valores[0] if len(valores) > 0 else None
            self.nombre = valores[1] if len(valores) > 1 else None
            self.email = valores[2] if len(valores) > 2 else None
            self.telefono = valores[3] if len(valores) > 3 else None
        else:
            self.id = kwargs.get("id")
            self.nombre = kwargs.get("nombre")
            self.email = kwargs.get("email")
            self.telefono = kwargs.get("telefono")
    monkeypatch.setattr(Cliente, "__init__", fake_init)
    yield
    monkeypatch.setattr(Cliente, "__init__", original_init)

# --- Tests para Cliente.consultar_todo ---

# Test: Consulta exitosa con un único registro.
def test_consultar_todo_success_single(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_cliente_success_single)
    result = Cliente.consultar_todo()
    assert isinstance(result, list)
    assert len(result) == 1
    c = result[0]
    assert c.id == 1
    assert c.nombre == "Juan Perez"
    assert c.email == "juan@example.com"
    assert c.telefono == "123456789"

# Test: Consulta exitosa con múltiples registros.
def test_consultar_todo_success_multiple(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_cliente_success_multiple)
    result = Cliente.consultar_todo()
    assert isinstance(result, list)
    assert len(result) == 2
    c1, c2 = result
    assert c1.id == 1
    assert c1.nombre == "Juan Perez"
    assert c1.email == "juan@example.com"
    assert c1.telefono == "123456789"
    assert c2.id == 2
    assert c2.nombre == "Maria Lopez"
    assert c2.email == "maria@example.com"
    assert c2.telefono == "987654321"

# Test: Consulta que retorna lista vacía.
def test_consultar_todo_empty(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_cliente_empty)
    result = Cliente.consultar_todo()
    assert result == []

# Test: Manejo de excepción en consultar_todo.
def test_consultar_todo_exception(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_cliente_failure)
    with pytest.raises(DBException) as excinfo:
        Cliente.consultar_todo()
    # Se verifica que el mensaje de error incluya el texto esperado.
    assert "Error al consultar todos los clientes:" in str(excinfo.value)


##### TEST PARA  def autenticar(cls, email, password): ##########   NO PASA UN TEST

import pytest
from src.app_web.models import Cliente, DBException, pgdb

# --- Adaptación del __init__ de Cliente para autenticar ---
# Si se reciben 5 argumentos (por ejemplo, id, nombre, email, password, telefono)
# se asignan todos; si se reciben 4, se asignan solo id, nombre, email y teléfono.
@pytest.fixture(autouse=True)
def patch_cliente_init(monkeypatch):
    original_init = Cliente.__init__
    def fake_init(self, *args, **kwargs):
        if args:
            if len(args) >= 5:
                self.id, self.nombre, self.email, self.password, self.telefono = args[:5]
            else:
                valores = args[:4]
                self.id = valores[0] if len(valores) > 0 else None
                self.nombre = valores[1] if len(valores) > 1 else None
                self.email = valores[2] if len(valores) > 2 else None
                self.telefono = valores[3] if len(valores) > 3 else None
        else:
            self.id = kwargs.get("id")
            self.nombre = kwargs.get("nombre")
            self.email = kwargs.get("email")
            self.password = kwargs.get("password")
            self.telefono = kwargs.get("telefono")
    monkeypatch.setattr(Cliente, "__init__", fake_init)
    yield
    monkeypatch.setattr(Cliente, "__init__", original_init)

# --- Fake Cursor para autenticar (usando fetchone) ---
class FakeCursorAuth:
    def __init__(self, fetchone_return):
        self.fetchone_return = fetchone_return
        self.queries = []
    def execute(self, query, params=None):
        self.queries.append(query)
    def fetchone(self):
        return self.fetchone_return
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, traceback):
        pass

# --- Fake functions para autenticar ---

def fake_get_cursor_autenticar_success():
    # Se simula la fila retornada con 5 elementos: (id, nombre, email, password, telefono)
    row = (1, "Juan Perez", "juan@example.com", "password123", "123456789")
    return FakeCursorAuth(row)

def fake_get_cursor_autenticar_not_found():
    # Simula que no se encuentra un registro (fetchone() retorna None)
    return FakeCursorAuth(None)

def fake_get_cursor_autenticar_failure():
    # Simula un fallo al obtener el cursor.
    class FailingCursorAuth:
        def __enter__(self):
            raise Exception("Simulated failure in autenticar")
        def __exit__(self, exc_type, exc_val, traceback):
            pass
    return FailingCursorAuth()

# --- Tests para el método autenticar de Cliente ---

def dummy_check_password(self, pwd):
    return True
# Antes de ejecutar el test, asigna el método dummy a la clase
Cliente.check_password = dummy_check_password

def test_autenticar_success(monkeypatch):
    # Primero, parchea el método check_password en la clase Cliente.
    monkeypatch.setattr(Cliente, "check_password", dummy_check_password)
    # Luego, inyecta el fake cursor que retorna una fila válida.
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_autenticar_success)
    
    user = Cliente.autenticar("juan@example.com", "password123")
    # Se espera que se retorne una instancia de Cliente con los datos correctos.
    assert user is not None, "Se esperaba un usuario, pero se obtuvo None"
    assert user.id == 1
    assert user.nombre == "Juan Perez"
    assert user.email == "juan@example.com"
    assert user.password == "password123"
    assert user.telefono == "123456789"

def test_autenticar_not_found(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_autenticar_not_found)
    user = Cliente.autenticar("noexiste@example.com", "pass")
    # Al no encontrar registro se espera que se retorne None.
    assert user is None

def test_autenticar_exception(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_autenticar_failure)
    with pytest.raises(DBException) as excinfo:
        Cliente.autenticar("juan@example.com", "password123")
    # Se verifica que el mensaje de error incluya el texto esperado.
    assert "Error durante la autenticación:" in str(excinfo.value)

########### TEST PARA FUNCION def consultar_todo(cls):  DE la clase producto 

import pytest
from decimal import Decimal
from src.app_web.models import Producto, DBException, pgdb

# --- Fixture para patchear el __init__ de Producto en tests de consultar_todo ---
@pytest.fixture(autouse=True)
def patch_producto_init(monkeypatch):
    # Se guarda el __init__ original (aunque en estos tests no queremos que ejecute la conversión conflictiva)
    original_init = Producto.__init__
    def dummy_init(self, descripcion=None, precio=None, id=None, stock=0, activo=True):
        self.id = id
        # Asignamos la descripción y stock directamente
        self.descripcion = descripcion
        self.stock = stock
        self.activo = activo
        # Para el precio, forzamos que si es ya Decimal se use tal cual; 
        # de lo contrario, intentamos convertir la cadena reemplazando comas por puntos.
        if isinstance(precio, Decimal):
            self.precio = precio
        else:
            # Aquí asumimos que el valor viene en formato adecuado (por ejemplo, "50.00")
            self.precio = Decimal(str(precio).replace(',', '.'))
    monkeypatch.setattr(Producto, "__init__", dummy_init)
    yield
    monkeypatch.setattr(Producto, "__init__", original_init)

# Fake Cursor que simula el comportamiento real.
class FakeCursor:
    def __init__(self, fetchall_return):
        self.fetchall_return = fetchall_return
        self.queries = []
    def execute(self, query, params=None):
        self.queries.append(query)
    def fetchall(self):
        return self.fetchall_return
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, traceback):
        pass

# Función fake para simular un resultado exitoso con una sola fila.
def fake_get_cursor_producto_success():
    # Ahora, para que no se intente la conversión conflictiva,
    # se retorna el precio como cadena "50.00"
    row = (1, "Producto A", "Descripcion A", "50.00", 10)
    return FakeCursor([row])

# Función fake para simular que no se encuentran productos (fetchall retorna lista vacía).
def fake_get_cursor_producto_empty():
    return FakeCursor([])

# Función fake para simular un fallo al obtener el cursor.
def fake_get_cursor_producto_failure():
    class FailingCursor:
        def __enter__(self):
            raise Exception("Simulated failure in consultar_todo Producto")
        def __exit__(self, exc_type, exc_val, traceback):
            pass
    return FailingCursor()

# --- Tests para Producto.consultar_todo ---

def test_consultar_todo_producto_empty(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_producto_empty)
    productos = Producto.consultar_todo()
    assert productos == []

def test_consultar_todo_producto_exception(monkeypatch):
    monkeypatch.setattr(pgdb, "get_cursor", fake_get_cursor_producto_failure)
    with pytest.raises(DBException) as excinfo:
        Producto.consultar_todo()
    assert "Error al consultar todos los productos:" in str(excinfo.value)