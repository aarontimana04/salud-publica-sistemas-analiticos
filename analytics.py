"""Indicadores operativos. No calcula ni sustituye diagnósticos clínicos."""
from io import BytesIO
import unicodedata
import pandas as pd

REQUIRED = {
    "id_sisa", "fecha_intervencion", "cliente", "campaña", "territorio",
    "sexo", "edad_meses", "hb_inicial", "clasificacion_anemia",
    "consejeria_preventiva", "resultado_entregado", "elegible",
}
OPTIONAL = ["hb_ajustada", "ferritina_inicial", "pcr_inicial", "altura_departamento",
            "altitud_aplica", "pasa_gestiona", "grupo_edad_meses", "registro_sintetico", "eess_referencia"]
AGE_ORDER = ["00-05 meses", "06-11 meses", "12-23 meses", "24-35 meses", "36+ meses", "Sin dato"]


def normalized(value):
    if pd.isna(value):
        return ""
    return unicodedata.normalize("NFKD", str(value).strip().lower()).encode("ascii", "ignore").decode()


def yes(series):
    return series.map(normalized).isin(["si", "yes", "true", "1"])


def known_no(series):
    return series.map(normalized).isin(["no", "false", "0"])


def classified(series):
    # Accept only explicit source categories, never treat a pending label as diagnosis.
    return series.map(normalized).isin([
        "sin anemia", "normal", "leve", "moderada", "severa",
        "anemia leve", "anemia moderada", "anemia severa",
    ])


def load_data(source):
    raw = pd.read_excel(BytesIO(source) if isinstance(source, bytes) else source,
                        dtype={"id_sisa": "string"})
    raw.columns = raw.columns.astype(str).str.strip()
    missing = REQUIRED - set(raw.columns)
    if missing:
        raise ValueError("Faltan columnas: " + ", ".join(sorted(missing)))
    if raw.empty:
        raise ValueError("El archivo no contiene registros.")
    d = raw.copy()
    d["id_sisa"] = d.id_sisa.str.strip().replace("", pd.NA)
    for c in OPTIONAL:
        if c not in d:
            d[c] = pd.NA
    d["fecha_intervencion"] = pd.to_datetime(d["fecha_intervencion"], errors="coerce")
    for c in ["edad_meses", "hb_inicial", "hb_ajustada", "ferritina_inicial", "pcr_inicial", "altura_departamento"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    for c in ["cliente", "campaña", "territorio", "sexo", "eess_referencia"]:
        d[c] = d[c].fillna("Sin dato").astype(str).str.strip().replace("", "Sin dato")
    parts = d.territorio.str.split("|", regex=False)
    d["departamento"] = parts.str[0].fillna("Sin dato")
    d["distrito"] = parts.str[-1].fillna("Sin dato")
    d["grupo_edad"] = pd.cut(d.edad_meses, [-1, 5, 11, 23, 35, float("inf")],
                             labels=AGE_ORDER[:-1]).astype("object").fillna("Sin dato")
    return d


def filter_data(d, selections=None, dates=None):
    out = d.copy()
    for col, values in (selections or {}).items():
        if values:
            out = out[out[col].isin(values)]
    if dates is not None:
        start, end = [pd.Timestamp(v).normalize() for v in dates]
        out = out[(out.fecha_intervencion >= start) & (out.fecha_intervencion < end + pd.Timedelta(days=1))]
    return out


def indicators(d):
    delivered = yes(d.resultado_entregado)
    counsel = yes(d.consejeria_preventiva)
    return {
        "registros": len(d), "personas": d.id_sisa.dropna().nunique(),
        "hb": int(d.hb_inicial.notna().sum()),
        "resultados": int(delivered.sum()), "consejeria": int(counsel.sum()),
        "cierre": int((delivered & counsel).sum()),
        "sin_resultado": int(known_no(d.resultado_entregado).sum()),
        "sin_consejeria": int(known_no(d.consejeria_preventiva).sum()),
        "sin_clasificacion": int((~classified(d.clasificacion_anemia)).sum()),
    }


def territory_summary(d):
    if d.empty:
        return pd.DataFrame(columns=["Territorio", "Registros", "Entregados", "Consejería", "Entrega (%)", "Pendientes de entrega"])
    work = d.assign(entregados=yes(d.resultado_entregado).astype(int),
                    consejeria=yes(d.consejeria_preventiva).astype(int),
                    pendientes=known_no(d.resultado_entregado).astype(int))
    t = work.groupby("territorio", dropna=False).agg(
        Registros=("id_sisa", "size"), Entregados=("entregados", "sum"),
        Consejería=("consejeria", "sum"), pendientes=("pendientes", "sum"))
    t["Entrega (%)"] = (100 * t.Entregados / t.Registros).round(1)
    return t.rename(columns={"pendientes": "Pendientes de entrega"}).rename_axis("Territorio").reset_index().sort_values(
        ["Pendientes de entrega", "Registros"], ascending=False)


def operational_records(d):
    cols = ["id_sisa", "fecha_intervencion", "campaña", "territorio", "eess_referencia",
            "grupo_edad", "sexo", "resultado_entregado", "consejeria_preventiva", "clasificacion_anemia"]
    return d[cols].copy()


def csv_bytes(d):
    # Neutralize spreadsheet formula prefixes in uploaded text before exporting CSV.
    export = d.copy()
    for c in export.select_dtypes(include=["object", "string"]).columns:
        export[c] = export[c].map(lambda v: "'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v)
    return export.to_csv(index=False).encode("utf-8-sig")
