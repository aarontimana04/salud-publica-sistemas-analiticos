from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent / "data/anemia_demo.csv"


def load_demo():
    return pd.read_csv(DATA)


def metrics(d, month=3):
    if month not in [1,2,3]:
        raise ValueError("Mes de seguimiento no válido")
    d = d.copy()
    for source, target in [(f"evaluacion_mes{month}","evaluacion_final"),
                           (f"hb_mes{month}","hb_mes3"),
                           (f"normal_mes{month}","hb_normal_mes3"),
                           (f"adherente_mes{month}","adherente"),
                           (f"llamadas_mes{month}","llamadas"),
                           (f"visitas_mes{month}","visitas")]:
        d[target] = d[source]
    for col in ["acceso_eess","alerta_resuelta","parasitologico_realizado","continua_eess"]:
        d[col] = d[f"{col}_mes{month}"]
    screened = d[d.tamizado]
    anemia = d[d.anemia_inicial]
    paired = d[d.evaluacion_final & d.hb_mes0.notna() & d.hb_mes3.notna()]
    def rate(num, den):
        return 100*num/den if den else None
    return dict(month=month, eligible=int(d.elegible.sum()), screened=len(screened), final=int(d.evaluacion_final.sum()),
                screening_rate=rate(len(screened), d.elegible.sum()),
                completion_rate=rate(d.evaluacion_final.sum(), len(screened)),
                anemia=len(anemia), prevalence=rate(len(anemia), len(screened)),
                severity=anemia.severidad.value_counts().reindex(["Leve","Moderada","Severa"],fill_value=0).to_dict(),
                ferritin=int(anemia.ferritina_realizada.sum()), pcr=int(anemia.pcr_realizada.sum()),
                access=rate(anemia.acceso_eess.sum(), len(anemia)),
                alerts=int(d.alerta_registrada.sum()), resolved=int(d.alerta_resuelta.sum()),
                parasitic=int(d.parasitologico_realizado.sum()), indicated=int(d.parasitologico_indicado.sum()),
                calls=int(d.llamadas.sum()), visits=int(d.visitas.sum()),
                adherence=rate(anemia.adherente.sum(),len(anemia)),
                hb0=paired.hb_mes0.mean(), hb3=paired.hb_mes3.mean(), paired=len(paired),
                normal=rate(paired.hb_normal_mes3.sum(),len(paired)),
                continues=rate(paired.continua_eess.sum(),len(paired)),
                territories=anemia.groupby("distrito").size().sort_values(ascending=False).to_dict())
