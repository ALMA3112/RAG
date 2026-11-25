#!/usr/bin/env python3
"""Fase A2: verificación numérica PDF vs Markdown, por documento y sección.
Compara el multiconjunto de números (valores, porcentajes, CAS, códigos UN) del texto del PDF contra el del Markdown.
Excluye del PDF los encabezados/pies (líneas con palabras que se repiten en >=60% de las páginas) y del Markdown las
imágenes y comentarios. Una sección con recall bajo o CAS faltantes es candidata a revisión manual contra el PDF."""
import re, json, csv, subprocess, importlib.util, pathlib
from collections import Counter

spec = importlib.util.spec_from_file_location("ing", pathlib.Path(__file__).with_name("04_ingesta.py"))
ing = importlib.util.module_from_spec(spec); spec.loader.exec_module(ing)

NUM, CASN = re.compile(r"\d+(?:[.,]\d+)?"), re.compile(r"\b\d{2,7}-\d{2}-\d\b")
digits = lambda s: re.sub(r"\d+", "#", s).strip()
UMBRAL = 0.95

def lineas_pdf(pdf, n_pag):
    pages = [subprocess.run(["pdftotext", "-f", str(k), "-l", str(k), str(pdf), "-"], capture_output=True, text=True).stdout.splitlines() for k in range(1, n_pag + 1)]
    freq = Counter(digits(l) for p in pages for l in {x.strip() for x in p} if l.strip())
    corte = max(3, 0.6 * n_pag)
    ruido = lambda l: re.search(r"[A-Za-zÁ-úñÑ]{3,}", l) and freq[digits(l.strip())] >= corte
    return [l for p in pages for l in p if l.strip() and not ruido(l)]

def lineas_md(texto):
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S); texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", texto)
    return [l for l in texto.split("\n") if l.strip() and not re.fullmatch(r"\|[\s\-:|]+\|?", l.strip())]

def trozos(lines):
    hits = sorted(ing.heading_hits(lines).items(), key=lambda kv: kv[1]); out = {}
    for k, (n, i) in enumerate(hits):
        out[n] = "\n".join(lines[i:hits[k + 1][1] if k + 1 < len(hits) else len(lines)])
    return out

def comparar(t_pdf, t_md):
    a, b = Counter(NUM.findall(t_pdf)), Counter(NUM.findall(t_md)); falta, sobra = a - b, b - a
    n = sum(a.values()); cas = set(CASN.findall(t_pdf)) - set(CASN.findall(t_md))
    return dict(n_pdf=n, n_md=sum(b.values()), faltan=sum(falta.values()), sobran=sum(sobra.values()),
                recall=round(1 - sum(falta.values()) / n, 3) if n else None, cas_faltan=" ".join(sorted(cas)),
                faltan_ej=" ".join(f"{t}x{c}" if c > 1 else t for t, c in falta.most_common(8)),
                sobran_ej=" ".join(f"{t}x{c}" if c > 1 else t for t, c in sobra.most_common(8)))

def main():
    filas = []
    for meta_f in sorted(ing.OUT.glob("FDS_*/meta.json")):
        m = json.loads(meta_f.read_text(encoding="utf-8")); md_f = meta_f.parent / m["md"]
        sp = trozos(lineas_pdf(pathlib.Path(m["ruta_pdf"]), m["paginas_pdf"])); sm = trozos(lineas_md(md_f.read_text(encoding="utf-8")))
        for s in range(1, 17):
            if s in sp and s in sm: filas.append(dict(id=m["id"], seccion=s, **comparar(sp[s], sm[s])))
            else: filas.append(dict(id=m["id"], seccion=s, n_pdf=None, n_md=None, faltan=None, sobran=None, recall=None, cas_faltan="", faltan_ej="", sobran_ej="", nota="seccion_no_detectada_en_" + ("pdf" if s not in sp else "md")))
    cols = ["id", "seccion", "n_pdf", "n_md", "faltan", "sobran", "recall", "cas_faltan", "faltan_ej", "sobran_ej", "nota"]
    with open(ing.MAN / "verificacion_numerica.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows([{c: r.get(c) for c in cols} for r in filas])
    ok = [r for r in filas if r["recall"] is not None]
    tp, fl = sum(r["n_pdf"] for r in ok), sum(r["faltan"] for r in ok)
    bajos = sorted([r for r in ok if r["recall"] < UMBRAL], key=lambda r: r["recall"])
    print(f"documentos: {len({r['id'] for r in filas})} | secciones comparadas: {len(ok)} | números en PDF: {tp} | faltan en md: {fl} (recall global {1 - fl / tp:.4f})")
    print(f"secciones con recall < {UMBRAL}: {len(bajos)} en {len({r['id'] for r in bajos})} docs | con CAS faltantes: {len([r for r in ok if r['cas_faltan']])}")
    print("sin sección detectable:", len([r for r in filas if r['recall'] is None]))
    for r in bajos[:15]: print(f"  {r['id']} §{r['seccion']}: recall {r['recall']} ({r['faltan']}/{r['n_pdf']} faltan) | faltan: {r['faltan_ej']}")

if __name__ == "__main__":
    main()
