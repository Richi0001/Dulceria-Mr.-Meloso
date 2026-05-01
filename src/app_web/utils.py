# app/utils.py
from decimal import Decimal

def calcular_descuento(subtotal):
    """
    Calcula el descuento a aplicar según el monto total de la compra.
    RN12, RF12, CU07
    """
    descuento = Decimal('0')
    # Asegurar que subtotal sea Decimal para cálculos precisos
    subtotal = Decimal(str(subtotal)) 

    if subtotal < 0: # CU07 Flujo alternativo 2.1: Monto negativo
        # Aunque la RN dice "si el monto es negativo, muestra un mensaje de error",
        # la función debería lanzar una excepción para que la capa superior la maneje.
        raise ValueError("El monto de la compra no puede ser negativo para calcular descuento.")
    
    # Aplica descuentos según los rangos definidos
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
    
    # Asegurar que el descuento tenga dos decimales de precisión (RN12)
    return descuento.quantize(Decimal('0.01'))