from pathlib import Path
from html import escape
import base64
import streamlit as st
from demo_metrics import load_demo, metrics

ROOT = Path(__file__).resolve().parent


def number(v):
    return f"{int(v):,}"


def percent(v):
    return "—" if v is None else f"{v:.0f}%"


def measure(label, value, total, color="", rate=None):
    ratio = 100*value/total if total else 0
    shown = percent(ratio) if rate is None else rate
    return f'<div class="measure" title="{value} de {total}"><div class="measure-line"><span>{escape(label)}</span><strong>{number(value)} <span class="small">{shown}</span></strong></div><div class="track"><div class="fill {color}" style="width:{ratio}%"></div></div></div>'


def rate_measure(label, rate):
    return f'<div class="measure"><div class="measure-line"><span>{label}</span><strong>{percent(rate)}</strong></div><div class="track"><div class="fill sky" style="width:{rate or 0}%"></div></div></div>'


def render_board(m):
    month = m['month']
    colors = ["#69c7e8", "#3185d4", "#000077"]
    severity = ''.join(f'<div style="width:{100*v/m["anemia"] if m["anemia"] else 0}%;background:{color}"></div>' for v,color in zip(m['severity'].values(),colors))
    legend = ''.join(f'<span><i style="background:{color}"></i>{name} {percent(100*v/m["anemia"] if m["anemia"] else None)}</span>' for (name,v),color in zip(m['severity'].items(),colors))
    max_territory = max(m['territories'].values(), default=1)
    territories = ''.join(f'<div class="territory-bar"><span>{escape(name)}</span><div class="bar" style="width:{100*v/max_territory}%;background:{"#FC7100" if i==0 else "#000077"}"></div><strong>{v}</strong></div>' for i,(name,v) in enumerate(m['territories'].items()))
    return f'''<div class="board"><div class="board-head"><div><strong>Alerta Anemia</strong> · Dashboard regional</div><div class="chips"><span class="chip">Región: ejemplo</span><span class="chip">Período: Mes 0 – Mes {month}</span></div></div><div class="board-grid">
<section class="tile"><div class="tile-head"><b>COBERTURA</b><span>N.º y %</span></div>{measure('Niños elegibles',m['eligible'],m['eligible'])}{measure('Tamizados',m['screened'],m['eligible'])}{measure('Con evaluación final' if month == 3 else f'Con evaluación al Mes {month}',m['final'],m['screened'],'sky')}</section>
<section class="tile"><div class="tile-head"><b>DETECCIÓN</b><span>Mes 0</span></div><div class="data-pair"><div class="big">{m['anemia']}</div><div class="definition"><b>niños con anemia inicial</b><br><span class="small">{percent(m['prevalence'])} de los tamizados</span></div></div><div class="severity">{severity}</div><div class="legend">{legend}</div><div class="small">Ferritina y PCR realizadas: <b>{m['ferritin']}</b></div></section>
<section class="tile"><div class="tile-head"><b>ARTICULACIÓN</b><span>con el EESS</span></div><div class="data-pair"><div class="big">{percent(m['access'])}</div><div class="definition"><b>derivados con acceso<br>efectivo al EESS</b></div></div>{measure('Alertas resueltas',m['resolved'],m['alerts'],'sky',f"/ {m['alerts']}")}{measure('Parasitológicos realizados',m['parasitic'],m['indicated'],'sky',f"/ {m['indicated']}")}</section>
<section class="tile"><div class="tile-head"><b>ACOMPAÑAMIENTO</b><span>Mes 1 – Mes {month}</span></div><div class="two-figures"><div><div class="big">{number(m['calls'])}</div><span class="small">llamadas</span></div><div><div class="big">{number(m['visits'])}</div><span class="small">visitas</span></div></div>{rate_measure('Adherencia al tratamiento',m['adherence'])}{rate_measure('Completa los 3 meses' if month == 3 else f'Evaluación al Mes {month}',m['completion_rate'])}</section>
<section class="tile"><div class="tile-head"><b>RESULTADOS</b><span>Hb promedio, g/dL</span></div><div class="hb-change"><div><div class="big before">{m['hb0']:.1f}</div><span class="small">Mes 0</span></div><span class="arrow">→</span><div><div class="big">{m['hb3']:.1f}</div><span class="small">Mes {month}</span></div><span class="delta">▲ +{m['hb3']-m['hb0']:.1f}</span></div>{rate_measure(f'Con Hb normal al Mes {month}',m['normal']).replace('fill sky','fill')}<div class="small" style="margin-top:10px">Continúan en el EESS: <b>{percent(m['continues'])}</b></div></section>
<section class="tile"><div class="tile-head"><b>TERRITORIO</b><span>casos por distrito</span></div>{territories}<div class="footnote">Datos agregados, sin identificar a las personas</div></section>
</div></div>'''


def main():
    st.set_page_config(page_title="Nuestros Programas de Salud Pública", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(f"<style>{(ROOT/'assets/demo.css').read_text()}</style>", unsafe_allow_html=True)
    logo = base64.b64encode((ROOT/'assets/logo-blue.png').read_bytes()).decode()
    st.markdown(f'<div class="banner-shell"><div class="sa-nav"><img class="sa-logo" src="data:image/png;base64,{logo}" alt="Sistemas Analíticos"><span class="portal-tag">Salud Pública · Portal Interno</span></div><div class="public-hero"><div class="hero-content"><div class="eyebrow">COMPROMETIDOS CON LA COMUNIDAD</div><h1><span>Nuestros Programas de</span><em>Salud Pública</em></h1><p>Alcance y seguimiento de nuestras campañas para conocer su impacto en la comunidad.</p><div class="trust-row"><span>Cobertura territorial</span><span>Seguimiento mensual</span><span>Resultados agregados</span></div></div></div></div>', unsafe_allow_html=True)
    program = st.radio("Programa", ["Anemia", "Diabetes", "Otros"], horizontal=True, label_visibility="collapsed",key="demo_program")
    if program != "Anemia":
        st.subheader(program)
        st.info("Vista reservada. Pendiente de incorporar la base de este programa.")
        return
    d = load_demo()
    a,b,c = st.columns([1.4,1.4,.7],vertical_alignment="bottom")
    with a:
        district = st.selectbox("Territorio", ["Todos los distritos"]+sorted(d.distrito.unique()), key="demo_district")
    with b:
        if 'demo_month' not in st.session_state:
            st.session_state['demo_month'] = 'Mes 3'
        month_label = st.select_slider("Seguimiento acumulado",options=["Mes 1","Mes 2","Mes 3"],key="demo_month")
    with c:
        def reset():
            st.session_state['demo_district'] = 'Todos los distritos'
            st.session_state['demo_month'] = 'Mes 3'
        st.button("Restablecer",on_click=reset,width="stretch")
    month = int(month_label[-1])
    f = d if district == "Todos los distritos" else d[d.distrito.eq(district)]
    m = metrics(f,month)
    st.caption(f"{district} · Mes 0 a Mes {month} · {len(f):,} registros. Los indicadores se actualizan al cambiar la selección.")
    st.markdown(render_board(m),unsafe_allow_html=True)
    st.markdown(f'<div class="sa-footer"><span>Sistemas Analíticos · Programas de Salud Pública</span><span>Programa de Anemia · Mes 0 a Mes {month}</span></div>',unsafe_allow_html=True)
