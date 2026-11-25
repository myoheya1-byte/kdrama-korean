# Builds one listen page per expression (NN.html) for a book, from the book's body markdown + its audio folder.
# Usage: python make_pages.py romance   |   python make_pages.py palace
import html, pathlib, re, sys

SITE = pathlib.Path(__file__).parent
ROOT = SITE.parent
BOOKS = {
    "romance": dict(md="04_1권_본문_전체.md", label="Romance", bg="#FFF8F8", accent="#EC8096", deep="#A03E5C",
                    text="#46323C", soft="#FBD9E3", line="#F2BFCD", tint="#FFF3F6"),
    "palace": dict(md="13_2권_본문_전체.md", label="Historical ① The Palace", bg="#FBF8F1", accent="#B8913A", deep="#1F2F55",
                   text="#2E2A33", soft="#EADFC6", line="#D9C79A", tint="#FAF5EA"),
    "christmas": dict(md="25_크리스마스편_본문_전체.md", label="Winter & Christmas", bg="#FFF9F3", accent="#B8213A", deep="#1F2A4D",
                      text="#2B2F45", soft="#F9DCDF", line="#EBCFCF", tint="#EAF2FA", unit="Day"),
    "office": dict(md="23_3권_본문_전체.md", label="Office", bg="#F5F9FD", accent="#4A8CC4", deep="#1F3A5F",
                   text="#2A3340", soft="#DCEBF7", line="#C5DCEF", tint="#EEF4FA"),
    "family": dict(md="34_4권_본문_전체.md", label="Family", bg="#FFFAF4", accent="#D9762B", deep="#6B3A22",
                   text="#3D2E26", soft="#FCEBDB", line="#EFD2B5", tint="#FFF3E6"),
    "school": dict(md="40_5권_본문_전체.md", label="School", bg="#F9FCF7", accent="#3F8F4E", deep="#225630",
                   text="#2C3A2F", soft="#E8F3E3", line="#CDE3C3", tint="#F1F8ED"),
    "travel": dict(md="47_여행편_본문_전체.md", label="Travel", bg="#F6FBFB", accent="#E2703A", deep="#0F6E7C",
                   text="#1E2B30", soft="#E6F4F4", line="#C9E4E4", tint="#EEF7F7"),
    "food": dict(md="54_음식편_본문_전체.md", label="Food", bg="#FFF9F2", accent="#C23822", deep="#4E2616",
                 text="#3A2A22", soft="#FBE3D6", line="#F0CDB8", tint="#FFF3EA"),
    "revenge": dict(md="60_복수막장편_본문_전체.md", label="Revenge", bg="#FBF8FC", accent="#961C4E", deep="#3A143E",
                    text="#2F2433", soft="#F3E3EE", line="#E3CCDD", tint="#F4EFF8"),
}

def parse_travel(md):
    """47 format: ### NN. title / - ro: / - en: / - You|They: ko | ro | en (You, They, You)."""
    out = []
    for n, title, b in re.findall(r"(?ms)^### (\d+)\. (.+?)$(.*?)(?=^### |^## |\Z)", md):
        g = lambda k: re.search(rf"^- {k}: (.+)$", b, re.M).group(1).strip()
        dl = [(("A" if w == "You" else "B"), ko.strip(), ro.strip(), en.strip())
              for w, ko, ro, en in re.findall(r"^- (You|They): (.+?) \| (.+?) \| (.+)$", b, re.M)]
        out.append(dict(n=int(n), title=re.sub(r"\s*\(샘플\)", "", title).strip(), roman=g("ro"), meaning=g("en"), ex=None, dl=dl))
    return out

def parse(md):
    out = []
    parts = re.split(r"(?m)^## (\d+)\. (.+)$", md)
    for i in range(1, len(parts), 3):
        n, title, body = int(parts[i]), parts[i + 1].strip(), parts[i + 2]
        roman = re.search(r"^\*\*(.+?)\*\*\s*$", body.strip(), re.M).group(1)
        meaning = re.search(r"\*\*Meaning:\*\*\s*(.+)", body).group(1).strip()
        ex = re.search(r"\*\*Example\*\*\n(.+)\n\*(.+)\*\n(.+)", body)
        # English line is optional: a wordless reply ("A: … *(silence)*") has none
        dl = re.findall(r"^([AB]):\s*(.*?)\s*\*\((.+)\)\*[ \t]*(?:\n—\s*(.+))?$", body, re.M)
        out.append(dict(n=n, title=title, roman=roman, meaning=meaning,
                        ex=(ex.group(1).strip(), ex.group(2).strip(), ex.group(3).strip()), dl=dl))
    return out

def plain(s):
    return html.escape(re.sub(r"\*\*?(.+?)\*\*?", r"\1", s))

def voices(book):
    """file name -> voice, read from the Typecast scripts (romance: 07 tags; palace: per-voice key)."""
    import json
    if book == "romance":
        t = (ROOT / "07_타입캐스트_대본_1권.txt").read_text(encoding="utf-8")
        kinds = ["word", "example", "dlg_a", "dlg_b"]
        tags = re.findall(r"^\d{3}\s+\[(.+?)\]", t, re.M)
        return {f"{i // 4 + 1:02d}_{kinds[i % 4]}": v for i, v in enumerate(tags)}, ["은경", "서준"]
    if book in ("christmas", "office", "family", "school", "travel", "food", "revenge"):
        key = json.loads((SITE / f"{'xmas' if book == 'christmas' else book}_voice_key.json").read_text(encoding="utf-8"))["order"]
        return {f: v for v, fs in key.items() for f in fs}, ["은경", "서준"]
    key = json.loads((SITE / "palace_voice_key.json").read_text(encoding="utf-8"))["by_voice"]
    return {f: v for v, fs in key.items() for f in fs}, ["서현", "필재", "서준"]

def page(book, c, e, audio):
    vmap, order = VOICES
    def vc(name):
        # palace dialogue files are dlg_1/dlg_2 in the key; romance uses dlg_a/dlg_b in both places
        return "v%d" % order.index(vmap.get(name, order[0]))
    nn = f"{e['n']:02d}"
    def snd(name):
        return f'<audio controls preload="auto" src="audio/{name}.mp3"></audio>' if name in audio else '<div class="quiet">(no words — just a look)</div>'
    rows = []
    k = 0
    for who, ko, ro, en in e["dl"]:
        silent = ko.strip(" .…") == ""          # a wordless beat ("…") has no audio file
        if not silent:
            k += 1
        # romance files are named by speaker (dlg_a / dlg_b); palace files by spoken-line order (dlg_1, dlg_2)
        name = f"{nn}_dlg_{who.lower()}" if book != "palace" else (f"{nn}_dlg_{k}" if not silent else f"{nn}_silent")
        badge = who
        if book == "travel":                    # travel: You / They / You → dlg_a, dlg_b, dlg_c
            name, badge = f"{nn}_dlg_{'abc'[k - 1]}", ("You" if who == "A" else "They")
        rows.append(f'<div class="card {vc(name)} {who.lower()}"><div class="ko"><span class="who">{badge}</span>{plain(ko)}</div>'
                    f'<div class="ro">{plain(ro)}</div><div class="en">{plain(en)}</div>{snd(name)}</div>')
    return f"""<!doctype html><html lang="ko" translate="no"><head><meta charset="utf-8"><meta name="google" content="notranslate">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{nn} {html.escape(e['title'])} · K-Drama Talk {c['label']}</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;font-family:-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;background:{c['bg']};color:{c['text']}}}
.wrap{{max-width:460px;margin:0 auto;padding:28px 20px 40px}}
.top{{font-size:12px;letter-spacing:.2em;color:{c['accent']};font-weight:700;text-transform:uppercase}}
.no{{display:inline-block;background:{c['deep']};color:#fff;border-radius:50%;width:38px;height:38px;line-height:38px;text-align:center;font-weight:800;margin-top:14px}}
h1{{font-size:42px;color:{c['deep']};margin:8px 0 0;line-height:1.2}}
.rom{{color:{c['accent']};font-size:18px}}.mean{{font-size:16px;font-weight:600;margin:6px 0 10px}}
.lab{{font-size:11px;letter-spacing:.14em;color:{c['accent']};font-weight:700;margin-top:22px;text-transform:uppercase}}
.card{{background:#fff;border:1px solid {c['line']};border-radius:18px;padding:14px 16px;margin:10px 0}}
.card.v1{{background:{c['soft']};border-color:{c['line']}}}
.card.v2{{background:{c['tint']};border-color:{c['line']}}}
.vk{{font-size:12px;margin:2px 0 6px;color:#888}}.sw{{display:inline-block;padding:0 !important;width:12px;height:12px;border-radius:3px;border:1px solid {c['line']};vertical-align:-2px;margin:0 4px 0 10px;background:#fff}}
.ko{{font-weight:700;color:{c['deep']};font-size:18px}}.ro{{font-size:13px;color:{c['accent']};font-style:italic;margin-top:2px}}.en{{font-size:14px;margin:2px 0 8px}}
.who{{display:inline-block;background:{c['accent']};color:#fff;border-radius:50%;width:24px;height:24px;line-height:24px;text-align:center;font-size:12px;font-weight:700;margin-right:6px}}
.b .who{{background:{c['deep']}}}{'.who{width:auto;min-width:24px;padding:0 9px;border-radius:12px}' if book == 'travel' else ''}
audio{{width:100%;height:40px}}.quiet{{font-size:13px;font-style:italic;color:#999}}
.nav{{display:flex;justify-content:space-between;margin-top:26px;font-size:14px}}.nav a{{color:{c['deep']};text-decoration:none;font-weight:700}}
.spd{{display:flex;gap:8px;margin:8px 0 2px}}.spd button{{border:1.5px solid {c['accent']};background:#fff;color:{c['deep']};border-radius:20px;padding:6px 14px;font-size:14px;font-weight:700}}
.spd button.on{{background:{c['deep']};border-color:{c['deep']};color:#fff}}
.foot{{margin-top:22px;font-size:12px;color:#aaa;text-align:center}}
</style></head><body><div class="wrap">
<div class="top">K-Drama Talk · {c['label']}</div>
<div class="no">{nn}</div><h1>{html.escape(e['title'])}</h1><div class="rom">{html.escape(e['roman'])}</div><div class="mean">{plain(e['meaning'])}</div><div class="spd"><button id="n" class="on" onclick="sp(1)">Normal</button><button id="s" onclick="sp(0.75)">🐢 Slow</button></div><div class="vk">Voices:{''.join(f'<span class="sw card v{k}"></span>{v}' for k, v in enumerate(VOICES[1]))}</div>

<div class="lab">Word</div>
<div class="card {vc(nn + '_word')}"><div class="ko">{html.escape(e['title'])}</div><div class="ro">{html.escape(e['roman'])}</div>{snd(nn + '_word')}</div>

{'' if not e['ex'] else f"""<div class="lab">Example</div>
<div class="card {vc(nn + '_example')}"><div class="ko">{plain(e['ex'][0])}</div><div class="ro">{plain(e['ex'][1])}</div><div class="en">{plain(e['ex'][2])}</div>{snd(nn + '_example')}</div>"""}

<div class="lab">Mini dialogue</div>
{''.join(rows)}
<div class="nav"><span>{f'<a href="{e["n"] - 1:02d}.html">← {e["n"] - 1:02d}</a>' if e['n'] > 1 else ''}</span><a href="index.html">All {TOTAL}</a><span>{f'<a href="{e["n"] + 1:02d}.html">{e["n"] + 1:02d} →</a>' if e['n'] < TOTAL else ''}</span></div>
<div class="foot">Korean audio made with AI voices, checked by a native speaker · ULBOM</div>
</div><script>
function sp(r){{document.querySelectorAll('audio').forEach(a=>{{a.playbackRate=r;a.preservesPitch=true;a.defaultPlaybackRate=r}});
document.getElementById('n').classList.toggle('on',r==1);document.getElementById('s').classList.toggle('on',r!=1);
try{{localStorage.setItem('kdt-speed',r)}}catch(e){{}}}}
try{{var r=parseFloat(localStorage.getItem('kdt-speed'));if(r&&r!=1)sp(r)}}catch(e){{}}
</script></body></html>"""

def main(book):
    c = BOOKS[book]
    global VOICES
    VOICES = voices(book)
    entries = (parse_travel if book == "travel" else parse)((ROOT / c["md"]).read_text(encoding="utf-8"))
    global TOTAL
    TOTAL = len(entries)
    d = SITE / book; (d / "audio").mkdir(parents=True, exist_ok=True)
    audio = {p.stem for p in (d / "audio").glob("*.mp3")}
    for e in entries:
        (d / f"{e['n']:02d}.html").write_text(page(book, c, e, audio), encoding="utf-8")
    links = "".join(f'<a class="it" href="{e["n"]:02d}.html"><b>{e["n"]:02d}</b> {html.escape(e["title"])}</a>' for e in entries)
    (d / "index.html").write_text(f"""<!doctype html><html lang="ko" translate="no"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>K-Drama Talk {c['label']} · Audio</title><style>body{{margin:0;font-family:-apple-system,"Malgun Gothic",sans-serif;background:{c['bg']};color:{c['text']}}}
.wrap{{max-width:460px;margin:0 auto;padding:28px 20px}}h1{{color:{c['deep']};font-size:26px}}.it{{display:block;padding:12px 14px;margin:6px 0;background:#fff;border:1px solid {c['line']};border-radius:12px;color:{c['deep']};text-decoration:none;font-size:17px}}.it b{{color:{c['accent']};margin-right:8px}}</style></head>
<body><div class="wrap"><h1>K-Drama Talk · {c['label']}</h1>{links}</div></body></html>""", encoding="utf-8")
    kinds = ("word", "dlg_a", "dlg_b", "dlg_c") if book == "travel" else ("word", "example")
    missing = [f"{e['n']:02d}_{k}" for e in entries for k in kinds if f"{e['n']:02d}_{k}" not in audio]
    print(book, len(entries), "pages; audio files", len(audio), "; missing word/example:", missing[:5])

main(sys.argv[1])
