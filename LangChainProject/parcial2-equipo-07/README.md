# Taquería El Buen Pastor — Agente LangChain (Equipo 07)

## Integrantes

| Rol | Nombre | Matrícula |
|---|---|---|
| Dominio (`dominio.py`, `test_equipo.py`) | [Nombre] | [Matrícula] |
| Herramientas (`herramientas.py`) | [Nombre] | [Matrícula] |
| Agente (`agente.py`, conversaciones, README) | [Nombre] | [Matrícula] |

## Escenario

Taquería "El Buen Pastor". Escenario propio (requiere autorización del profesor por escrito).

## Cómo correr

```bash
# pruebas
uv run pytest parcial2-equipo-07/pruebas
# consola
uv run python parcial2-equipo-07/agente.py
```

Sin `uv`, con el venv de la clase:

```bash
python -m pytest parcial2-equipo-07/pruebas
python parcial2-equipo-07/agente.py
```

Configurar `.env` a partir de `.env.example` y colocar la `GOOGLE_API_KEY`.

## Lo que se agregó más allá de lo pedido

- `consultar_pedido` (lectura).
- Pago `mixto`.
- `.env.example`, `.gitignore`.
- Pruebas de cableado del agente con modelo falso (aprobar/rechazar/memoria/lectura sin aprobación).
