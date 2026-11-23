# Reglas del negocio — Taquería El Buen Pastor

Cada regla tiene un ID. Cada una tiene al menos una prueba en `pruebas/test_equipo.py` y cada rechazo comprueba que el estado no cambió. Montos en pesos enteros.

| ID | Regla | Mensaje de error (ejemplo) |
|---|---|---|
| **H1** | Se atiende de 13:00 a 21:30; la cocina recibe pedidos de 13:00 hasta **antes** de las 21:15 (`13:00 ≤ hora < 21:15`). | "La cocina está cerrada. Recibimos pedidos de 13:00 a 21:15." |
| **M1** | El **pozole** solo se sirve los jueves. | "El pozole solo se sirve los jueves." |
| **M2** | El **menudo** solo se sirve sábados y domingos. | "El menudo solo se sirve sábados y domingos." |
| **P1** | Un pedido tiene al menos un renglón; las cantidades son enteros positivos. | "La cantidad debe ser un entero mayor a cero." |
| **P2** | Máximo 10 unidades por platillo en un mismo pedido (se suman los renglones repetidos). | "Máximo 10 por platillo." |
| **P3** | El cliente debe existir. | "No existe el cliente 'X'." |
| **P4** | El platillo debe existir en el menú. | "No existe el platillo 'X'." |
| **S1** | No se pueden pedir más piezas que las existencias; el mensaje indica el máximo disponible. | "Solo quedan 3 de Tacos de lengua." |
| **S2** | El pedido es **todo o nada**: si un renglón falla, no se descuenta stock ni saldo de ninguno. | (el estado no cambia) |
| **PG1** | Pago con `saldo` (Tarjeta Taquera): requiere `saldo ≥ total` y descuenta el total. | — |
| **PG2** | Con `saldo` insuficiente se rechaza e indica cuánto falta y que existe el pago `mixto`. | "Saldo insuficiente: cuesta $150 y tienes $100 (faltan $50). Puedes pagar de forma mixta." |
| **PG3** | Pago `mixto`: se descuenta **todo** el saldo disponible y el resto se paga en efectivo en caja. | — |
| **PG4** | El saldo nunca queda negativo. | — |
| **C1** | Solo se cancela un pedido que existe, es del mismo cliente y está en estado `activo`. | "No encontré un pedido activo con ese número a tu nombre." |
| **C2** | Al cancelar se devuelve el stock y la parte pagada con saldo; la parte en efectivo se devuelve en caja (se informa). | — |
| **C3** | Un pedido ya cancelado no se puede cancelar otra vez. | "Ese pedido ya estaba cancelado." |

## Orden de validación en `crear_pedido`

cliente → método de pago → renglones (P1) → horario (H1) → platillo existe (P4) → disponible hoy (M1/M2) → máximo (P2) → stock (S1) → pago (PG).

## Escenario

Taquería "El Buen Pastor". Atención de 13:00 a 21:30, cocina recibe pedidos hasta antes de las 21:15. Fecha/hora fijas en `datos.json` (martes 14:00).
