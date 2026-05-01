# Dulceria-Mr.-Meloso
Dulcería online desarrollada en Python que permite a los usuarios explorar un catálogo de productos, agregar artículos al carrito y realizar compras de forma sencilla. Incluye gestión de usuarios, inventario, utilizando Flask para el backend y PostgreSQL como sistema de base de datos.

# Dulcería Mr. Meloso

Aplicación web de una dulcería online desarrollada en Python con Flask y PostgreSQL. Permite a los usuarios explorar productos, agregarlos al carrito y gestionar pedidos.

---

## Instalación y configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/Richi0001/Dulceria-Mr.-Meloso.git
cd Dulceria-Mr.-Meloso
```

---

### 2. Crear entorno virtual

```bash
python3 -m venv venv
```

---

### 3. Activar entorno virtual

En Linux / Ubuntu:

```bash
source venv/bin/activate
```

---

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

### 5. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto con:

```env
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_NAME=tu_base_de_datos
DB_HOST=localhost
```

---

## Ejecución del proyecto

```bash
python3 run.py
```

---

## Notas importantes

* No subir el archivo `.env` al repositorio.
* El entorno virtual (`venv/`) está ignorado en Git.
* Asegúrate de tener PostgreSQL instalado y configurado.

---

## Tecnologías usadas

* Python
* Flask
* PostgreSQL
* HTML5/CSS3/Bootstrap
