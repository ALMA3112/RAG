#!/usr/bin/env python3
"""Genera docs/extraccion_verificacion.md a partir de los CSV de data/manifests (evidencia de verificación A1-A2).
Todo número y toda lista salen de los datos; solo la sección 'Limitaciones' es texto fijo, respaldado por esos datos."""
import csv, pathlib, collections, datetime, importlib.util

M, OUT = pathlib.Path("data/manifests"), pathlib.Path("docs/extraccion_verificacion.md")
def rd(n):
    p = M / n
    return list(csv.DictReader(open(p, encoding="utf-8"))) if p.exists() else None
def tabla(rows, cols, tope=None):
    if not rows: return "_(sin filas)_\n"
    rows = rows[:tope] if tope else rows
    f = lambda v: str(v if v is not None else "").replace("|", "/").replace("\n", " ")[:110]
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(f(r.get(c)) for c in cols) + " |" for r in rows]) + "\n"
def ids(rows): return sorted({r["id"] for r in rows})

docs, sec, qa, img = rd("manifest_documentos.csv"), rd("secciones.csv"), rd("qa_ingesta.csv"), rd("imagenes.csv")
rep, rept, sosp = rd("reparaciones.csv"), rd("reparaciones_tablas.csv"), rd("tablas_sospechosas.csv")
vn, vd, det = rd("verificacion_numerica.csv"), rd("verificacion_documentos.csv"), rd("perdidos_detalle.csv")
L = [f"# Verificación de la extracción (PDF → Markdown)\n", f"_Generado el {datetime.date.today()} a partir de `data/manifests/*.csv`. Extractor: Docling sin OCR (ver `meta.json` de cada documento)._\n"]

L.append("## 1. Resumen\n")
if docs: L.append(f"- Documentos procesados: **{len(docs)}** (el ZIP suministrado no incluye el FDS 12; la numeración llega a 102). Tiempo total de conversión: {sum(float(d['tiempo_s']) for d in docs) / 60:.0f} min.")
if sec:
    c = collections.Counter(r["estado"] for r in sec); L.append(f"- Secciones (documento × 16): {dict(c)}. `OK`: título en PDF y en Markdown; `REPARADO_ESTRUCTURA`: texto presente pero título pegado a un párrafo, separado con `06_reparar_md.py`; `AUSENTE_EN_ORIGINAL`: ni el PDF ni el Markdown la tienen.")
if vd and vn:
    tp, tl = sum(int(d["n_pdf"]) for d in vd), sum(int(d["perdidos"]) for d in vd); ok = [r for r in vn if r["recall"] not in ("", None)]
    reub = [r for r in ok if float(r["recall"]) < .95 <= float(r["recall_ajustado"])]; real = [r for r in ok if float(r["recall_ajustado"]) < .95]
    L.append(f"- Verificación numérica (valores, porcentajes, CAS, códigos): **{tp - tl} de {tp}** números del PDF aparecen en el Markdown (recall de documento **{1 - tl / tp:.4f}**); {tl} no aparecen en ninguna parte. CAS perdidos: **{sum(1 for r in ok if r['cas_faltan'])}** secciones con CAS faltantes.")
    L.append(f"- Secciones con recall < 0,95: {len(reub)} por texto **reubicado** (otro orden de lectura, nada perdido) y {len(real)} por pérdida real en {len(ids(real))} documento(s).")
L.append("\n## 2. Procedencia y versión\n")
if docs:
    c = collections.Counter((d["fabricante"], d["fabricante_fuente"]) for d in docs); fab = collections.defaultdict(dict)
    for (f, s), n in c.items(): fab[f][s] = n
    L.append(tabla([dict(fabricante=f, docs=sum(v.values()), **{k: v.get(k, 0) for k in ("linea_etiquetada", "nombre_archivo", "mencion_pag1-2")}) for f, v in sorted(fab.items(), key=lambda kv: -sum(kv[1].values()))], ["fabricante", "docs", "linea_etiquetada", "nombre_archivo", "mencion_pag1-2"]))
    sv = [d for d in docs if not (d["version_archivo"] or d["version_texto"])]; sf = [d for d in docs if not (d["fecha_emision"] or d["fecha_revision"] or d["fecha_actualizacion"])]
    men = [d for d in docs if d["fabricante_fuente"] == "mencion_pag1-2"]
    L.append(f"- Sin versión declarada en el documento: **{len(sv)}** ({', '.join(d['id'] for d in sv)}). No se inventa: queda vacío.")
    L.append(f"- Sin fecha: **{len(sf)}** ({', '.join(d['id'] for d in sf) or 'ninguno'}).")
    L.append(f"- Fabricante deducido solo por mención en las páginas 1-2 (confianza media, revisar): **{len(men)}** ({', '.join(d['id'] for d in men)}).\n")
L.append("## 3. Secciones que no salieron `OK`\n")
if sec: L.append(tabla([r for r in sec if r["estado"] != "OK"], ["id", "seccion", "estado", "pag_ini", "pag_fin", "titulo"]))
if rep: L.append("Reparaciones de encabezados en línea (texto original sin alterar; solo se separó el título):\n\n" + tabla(rep, ["id", "seccion", "pagina", "antes", "titulo"]))
if qa:
    pm = [r for r in qa if r["paginas_coinciden"] not in ("True", "")]
    L.append(f"Páginas del Markdown ≠ páginas del PDF: {', '.join(f'{r['id']} ({r['paginas_md']}/{r['paginas_pdf']})' for r in pm) or 'ninguno'} (verificado para FDS_097: la página 17 del PDF no tiene texto ni imágenes, por eso el Markdown no genera su marca; si aparece otro documento, revisarlo a mano).\n")
L.append("## 4. Tablas\n")
if rept: L.append("Filas fusionadas **reparadas** (el i-ésimo ingrediente se empareja con el i-ésimo porcentaje; orden verificado contra el PDF y sin añadir ni perder texto):\n\n" + tabla(rept, ["id", "seccion", "pagina", "filas_nuevas", "antes"]))
if sosp:
    c = collections.Counter((r["seccion"], r["motivo"]) for r in sosp)
    L.append(f"Tablas con varias sustancias o resultados apilados en una celda, **no reparadas** (emparejar exigiría inferir): {len(sosp)} filas en {len(ids(sosp))} documento(s).\n")
    L.append(tabla([dict(seccion=s, motivo=m, filas=n, docs=len({r['id'] for r in sosp if r['seccion'] == s and r['motivo'] == m})) for (s, m), n in c.most_common()], ["seccion", "motivo", "filas", "docs"]))
L.append("## 5. Números del PDF que no están en el Markdown\n")
if det:
    pc = collections.Counter(); dc = collections.defaultdict(set)
    for r in det: pc[r["clase"]] += int(r["faltan"]); dc[r["clase"]].add(r["id"])
    L.append(tabla([dict(clase=k, numeros=v, documentos=len(dc[k])) for k, v in pc.items()], ["clase", "numeros", "documentos"]))
    cj = [r for r in det if r["clase"] == "caja_NFPA_HMIS"]; ag = collections.defaultdict(lambda: [0, set()])
    for r in cj: ag[r["id"]][0] += int(r["faltan"]); ag[r["id"]][1].add(r["pagina"])
    L.append("**Cajas NFPA/HMIS** (texto dentro de figuras; la imagen sí se conserva y enlaza): " + "; ".join(f"{i} ({n} núm., p. {','.join(sorted(p, key=lambda x: int(x or 0)))})" for i, (n, p) in sorted(ag.items())) + "\n")
    L.append("**Resto de pérdidas** (todas las filas; `candidatas` > `faltan` indica que el dígito es ambiguo):\n\n" + tabla([r for r in det if r["clase"] == "otro"], ["id", "token", "faltan", "candidatas", "seccion", "pagina", "linea_pdf"]))
L.append("## 6. Imágenes\n")
if img:
    dec = sum(r["decorativa_probable"] == "True" for r in img)
    L.append(f"- Imágenes únicas conservadas: **{len(img)}** (copias idénticas unificadas por hash). Marcadas como decorativas probables (se repiten ≥3 veces o miden <80 px): {dec}. Ninguna se elimina; la marca solo sirve para decidir qué indexar.\n")
L.append("""## 7. Limitaciones y mitigaciones
- **Texto dentro de figuras (cajas NFPA/HMIS, pictogramas):** Docling sin OCR no copia el texto de las figuras. La imagen se conserva y se enlaza desde el Markdown. En una prueba manual, tesseract leyó bien la caja de Tecnidecor (FDS 2: `3 1 0`) pero en el diagrama de Sika (FDS 69) devolvió un dígito incorrecto frente a la capa de texto del PDF; como un dígito falso es peor que uno ausente en una ficha de seguridad, **no se inserta OCR de figuras**. Los pictogramas no se interpretan. Mitigación: el sistema debe responder «evidencia insuficiente» para clasificaciones NFPA/HMIS.
- **PDF con orden de lectura enredado (Bler, por marca de agua):** el texto está completo pero en otra sección; se reparó la estructura de títulos y se documenta la reubicación.
- **Tablas aplanadas o apiladas:** el contenido está, pero se perdió la alineación fila a fila; no se reconstruye por inferencia.
- **Verificación numérica:** compara el multiconjunto de números, no el texto completo; para dígitos sueltos es una cota inferior (un dígito sobrante en otra parte puede tapar uno perdido). Se complementa con revisión manual de casos (ver `perdidos_detalle.csv`).
""")
OUT.parent.mkdir(exist_ok=True); OUT.write_text("\n".join(L), encoding="utf-8"); print(f"escrito {OUT} ({OUT.stat().st_size // 1024} KB, {len(L)} bloques)")
