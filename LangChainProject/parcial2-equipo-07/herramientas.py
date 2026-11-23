"""Herramientas del agente. Capturan ErrorDeNegocio y devuelven texto."""
import json
from dataclasses import dataclass

from langchain.tools import ToolRuntime, tool
from pydantic import BaseModel, Field

from dominio import ErrorDeNegocio, ServicioTaqueria


@dataclass
class Contexto:
    servicio: ServicioTaqueria


class ItemPedido(BaseModel):
    platillo_id: str = Field(description="ID del platillo tal como aparece en consultar_menu, p. ej. 'taco_pastor'.")
    cantidad: int = Field(description="Número de piezas o porciones (entero positivo).")


def _responder(funcion, *args, **kwargs) -> str:
    """Ejecuta una operación del dominio; los errores de negocio vuelven como texto."""
    try:
        return json.dumps({"ok": True, "resultado": funcion(*args, **kwargs)}, ensure_ascii=False)
    except ErrorDeNegocio as e:
        return f"ERROR: {e}"


@tool
def consultar_menu(runtime: ToolRuntime[Contexto]) -> str:
    """Usa esta herramienta para saber qué platillos se sirven HOY, con precio y existencias.
    Úsala siempre antes de afirmar que un platillo existe o está disponible. No modifica nada."""
    return _responder(runtime.context.servicio.consultar_menu)


@tool
def verificar_saldo(cliente_id: str, runtime: ToolRuntime[Contexto]) -> str:
    """Usa esta herramienta para consultar el saldo de la Tarjeta Taquera de un cliente.
    Requiere el ID del cliente (p. ej. 'C001'); si no lo tienes, pídeselo. No modifica nada."""
    return _responder(runtime.context.servicio.verificar_saldo, cliente_id)


@tool
def consultar_pedido(cliente_id: str, pedido_id: str, runtime: ToolRuntime[Contexto]) -> str:
    """Usa esta herramienta para ver el estado y el detalle de un pedido existente
    (p. ej. 'P001') de un cliente. No modifica nada."""
    return _responder(runtime.context.servicio.consultar_pedido, cliente_id, pedido_id)


@tool
def crear_pedido(
    cliente_id: str,
    items: list[ItemPedido],
    runtime: ToolRuntime[Contexto],
    metodo_pago: str = "saldo",
) -> str:
    """ESCRIBE: crea un pedido, descuenta stock y cobra. Requiere aprobación humana.
    Úsala solo cuando el cliente ya confirmó qué quiere y cuántos. Antes consulta el menú.
    metodo_pago: 'saldo' (Tarjeta Taquera) o 'mixto' (todo el saldo + efectivo en caja)."""
    return _responder(runtime.context.servicio.crear_pedido,
                      cliente_id, [i.model_dump() for i in items], metodo_pago)


@tool
def cancelar_pedido(cliente_id: str, pedido_id: str, runtime: ToolRuntime[Contexto]) -> str:
    """ESCRIBE: cancela un pedido activo y devuelve stock y saldo. Requiere aprobación humana.
    Úsala solo si el cliente pidió explícitamente cancelar y conoces el número de pedido."""
    return _responder(runtime.context.servicio.cancelar_pedido, cliente_id, pedido_id)


HERRAMIENTAS = [consultar_menu, verificar_saldo, consultar_pedido, crear_pedido, cancelar_pedido]
