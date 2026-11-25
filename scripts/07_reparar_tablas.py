#!/usr/bin/env python3
"""Fase A2: reparación determinista de filas de tabla fusionadas + inventario de tablas sospechosas.
Regla: una fila de 2 celdas con k>=2 'CAS:' en una celda y exactamente k rangos de porcentaje en la otra se separa en
k filas (i-ésimo ingrediente <-> i-ésimo porcentaje; el orden se verificó contra el PDF). Se comprueba que no se agregue
ni se pierda ningún token. Lo demás NO se repara (exigiría inferir): solo se registra en tablas_sospechosas.csv."""
import re, json, csv, importlib.util, pathlib

spec = importlib.util.spec_from_file_location("ing", pathlib.Path(__file__).with_name("04_ingesta.py"))
ing = importlib.util.module_from_spec(spec); spec.loader.exec_module(ing)

CAS = re.compile(r"CAS:?\s*\d{2,7}-\d{2}-\d")
PCT = re.compile(r"[<>≤≥]?\s*\d+(?:[.,]\d+)?\s*%?\s*[-–]\s*[<>≤≥]?\s*\d+(?:[.,]\d+)?\s*%")
ENTRY = re.compile(r"\s*(.+?CAS:?\s*\d{2,7}-\d{2}-\d)")
SEP = re.compile(r"\|[\s\-:|]+\|?")
norm_ws = lambda s: re.sub(r"\s+", " ", s).strip()
tokens = lambda s: sorted(t for t in s.replace("|", " ").split())

def es_fila(l):
    s = l.strip(); return s.startswith("|") and not SEP.fullmatch(s)

def partir_fila(line):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) != 2: return None
    for ia, ib in ((0, 1), (1, 0)):
        a, b = cells[ia], cells[ib]; k = len(CAS.findall(a))
        if k < 2: continue
        entries, pcts = ENTRY.findall(a), [p.strip() for p in PCT.findall(b)]
        if len(entries) != k or len(pcts) != k: return None
        if norm_ws(" ".join(entries)) != norm_ws(a) or PCT.sub("", b).strip(): return None
        rows = [f"| {e.strip()} | {p} |" if ia == 0 else f"| {p} | {e.strip()} |" for e, p in zip(entries, pcts)]
        if tokens(" ".join(rows)) != tokens(line): return None          # nada agregado ni perdido
        return rows
    return None

def seccion_de(sec_md, i):
    prev = [n for n, s in sec_md.items() if s["linea"] <= i]
    return max(prev, key=lambda n: sec_md[n]["linea"]) if prev else None

def n_fusionadas(lines):
    return sum(1 for l in lines if l.lstrip().startswith("|") and any(len(CAS.findall(c)) >= 2 for c in l.split("|")))

def main():
    rep, sosp = [], []
    for mp in sorted(ing.OUT.glob("FDS_*/FDS_*.md")):
        if mp.name.endswith(".docling.md"): continue
        did = mp.stem; lines = mp.read_text(encoding="utf-8").split("\n")
        pg = ing.paginas_por_linea(lines); sec = ing.secciones_md(lines, pg)
        nuevas, cambios = [], []
        for i, l in enumerate(lines):
            filas = partir_fila(l) if es_fila(l) else None
            if filas:
                cambios.append(dict(tipo="fila_tabla_fusionada", seccion=seccion_de(sec, i), linea=i, pagina=pg[i], antes=norm_ws(l)[:200], filas_nuevas=len(filas)))
                nuevas.extend(filas)
            else:
                nuevas.append(l)
        meta_f = mp.parent / "meta.json"; meta = json.loads(meta_f.read_text(encoding="utf-8"))
        if cambios:
            mp.write_text("\n".join(nuevas), encoding="utf-8"); lines = nuevas
            pg = ing.paginas_por_linea(lines); sec = ing.secciones_md(lines, pg)
            meta["reparaciones_tablas"] = meta.get("reparaciones_tablas", []) + cambios
            meta["qa"]["filas_tabla_fusionadas"] = n_fusionadas(lines)
            meta_f.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        for i, l in enumerate(lines):
            if not es_fila(l): continue
            cells = l.strip().strip("|").split("|")
            motivos = (["celdas_con_varios_CAS"] if any(len(CAS.findall(c)) >= 2 for c in cells) else []) + (["celda_muy_larga"] if any(len(c) > 350 for c in cells) else [])
            if motivos:
                sosp.append(dict(id=did, seccion=seccion_de(sec, i), linea=i, pagina=pg[i], motivo="+".join(motivos), estado="NO_REPARADA_requiere_inferencia", texto=norm_ws(l)[:200]))
    filas = [dict(id=json.loads(p.read_text(encoding="utf-8"))["id"], **r) for p in sorted(ing.OUT.glob("FDS_*/meta.json"))
             for r in json.loads(p.read_text(encoding="utf-8")).get("reparaciones_tablas", [])]
    for nombre, datos in (("reparaciones_tablas.csv", filas), ("tablas_sospechosas.csv", sosp)):
        if datos:
            with open(ing.MAN / nombre, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(datos[0].keys())); w.writeheader(); w.writerows(datos)
    ing.consolidar()
    print(f"filas reparadas (acumulado): {len(filas)} en {sorted({r['id'] for r in filas})}")
    print(f"tablas sospechosas sin reparar: {len(sosp)} en {sorted({r['id'] for r in sosp})}")

if __name__ == "__main__":
    main()
