from pathlib import Path
from html import escape
import base64
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from analytics import (load_data, filter_data, indicators, territory_summary, yes,
                       classified, known_no, operational_records, csv_bytes, AGE_ORDER)

ROOT = Path(__file__).resolve().parent
NAVY, ORANGE, TEAL, GRAY = "#000077", "#FC7100", "#149B91", "#DADCEB"
st.set_page_config(page_title="Nuestros Programas de Salud Pública", page_icon="🟠", layout="wide")
st.markdown(f"<style>{(ROOT / 'assets/style.css').read_text()}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def read_excel(content):
    return load_data(content)


def chart(fig, height=260):
    fig.update_layout(height=height, margin=dict(l=8, r=14, t=24, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Arial, sans-serif", size=12, color="#555572"),
                      showlegend=False)
    fig.update_xaxes(showgrid=False, zeroline=False, automargin=True)
    fig.update_yaxes(gridcolor="#eeeef5", zeroline=False, automargin=True)
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})


def kpi(label, value, note):
    st.markdown(f'<div class="kpi"><div class="kpi-label">{escape(label)}</div>'
                f'<div class="kpi-value">{escape(str(value))}</div>'
                f'<div class="kpi-note">{escape(note)}</div></div>', unsafe_allow_html=True)


def insight(text):
    st.markdown(f'<div class="insight">{text}</div>', unsafe_allow_html=True)


def panel_title(title, subtitle):
    st.subheader(title)
    st.caption(subtitle)


def clear_filter_state():
    for key in list(st.session_state):
        if key.startswith("filter_") or key == "dates":
            del st.session_state[key]


with st.sidebar:
    logo = base64.b64encode((ROOT / "assets/logo.png").read_bytes()).decode()
    st.markdown(f'<div class="brand"><img src="data:image/png;base64,{logo}" alt="Sistemas Analíticos"></div>', unsafe_allow_html=True)
    st.caption("PROGRAMAS DE SALUD PÚBLICA")
    program = st.radio("Programa", ["Anemia", "Diabetes", "Otros"], label_visibility="collapsed", key="program")
    st.divider()
    if program == "Anemia":
        st.markdown("**Fuente de información**")
        uploaded = st.file_uploader("Actualizar base de anemia", type=["xlsx"], help="Conserva las columnas del Excel original. Se procesa en esta sesión.", on_change=clear_filter_state)
        source = uploaded.name if uploaded else "BD_ANEMIA.xlsx"
        try:
            content = uploaded.getvalue() if uploaded else (ROOT / "data/BD_ANEMIA.xlsx").read_bytes()
            d = read_excel(content)
        except (ValueError, OSError, ImportError) as err:
            st.error(f"No se pudo cargar la base: {err}")
            st.stop()
        except Exception:
            st.error("El archivo no es un Excel válido o no se pudo leer. Vuelve a cargar un .xlsx.")
            st.stop()
        st.caption(f"{source} · {len(d):,} registros")
        st.divider()
        st.markdown("**Filtrar campaña**")
        selections = {}
        for col, label in [("departamento", "Departamento"), ("territorio", "Territorio"), ("campaña", "Campaña"), ("cliente", "Cliente"), ("grupo_edad", "Grupo de edad"), ("sexo", "Sexo")]:
            selections[col] = st.multiselect(label, sorted(d[col].dropna().unique()), key=f"filter_{col}")
        valid_dates = d.fecha_intervencion.dropna()
        date_range = None
        if not valid_dates.empty:
            date_range = st.date_input("Fecha de intervención", value=(valid_dates.min().date(), valid_dates.max().date()),
                                       min_value=valid_dates.min().date(), max_value=valid_dates.max().date(), key="dates")
        def reset_filters():
            for col in selections:
                st.session_state[f"filter_{col}"] = []
            if date_range is not None:
                st.session_state.pop("dates", None)
        st.button("Restablecer filtros", width="stretch", on_click=reset_filters)
    st.divider()
    st.markdown("[Sistemas Analíticos](https://www.sistemasanaliticos.com/)")
    st.caption("Información para gestionar el alcance y seguimiento de las campañas.")

st.markdown('<div class="hero"><div class="eyebrow">SISTEMAS ANALÍTICOS</div>'
            '<h1>Nuestros Programas de Salud Pública</h1>'
            '<p>Alcance, resultados y oportunidades para nuestras campañas.</p></div>', unsafe_allow_html=True)

if program != "Anemia":
    st.markdown(f'<div class="section-head">{escape(program)}</div>', unsafe_allow_html=True)
    st.markdown('<span class="status-pill">Pendiente de incorporar datos</span>', unsafe_allow_html=True)
    st.info("Esta vista está reservada para el programa. Los indicadores se habilitarán al incorporar su base de datos.")
    if program == "Diabetes":
        st.caption("Estructura propuesta a partir del dashboard de referencia.")
        for col, title, description in zip(st.columns(3), ["Cascada de atención", "Control glucémico", "Continuidad del cuidado"],
            ["Identificados, vinculados al EESS, en tratamiento y con seguimiento.",
             "HbA1c inicial y de control, con fechas y mediciones de las mismas personas.",
             "Adherencia registrada, entrega de resultados y barreras reportadas."]):
            with col, st.container(border=True):
                st.subheader(title)
                st.write(description)
        st.caption("Se necesita una base de Diabetes con identificador, territorio, fechas, etapas de atención y mediciones de seguimiento.")
    else:
        st.write("El tercer programa puede configurarse cuando se definan su nombre, población y objetivos.")
    st.stop()

if date_range is not None and len(date_range) != 2:
    st.info("Selecciona también la fecha final del período.")
    st.stop()
f = filter_data(d, selections, date_range)
st.markdown('<div class="section-head">Programa de Anemia</div>', unsafe_allow_html=True)
if date_range:
    period = f"{pd.Timestamp(date_range[0]):%d/%m/%Y} — {pd.Timestamp(date_range[1]):%d/%m/%Y}"
else:
    period = "Sin fechas válidas"
st.caption(f"Dashboard de campaña · {period} · {len(f)} de {len(d)} registros")
synthetic = d.registro_sintetico.fillna("").astype(str).str.contains("FICTICIO|SINT[EÉ]TICO", case=False, regex=True)
if synthetic.any():
    st.warning(f"Base de demostración: {int(synthetic.sum())} de {len(d)} registros marcados como ficticios. No usar para atención clínica.", icon="⚠️")
if f.empty:
    st.info("No hay registros para esta combinación de filtros. Cambia la selección o restablece los filtros.")
    st.stop()
m = indicators(f)
n = len(f)
cols = st.columns(4)
for col, args in zip(cols, [
    ("Personas registradas", m["personas"], f"{n} registros · {f.territorio.nunique()} territorios"),
    ("Hemoglobina registrada", f'{m["hb"] / n:.0%}', f'{m["hb"]} de {n} registros con Hb inicial'),
    ("Resultados entregados", f'{m["resultados"] / n:.0%}', f'{m["resultados"]} de {n} registros'),
    ("Consejería preventiva", f'{m["consejeria"] / n:.0%}', f'{m["consejeria"]} de {n} registros')]):
    with col:
        kpi(*args)
st.write("")
overview, territory, quality = st.tabs(["Resumen de campaña", "Territorios y seguimiento", "Calidad y metodología"])

with overview:
    left, right = st.columns([1.6, 1])
    with left, st.container(border=True):
        panel_title("Avance de la atención", "Coberturas independientes sobre los registros filtrados")
        labels = ["Registrados", "Con Hb inicial", "Resultado entregado", "Con consejería", "Resultado + consejería"]
        values = [n, m["hb"], m["resultados"], m["consejeria"], m["cierre"]]
        fig = go.Figure(go.Bar(x=labels, y=values, marker_color=[NAVY, NAVY, NAVY, ORANGE, TEAL],
                              text=[f"{v}<br>{v/n:.0%}" for v in values], textposition="outside", cliponaxis=False))
        fig.update_yaxes(range=[0, n * 1.3], title="Registros")
        chart(fig)
        st.caption("Las barras no implican etapas consecutivas. La última cuenta registros que cumplen ambos campos.")
    with right, st.container(border=True):
        panel_title("Oportunidades de seguimiento", "Pendientes operativos para gestionar la campaña")
        insight(f'<strong>{m["sin_resultado"]} resultados sin entregar</strong><br>Registros con entrega marcada como «No».')
        insight(f'<strong>{m["sin_consejeria"]} registros sin consejería</strong><br>Consejería preventiva marcada como «No».')
        insight(f'<strong>{m["sin_clasificacion"]} clasificaciones no disponibles</strong><br>Estado pendiente, ausente o no reconocido en la base.')
    a, b, c = st.columns([1, 1, 1.15])
    with a, st.container(border=True):
        panel_title("Población alcanzada", "Distribución por edad registrada")
        counts = f.grupo_edad.value_counts().reindex(AGE_ORDER, fill_value=0)
        counts = counts[counts > 0]
        chart(go.Figure(go.Bar(x=counts.values, y=counts.index, orientation="h", marker_color=NAVY,
                              text=counts.values, textposition="outside", cliponaxis=False)), 240)
    with b, st.container(border=True):
        panel_title("Hemoglobina inicial", "Distribución de valores registrados; unidad por confirmar")
        hb = f.hb_inicial.dropna()
        if hb.empty:
            st.info("No hay valores de hemoglobina inicial.")
        else:
            chart(go.Figure(go.Histogram(x=hb, nbinsx=12, marker_color=ORANGE)), 240)
            st.caption(f"Mediana: {hb.median():.1f} · {len(hb)} mediciones. No representa una clasificación de anemia.")
    with c, st.container(border=True):
        panel_title("Actividad por mes", "Entrega y consejería entre registros de cada mes")
        monthly = f.assign(Mes=f.fecha_intervencion.dt.to_period("M").astype(str),
                           Entrega=yes(f.resultado_entregado).astype(int),
                           Consejería=yes(f.consejeria_preventiva).astype(int))
        monthly = monthly[f.fecha_intervencion.notna()].groupby("Mes").agg(
            Registros=("id_sisa", "size"), Entrega=("Entrega", "sum"), Consejería=("Consejería", "sum"))
        fig = go.Figure()
        for label, color in [("Entrega", NAVY), ("Consejería", ORANGE)]:
            fig.add_trace(go.Scatter(x=monthly.index, y=100 * monthly[label] / monthly.Registros,
                                     mode="lines+markers", name=label, line=dict(color=color, width=3)))
        chart(fig, 240)
        # chart() applies common defaults, so render the legend via a compact caption.
        st.caption("Azul: entrega (%) · Naranja: consejería (%). Cada mes tiene su propia población; no mide evolución clínica.")

with territory:
    t = territory_summary(f)
    l, r = st.columns([1.25, 1])
    with l, st.container(border=True):
        panel_title("Dónde reforzar la entrega", "Territorios ordenados por número de resultados sin entregar")
        top = t.head(10).iloc[::-1]
        chart(go.Figure(go.Bar(x=top["Pendientes de entrega"], y=top.Territorio.str.replace("|", " / ", regex=False),
                              orientation="h", marker_color=ORANGE, text=top["Pendientes de entrega"],
                              textposition="outside", cliponaxis=False)), 350)
    with r, st.container(border=True):
        panel_title("Prioridad de campaña", "Una oportunidad basada en el volumen pendiente")
        first = t.iloc[0]
        if first["Pendientes de entrega"] > 0:
            insight(f'<strong>{escape(first.Territorio.replace("|", " / "))}</strong><br>'
                    f'{first["Pendientes de entrega"]} resultados sin entregar entre {first.Registros} registros.')
        else:
            st.success("No hay entregas marcadas como «No» en los territorios filtrados.")
        st.metric("Resultado y consejería registrados", f'{m["cierre"] / n:.0%}', help="Intersección: ambos campos marcados Sí / registros filtrados.")
        st.caption(f'{m["cierre"]} de {n} registros. Las brechas pueden superponerse; no deben sumarse como personas distintas.')
    st.dataframe(t, hide_index=True, width="stretch")
    st.download_button("Descargar resumen territorial", csv_bytes(t), "resumen_territorial.csv", "text/csv")
    with st.expander("Registros para seguimiento"):
        status = st.selectbox("Mostrar", ["Todos", "Resultado sin entregar", "Sin consejería", "Clasificación no disponible"])
        detail = f
        if status == "Resultado sin entregar":
            detail = f[known_no(f.resultado_entregado)]
        elif status == "Sin consejería":
            detail = f[known_no(f.consejeria_preventiva)]
        elif status == "Clasificación no disponible":
            detail = f[~classified(f.clasificacion_anemia)]
        records = operational_records(detail)
        st.caption("Se muestran identificadores de registro. No se incluyen nombres, documentos, teléfonos ni direcciones.")
        st.dataframe(records, hide_index=True, width="stretch")
        st.download_button("Descargar seguimiento filtrado", csv_bytes(records), "seguimiento_anemia.csv", "text/csv")

with quality:
    l, r = st.columns([1.2, 1])
    with l, st.container(border=True):
        panel_title("Disponibilidad de datos", "Valores presentes sobre los registros filtrados")
        fields = {"Hb inicial": "hb_inicial", "Hb ajustada": "hb_ajustada", "Ferritina inicial": "ferritina_inicial",
                  "PCR inicial": "pcr_inicial", "Altura registrada": "altura_departamento"}
        completeness = pd.DataFrame([{"Campo": label, "Disponibles": int(f[col].notna().sum()),
                                     "Sin dato": int(f[col].isna().sum()),
                                     "Cobertura (%)": round(100*f[col].notna().sum()/n, 1)} for label, col in fields.items()])
        st.dataframe(completeness, hide_index=True, width="stretch")
        st.caption("La ausencia de ferritina o PCR no implica por sí sola incumplimiento: la indicación está pendiente en esta base.")
    with r, st.container(border=True):
        panel_title("Validaciones de registro", "Observaciones del archivo cargado completo")
        st.write(f"• Identificadores repetidos: {int(d.id_sisa.dropna().duplicated().sum())}")
        st.write(f"• Identificadores ausentes: {int(d.id_sisa.isna().sum())}")
        st.write(f"• Fechas inválidas o ausentes: {int(d.fecha_intervencion.isna().sum())}")
        st.write(f"• Edades negativas o ausentes: {int((d.edad_meses.isna() | d.edad_meses.lt(0)).sum())}")
        unknown_delivery = ~(yes(d.resultado_entregado) | known_no(d.resultado_entregado))
        st.write(f"• Entrega sin respuesta Sí/No: {int(unknown_delivery.sum())}")
        st.caption("Se conservan los registros de origen. Los duplicados no se eliminan automáticamente.")
    with st.expander("Cómo se calculan los indicadores", expanded=True):
        st.markdown("""
- **Personas registradas:** identificadores `id_sisa` distintos y no vacíos. Requiere que el ID represente a una persona; si representa una atención, es un conteo de IDs.
- **Coberturas:** registros con el campo marcado «Sí» divididos entre todos los registros filtrados. Respuestas vacías o desconocidas no cuentan como «Sí» ni como «No».
- **Seguimiento pendiente:** registros con entrega o consejería marcada «No». Los conteos pueden superponerse.
- **Clasificación disponible:** categorías explícitas de la fuente (sin anemia/normal, leve, moderada o severa). Los estados pendientes no se convierten en diagnósticos.
- **Período:** fecha de intervención, incluyendo ambos extremos; no se infiere la fecha del nombre de campaña.
- **Hemoglobina:** se presenta el valor inicial, sin aplicar umbrales, corrección por altura ni fórmulas clínicas. Confirmar la unidad con el responsable de la base.

La base actual no permite medir recuperación, adherencia al tratamiento ni cambios a los tres meses. Para ello se necesitan mediciones y estados de seguimiento de las mismas personas.
""")
st.markdown('<div class="footer">Sistemas Analíticos · Programas de Salud Pública · Datos de la base cargada</div>', unsafe_allow_html=True)
