# -*- coding: utf-8 -*-
"""Trae los resultados del Mundial desde una API y los escribe en la base.
Lo corre GitHub Actions cada 30 min. Lee API_KEY y DATABASE_URL del entorno.
Es SEGURO: solo escribe partidos que mapea con confianza (los demas se omiten,
y se pueden cargar a mano desde el panel Admin)."""
import os
import unicodedata

import requests

import db
from fixtures import PARTIDOS

# football-data.org (plan gratis incluye el Mundial -> competicion "WC")
API_URL = os.environ.get("API_URL", "https://api.football-data.org/v4/competitions/WC/matches")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return " ".join("".join(c for c in s if c.isalnum() or c == " ").split())


# nombre (en ingles, varias formas posibles) -> nuestro nombre en espanol
ENG = {
    "mexico": "México", "south africa": "Sudáfrica",
    "korea republic": "Corea del Sur", "south korea": "Corea del Sur",
    "czechia": "República Checa", "czech republic": "República Checa",
    "canada": "Canadá", "bosnia and herzegovina": "Bosnia", "bosnia herzegovina": "Bosnia",
    # norm() borra el guion de "Bosnia-Herzegovina" y lo deja pegado -> "bosniaherzegovina"
    "bosniaherzegovina": "Bosnia",
    "bosnia": "Bosnia", "united states": "Estados Unidos", "usa": "Estados Unidos",
    "paraguay": "Paraguay", "qatar": "Catar", "switzerland": "Suiza", "brazil": "Brasil",
    "morocco": "Marruecos", "haiti": "Haití", "scotland": "Escocia", "australia": "Australia",
    "turkiye": "Turquía", "turkey": "Turquía", "germany": "Alemania", "curacao": "Curazao",
    "netherlands": "Países Bajos", "japan": "Japón", "cote divoire": "Costa de Marfil",
    "ivory coast": "Costa de Marfil", "ecuador": "Ecuador", "sweden": "Suecia",
    "tunisia": "Túnez", "spain": "España", "cape verde": "Cabo Verde", "cabo verde": "Cabo Verde",
    "cape verde islands": "Cabo Verde", "cabo verde islands": "Cabo Verde",
    "belgium": "Bélgica", "egypt": "Egipto", "saudi arabia": "Arabia Saudita", "uruguay": "Uruguay",
    "iran": "Irán", "ir iran": "Irán", "new zealand": "Nueva Zelanda", "france": "Francia",
    "senegal": "Senegal", "iraq": "Irak", "norway": "Noruega", "argentina": "Argentina",
    "algeria": "Argelia", "austria": "Austria", "jordan": "Jordania", "portugal": "Portugal",
    "congo dr": "RD Congo", "dr congo": "RD Congo", "democratic republic of congo": "RD Congo",
    "england": "Inglaterra", "croatia": "Croacia", "ghana": "Ghana", "panama": "Panamá",
    "uzbekistan": "Uzbekistán", "colombia": "Colombia",
}

# (local_norm, visitante_norm) -> numero de partido
FIX = {(norm(p["local"]), norm(p["visitante"])): p["num"] for p in PARTIDOS}


def a_nuestro(nombre_api):
    return ENG.get(norm(nombre_api))


def mapear(api_json):
    """Devuelve (mapeados, no_mapeados) para los partidos FINALIZADOS.
    mapeados = [(num_partido, gl, gv)] cruzados en CUALQUIER orden (si la API trae
      el local/visitante invertido, se intercambian los goles a nuestro orden).
    no_mapeados = [texto] de los FINISHED que no se pudieron cruzar, para diagnostico
      en el log (nombres crudos de la API)."""
    out, no_map = [], []
    for m in api_json.get("matches", []):
        if m.get("status") != "FINISHED":
            continue
        ft = (m.get("score") or {}).get("fullTime") or {}
        gh, ga = ft.get("home"), ft.get("away")
        raw_h = (m.get("homeTeam") or {}).get("name")
        raw_a = (m.get("awayTeam") or {}).get("name")
        if gh is None or ga is None:
            no_map.append(f"{raw_h} vs {raw_a}: FINISHED sin marcador")
            continue
        h = a_nuestro(raw_h)
        a = a_nuestro(raw_a)
        if not h or not a:
            falta = raw_h if not h else raw_a
            no_map.append(f"{raw_h} {gh}-{ga} {raw_a}: nombre sin traducir ('{falta}')")
            continue
        num = FIX.get((norm(h), norm(a)))
        if num:
            out.append((num, int(gh), int(ga)))
            continue
        # la API a veces trae el local/visitante al reves -> probar orden invertido
        num = FIX.get((norm(a), norm(h)))
        if num:
            out.append((num, int(ga), int(gh)))  # goles intercambiados a nuestro orden
            continue
        no_map.append(f"{h} {gh}-{ga} {a}: no esta en el fixture (en ningun orden)")
    return out, no_map


def actualizar(api_key):
    """Trae los resultados de la API y los escribe en la base. Devuelve cuantos."""
    r = requests.get(API_URL, headers={"X-Auth-Token": api_key}, timeout=30)
    r.raise_for_status()
    encontrados, no_map = mapear(r.json())
    for num, gh, ga in encontrados:
        db.set_resultado(num, gh, ga)
    if no_map:
        print(f"FINISHED que no se pudieron mapear ({len(no_map)}):")
        for t in no_map:
            print("  -", t)
    return len(encontrados)


def main():
    key = os.environ.get("API_KEY")
    if not key:
        print("Falta API_KEY"); return
    print(f"Resultados actualizados: {actualizar(key)}")


if __name__ == "__main__":
    main()
