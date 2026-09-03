#!/usr/bin/env python3
"""Generate the guide's SVG figures, tuned to the htmler blue theme.

The kit's grey/purple house style is re-hued to htmler's blue-forward palette.
Because the figures are inlined as static base64 images (no page CSS reaches
them), every colour is chosen to work on BOTH the dark (#0b0d12) and light
(#ffffff) themes at once. The trick: a mid-slate around luminance ~0.2 gives
roughly 4.3:1 contrast three ways — white text sitting on the fill, and the
same colour used as ink on either background.

  * slate blue  #6B7B94  (neutral boxes, connectors, axes, labels)
  * blue        #3E7CC0  (highlighted / "after" boxes)         + dark #2F5F98
  * teal        #1F918C  (positive "result" accent)
  * amber       #D9922B  (warning / spill; dark text on fill)
  * red         #D65A5F  (problem callouts)
  * muted       #9AA0B4  (captions)
  * white       #FFFFFF  (text inside dark fills)
  * 1.5pt wide rules, Aptos / system sans font stack

Run:  python3 scripts/gen_figures.py
Output: <chapter>/figures/*.svg
"""
import base64
import io
import os
import re

# ── House-style constants (htmler blue theme, dual light/dark legible) ───────
GREY = "#6B7B94"
GREY_D = "#55637A"
PURPLE = "#3E7CC0"
PURPLE_D = "#2F5F98"
TEAL = "#1F918C"
AMBER = "#D9922B"
RED = "#D65A5F"
WHITE = "#FFFFFF"
LIGHT = "#9AA0B4"
INK_DARK = "#1F2433"  # text on light (amber) fills
# Hand-drawn Excalidraw look: Virgil is embedded per-figure (see _font_face);
# 'Segoe Print'/cursive are only fallbacks if the embed ever fails.
FONT = "'Virgil','Segoe Print','Comic Sans MS',cursive"
RULE = 1.5  # pt wide rules

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "fonts", "JetBrainsMonoNerdFont-Regular.woff2")
_FACE_CACHE = {}


def _font_face(text):
    """Return a <style> block embedding a Virgil subset for `text`.

    The figures are inlined as base64 <img> data URIs, and browsers do not
    fetch external fonts for <img>-loaded SVGs — so the hand-drawn font must
    travel *inside* each SVG. We subset to the glyphs actually used to keep
    each figure tiny (~8-14 KB)."""
    # Subset to exactly the glyphs this figure uses (plus a space) so each
    # embedded font stays as small as possible.
    key = "".join(sorted(set(text) | {" "}))
    if key in _FACE_CACHE:
        return _FACE_CACHE[key]
    try:
        from fontTools import subset as _subset
        opts = _subset.Options()
        opts.flavor = "woff2"
        opts.desubroutinize = True
        opts.ignore_missing_unicodes = True
        font = _subset.load_font(FONT_PATH, opts)
        ss = _subset.Subsetter(options=opts)
        ss.populate(text=key)
        ss.subset(font)
        buf = io.BytesIO()
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        face = ("<style>@font-face{font-family:'Virgil';font-style:normal;"
                "font-weight:400;src:url(data:font/woff2;base64," + b64 +
                ") format('woff2');}</style>")
    except Exception as exc:  # pragma: no cover - fonttools optional
        print("  ! font embed skipped:", exc)
        face = ""
    _FACE_CACHE[key] = face
    return face


# ── Primitive builders ──────────────────────────────────────────────────────
def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def defs():
    """Arrowhead markers in each ink colour."""
    marks = []
    for name, col in (("g", GREY), ("p", PURPLE), ("t", TEAL),
                      ("r", RED), ("a", AMBER), ("l", LIGHT)):
        marks.append(
            f'<marker id="ah-{name}" viewBox="0 0 10 10" refX="8.5" refY="5" '
            f'markerWidth="4.5" markerHeight="4.5" orient="auto-start-reverse">'
            f'<path d="M0 0L10 5L0 10z" fill="{col}"/></marker>')
    return "<defs>" + "".join(marks) + "</defs>"


def rrect(x, y, w, h, fill, rx=9, stroke=None, sw=RULE, dash=None, opacity=None):
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" '
         f'fill="{fill}"')
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw}"'
    if dash:
        s += f' stroke-dasharray="{dash}"'
    if opacity is not None:
        s += f' opacity="{opacity}"'
    return s + "/>"


def tspan_lines(x, cy, lines, fill, size, weight, lh):
    """Vertically centred multiline <text>."""
    n = len(lines)
    y0 = cy - (n - 1) * lh / 2.0
    out = [f'<text x="{x}" y="{y0}" fill="{fill}" font-family="{FONT}" '
           f'font-size="{size}" font-weight="{weight}" text-anchor="middle" '
           f'dominant-baseline="central">']
    for i, ln in enumerate(lines):
        dy = 0 if i == 0 else lh
        out.append(f'<tspan x="{x}" dy="{dy}">{esc(ln)}</tspan>')
    out.append("</text>")
    return "".join(out)


def box(x, y, w, h, lines, fill=GREY, tcol=WHITE, size=13, weight=600,
        rx=9, lh=16, stroke=None, sw=RULE, dash=None):
    if isinstance(lines, str):
        lines = [lines]
    r = rrect(x, y, w, h, fill, rx=rx, stroke=stroke, sw=sw, dash=dash)
    t = tspan_lines(x + w / 2.0, y + h / 2.0, lines, tcol, size, weight, lh)
    return r + t


def obox(x, y, w, h, lines, stroke=GREY, tcol=GREY, size=13, weight=600,
         rx=9, lh=16, sw=RULE, dash=None, fill="none"):
    """Outlined box (transparent fill) with coloured text."""
    r = rrect(x, y, w, h, fill, rx=rx, stroke=stroke, sw=sw, dash=dash)
    t = tspan_lines(x + w / 2.0, y + h / 2.0, lines if isinstance(lines, list)
                    else [lines], tcol, size, weight, lh)
    return r + t


def text(x, y, s, fill=GREY, size=13, weight=600, anchor="middle",
         italic=False, mono=False):
    fam = ("'SFMono-Regular',ui-monospace,'JetBrains Mono',Consolas,monospace"
           if mono else FONT)
    st = ""  # italics disabled: the hand-drawn font is hard to read slanted
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-family="{fam}" '
            f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}"'
            f'{st} dominant-baseline="central">{esc(s)}</text>')


def line(x1, y1, x2, y2, col=GREY, sw=RULE, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" '
            f'stroke-width="{sw}"{d}/>')


def _mk(col):
    return {GREY: "g", PURPLE: "p", TEAL: "t", RED: "r", AMBER: "a",
            LIGHT: "l"}.get(col, "g")


def arrow(x1, y1, x2, y2, col=GREY, sw=RULE, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" '
            f'stroke-width="{sw}" marker-end="url(#ah-{_mk(col)})"{d}/>')


def path(d, col=GREY, sw=RULE, dash=None, arrow_end=False, fill="none"):
    dd = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#ah-{_mk(col)})"' if arrow_end else ""
    return (f'<path d="{d}" fill="{fill}" stroke="{col}" stroke-width="{sw}"'
            f'{dd}{m}/>')


def cylinder(x, y, w, h, fill=GREY, tcol=WHITE, lines=None, size=12,
             stroke=None, sw=RULE):
    """Database / memory cylinder."""
    ry = min(h * 0.16, 14)
    st = (f' stroke="{stroke}" stroke-width="{sw}"') if stroke else ""
    body = (f'<path d="M{x} {y+ry} A{w/2} {ry} 0 0 0 {x+w} {y+ry} '
            f'L{x+w} {y+h-ry} A{w/2} {ry} 0 0 1 {x} {y+h-ry} Z" '
            f'fill="{fill}"{st}/>')
    top = (f'<ellipse cx="{x+w/2}" cy="{y+ry}" rx="{w/2}" ry="{ry}" '
           f'fill="{fill}"{st}/>')
    lip = (f'<path d="M{x} {y+ry} A{w/2} {ry} 0 0 0 {x+w} {y+ry}" '
           f'fill="none" stroke="{WHITE}" stroke-width="1" opacity="0.35"/>')
    t = ""
    if lines:
        t = tspan_lines(x + w / 2.0, y + h / 2.0 + ry / 2, lines, tcol, size,
                        600, 15)
    return body + top + lip + t


def svg(w, h, body, title=""):
    t = f"<title>{esc(title)}</title>" if title else ""
    used = "".join(re.findall(r'>([^<]*)<', body)) + title
    face = _font_face(used)
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" font-family="{FONT}">{face}{t}{defs()}'
            f'{body}</svg>\n')


def write(rel_path, content):
    full = os.path.join(REPO_ROOT, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print("wrote", rel_path, f"({len(content)} bytes)")


# ── Before/after "code card" primitives ─────────────────────────────────────
MONO = ("'SFMono-Regular',ui-monospace,'JetBrains Mono',Menlo,"
        "Consolas,monospace")
CARD_BG = "#232A35"          # self-contained dark code card (theme-independent)
CODE_FG = "#D7DCE6"
CODE_DIM = "#8892A5"
CODE_HI = "#7FC4FF"          # changed / highlighted line
CODE_GOOD = "#83CEA3"        # added
CODE_BAD = "#E98A90"         # removed
LBL_BEFORE = "#9AA0B4"
LBL_AFTER = "#7FC4FF"
PAD = 14
LH = 19
CSIZE = 12.5
CHARW = 7.55
LABEL_AREA = 28
BOTTOM = 12
_STYLE_COL = {"n": CODE_FG, "hi": CODE_HI, "dim": CODE_DIM,
              "good": CODE_GOOD, "bad": CODE_BAD}


def _txt(ln):
    return ln[0] if isinstance(ln, tuple) else ln


def card_size(lines, label, minw=0):
    maxlen = max([len(_txt(l)) for l in lines] + [len(label) + 2])
    w = max(minw, PAD * 2 + int(round(maxlen * CHARW)))
    h = LABEL_AREA + len(lines) * LH + BOTTOM
    return w, h


def code_card(x, y, lines, label, border, labelcol, minw=0):
    w, h = card_size(lines, label, minw)
    out = [rrect(x, y, w, h, CARD_BG, rx=11, stroke=border, sw=1.75)]
    out.append(f'<text x="{x+PAD}" y="{y+15}" fill="{labelcol}" '
               f'font-family="{FONT}" font-size="10.5" font-weight="700" '
               f'letter-spacing="1.2" text-anchor="start" '
               f'dominant-baseline="central">{esc(label)}</text>')
    cy = y + LABEL_AREA + LH / 2
    for ln in lines:
        txt, style = (ln if isinstance(ln, tuple) else (ln, "n"))
        out.append(
            f'<text x="{x+PAD}" y="{cy}" fill="{_STYLE_COL[style]}" '
            f'font-family="{MONO}" font-size="{CSIZE}" text-anchor="start" '
            f'dominant-baseline="central" '
            f'xml:space="preserve">{esc(txt)}</text>')
        cy += LH
    return "".join(out), w, h


def before_after(fname, title, before, after, op="", note_b="", note_a="",
                 blabel="BEFORE", alabel="AFTER", title2="", gap=104):
    wl, hl = card_size(before, blabel)
    wr, hr = card_size(after, alabel)
    top = 46 if not title2 else 62
    y0 = top
    maxh = max(hl, hr)
    xl = 24
    xr = xl + wl + gap
    W = xr + wr + 24
    note_h = 26 if (note_b or note_a) else 0
    H = top + maxh + note_h + 18
    b = [text(W / 2, 24, title, GREY, 15.5, 700)]
    if title2:
        b.append(text(W / 2, 44, title2, LIGHT, 11.5, 500, italic=True))
    cl, _, _ = code_card(xl, y0, before, blabel, GREY_D, LBL_BEFORE)
    cr, _, _ = code_card(xr, y0, after, alabel, PURPLE, LBL_AFTER)
    b.append(cl)
    b.append(cr)
    ay = y0 + maxh / 2
    b.append(arrow(xl + wl + 16, ay, xr - 12, ay, PURPLE, 2.0))
    if op:
        b.append(text((xl + wl + xr) / 2, ay - 13, op, PURPLE, 11, 700))
    if note_b:
        b.append(text(xl + wl / 2, y0 + maxh + 15, note_b, RED, 11, 600))
    if note_a:
        b.append(text(xr + wr / 2, y0 + maxh + 15, note_a, TEAL, 11, 600))
    write(fname, svg(W, H, "".join(b), title))


def rules_fig(fname, title, pairs, note="", lhs_hdr="", rhs_hdr=""):
    """A card of  lhs  →  rhs  rewrite rules (monospace)."""
    lw = max(len(l) for l, _ in pairs)
    rw = max(len(r) for _, r in pairs)
    x0, y0 = 24, 46
    lx = x0 + PAD
    arrow_x1 = lx + int(lw * CHARW) + 12
    arrow_x2 = arrow_x1 + 30
    rx = arrow_x2 + 12
    cardw = (rx + int(rw * CHARW) + PAD) - x0
    rows = len(pairs)
    hdr_h = 20 if (lhs_hdr or rhs_hdr) else 0
    cardh = LABEL_AREA + hdr_h + rows * LH + BOTTOM
    W = x0 + cardw + 24
    H = y0 + cardh + (24 if note else 12)
    b = [text(W / 2, 24, title, GREY, 15.5, 700)]
    b.append(rrect(x0, y0, cardw, cardh, CARD_BG, rx=11, stroke=GREY_D,
                   sw=1.75))
    cy = y0 + LABEL_AREA + hdr_h + LH / 2
    if hdr_h:
        b.append(text(lx, y0 + 16, lhs_hdr, LBL_BEFORE, 10.5, 700,
                      anchor="start"))
        b.append(text(rx, y0 + 16, rhs_hdr, LBL_AFTER, 10.5, 700,
                      anchor="start"))
    for l, r in pairs:
        b.append(f'<text x="{lx}" y="{cy}" fill="{CODE_FG}" '
                 f'font-family="{MONO}" font-size="{CSIZE}" text-anchor="start"'
                 f' dominant-baseline="central" '
                 f'xml:space="preserve">{esc(l)}</text>')
        b.append(arrow(arrow_x1, cy, arrow_x2, cy, PURPLE, 1.8))
        b.append(f'<text x="{rx}" y="{cy}" fill="{CODE_GOOD}" '
                 f'font-family="{MONO}" font-size="{CSIZE}" text-anchor="start"'
                 f' dominant-baseline="central" '
                 f'xml:space="preserve">{esc(r)}</text>')
        cy += LH
    if note:
        b.append(text(W / 2, y0 + cardh + 13, note, LIGHT, 11, 500,
                      italic=True))
    write(fname, svg(W, H, "".join(b), title))




# ── memory-domain helpers ────────────────────────────────────────────────────
def seg(x, y, w, h, label, color, sub=None, tcol=WHITE, size=12.5, rx=3,
        stroke=None):
    lines = [label] if sub is None else [label, sub]
    return box(x, y, w, h, lines, color, tcol=tcol, size=size, rx=rx, lh=15,
               stroke=stroke)


def addr(x, y, s):
    return text(x, y, s, LIGHT, 10.5, 600, anchor="end", mono=True)


def perm(x, y, s, col=TEAL):
    return text(x, y, s, col, 11, 700, anchor="start", mono=True)


# ── UML helpers ──────────────────────────────────────────────────────────────
UML_SIZE = 11
UML_LH = 17


def uml_class(x, y, w, name, attrs=None, methods=None, fill=GREY,
              stereotype=None):
    """A 3-compartment UML class box. Returns (svg, w, h)."""
    attrs = attrs or []
    methods = methods or []
    head_h = 34 if stereotype else 26
    seg_a = len(attrs) * UML_LH + 10 if attrs else 0
    seg_m = len(methods) * UML_LH + 10 if methods else 0
    h = head_h + (seg_a + seg_m or 6)
    p = [rrect(x, y, w, h, fill, rx=6)]
    if stereotype:
        p.append(text(x + w / 2, y + 13, "\u00ab" + stereotype + "\u00bb",
                      WHITE, 9.5, 600))
        p.append(text(x + w / 2, y + 27, name, WHITE, 12.5, 700))
    else:
        p.append(text(x + w / 2, y + 15, name, WHITE, 12.5, 700))
    yy = y + head_h
    for seg, hh in ((attrs, seg_a), (methods, seg_m)):
        if not seg:
            continue
        p.append(line(x, yy, x + w, yy, WHITE, 1))
        cy = yy + 8 + UML_LH / 2 - 3
        for it in seg:
            p.append(text(x + 10, cy, it, WHITE, UML_SIZE, 500,
                          anchor="start", mono=True))
            cy += UML_LH
        yy += hh
    return "".join(p), w, h


def _tri(cx, cy, d, col=GREY, fill="none", s=11):
    if d == "up":
        pts = f"{cx},{cy} {cx-s*0.72},{cy+s} {cx+s*0.72},{cy+s}"
    elif d == "down":
        pts = f"{cx},{cy} {cx-s*0.72},{cy-s} {cx+s*0.72},{cy-s}"
    elif d == "left":
        pts = f"{cx},{cy} {cx+s},{cy-s*0.72} {cx+s},{cy+s*0.72}"
    else:
        pts = f"{cx},{cy} {cx-s},{cy-s*0.72} {cx-s},{cy+s*0.72}"
    return (f'<polygon points="{pts}" fill="{fill}" stroke="{col}" '
            f'stroke-width="1.6" stroke-linejoin="round"/>')


def vrel(cx, y_from, y_to, kind="inherit", col=None, label=None):
    """Vertical relationship; head sits at y_to (the parent/target)."""
    up = y_to < y_from
    d = "up" if up else "down"
    dash = "5 4" if kind in ("realize", "dependency") else None
    if col is None:
        col = PURPLE if kind in ("inherit", "realize") else GREY
    parts = []
    if kind in ("inherit", "realize"):
        parts.append(_tri(cx, y_to, d, col, "none", 11))
        base = y_to + (11 if up else -11)
        parts.append(line(cx, y_from, cx, base, col, 1.6, dash=dash))
    else:
        parts.append(arrow(cx, y_from, cx, y_to, col, 1.7, dash=dash))
    if label:
        parts.append(text(cx + 8, (y_from + y_to) / 2, label, LIGHT, 9.5, 600,
                          anchor="start"))
    return "".join(parts)


def hrel(cy, x_from, x_to, kind="assoc", col=GREY, label=None):
    """Horizontal association / dependency (open arrow at x_to)."""
    dash = "5 4" if kind == "dependency" else None
    parts = [arrow(x_from, cy, x_to, cy, col, 1.7, dash=dash)]
    if label:
        parts.append(text((x_from + x_to) / 2, cy - 9, label, LIGHT, 9.5, 600))
    return "".join(parts)


def hcompose(cy, xw, xp, filled, col=TEAL, label=None):
    """Aggregation/composition diamond at the whole (left), line to part."""
    fillc = col if filled else "none"
    s = 8
    pts = f"{xw},{cy} {xw+s},{cy-s} {xw+2*s},{cy} {xw+s},{cy+s}"
    parts = [f'<polygon points="{pts}" fill="{fillc}" stroke="{col}" '
             f'stroke-width="1.6" stroke-linejoin="round"/>']
    parts.append(line(xw + 2 * s, cy, xp, cy, col, 1.6))
    if label:
        parts.append(text((xw + xp) / 2, cy - 9, label, LIGHT, 9.5, 600))
    return "".join(parts)


def vcompose(cx, y_whole, y_part, filled, col=TEAL, label=None):
    """Aggregation/composition diamond at the whole, line toward the part."""
    fillc = col if filled else "none"
    s = 8
    up = y_part < y_whole
    if up:
        pts = f"{cx},{y_whole} {cx-s},{y_whole-s} {cx},{y_whole-2*s} {cx+s},{y_whole-s}"
        base = y_whole - 2 * s
    else:
        pts = f"{cx},{y_whole} {cx-s},{y_whole+s} {cx},{y_whole+2*s} {cx+s},{y_whole+s}"
        base = y_whole + 2 * s
    parts = [f'<polygon points="{pts}" fill="{fillc}" stroke="{col}" '
             f'stroke-width="1.6" stroke-linejoin="round"/>']
    parts.append(line(cx, base, cx, y_part, col, 1.6))
    if label:
        parts.append(text(cx + 8, (y_whole + y_part) / 2, label, LIGHT, 9.5,
                          600, anchor="start"))
    return "".join(parts)


def tree_conn(parent_cx, parent_by, children, kind="inherit", col=None):
    """Classic UML generalisation tree: one triangle at the parent, a
    horizontal bus, and a vertical drop to each child (cx, y_top)."""
    if col is None:
        col = PURPLE if kind in ("inherit", "realize") else GREY
    dash = "5 4" if kind == "realize" else None
    bus = parent_by + 38
    parts = [_tri(parent_cx, parent_by, "up", col, "none", 11)]
    parts.append(line(parent_cx, parent_by + 11, parent_cx, bus, col, 1.6,
                      dash=dash))
    xs = [c[0] for c in children] + [parent_cx]
    parts.append(line(min(xs), bus, max(xs), bus, col, 1.6, dash=dash))
    for cx, cy in children:
        parts.append(line(cx, bus, cx, cy, col, 1.6, dash=dash))
    return "".join(parts)


def elbow_up(cx_from, y_from, cx_to, y_to, kind="inherit", col=None):
    """L-shaped connector from a child up to a (possibly offset) parent."""
    if col is None:
        col = PURPLE if kind in ("inherit", "realize") else GREY
    dash = "5 4" if kind in ("realize", "dependency") else None
    mid = y_to + 36
    parts = [line(cx_from, y_from, cx_from, mid, col, 1.6, dash=dash),
             line(cx_from, mid, cx_to, mid, col, 1.6, dash=dash)]
    if kind in ("inherit", "realize"):
        parts.append(_tri(cx_to, y_to, "up", col, "none", 11))
        parts.append(line(cx_to, mid, cx_to, y_to + 11, col, 1.6, dash=dash))
    else:
        parts.append(arrow(cx_to, mid, cx_to, y_to, col, 1.7, dash=dash))
    return "".join(parts)


def fig(fname, W, H, title, body, cap=None):
    b = [text(W / 2, 26, title, GREY, 15.5, 700)] + list(body)
    if cap:
        b.append(text(W / 2, H - 14, cap, LIGHT, 10.5, 500))
    write("figures/" + fname, svg(W, H, "".join(b), title))


# ── OS diagram helpers ───────────────────────────────────────────────────────
def circle(cx, cy, r, fill="none", stroke=GREY, sw=RULE, tcol=None, label=None,
           size=12):
    c = (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" '
         f'stroke-width="{sw}"/>')
    if label is not None:
        c += tspan_lines(cx, cy, label if isinstance(label, list) else [label],
                         tcol or WHITE, size, 600, 14)
    return c


def vstack(x, y, w, rows, rh=46, gap=10, size=12.5, lh=15):
    """Vertical stack of labelled boxes. rows: (lines, fill[, tcol])."""
    out = []
    cy = y
    for row in rows:
        lines, fill = row[0], row[1]
        tcol = row[2] if len(row) > 2 else WHITE
        out.append(box(x, cy, w, rh, lines, fill, tcol=tcol, size=size, lh=lh))
        cy += rh + gap
    return "".join(out), cy - gap


def gantt(x, y, segs, unit=26, h=42, start=0, size=12):
    """Gantt bar. segs: (label, duration[, col]). Returns (svg, end_x)."""
    out = []
    cx = x
    ticks = [start]
    t = start
    for seg in segs:
        label, dur = seg[0], seg[1]
        col = seg[2] if len(seg) > 2 else PURPLE
        w = dur * unit
        if label:
            out.append(box(cx, y, w, h, [label], col, size=size, rx=5))
        else:
            out.append(rrect(cx, y, w, h, "none", rx=5, stroke=LIGHT,
                             dash="3 3"))
        cx += w
        t += dur
        ticks.append(t)
    for i, tk in enumerate(ticks):
        tx = x + sum(s[1] for s in segs[:i]) * unit
        out.append(line(tx, y + h, tx, y + h + 5, LIGHT, 1))
        out.append(text(tx, y + h + 14, str(tk), LIGHT, 10, 600))
    return "".join(out), cx


def cellgrid(x, y, rowlabels, collabels, cells, cw=110, ch=34, lw=120):
    """Matrix with row/col headers. cells[r][c] = (text, col)."""
    out = []
    for j, cl in enumerate(collabels):
        out.append(text(x + lw + j * cw + cw / 2, y - 10, cl, GREY, 11, 700))
    for i, rl in enumerate(rowlabels):
        yy = y + i * ch
        out.append(text(x + lw - 10, yy + ch / 2, rl, GREY, 11, 700,
                        anchor="end"))
        for j in range(len(collabels)):
            txt, col = cells[i][j]
            out.append(box(x + lw + j * cw, yy, cw - 6, ch - 6, [txt], col,
                           size=10.5, rx=5))
    return "".join(out)


# ── Ch01 · Introduction & fundamentals ───────────────────────────────────────
def fig_os_position():
    rows = [(["Users"], GREY),
            (["Application programs", "(compilers, browsers, editors)"], PURPLE),
            (["System programs & libraries"], TEAL),
            (["Operating system  ·  kernel"], PURPLE_D),
            (["Hardware", "(CPU · memory · I/O devices)"], GREY_D)]
    body, endy = vstack(180, 58, 380, rows, rh=52, gap=10, lh=15)
    fig("os-position.svg", 740, endy + 30,
        "Where the operating system sits", [body],
        "each layer uses only the services of the layer beneath it")


def fig_monolithic_vs_microkernel():
    b = []
    b.append(text(210, 58, "Monolithic kernel", GREY, 12.5, 700))
    b.append(text(600, 58, "Microkernel", GREY, 12.5, 700))
    b.append(line(405, 74, 405, 360, LIGHT, 1, dash="4 4"))
    # monolithic: everything in kernel space
    b.append(rrect(60, 150, 320, 190, "none", rx=10, stroke=PURPLE_D, sw=1.6))
    b.append(text(210, 168, "kernel space", LIGHT, 9.5, 600))
    for i, s in enumerate(["Scheduler", "Memory mgr", "VFS / files",
                           "Drivers", "IPC", "Network"]):
        cx = 78 + (i % 2) * 150
        cy = 186 + (i // 2) * 50
        b.append(box(cx, cy, 130, 40, [s], PURPLE, size=11))
    b.append(box(110, 96, 200, 40, ["User programs"], GREY, size=11))
    b.append(arrow(210, 136, 210, 150, GREY, 1.6))
    # microkernel: tiny kernel + user-space servers
    servers = ["FS server", "Driver", "Memory server", "Net server"]
    for i, s in enumerate(servers):
        cx = 450 + (i % 2) * 160
        cy = 96 + (i // 2) * 52
        b.append(box(cx, cy, 145, 42, [s], TEAL, size=11))
    b.append(rrect(450, 210, 305, 130, "none", rx=10, stroke=PURPLE_D, sw=1.6))
    b.append(text(602, 228, "kernel space", LIGHT, 9.5, 600))
    b.append(box(470, 250, 265, 70, ["Microkernel", "IPC · scheduling · basic memory"],
                 PURPLE_D, size=11, lh=15))
    for i in range(4):
        cx = 522 + (i % 2) * 160
        cy = 138
        b.append(arrow(cx, cy, 602, 250, GREY, 1.3, dash="4 3"))
    b.append(text(602, 352, "servers run in user space, talk via IPC", LIGHT,
                  9.5, 600))
    fig("monolithic-vs-microkernel.svg", 800, 380,
        "Monolithic kernel vs microkernel", b)


def fig_system_call():
    b = []
    b.append(line(60, 150, 760, 150, LIGHT, 1.2, dash="5 4"))
    b.append(text(72, 138, "user mode", LIGHT, 10, 700, anchor="start"))
    b.append(text(72, 166, "kernel mode", LIGHT, 10, 700, anchor="start"))
    b.append(box(60, 80, 190, 54, ["User process", "read(fd, buf, n)"], GREY,
                 size=11, lh=15))
    b.append(box(300, 80, 190, 54, ["C library wrapper", "(glibc)"], PURPLE,
                 size=11, lh=15))
    b.append(box(300, 185, 190, 54, ["syscall handler", "(dispatch table)"],
                 PURPLE_D, size=11, lh=15))
    b.append(box(560, 185, 190, 54, ["kernel service", "routine"], TEAL,
                 size=11, lh=15))
    b.append(arrow(250, 107, 300, 107, GREY, 1.7))
    b.append(arrow(395, 134, 395, 185, PURPLE, 1.8))
    b.append(text(500, 170, "trap  (int / syscall)", PURPLE, 10, 700))
    b.append(arrow(490, 212, 560, 212, GREY, 1.7))
    b.append(path("M655 185 C655 142 300 142 250 126", GREY, 1.5, dash="5 4",
                  arrow_end=True))
    b.append(text(430, 138, "return value", LIGHT, 9.5, 600))
    fig("system-call.svg", 800, 300,
        "A system call crosses the user / kernel boundary", b,
        "the mode switch is the only gateway into privileged code")


def fig_user_kernel_mode():
    b = []
    b.append(box(65, 90, 260, 150, [""], GREY, rx=12))
    b.append(text(205, 112, "User mode  (ring 3)", WHITE, 12.5, 700))
    for i, t in enumerate(["restricted instructions", "no direct I/O",
                           "own virtual address space"]):
        b.append(text(110, 146 + i * 26, "\u2022 " + t, WHITE, 10.5, 500,
                      anchor="start"))
    b.append(box(475, 90, 260, 150, [""], PURPLE_D, rx=12))
    b.append(text(580, 112, "Kernel mode  (ring 0)", WHITE, 12.5, 700))
    for i, t in enumerate(["all instructions", "direct hardware access",
                           "manages every process"]):
        b.append(text(495, 146 + i * 26, "\u2022 " + t, WHITE, 10.5, 500,
                      anchor="start"))
    b.append(path("M350 130 C400 110 400 110 450 130", PURPLE, 1.8,
                  arrow_end=True))
    b.append(text(400, 96, "syscall / interrupt / trap", PURPLE, 10, 700))
    b.append(path("M450 200 C400 220 400 220 350 200", GREY, 1.8,
                  arrow_end=True))
    b.append(text(400, 232, "return  (mode bit \u2192 user)", GREY, 10, 700))
    fig("user-kernel-mode.svg", 780, 290,
        "Two privilege levels, one controlled transition", b)


# ── Ch02 · Process management ────────────────────────────────────────────────
def fig_five_state_model():
    b = []
    new = (60, 160); ready = (300, 90); run = (550, 90)
    wait = (300, 250); term = (760, 160)
    for (x, y), lbl, col in [(new, "New", GREY), (ready, "Ready", PURPLE),
                             (run, "Running", TEAL), (wait, "Waiting", AMBER),
                             (term, "Terminated", GREY)]:
        b.append(box(x, y, 150, 56, [lbl], col, size=13))
    # admit
    b.append(arrow(210, 178, 300, 132, GREY, 1.7))
    b.append(text(250, 148, "admit", LIGHT, 9.5, 600))
    # dispatch
    b.append(arrow(450, 118, 550, 118, PURPLE, 1.7))
    b.append(text(500, 106, "dispatch", LIGHT, 9.5, 600))
    # interrupt (top arc Running -> Ready)
    b.append(path("M560 96 C500 52 400 52 380 90", GREY, 1.6, arrow_end=True))
    b.append(text(470, 48, "interrupt / timeout", LIGHT, 9.5, 600))
    # I/O wait (Running -> Waiting)
    b.append(arrow(600, 146, 435, 252, AMBER, 1.7))
    b.append(text(575, 210, "I/O or event wait", LIGHT, 9.5, 600))
    # I/O done (Waiting -> Ready), routed in the gap between New and column
    b.append(path("M300 262 C250 220 250 140 300 128", TEAL, 1.6,
                  arrow_end=True))
    b.append(text(252, 196, "I/O done", LIGHT, 9.5, 600, anchor="end"))
    # exit
    b.append(arrow(700, 118, 760, 172, GREY, 1.7))
    b.append(text(722, 142, "exit", LIGHT, 9.5, 600, anchor="start"))
    fig("five-state-model.svg", 980, 330,
        "The five-state process model", b,
        "the scheduler moves a process between Ready and Running")


def fig_context_switch():
    b = []
    b.append(line(60, 210, 820, 210, LIGHT, 1, dash="4 4"))
    b.append(box(60, 90, 150, 44, ["Process P0", "executing"], TEAL, size=11,
                 lh=14))
    b.append(box(60, 250, 150, 44, ["PCB0"], GREY, size=11))
    b.append(box(360, 150, 200, 60, ["kernel", "save P0 \u2192 load P1"],
                 PURPLE_D, size=11, lh=15))
    b.append(box(670, 90, 150, 44, ["Process P1", "executing"], TEAL, size=11,
                 lh=14))
    b.append(box(670, 250, 150, 44, ["PCB1"], GREY, size=11))
    b.append(arrow(210, 112, 360, 165, GREY, 1.6))
    b.append(text(250, 128, "interrupt", LIGHT, 9.5, 600, anchor="start"))
    b.append(arrow(300, 272, 360, 200, GREY, 1.5, dash="4 3"))
    b.append(text(250, 262, "save state", LIGHT, 9.5, 600, anchor="start"))
    b.append(arrow(560, 200, 640, 272, GREY, 1.5, dash="4 3"))
    b.append(text(590, 262, "load state", LIGHT, 9.5, 600, anchor="start"))
    b.append(arrow(560, 165, 670, 112, GREY, 1.6))
    b.append(text(560, 128, "resume", LIGHT, 9.5, 600, anchor="start"))
    b.append(text(440, 250, "idle: pure overhead", RED, 10, 600))
    fig("context-switch.svg", 880, 320,
        "A context switch saves one process and restores another", b)


def fig_process_vs_thread():
    b = []
    b.append(text(210, 58, "Multiple processes", GREY, 12.5, 700))
    for i, x in enumerate([60, 250]):
        b.append(rrect(x, 78, 160, 240, "none", rx=10, stroke=GREY, sw=1.6))
        b.append(text(x + 80, 96, f"Process {i}", LIGHT, 10, 700))
        for j, (lbl, col) in enumerate([("code", PURPLE), ("data", PURPLE),
                                        ("heap", TEAL), ("stack", AMBER),
                                        ("registers", GREY)]):
            b.append(box(x + 18, 110 + j * 42, 124, 34, [lbl], col, size=10.5,
                         rx=5))
    b.append(text(620, 58, "Multiple threads, one process", GREY, 12.5, 700))
    b.append(rrect(470, 78, 320, 240, "none", rx=10, stroke=GREY, sw=1.6))
    for j, (lbl, col) in enumerate([("code", PURPLE), ("data", PURPLE),
                                    ("heap", TEAL)]):
        b.append(box(490, 98 + j * 42, 280, 34, [lbl + "  (shared)"], col,
                     size=10.5, rx=5))
    for i in range(3):
        x = 490 + i * 95
        b.append(box(x, 232, 84, 34, [f"stack {i}"], AMBER, size=10, rx=5))
        b.append(box(x, 272, 84, 34, [f"regs {i}"], GREY, size=10, rx=5))
    b.append(text(630, 300, "per-thread", LIGHT, 9.5, 600))
    fig("process-vs-thread.svg", 820, 340,
        "Processes isolate; threads share", b)


def fig_scheduling_queues():
    b = []
    b.append(box(60, 120, 140, 46, ["Ready queue"], PURPLE, size=11))
    b.append(box(300, 120, 120, 46, ["CPU"], TEAL, size=13))
    b.append(arrow(200, 143, 300, 143, GREY, 1.7))
    b.append(text(250, 131, "dispatch", LIGHT, 9.5, 600))
    b.append(arrow(420, 143, 520, 143, GREY, 1.7))
    b.append(text(560, 143, "exit", GREY, 10, 700, anchor="start"))
    events = [("I/O request", "I/O wait queue", TEAL, 240),
              ("wait for interrupt", "event queue", GREY, 340)]
    for lbl, q, col, yy in events:
        b.append(path(f"M360 166 C360 {yy} 360 {yy} 310 {yy}", col, 1.5,
                      arrow_end=True))
        b.append(box(150, yy - 20, 160, 40, [q], col, size=10.5, rx=6))
        b.append(path(f"M150 {yy} C60 {yy} 60 166 128 148", GREY, 1.4,
                      dash="4 3", arrow_end=True))
        b.append(text(470, yy, lbl, LIGHT, 9.5, 600, anchor="middle"))
    # time-slice expired: straight back to the ready queue
    b.append(path("M360 120 C360 86 200 86 132 118", AMBER, 1.5, dash="4 3",
                  arrow_end=True))
    b.append(text(250, 78, "time-slice expired", AMBER, 9.5, 600))
    fig("scheduling-queues.svg", 640, 420,
        "Queueing model of process scheduling", b,
        "a process cycles through Ready \u2192 CPU \u2192 wait until it exits")


def fig_ipc_models():
    b = []
    b.append(text(210, 58, "Shared memory", GREY, 12.5, 700))
    b.append(box(60, 84, 130, 50, ["Process A"], GREY, size=11))
    b.append(box(280, 84, 130, 50, ["Process B"], GREY, size=11))
    b.append(box(150, 210, 170, 50, ["shared region"], TEAL, size=11))
    b.append(arrow(125, 134, 200, 210, GREY, 1.6))
    b.append(arrow(345, 134, 270, 210, GREY, 1.6))
    b.append(text(235, 285, "kernel maps it once; then direct reads/writes",
                  LIGHT, 9, 500))
    b.append(line(450, 74, 450, 300, LIGHT, 1, dash="4 4"))
    b.append(text(620, 58, "Message passing", GREY, 12.5, 700))
    b.append(box(500, 84, 130, 50, ["Process A"], GREY, size=11))
    b.append(box(720, 84, 130, 50, ["Process B"], GREY, size=11))
    b.append(box(560, 200, 230, 50, ["kernel", "send() / receive()"],
                 PURPLE_D, size=11, lh=14))
    b.append(arrow(565, 134, 620, 200, GREY, 1.6))
    b.append(arrow(785, 134, 730, 200, GREY, 1.6))
    b.append(text(675, 285, "every message is copied through the kernel",
                  LIGHT, 9, 500))
    fig("ipc-models.svg", 900, 320,
        "Two IPC models: share memory or pass messages", b)


# ── Ch03 · Memory management ─────────────────────────────────────────────────
def fig_memory_hierarchy():
    b = []
    layers = [("Registers", "< 1 ns", "~1 KB", PURPLE_D, 200),
              ("L1 / L2 / L3 cache", "1-30 ns", "KB-MB", PURPLE, 300),
              ("Main memory (RAM)", "~100 ns", "GB", TEAL, 420),
              ("SSD", "~100 \u00b5s", "TB", AMBER, 540),
              ("Hard disk (HDD)", "~10 ms", "TB+", GREY, 660)]
    y = 60
    for name, spd, sz, col, w in layers:
        x = (760 - w) / 2
        b.append(box(x, y, w, 46, [name], col, size=12))
        b.append(text(x - 12, y + 23, spd, LIGHT, 10, 600, anchor="end"))
        b.append(text(x + w + 12, y + 23, sz, LIGHT, 10, 600, anchor="start"))
        y += 58
    b.append(text(150, 44, "faster, costlier", LIGHT, 10, 700))
    b.append(text(620, y + 6, "bigger, cheaper", LIGHT, 10, 700))
    fig("memory-hierarchy.svg", 760, y + 30,
        "The memory hierarchy", b)


def fig_paging_translation():
    b = []
    b.append(box(60, 90, 220, 50, ["page # (p)", "offset (d)"], GREY, size=11,
                 lh=15))
    b.append(text(170, 74, "logical address", LIGHT, 10, 600))
    b.append(line(170, 90, 170, 140, WHITE, 1.2))
    b.append(box(360, 70, 180, 150, ["page table"], PURPLE, size=12))
    for i in range(3):
        b.append(line(360, 108 + i * 32, 540, 108 + i * 32, WHITE, 0.8))
    b.append(arrow(280, 100, 360, 100, GREY, 1.6))
    b.append(text(320, 88, "index p", LIGHT, 9, 600))
    b.append(box(620, 90, 220, 50, ["frame # (f)", "offset (d)"], TEAL,
                 size=11, lh=15))
    b.append(text(730, 74, "physical address", LIGHT, 10, 600))
    b.append(arrow(540, 130, 620, 115, PURPLE, 1.6))
    b.append(text(585, 100, "frame f", LIGHT, 9, 600))
    b.append(path("M170 140 C170 260 730 260 730 140", GREY, 1.4, dash="5 4",
                  arrow_end=True))
    b.append(text(450, 258, "offset copied unchanged", LIGHT, 9.5, 600))
    fig("paging-translation.svg", 940, 300,
        "Address translation under paging", b,
        "the page number indexes the table; the offset passes straight through")


def fig_tlb():
    b = []
    b.append(box(60, 130, 120, 50, ["CPU", "page p"], GREY, size=11, lh=14))
    b.append(box(260, 90, 200, 60, ["TLB", "(cache of translations)"], PURPLE,
                 size=11, lh=15))
    b.append(box(300, 250, 200, 55, ["page table", "(in memory)"], TEAL,
                 size=11, lh=15))
    b.append(box(620, 130, 180, 50, ["physical", "frame f"], TEAL, size=11,
                 lh=14))
    b.append(arrow(180, 150, 260, 130, GREY, 1.6))
    b.append(arrow(460, 115, 620, 145, TEAL, 1.8))
    b.append(text(545, 100, "hit  (fast)", TEAL, 10, 700))
    b.append(arrow(360, 150, 390, 250, AMBER, 1.7))
    b.append(text(300, 210, "miss", AMBER, 10, 700, anchor="start"))
    b.append(arrow(500, 275, 690, 180, GREY, 1.6))
    b.append(text(600, 250, "walk table, then load frame", LIGHT, 9.5, 600))
    b.append(path("M400 250 C380 200 340 175 360 152", GREY, 1.3, dash="4 3",
                  arrow_end=True))
    b.append(text(300, 195, "update TLB", LIGHT, 9, 600, anchor="start"))
    fig("tlb.svg", 840, 340,
        "The TLB caches recent page-table lookups", b)


def fig_two_level_page_table():
    b = []
    b.append(box(60, 80, 300, 44, ["p1", "p2", "offset"], GREY, size=11))
    b.append(line(160, 80, 160, 124, WHITE, 1))
    b.append(line(260, 80, 260, 124, WHITE, 1))
    b.append(text(110, 66, "p1", LIGHT, 9.5, 600))
    b.append(text(210, 66, "p2", LIGHT, 9.5, 600))
    b.append(text(310, 66, "offset", LIGHT, 9.5, 600))
    b.append(box(140, 180, 150, 120, ["outer", "page table"], PURPLE, size=11,
                 lh=15))
    b.append(box(400, 180, 150, 120, ["inner", "page table"], TEAL, size=11,
                 lh=15))
    b.append(box(650, 200, 150, 60, ["frame", "in memory"], GREY, size=11,
                 lh=15))
    b.append(arrow(110, 124, 200, 180, GREY, 1.6))
    b.append(text(120, 158, "p1", LIGHT, 9, 600))
    b.append(arrow(290, 235, 400, 235, PURPLE, 1.6))
    b.append(text(345, 223, "p2", LIGHT, 9, 600))
    b.append(arrow(550, 235, 650, 232, TEAL, 1.6))
    fig("two-level-page-table.svg", 840, 330,
        "A two-level (hierarchical) page table", b,
        "paging the page table keeps large address spaces sparse and cheap")


def fig_page_fault():
    b = []
    steps = [("reference page", GREY),
             ("valid bit = 0 \u2192 trap to OS", AMBER),
             ("locate page on disk", PURPLE),
             ("load into a free frame", TEAL),
             ("update page table", PURPLE),
             ("restart instruction", TEAL)]
    for i, (lbl, col) in enumerate(steps):
        x = 60 + (i % 3) * 270
        y = 90 + (i // 3) * 110
        b.append(box(x, y, 210, 56, [lbl], col, size=11))
        if i % 3 != 2 and i != len(steps) - 1:
            b.append(arrow(x + 210, y + 28, x + 270, y + 28, GREY, 1.6))
    b.append(path("M705 146 C705 180 165 180 165 190", GREY, 1.5,
                  arrow_end=True))
    fig("page-fault.svg", 880, 290,
        "Servicing a page fault", b,
        "a missing page is fetched from disk, then the instruction re-runs")


def fig_clock_replacement():
    b = []
    import math
    cx, cy, r = 300, 200, 110
    b.append(circle(cx, cy, r, "none", GREY, 1.4))
    frames = [("A", 1), ("B", 0), ("C", 1), ("D", 1), ("E", 0), ("F", 0),
              ("G", 1), ("H", 0)]
    n = len(frames)
    for i, (lbl, ref) in enumerate(frames):
        ang = -90 + i * 360 / n
        rad = math.radians(ang)
        px = cx + r * math.cos(rad)
        py = cy + r * math.sin(rad)
        col = TEAL if ref else GREY
        b.append(circle(px, py, 24, col, col, 1.2, WHITE,
                        [lbl, f"ref={ref}"], size=9.5))
    # clock hand pointing to first frame (top)
    b.append(arrow(cx, cy, cx, cy - (r - 26), RED, 2.0))
    b.append(text(cx, cy + 8, "hand", RED, 10, 700))
    b.append(text(560, 130, "ref = 1 \u2192 clear it,", LIGHT, 10.5, 600,
                  anchor="start"))
    b.append(text(560, 150, "advance the hand", LIGHT, 10.5, 600,
                  anchor="start"))
    b.append(text(560, 180, "ref = 0 \u2192 evict", RED, 10.5, 700,
                  anchor="start"))
    b.append(text(560, 200, "this frame", RED, 10.5, 700, anchor="start"))
    fig("clock-replacement.svg", 760, 340,
        "Second-chance (clock) page replacement", b)


def fig_fragmentation():
    b = []
    b.append(text(210, 58, "External fragmentation", GREY, 12, 700))
    blocks = [("P1", TEAL, 46), ("free", None, 30), ("P2", TEAL, 34),
              ("free", None, 22), ("P3", TEAL, 40), ("free", None, 28)]
    y = 80
    for lbl, col, h in blocks:
        if col:
            b.append(box(120, y, 180, h, [lbl], col, size=10.5, rx=4))
        else:
            b.append(rrect(120, y, 180, h, "none", rx=4, stroke=RED,
                          dash="4 3"))
            b.append(text(210, y + h / 2, lbl, RED, 10, 600))
        y += h + 4
    b.append(text(210, y + 12, "free memory scattered in small holes",
                  LIGHT, 9.5, 500))
    b.append(arrow(320, 190, 430, 190, PURPLE, 2))
    b.append(text(375, 176, "compaction", PURPLE, 10, 700))
    b.append(box(470, 80, 180, 120, ["P1", "P2", "P3"], TEAL, size=11, lh=34))
    b.append(rrect(470, 204, 180, 84, "none", rx=4, stroke=TEAL, dash="4 3"))
    b.append(text(560, 246, "one large hole", TEAL, 10.5, 700))
    fig("fragmentation.svg", 720, 320,
        "External fragmentation and compaction", b)


# ── Ch04 · CPU scheduling ────────────────────────────────────────────────────
def fig_cpu_io_burst():
    b = []
    segs = [("CPU", 3, PURPLE), ("I/O", 2, AMBER), ("CPU", 2, PURPLE),
            ("I/O", 3, AMBER), ("CPU", 2, PURPLE), ("I/O", 2, AMBER),
            ("CPU", 1, PURPLE)]
    g, endx = gantt(70, 110, segs, unit=42, h=50)
    b.append(g)
    b.append(text(70, 90, "burst", LIGHT, 10, 700, anchor="start"))
    b.append(box(70, 210, 150, 34, ["CPU burst"], PURPLE, size=10.5, rx=5))
    b.append(box(240, 210, 150, 34, ["I/O burst"], AMBER, size=10.5, rx=5))
    b.append(text(endx + 20, 135, "\u2026", LIGHT, 16, 700, anchor="start"))
    fig("cpu-io-burst.svg", endx + 60, 280,
        "Processes alternate CPU and I/O bursts", b,
        "CPU-bound jobs have long CPU bursts; I/O-bound jobs have short ones")


def fig_round_robin():
    b = []
    segs = [("P1", 2, PURPLE), ("P2", 2, TEAL), ("P3", 2, AMBER),
            ("P1", 2, PURPLE), ("P2", 1, TEAL), ("P3", 2, AMBER),
            ("P1", 1, PURPLE)]
    g, endx = gantt(70, 110, segs, unit=44, h=50)
    b.append(g)
    b.append(text(70, 92, "quantum = 2", LIGHT, 10.5, 700, anchor="start"))
    b.append(text(endx / 2 + 35, 210, "each process runs one time quantum, "
                  "then goes to the back of the queue", LIGHT, 10, 500))
    fig("round-robin.svg", endx + 60, 250,
        "Round-robin scheduling with a fixed time quantum", b)


def fig_mlfq():
    b = []
    queues = [("Q0  ·  RR, quantum 8", PURPLE, 90),
              ("Q1  ·  RR, quantum 16", TEAL, 160),
              ("Q2  ·  FCFS", AMBER, 230)]
    for lbl, col, y in queues:
        b.append(box(120, y, 360, 46, [lbl], col, size=11.5))
    b.append(box(560, 90, 150, 46, ["CPU"], GREY, size=12))
    for _, _, y in queues:
        b.append(arrow(480, y + 23, 560, 105 if y == 90 else 118, GREY, 1.5,
                       dash=None if y == 90 else "4 3"))
    b.append(path("M300 136 C300 160 300 160 300 160", AMBER, 1))
    b.append(arrow(300, 136, 300, 160, RED, 1.7))
    b.append(text(315, 150, "uses full quantum \u2192 demote", RED, 9.5, 600,
                  anchor="start"))
    b.append(arrow(300, 206, 300, 230, RED, 1.7))
    b.append(text(60, 90 + 23, "high", LIGHT, 10, 700, anchor="end"))
    b.append(text(60, 230 + 23, "low", LIGHT, 10, 700, anchor="end"))
    b.append(text(600, 200, "priority", LIGHT, 10, 700))
    fig("mlfq.svg", 760, 310,
        "Multi-level feedback queue", b,
        "new jobs enter high; CPU-hungry jobs sink to lower priority queues")


def fig_priority_inversion():
    b = []
    b.append(box(60, 90, 120, 40, ["High  H"], RED, size=11))
    b.append(box(60, 150, 120, 40, ["Med  M"], AMBER, size=11))
    b.append(box(60, 210, 120, 40, ["Low  L"], TEAL, size=11))
    # timeline bars
    b.append(box(200, 210, 90, 40, ["holds lock"], TEAL, size=9.5, rx=5))
    b.append(rrect(290, 90, 250, 40, "none", rx=5, stroke=RED, dash="4 3"))
    b.append(text(415, 110, "H blocked, waiting for lock", RED, 9.5, 600))
    b.append(box(290, 150, 250, 40, ["M runs (preempts L)"], AMBER, size=9.5,
                 rx=5))
    b.append(box(540, 210, 120, 40, ["L resumes"], TEAL, size=9.5, rx=5))
    b.append(box(660, 90, 120, 40, ["H runs"], RED, size=9.5, rx=5))
    b.append(line(200, 270, 780, 270, LIGHT, 1))
    b.append(text(490, 286, "time \u2192", LIGHT, 10, 600))
    b.append(text(415, 60, "M delays H indefinitely \u2014 priority inversion",
                  GREY, 11, 700))
    fig("priority-inversion.svg", 860, 320,
        "Priority inversion", b,
        "fix with priority inheritance: L temporarily inherits H's priority")


# ── Ch05 · File systems ──────────────────────────────────────────────────────
def _diskrow(b, x, y, blocks, cols):
    for i, (idx, col) in enumerate(zip(blocks, cols)):
        b.append(box(x + i * 46, y, 42, 34, [str(idx)], col, size=10, rx=4))


def fig_file_allocation():
    b = []
    # contiguous
    b.append(text(150, 60, "Contiguous", GREY, 12, 700))
    for i in range(5):
        col = TEAL if 1 <= i <= 3 else GREY_D
        b.append(box(60 + i * 46, 78, 42, 34, [str(i)], col, size=10, rx=4))
    b.append(text(150, 128, "start=1, length=3", LIGHT, 9, 500))
    # linked
    b.append(text(480, 60, "Linked", GREY, 12, 700))
    order = [(0, "1"), (2, "4"), (4, "\u2205")]
    xs = [360, 480, 600]
    for (blk, nxt), x in zip(order, xs):
        b.append(box(x, 78, 70, 40, [f"blk {blk}", f"next {nxt}"], PURPLE,
                     size=9.5, lh=13))
    b.append(arrow(430, 98, 480, 98, GREY, 1.5))
    b.append(arrow(550, 98, 600, 98, GREY, 1.5))
    # indexed
    b.append(text(300, 170, "Indexed", GREY, 12, 700))
    b.append(box(60, 190, 90, 130, ["index", "block"], PURPLE_D, size=10,
                 lh=14))
    for i in range(4):
        b.append(line(60, 226 + i * 22, 150, 226 + i * 22, WHITE, 0.7))
    tgt = [(260, 200), (400, 250), (300, 300), (500, 210)]
    for i, (tx, ty) in enumerate(tgt):
        b.append(box(tx, ty, 60, 34, [f"blk {i}"], TEAL, size=9.5, rx=4))
        b.append(arrow(150, 210 + i * 22, tx, ty + 17, GREY, 1.2))
    fig("file-allocation.svg", 700, 350,
        "Three file allocation methods", b)


def fig_inode():
    b = []
    ino, _, ih = 60, 0, 0
    b.append(box(60, 80, 220, 150, [""], PURPLE, rx=8))
    b.append(text(170, 98, "inode", WHITE, 12, 700))
    for i, t in enumerate(["mode, owner, size", "timestamps",
                           "link count"]):
        b.append(text(78, 122 + i * 20, "\u2022 " + t, WHITE, 10, 500,
                      anchor="start"))
    b.append(text(78, 190, "direct blocks \u00d7 12", WHITE, 10, 600,
                  anchor="start"))
    b.append(text(78, 210, "indirect pointers", WHITE, 10, 600, anchor="start"))
    # data blocks
    for i in range(3):
        b.append(box(360, 80 + i * 44, 90, 34, [f"data {i}"], TEAL, size=10,
                     rx=4))
        b.append(arrow(280, 190, 360, 97 + i * 44, GREY, 1.3))
    # indirect
    b.append(box(360, 220, 100, 40, ["single", "indirect"], AMBER, size=10,
                 lh=13))
    b.append(arrow(280, 210, 360, 240, GREY, 1.4))
    b.append(box(520, 200, 90, 34, ["data \u2026"], TEAL, size=10, rx=4))
    b.append(box(520, 244, 90, 34, ["data \u2026"], TEAL, size=10, rx=4))
    b.append(arrow(460, 240, 520, 217, GREY, 1.3))
    b.append(arrow(460, 245, 520, 261, GREY, 1.3))
    b.append(text(520, 300, "indirect block \u2192 many more blocks", LIGHT,
                  9.5, 500))
    fig("inode.svg", 720, 340,
        "An inode: metadata plus direct and indirect block pointers", b)


def fig_directory_tree():
    b = []
    b.append(box(330, 70, 100, 40, ["/"], PURPLE_D, size=12))
    lvl1 = [("bin", 120), ("home", 330), ("etc", 540)]
    for nm, x in lvl1:
        b.append(box(x, 170, 100, 40, [nm], PURPLE, size=11))
        b.append(line(380, 110, x + 50, 170, GREY, 1.3))
    leaves = [("ls", 60), ("sh", 180), ("alice", 300), ("bob", 420),
              ("passwd", 540)]
    parents = {60: 170, 180: 170, 300: 380, 420: 380, 540: 590}
    for nm, x in leaves:
        col = TEAL
        b.append(box(x, 270, 96, 38, [nm], col, size=10.5))
        b.append(line(parents[x] + 0, 210, x + 48, 270, GREY, 1.2))
    b.append(text(700, 190, "directory", PURPLE, 10, 700, anchor="start"))
    b.append(text(700, 288, "file", TEAL, 10, 700, anchor="start"))
    fig("directory-tree.svg", 780, 340,
        "Tree-structured directory", b,
        "each process has a current directory; paths may be absolute or relative")


def fig_journaling():
    b = []
    steps = [("1. write intent", "to the journal (log)", PURPLE),
             ("2. commit record", "journal is durable", AMBER),
             ("3. checkpoint", "apply to main FS", TEAL)]
    for i, (a, c, col) in enumerate(steps):
        x = 60 + i * 250
        b.append(box(x, 100, 210, 62, [a, c], col, size=11, lh=15))
        if i < 2:
            b.append(arrow(x + 210, 131, x + 250, 131, GREY, 1.7))
    b.append(box(60, 220, 460, 40, ["journal (circular log)"], PURPLE_D,
                 size=11))
    b.append(box(560, 220, 200, 40, ["main file system"], GREY, size=11))
    b.append(arrow(520, 240, 560, 240, GREY, 1.6))
    b.append(text(400, 300, "after a crash: replay committed transactions, "
                  "discard the rest", RED, 10, 600))
    fig("journaling.svg", 820, 330,
        "Write-ahead journaling keeps the file system consistent", b)


# ── Ch06 · Synchronization & deadlocks ───────────────────────────────────────
def fig_producer_consumer():
    b = []
    b.append(box(60, 130, 150, 56, ["Producer", "produces item"], TEAL,
                 size=11, lh=14))
    b.append(box(660, 130, 150, 56, ["Consumer", "consumes item"], PURPLE,
                 size=11, lh=14))
    b.append(rrect(280, 120, 300, 76, "none", rx=10, stroke=GREY, sw=1.6))
    b.append(text(430, 138, "bounded buffer (N slots)", LIGHT, 10, 600))
    for i in range(5):
        col = AMBER if i < 3 else GREY_D
        b.append(box(300 + i * 54, 154, 48, 32, [""], col, rx=4))
    b.append(arrow(210, 158, 280, 158, TEAL, 1.7))
    b.append(arrow(580, 158, 660, 158, PURPLE, 1.7))
    b.append(text(430, 232, "empty \u2193 (wait if full)   ·   full \u2191 "
                  "(wait if empty)   ·   mutex for the buffer", LIGHT, 9.5, 500))
    fig("producer-consumer.svg", 880, 280,
        "Producer-consumer with a bounded buffer", b,
        "semaphores empty and full count slots; mutex guards the shared buffer")


def fig_resource_allocation_graph():
    b = []
    # processes as circles, resources as squares
    P = {"P1": (120, 120), "P2": (380, 120), "P3": (250, 300)}
    R = {"R1": (250, 90), "R2": (250, 210), "R3": (120, 300)}
    for nm, (x, y) in P.items():
        b.append(circle(x, y, 34, GREY, GREY, 1.5, WHITE, nm, size=12))
    for nm, (x, y) in R.items():
        b.append(box(x - 30, y - 26, 60, 52, [nm, "\u25cf"], PURPLE, size=11,
                     lh=15))
    # deadlock cycle P1 -> R1 -> P2 -> R2 -> P1
    b.append(arrow(280, 98, 350, 114, TEAL, 1.6))              # R1 held by P2
    b.append(arrow(152, 108, 226, 92, AMBER, 1.6, dash="5 4"))  # P1 requests R1
    b.append(arrow(230, 198, 150, 136, TEAL, 1.6))             # R2 held by P1
    b.append(arrow(360, 142, 276, 198, AMBER, 1.6, dash="5 4"))  # P2 requests R2
    b.append(arrow(152, 300, 216, 300, TEAL, 1.6))             # R3 held by P3
    b.append(text(560, 120, "solid: resource held by process", TEAL,
                  10, 600, anchor="start"))
    b.append(text(560, 148, "dashed: process requests resource", AMBER,
                  10, 600, anchor="start"))
    b.append(text(560, 184, "P1 \u2192 R1 \u2192 P2 \u2192 R2 \u2192 P1",
                  GREY, 10.5, 700, anchor="start"))
    b.append(text(560, 208, "a cycle \u21d2 possible deadlock", RED, 10.5, 700,
                  anchor="start"))
    fig("resource-allocation-graph.svg", 900, 360,
        "Resource-allocation graph", b)


def fig_deadlock_conditions():
    b = []
    conds = [("Mutual", "exclusion", "a resource is held", "by one process", PURPLE),
             ("Hold and", "wait", "hold one, wait", "for another", TEAL),
             ("No", "preemption", "can't force a", "resource away", AMBER),
             ("Circular", "wait", "a cycle of", "waiting processes", RED)]
    for i, (a, a2, c, c2, col) in enumerate(conds):
        x = 50 + i * 195
        b.append(box(x, 90, 175, 70, [a + " " + a2], col, size=12))
        b.append(text(x + 87, 178, c, LIGHT, 9.5, 500))
        b.append(text(x + 87, 194, c2, LIGHT, 9.5, 500))
        if i < 3:
            b.append(text(x + 185, 125, "+", GREY, 16, 700))
    b.append(text(430, 240, "all four must hold at once \u2014 break any one "
                  "to prevent deadlock", GREY, 11, 700))
    fig("deadlock-conditions.svg", 860, 280,
        "The four necessary conditions for deadlock", b)


def fig_bankers_safe_state():
    b = []
    b.append(rrect(90, 90, 620, 220, "none", rx=14, stroke=GREY, dash="5 4"))
    b.append(text(160, 112, "all states", GREY, 11, 700))
    # safe region (left) and deadlock region (right) are disjoint
    b.append(rrect(120, 150, 250, 130, TEAL, rx=12, opacity=0.15))
    b.append(rrect(120, 150, 250, 130, "none", rx=12, stroke=TEAL, sw=1.6))
    b.append(text(200, 172, "safe", TEAL, 11, 700))
    b.append(text(245, 220, "a safe sequence exists", TEAL, 9.5, 600))
    b.append(rrect(420, 150, 250, 130, RED, rx=12, opacity=0.15))
    b.append(rrect(420, 150, 250, 130, "none", rx=12, stroke=RED, sw=1.6))
    b.append(text(500, 172, "deadlock", RED, 11, 700))
    b.append(text(545, 220, "no safe sequence", RED, 9.5, 600))
    b.append(text(395, 130, "unsafe (between)", GREY, 9.5, 600))
    b.append(text(730, 150, "Banker's algorithm", LIGHT, 10, 700,
                  anchor="start"))
    b.append(text(730, 174, "grants a request only", LIGHT, 10, 500,
                  anchor="start"))
    b.append(text(730, 194, "if the system stays", LIGHT, 10, 500,
                  anchor="start"))
    b.append(text(730, 214, "in a safe state", LIGHT, 10, 500,
                  anchor="start"))
    fig("bankers-safe-state.svg", 980, 340,
        "Safe, unsafe, and deadlocked states", b)


# ── Ch07 · I/O & storage ─────────────────────────────────────────────────────
def fig_dma():
    b = []
    b.append(box(60, 90, 140, 54, ["CPU"], GREY, size=13))
    b.append(box(60, 240, 160, 54, ["DMA controller"], PURPLE, size=11))
    b.append(box(340, 240, 150, 54, ["device", "(disk / NIC)"], TEAL, size=11,
                 lh=14))
    b.append(box(340, 90, 150, 54, ["main memory"], TEAL, size=12))
    b.append(arrow(130, 144, 130, 240, GREY, 1.6))
    b.append(text(150, 195, "1. program", LIGHT, 9.5, 600, anchor="start"))
    b.append(text(150, 209, "   the transfer", LIGHT, 9.5, 600, anchor="start"))
    b.append(arrow(220, 267, 340, 267, PURPLE, 1.8))
    b.append(text(280, 255, "2. bus", LIGHT, 9.5, 600))
    b.append(path("M220 250 C280 180 300 150 340 130", PURPLE, 1.8,
                  arrow_end=True))
    b.append(text(310, 200, "3. device \u2194 memory", LIGHT, 9.5, 600,
                  anchor="start"))
    b.append(path("M130 240 C90 200 90 180 128 145", RED, 1.6, dash="5 4",
                  arrow_end=True))
    b.append(text(150, 165, "4. interrupt", RED, 9.5, 700, anchor="start"))
    b.append(text(150, 179, "   when done", RED, 9.5, 700, anchor="start"))
    fig("dma.svg", 640, 340,
        "Direct Memory Access frees the CPU during bulk transfers", b,
        "the CPU sets up the transfer; the DMA controller moves the data")


def fig_io_software_layers():
    rows = [(["User-level I/O software", "(library calls, spooling)"], GREY),
            (["Device-independent OS software", "(naming, buffering, allocation)"], PURPLE),
            (["Device drivers"], TEAL),
            (["Interrupt handlers"], AMBER),
            (["Hardware", "(controllers & devices)"], GREY_D)]
    body, endy = vstack(200, 58, 380, rows, rh=52, gap=8, lh=14)
    fig("io-software-layers.svg", 780, endy + 30,
        "The layered I/O software stack", [body],
        "each layer hides device detail from the layer above")


def fig_hdd_anatomy():
    b = []
    cx, cy = 250, 200
    for r, col in [(120, GREY_D), (92, GREY), (64, GREY_D), (36, GREY)]:
        b.append(circle(cx, cy, r, "none", col, 1.2))
    b.append(circle(cx, cy, 128, "none", PURPLE, 1.8))
    b.append(circle(cx, cy, 8, GREY, GREY, 1))
    # sector wedge
    b.append(path(f"M{cx} {cy} L{cx+128} {cy} A128 128 0 0 0 {cx+120} {cy-44} Z",
                  PURPLE, 1.2, fill=PURPLE))
    # arm + head
    b.append(line(470, 90, cx + 70, cy - 30, GREY, 4))
    b.append(box(440, 70, 70, 34, ["head"], TEAL, size=10, rx=5))
    b.append(text(cx, cy + 150, "platter", LIGHT, 10, 600))
    b.append(text(cx + 150, cy - 70, "sector", PURPLE, 10, 700, anchor="start"))
    b.append(text(cx + 60, cy + 90, "track", LIGHT, 10, 600, anchor="start"))
    b.append(text(560, 200, "seek time: move arm to track", LIGHT, 9.5, 600,
                  anchor="start"))
    b.append(text(560, 224, "rotational latency: spin to sector", LIGHT, 9.5,
                  600, anchor="start"))
    b.append(text(560, 248, "transfer time: read the bits", LIGHT, 9.5, 600,
                  anchor="start"))
    fig("hdd-anatomy.svg", 860, 380, "Anatomy of a hard disk drive", b)


def fig_disk_scheduling_scan():
    b = []
    x0, x1 = 90, 720
    axis_y = 316
    b.append(line(x0, axis_y, x1, axis_y, LIGHT, 1.2))
    for c in range(0, 201, 40):
        tx = x0 + c / 200 * (x1 - x0)
        b.append(line(tx, axis_y, tx, axis_y + 5, LIGHT, 1))
        b.append(text(tx, axis_y + 18, str(c), LIGHT, 9.5, 600))
    b.append(text(405, axis_y + 40, "cylinder number", LIGHT, 10, 700))
    order = [53, 98, 122, 183, 199, 37, 14]
    pts = [(x0 + c / 200 * (x1 - x0), 90 + i * 28) for i, c in enumerate(order)]
    for i in range(len(pts) - 1):
        b.append(arrow(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                       PURPLE, 1.6))
    for i, c in enumerate(order):
        tx, ty = pts[i]
        col = GREY if c == 199 else TEAL
        b.append(circle(tx, ty, 5, col, col, 1))
        b.append(text(tx, ty - 12, str(c), LIGHT, 9, 600))
    b.append(text(150, 90, "start 53", GREY, 10, 700, anchor="start"))
    b.append(text(x1 - 4, 200, "reverse at", LIGHT, 9, 600, anchor="end"))
    b.append(text(x1 - 4, 214, "end of disk", LIGHT, 9, 600, anchor="end"))
    fig("disk-scheduling-scan.svg", 800, 390,
        "SCAN (elevator) disk scheduling", b,
        "the head sweeps to one end servicing requests, then reverses")


def fig_raid_levels():
    b = []
    def disk(x, y, blocks, title):
        b.append(text(x + 45, y - 10, title, GREY, 10.5, 700))
        for i, (lbl, col) in enumerate(blocks):
            b.append(box(x, y + i * 34, 90, 30, [lbl], col, size=10, rx=4))
    b.append(text(140, 58, "RAID 0 · striping", GREY, 12, 700))
    disk(60, 100, [("A1", PURPLE), ("A3", PURPLE), ("A5", PURPLE)], "disk 0")
    disk(170, 100, [("A2", TEAL), ("A4", TEAL), ("A6", TEAL)], "disk 1")
    b.append(text(140, 220, "speed, no redundancy", LIGHT, 9, 500))
    b.append(text(430, 58, "RAID 1 · mirroring", GREY, 12, 700))
    disk(350, 100, [("A1", PURPLE), ("A2", PURPLE), ("A3", PURPLE)], "disk 0")
    disk(460, 100, [("A1", PURPLE), ("A2", PURPLE), ("A3", PURPLE)], "copy")
    b.append(text(430, 220, "full redundancy, half capacity", LIGHT, 9, 500))
    b.append(text(720, 58, "RAID 5 · distributed parity", GREY, 12, 700))
    disk(630, 100, [("A1", TEAL), ("B1", TEAL), ("Pc", AMBER)], "disk 0")
    disk(740, 100, [("A2", TEAL), ("Pb", AMBER), ("C2", TEAL)], "disk 1")
    disk(850, 100, [("Pa", AMBER), ("B2", TEAL), ("C1", TEAL)], "disk 2")
    b.append(text(760, 220, "parity spread across disks", LIGHT, 9, 500))
    fig("raid-levels.svg", 1000, 250, "Common RAID levels", b)


# ── Ch08 · Security & protection ─────────────────────────────────────────────
def fig_cia_triad():
    b = []
    cx, cy, r = 380, 220, 120
    import math
    pts = []
    for ang in (-90, 30, 150):
        rad = math.radians(ang)
        pts.append((cx + r * math.cos(rad), cy + r * math.sin(rad)))
    b.append(path(f"M{pts[0][0]} {pts[0][1]} L{pts[1][0]} {pts[1][1]} "
                  f"L{pts[2][0]} {pts[2][1]} Z", GREY, 1.8))
    labels = [("Confidentiality", "keep secrets secret", PURPLE),
              ("Integrity", "no tampering", TEAL),
              ("Availability", "up when needed", AMBER)]
    for (px, py), (lbl, sub, col) in zip(pts, labels):
        b.append(box(px - 90, py - 26, 180, 52, [lbl, sub], col, size=11,
                     lh=14))
    b.append(text(cx, cy + 6, "security", LIGHT, 11, 700))
    fig("cia-triad.svg", 760, 380,
        "The CIA triad of information security", b)


def fig_asymmetric_encryption():
    b = []
    b.append(box(60, 150, 130, 50, ["Sender"], GREY, size=12))
    b.append(box(660, 150, 130, 50, ["Receiver"], GREY, size=12))
    b.append(box(280, 90, 130, 44, ["plaintext"], TEAL, size=11))
    b.append(box(280, 210, 170, 44, ["receiver's", "public key"], PURPLE,
                 size=10.5, lh=13))
    b.append(box(470, 150, 150, 50, ["ciphertext"], AMBER, size=11))
    b.append(box(500, 250, 170, 44, ["receiver's", "private key"], PURPLE_D,
                 size=10.5, lh=13))
    b.append(arrow(190, 165, 280, 120, GREY, 1.5))
    b.append(arrow(345, 134, 470, 165, GREY, 1.6))
    b.append(text(410, 118, "encrypt", LIGHT, 9.5, 600))
    b.append(arrow(345, 210, 430, 180, PURPLE, 1.4, dash="4 3"))
    b.append(arrow(620, 170, 660, 170, GREY, 1.6))
    b.append(arrow(560, 250, 560, 200, PURPLE_D, 1.4, dash="4 3"))
    b.append(text(600, 220, "decrypt", LIGHT, 9.5, 600))
    fig("asymmetric-encryption.svg", 840, 320,
        "Asymmetric (public-key) encryption", b,
        "anyone can encrypt with the public key; only the private key decrypts")


def fig_access_control_matrix():
    b = []
    rows = ["Alice", "Bob", "root"]
    cols = ["File F1", "File F2", "Printer"]
    RW = ("rw", TEAL); R = ("r", PURPLE); NO = ("\u2014", GREY_D)
    PR = ("print", AMBER); ALL_ = ("rwx", TEAL)
    cells = [[RW, R, PR],
             [R, NO, PR],
             [ALL_, ALL_, ALL_]]
    b.append(cellgrid(90, 110, rows, cols, cells, cw=140, ch=44, lw=110))
    b.append(text(430, 250, "rows = subjects (domains) · columns = objects · "
                  "cells = allowed rights", LIGHT, 10, 500))
    fig("access-control-matrix.svg", 760, 290,
        "Access-control matrix", b)


# ── Ch09 · Advanced topics ───────────────────────────────────────────────────
def fig_virtualization_types():
    b = []
    b.append(text(220, 58, "Type 1 · bare-metal", GREY, 12, 700))
    body1, e1 = vstack(90, 78, 300, [
        (["VM", "guest OS"], PURPLE), (["VM", "guest OS"], PURPLE),
        (["Hypervisor"], PURPLE_D), (["Hardware"], GREY_D)], rh=46, gap=8,
        lh=14)
    # override: place two VMs side by side instead
    b = [text(220, 58, "Type 1 · bare-metal", GREY, 12, 700)]
    b.append(box(90, 78, 140, 60, ["VM", "guest OS"], PURPLE, size=10.5, lh=14))
    b.append(box(250, 78, 140, 60, ["VM", "guest OS"], PURPLE, size=10.5,
                 lh=14))
    b.append(box(90, 150, 300, 46, ["Hypervisor"], PURPLE_D, size=12))
    b.append(box(90, 206, 300, 46, ["Hardware"], GREY_D, size=12))
    b.append(text(560, 58, "Type 2 · hosted", GREY, 12, 700))
    b.append(box(470, 78, 140, 56, ["VM", "guest OS"], PURPLE, size=10.5,
                 lh=14))
    b.append(box(630, 78, 140, 56, ["VM", "guest OS"], PURPLE, size=10.5,
                 lh=14))
    b.append(box(470, 142, 300, 40, ["Hypervisor (app)"], TEAL, size=11))
    b.append(box(470, 186, 300, 40, ["Host OS"], PURPLE_D, size=11))
    b.append(box(470, 230, 300, 40, ["Hardware"], GREY_D, size=11))
    fig("virtualization-types.svg", 840, 300,
        "Type 1 vs Type 2 hypervisors", b,
        "a bare-metal hypervisor runs on hardware; a hosted one runs on an OS")


def fig_containers_vs_vms():
    b = []
    b.append(text(210, 58, "Virtual machines", GREY, 12, 700))
    for i in range(2):
        x = 70 + i * 160
        b.append(box(x, 78, 140, 40, ["App"], TEAL, size=11))
        b.append(box(x, 120, 140, 40, ["Bins/libs"], PURPLE, size=10.5))
        b.append(box(x, 162, 140, 44, ["Guest OS"], PURPLE_D, size=10.5))
    b.append(box(70, 214, 300, 38, ["Hypervisor"], GREY, size=11))
    b.append(box(70, 254, 300, 38, ["Host OS + hardware"], GREY_D, size=11))
    b.append(text(620, 58, "Containers", GREY, 12, 700))
    for i in range(3):
        x = 470 + i * 108
        b.append(box(x, 78, 96, 40, ["App"], TEAL, size=11))
        b.append(box(x, 120, 96, 40, ["Bins/libs"], PURPLE, size=10))
    b.append(box(470, 168, 320, 40, ["Container engine"], AMBER, size=11))
    b.append(box(470, 210, 320, 40, ["Host OS  (shared kernel)"], PURPLE_D,
                 size=11))
    b.append(box(470, 252, 320, 38, ["Hardware"], GREY_D, size=11))
    b.append(text(630, 305, "no guest OS \u2192 lighter, faster", LIGHT, 9.5,
                  600))
    fig("containers-vs-vms.svg", 840, 330,
        "Containers share the host kernel; VMs don't", b)


def fig_mobile_os_architecture():
    rows = [(["Applications"], TEAL),
            (["Application framework", "(activity, window, telephony managers)"], PURPLE),
            (["Libraries  +  runtime", "(graphics, media, VM/ART)"], PURPLE_D),
            (["Hardware abstraction layer (HAL)"], AMBER),
            (["Kernel", "(power, drivers, memory, IPC)"], GREY_D)]
    body, endy = vstack(160, 58, 440, rows, rh=52, gap=8, lh=14)
    fig("mobile-os-architecture.svg", 760, endy + 30,
        "Layered mobile OS architecture", [body])


# ── Ch10 · Case studies ──────────────────────────────────────────────────────
def fig_linux_architecture():
    b = []
    b.append(box(120, 62, 520, 40, ["User applications  ·  shells  ·  daemons"],
                 GREY, size=11))
    b.append(box(120, 110, 520, 40, ["GNU C library (glibc)"], TEAL, size=11))
    b.append(rrect(120, 158, 520, 24, PURPLE_D, rx=6))
    b.append(text(380, 170, "system call interface", WHITE, 10.5, 700))
    b.append(rrect(120, 190, 520, 150, "none", rx=10, stroke=PURPLE, sw=1.6))
    b.append(text(380, 208, "kernel", LIGHT, 10, 700))
    subs = ["Process / scheduler", "Memory mgmt", "VFS / file systems",
            "Networking", "Device drivers", "Arch code"]
    for i, s in enumerate(subs):
        cx = 140 + (i % 3) * 172
        cy = 224 + (i // 3) * 54
        b.append(box(cx, cy, 158, 44, [s], PURPLE, size=10.5))
    b.append(box(120, 350, 520, 40, ["Hardware"], GREY_D, size=11))
    for y in (102, 150, 340):
        b.append(arrow(380, y, 380, y + 8, GREY, 1.2))
    fig("linux-architecture.svg", 760, 420, "Linux architecture", b)


def fig_windows_nt_structure():
    b = []
    b.append(text(400, 54, "user mode", LIGHT, 10, 700))
    b.append(box(80, 66, 200, 44, ["Environment", "subsystems"], GREY, size=10.5,
                 lh=13))
    b.append(box(300, 66, 200, 44, ["Applications"], GREY, size=11))
    b.append(box(520, 66, 200, 44, ["System", "processes"], GREY, size=10.5,
                 lh=13))
    b.append(line(60, 130, 740, 130, LIGHT, 1.2, dash="5 4"))
    b.append(text(400, 144, "kernel mode", LIGHT, 10, 700))
    b.append(rrect(80, 158, 640, 96, "none", rx=10, stroke=PURPLE, sw=1.6))
    b.append(text(400, 174, "Executive", LIGHT, 10, 700))
    execs = ["I/O mgr", "Object mgr", "Memory mgr", "Process mgr", "Security"]
    for i, s in enumerate(execs):
        b.append(box(96 + i * 126, 188, 116, 44, [s], PURPLE, size=10))
    b.append(box(80, 264, 310, 42, ["Kernel", "(scheduling, dispatch)"],
                 PURPLE_D, size=10.5, lh=13))
    b.append(box(410, 264, 310, 42, ["Hardware Abstraction Layer (HAL)"],
                 TEAL, size=10.5))
    b.append(box(80, 316, 640, 38, ["Hardware"], GREY_D, size=11))
    fig("windows-nt-structure.svg", 800, 380, "Windows NT architecture", b)


def fig_android_architecture():
    rows = [(["System & user apps"], TEAL),
            (["Java API framework", "(managers, content providers)"], PURPLE),
            (["Native C/C++ libraries  ·  Android runtime (ART)"], PURPLE_D),
            (["Hardware abstraction layer (HAL)"], AMBER),
            (["Linux kernel", "(drivers, power, Binder IPC)"], GREY_D)]
    body, endy = vstack(150, 58, 460, rows, rh=52, gap=8, lh=14)
    fig("android-architecture.svg", 760, endy + 30,
        "Android software stack", [body])


# ── Ch14 · Networking ────────────────────────────────────────────────────────
def fig_network_stack():
    b = []
    layers = [("Application", "HTTP · DNS · SSH", TEAL),
              ("Transport", "TCP · UDP  (ports)", PURPLE),
              ("Network", "IP  (addresses, routing)", PURPLE_D),
              ("Link", "Ethernet · Wi-Fi (frames)", AMBER),
              ("Physical", "bits on the wire", GREY_D)]
    y = 60
    for name, sub, col in layers:
        b.append(box(160, y, 300, 48, [name], col, size=12))
        b.append(text(480, y + 24, sub, LIGHT, 10, 500, anchor="start"))
        y += 56
    b.append(arrow(120, 70, 120, y - 20, GREY, 1.6))
    b.append(text(96, (60 + y) / 2, "send", LIGHT, 10, 700, anchor="middle"))
    b.append(text(96, (60 + y) / 2 + 16, "\u2193", LIGHT, 12, 700))
    fig("network-stack.svg", 780, y + 24,
        "The TCP/IP protocol stack", b,
        "each layer adds a header; the peer layer on the far side reads it")


def fig_tcp_handshake():
    b = []
    b.append(box(90, 70, 150, 44, ["Client"], PURPLE, size=12))
    b.append(box(560, 70, 150, 44, ["Server"], TEAL, size=12))
    b.append(line(165, 114, 165, 320, LIGHT, 1.2))
    b.append(line(635, 114, 635, 320, LIGHT, 1.2))
    msgs = [(150, "SYN  seq=x", 0),
            (200, "SYN-ACK  seq=y, ack=x+1", 1),
            (250, "ACK  ack=y+1", 0)]
    for y, m, rev in msgs:
        if rev:
            b.append(arrow(635, y, 165, y, TEAL, 1.7))
            b.append(text(400, y - 10, m, LIGHT, 10, 600))
        else:
            b.append(arrow(165, y, 635, y, PURPLE, 1.7))
            b.append(text(400, y - 10, m, LIGHT, 10, 600))
    b.append(text(165, 300, "ESTABLISHED", TEAL, 10, 700))
    b.append(text(635, 300, "ESTABLISHED", TEAL, 10, 700))
    fig("tcp-handshake.svg", 800, 340,
        "TCP three-way handshake", b,
        "three segments synchronise sequence numbers before any data flows")


def fig_tcp_termination():
    b = []
    b.append(box(90, 70, 150, 44, ["Active close"], PURPLE, size=11))
    b.append(box(560, 70, 150, 44, ["Passive close"], TEAL, size=11))
    b.append(line(165, 114, 165, 340, LIGHT, 1.2))
    b.append(line(635, 114, 635, 340, LIGHT, 1.2))
    msgs = [(150, "FIN", 0), (195, "ACK", 1), (250, "FIN", 1), (295, "ACK", 0)]
    for y, m, rev in msgs:
        if rev:
            b.append(arrow(635, y, 165, y, TEAL, 1.7))
        else:
            b.append(arrow(165, y, 635, y, PURPLE, 1.7))
        b.append(text(400, y - 10, m, LIGHT, 10, 600))
    b.append(text(165, 325, "TIME_WAIT", AMBER, 10, 700))
    fig("tcp-termination.svg", 800, 360,
        "TCP four-way connection termination", b,
        "each direction is closed independently with its own FIN / ACK")


# ── Ch15 · Boot process ──────────────────────────────────────────────────────
def fig_boot_process():
    b = []
    steps = [("Power on", "CPU resets", GREY),
             ("Firmware", "BIOS / UEFI, POST", PURPLE),
             ("Bootloader", "GRUB loads kernel", TEAL),
             ("Kernel", "init hardware, mount root", PURPLE_D),
             ("init / systemd", "start services", AMBER),
             ("User space", "login, shell", GREY_D)]
    for i, (a, c, col) in enumerate(steps):
        x = 50 + (i % 3) * 310
        y = 80 + (i // 3) * 120
        b.append(box(x, y, 250, 64, [a, c], col, size=12, lh=16))
        if i % 3 != 2 and i != len(steps) - 1:
            b.append(arrow(x + 250, y + 32, x + 310, y + 32, GREY, 1.7))
    b.append(path("M795 144 C795 182 175 182 175 200", GREY, 1.5,
                  arrow_end=True))
    fig("boot-process.svg", 980, 300,
        "From power-on to a usable system", b,
        "each stage hands control to the next, more capable one")


def fig_bios_vs_uefi():
    b = []
    b.append(box(80, 80, 300, 40, ["Legacy BIOS"], GREY, size=12))
    for i, t in enumerate(["16-bit real mode", "MBR partitioning (< 2 TB)",
                           "boot code in 512-byte sector", "no secure boot",
                           "slow, sequential POST"]):
        b.append(text(96, 138 + i * 30, "\u2022 " + t, GREY, 10.5, 500,
                      anchor="start"))
    b.append(box(500, 80, 300, 40, ["UEFI"], PURPLE, size=12))
    for i, t in enumerate(["32/64-bit, drivers", "GPT partitioning (huge disks)",
                           "EFI apps on a FAT partition", "Secure Boot",
                           "faster, parallel init"]):
        b.append(text(516, 138 + i * 30, "\u2022 " + t, PURPLE, 10.5, 500,
                      anchor="start"))
    fig("bios-vs-uefi.svg", 860, 310,
        "Legacy BIOS vs UEFI firmware", b)


ALL = [
    # Ch01 introduction
    fig_os_position, fig_monolithic_vs_microkernel, fig_system_call,
    fig_user_kernel_mode,
    # Ch02 process management
    fig_five_state_model, fig_context_switch, fig_process_vs_thread,
    fig_scheduling_queues, fig_ipc_models,
    # Ch03 memory management
    fig_memory_hierarchy, fig_paging_translation, fig_tlb,
    fig_two_level_page_table, fig_page_fault, fig_clock_replacement,
    fig_fragmentation,
    # Ch04 cpu scheduling
    fig_cpu_io_burst, fig_round_robin, fig_mlfq, fig_priority_inversion,
    # Ch05 file systems
    fig_file_allocation, fig_inode, fig_directory_tree, fig_journaling,
    # Ch06 synchronization & deadlocks
    fig_producer_consumer, fig_resource_allocation_graph,
    fig_deadlock_conditions, fig_bankers_safe_state,
    # Ch07 I/O & storage
    fig_dma, fig_io_software_layers, fig_hdd_anatomy,
    fig_disk_scheduling_scan, fig_raid_levels,
    # Ch08 security
    fig_cia_triad, fig_asymmetric_encryption, fig_access_control_matrix,
    # Ch09 advanced
    fig_virtualization_types, fig_containers_vs_vms,
    fig_mobile_os_architecture,
    # Ch10 case studies
    fig_linux_architecture, fig_windows_nt_structure,
    fig_android_architecture,
    # Ch14 networking
    fig_network_stack, fig_tcp_handshake, fig_tcp_termination,
    # Ch15 boot
    fig_boot_process, fig_bios_vs_uefi,
]

if __name__ == "__main__":
    for fn in ALL:
        fn()
    print(f"\nDone: {len(ALL)} figures generated.")

