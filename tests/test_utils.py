import pytest
from decimal import Decimal
from src.app_web.utils import calcular_descuento

# Caso de monto negativo → debe lanzar excepción.
def test_calcular_descuento_negativo():
    with pytest.raises(ValueError) as excinfo:
        calcular_descuento(-50)
    assert "El monto de la compra no puede ser negativo" in str(excinfo.value)

# Caso sin descuento: monto menor a 100.
def test_calcular_descuento_sin_descuento():
    # Ejemplo: 50 no alcanza para ningún descuento.
    descuento = calcular_descuento(50)
    assert descuento == Decimal("0.00")

# Caso: subtotal mayor o igual a 700 → descuento 25%
def test_calcular_descuento_mayor_700():
    subtotal = "700"  # se envía como cadena
    descuento = calcular_descuento(subtotal)
    expected = Decimal("700") * Decimal("0.25")
    expected = expected.quantize(Decimal("0.01"))
    assert descuento == expected

# Caso: subtotal entre 500 y 699.99 → descuento 20%
def test_calcular_descuento_entre_500_y_700():
    subtotal = 600  # se puede enviar como entero
    descuento = calcular_descuento(subtotal)
    expected = Decimal("600") * Decimal("0.20")
    expected = expected.quantize(Decimal("0.01"))
    assert descuento == expected

# Caso: subtotal entre 300 y 499.99 → descuento 15%
def test_calcular_descuento_entre_300_y_500():
    subtotal = 300
    descuento = calcular_descuento(subtotal)
    expected = Decimal("300") * Decimal("0.15")
    expected = expected.quantize(Decimal("0.01"))
    assert descuento == expected

# Caso: subtotal entre 200 y 299.99 → descuento 10%
def test_calcular_descuento_entre_200_y_300():
    subtotal = 250
    descuento = calcular_descuento(subtotal)
    expected = Decimal("250") * Decimal("0.10")
    expected = expected.quantize(Decimal("0.01"))
    assert descuento == expected

# Caso: subtotal entre 100 y 199.99 → descuento 5%
def test_calcular_descuento_entre_100_y_200():
    subtotal = 150
    descuento = calcular_descuento(subtotal)
    expected = Decimal("150") * Decimal("0.05")
    expected = expected.quantize(Decimal("0.01"))
    assert descuento == expected

# Caso adicional: subtotal enviado como cadena (distinta forma)
def test_calcular_descuento_con_subtotal_string():
    subtotal = "150.00"
    descuento = calcular_descuento(subtotal)
    expected = Decimal("150.00") * Decimal("0.05")
    expected = expected.quantize(Decimal("0.01"))
    assert descuento == expected