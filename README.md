# Nuestros Programas de Salud Pública

Dashboard local de Streamlit con identidad de Sistemas Analíticos y estilo del portal SEACE: navegación superior, cabecera amplia, azul `#000077`, naranja `#FC7100`, detalles turquesa y logotipo proporcionado.

## Ejecutar

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Abrir http://localhost:8501. La vista principal usa `data/anemia_demo.csv`: 1,200 registros sintéticos generados para reproducir las cifras de la referencia. Para regenerarlos: `.venv/bin/python scripts/generate_demo.py`.

La vista http://localhost:8501/?source=excel conserva el análisis del Excel original `data/BD_ANEMIA.xlsx` y la carga de otra base compatible. No modifica el archivo entregado.

## Vistas

- Anemia (demo): cobertura, detección, articulación con EESS, acompañamiento, Hb promedio y casos por distrito. Filtro territorial y selector acumulado Mes 1 / Mes 2 / Mes 3; restablecer devuelve la referencia completa.
- Excel original: filtros de fecha, departamento, territorio, campaña, cliente, edad y sexo; indicadores operativos, prioridades territoriales y exportación CSV.
- Diabetes: estructura reservada, sin cifras simuladas. Requiere base propia e indicadores acordados.
- Otros: espacio para el tercer programa, pendiente de definir.

El archivo recibido contiene 100 registros ficticios y clasificaciones pendientes. La app conserva esta advertencia y no aplica algoritmos de diagnóstico. Los porcentajes operativos usan registros como denominador. El conteo de personas supone que `id_sisa` identifica a una persona. No se muestran ni exportan nombres, documentos, teléfonos o direcciones. La copia de datos está excluida de Git; incluirla por separado si se traslada el proyecto.

La demo contiene etiquetas de severidad y Hb normal simuladas; no aplica umbrales clínicos. Todos los indicadores de la imagen se calculan desde el CSV. El 85% de evaluación final usa 918 / 1080 tamizados. Las medias de Hb se calculan sobre los mismos 918 registros; el 38%, 92%, 78%, 64%, 88% y las proporciones de severidad se redondean al entero más próximo.

Mes 1 y Mes 2 son cortes simulados adicionales. Hb compara las mismas personas dentro de cada corte; la población evaluada cambia entre meses. La vista principal no incluye tabla de datos, apartado de cálculos ni enlace al Excel. El logotipo azul proporcionado se muestra centrado con transparencia original.

## Verificar

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Referencias: [Sistemas Analíticos](https://www.sistemasanaliticos.com/) y [Streamlit](https://docs.streamlit.io/develop/api-reference).
