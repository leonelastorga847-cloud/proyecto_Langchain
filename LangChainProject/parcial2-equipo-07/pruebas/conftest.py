import sys
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dominio import ServicioTaqueria, cargar_servicio  # noqa: E402


@pytest.fixture
def servicio():
    return cargar_servicio()                      # martes 14:00


def servicio_en(ahora: str) -> ServicioTaqueria:
    base = cargar_servicio().snapshot()
    base["ahora"] = ahora
    return ServicioTaqueria(base)


@pytest.fixture
def servicio_jueves():
    return servicio_en("2025-11-20T14:00:00")


@pytest.fixture
def servicio_cocina_cerrada():
    return servicio_en("2025-11-18T21:20:00")


@pytest.fixture
def servicio_sabado():
    return servicio_en("2025-11-22T14:00:00")


@pytest.fixture
def servicio_2114():
    return servicio_en("2025-11-18T21:14:00")


@pytest.fixture
def servicio_1259():
    return servicio_en("2025-11-18T12:59:00")
