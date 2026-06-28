# -*- coding: utf-8 -*-
"""Trae del API los partidos de ELIMINATORIA y los escribe en la tabla 'partidos'
(num >= 73). Igual que fetch_resultados.py pero para el calendario: a medida que se
definen los clasificados, los partidos se van llenando solos. Lo corre el mismo
GitHub Action. Es SEGURO: solo escribe partidos cuyos DOS equipos ya estan definidos
y se traducen con confianza; los demas (aun 'por definir') se omiten y entran luego.
La fase de grupos (1-72) NO se toca: vive estatica en fixtures.py."""
import os

import requests

import db
from fetch_resultados import API_URL, a_nuestro  # reutiliza API y traduccion de nombres

# stage de la API -> etiqueta en espanol (con prettify generico para desconocidos)
ETIQUETAS = {
    "LAST_32": "Dieciseisavos", "ROUND_OF_32": "Dieciseisavos",
    "LAST_16": "Octavos", "ROUND_OF_16": "Octavos",
    "QUARTER_FINALS": "Cuartos", "QUARTER_FINAL": "Cuartos",
    "SEMI_FINALS": "Semifinal", "SEMI_FINAL": "Semifinal",
    "THIRD_PLACE": "3er puesto", "3RD_PLACE": "3er puesto",
    "FINAL": "Final",
}


def etiqueta(stage):
    return ETIQUETAS.get(stage) or (stage or "Eliminatoria").replace("_", " ").title()


def sincronizar(api_json):
    """Devuelve (nuevos, actualizados, omitidos[texto]). Escribe en la BD."""
    nuevos = actualizados = 0
    omitidos = []
    # ordenar por fecha+id para que la asignacion de numeros sea estable y cronologica
    elim = [m for m in api_json.get("matches", [])
            if m.get("stage") and m.get("stage") != "GROUP_STAGE"]
    elim.sort(key=lambda m: (str(m.get("utcDate") or ""), str(m.get("id") or "")))
    for m in elim:
        raw_h = (m.get("homeTeam") or {}).get("name")
        raw_a = (m.get("awayTeam") or {}).get("name")
        h = a_nuestro(raw_h)
        a = a_nuestro(raw_a)
        if not h or not a:
            # equipos aun por definir, o nombre sin traducir -> se intenta luego
            omitidos.append(f"{etiqueta(m.get('stage'))}: {raw_h} vs {raw_a}")
            continue
        api_id = str(m.get("id"))
        num = db.num_de_api(api_id)
        if num is None:
            num = db.siguiente_num_partido()
            nuevos += 1
        else:
            actualizados += 1
        db.upsert_partido(num, api_id, etiqueta(m.get("stage")), h, a,
                          m.get("venue") or "", m.get("utcDate"))
    return nuevos, actualizados, omitidos


def actualizar(api_key):
    r = requests.get(API_URL, headers={"X-Auth-Token": api_key}, timeout=30)
    r.raise_for_status()
    nuevos, actualizados, omitidos = sincronizar(r.json())
    if omitidos:
        print(f"Partidos de eliminatoria aun sin definir/mapear ({len(omitidos)}):")
        for t in omitidos:
            print("  -", t)
    print(f"Eliminatoria: {nuevos} nuevos, {actualizados} actualizados.")
    return nuevos, actualizados


def main():
    key = os.environ.get("API_KEY")
    if not key:
        print("Falta API_KEY"); return
    db.init_db([])  # asegura que exista la tabla partidos
    actualizar(key)


if __name__ == "__main__":
    main()
