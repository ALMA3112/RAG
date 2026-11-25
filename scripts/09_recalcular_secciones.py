#!/usr/bin/env python3
"""Recalcula secciones, rangos de pagina y estados de todos los documentos con el detector de titulos estricto (04).
No modifica ningun Markdown. Conserva el estado REPARADO_ESTRUCTURA. Informa de cada cambio."""
import json, importlib.util, pathlib

def cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, pathlib.Path(__file__).with_name(nombre + ".py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

rep = cargar("06_reparar_md"); ing = rep.ing
cambios_estado, cambios_pag = [], []
for meta_f in sorted(ing.OUT.glob("FDS_*/meta.json")):
    m = json.loads(meta_f.read_text(encoding="utf-8")); lines = (meta_f.parent / m["md"]).read_text(encoding="utf-8").splitlines()
    reparadas = {r["seccion"] for r in m.get("reparaciones", [])}
    sec_md, est = rep.estados_de(lines, pathlib.Path(m["ruta_pdf"]), reparadas)
    for s in range(1, 17):
        if est[str(s)] != m["estados"].get(str(s)): cambios_estado.append((m["id"], s, m["estados"].get(str(s)), est[str(s)]))
        antes = next((x["pag_ini"] for x in m["secciones"] if x["seccion"] == s), None)
        if antes != (sec_md[s]["pag_ini"] if s in sec_md else None): cambios_pag.append((m["id"], s, antes, sec_md[s]["pag_ini"] if s in sec_md else None))
    m["secciones"], m["estados"] = list(sec_md.values()), est
    meta_f.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
ing.consolidar()
print(f"cambios de estado: {len(cambios_estado)} {cambios_estado[:12]}")
print(f"secciones cuya página de inicio cambió: {len(cambios_pag)} en {len({c[0] for c in cambios_pag})} docs {cambios_pag[:8]}")
