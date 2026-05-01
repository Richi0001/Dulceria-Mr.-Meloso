# app/models.py
from decimal import Decimal
from datetime import datetime
import re
from werkzeug.security import generate_password_hash, check_password_hash
from .postgres_db import pgdb

# --- Excepciones Personalizadas ---
class AltaProductoException(Exception):
    """Excepción para errores al dar de alta o actualizar un producto."""
    pass
    
class AltaProductoPrecioException(AltaProductoException):
    """Excepción específica para errores de precio en productos."""
    pass

class DBException(Exception):
    """Excepción genérica para errores de base de datos."""
    pass

# --- Clase Producto ---
class Producto:
    def __init__(self, descripcion=None, precio=None, id=None, stock=0, activo=True):
        self.id = id
        self.descripcion = descripcion
        self.activo = activo

        # Validaciones de precio
        if precio is not None:
            try:
                # Se asegura que precio sea del tipo Decimal para cálculos precisos
                self.precio = Decimal(str(precio)) if not isinstance(precio, Decimal) else precio
            except Exception:
                raise AltaProductoPrecioException("Error: El precio es inválido (no numérico).")
            if self.precio < 0:
                raise AltaProductoPrecioException("Error: El precio no puede ser negativo.")
            if self.precio == 0:
                raise AltaProductoPrecioException("Error: El precio no puede ser cero.")
            if self.precio > Decimal('9999999999.99'):
                raise AltaProductoPrecioException("Error: El precio es demasiado grande.")
        else:
            self.precio = None

        # Validaciones de stock
        if isinstance(stock, str):
            try:
                self.stock = int(stock)
            except Exception:
                raise AltaProductoException("Error: El stock es inválido (no numérico entero).")
        else:
            self.stock = stock

        if self.stock < 0:
            raise AltaProductoException("Error: El stock no puede ser negativo.")


    def reducir_stock(self, cantidad):
        """Reduce el stock del producto al registrar una compra."""
        if self.stock < cantidad:
            raise ValueError(f"No hay suficiente stock para {self.descripcion}. Disponible: {self.stock}")
        try:
            with pgdb.get_cursor() as cur:
                cur.execute(
                    "UPDATE Productos SET stock = stock - %s WHERE id = %s RETURNING stock",
                    (cantidad, self.id)
                )
                self.stock = cur.fetchone()[0]  # Actualiza el stock del objeto
            return True
        except Exception as e:
            raise DBException(f"Error al reducir stock del producto {self.id}: {e}")


    @classmethod
    def consultar_id(cls, id):
        """Consulta un producto por su ID."""
        try:
            with pgdb.get_cursor() as cur:
                cur.execute(
                    "SELECT id, descripcion, precio, stock, activo FROM Productos WHERE id = %s",
                    (id,)
                )
                row = cur.fetchone()
                if row:
                    return cls(id=row[0], descripcion=row[1], precio=row[2], stock=row[3], activo=row[4])
            return None
        except Exception as e:
            raise DBException(f"Error al consultar producto por ID {id}: {e}")

    @classmethod
    def consultar_todo(cls):
        """Consulta todos los productos (activos e inactivos)."""
        try:
            with pgdb.get_cursor() as cur:
                cur.execute("SELECT id, descripcion, precio, stock, activo FROM Productos ORDER BY id")
                return [cls(id=row[0], descripcion=row[1], precio=row[2], stock=row[3], activo=row[4])
                        for row in cur.fetchall()]
        except Exception as e:
            raise DBException(f"Error al consultar todos los productos: {e}")

# --- Clase Cliente ---
class Cliente:
    def __init__(self, nombre=None, email=None, telefono=None, direccion=None, password=None, id=None, password_hash=None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.telefono = telefono
        self.direccion = direccion
        self.password = password # Usado solo para hashear, no se almacena directamente
        self.password_hash = password_hash # El hash de la contraseña

    @staticmethod
    def validar_email(email):
        """Valida formato de email. RNF1"""
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

    @staticmethod
    def validar_telefono(telefono):
        """Valida teléfono (debe ser numérico y 10 dígitos). RN6, RF6"""
        if not telefono or not isinstance(telefono, str):
            return False
        return telefono.isdigit() and len(telefono) == 10

    @classmethod
    def email_existe(cls, email):
        """Verifica si el email ya está registrado. RN6, RF6"""
        try:
            with pgdb.get_cursor() as cur:
                cur.execute("SELECT id FROM clientes WHERE email = %s", (email,))
                return cur.fetchone() is not None
        except Exception as e:
            raise DBException(f"Error al verificar existencia de email: {e}")

    @classmethod
    def crear(cls, nombre, email, telefono, direccion, password):
        """Crea nuevo cliente con validaciones. RN6, RF6, CU03"""
        if not nombre or not email or not telefono or not direccion or not password:
            raise ValueError("Todos los campos son obligatorios.")

        if not cls.validar_email(email):
            raise ValueError("Formato de email inválido.")
            
        if cls.email_existe(email):
            raise ValueError("Este correo ya está registrado.")
            
        if not cls.validar_telefono(telefono):
            raise ValueError("Teléfono debe tener 10 dígitos numéricos.")
        
        # Hashear la contraseña antes de guardar
        hashed_pw = generate_password_hash(password)
        
        try:
            with pgdb.get_cursor() as cur:
                cur.execute(
                    """INSERT INTO clientes   
                    (nombre, email, telefono, direccion, password_hash) 
                    VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                    (nombre, email, telefono, direccion, hashed_pw)
                )
                cliente_id = cur.fetchone()[0]
                return cls(id=cliente_id, nombre=nombre, email=email, 
                           telefono=telefono, direccion=direccion)
        except Exception as e:
            raise DBException(f"Error al crear cliente: {e}")

    @classmethod
    def autenticar(cls, email, password):
        """Autentica cliente. RF6"""
        try:
            with pgdb.get_cursor() as cur:
                cur.execute(
                    "SELECT id, nombre, password_hash FROM clientes WHERE email = %s", 
                    (email,)
                )
                cliente_data = cur.fetchone()
                if cliente_data and check_password_hash(cliente_data[2], password):
                    return cls(id=cliente_data[0], nombre=cliente_data[1], email=email)
            return None
        except Exception as e:
            raise DBException(f"Error durante la autenticación: {e}")

    @classmethod
    def consultar_todo(cls):
        """Consulta todos los clientes (útil para filtros en consulta de compras)."""
        try:
            with pgdb.get_cursor() as cur:
                cur.execute("SELECT id, nombre, email, telefono, direccion FROM clientes ORDER BY nombre")
                return [cls(id=row[0], nombre=row[1], email=row[2], telefono=row[3], direccion=row[4]) 
                        for row in cur.fetchall()]
        except Exception as e:
            raise DBException(f"Error al consultar todos los clientes: {e}")

# --- Clase compra ---
class compra:

    def __init__(self, cliente_id, subtotal, descuento, total, metodo_pago, id=None, fecha=None):
        self.id = id
        self.cliente_id = cliente_id
        self.subtotal = subtotal
        self.descuento = descuento
        self.total = total
        self.metodo_pago = metodo_pago
        self.fecha = fecha 

    def insertar(self):
        try:
            with pgdb.get_cursor() as cur:
                cur.execute(
                    "INSERT INTO compras (cliente_id, fecha, subtotal, descuento, total, metodo_pago) VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s, %s) RETURNING id",
                    (self.cliente_id, self.subtotal, self.descuento, self.total, self.metodo_pago)
                )
                self.id = cur.fetchone()[0]
            return self.id
        except Exception as e:
            raise DBException(f"Error al insertar compra: {e}")

    @classmethod
    def consultar_por_cliente(cls, cliente_id):
        try:
            with pgdb.get_cursor() as cur:
                cur.execute(
                    "SELECT id, cliente_id, fecha, subtotal, descuento, total, metodo_pago FROM compras WHERE cliente_id = %s ORDER BY fecha DESC",
                    (cliente_id,)
                )
                compras = []
                for row in cur.fetchall():
                    compra = cls(
                        cliente_id=row[1],
                        subtotal=row[3],
                        descuento=row[4],
                        total=row[5],
                        metodo_pago=row[6],
                        id=row[0],
                        fecha=row[2]
                    )
                    compras.append(compra)
                return compras
        except Exception as e:
            raise DBException(f"Error al consultar compras por cliente {cliente_id}: {e}")

    @classmethod
    def consultar_por_id(cls, id):
        try:
            with pgdb.get_cursor() as cur:
                cur.execute(
                    "SELECT id, cliente_id, fecha, subtotal, descuento, total, metodo_pago FROM compras WHERE id = %s",
                    (id,)
                )
                row = cur.fetchone()
                if row:
                    return cls(
                        cliente_id=row[1],
                        subtotal=row[3],
                        descuento=row[4],
                        total=row[5],
                        metodo_pago=row[6],
                        id=row[0],
                        fecha=row[2]
                    )
                return None
        except Exception as e:
            raise DBException(f"Error al consultar compra por ID {id}: {e}")


# --- Clase Detallecompra ---
class Detallecompra:
    def __init__(self, compra_id=None, producto_id=None, cantidad=0, precio_unitario=0, id=None):
        self.id = id
        self.compra_id = compra_id
        self.producto_id = producto_id
        self.cantidad = cantidad
        self.precio_unitario = Decimal(str(precio_unitario)) if precio_unitario is not None else Decimal('0')

    def insertar(self):
        """Inserta un detalle de compra en la base de datos. RN14, RF14"""
        try:
            with pgdb.get_cursor() as cur:
                cur.execute(
                    """INSERT INTO Detallecompra (compra_id, producto_id, cantidad, precio_unitario) 
                    VALUES (%s, %s, %s, %s) RETURNING id""",
                    (self.compra_id, self.producto_id, self.cantidad, self.precio_unitario)
                )
                self.id = cur.fetchone()[0]
            return self.id
        except Exception as e:
            raise DBException(f"Error al insertar detalle de compra: {e}")

    @classmethod
    def consultar_por_compra(cls, compra_id):
        """Consulta todos los detalles de una compra específica. CU06, RN14, RF14"""
        try:
            with pgdb.get_cursor() as cur:
                # RN16, RF16: Se deben guardar los detalles incluso si el producto luego es modificado o eliminado.
                # Esto se logra guardando el precio_unitario en Detallecompra y haciendo un LEFT JOIN para la descripción
                cur.execute(
                    """SELECT dv.id, dv.producto_id, p.descripcion, dv.cantidad, dv.precio_unitario 
                    FROM Detallecompra dv LEFT JOIN Productos p ON dv.producto_id = p.id 
                    WHERE dv.compra_id = %s""",
                    (compra_id,)
                )
                return [{
                    'id': row[0],
                    'producto_id': row[1],
                    # Si el producto se eliminó (lógicamente), la descripción podría ser NULL si no existe en Productos
                    # Podemos manejar esto en el template o aquí
                    'descripcion': row[2] if row[2] else "Producto (Eliminado/Desconocido)", 
                    'cantidad': row[3],
                    'precio_unitario': row[4],
                    'importe': row[3] * row[4] # Cálculo del importe por línea
                } for row in cur.fetchall()]
        except Exception as e:
            raise DBException(f"Error al consultar detalles de compra {compra_id}: {e}")
        
