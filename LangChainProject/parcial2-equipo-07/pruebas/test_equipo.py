import pytest
from dominio import ErrorDeNegocio, ServicioTaqueria, cargar_servicio


def test_H1_cocina_cerrada_2120(servicio_cocina_cerrada):
    antes = servicio_cocina_cerrada.snapshot()
    with pytest.raises(ErrorDeNegocio, match="cerrada"):
        servicio_cocina_cerrada.crear_pedido("C002", [{"platillo_id": "taco_pastor", "cantidad": 1}])
    assert servicio_cocina_cerrada.snapshot() == antes


def test_H1_acepta_2114(servicio_2114):
    r = servicio_2114.crear_pedido("C002", [{"platillo_id": "taco_pastor", "cantidad": 1}])
    assert r["total"] == 25


def test_H1_cerrada_1259(servicio_1259):
    antes = servicio_1259.snapshot()
    with pytest.raises(ErrorDeNegocio, match="cerrada"):
        servicio_1259.crear_pedido("C002", [{"platillo_id": "taco_pastor", "cantidad": 1}])
    assert servicio_1259.snapshot() == antes


def test_M1_pozole_martes_rechaza(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio, match="jueves"):
        servicio.crear_pedido("C002", [{"platillo_id": "pozole", "cantidad": 1}])
    assert servicio.snapshot() == antes


def test_M1_pozole_jueves_acepta(servicio_jueves):
    r = servicio_jueves.crear_pedido("C002", [{"platillo_id": "pozole", "cantidad": 1}])
    assert r["total"] == 95


def test_M2_menudo_entre_semana_rechaza(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio, match="menudo"):
        servicio.crear_pedido("C002", [{"platillo_id": "menudo", "cantidad": 1}])
    assert servicio.snapshot() == antes


def test_M2_menudo_sabado_acepta(servicio_sabado):
    r = servicio_sabado.crear_pedido("C002", [{"platillo_id": "menudo", "cantidad": 1}])
    assert r["total"] == 90


def test_P1_lista_vacia(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio):
        servicio.crear_pedido("C002", [])
    assert servicio.snapshot() == antes


def test_P1_cantidad_cero(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio, match="mayor a cero"):
        servicio.crear_pedido("C002", [{"platillo_id": "taco_pastor", "cantidad": 0}])
    assert servicio.snapshot() == antes


def test_P1_cantidad_negativa(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio, match="mayor a cero"):
        servicio.crear_pedido("C002", [{"platillo_id": "taco_pastor", "cantidad": -1}])
    assert servicio.snapshot() == antes


def test_P1_cantidad_no_entera(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio, match="mayor a cero"):
        servicio.crear_pedido("C002", [{"platillo_id": "taco_pastor", "cantidad": "dos"}])
    assert servicio.snapshot() == antes


def test_P2_mas_de_10(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio, match="Máximo"):
        servicio.crear_pedido("C002", [{"platillo_id": "taco_pastor", "cantidad": 11}])
    assert servicio.snapshot() == antes


def test_P2_renglones_repetidos_se_suman(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio, match="Máximo"):
        servicio.crear_pedido("C002", [
            {"platillo_id": "taco_pastor", "cantidad": 6},
            {"platillo_id": "taco_pastor", "cantidad": 6},
        ])
    assert servicio.snapshot() == antes


def test_P3_cliente_inexistente(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio, match="No existe el cliente"):
        servicio.crear_pedido("NOPE", [{"platillo_id": "taco_pastor", "cantidad": 1}])
    assert servicio.snapshot() == antes


def test_P4_platillo_inexistente(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio, match="No existe el platillo"):
        servicio.crear_pedido("C002", [{"platillo_id": "no_existe", "cantidad": 1}])
    assert servicio.snapshot() == antes


def test_S1_stock_insuficiente(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio, match="Solo quedan 3"):
        servicio.crear_pedido("C002", [{"platillo_id": "taco_lengua", "cantidad": 5}])
    assert servicio.snapshot() == antes


def test_S2_todo_o_nada(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio):
        servicio.crear_pedido("C002", [
            {"platillo_id": "taco_pastor", "cantidad": 1},
            {"platillo_id": "taco_lengua", "cantidad": 5},
        ])
    assert servicio.snapshot() == antes


def test_PG1_descuenta_total_saldo(servicio):
    r = servicio.crear_pedido("C001", [{"platillo_id": "taco_pastor", "cantidad": 2}])
    # 2 * 25 = 50, Ana saldo 100 -> 50
    assert r["total"] == 50
    assert r["pagado_con_saldo"] == 50
    assert r["pagado_en_efectivo"] == 0
    assert servicio.verificar_saldo("C001")["saldo"] == 50


def test_PG2_saldo_insuficiente(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio, match="faltan"):
        servicio.crear_pedido("C001", [{"platillo_id": "taco_pastor", "cantidad": 5}])  # 125 > 100
    assert servicio.snapshot() == antes


def test_PG3_mixto(servicio):
    r = servicio.crear_pedido("C001", [{"platillo_id": "taco_pastor", "cantidad": 5}], metodo_pago="mixto")
    # 5*25=125, saldo 100 -> 100 saldo + 25 efectivo
    assert r["total"] == 125
    assert r["pagado_con_saldo"] == 100
    assert r["pagado_en_efectivo"] == 25
    assert servicio.verificar_saldo("C001")["saldo"] == 0


def test_PG4_saldo_no_negativo(servicio):
    servicio.crear_pedido("C001", [{"platillo_id": "taco_pastor", "cantidad": 4}], metodo_pago="mixto")
    assert servicio.verificar_saldo("C001")["saldo"] == 0


def test_C1_pedido_ajeno_o_inexistente(servicio):
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio):
        servicio.cancelar_pedido("C001", "P001")
    assert servicio.snapshot() == antes
    with pytest.raises(ErrorDeNegocio):
        servicio.cancelar_pedido("C002", "P999")
    assert servicio.snapshot() == antes


def test_C2_devuelve_stock_y_saldo(servicio):
    # crear pedido con C002
    r = servicio.crear_pedido("C002", [{"platillo_id": "taco_pastor", "cantidad": 2}])
    pid = r["pedido_id"]
    stock_antes = [x for x in servicio.consultar_menu() if x["id"] == "taco_pastor"][0]["existencias"]
    saldo_antes = servicio.verificar_saldo("C002")["saldo"]
    res = servicio.cancelar_pedido("C002", pid)
    assert res["saldo_devuelto"] == r["pagado_con_saldo"]
    stock_despues = [x for x in servicio.consultar_menu() if x["id"] == "taco_pastor"][0]["existencias"]
    assert stock_despues == stock_antes + 2
    assert servicio.verificar_saldo("C002")["saldo"] == saldo_antes + r["pagado_con_saldo"]


def test_C3_cancelar_dos_veces(servicio):
    r = servicio.crear_pedido("C002", [{"platillo_id": "taco_pastor", "cantidad": 1}])
    pid = r["pedido_id"]
    servicio.cancelar_pedido("C002", pid)
    antes = servicio.snapshot()
    with pytest.raises(ErrorDeNegocio, match="ya estaba cancelado"):
        servicio.cancelar_pedido("C002", pid)
    assert servicio.snapshot() == antes


def test_consultar_pedido_ok(servicio):
    d = servicio.consultar_pedido("C002", "P001")
    assert d["pedido_id"] == "P001"
    assert d["estado"] == "activo"


def test_consultar_menu_no_muestra_pozole_martes(servicio):
    ids = [p["id"] for p in servicio.consultar_menu()]
    assert "pozole" not in ids
    assert "menudo" not in ids


# ---------- Agent wiring tests ----------
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from agente import crear_agente, ACCIONES_CON_APROBACION
from herramientas import Contexto
from dominio import cargar_servicio


class _FakeModel(BaseChatModel):
    messages: list
    idx: int = 0

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        msg = self.messages[self.idx]
        self.idx += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])

    @property
    def _llm_type(self):
        return "fake"

    def bind_tools(self, tools, **kwargs):
        return self


def test_agente_aprobar_escritura():
    svc = cargar_servicio()
    contexto = Contexto(servicio=svc)
    antes_stock = svc.snapshot()["inventario"]["taco_pastor"]
    modelo = _FakeModel(messages=[
        AIMessage(content="", tool_calls=[{"name": "crear_pedido", "args": {
            "cliente_id": "C001", "items": [{"platillo_id": "taco_pastor", "cantidad": 1}], "metodo_pago": "saldo"
        }, "id": "c1", "type": "tool_call"}]),
        AIMessage(content="Pedido creado"),
    ])
    agente = crear_agente(modelo, InMemorySaver())
    config = {"configurable": {"thread_id": "t-aprueba"}}
    res = agente.invoke({"messages": [{"role": "user", "content": "pide 1 taco"}]}, config=config, context=contexto)
    assert res.get("__interrupt__")
    res2 = agente.invoke(__import__("langgraph.types", fromlist=["Command"]).Command(resume={"decisions": [{"type": "approve"}]}), config=config, context=contexto)
    # stock descontado
    assert svc.snapshot()["inventario"]["taco_pastor"] == antes_stock - 1


def test_agente_rechazar_escritura():
    svc = cargar_servicio()
    contexto = Contexto(servicio=svc)
    antes_stock = svc.snapshot()["inventario"]["taco_pastor"]
    modelo = _FakeModel(messages=[
        AIMessage(content="", tool_calls=[{"name": "crear_pedido", "args": {
            "cliente_id": "C001", "items": [{"platillo_id": "taco_pastor", "cantidad": 1}], "metodo_pago": "saldo"
        }, "id": "c1", "type": "tool_call"}]),
        AIMessage(content="No se realizó"),
    ])
    agente = crear_agente(modelo, InMemorySaver())
    config = {"configurable": {"thread_id": "t-rechaza"}}
    agente.invoke({"messages": [{"role": "user", "content": "pide 1 taco"}]}, config=config, context=contexto)
    agente.invoke(__import__("langgraph.types", fromlist=["Command"]).Command(resume={"decisions": [{"type": "reject", "message": "no"}]}), config=config, context=contexto)
    assert svc.snapshot()["inventario"]["taco_pastor"] == antes_stock


def test_agente_memoria():
    from langchain_core.language_models.chat_models import BaseChatModel as BCM
    svc = cargar_servicio()
    contexto = Contexto(servicio=svc)

    class M(BCM):
        msgs: list
        idx: int = 0
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            # echo last user content length marker
            return __import__("langchain_core.outputs", fromlist=["ChatResult", "ChatGeneration"]).ChatResult(
                generations=[__import__("langchain_core.outputs", fromlist=["ChatGeneration"]).ChatGeneration(
                    message=AIMessage(content=f"memoria ok: {len(messages)} msgs"))])
        @property
        def _llm_type(self): return "fake"
        def bind_tools(self, tools, **kwargs): return self

    modelo = M(msgs=[])
    agente = crear_agente(modelo, InMemorySaver())
    config = {"configurable": {"thread_id": "t-mem"}}
    agente.invoke({"messages": [{"role": "user", "content": "hola"}]}, config=config, context=contexto)
    r2 = agente.invoke({"messages": [{"role": "user", "content": "y ahora?"}]}, config=config, context=contexto)
    # segunda invocación ve más mensajes por memoria
    assert "memoria ok" in r2["messages"][-1].content


def test_agente_lectura_no_pide_aprobacion():
    svc = cargar_servicio()
    contexto = Contexto(servicio=svc)
    modelo = _FakeModel(messages=[
        AIMessage(content="", tool_calls=[{"name": "consultar_menu", "args": {}, "id": "c1", "type": "tool_call"}]),
        AIMessage(content="menu mostrado"),
    ])
    agente = crear_agente(modelo, InMemorySaver())
    config = {"configurable": {"thread_id": "t-lectura"}}
    res = agente.invoke({"messages": [{"role": "user", "content": "menu"}]}, config=config, context=contexto)
    assert not res.get("__interrupt__")
