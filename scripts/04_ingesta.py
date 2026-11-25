#!/usr/bin/env python3
"""Ingesta de FDS: PDF -> Markdown (Docling, sin OCR) + metadatos + secciones + imagenes.
Reanudable: omite los documentos que ya tienen meta.json (usar --force para rehacer).
Uso:  python scripts/04_ingesta.py --solo 36 45 31      (prueba)
      python scripts/04_ingesta.py                       (corpus completo)"""
import re, sys, json, csv, time, hashlib, argparse, pathlib, datetime, unicodedata, subprocess
from importlib.metadata import version

RAW, OUT, MAN = pathlib.Path("data/raw_pdfs"), pathlib.Path("data/markdown"), pathlib.Path("data/manifests")
PB = "<!--PB-->"
PAGE_RE = re.compile(r"<!-- page: (\d+) -->")

def norm(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()

# ---------- detector de las 16 secciones (probado sobre los 101 PDF) ----------
KW = {1: r"identific|identif", 2: r"peligro|riesgo|hazard|composici|ingredient|componente",
      3: r"composici|ingredient|componente|peligro|riesgo|hazard", 4: r"primeros auxilios|first.?aid|auxilio",
      5: r"incendio|lucha contra|fire|extinci", 6: r"vertido|derrame|accidental|release",
      7: r"manipula|almacen|handling|storage", 8: r"exposici|proteccion personal|exposure",
      9: r"propiedades f|physical", 10: r"estabilidad|reactividad|stability", 11: r"toxicol",
      12: r"ecolog|ecotox", 13: r"eliminaci|disposal|disposici|residuo", 14: r"transporte|transport",
      15: r"reglament|regulat|normativ", 16: r"otras? informaci|other information|informacion adicional"}
HEAD = re.compile(r"(?:seccion|section)?\s*(\d{1,2})(?!\d|\.\d)\s*[:.\-–)]*\s*(.*)$")

def heading_hits(lines):
    hits = {}
    for i, raw in enumerate(lines):
        m = HEAD.match(norm(raw).strip().lstrip("#*_>| -").strip())
        if m:
            n = int(m.group(1))
            if 1 <= n <= 16 and n not in hits and re.search(KW[n], m.group(2)[:120]):
                hits[n] = i
    return hits

# ---------- metadatos ----------
KNOWN = [("TECNIDECOR", "Tecnidecor"), ("PINTUCO", "Pintuco"), ("CORONA", "Corona"), ("SIKA", "Sika"),
         ("PPG", "PPG"), ("INVESA", "Invesa"), ("PINTULAND", "Pintuland"), ("BLER", "Bler"), ("AXALTA", "Axalta"),
         ("IEDISA|GRAPHENSTONE", "Graphenstone (IEDISA)"), ("AKZO ?NOBEL|AKSONOBEL|INTERNATIONAL PAINT|INTERNATIONAL", "International / AkzoNobel")]
LABEL = re.compile(r"(?i)^\s*(?:datos del )?(empresa|fabricante(?:\s*/\s*distribuidor)?|proveedor|raz[oó]n social|distribuidor|company|supplier|manufacturer)(?: o fabricante)?\s*[:\-]?\s{1,}(.{3,80})$")
DATE = r"(\d{4}[/.\-]\d{1,2}[/.\-]\d{1,2}|\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}|\d{1,2}\s+(?:de\s+)?[A-Za-záéíóúÁÉÍÓÚ]+\s+(?:de\s+)?\d{4}|[A-Za-záéíóúÁÉÍÓÚ]+\s+de\s+\d{4}|[A-Za-z]{3}-\d{2})"
EMI = re.compile(r"(?i)(?:fecha\s+de\s+)?emisi[oó]n\s*[:|]?\s*" + DATE)
REV = re.compile(r"(?i)(?:fecha\s+de\s+(?:la\s+)?(?:[uú]ltima\s+)?)?revisi[oó]n\s*[:|]?\s*" + DATE)
ACT = re.compile(r"(?i)(?:fecha\s+de\s+)?actualizaci[oó]n\s*[:|]?\s*" + DATE)
DOCNUM = re.compile(r"(?i)(?:MSDS\s*no\.?|N[úu]mero de HDS:?)\s*(\d+)")
VERS = re.compile(r"(?i)versi[oó]n(?:\s+de\s+la\s+fds)?\s*[:|]?\s*(\d+(?:\.\d+)?)")

def match_known(text):
    return next((lab for pat, lab in KNOWN if re.search(pat, text.upper())), None)

def fds_num(p):
    return int(re.search(r"FDS ?(\d+)", p.name).group(1))

def pdftext(pdf, layout=False, last=None):
    cmd = ["pdftotext"] + (["-layout"] if layout else []) + (["-l", str(last)] if last else []) + [str(pdf), "-"]
    return subprocess.run(cmd, capture_output=True, text=True).stdout

def metadatos(pdf):
    t12 = pdftext(pdf, layout=True, last=2)
    cand = None
    for l in t12.splitlines()[:200]:
        m = LABEL.match(l)
        if m: cand = re.sub(r"\s{2,}.*$", "", m.group(2).strip())[:80]; break
    f_txt, f_arc, f_men = (match_known(cand) if cand else None), match_known(pdf.name), match_known(t12)
    fab, fuente = next(((v, s) for v, s in [(f_txt, "linea_etiquetada"), (f_arc, "nombre_archivo"), (f_men, "mencion_pag1-2")] if v), (None, "NO_DETERMINADO"))
    prod = re.sub(r"^FDS\s*\d+\s*[-–_]*\s*", "", pdf.stem)
    prod = re.sub(r"\s*\(Versi[oó]n\s*\d+\)", "", prod).replace("_", " ").strip(" -")
    ver_arc = re.search(r"\(Versi[oó]n\s*(\d+)\)", pdf.name)
    g = lambda rx: (rx.search(t12).group(1).strip() if rx.search(t12) else None)
    v = VERS.search(t12)
    pg = re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout)
    return dict(fabricante=fab, fabricante_fuente=fuente, fabricante_linea=cand,
                fabricante_discrepa=bool(f_txt and f_arc and f_txt != f_arc), producto_archivo=prod,
                version_archivo=ver_arc.group(1) if ver_arc else None, version_texto=v.group(1) if v else None,
                fecha_emision=g(EMI), fecha_revision=g(REV), fecha_actualizacion=g(ACT), doc_numero=g(DOCNUM), anio_carpeta=re.search(r"(20\d\d)", str(pdf.parent)).group(1),
                paginas_pdf=int(pg.group(1)) if pg else None)

# ---------- posproceso del Markdown ----------
def numerar_paginas(md):
    partes = md.split(PB)
    return "".join(f"<!-- page: {k} -->\n{p}" for k, p in enumerate(partes, 1)), len(partes)

def paginas_por_linea(lines):
    cur, out = 1, []
    for l in lines:
        m = PAGE_RE.match(l)
        if m: cur = int(m.group(1))
        out.append(cur)
    return out

def secciones_md(lines, pages):
    orden = sorted(heading_hits(lines).items(), key=lambda kv: kv[1])
    res = {}
    for k, (n, i) in enumerate(orden):
        fin = orden[k + 1][1] if k + 1 < len(orden) else len(lines)
        res[n] = dict(seccion=n, titulo=lines[i].strip()[:120], linea=i, pag_ini=pages[i], pag_fin=pages[max(i, fin - 1)])
    return res

def dedup_imagenes(d, md, pages_lines):
    img_dir, canon = d / "img", {}
    if not img_dir.exists(): return md, []
    for f in sorted(img_dir.glob("*.png")):
        h = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
        if h in canon:
            md = md.replace(f"img/{f.name}", f"img/{canon[h][0]}"); f.unlink()
        else:
            canon[h] = (f.name,)
    lines = md.splitlines(); pg = paginas_por_linea(lines); info = []
    from PIL import Image
    for h, (name,) in canon.items():
        refs = [pg[i] for i, l in enumerate(lines) if f"img/{name}" in l]
        w, ht = Image.open(img_dir / name).size
        info.append(dict(archivo=f"img/{name}", sha16=h, ancho=w, alto=ht, repeticiones=len(refs), paginas=sorted(set(refs)),
                         decorativa_probable=(len(refs) >= 3 or max(w, ht) < 80)))
    return md, info

# ---------- conversion ----------
_conv = None
def convertir(pdf, md_path):
    global _conv
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling_core.types.doc import ImageRefMode
    if _conv is None:
        o = PdfPipelineOptions(); o.do_ocr = False; o.do_table_structure = True
        o.generate_picture_images = True; o.images_scale = 2.0
        _conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=o)})
    doc = _conv.convert(str(pdf)).document
    kw = dict(artifacts_dir=pathlib.Path("img"), image_mode=ImageRefMode.REFERENCED)
    try:
        doc.save_as_markdown(md_path, page_break_placeholder=f"\n\n{PB}\n\n", **kw)
    except TypeError:
        doc.save_as_markdown(md_path, **kw)

def procesar(pdf, n, did, d):
    t0 = time.time()
    meta = dict(id=did, num=n, archivo=pdf.name, ruta_pdf=str(pdf), sha256_pdf=hashlib.sha256(pdf.read_bytes()).hexdigest())
    meta.update(metadatos(pdf))
    md_path = d / f"{did}.md"
    convertir(pdf, md_path)
    md = md_path.read_text(encoding="utf-8")
    (d / f"{did}.docling.md").write_text(md, encoding="utf-8")          # copia sin posproceso (auditoria)
    hay_pb = PB in md
    md, n_pag_md = numerar_paginas(md) if hay_pb else (md, None)
    md, imgs = dedup_imagenes(d, md, None)
    md_path.write_text(md, encoding="utf-8")
    lines = md.splitlines(); pg = paginas_por_linea(lines)
    sec_md = secciones_md(lines, pg)
    sec_pdf = heading_hits(pdftext(pdf).splitlines())
    estados = {}
    for s in range(1, 17):
        en_pdf, en_md = s in sec_pdf, s in sec_md
        estados[s] = ("OK" if en_pdf and en_md else "FALLO_EXTRACCION" if en_pdf else
                      "SOLO_EN_MD_REVISAR" if en_md else "AUSENTE_EN_ORIGINAL")
    fusion = sum(1 for l in lines if l.lstrip().startswith("|") and any(len(re.findall(r"CAS:?\s*\d", c)) >= 2 for c in l.split("|")))
    meta.update(extractor=dict(herramienta="docling", docling=version("docling"), do_ocr=False, tablas=True, imagenes_escala=2.0),
                generado=datetime.datetime.now().isoformat(timespec="seconds"), tiempo_s=round(time.time() - t0, 1),
                md=f"{did}.md", secciones=list(sec_md.values()), estados=estados, imagenes=imgs,
                qa=dict(paginas_pdf=meta["paginas_pdf"], paginas_md=n_pag_md, marcas_pagina=hay_pb,
                        paginas_coinciden=(n_pag_md == meta["paginas_pdf"]) if n_pag_md else None,
                        filas_tabla_fusionadas=fusion, imagenes_unicas=len(imgs),
                        imagenes_decorativas_prob=sum(i["decorativa_probable"] for i in imgs)))
    return meta

# ---------- consolidacion ----------
def consolidar():
    metas = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(OUT.glob("FDS_*/meta.json"))]
    def w(name, rows):
        if not rows: return
        with open(MAN / name, "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=list(rows[0].keys())); wr.writeheader(); wr.writerows(rows)
    keys = ["id", "num", "archivo", "fabricante", "fabricante_fuente", "fabricante_linea", "fabricante_discrepa", "producto_archivo",
            "version_archivo", "version_texto", "fecha_emision", "fecha_revision", "fecha_actualizacion", "doc_numero", "anio_carpeta", "paginas_pdf", "sha256_pdf", "md", "tiempo_s"]
    w("manifest_documentos.csv", [{k: m.get(k) for k in keys} for m in metas])
    w("secciones.csv", [dict(id=m["id"], seccion=s, estado=m["estados"][str(s)],
        pag_ini=next((x["pag_ini"] for x in m["secciones"] if x["seccion"] == s), None),
        pag_fin=next((x["pag_fin"] for x in m["secciones"] if x["seccion"] == s), None),
        titulo=next((x["titulo"] for x in m["secciones"] if x["seccion"] == s), None)) for m in metas for s in range(1, 17)])
    w("imagenes.csv", [{"id": m["id"], **{**i, "paginas": ",".join(map(str, i["paginas"]))}} for m in metas for i in m["imagenes"]])
    w("qa_ingesta.csv", [dict(id=m["id"], **m["qa"], secciones_ok=sum(v in ("OK", "REPARADO_ESTRUCTURA") for v in m["estados"].values()),
        fallos_extraccion=[k for k, v in m["estados"].items() if v == "FALLO_EXTRACCION"],
        ausentes_original=[k for k, v in m["estados"].items() if v == "AUSENTE_EN_ORIGINAL"]) for m in metas])
    print(f"Consolidado: {len(metas)} documentos -> {MAN}")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--solo", nargs="*", type=int); ap.add_argument("--force", action="store_true")
    a = ap.parse_args(); MAN.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(RAW.rglob("*.pdf"), key=fds_num)
    if a.solo: pdfs = [p for p in pdfs if fds_num(p) in a.solo]
    for k, pdf in enumerate(pdfs, 1):
        n = fds_num(pdf); did = f"FDS_{n:03d}"; d = OUT / did
        if (d / "meta.json").exists() and not a.force:
            print(f"[{k}/{len(pdfs)}] {did} omitido (ya procesado)"); continue
        d.mkdir(parents=True, exist_ok=True)
        try:
            meta = procesar(pdf, n, did, d)
            (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
            (d / "error.txt").unlink(missing_ok=True)
            bad = [s for s, v in meta["estados"].items() if v != "OK"]
            print(f"[{k}/{len(pdfs)}] {did} {meta['tiempo_s']}s | {meta['fabricante']} | secc!=OK {bad} | img {meta['qa']['imagenes_unicas']} | pags {meta['qa']['paginas_md']}/{meta['qa']['paginas_pdf']}", flush=True)
        except Exception as e:
            (d / "error.txt").write_text(repr(e), encoding="utf-8"); print(f"[{k}/{len(pdfs)}] {did} ERROR: {e!r}", flush=True)
    consolidar()

if __name__ == "__main__":
    main()
