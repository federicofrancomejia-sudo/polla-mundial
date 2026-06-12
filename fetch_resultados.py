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
    "bosnia": "Bosnia", "united states": "Estados Unidos", "usa": "Estados Unidos",
    "paraguay": "Paraguay", "qatar": "Catar", "switzerland": "Suiza", "brazil": "Brasil",
    "morocco": "Marruecos", "haiti": "Haití", "scotland": "Escocia", "australia": "Australia",
    "turkiye": "Turquía", "turkey": "Turquía", "germany": "Alemania", "curacao": "Curazao",
    "netherlands": "Países Bajos", "japan": "Japón", "cote divoire": "Costa de Marfil",
    "ivory coast": "Costa de Marfil", "ecuador": "Ecuador", "sweden": "Suecia",
    "tunisia": "Túnez", "spain": "España", "cape verde": "Cabo Verde", "cabo verde": "Cabo Verde",
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
    """Devuelve [(num_partido, gl, gv)] para los partidos FINALIZADOS que mapean."""
    out = []
    for m in api_json.get("matches", []):
        if m.get("status") != "FINISHED":
            continue
        ft = (m.get("score") or {}).get("fullTime") or {}
        gh, ga = ft.get("home"), ft.get("away")
        if gh is None or ga is None:
            continue
        h = a_nuestro((m.get("homeTeam") or {}).get("name"))
        a = a_nuestro((m.get("awayTeam") or {}).get("name"))
        if not h or not a:
            continue
        num = FIX.get((norm(h), norm(a)))
        if num:
            out.append((num, int(gh), int(ga)))
    return out


def main():
    key = os.environ.get("API_KEY")
    if not key:
        print("Falta API_KEY"); return
    r = requests.get(API_URL, headers={"X-Auth-Token": key}, timeout=30)
    r.raise_for_status()
    encontrados = mapear(r.json())
    for num, gh, ga in encontrados:
        db.set_resultado(num, gh, ga)
    print(f"Resultados actualizados: {len(encontrados)}")


if __name__ == "__main__":
    main()
