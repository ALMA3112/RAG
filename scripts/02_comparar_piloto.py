import re, pathlib

SEC = {1:"identific",2:"peligro|hazard",3:"composici|ingredient",4:"primeros auxilios|first.aid",
       5:"incendio|lucha contra|fire",6:"vertido|derrame|accidental",7:"manipulaci|almacen|handling",
       8:"exposici|protecci[oó]n personal",9:"propiedades f|physical",10:"estabilidad|reactividad",
       11:"toxicol",12:"ecol[oó]gic|ecolog",13:"eliminaci|disposal",14:"transporte|transport",
       15:"reglament|regulat",16:"otra informaci|other information"}

def sec_re(n, k):
    return rf"(?im)^[#*_>|\s-]*(?:secci[oó]n|section)?\s*{n}(?!\d)\s*[.:)\-–]?\s*[^\n]{{0,30}}?(?:{k})"

def first_table(text, maxl=10):
    block = []
    for l in text.splitlines():
        if l.lstrip().startswith("|"): block.append(l[:150])
        elif block: break
    return block[:maxl]

print(f"{'archivo':58} {'palabras':>8} {'filas|':>7} {'img':>4} {'secc':>5}  faltan")
for p in sorted(pathlib.Path("data/pilot").glob("*.md")):
    t = p.read_text(encoding="utf-8")
    rows = sum(1 for l in t.splitlines() if l.lstrip().startswith("|"))
    found = [n for n, k in SEC.items() if re.search(sec_re(n, k), t)]
    miss = [n for n in SEC if n not in found]
    print(f"{p.name[:58]:58} {len(t.split()):8} {rows:7} {len(re.findall(r'!\[', t)):4} {len(found):4}/16  {miss}")

print("\n--- Primera tabla de FDS 36 ---")
for p in sorted(pathlib.Path("data/pilot").glob("FDS_36*.md")):
    print(f"\n[{p.name}]")
    print("\n".join(first_table(p.read_text(encoding='utf-8'))) or "(sin tabla)")
