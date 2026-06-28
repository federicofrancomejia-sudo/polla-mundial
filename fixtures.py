# -*- coding: utf-8 -*-
"""Calendario del Mundial 2026 - fase de grupos (72 partidos).
Horas en hora de Colombia (America/Bogota)."""
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Bogota")

# (jornada, grupo, dia_junio, hora, minuto, local, visitante, ciudad)
_RAW = [
    (1, "A", 11, 14, 0, "México", "Sudáfrica", "Ciudad de México"),
    (1, "A", 11, 21, 0, "Corea del Sur", "República Checa", "Guadalajara"),
    (1, "B", 12, 14, 0, "Canadá", "Bosnia", "Toronto"),
    (1, "D", 12, 20, 0, "Estados Unidos", "Paraguay", "Los Ángeles"),
    (1, "B", 13, 14, 0, "Catar", "Suiza", "San Francisco"),
    (1, "C", 13, 17, 0, "Brasil", "Marruecos", "Nueva York/NJ"),
    (1, "C", 13, 20, 0, "Haití", "Escocia", "Boston"),
    (1, "D", 13, 23, 0, "Australia", "Turquía", "Vancouver"),
    (1, "E", 14, 12, 0, "Alemania", "Curazao", "Houston"),
    (1, "F", 14, 15, 0, "Países Bajos", "Japón", "Dallas"),
    (1, "E", 14, 18, 0, "Costa de Marfil", "Ecuador", "Filadelfia"),
    (1, "F", 14, 21, 0, "Suecia", "Túnez", "Monterrey"),
    (1, "H", 15, 11, 0, "España", "Cabo Verde", "Atlanta"),
    (1, "G", 15, 14, 0, "Bélgica", "Egipto", "Seattle"),
    (1, "H", 15, 17, 0, "Arabia Saudita", "Uruguay", "Miami"),
    (1, "G", 15, 20, 0, "Irán", "Nueva Zelanda", "Los Ángeles"),
    (1, "I", 16, 14, 0, "Francia", "Senegal", "Nueva York/NJ"),
    (1, "I", 16, 17, 0, "Irak", "Noruega", "Boston"),
    (1, "J", 16, 20, 0, "Argentina", "Argelia", "Kansas City"),
    (1, "J", 16, 23, 0, "Austria", "Jordania", "San Francisco"),
    (1, "K", 17, 12, 0, "Portugal", "RD Congo", "Houston"),
    (1, "L", 17, 15, 0, "Inglaterra", "Croacia", "Dallas"),
    (1, "L", 17, 18, 0, "Ghana", "Panamá", "Toronto"),
    (1, "K", 17, 21, 0, "Uzbekistán", "Colombia", "Ciudad de México"),
    (2, "A", 18, 11, 0, "República Checa", "Sudáfrica", "Atlanta"),
    (2, "B", 18, 14, 0, "Suiza", "Bosnia", "Los Ángeles"),
    (2, "B", 18, 17, 0, "Canadá", "Catar", "Vancouver"),
    (2, "A", 18, 20, 0, "México", "Corea del Sur", "Guadalajara"),
    (2, "D", 19, 14, 0, "Estados Unidos", "Australia", "Seattle"),
    (2, "C", 19, 17, 0, "Escocia", "Marruecos", "Boston"),
    (2, "C", 19, 20, 0, "Brasil", "Haití", "Filadelfia"),
    (2, "D", 19, 23, 0, "Turquía", "Paraguay", "San Francisco"),
    (2, "F", 20, 14, 0, "Países Bajos", "Suecia", "Houston"),
    (2, "E", 20, 15, 0, "Alemania", "Costa de Marfil", "Toronto"),
    (2, "E", 20, 19, 0, "Ecuador", "Curazao", "Kansas City"),
    (2, "F", 20, 23, 0, "Túnez", "Japón", "Monterrey"),
    (2, "H", 21, 11, 0, "España", "Arabia Saudita", "Atlanta"),
    (2, "G", 21, 14, 0, "Bélgica", "Irán", "Los Ángeles"),
    (2, "H", 21, 17, 0, "Uruguay", "Cabo Verde", "Miami"),
    (2, "G", 21, 20, 0, "Nueva Zelanda", "Egipto", "Vancouver"),
    (2, "J", 22, 12, 0, "Argentina", "Austria", "Dallas"),
    (2, "I", 22, 16, 0, "Francia", "Irak", "Filadelfia"),
    (2, "I", 22, 19, 0, "Noruega", "Senegal", "Nueva York/NJ"),
    (2, "J", 22, 22, 0, "Jordania", "Argelia", "San Francisco"),
    (2, "K", 23, 12, 0, "Portugal", "Uzbekistán", "Houston"),
    (2, "L", 23, 15, 0, "Inglaterra", "Ghana", "Boston"),
    (2, "L", 23, 18, 0, "Panamá", "Croacia", "Toronto"),
    (2, "K", 23, 21, 0, "Colombia", "RD Congo", "Guadalajara"),
    (3, "B", 24, 14, 0, "Suiza", "Canadá", "Vancouver"),
    (3, "B", 24, 14, 0, "Bosnia", "Catar", "Seattle"),
    (3, "C", 24, 17, 0, "Escocia", "Brasil", "Miami"),
    (3, "C", 24, 17, 0, "Marruecos", "Haití", "Atlanta"),
    (3, "A", 24, 20, 0, "República Checa", "México", "Ciudad de México"),
    (3, "A", 24, 20, 0, "Sudáfrica", "Corea del Sur", "Monterrey"),
    (3, "E", 25, 15, 0, "Curazao", "Costa de Marfil", "Filadelfia"),
    (3, "E", 25, 15, 0, "Ecuador", "Alemania", "Nueva York/NJ"),
    (3, "F", 25, 18, 0, "Japón", "Suecia", "Dallas"),
    (3, "F", 25, 18, 0, "Túnez", "Países Bajos", "Kansas City"),
    (3, "D", 25, 21, 0, "Turquía", "Estados Unidos", "Los Ángeles"),
    (3, "D", 25, 21, 0, "Paraguay", "Australia", "San Francisco"),
    (3, "I", 26, 14, 0, "Noruega", "Francia", "Boston"),
    (3, "I", 26, 14, 0, "Senegal", "Irak", "Toronto"),
    (3, "H", 26, 19, 0, "Cabo Verde", "Arabia Saudita", "Houston"),
    (3, "H", 26, 19, 0, "Uruguay", "España", "Guadalajara"),
    (3, "G", 26, 22, 0, "Egipto", "Irán", "Seattle"),
    (3, "G", 26, 22, 0, "Nueva Zelanda", "Bélgica", "Vancouver"),
    (3, "L", 27, 16, 0, "Panamá", "Inglaterra", "Nueva York/NJ"),
    (3, "L", 27, 16, 0, "Croacia", "Ghana", "Filadelfia"),
    (3, "K", 27, 18, 30, "Colombia", "Portugal", "Miami"),
    (3, "K", 27, 18, 30, "RD Congo", "Uzbekistán", "Atlanta"),
    (3, "J", 27, 21, 0, "Argelia", "Austria", "Kansas City"),
    (3, "J", 27, 21, 0, "Jordania", "Argentina", "Dallas"),
]

DIAS = {0: "lun", 1: "mar", 2: "mié", 3: "jue", 4: "vie", 5: "sáb", 6: "dom"}
MESES = {5: "may", 6: "jun", 7: "jul", 8: "ago"}


def _dict_partido(num, jornada, grupo, local, visitante, ciudad, ko):
    """Arma el dict de un partido a partir de su kickoff (datetime con tz)."""
    return {
        "num": num, "jornada": jornada, "grupo": grupo, "local": local,
        "visitante": visitante, "ciudad": ciudad, "kickoff": ko,
        "dia_txt": f"{DIAS[ko.weekday()]} {ko.day:02d}-{MESES.get(ko.month, ko.strftime('%m'))}",
        "hora_txt": ko.strftime("%I:%M %p").lstrip("0").lower()
                      .replace("am", "a.m.").replace("pm", "p.m."),
    }


# Fase de grupos (1-72): estatica.
PARTIDOS_GRUPOS = []
for i, (j, g, d, h, m, loc, vis, ciu) in enumerate(_RAW, start=1):
    ko = datetime(2026, 6, d, h, m, tzinfo=TZ)
    PARTIDOS_GRUPOS.append(_dict_partido(i, j, g, loc, vis, ciu, ko))

assert len(PARTIDOS_GRUPOS) == 72


def _cargar_eliminatorias():
    """Lee de la BD los partidos de eliminatoria (num>=73) y los formatea.
    Best-effort: ante CUALQUIER fallo (BD caida, tabla inexistente, etc.) devuelve
    [] para que la app siga funcionando solo con la fase de grupos. Sin regresion."""
    try:
        import db
        out = []
        for r in db.partidos_eliminatoria():
            ko = datetime.fromisoformat(str(r["kickoff"]).replace("Z", "+00:00")).astimezone(TZ)
            out.append(_dict_partido(r["num"], r.get("etapa") or "Eliminatoria", "",
                                     r["local"], r["visitante"], r.get("ciudad") or "", ko))
        return out
    except Exception:
        return []


# Lista completa = grupos + eliminatorias (ordenada por num para que num-1 sea el indice).
PARTIDOS = sorted(PARTIDOS_GRUPOS + _cargar_eliminatorias(), key=lambda p: p["num"])
_POR_NUM = {p["num"]: p for p in PARTIDOS}


def por_num(n):
    return _POR_NUM.get(n)


def recargar():
    """Reconstruye PARTIDOS desde la BD (para llamar tras una sync de partidos)."""
    global PARTIDOS, _POR_NUM
    PARTIDOS = sorted(PARTIDOS_GRUPOS + _cargar_eliminatorias(), key=lambda p: p["num"])
    _POR_NUM = {p["num"]: p for p in PARTIDOS}
    return PARTIDOS
