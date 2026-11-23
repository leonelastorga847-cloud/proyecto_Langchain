"""Composición del agente: prompt, memoria y aprobación humana. Sin reglas de negocio."""
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from dominio import cargar_servicio
from herramientas import HERRAMIENTAS, Contexto

PROMPT_SISTEMA = """Eres el mesero virtual de la Taquería El Buen Pastor. Hablas siempre en español,
con trato amable y breve.

Cómo trabajas:
- Nunca inventes platillos, precios, existencias, saldos ni pedidos: consulta siempre con las herramientas.
- Si no tienes el ID de cliente y lo necesitas, pídelo antes de usar herramientas.
- Antes de crear un pedido, confirma con el cliente los platillos, las cantidades y el método de pago.
- Si una herramienta responde ERROR, explica el motivo al cliente con tus palabras y ofrece una alternativa.
  No insistas con la misma operación ni intentes saltarte el rechazo.
- Si una operación es rechazada por la persona que aprueba, informa que no se realizó.

Alcance: solo atiendes la taquería (menú, pedidos, saldo y cancelaciones). Si preguntan por
cualquier otro tema, declina con amabilidad y recuerda en qué sí puedes ayudar."""

ACCIONES_CON_APROBACION = ["crear_pedido", "cancelar_pedido"]   # toda escritura


def crear_agente(modelo, checkpointer=None):
    return create_agent(
        model=modelo,
        tools=HERRAMIENTAS,
        system_prompt=PROMPT_SISTEMA,
        middleware=[HumanInTheLoopMiddleware(
            interrupt_on={accion: True for accion in ACCIONES_CON_APROBACION}
        )],
        checkpointer=checkpointer or InMemorySaver(),   # HITL requiere checkpointer
        context_schema=Contexto,
    )


def _texto(mensaje) -> str:
    c = mensaje.content
    if isinstance(c, str):
        return c
    return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in c)


def consola() -> None:
    load_dotenv()
    agente = crear_agente(init_chat_model(os.environ["MODELO"]), InMemorySaver())
    contexto = Contexto(servicio=cargar_servicio())
    # Un thread_id por conversación/cliente: así no se mezclan los hilos
    config = {"configurable": {"thread_id": input("Hilo (ej. mesa-1): ").strip() or "mesa-1"}}

    while True:
        texto = input("\nTú: ").strip()
        if texto.lower() in {"salir", "exit"}:
            break
        entrada = {"messages": [{"role": "user", "content": texto}]}
        try:
            while True:
                resultado = agente.invoke(entrada, config=config, context=contexto)
                pausas = resultado.get("__interrupt__")
                if not pausas:
                    break
                decisiones = []
                for accion in pausas[0].value["action_requests"]:
                    print(f"\n⏸️  El agente quiere ejecutar: {accion['name']}\n    Argumentos: {accion['args']}")
                    if input("    ¿Apruebas? [s/n]: ").strip().lower() == "s":
                        decisiones.append({"type": "approve"})
                    else:
                        decisiones.append({"type": "reject", "message": "La persona encargada rechazó la operación."})
                entrada = Command(resume={"decisions": decisiones})
            print(f"\nMesero: {_texto(resultado['messages'][-1])}")
        except Exception as e:   # la consola no debe caerse por un fallo del proveedor
            print(f"\n[Error técnico: {e}] Intenta de nuevo.")


if __name__ == "__main__":
    consola()
