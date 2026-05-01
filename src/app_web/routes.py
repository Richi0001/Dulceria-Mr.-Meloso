from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from decimal import Decimal
from datetime import datetime

from .models import Producto, Cliente, compra, Detallecompra, DBException
from .utils import calcular_descuento

# --- Definición de Blueprints ---
auth_bp = Blueprint('auth_bp', __name__)
productos_bp = Blueprint('productos_bp', __name__, url_prefix='/productos')
compras_bp = Blueprint('compras_bp', __name__, url_prefix='/compras')

# Agrega en routes.py, junto con las otras rutas
@auth_bp.route('/')
def home():
    return redirect(url_for('auth_bp.login_cliente'))

# --- Decorador para requerir autenticación de cliente ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'cliente_id' not in session:
            flash('Debe iniciar sesión para acceder a esta sección.', 'danger')
            return redirect(url_for('auth_bp.login_cliente'))
        return f(*args, **kwargs)
    return decorated_function

# --- RUTAS DE AUTENTICACIÓN (auth_bp) ---
@auth_bp.route('/registro_cliente', methods=['GET', 'POST'])
def registro_cliente():
    if 'cliente_id' in session:
        return redirect(url_for('compras_bp.inicio_home'))
    if request.method == 'POST':
        try:
            cliente = Cliente.crear(
                nombre=request.form['nombre'],
                email=request.form['email'],
                telefono=request.form['telefono'],
                direccion=request.form['direccion'],
                password=request.form['password']
            )
            session['cliente_id'] = cliente.id
            session['cliente_nombre'] = cliente.nombre
            flash('Registro exitoso! Bienvenido ' + cliente.nombre, 'success')
            return redirect(url_for('compras_bp.inicio_home'))
        except Exception as e:
            flash(f"Error al registrar cliente: {e}", "danger")
    return render_template('registro_cliente.html')

@auth_bp.route('/login_cliente', methods=['GET', 'POST'])
def login_cliente():
    if 'cliente_id' in session:
        return redirect(url_for('compras_bp.inicio_home'))
    if request.method == 'POST':
        try:
            cliente = Cliente.autenticar(
                email=request.form['email'],
                password=request.form['password']
            )
            if cliente:
                session['cliente_id'] = cliente.id
                session['cliente_nombre'] = cliente.nombre
                flash('Bienvenido de vuelta ' + cliente.nombre, 'success')
                return redirect(url_for('compras_bp.inicio_home'))
            else:
                flash('Email o contraseña incorrectos', 'danger')
        except Exception as e:
            flash(f"Error en la autenticación: {e}", "danger")
    return render_template('login_cliente.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('auth_bp.login_cliente'))

# --- RUTAS DE PÁGINA PRINCIPAL Y GENERALES (compras_bp) ---
@compras_bp.route('/inicio')
@login_required
def inicio_home():
    return render_template('inicio.html')

# --- RUTAS DE GESTIÓN DE PRODUCTOS (productos_bp) ---
@productos_bp.route('/consulta')
@login_required
def consulta_productos():
    try:
        resultados = Producto.consultar_todo()
        return render_template("consulta.html", datos=resultados)
    except DBException as e:
        flash(f"Error al cargar productos: {e}", "danger")
        return render_template("consulta.html", datos=[])

# Se han removido las rutas de alta, edición y eliminación de productos.

# --- RUTAS DEL MÓDULO DE compraS (compras_bp) ---
@compras_bp.route('/')
@login_required
def listar_compras():
    try:
        compras = compra.consultar_por_cliente(session['cliente_id'])
        return render_template('lista_compras.html', compras=compras)
    except DBException as e:
        flash(f"Error al cargar sus compras: {e}", "danger")
        return render_template('lista_compras.html', compras=[])

@compras_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva_compra():
    if request.method == 'POST':
        try:
            accion = request.form.get('accion')
            if accion == 'agregar':
                # Acción: Agregar producto a la compra actual
                producto_id = request.form['producto_id']
                cantidad_str = request.form['cantidad']
                try:
                    cantidad = int(cantidad_str)
                    if cantidad <= 0:
                        flash('La cantidad debe ser un número entero positivo.', 'danger')
                        return redirect(url_for('compras_bp.nueva_compra'))
                except ValueError:
                    flash('La cantidad debe ser un número válido.', 'danger')
                    return redirect(url_for('compras_bp.nueva_compra'))
                producto = Producto.consultar_id(producto_id)
                if not producto or not producto.activo:
                    flash('Producto no encontrado o inactivo.', 'danger')
                    return redirect(url_for('compras_bp.nueva_compra'))
                detalle_temp = session.get('detalle_compra_temp', {})
                cantidad_acumulada = detalle_temp.get(producto_id, 0)
                nueva_cantidad_total = cantidad_acumulada + cantidad
                if producto.stock < nueva_cantidad_total:
                    flash(f'No hay suficiente stock para {producto.descripcion}. Disponible: {producto.stock}, ya agregado: {cantidad_acumulada}', 'danger')
                    return redirect(url_for('compras_bp.nueva_compra'))
                detalle_temp[producto_id] = nueva_cantidad_total
                session['detalle_compra_temp'] = detalle_temp
                flash('Producto agregado a la compra.', 'success')
                return redirect(url_for('compras_bp.nueva_compra'))
            elif accion == 'confirmar':
                # Acción: Confirmar la compra utilizando el detalle almacenado en sesión
                detalle_temp = session.get('detalle_compra_temp', {})
                if not detalle_temp:
                    flash('Debe agregar al menos un producto a la compra.', 'danger')
                    return redirect(url_for('compras_bp.nueva_compra'))
                metodo_pago = request.form.get('metodo_pago', 'efectivo')
                total_subtotal = Decimal('0')
                total_descuento = Decimal('0')
                compra_detalles = []
                for producto_id, cantidad in detalle_temp.items():
                    producto = Producto.consultar_id(producto_id)
                    if not producto:
                        flash(f'Producto con id {producto_id} no encontrado.', 'danger')
                        return redirect(url_for('compras_bp.nueva_compra'))
                    precio_unitario = producto.precio
                    subtotal = precio_unitario * cantidad
                    descuento = calcular_descuento(subtotal)
                    total_subtotal += subtotal
                    total_descuento += descuento
                    compra_detalles.append({
                        'producto': producto,
                        'cantidad': cantidad,
                        'precio_unitario': precio_unitario
                    })
                total = total_subtotal - total_descuento
                nueva_compra_obj = compra(
                    cliente_id=session['cliente_id'],
                    subtotal=total_subtotal,
                    descuento=total_descuento,
                    total=total,
                    metodo_pago=metodo_pago
                )
                compra_id = nueva_compra_obj.insertar()
                for detalle in compra_detalles:
                    Detallecompra(
                        compra_id=compra_id,
                        producto_id=detalle['producto'].id,
                        cantidad=detalle['cantidad'],
                        precio_unitario=detalle['precio_unitario']
                    ).insertar()
                    detalle['producto'].reducir_stock(detalle['cantidad'])
                session.pop('detalle_compra_temp', None)
                flash('Compra registrada exitosamente!', 'success')
                return redirect(url_for('compras_bp.detalle_compra', id=compra_id))
        except DBException as e:
            flash(f'Error en la base de datos al registrar la compra: {str(e)}', 'danger')
        except Exception as e:
            flash(f'Ocurrió un error inesperado al registrar la compra: {str(e)}', 'danger')
    productos = Producto.consultar_todo()
    productos_activos = [p for p in productos if p.activo and p.stock > 0]
    detalle_temp = session.get('detalle_compra_temp', {})
    return render_template('nueva_compra.html', productos=productos_activos, detalle=detalle_temp)

@compras_bp.route('/<int:id>')
@login_required
def detalle_compra(id):
    try:
        compra_obj = compra.consultar_por_id(id)
        if not compra_obj or compra_obj.cliente_id != session['cliente_id']:
            flash("Compra no encontrada o no tienes permiso para verla.", "danger")
            return redirect(url_for('compras_bp.listar_compras'))
        detalles = Detallecompra.consultar_por_compra(id)
        return render_template('detalle_compra.html', compra=compra_obj, detalles=detalles)
    except DBException as e:
        flash(f"Error al cargar el detalle de la compra: {e}", "danger")
        return redirect(url_for('compras_bp.listar_compras'))
    except Exception as e:
        flash(f"Ocurrió un error inesperado al cargar el detalle: {e}", "danger")
        return redirect(url_for('compras_bp.listar_compras'))

@compras_bp.route('/consultar', methods=['GET'])
@login_required
def consultar_compras():
    try:
        compras = compra.consultar_por_cliente(session['cliente_id'])
    except DBException as e:
        flash(f"Error al cargar compras: {e}", "danger")
        compras = []
    return render_template('lista_compras.html', compras=compras)