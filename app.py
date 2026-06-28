# -*- coding: utf-8 -*-
"""Polla Mundial 2026 - App web (Streamlit). Mobile-friendly."""
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

import db
import fixtures
from fixtures import PARTIDOS, TZ, por_num

# ===== Configuración =====
# Los participantes viven en la base de datos (no en el código), así el repo
# queda sin datos personales. Se siembran al migrar desde el Excel.
BOLSA_UNIT = 50000

st.set_page_config(page_title="Polla Mundial 2026", page_icon="🏆", layout="centered")
db.init_db([])  # asegura que existan las tablas (no siembra nombres)


@st.cache_data(ttl=600, show_spinner=False)
def _refrescar_calendario(_ventana):
    """Cada ~10 min relee de la BD los partidos de eliminatoria que haya agregado
    fetch_partidos.py, sin necesidad de reiniciar el worker ni redesplegar.
    Muta PARTIDOS en sitio; cacheado por ventana de 10 min para no golpear la BD."""
    fixtures.recargar()
    return _ventana


_refrescar_calendario(int(time.time() // 600))


def now_co():
    return datetime.now(TZ)


def puntos(pred, real):
    if not pred or not real:
        return None
    pgl, pgv = pred
    rgl, rgv = real
    if None in (pgl, pgv, rgl, rgv):
        return None
    if pgl == rgl and pgv == rgv:
        return 3
    sg = lambda x: (x > 0) - (x < 0)
    if sg(pgl - pgv) == sg(rgl - rgv):
        return 1 if pgl == pgv else 2
    return 0


def proximo_partido(now):
    fut = [p for p in PARTIDOS if p["kickoff"] > now]
    return min(fut, key=lambda p: p["kickoff"]) if fut else None


# ===== Login =====
def login_view():
    st.title("🏆 Polla Mundial 2026")
    st.caption("Ingresa para apostar y ver el ranking.")
    nombre = st.selectbox("Tu nombre", db.lista_participantes())
    pin = st.text_input("Tu PIN (créalo en tu primer ingreso)", type="password")
    if st.button("Entrar", type="primary", width="stretch"):
        ok, msg = db.login(nombre, pin)
        if ok:
            st.session_state.user = nombre
            st.rerun()
        else:
            st.error(msg)
    st.info("💡 La primera vez que entras, el PIN que escribas queda como tu clave.")


# ===== Contador (se actualiza solo cada segundo) =====
@st.fragment(run_every=1)
def contador():
    now = now_co()
    prox = proximo_partido(now)
    if prox is None:
        st.success("✅ Fase de grupos finalizada")
        return
    seg = int((prox["kickoff"] - now).total_seconds())
    d, r = divmod(seg, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    falta = (f"{d}d " if d else "") + f"{h:02d}:{m:02d}:{s:02d}"
    st.markdown(
        f"<div style='text-align:center;background:#C00000;color:#fff;padding:10px;border-radius:10px'>"
        f"<div style='font-size:13px'>⏱ PRÓXIMO PARTIDO — cierra en</div>"
        f"<div style='font-size:30px;font-weight:bold'>{falta}</div>"
        f"<div style='font-size:15px'>{prox['local']} vs {prox['visitante']}"
        f" · {prox['dia_txt']} {prox['hora_txt']}</div></div>",
        unsafe_allow_html=True)


# ===== Apuestas =====
def apuestas_view(user):
    now = now_co()
    mis = db.get_apuestas(user)
    res = db.get_resultados()

    if "msg_ok" in st.session_state:
        st.success(st.session_state.pop("msg_ok"))

    contador()
    st.write("")

    # Pendientes de HOY
    hoy = now.date()
    pend_hoy = [p for p in PARTIDOS
                if p["kickoff"].date() == hoy and p["kickoff"] > now and p["num"] not in mis]
    if pend_hoy:
        nombres = ", ".join(f"{p['local']} vs {p['visitante']}" for p in pend_hoy)
        st.warning(f"⚠️ Te faltan por apostar HOY: {nombres}")

    st.subheader("⚽ Mis apuestas")
    st.caption("Pon los goles y dale **Confirmar** en cada partido. Se cierra a su hora de inicio.")

    dias = sorted({p["kickoff"].date() for p in PARTIDOS})
    for dia in dias:
        ps = [p for p in PARTIDOS if p["kickoff"].date() == dia]
        with st.expander(f"📅 {ps[0]['dia_txt']}  ({len(ps)} partidos)", expanded=(dia == hoy)):
            for p in ps:
                n = p["num"]
                pred = mis.get(n)
                if p["kickoff"] <= now:   # CERRADO
                    ap = f"{pred[0]}-{pred[1]}" if pred else "sin apuesta"
                    rr = res.get(n)
                    extra = ""
                    if rr:
                        pt = puntos(pred, rr)
                        extra = f"  ·  resultado {rr[0]}-{rr[1]}  ·  **{pt if pt is not None else 0} pts**"
                    st.markdown(f"🔒 **{p['local']} vs {p['visitante']}** · {p['hora_txt']}")
                    st.caption(f"CERRADO — tu apuesta: {ap}{extra}")
                else:                     # ABIERTO -> mini formulario con Confirmar
                    with st.form(f"f_{n}", border=True):
                        st.markdown(f"**{p['local']} vs {p['visitante']}**  ·  {p['hora_txt']}")
                        if pred:
                            st.caption(f"✅ Confirmada: {pred[0]}-{pred[1]}  (puedes cambiarla)")
                        c1, c2 = st.columns(2)
                        gl = c1.number_input(p["local"], min_value=0, max_value=20, step=1,
                                             value=(pred[0] if pred else None),
                                             key=f"gl_{n}", placeholder="-")
                        gv = c2.number_input(p["visitante"], min_value=0, max_value=20, step=1,
                                             value=(pred[1] if pred else None),
                                             key=f"gv_{n}", placeholder="-")
                        ok = st.form_submit_button("✅ Confirmar apuesta", type="primary",
                                                   width="stretch")
                    if ok:
                        if p["kickoff"] <= now_co():
                            st.error("⏰ Este partido ya cerró, no se puede confirmar.")
                        elif gl is None or gv is None:
                            st.warning("Pon los dos goles antes de confirmar.")
                        else:
                            db.set_apuesta(user, n, int(gl), int(gv))
                            st.session_state["msg_ok"] = (
                                f"✓ {p['local']} {int(gl)}-{int(gv)} {p['visitante']} — ¡apuesta confirmada!")
                            st.rerun()


# ===== Ranking =====
def calcular_ranking():
    todas = db.todas_apuestas()
    res = db.get_resultados()
    filas = []
    for nombre in db.lista_participantes():
        ap = todas.get(nombre, {})
        tot = ex = apu = 0
        for n, pred in ap.items():
            if pred[0] is not None and pred[1] is not None:
                apu += 1
            pt = puntos(pred, res.get(n))
            if pt is not None:
                tot += pt
                ex += (pt == 3)
        filas.append({"Participante": nombre, "Puntos": tot, "Exactos": ex, "Apostados": apu})
    filas.sort(key=lambda f: (-f["Puntos"], -f["Exactos"], f["Participante"]))
    for i, f in enumerate(filas, 1):
        f["Puesto"] = i
    return filas


def ranking_view(user):
    st.subheader("📊 Ranking general")
    filas = calcular_ranking()
    res = db.get_resultados()
    st.caption(f"Partidos con resultado cargado: {len(res)}")
    df = pd.DataFrame(filas)[["Puesto", "Participante", "Puntos", "Exactos", "Apostados"]]
    yo = df[df["Participante"] == user]
    if not yo.empty:
        r = yo.iloc[0]
        st.metric(f"Tu posición ({user})", f"#{int(r['Puesto'])}", f"{int(r['Puntos'])} pts")
    st.dataframe(df, hide_index=True, width="stretch")

    # --- Resultados de los partidos jugados ---
    st.markdown("### 📋 Resultados")
    rr_rows = [{"#": p["num"], "Partido": f"{p['local']} vs {p['visitante']}",
                "Resultado": f"{res[p['num']][0]}-{res[p['num']][1]}"}
               for p in PARTIDOS if p["num"] in res]
    if rr_rows:
        st.dataframe(pd.DataFrame(rr_rows), hide_index=True, width="stretch")
    else:
        st.caption("Aún no hay resultados cargados.")

    # --- Mi detalle: resultado vs mi apuesta + puntos ---
    st.markdown(f"### 🧾 Mi detalle — {user}")
    mis = db.get_apuestas(user)
    det = []
    for p in PARTIDOS:
        if p["num"] not in res:
            continue
        rr = res[p["num"]]
        ap = mis.get(p["num"])
        pt = puntos(ap, rr)
        det.append({"Partido": f"{p['local']} vs {p['visitante']}",
                    "Resultado": f"{rr[0]}-{rr[1]}",
                    "Tu apuesta": f"{ap[0]}-{ap[1]}" if ap else "—",
                    "Pts": pt if pt is not None else 0})
    if det:
        df_det = pd.DataFrame(det)
        st.dataframe(df_det, hide_index=True, width="stretch")
        st.caption(f"Total: {sum(d['Pts'] for d in det)} pts en {len(det)} partidos jugados.")
    else:
        st.caption("Cuando haya resultados, aquí verás tu apuesta vs el marcador real y tus puntos.")


# ===== Apuestas de todos (público — transparencia) =====
def apuestas_todos_view():
    st.subheader("👀 Apuestas de todos")
    st.caption("Mira lo que va apostando cada quien, partido por partido. Total transparencia.")
    prox = proximo_partido(now_co())
    idx = (prox["num"] - 1) if prox else 0
    num = st.selectbox("Partido", [p["num"] for p in PARTIDOS],
                       index=idx, format_func=_label, key="todos_num")
    p = por_num(num)
    res = db.get_resultados().get(num)
    if p["kickoff"] <= now_co():
        estado = "🔒 CERRADO"
    else:
        estado = f"🟢 ABIERTO — cierra {p['dia_txt']} {p['hora_txt']}"
    if res:
        estado += f"  ·  resultado {res[0]}-{res[1]}"
    st.markdown(f"**{p['local']} vs {p['visitante']}** — {estado}")

    todas = db.todas_apuestas()
    filas = []
    for nombre in sorted(db.lista_participantes()):
        ap = _bet(num, nombre, todas)
        fila = {"Participante": nombre,
                "Apuesta": f"{ap[0]}-{ap[1]}" if ap else "⏳ pendiente"}
        if res:
            pt = puntos(ap, res)
            fila["Pts"] = pt if pt is not None else 0
        filas.append(fila)
    apostaron = sum(1 for f in filas if f["Apuesta"] != "⏳ pendiente")
    st.caption(f"Apostaron {apostaron} de {len(filas)}.")
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")


# ===== Generadores de mensajes (WhatsApp) =====
def _bet(num, nombre, todas):
    ap = todas.get(nombre, {}).get(num)
    if ap and ap[0] is not None and ap[1] is not None:
        return ap
    return None


def texto_apuestas(num):
    p = por_num(num)
    todas = db.todas_apuestas()
    con, faltan = [], []
    for nombre in sorted(db.lista_participantes()):
        ap = _bet(num, nombre, todas)
        (con if ap else faltan).append((nombre, ap))
    out = [f"⚽ APUESTAS — {p['local']} vs {p['visitante']} ({p['dia_txt']} {p['hora_txt']})", ""]
    out += [f"• {n}: {a[0]}-{a[1]}" for n, a in con]
    if faltan:
        out += ["", "⏳ Faltan: " + ", ".join(n for n, _ in faltan)]
    return "\n".join(out)


def texto_pendientes(num):
    p = por_num(num)
    todas = db.todas_apuestas()
    faltan = [n for n in sorted(db.lista_participantes()) if not _bet(num, n, todas)]
    if not faltan:
        return f"✅ Todos apostaron {p['local']} vs {p['visitante']}."
    out = [f"⏰ FALTAN por apostar {p['local']} vs {p['visitante']} (cierra {p['dia_txt']} {p['hora_txt']}):", ""]
    out += [f"👉 {n}" for n in faltan]
    return "\n".join(out)


def texto_ganadores(num):
    p = por_num(num)
    rr = db.get_resultados().get(num)
    if not rr:
        return "Aún no hay resultado cargado para este partido."
    todas = db.todas_apuestas()
    g = {3: [], 2: [], 1: [], 0: []}
    for nombre in sorted(db.lista_participantes()):
        pt = puntos(_bet(num, nombre, todas), rr)
        if pt is not None:
            g[pt].append(nombre)
    out = [f"⚽ {p['local']} {rr[0]}-{rr[1]} {p['visitante']}", ""]
    if g[3]:
        out += ["🎯 3 pts (exacto): " + ", ".join(g[3])]
    if g[2]:
        out += ["✅ 2 pts (ganador): " + ", ".join(g[2])]
    if g[1]:
        out += ["➕ 1 pt (empate): " + ", ".join(g[1])]
    if g[0]:
        out += ["⚪ 0 pts: " + ", ".join(g[0])]
    out += ["", "🏆 ACUMULADO"]
    for f in calcular_ranking():
        out.append(f"{f['Puesto']}. {f['Participante']} — {f['Puntos']} pts")
    return "\n".join(out)


def _label(num):
    p = por_num(num)
    return f"P{num} · {p['local']} vs {p['visitante']} ({p['dia_txt']} {p['hora_txt']})"


# ===== Admin =====
def admin_view():
    st.subheader("🛠️ Panel de administrador")
    res = db.get_resultados()
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📥 Resultados", "💬 Mensajes", "👥 Faltantes", "🧑‍🤝‍🧑 Personas"])

    # --- Cargar resultados ---
    with tab1:
        if st.button("🔄 Actualizar partidos y resultados ahora (desde la API)", type="primary", width="stretch"):
            key = st.secrets["API_KEY"] if "API_KEY" in st.secrets else None
            if not key:
                st.error("Falta API_KEY en los Secrets de la app (Settings → Secrets).")
            else:
                try:
                    import fetch_partidos
                    import fetch_resultados
                    nv, ac = fetch_partidos.actualizar(key)   # 1) eliminatorias
                    fixtures.recargar()                        # que aparezcan ya
                    _refrescar_calendario.clear()              # invalida el cache de 10 min
                    n = fetch_resultados.actualizar(key)       # 2) resultados
                    st.success(f"✅ Eliminatoria: {nv} nuevos, {ac} actualizados · "
                               f"Resultados: {n} traídos/actualizados.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo actualizar: {e}")
        st.caption("O escribe los goles a mano abajo. El ranking se actualiza solo.")
        dias = sorted({p["kickoff"].date() for p in PARTIDOS})
        with st.form("form_res"):
            for dia in dias:
                ps = [p for p in PARTIDOS if p["kickoff"].date() == dia]
                with st.expander(f"📅 {ps[0]['dia_txt']}", expanded=(dia == now_co().date())):
                    for p in ps:
                        n = p["num"]
                        rr = res.get(n)
                        st.markdown(f"**{p['local']} vs {p['visitante']}**")
                        c1, c2 = st.columns(2)
                        c1.number_input(p["local"], min_value=0, max_value=20, step=1,
                                        value=(rr[0] if rr else None), key=f"rgl_{n}",
                                        placeholder="-")
                        c2.number_input(p["visitante"], min_value=0, max_value=20, step=1,
                                        value=(rr[1] if rr else None), key=f"rgv_{n}",
                                        placeholder="-")
            g = st.form_submit_button("💾 Guardar resultados", type="primary", width="stretch")
        if g:
            for p in PARTIDOS:
                n = p["num"]
                gl = st.session_state.get(f"rgl_{n}")
                gv = st.session_state.get(f"rgv_{n}")
                db.set_resultado(n, None if gl is None else int(gl),
                                 None if gv is None else int(gv))
            st.success("✅ Resultados guardados.")
            st.rerun()

    # --- Mensajes para WhatsApp ---
    with tab2:
        st.caption("Elige un partido y copia el mensaje (botón de copiar arriba a la derecha de cada cuadro).")
        prox = proximo_partido(now_co())
        idx = (prox["num"] - 1) if prox else 0
        num = st.selectbox("Partido", [p["num"] for p in PARTIDOS],
                           index=idx, format_func=_label, key="msg_num")
        st.markdown("**📋 Apuestas del partido**")
        st.code(texto_apuestas(num), language=None)
        st.markdown("**⏰ Pendientes por cargar**")
        st.code(texto_pendientes(num), language=None)
        st.markdown("**🏆 Ganadores + Acumulado**")
        st.code(texto_ganadores(num), language=None)

    # --- Faltantes & control ---
    with tab3:
        prox = proximo_partido(now_co())
        idx = (prox["num"] - 1) if prox else 0
        num = st.selectbox("¿Quiénes faltan en el partido...?", [p["num"] for p in PARTIDOS],
                           index=idx, format_func=_label, key="falt_num")
        todas = db.todas_apuestas()
        faltan = [n for n in sorted(db.lista_participantes()) if not _bet(num, n, todas)]
        if faltan:
            st.warning(f"Faltan {len(faltan)} por apostar este partido:")
            st.write("  •  ".join(faltan))
        else:
            st.success("✅ Todos apostaron este partido.")
        st.divider()
        st.markdown("**Control general** (PIN creado y total de apuestas)")
        pins = db.con_pin()
        filas = [{"Participante": n, "¿PIN?": "Sí" if pins.get(n) else "No",
                  "Apostados": len(todas.get(n, {}))} for n in db.lista_participantes()]
        st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
        st.caption("Resetear PIN de alguien que lo olvidó:")
        quien = st.selectbox("Participante", db.lista_participantes(), key="reset_sel")
        if st.button("Resetear su PIN"):
            db.reset_pin(quien)
            st.success(f"PIN de {quien} reseteado. Creará uno nuevo en su próximo ingreso.")

    # --- Agregar / quitar personas ---
    with tab4:
        st.markdown("**➕ Agregar persona**")
        with st.form("add_pers", clear_on_submit=True):
            nuevo = st.text_input("Nombre y apellido", placeholder="Ej: Pedro Pérez")
            if st.form_submit_button("Agregar", type="primary"):
                ok, msg = db.agregar_participante(nuevo)
                (st.success if ok else st.error)(msg)
        st.divider()
        st.markdown("**🗑️ Quitar persona** (borra también todas sus apuestas)")
        candidatos = [n for n in db.lista_participantes() if not db.es_admin(n)]
        if candidatos:
            quitar = st.selectbox("Persona a quitar", candidatos, key="del_sel")
            conf = st.checkbox(f"Sí, quitar a {quitar} y todas sus apuestas", key="del_conf")
            if st.button("Quitar definitivamente", type="primary", disabled=not conf):
                ok, msg = db.eliminar_participante(quitar)
                (st.success if ok else st.error)(msg)
                st.rerun()
        else:
            st.caption("No hay personas para quitar.")
        st.divider()
        st.caption(f"Total participantes: {len(db.lista_participantes())}")


# ===== Main =====
def main():
    if "user" not in st.session_state:
        st.session_state.user = None
    if not st.session_state.user:
        login_view()
        return

    user = st.session_state.user
    with st.sidebar:
        st.markdown(f"👤 **{user}**")
        bolsa = BOLSA_UNIT * len(db.lista_participantes())
        st.caption(f"Bolsa: ${bolsa:,.0f}".replace(",", "."))
        st.caption(f"🥇 ${bolsa*.5:,.0f} · 🥈 ${bolsa*.3:,.0f} · 🥉 ${bolsa*.2:,.0f}".replace(",", "."))
        if st.button("Cerrar sesión"):
            st.session_state.user = None
            st.rerun()

    tabs = ["⚽ Apuestas", "📊 Ranking", "👀 Apuestas de todos"]
    if db.es_admin(user):
        tabs.append("🛠️ Admin")
    sel = st.tabs(tabs)
    with sel[0]:
        apuestas_view(user)
    with sel[1]:
        ranking_view(user)
    with sel[2]:
        apuestas_todos_view()
    if db.es_admin(user):
        with sel[3]:
            admin_view()


main()
