# Verificación de la extracción (PDF → Markdown)

_Generado el 2026-11-26 a partir de `data/manifests/*.csv`. Extractor: Docling sin OCR (ver `meta.json` de cada documento)._

## 1. Resumen

- Documentos procesados: **101** (el ZIP suministrado no incluye el FDS 12; la numeración llega a 102). Tiempo total de conversión: 129 min.
- Secciones (documento × 16): {'OK': 1611, 'AUSENTE_EN_ORIGINAL': 1, 'REPARADO_ESTRUCTURA': 4}. `OK`: título en PDF y en Markdown; `REPARADO_ESTRUCTURA`: texto presente pero título pegado a un párrafo, separado con `06_reparar_md.py`; `AUSENTE_EN_ORIGINAL`: ni el PDF ni el Markdown la tienen.
- Verificación numérica (valores, porcentajes, CAS, códigos): **40081 de 40189** números del PDF aparecen en el Markdown (recall de documento **0.9973**); 108 no aparecen en ninguna parte. CAS perdidos: **0** secciones con CAS faltantes.
- Secciones con recall < 0,95: 16 por texto **reubicado** (otro orden de lectura, nada perdido) y 30 por pérdida real en 22 documento(s).

## 2. Procedencia y versión

| fabricante | docs | linea_etiquetada | nombre_archivo | mencion_pag1-2 |
|---|---|---|---|---|
| Pintuco | 22 | 0 | 14 | 8 |
| Corona | 17 | 0 | 17 | 0 |
| Sika | 14 | 6 | 8 | 0 |
| International / AkzoNobel | 11 | 0 | 10 | 1 |
| Tecnidecor | 10 | 10 | 0 | 0 |
| Pintuland | 9 | 0 | 8 | 1 |
| Invesa | 6 | 0 | 6 | 0 |
| PPG | 6 | 6 | 0 | 0 |
| Axalta | 3 | 0 | 0 | 3 |
| Bler | 2 | 0 | 2 | 0 |
| Graphenstone (IEDISA) | 1 | 0 | 0 | 1 |

- Sin versión declarada en el documento: **17** (FDS_001, FDS_002, FDS_003, FDS_004, FDS_007, FDS_009, FDS_013, FDS_014, FDS_015, FDS_016, FDS_017, FDS_020, FDS_022, FDS_026, FDS_027, FDS_028, FDS_036). No se inventa: queda vacío.
- Sin fecha: **1** (FDS_007).
- Fabricante deducido solo por mención en las páginas 1-2 (confianza media, revisar): **14** (FDS_005, FDS_006, FDS_007, FDS_008, FDS_010, FDS_011, FDS_018, FDS_019, FDS_021, FDS_023, FDS_024, FDS_025, FDS_066, FDS_083).

## 3. Secciones que no salieron `OK`

| id | seccion | estado | pag_ini | pag_fin | titulo |
|---|---|---|---|---|---|
| FDS_002 | 4 | AUSENTE_EN_ORIGINAL |  |  |  |
| FDS_100 | 5 | REPARADO_ESTRUCTURA | 3 | 4 | ## SECCIÓN 5: MEDIDAS DE LUCHA CONTRA INCENDIOS 5.1 Medios de extinción apropiados: Medios de extinción apropi |
| FDS_100 | 7 | REPARADO_ESTRUCTURA | 4 | 4 | ## SECCIÓN 7: MANIPULACIÓN Y ALMACENAMIENTO 7.1 Precauciones que se deben tomar para garantizar una manipulaci |
| FDS_101 | 5 | REPARADO_ESTRUCTURA | 3 | 3 | ## SECCIÓN 5: MEDIDAS DE LUCHA CONTRA INCENDIOS 5.1 Medios de extinción apropiados: Medios de extinción apropi |
| FDS_101 | 15 | REPARADO_ESTRUCTURA | 12 | 12 | ## SECCIÓN 15: INFORMACIÓN SOBRE LA REGLAMENTACIÓN 15.1 Disposiciones específicas sobre seguridad, salud y med |

Reparaciones de encabezados en línea (texto original sin alterar; solo se separó el título):

| id | seccion | pagina | antes | titulo |
|---|---|---|---|---|
| FDS_100 | 5 | 3 | , de tratamiento especial: No relevante | SECCIÓN 5: MEDIDAS DE LUCHA CONTRA INCENDIOS 5.1 Medios de extinción apropiados: |
| FDS_100 | 7 | 4 | otras secciones: Ver secciones 8 y 13. | SECCIÓN 7: MANIPULACIÓN Y ALMACENAMIENTO 7.1 Precauciones que se deben tomar par |
| FDS_101 | 5 | 3 | , de tratamiento especial: No relevante | SECCIÓN 5: MEDIDAS DE LUCHA CONTRA INCENDIOS 5.1 Medios de extinción apropiados: |
| FDS_101 | 15 | 12 | POL 73/78 y al Código IBC: No relevante | SECCIÓN 15: INFORMACIÓN SOBRE LA REGLAMENTACIÓN 15.1 Disposiciones específicas s |

Páginas del Markdown ≠ páginas del PDF: FDS_097 (16/17) (verificado para FDS_097: la página 17 del PDF no tiene texto ni imágenes, por eso el Markdown no genera su marca; si aparece otro documento, revisarlo a mano).

## 4. Tablas

Filas fusionadas **reparadas** (el i-ésimo ingrediente se empareja con el i-ésimo porcentaje; orden verificado contra el PDF y sin añadir ni perder texto):

| id | seccion | pagina | filas_nuevas | antes |
|---|---|---|---|---|
| FDS_020 | 3 | 3 | 2 | / Varsol CAS: 8032-32-4 Xileno CAS: 1330-20-7 / 10% - 20% 10% - 20% / |
| FDS_036 | 3 | 3 | 6 | / Acetato de butilo CAS: 123-86-4 Xileno CAS: 1330-20-7 nafta disolvente (petróleo), fracción aromática ligera |

Tablas con varias sustancias o resultados apilados en una celda, **no reparadas** (emparejar exigiría inferir): 184 filas en 43 documento(s).

| seccion | motivo | filas | docs |
|---|---|---|---|
| 12 | varias_pruebas_en_celda | 66 | 19 |
| 8 | varias_pruebas_en_celda | 60 | 33 |
| 11 | varias_pruebas_en_celda | 41 | 21 |
| 16 | varias_pruebas_en_celda | 10 | 10 |
| 8 | varios_CAS_en_celda+varias_pruebas_en_celda | 6 | 6 |
| 12 | varios_CAS_en_celda | 1 | 1 |

## 5. Números del PDF que no están en el Markdown

| clase | numeros | documentos |
|---|---|---|
| caja_NFPA_HMIS | 93 | 24 |
| otro | 15 | 9 |

**Cajas NFPA/HMIS** (texto dentro de figuras; la imagen sí se conserva y enlaza): FDS_001 (3 núm., p. 1); FDS_002 (2 núm., p. 1); FDS_003 (5 núm., p. 1); FDS_004 (3 núm., p. 1); FDS_009 (3 núm., p. 1); FDS_011 (1 núm., p. 8); FDS_013 (3 núm., p. 1); FDS_015 (4 núm., p. 1); FDS_016 (3 núm., p. 1); FDS_017 (4 núm., p. 1); FDS_023 (4 núm., p. 13); FDS_024 (3 núm., p. 1,13); FDS_025 (4 núm., p. 1,14); FDS_055 (2 núm., p. 1); FDS_058 (1 núm., p. 7); FDS_069 (5 núm., p. 1,13); FDS_070 (6 núm., p. 1,6); FDS_071 (5 núm., p. 1,12); FDS_072 (6 núm., p. 1,11); FDS_073 (8 núm., p. 1,3,10); FDS_074 (5 núm., p. 5,7,12); FDS_086 (6 núm., p. 9); FDS_087 (6 núm., p. 1,12); FDS_094 (1 núm., p. 4)

**Resto de pérdidas** (todas las filas; `candidatas` > `faltan` indica que el dígito es ambiguo):

| id | token | faltan | candidatas | seccion | pagina | linea_pdf |
|---|---|---|---|---|---|---|
| FDS_029 | 2396 | 1 | 1 | 2 | 1 | Dioxido de titanio; Mezcla de: 5-cloro-2-metil-2H-isotiazol-3-ona [EC no. 247-500-7] y 2-metil-2H-isotiazol-3- |
| FDS_050 | 10.5 | 1 | 3 | 7 | 4 | Evitar fuentes de calor, radiación, electricidad estática y el contacto con alimentos. Para información adicio |
| FDS_055 | 1584 | 1 | 1 | 8 | 5 | NOMATIVIDAD APLICABLE: NTC 1584, NTC 1589, NTC 3851 y NTC 1728. |
| FDS_055 | 1589 | 1 | 1 | 8 | 5 | NOMATIVIDAD APLICABLE: NTC 1584, NTC 1589, NTC 3851 y NTC 1728. |
| FDS_055 | 1728 | 1 | 1 | 8 | 5 | NOMATIVIDAD APLICABLE: NTC 1584, NTC 1589, NTC 3851 y NTC 1728. |
| FDS_055 | 3851 | 1 | 1 | 8 | 5 | NOMATIVIDAD APLICABLE: NTC 1584, NTC 1589, NTC 3851 y NTC 1728. |
| FDS_060 | 50 | 1 | 51 | 8 | 5 | 50 ppm |
| FDS_070 | 13 | 1 | 3 | 6 | 5 | sección 13). |
| FDS_070 | 6 | 1 | 2 | 6 | 5 | SECCIÓN 6. MEDIDAS QUE DEBEN TOMARSE EN CASO DE DERRAME ACCIDENTAL O FUGA |
| FDS_073 | 1618 | 1 | 1 | 3 | 3 | ácidos grasos, C14-18 e insaturados de C1618, tratados con ácido maleico |
| FDS_074 | 12 | 2 | 3 | 2 | 2 | P333 + P313 En caso de irritación cutánea o sarpullido: consul2 / 12 |
| FDS_074 | 5 | 1 | 6 | 3 | 3 | 64742-94-5 |
| FDS_087 | 13 | 1 | 3 | 2 | 2 | P370 + P378 En caso de incendio: Utilizar arena seca, producto químico seco o espuma resistente al alcohol par |
| FDS_090 | 50 | 1 | 23 | 9 | 5 | Presión de vapor a 50 ºC: |

## 6. Imágenes

- Imágenes únicas conservadas: **1506** (copias idénticas unificadas por hash). Marcadas como decorativas probables (se repiten ≥3 veces o miden <80 px): 782. Ninguna se elimina; la marca solo sirve para decidir qué indexar.

## 7. Limitaciones y mitigaciones
- **Texto dentro de figuras (cajas NFPA/HMIS, pictogramas):** Docling sin OCR no copia el texto de las figuras. La imagen se conserva y se enlaza desde el Markdown. En una prueba manual, tesseract leyó bien la caja de Tecnidecor (FDS 2: `3 1 0`) pero en el diagrama de Sika (FDS 69) devolvió un dígito incorrecto frente a la capa de texto del PDF; como un dígito falso es peor que uno ausente en una ficha de seguridad, **no se inserta OCR de figuras**. Los pictogramas no se interpretan. Mitigación: el sistema debe responder «evidencia insuficiente» para clasificaciones NFPA/HMIS.
- **PDF con orden de lectura enredado (Bler, por marca de agua):** el texto está completo pero en otra sección; se reparó la estructura de títulos y se documenta la reubicación.
- **Tablas aplanadas o apiladas:** el contenido está, pero se perdió la alineación fila a fila; no se reconstruye por inferencia.
- **Verificación numérica:** compara el multiconjunto de números, no el texto completo; para dígitos sueltos es una cota inferior (un dígito sobrante en otra parte puede tapar uno perdido). Se complementa con revisión manual de casos (ver `perdidos_detalle.csv`).
