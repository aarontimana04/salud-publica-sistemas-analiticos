"""Genera una cohorte ficticia reproducible para el dashboard de referencia."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
rng = np.random.default_rng(20261012)
n = 1200
d = pd.DataFrame({"id_demo": [f"DEMO-ANE-{i:04d}" for i in range(1, n+1)]})
d["region"] = "Región ejemplo"
d["elegible"] = True
d["tamizado"] = np.arange(n) < 1080
d["evaluacion_final"] = np.arange(n) < 918
d["anemia_inicial"] = np.arange(n) < 410
d["severidad"] = "Sin anemia simulada"
d.loc[:253, "severidad"] = "Leve"
d.loc[254:397, "severidad"] = "Moderada"
d.loc[398:409, "severidad"] = "Severa"
d.loc[1080:, "severidad"] = "Sin tamizaje"
d["distrito"] = "Distrito A"
start = 0
for name, size in zip(list("ABCDE"), [141,105,78,52,34]):
    d.loc[start:start+size-1, "distrito"] = f"Distrito {name}"
    start += size
d.loc[410:, "distrito"] = [f"Distrito {v}" for v in rng.choice(list("ABCDE"), n-410)]
for col, size in {"ferritina_realizada":410, "pcr_realizada":410, "acceso_eess":377,
                  "alerta_registrada":156, "alerta_resuelta":141,
                  "parasitologico_indicado":120, "parasitologico_realizado":98,
                  "adherente":320, "hb_normal_mes3":588, "continua_eess":808}.items():
    d[col] = np.arange(n) < size
d["llamadas"] = np.where(d.anemia_inicial, 6, 0)
d["visitas"] = np.where(d.anemia_inicial, 2, 0)
d["hb_mes0"] = np.nan
d["hb_mes3"] = np.nan
# La media de la cohorte emparejada de 918 será exactamente 10.2 y 11.4.
baseline = rng.uniform(8.5, 12, 918)
baseline += 10.2-baseline.mean()
final = rng.uniform(10, 13, 918)
final += 11.4-final.mean()
d.loc[:917, "hb_mes0"] = baseline
d.loc[:917, "hb_mes3"] = final
d.loc[918:1079, "hb_mes0"] = rng.uniform(9, 13, 162)
d["dato_ficticio"] = True
# Seguimiento mensual simulado. Mes 3 conserva las cifras de la referencia.
for month, completed, normal, adherent in [(1,600,330,250),(2,780,468,290),(3,918,588,320)]:
    d[f"evaluacion_mes{month}"] = np.arange(n) < completed
    d[f"hb_mes{month}"] = np.nan
    d.loc[:completed-1, f"hb_mes{month}"] = d.loc[:completed-1,"hb_mes0"] + (final[:completed] - baseline[:completed]) * month/3
    d[f"normal_mes{month}"] = np.arange(n) < normal
    d[f"adherente_mes{month}"] = np.arange(n) < adherent
    d[f"llamadas_mes{month}"] = np.where(d.anemia_inicial,2*month,0)
    visits = {1:(np.arange(n)<273).astype(int),
              2:1+(np.arange(n)<136).astype(int),3:np.full(n,2)}[month]
    d[f"visitas_mes{month}"] = np.where(d.anemia_inicial,visits,0)
    for col in ["acceso_eess","alerta_resuelta","parasitologico_realizado","continua_eess"]:
        limit = int(d[col].sum()*month/3)
        d[f"{col}_mes{month}"] = np.arange(n) < limit
ROOT.joinpath("data").mkdir(exist_ok=True)
d.to_csv(ROOT / "data/anemia_demo.csv", index=False)
print(f"Generados {len(d)} registros ficticios en data/anemia_demo.csv")
