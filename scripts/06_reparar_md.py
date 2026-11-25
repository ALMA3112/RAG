#!/usr/bin/env python3
"""Reparaciones deterministas sobre el Markdown ya generado (Fase A2). Idempotente y con registro.
1) encabezado_en_linea: 'SECCIÓN N: TÍTULO' pegado en medio de un párrafo se separa en su propia línea con '## '.
   Solo se aplica a secciones que NO se detectan al inicio de línea. No se agrega ni se infiere ningún texto."""
import re, json, csv, importlib.util, pathlib

spec = importlib.util.spec_from_file_location("ing", pathlib.Path(__file__).with_name("04_ingesta.py"))
ing = importlib.util.module_from_spec(spec); spec.loader.exec_module(ing)

INLINE = re.compile(r"SECCI[OÓ]N\s+(\d{1,2})\s*:\s*(?=[A-ZÁÉÍÓÚÑ])")

def reparar_encabezados(md):
    lines = md.split("\n"); pg = ing.paginas_por_linea(lines)
    presentes = set(ing.heading_hits(lines)); cambios, out = [], []
    for i, l in enumerate(lines):
        cortes = []
        if not l.lstrip().startswith("#"):
            for m in INLINE.finditer(l):
                n = int(m.group(1))
                if m.start() > 0 and 1 <= n <= 16 and n not in presentes:
                    presentes.add(n); cortes.append((m.start(), n))
        for s, n in sorted(cortes, reverse=True):
            cambios.append(dict(tipo="encabezado_en_linea", seccion=n, linea=i, pagina=pg[i],
                                antes=l[max(0, s - 40):s].strip(), titulo=l[s:s + 80]))
            l = l[:s].rstrip() + "\n\n## " + l[s:]
        out.append(l)
    return "\n".join(out), sorted(cambios, key=lambda c: (c["linea"], c["seccion"]))

def estados_de(lines, pdf, reparadas):
    pg = ing.paginas_por_linea(lines); sec_md = ing.secciones_md(lines, pg)
    sec_pdf = ing.heading_hits(ing.pdftext(pdf).splitlines()); est = {}
    for s in range(1, 17):
        en_pdf, en_md = s in sec_pdf, s in sec_md
        est[str(s)] = ("REPARADO_ESTRUCTURA" if en_pdf and en_md and s in reparadas else "OK" if en_pdf and en_md else
                       "FALLO_EXTRACCION" if en_pdf else "SOLO_EN_MD_REVISAR" if en_md else "AUSENTE_EN_ORIGINAL")
    return sec_md, est

def main():
    tocados = []
    for mp in sorted(ing.OUT.glob("FDS_*/FDS_*.md")):
        if mp.name.endswith(".docling.md"): continue
        md = mp.read_text(encoding="utf-8"); nuevo, cambios = reparar_encabezados(md)
        if not cambios: continue
        mp.write_text(nuevo, encoding="utf-8")
        meta_f = mp.parent / "meta.json"; meta = json.loads(meta_f.read_text(encoding="utf-8"))
        reparadas = {c["seccion"] for c in cambios} | {r["seccion"] for r in meta.get("reparaciones", [])}
        sec_md, est = estados_de(nuevo.splitlines(), pathlib.Path(meta["ruta_pdf"]), reparadas)
        meta.update(secciones=list(sec_md.values()), estados=est, reparaciones=meta.get("reparaciones", []) + cambios)
        meta_f.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8"); tocados.append((mp.stem, [c["seccion"] for c in cambios]))
    filas = [dict(id=json.loads(p.read_text(encoding="utf-8"))["id"], **r) for p in sorted(ing.OUT.glob("FDS_*/meta.json"))
             for r in json.loads(p.read_text(encoding="utf-8")).get("reparaciones", [])]
    if filas:
        with open(ing.MAN / "reparaciones.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0].keys())); w.writeheader(); w.writerows(filas)
    ing.consolidar()
    print("documentos reparados en esta pasada:", tocados or "ninguno (ya estaba reparado)")

if __name__ == "__main__":
    main()
