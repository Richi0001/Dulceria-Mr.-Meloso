from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager

db_config = {
    "host": "localhost",
    "database": "sistema_abc",
    "user": "uacm",
    "password": "uacm1"
}

_tabla_productos = "CREATE TABLE IF NOT EXISTS Productos (" \
                   "id SERIAL PRIMARY KEY," \
                   "descripcion TEXT NOT NULL," \
                   "precio NUMERIC(10, 2) CHECK (precio >= 0)," \
                   "stock INTEGER CHECK (stock >= 0)," \
                   "activo BOOLEAN DEFAULT TRUE" \
                   ");"

_tabla_clientes = """CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    telefono TEXT NOT NULL,
    direccion TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""

_tabla_compras = """CREATE TABLE IF NOT EXISTS compras (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subtotal NUMERIC(10,2) CHECK (subtotal >= 0),
    descuento NUMERIC(10,2) CHECK (descuento >= 0),
    total NUMERIC(10,2) CHECK (total >= 0),
    metodo_pago TEXT NOT NULL
);"""

_tabla_detalle_compra = """CREATE TABLE IF NOT EXISTS Detallecompra (
    id SERIAL PRIMARY KEY,
    compra_id INTEGER REFERENCES compras(id),
    producto_id INTEGER REFERENCES Productos(id),
    cantidad INTEGER CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) CHECK (precio_unitario >= 0)
);"""

class PostgresDB:
    def __init__(self):
        self.app = None
        self.pool = None

    def init_app(self, app):
        self.app = app
        self.connect()

    def connect(self):
        self.pool = ThreadedConnectionPool(minconn=1, maxconn=30, **db_config)

    @contextmanager
    def get_cursor(self):
        if self.pool is None:
            self.connect()
        con = self.pool.getconn()
        try:
            cursor = con.cursor()
            yield cursor
            con.commit()
        except Exception as e:
            con.rollback()
            raise e
        finally:
            self.pool.putconn(con)

    def create_all_tables(self):
            with self.get_cursor() as cur:
                # Eliminamos las tablas existentes (con CASCADE para remover dependencias)
                cur.execute("DROP TABLE IF EXISTS Detallecompra CASCADE;")
                cur.execute("DROP TABLE IF EXISTS compras CASCADE;")
                cur.execute("DROP TABLE IF EXISTS Productos CASCADE;")
                cur.execute("DROP TABLE IF EXISTS clientes CASCADE;")
                # Crear las tablas en el orden correcto
                cur.execute(_tabla_clientes)
                cur.execute(_tabla_productos)
                cur.execute(_tabla_compras)
                cur.execute(_tabla_detalle_compra)
                # Insertar productos de ejemplo
                cur.execute("INSERT INTO Productos (descripcion, precio, stock, activo) VALUES ('Paleta Payaso', 15.50, 80, TRUE);")
                cur.execute("INSERT INTO Productos (descripcion, precio, stock, activo) VALUES ('Chicle Trident Menta', 5.00, 300, TRUE);")
                cur.execute("INSERT INTO Productos (descripcion, precio, stock, activo) VALUES ('Galletas Oreo', 22.00, 120, TRUE);")
                cur.execute("INSERT INTO Productos (descripcion, precio, stock, activo) VALUES ('Tamarindos Sal y Limon', 10.00, 180, TRUE);")
                cur.execute("INSERT INTO Productos (descripcion, precio, stock, activo) VALUES ('Dulce de Leche Cajeta', 35.00, 60, TRUE);")
                cur.execute("INSERT INTO Productos (descripcion, precio, stock, activo) VALUES ('Gomitas de Ositos', 8.50, 250, TRUE);")
                cur.execute("INSERT INTO Productos (descripcion, precio, stock, activo) VALUES ('Pulparindo Original', 7.00, 200, TRUE);")
                cur.execute("INSERT INTO Productos (descripcion, precio, stock, activo) VALUES ('Mazapan De La Rosa', 6.00, 150, TRUE);")
                cur.execute("INSERT INTO Productos (descripcion, precio, stock, activo) VALUES ('Dulce de Guayaba', 18.00, 90, TRUE);")
                cur.execute("INSERT INTO Productos (descripcion, precio, stock, activo) VALUES ('Pelon Pelo Rico', 13.00, 110, FALSE);")


# Instancia global
pgdb = PostgresDB()