from flask import render_template, request, redirect, url_for, session, flash
from decimal import Decimal
from .models import Producto, Cliente, compra, Detallecompra, AltaProductoException, AltaProductoPrecioException
from .postgres_db import pgdb

def registrar_rutas(app):
    """
    Registra todas las rutas de la aplicación Flask.
    
    Args:
        app: Instancia de la aplicación Flask
        
    """
    
    # --- RUTAS PRINCIPALES ---
    
    @app.route('/')
    def home():
        """Redirige la raíz a la página de login de cliente"""
        return redirect(url_for('login_cliente'))

    # --- AUTENTICACIÓN Y PERFIL ---
    
    @app.route('/registro_cliente', methods=['GET', 'POST'])
    def registro_cliente():
        """
        Maneja el registro de nuevos clientes.
        
        GET: Muestra el formulario de registro
        POST: Procesa el formulario y crea el cliente
        """
        # Si ya está logueado, redirige al inicio
        if 'cliente_id' in session:
            return redirect(url_for('inicio_home'))
            
        if request.method == 'POST':
            try:
                # Crear nuevo cliente con los datos del formulario
                cliente = Cliente.crear(
                    nombre=request.form['nombre'],
                    email=request.form['email'],
                    telefono=request.form['telefono'],
                    direccion=request.form['direccion'],
                    password=request.form['password']
                )
                # Establecer sesión
                session['cliente_id'] = cliente.id
                session['cliente_nombre'] = cliente.nombre
                flash('Registro exitoso! Bienvenido ' + cliente.nombre, 'success')
                return redirect(url_for('inicio_home'))
            except ValueError as e:
                # Mostrar errores de validación
                flash(str(e), 'danger')
        return render_template('registro_cliente.html')

    @app.route('/login_cliente', methods=['GET', 'POST'])
    def login_cliente():
        """
        Maneja el inicio de sesión de clientes.
        
        GET: Muestra el formulario de login
        POST: Valida credenciales e inicia sesión
        """
        if 'cliente_id' in session:
            return redirect(url_for('inicio_home'))
            
        if request.method == 'POST':
            # Autenticar cliente
            cliente = Cliente.autenticar(
                email=request.form['email'],
                password=request.form['password']
            )
            if cliente:
                # Establecer sesión
                session['cliente_id'] = cliente.id
                session['cliente_nombre'] = cliente.nombre
                flash('Bienvenido de vuelta ' + cliente.nombre, 'success')
                return redirect(url_for('inicio_home'))
            flash('Email o contraseña incorrectos', 'danger')
        return render_template('login_cliente.html')

    @app.route('/logout')
    def logout():
        """Cierra la sesión del cliente actual"""
        session.pop('cliente_id', None)
        session.pop('cliente_nombre', None)
        flash('Has cerrado sesión', 'info')
        return redirect(url_for('login_cliente'))

    # --- PÁGINA DE INICIO ---
    
    @app.route('/inicio')
    def inicio_home():
        """Muestra la página principal del sistema"""
        if 'cliente_id' not in session:
            return redirect(url_for('registro_cliente'))
        return render_template('inicio.html')

    # --- GESTIÓN DE PRODUCTOS ---
    
    @app.route('/consulta_productos')
    def consulta_productos():
        """Muestra listado de todos los productos"""
        if 'cliente_id' not in session:
            return redirect(url_for('registro_cliente'))
        resultados = Producto.consultar_todo()
        return render_template("consulta.html", datos=resultados)

    @app.route('/alta_producto', methods=['GET', 'POST'])
    def alta_producto():
        """
        Maneja el alta de nuevos productos.
        
        GET: Muestra el formulario
        POST: Procesa el formulario y crea el producto
        """
        if 'cliente_id' not in session:
            return redirect(url_for('registro_cliente'))
            
        if request.method == 'POST':
            try:
                # Crear nuevo producto con datos del formulario
                nuevo_prod = Producto(
                    descripcion=request.form['descripcion'],
                    precio=request.form['precio'],
                    stock=request.form.get('stock', 0)
                )
                nuevo_prod.insertar()
                flash("Producto registrado exitosamente", "success")
                return redirect(url_for('consulta_productos'))
            except (AltaProductoException, AltaProductoPrecioException) as e:
                flash(str(e), "danger")
        return render_template('producto.html')
    
     
    @app.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
    def editar_producto(id):
        """
        Edita un producto existente.
        
        GET: Muestra formulario con datos actuales
        POST: Actualiza el producto con nuevos datos
        """
        if 'cliente_id' not in session:
            return redirect(url_for('registro_cliente'))
        
        # Obtener producto a editar
        producto = Producto.consultar_id(id)
        
        if not producto:
            flash("Producto no encontrado", "danger")
            return redirect(url_for('consulta_productos'))
        
        if request.method == 'POST':
            try:
                # Actualizar datos del producto
                producto.descripcion = request.form['descripcion']
                producto.precio = request.form['precio']
                producto.stock = request.form['stock']
                
                if producto.actualizar() > 0:
                    flash("Producto actualizado correctamente", "success")
                else:
                    flash("No se pudo actualizar el producto", "warning")
                    
                return redirect(url_for('consulta_productos'))
                
            except (AltaProductoException, AltaProductoPrecioException) as e:
                flash(str(e), "danger")
        
        return render_template('editar_producto.html', producto=producto)

    # --- MÓDULO DE compraS ---
    
    @app.route('/compras')
    def listar_compras():
        """Muestra listado de compras del cliente actual"""
        if 'cliente_id' not in session:
            return redirect(url_for('registro_cliente'))
        
        # Obtener compras del cliente actual
        compras = compra.consultar_por_cliente(session['cliente_id'])
        return render_template('lista_compras.html', compras=compras)

    @app.route('/compras/')
    def listar_compras_con_slash():
        """Redirige /compras/ a /compras para consistencia en URLs"""
        return redirect(url_for('listar_compras'))

    @app.route('/nueva_compra', methods=['GET', 'POST'])
    def nueva_compra():
        """
        Maneja el proceso de creación de nuevas compras (un producto por vez, sin carrito).
        """
        if 'cliente_id' not in session:
            return redirect(url_for('registro_cliente'))

        if request.method == 'POST':
            try:
                producto_id = request.form['producto_id']
                cantidad = int(request.form['cantidad'])
                metodo_pago = request.form['metodo_pago']
                producto = Producto.consultar_id(producto_id)
                if not producto:
                    flash('Producto no encontrado', 'danger')
                    return redirect(url_for('nueva_compra'))
                if producto.stock < cantidad:
                    flash(f'No hay suficiente stock de {producto.descripcion}. Disponible: {producto.stock}', 'danger')
                    return redirect(url_for('nueva_compra'))
                precio_unitario = producto.precio
                subtotal = precio_unitario * cantidad
                descuento = Decimal('0')
                if subtotal >= Decimal('700'):
                    descuento = subtotal * Decimal('0.25')
                elif subtotal >= Decimal('500'):
                    descuento = subtotal * Decimal('0.20')
                elif subtotal >= Decimal('300'):
                    descuento = subtotal * Decimal('0.15')
                elif subtotal >= Decimal('200'):
                    descuento = subtotal * Decimal('0.10')
                elif subtotal >= Decimal('100'):
                    descuento = subtotal * Decimal('0.05')
                total = subtotal - descuento
                compra = compra(
                    cliente_id=session['cliente_id'],
                    subtotal=subtotal,
                    descuento=descuento,
                    total=total,
                    metodo_pago=metodo_pago
                )
                compra_id = compra.insertar()
                Detallecompra(
                    compra_id=compra_id,
                    producto_id=producto.id,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario
                ).insertar()
                producto.reducir_stock(cantidad)
                flash('compra registrada exitosamente!', 'success')
                return redirect(url_for('detalle_compra', id=compra_id))
            except Exception as e:
                flash(f'Error al registrar compra: {str(e)}', 'danger')

        productos = Producto.consultar_todo()
        productos_activos = [p for p in productos if p.activo and p.stock > 0]
        return render_template('nueva_compra.html', productos=productos_activos)

    @app.route('/compra/<int:id>')
    def detalle_compra(id):
        """Muestra el detalle completo de una compra específica"""
        if 'cliente_id' not in session:
            return redirect(url_for('registro_cliente'))
        
        # Obtener compra y validar que pertenece al cliente
        compra = compra.consultar_por_id(id)
        if not compra or compra.cliente_id != session['cliente_id']:
            flash("compra no encontrada o no autorizada", "danger")
            return redirect(url_for('listar_compras'))
        
        # Obtener detalles de la compra
        detalles = Detallecompra.consultar_por_compra(id)
        return render_template('detalle_compra.html', compra=compra, detalles=detalles)