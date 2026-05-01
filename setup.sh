#!/bin/bash

echo "Configurando PostgreSQL..."

# Crear usuario y BD (ignora errores si ya existen)
sudo -u postgres psql <<EOF
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'uacm') THEN
      CREATE USER uacm WITH PASSWORD 'uacm1';
   END IF;
END
\$\$;

CREATE DATABASE sistema_abc OWNER uacm;
GRANT ALL PRIVILEGES ON DATABASE sistema_abc TO uacm;
EOF

echo "Configurando entorno virtual..."

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

venv/bin/pip install -r requiirements.txt

echo "cONFIGUURACIÓN LISTA"
