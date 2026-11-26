#!/usr/bin/env python3
"""Fase A2: verificación numérica PDF vs Markdown, por documento y sección (v2).
Compara el multiconjunto de números (valores, porcentajes, CAS, códigos UN) del texto del PDF contra el del Markdown.
 - Secciones: detector estricto de títulos (04), con cadena 1..16 en orden; no se dejan engañar por referencias cruzadas.
 - Encabezados/pies del PDF: una línea corta se descarta si TODAS sus palabras aparecen en las primeras/últimas líneas de
   su página (modo layout). Docling elimina ese mobiliario a propósito; los títulos de sección nunca se descartan.
 - Markdown: se ignoran imágenes y comentarios.
Nivel documento: un número del PDF que no aparece en NINGUNA parte del Markdown está PERDIDO; si falta en su sección pero
está en otra, está REUBICADO (orden de lectura distinto). El recall ajustado solo penaliza lo perdido."""
import re, json, csv, subprocess, importlib.util, pathlib
from collections import Counter

spec = importlib.util.spec_from_file_location("ing", pathlib.Path(__file__).with_name("04_ingesta.py"))
ing = importlib.util.module_from_spec(spec); spec.loader.exec_module(ing)

NUM, CASN, W = re.compile(r"\d+(?:[.,]\d+)?"), re.compile(r"\b\d{2,7}-\d{2}-\d\b"), re.compile(r"[\w.,/\-]+")
UMBRAL = 0.95
CAJA = re.compile(r"(?i)NFPA|HMIS|\bSALUD\b|INFLAMAB|INESTAB|REACTIV|PELIGRO\s+F[IÍ]SICO|PROTECCI[OÓ]N\s+PERSONAL")

def detalle(did, lp, deficit):
    """Una fila por número perdido: dónde aparece en el PDF (candidatas), su sección, página y clase."""
    L = [t.strip() for t, _, _ in lp]; E = [e for _, e, _ in lp]; P = [k for _, _, k in lp]; hits = ing.heading_hits([t for t, _, _ in lp])
    filas = []
    for tok, d in sorted(deficit.items()):
        rx = re.compile(r"(?<![\d.,])" + re.escape(tok) + r"(?!\d|[.,]\d)")
        cand = [i for i in range(len(L)) if not E[i] and rx.search(L[i])]
        if not cand: cand = [i for i in range(len(L)) if not E[i] and tok in L[i]]          # pegado a letras (p. ej. código de producto)
        ctx = lambda i: " ".join(L[max(0, i - 4): i + 5])
        caja = [i for i in cand if CAJA.search(ctx(i))]; i = (caja or cand or [None])[0]
        sec = max((n for n, h in hits.items() if i is not None and h <= i), default=None)
        filas.append(dict(id=did, token=tok, faltan=d, candidatas=len(cand), clase="caja_NFPA_HMIS" if caja else "otro", tipo=tipo(tok),
                          seccion=sec, pagina=P[i] if i is not None else None, linea_pdf=(L[i][:110] if i is not None else "")))
    return filas


def pdftxt(pdf, k, layout):
    cmd = ["pdftotext"] + (["-layout"] if layout else []) + ["-f", str(k), "-l", str(k), str(pdf), "-"]
    return [l for l in subprocess.run(cmd, capture_output=True, text=True).stdout.splitlines() if l.strip()]

PAGINADOR = re.compile(r"(?i)^\s*(?:p[aá]g(?:ina)?\.?\s*)?\d+\s*(?:/|de|of)\s*\d+\s*$")
CONTINUA = re.compile(r"(?i)^-?\s*contin[uú]a en la siguiente p[aá]gina\s*")
DIGITO = re.compile(r"(?<![\w.,/-])\d(?![\w.,/-])")

def lineas_pdf(pdf, n_pag):
    """[(texto, es_mobiliario, pagina)] en orden de lectura. Mobiliario (encabezados/pies que Docling elimina a propósito):
    contadores de página ('3/12'), líneas idénticas en >=60% de las páginas (tras quitar 'CONTINÚA EN LA SIGUIENTE PÁGINA'),
    y dígitos sueltos de las primeras 6 líneas de la página (rombo NFPA del encabezado, p. ej. Tecnidecor)."""
    pages = [pdftxt(pdf, k, False) for k in range(1, n_pag + 1)]
    limpia = lambda l: CONTINUA.sub("", l.strip())
    exacta = Counter(limpia(x) for p in pages for x in {y for y in p})
    corte = max(3, 0.6 * n_pag); out = []
    for k, p in enumerate(pages, 1):
        zona = re.sub(r"(?i)p[aá]g\w*\.?\s*\d+(?:\s*(?:de|/|of)\s*\d+|\s+de\b)?", " ", " ".join(pdftxt(pdf, k, True)[:6]))   # el contador de página no son líneas sueltas
        cab = Counter(DIGITO.findall(zona))
        total_usado = False
        for pos, l in enumerate(p):
            t = limpia(l); entero_corto = re.fullmatch(r"\d{1,2}", t) is not None
            mueble = t == "" or bool(PAGINADOR.match(t)) or (exacta[t] >= corte and not entero_corto)
            if not mueble and re.fullmatch(r"\d", t) and cab[t] > 0: cab[t] -= 1; mueble = True
            if not mueble and pos < 10 and t == str(n_pag) and len(t) == 1 and not total_usado: total_usado = True; mueble = True   # total de páginas suelto ("Página 1 de" / "4")
            out.append((l, mueble, k))
    return out

def lineas_md(texto):
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S); texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", texto)
    return [l for l in texto.split("\n") if l.strip() and not re.fullmatch(r"\|[\s\-:|]+\|?", l.strip())]

def trozos(lines, mueble=None):
    hits = sorted(ing.heading_hits(lines).items(), key=lambda kv: kv[1]); out = {}
    for k, (n, i) in enumerate(hits):
        fin = hits[k + 1][1] if k + 1 < len(hits) else len(lines)
        out[n] = "\n".join(lines[j] for j in range(i, fin) if j == i or not (mueble and mueble[j]))
    return out

def comparar(t_pdf, t_md, pool):
    a, b = Counter(NUM.findall(t_pdf)), Counter(NUM.findall(t_md)); falta, sobra = a - b, b - a
    perdidos = Counter()
    for t, c in falta.items():
        usar = min(c, pool[t]); pool[t] -= usar
        if usar: perdidos[t] = usar
    n = sum(a.values()); cas = set(CASN.findall(t_pdf)) - set(CASN.findall(t_md))
    return dict(n_pdf=n, n_md=sum(b.values()), faltan=sum(falta.values()), faltan_perdidos=sum(perdidos.values()), sobran=sum(sobra.values()),
                recall=round(1 - sum(falta.values()) / n, 3) if n else None,
                recall_ajustado=round(1 - sum(perdidos.values()) / n, 3) if n else None, cas_faltan=" ".join(sorted(cas)),
                faltan_ej=" ".join(f"{t}x{c}" if c > 1 else t for t, c in falta.most_common(8)),
                perdidos_ej=" ".join(f"{t}x{c}" if c > 1 else t for t, c in perdidos.most_common(8)), perdidos=perdidos)

def tipo(t):
    return "digito_suelto" if re.fullmatch(r"\d", t) else "anio" if re.fullmatch(r"(19|20)\d\d", t) else "decimal" if re.search(r"[.,]", t) else "otro"

def main():
    filas, docs, det, por_tipo, por_sec = [], [], [], Counter(), Counter()
    for meta_f in sorted(ing.OUT.glob("FDS_*/meta.json")):
        m = json.loads(meta_f.read_text(encoding="utf-8")); md_f = meta_f.parent / m["md"]
        lp = lineas_pdf(pathlib.Path(m["ruta_pdf"]), m["paginas_pdf"]); mdl = lineas_md(md_f.read_text(encoding="utf-8"))
        sp = trozos([t for t, _, _ in lp], [e for _, e, _ in lp]); sm = trozos(mdl)
        pdf_all = Counter(NUM.findall("\n".join(t for t, e, _ in lp if not e))); md_all = Counter(NUM.findall("\n".join(mdl)))
        deficit = pdf_all - md_all                                 # perdidos a nivel documento (no están en ninguna parte)
        pool = Counter(deficit); det += detalle(m["id"], lp, deficit)
        for s in range(1, 17):
            if s in sp and s in sm:
                r = comparar(sp[s], sm[s], pool)
                for t, c in r["perdidos"].items(): por_tipo[tipo(t)] += c
                por_sec[s] += sum(r["perdidos"].values()); r.pop("perdidos"); filas.append(dict(id=m["id"], seccion=s, **r))
            else: filas.append(dict(id=m["id"], seccion=s, nota="seccion_no_detectada_en_" + ("pdf" if s not in sp else "md")))
        n_pdf, perd = sum(pdf_all.values()), sum(deficit.values())
        docs.append(dict(id=m["id"], n_pdf=n_pdf, perdidos=perd, recall_doc=round(1 - perd / n_pdf, 4) if n_pdf else None,
                         perdidos_ej=" ".join(f"{t}x{c}" if c > 1 else t for t, c in deficit.most_common(12))))
    cols = ["id", "seccion", "n_pdf", "n_md", "faltan", "faltan_perdidos", "sobran", "recall", "recall_ajustado", "cas_faltan", "faltan_ej", "perdidos_ej", "nota"]
    dcols = ["id", "token", "faltan", "candidatas", "clase", "tipo", "seccion", "pagina", "linea_pdf"]
    for nombre, c, datos in (("verificacion_numerica.csv", cols, filas), ("verificacion_documentos.csv", list(docs[0].keys()), docs), ("perdidos_detalle.csv", dcols, det)):
        with open(ing.MAN / nombre, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=c); w.writeheader(); w.writerows([{k: r.get(k) for k in c} for r in datos])
    ok = [r for r in filas if r.get("recall") is not None]; tp = sum(d["n_pdf"] for d in docs); tl = sum(d["perdidos"] for d in docs)
    sec_bajas = [r for r in ok if r["recall_ajustado"] < UMBRAL]; sec_reub = [r for r in ok if r["recall"] < UMBRAL <= r["recall_ajustado"]]
    por_clase = Counter(); docs_clase = {}
    for r in det: por_clase[r["clase"]] += r["faltan"]; docs_clase.setdefault(r["clase"], set()).add(r["id"])
    print(f"documentos: {len(docs)} | números del PDF (sin encabezados/pies): {tp} | perdidos (no están en ninguna parte del md): {tl} -> recall de documento {1 - tl / tp:.4f}")
    print(f"secciones con recall < {UMBRAL} por orden de lectura distinto (texto REUBICADO, no perdido): {len(sec_reub)} | por pérdida real: {len(sec_bajas)} en {len({r['id'] for r in sec_bajas})} docs | CAS faltantes: {len([r for r in ok if r['cas_faltan']])}")
    print("perdidos por tipo de número:", dict(por_tipo), "| por sección (asignados):", dict(sorted(por_sec.items(), key=lambda kv: -kv[1])[:6]))
    print("perdidos por clase:", {k: f"{v} números en {len(docs_clase[k])} docs" for k, v in por_clase.items()})
    print("sin sección detectable:", [(r['id'], r['seccion']) for r in filas if r.get('nota')])
    print("perdidos de clase 'otro' (no son caja NFPA/HMIS), uno por fila:")
    for r in sorted([r for r in det if r["clase"] == "otro"], key=lambda r: (-r["faltan"], r["id"]))[:14]:
        print(f"  {r['id']} §{r['seccion']} p.{r['pagina']}: {r['token']}x{r['faltan']} ({r['candidatas']} candidatas) | {r['linea_pdf'][:80]}")

if __name__ == "__main__":
    main()
