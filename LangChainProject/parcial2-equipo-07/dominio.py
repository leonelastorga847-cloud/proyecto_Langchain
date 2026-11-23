"""Reglas del negocio de la taquería. No importa LangChain."""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, time
from pathlib import Path

ESCENARIO = "taqueria"
RUTA_DATOS = Path(__file__).with_name("datos.json")
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
MAX_POR_PLATILLO = 10
METODOS_PAGO = ("saldo", "mixto")


class ErrorDeNegocio(Exception):
    """Una regla no se cumple. Si se lanza, NO se cambió ningún dato."""


class ServicioTaqueria:
    def __init__(self, datos: dict):
        self._d = deepcopy(datos)          # el estado vive en memoria, no en datos.json

    # ---------- utilidades ----------
    def snapshot(self) -> dict:
        """Copia del estado; útil en pruebas para comprobar que nada cambió."""
        return deepcopy(self._d)

    def _ahora(self) -> datetime:
        return datetime.fromisoformat(self._d["ahora"])    # nunca datetime.now()

    def _dia(self) -> str:
        return DIAS[self._ahora().weekday()]

    def _cliente(self, cliente_id: str) -> dict:
        try:
            return self._d["clientes"][cliente_id]
        except KeyError:
            raise ErrorDeNegocio(f"No existe el cliente '{cliente_id}'.") from None

    def _disponible_hoy(self, platillo: dict) -> bool:
        return platillo["dias"] is None or self._dia() in platillo["dias"]

    def validar_horario(self) -> None:                                  # H1
        h = self._d["horario"]
        apertura = time.fromisoformat(h["apertura"])
        ultima = time.fromisoformat(h["ultima_orden"])
        if not (apertura <= self._ahora().time() < ultima):
            raise ErrorDeNegocio(
                f"La cocina está cerrada. Recibimos pedidos de {h['apertura']} a {h['ultima_orden']}."
            )

    # ---------- lecturas ----------
    def consultar_menu(self) -> list[dict]:                             # M1, M2
        return [
            {"id": pid, "nombre": p["nombre"], "precio": p["precio"],
             "existencias": self._d["inventario"].get(pid, 0)}
            for pid, p in self._d["menu"].items() if self._disponible_hoy(p)
        ]

    def verificar_saldo(self, cliente_id: str) -> dict:
        c = self._cliente(cliente_id)
        return {"cliente_id": cliente_id, "nombre": c["nombre"], "saldo": c["saldo"]}

    def consultar_pedido(self, cliente_id: str, pedido_id: str) -> dict:
        self._cliente(cliente_id)
        ped = self._d["pedidos"].get(pedido_id)
        if not ped or ped["cliente_id"] != cliente_id:
            raise ErrorDeNegocio("No encontré un pedido con ese número a tu nombre.")
        return {"pedido_id": pedido_id, **ped}

    # ---------- escrituras ----------
    def crear_pedido(self, cliente_id: str, items: list[dict], metodo_pago: str = "saldo") -> dict:
        # P3
        cliente = self._cliente(cliente_id)
        # método de pago
        if metodo_pago not in METODOS_PAGO:
            raise ErrorDeNegocio("Método de pago inválido. Usa 'saldo' o 'mixto'.")
        # P1: al menos un renglón
        if not items:
            raise ErrorDeNegocio("El pedido debe tener al menos un platillo.")
        # P1: cantidades enteros positivos
        for it in items:
            cant = it.get("cantidad") if isinstance(it, dict) else None
            if not isinstance(cant, int) or isinstance(cant, bool) or cant <= 0:
                raise ErrorDeNegocio("La cantidad debe ser un entero mayor a cero.")
        # H1
        self.validar_horario()

        # agregación de renglones repetidos
        cantidades: dict[str, int] = {}
        for it in items:
            pid = it.get("platillo_id") if isinstance(it, dict) else None
            cant = it.get("cantidad")
            cantidades[pid] = cantidades.get(pid, 0) + cant

        total = 0
        for pid, cant in cantidades.items():
            # P4
            if pid not in self._d["menu"]:
                raise ErrorDeNegocio(f"No existe el platillo '{pid}'.")
            p = self._d["menu"][pid]
            # M1, M2
            if not self._disponible_hoy(p):
                if p.get("dias"):
                    raise ErrorDeNegocio(f"El {p['nombre'].lower()} solo se sirve los {', '.join(p['dias'])}.")
                raise ErrorDeNegocio(f"{p['nombre']} no está disponible hoy.")
            # P2
            if cant > MAX_POR_PLATILLO:
                raise ErrorDeNegocio(f"Máximo {MAX_POR_PLATILLO} por platillo.")
            # S1
            disponibles = self._d["inventario"].get(pid, 0)
            if cant > disponibles:
                raise ErrorDeNegocio(f"Solo quedan {disponibles} de {p['nombre']}.")
            total += p["precio"] * cant

        saldo = cliente["saldo"]
        # PG2
        if metodo_pago == "saldo" and saldo < total:
            raise ErrorDeNegocio(
                f"Saldo insuficiente: el pedido cuesta ${total} y tu saldo es ${saldo} "
                f"(faltan ${total - saldo}). Puedes pagar de forma mixta."
            )
        # PG1, PG3
        con_saldo = total if metodo_pago == "saldo" else min(saldo, total)
        en_efectivo = total - con_saldo

        # --- todo validado: ahora sí se modifica (S2) ---
        for pid, cant in cantidades.items():
            self._d["inventario"][pid] -= cant
        cliente["saldo"] -= con_saldo                                   # PG4
        pedido_id = f"P{len(self._d['pedidos']) + 1:03d}"
        self._d["pedidos"][pedido_id] = {
            "cliente_id": cliente_id, "estado": "activo",
            "items": [{"platillo_id": p, "cantidad": c} for p, c in cantidades.items()],
            "total": total, "pagado_saldo": con_saldo, "pagado_efectivo": en_efectivo,
        }
        return {"pedido_id": pedido_id, "total": total, "pagado_con_saldo": con_saldo,
                "pagado_en_efectivo": en_efectivo, "saldo_restante": cliente["saldo"]}

    def cancelar_pedido(self, cliente_id: str, pedido_id: str) -> dict:
        cliente = self._cliente(cliente_id)
        ped = self._d["pedidos"].get(pedido_id)
        if not ped or ped["cliente_id"] != cliente_id:                  # C1
            raise ErrorDeNegocio("No encontré un pedido activo con ese número a tu nombre.")
        if ped["estado"] == "cancelado":                                # C3
            raise ErrorDeNegocio("Ese pedido ya estaba cancelado.")
        if ped["estado"] != "activo":
            raise ErrorDeNegocio("No encontré un pedido activo con ese número a tu nombre.")
        for it in ped["items"]:                                         # C2
            self._d["inventario"][it["platillo_id"]] += it["cantidad"]
        cliente["saldo"] += ped["pagado_saldo"]
        ped["estado"] = "cancelado"
        return {"pedido_id": pedido_id, "saldo_devuelto": ped["pagado_saldo"],
                "efectivo_a_devolver_en_caja": ped["pagado_efectivo"],
                "saldo_actual": cliente["saldo"]}


def cargar_servicio(ruta: str | Path | None = None) -> ServicioTaqueria:
    with open(ruta or RUTA_DATOS, encoding="utf-8") as f:
        return ServicioTaqueria(json.load(f))
