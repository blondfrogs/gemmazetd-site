#!/usr/bin/env python3
"""Build codex.html from data/catalog.json (exported by the game's CatalogExportTests).

Workflow when game data changes:
  1. in the game repo: xcodebuild test ... -only-testing:GemMazeTDTests/CatalogExportTests
  2. here:            python3 tools/build_codex.py
  3. commit + push
"""
import json, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
cat = json.loads((ROOT / "data" / "catalog.json").read_text())

def esc(s): return html.escape(str(s))
def spd(cd): return f"{1/cd:.2f}/s" if cd else "—"
def num(x):  return f"{x:g}"

# ── Base gems: one card each with the tier ladder ────────────────────────────────────────────
gem_cards = []
for g in cat["gems"]:
    rows = "".join(
        f"<tr><td>{esc(t['name'])}</td><td class='num'>{num(t['damage'])}</td>"
        f"<td class='num'>{num(t['range'])}</td><td class='num'>{spd(t['cooldown'])}</td></tr>"
        for t in g["tiers"])
    type_chip = f"<span class='chip {'magic' if g['damageType']=='Magic' else 'phys'}'>{esc(g['damageType'])}</span>"
    tgt_chip = f"<span class='chip tgt'>{esc(g['targets'])}</span>"
    gem_cards.append(f"""
    <div class="gemcard">
      <div class="gemhead">
        <img src="data/thumbs/el-{esc(g['element'])}.png" alt="" width="46" height="46">
        <div><h3>{esc(g['name'])} <span class="code">({esc(g['code'])})</span></h3>
        <p class="effect">{esc(g['effect'])}</p></div>
      </div>
      <div class="chips">{type_chip}{tgt_chip}</div>
      <div class="tablewrap"><table>
        <tr><th>Tier</th><th>DMG</th><th>RNG</th><th>SPD</th></tr>{rows}
      </table></div>
    </div>""")

# ── Crafted towers: one table, grouped by recipe line ────────────────────────────────────────
towers = sorted(cat["towers"], key=lambda t: (t["line"], t["damage"]))
tower_rows, last_line = [], None
for t in towers:
    if t["line"] != last_line:
        tower_rows.append(f"<tr class='group'><td colspan='6'>{esc(t['line'])}</td></tr>")
        last_line = t["line"]
    name = esc(t["name"]) + (" <span class='elite'>★</span>" if t["elite"] else "")
    recipe = esc(" + ".join(t["ingredients"]))
    if t["secret"]: recipe += " <span class='chip abil'>Secret</span>"
    tower_rows.append(
        f"<tr><td class='namecell'><img src='data/thumbs/tower-{esc(t['slug'])}.png' alt='' width='34' height='34'>{name}</td>"
        f"<td>{recipe}</td><td class='num'>{num(t['damage'])}</td><td class='num'>{spd(t['cooldown'])}</td>"
        f"<td class='num'>{num(t['range'])}</td><td class='blurb'>{esc(t['blurb'])}</td></tr>")

# ── Creeps: sorted by first wave ─────────────────────────────────────────────────────────────
creeps = sorted(cat["creeps"], key=lambda c: (c["waves"][0] if c["waves"] else 99, c["name"]))
creep_rows = []
for c in creeps:
    chips = []
    if c["boss"]:        chips.append("<span class='chip boss'>👑 BOSS</span>")
    if c["flying"]:      chips.append("<span class='chip tgt'>Flying</span>")
    if c["magicImmune"]: chips.append("<span class='chip magic'>Magic-Immune</span>")
    if c["physImmune"]:  chips.append("<span class='chip phys'>Phys-Immune</span>")
    chips += [f"<span class='chip abil'>{esc(a)}</span>" for a in c["abilities"]]
    waves = ", ".join(str(w) for w in c["waves"]) or "—"
    mr = f"{round(c['magicResist']*100)}%"
    creep_rows.append(
        f"<tr><td class='num'>{waves}</td>"
        f"<td class='namecell'><img src='data/thumbs/creep-{esc(c['id'])}.png' alt='' width='34' height='34'>{esc(c['name'])}</td>"
        f"<td class='num'>{num(c['hp'])}</td><td class='num'>{num(c['armor'])}</td><td class='num'>{mr}</td>"
        f"<td class='num'>{num(c['speed'])}</td><td>{''.join(chips) or '—'}</td></tr>")

counts = cat["counts"]
page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Codex — Gem Maze TD</title>
<meta name="description" content="Every gem, crafted tower, and creep in Gem Maze TD — stats exported straight from the game's code.">
<link rel="icon" type="image/png" href="assets/favicon.png">
<style>
  :root {{ --bg:#0B1626; --panel:#14263F; --panel2:#1A2E49; --line:#23405F; --text:#EAF3FC;
          --dim:#97AFC7; --frost:#A8D4FF; --frost-deep:#5FA8E8; --gold:#F5CE62; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text); line-height:1.5;
    font-family:"Avenir Next", Avenir, -apple-system, system-ui, sans-serif;
    background-image:radial-gradient(900px 400px at 50% -8%, #16304F 0%, transparent 60%); }}
  main {{ max-width:1020px; margin:0 auto; padding:0 16px 80px; }}
  .topnav {{ position:sticky; top:0; z-index:20; display:flex; align-items:center; gap:18px;
    padding:10px 20px; border-bottom:1px solid var(--line);
    background:rgba(11,22,38,.78); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); }}
  .topnav .brand {{ display:flex; align-items:center; gap:10px; font-weight:800; color:var(--text);
    text-decoration:none; font-size:1.02rem; }}
  .topnav .brand img {{ width:30px; height:30px; border-radius:7px; }}
  .topnav a.link {{ color:var(--dim); text-decoration:none; font-weight:600; font-size:.95rem; }}
  .topnav a.link:hover, .topnav a.link.active {{ color:var(--frost); }}
  .topnav .spacer {{ flex:1; }}
  .topnav .beta-pill {{ color:#06240F; background:linear-gradient(180deg,#4ADE80,#16A34A);
    font-weight:700; font-size:.88rem; text-decoration:none; padding:8px 16px; border-radius:99px; }}
  @media (max-width:480px) {{ .topnav {{ gap:12px; padding:10px 14px; }} .topnav .brand span {{ display:none; }} }}
  h1 {{ font-size:2rem; font-weight:800; margin:10px 0 4px;
      background:linear-gradient(180deg,#FFF 20%,var(--frost) 90%);
      -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }}
  .sub {{ color:var(--dim); margin:0 0 18px; }}
  nav.jump {{ position:sticky; top:52px; z-index:5; display:flex; gap:8px; padding:10px 0;
    background:linear-gradient(180deg, var(--bg) 75%, transparent); }}
  nav.jump a {{ color:var(--frost); text-decoration:none; font-weight:700; font-size:.9rem;
    border:1px solid var(--line); border-radius:99px; padding:6px 14px; background:var(--panel); }}
  h2 {{ color:var(--frost); font-size:1.4rem; margin:40px 0 4px; }}
  .secsub {{ color:var(--dim); font-size:.92rem; margin:0 0 14px; }}
  .gemgrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:14px; }}
  .gemcard {{ background:var(--panel); border:1px solid var(--line); border-radius:14px; padding:14px; }}
  .gemhead {{ display:flex; gap:10px; align-items:center; }}
  .gemhead h3 {{ margin:0; font-size:1.05rem; }}
  .code {{ color:var(--dim); font-weight:600; font-size:.85rem; }}
  .effect {{ margin:2px 0 0; color:var(--dim); font-size:.85rem; }}
  .chips {{ margin:8px 0; }}
  .chip {{ display:inline-block; font-size:.7rem; font-weight:700; padding:2px 8px; border-radius:99px; margin:2px 4px 2px 0; }}
  .chip.phys {{ color:#9CC4EF; background:#16304F; }}
  .chip.magic {{ color:#CBA7F0; background:#2C1A45; }}
  .chip.tgt {{ color:#8FD8CD; background:#123B34; }}
  .chip.boss {{ color:var(--gold); background:#3A2B10; }}
  .chip.abil {{ color:#F0B860; background:#3A2B10; }}
  .elite {{ color:var(--gold); }}
  .secret {{ color:var(--dim); }}
  .tablewrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:10px; margin-top:6px; }}
  table {{ border-collapse:collapse; width:100%; font-size:.88rem; }}
  th {{ text-align:left; font-size:.68rem; letter-spacing:.09em; text-transform:uppercase; color:var(--dim);
      padding:8px 10px; background:var(--panel2); border-bottom:1px solid var(--line); white-space:nowrap; }}
  td {{ padding:7px 10px; border-bottom:1px solid var(--line); vertical-align:middle; }}
  tr:last-child td {{ border-bottom:none; }}
  td.num {{ font-variant-numeric:tabular-nums; white-space:nowrap; }}
  td.namecell {{ white-space:nowrap; font-weight:700; }}
  td.namecell img {{ vertical-align:middle; margin-right:8px; border-radius:6px; }}
  td.blurb {{ color:var(--dim); font-size:.84rem; min-width:220px; }}
  tr.group td {{ background:var(--panel2); color:var(--frost); font-weight:800; font-size:.8rem;
    letter-spacing:.06em; text-transform:uppercase; }}
  footer {{ margin-top:56px; padding-top:18px; border-top:1px solid var(--line);
    color:var(--dim); font-size:.85rem; text-align:center; }}
  footer a {{ color:var(--frost); }}
</style>
</head>
<body>
<nav class="topnav">
  <a class="brand" href="index.html"><img src="assets/favicon.png" alt=""><span>Gem Maze TD</span></a>
  <a class="link active" href="codex.html">Codex</a>
  <a class="link" href="index.html#notify">Launch news</a>
  <span class="spacer"></span>
  <a class="beta-pill" href="https://testflight.apple.com/join/R9X8shZE">Join the Beta</a>
</nav>
<main>
  <h1>The Codex</h1>
  <p class="sub">Every gem, crafted tower, and creep — exported straight from the game's code, so these ARE the live numbers. DMG per hit · SPD in attacks/sec · RNG in board cells.</p>
  <nav class="jump">
    <a href="#gems">Gems ({counts['gems']})</a>
    <a href="#towers">Towers ({counts['towers']})</a>
    <a href="#creeps">Creeps ({counts['creeps']})</a>
  </nav>

  <h2 id="gems">Base gems</h2>
  <p class="secsub">The 8 rollable gems. Two of a kind fuse one tier up; four fuse two tiers up. Tier 6 is combine-only.</p>
  <div class="gemgrid">{"".join(gem_cards)}</div>

  <h2 id="towers">Crafted towers</h2>
  <p class="secsub">Exact gem sets fuse into elite towers — the full tree, grouped by recipe line. ★ marks the elite tier of a line.</p>
  <div class="tablewrap"><table>
    <tr><th>Tower</th><th>Recipe</th><th>DMG</th><th>SPD</th><th>RNG</th><th>Effect</th></tr>
    {"".join(tower_rows)}
  </table></div>

  <h2 id="creeps">Creeps</h2>
  <p class="secsub">The full bestiary, in wave order. HP is the 1-player base before difficulty scaling; speed in authentic game units.</p>
  <div class="tablewrap"><table>
    <tr><th>Wave</th><th>Creep</th><th>HP</th><th>Armor</th><th>M-Res</th><th>Speed</th><th>Traits</th></tr>
    {"".join(creep_rows)}
  </table></div>

  <footer>
    Numbers exported from the live game code — if the game changes, this page regenerates.<br>
    <a href="index.html">Home</a> · <a href="https://testflight.apple.com/join/R9X8shZE">Join the beta</a>
  </footer>
</main>
</body>
</html>
"""
(ROOT / "codex.html").write_text(page)
print(f"codex.html written: {counts['gems']} gems, {counts['towers']} towers, {counts['creeps']} creeps")
