"""
Analiza qué campos varían dentro de cada nivel de la jerarquía:
    Marca → Modelo → Submodelo → Version

Uso:
    python analizar_variabilidad.py datos.json

El JSON puede ser:
  - Un array de objetos:  [ {...}, {...}, ... ]
  - Un objeto por línea (JSONL):  {...}\n{...}\n...
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


# ── Campos que mapean a cada nivel ───────────────────────────────────────────

CAMPOS_CANDIDATOS = {
    "marca":     ["marca"],
    "modelo":    ["marca", "modelo", "carroceria", "puertas", "plazas",
                  "longitud", "anchura", "altura", "capacidad_maletero"],
    "submodelo": ["marca", "modelo", "submodelo", "carroceria", "puertas",
                  "plazas", "longitud", "anchura", "altura", "capacidad_maletero",
                  "foto_url"],
    "version":   None,  # todo el resto
}

# Clave que identifica cada nivel (los valores que forman el "grupo")
NIVEL_KEYS = {
    "marca":     ("marca",),
    "modelo":    ("marca", "modelo"),
    "submodelo": ("marca", "modelo", "submodelo"),
}


# ── Carga del JSON (stream-friendly para ficheros grandes) ────────────────────

def cargar_registros(path: str):
    """Devuelve un iterador de dicts. Soporta array JSON y JSONL."""
    p = Path(path)
    raw = p.read_text(encoding="utf-8").strip()

    # Intenta como JSON normal primero
    if raw.startswith("["):
        data = json.loads(raw)
        yield from data
        return

    # JSONL (un objeto por línea)
    for linea in raw.splitlines():
        linea = linea.strip().rstrip(",")
        if linea.startswith("{"):
            try:
                yield json.loads(linea)
            except json.JSONDecodeError:
                pass


# ── Análisis de variabilidad ──────────────────────────────────────────────────

def analizar(path: str):
    # grupos[nivel][clave_grupo] = {campo: set(valores)}
    grupos = {
        nivel: defaultdict(lambda: defaultdict(set))
        for nivel in NIVEL_KEYS
    }

    n_registros = 0
    for reg in cargar_registros(path):
        n_registros += 1
        for nivel, key_fields in NIVEL_KEYS.items():
            clave = tuple(str(reg.get(k, "")) for k in key_fields)
            campos_a_revisar = CAMPOS_CANDIDATOS.get(nivel) or list(reg.keys())
            for campo in campos_a_revisar:
                valor = reg.get(campo)
                grupos[nivel][clave][campo].add(
                    str(valor) if valor is not None else "__null__"
                )

    print(f"\n{'─'*60}")
    print(f"  Registros procesados: {n_registros:,}")
    print(f"{'─'*60}\n")

    for nivel, key_fields in NIVEL_KEYS.items():
        agrupaciones = grupos[nivel]
        campos_candidatos = CAMPOS_CANDIDATOS.get(nivel) or []

        # Para cada campo, ¿cuántos grupos tienen más de un valor distinto?
        variabilidad: dict[str, list[tuple]] = defaultdict(list)
        for clave, campos in agrupaciones.items():
            for campo, valores in campos.items():
                if len(valores) > 1:
                    variabilidad[campo].append((clave, sorted(valores)))

        print(f"{'═'*60}")
        print(f"  NIVEL: {nivel.upper()}  (agrupado por {key_fields})")
        print(f"  Grupos distintos: {len(agrupaciones):,}")
        print(f"{'═'*60}")

        campos_revisados = campos_candidatos or sorted(
            {c for d in agrupaciones.values() for c in d}
        )

        for campo in campos_revisados:
            casos = variabilidad.get(campo, [])
            if not casos:
                print(f"  ✅  {campo:35s} → siempre igual dentro del grupo")
            else:
                pct = 100 * len(casos) / len(agrupaciones)
                print(f"  ⚠️   {campo:35s} → varía en {len(casos):>4} grupos "
                      f"({pct:.1f}%)")
                # Muestra hasta 3 ejemplos concretos
                for clave, vals in casos[:3]:
                    label = " / ".join(clave)
                    vals_str = ", ".join(vals[:6])
                    if len(vals) > 6:
                        vals_str += f" … (+{len(vals)-6} más)"
                    print(f"       Ej: [{label}]")
                    print(f"           valores: {vals_str}")
                if len(casos) > 3:
                    print(f"       … y {len(casos)-3} grupos más")
        print()


# ── Entrada ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python analizar_variabilidad.py <fichero.json>")
        sys.exit(1)
    analizar(sys.argv[1])