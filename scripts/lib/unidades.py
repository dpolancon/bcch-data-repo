"""
Purpose:  Unidades canónicas de los paneles. Convierte cada serie a una sola
          unidad por dimensión y declara si el valor se puede sumar entre
          regiones, para que un panel diga por sí mismo qué operaciones admite.
Task:     Revisión multiescalar de la BDE -- proyecto de precio del suelo
Inputs:   n/a (declaraciones y conversión pura)
Outputs:  n/a
Created:  2026-08-27
Updated:  2026-08-27
Owner:    dpolancon
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Dimensiones. Dos magnitudes de dimensiones distintas nunca son comparables
# --no se convierte un metro cuadrado a un peso--, pero dos de la misma
# dimensión deben venir en la misma unidad o no se pueden ni sumar ni
# comparar. El Banco Central publica saldos promedio en pesos y saldos
# totales en millones de pesos, con tres órdenes de magnitud de diferencia y
# sin advertirlo en ninguna parte salvo el nombre de la serie.
# --------------------------------------------------------------------------

DINERO = "dinero"
SUPERFICIE = "superficie"
CONTEO = "conteo"
TASA = "tasa"

DIMENSIONES = (DINERO, SUPERFICIE, CONTEO, TASA)

# Unidad canónica de cada dimensión. El peso es la base natural del dinero:
# escalar la presentación es trivial, y una unidad implícita de millones es
# exactamente lo que produce un error de tres órdenes de magnitud.
CANONICA = {
    DINERO: "pesos",
    SUPERFICIE: "m2",
    CONTEO: "unidades",
    TASA: "%",
}

# Cómo se agrega entre regiones. `total` se suma; `promedio` no --sumar
# saldos promedio de dieciséis regiones no da nada interpretable, y sumar
# porcentajes de carteras con denominadores distintos, menos.
TOTAL = "total"
PROMEDIO = "promedio"

# Unidad de origen -> (dimensión, factor a la canónica, agregación, nota).
# Todo lo que entre a un panel pasa por acá; una unidad no declarada revienta
# en vez de colarse con factor 1 supuesto.
UNIDADES = {
    "pesos nominales por cuenta": (DINERO, 1.0, PROMEDIO, "nominal, sin deflactar"),
    "millones de pesos nominales": (DINERO, 1e6, TOTAL, "nominal, sin deflactar"),
    "pesos": (DINERO, 1.0, TOTAL, ""),
    "miles de millones de pesos encadenados 2018": (
        DINERO, 1e9, TOTAL, "volumen encadenado, referencia 2018; no aditivo entre sectores",
    ),
    "m2": (SUPERFICIE, 1.0, TOTAL, ""),
    "unidades": (CONTEO, 1.0, TOTAL, ""),
    "número de cuentas de personas naturales": (
        CONTEO, 1.0, TOTAL, "cuentas, no personas: una persona puede tener varias",
    ),
    "% de la cartera de vivienda": (TASA, 1.0, PROMEDIO, "porcentaje de la cartera de vivienda"),
    "% de la cartera de consumo": (TASA, 1.0, PROMEDIO, "porcentaje de la cartera de consumo"),
    "% de la cartera comercial": (TASA, 1.0, PROMEDIO, "porcentaje de la cartera comercial"),
    "% de las cuentas del país": (TASA, 1.0, PROMEDIO, "participación en el total nacional"),
    "fracción del producto regional": (TASA, 100.0, PROMEDIO, "participación sectorial"),
}


class UnidadDesconocida(KeyError):
    """Una unidad sin declarar. Se falla en vez de suponer factor 1."""


def resolver(unidad: str) -> tuple[str, float, str, str]:
    """Dimensión, factor a la canónica, agregación y nota de una unidad."""
    try:
        return UNIDADES[unidad]
    except KeyError:
        raise UnidadDesconocida(
            f"Unidad no declarada: {unidad!r}. Declárela en lib/unidades.py "
            "con su dimensión y su factor; suponer factor 1 es cómo se "
            "confunden pesos con millones de pesos."
        ) from None


def normalizar(marco, col_valor: str = "valor", col_unidad: str = "unidad"):
    """Convierte `col_valor` a la unidad canónica de su dimensión.

    Devuelve el marco con tres columnas nuevas y la unidad reescrita:
    `dimension`, `agregacion` y `unidad_original`. Un panel que pasa por acá
    describe por sí mismo qué operaciones admite, que es lo que faltaba
    cuando se sumaron los doce meses de un stock y cuando se etiquetaron
    igual un saldo en pesos y otro en millones de pesos.
    """
    marco = marco.copy()
    resueltas = {u: resolver(u) for u in marco[col_unidad].dropna().unique()}

    marco["unidad_original"] = marco[col_unidad]
    marco["dimension"] = marco[col_unidad].map(lambda u: resueltas[u][0])
    marco["agregacion"] = marco[col_unidad].map(lambda u: resueltas[u][2])
    factor = marco[col_unidad].map(lambda u: resueltas[u][1])
    marco[col_valor] = marco[col_valor] * factor
    marco[col_unidad] = marco["dimension"].map(CANONICA)
    return marco
