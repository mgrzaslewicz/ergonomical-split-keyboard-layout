#!/usr/bin/env python3
"""
Deterministic HTML visual of a Vial keyboard layout (.vil file).
Usage: python3 generate_layout.py [input.vil [output.html]]
Same input + same script = byte-identical output.
"""

import json
import re
import sys
from pathlib import Path

# ── Keycode tables ─────────────────────────────────────────────────────────────

KC = {
    'KC_A': 'A', 'KC_B': 'B', 'KC_C': 'C', 'KC_D': 'D', 'KC_E': 'E',
    'KC_F': 'F', 'KC_G': 'G', 'KC_H': 'H', 'KC_I': 'I', 'KC_J': 'J',
    'KC_K': 'K', 'KC_L': 'L', 'KC_M': 'M', 'KC_N': 'N', 'KC_O': 'O',
    'KC_P': 'P', 'KC_Q': 'Q', 'KC_R': 'R', 'KC_S': 'S', 'KC_T': 'T',
    'KC_U': 'U', 'KC_V': 'V', 'KC_W': 'W', 'KC_X': 'X', 'KC_Y': 'Y',
    'KC_Z': 'Z',
    'KC_1': '1', 'KC_2': '2', 'KC_3': '3', 'KC_4': '4', 'KC_5': '5',
    'KC_6': '6', 'KC_7': '7', 'KC_8': '8', 'KC_9': '9', 'KC_0': '0',
    'KC_SPACE': 'SPC',
    'KC_ENTER': '↵',
    'KC_ESCAPE': 'ESC',
    'KC_BSPACE': '⌫',
    'KC_TAB': '⇥',
    'KC_MINUS': '-', 'KC_EQUAL': '=',
    'KC_LBRACKET': '[', 'KC_RBRACKET': ']',
    'KC_BSLASH': '\\',
    'KC_SCOLON': ';', 'KC_QUOTE': "'", 'KC_GRAVE': '`',
    'KC_COMMA': ',', 'KC_DOT': '.', 'KC_SLASH': '/',
    'KC_CAPSLOCK': 'CAPS',
    'KC_DELETE': 'DEL',
    'KC_HOME': 'HOME', 'KC_END': 'END',
    'KC_PGUP': 'PgUp', 'KC_PGDOWN': 'PgDn',
    'KC_UP': '↑', 'KC_DOWN': '↓', 'KC_LEFT': '←', 'KC_RIGHT': '→',
    'KC_F1': 'F1', 'KC_F2': 'F2', 'KC_F3': 'F3', 'KC_F4': 'F4',
    'KC_F5': 'F5', 'KC_F6': 'F6', 'KC_F7': 'F7', 'KC_F8': 'F8',
    'KC_F9': 'F9', 'KC_F10': 'F10', 'KC_F11': 'F11', 'KC_F12': 'F12',
    'KC_PSCREEN': 'PrtSc',
    'KC_KP_0': '0', 'KC_KP_1': '1', 'KC_KP_2': '2', 'KC_KP_3': '3',
    'KC_KP_4': '4', 'KC_KP_5': '5', 'KC_KP_6': '6', 'KC_KP_7': '7',
    'KC_KP_8': '8', 'KC_KP_9': '9',
    'KC_KP_MINUS': '-',
    'KC_VOLU': 'Vol+', 'KC_VOLD': 'Vol-', 'KC_MPLY': '⏯',
    'KC_RALT': 'RAlt',
    'KC_LSHIFT': '⇧',
    'QK_CAPS_WORD_TOGGLE': 'CAPS\nWRD',
    'KC_TRNS': '▽',
    'KC_NO': '',
}

SHIFTED = {
    'KC_1': '!', 'KC_2': '@', 'KC_3': '#', 'KC_4': '$', 'KC_5': '%',
    'KC_6': '^', 'KC_7': '&', 'KC_8': '*', 'KC_9': '(', 'KC_0': ')',
    'KC_MINUS': '_', 'KC_EQUAL': '+',
    'KC_LBRACKET': '{', 'KC_RBRACKET': '}',
    'KC_BSLASH': '|', 'KC_SCOLON': ':', 'KC_QUOTE': '"',
    'KC_GRAVE': '~', 'KC_COMMA': '<', 'KC_DOT': '>', 'KC_SLASH': '?',
    'KC_ENTER': '⇧↵',
}

MOD_SYM = {
    'LGUI_T': '⌘', 'RGUI_T': '⌘',
    'LALT_T': '⌥', 'RALT_T': '⌥',
    'LCTL_T': '⌃', 'RCTL_T': '⌃',
    'LSFT_T': '⇧', 'RSFT_T': '⇧',
}

LAYER_NAMES = ['Base', 'Nav/Num', 'Symbols', 'Layer 3', 'Layer 4',
               'Layer 5', 'Layer 6', 'Layer 7']

COMBO_COLORS = [
    ('#e74c3c', '#e74c3c2a'),
    ('#e67e22', '#e67e222a'),
    ('#f1c40f', '#f1c40f2a'),
    ('#2ecc71', '#2ecc712a'),
    ('#3498db', '#3498db2a'),
    ('#9b59b6', '#9b59b62a'),
    ('#1abc9c', '#1abc9c2a'),
    ('#e91e63', '#e91e632a'),
]


# ── Key decoding ───────────────────────────────────────────────────────────────

def kc_name(kc):
    return KC.get(kc, kc.replace('KC_', ''))


def decode(kc, tap_dances):
    """Returns (main_label, sub_label, raw_kc_for_combo_matching)."""
    if kc == -1:
        return None, None, None

    m = re.match(r'(LGUI_T|LALT_T|LCTL_T|LSFT_T|RGUI_T|RALT_T|RCTL_T|RSFT_T)\((.+)\)$', kc)
    if m:
        return kc_name(m.group(2)), MOD_SYM[m.group(1)], m.group(2)

    m = re.match(r'LT(\d+)\((.+)\)$', kc)
    if m:
        return kc_name(m.group(2)), f'L{m.group(1)}', m.group(2)

    m = re.match(r'LT\((\d+),\s*(.+)\)$', kc)
    if m:
        return kc_name(m.group(2)), f'L{m.group(1)}', m.group(2)

    m = re.match(r'MO\((\d+)\)$', kc)
    if m:
        return f'MO{m.group(1)}', '', kc

    m = re.match(r'TD\((\d+)\)$', kc)
    if m:
        n = int(m.group(1))
        td = tap_dances[n] if n < len(tap_dances) else ['KC_NO'] * 5
        tap_label = kc_name(td[0]) if td[0] != 'KC_NO' else ''
        dtap_label, _, _ = decode(td[1], tap_dances) if td[1] not in ('KC_NO', '') else ('', None, None)
        sub = f'2×{dtap_label}' if dtap_label else ''
        raw = td[0] if td[0] != 'KC_NO' else kc
        return tap_label, sub, raw

    m = re.match(r'LSFT\((.+)\)$', kc)
    if m:
        inner = m.group(1)
        return SHIFTED.get(inner, f'⇧{kc_name(inner)}'), '', kc

    m = re.match(r'LCTL\((.+)\)$', kc)
    if m:
        return f'⌃{kc_name(m.group(1))}', '', kc

    return kc_name(kc), '', kc


# ── Combo position map ─────────────────────────────────────────────────────────

def build_pos_map(layout, tap_dances):
    """raw_kc → list of (layer, group, col) across all layers."""
    pos = {}
    for li, layer in enumerate(layout):
        for gi, row in enumerate(layer):
            for ci, kc in enumerate(row):
                if kc == -1:
                    continue
                _, _, raw = decode(kc, tap_dances)
                if raw and raw not in ('KC_NO', 'KC_TRNS'):
                    pos.setdefault(raw, []).append((li, gi, ci))
    return pos


# ── HTML rendering ─────────────────────────────────────────────────────────────

def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')


def render_key(kc, tap_dances, combo_style=''):
    label, sub, _ = decode(kc, tap_dances)
    if label is None:
        return '<div class="key phantom"></div>'
    cls = ''
    if kc == 'KC_TRNS':
        cls = ' trans'
    elif kc == 'KC_NO':
        cls = ' empty'
    sub_html = f'<span class="sub">{esc(sub)}</span>' if sub else ''
    return (
        f'<div class="key{cls}" style="{combo_style}">'
        f'<span class="main">{esc(label)}</span>'
        f'{sub_html}'
        f'</div>'
    )


def render_row(row, group_idx, layer_idx, reversed_cols, tap_dances, key_colors):
    cells = []
    for c_idx, kc in enumerate(row):
        # c_idx is the actual data column; reversal is visual only
        color_pair = key_colors.get((layer_idx, group_idx, c_idx))
        style = ''
        if color_pair and kc not in (-1, 'KC_TRNS', 'KC_NO'):
            style = f'border-color:{color_pair[0]};background:{color_pair[1]};'
        cells.append(render_key(kc, tap_dances, style))
    if reversed_cols:
        cells.reverse()
    return '<div class="row">' + ''.join(cells) + '</div>'


def render_layer(layer_data, layer_idx, tap_dances, key_colors):
    # Groups 0-4 = left half, 5-9 = right half.
    # Right half is stored outermost-first, so reverse cols for display.
    def half(main_rows, thumb, start_group, reversed_cols):
        html = '<div class="half">'
        for r, row in enumerate(main_rows):
            html += render_row(row, start_group + r, layer_idx, reversed_cols, tap_dances, key_colors)
        html += render_row(thumb, start_group + 4, layer_idx, reversed_cols, tap_dances, key_colors)
        html += '</div>'
        return html

    return (
        '<div class="keyboard">'
        + half(layer_data[0:4], layer_data[4], 0, False)
        + '<div class="gap"></div>'
        + half(layer_data[5:9], layer_data[9], 5, True)
        + '</div>'
    )


def is_layer_empty(layer):
    return all(kc in ('KC_TRNS', 'KC_NO', -1) for row in layer for kc in row)


# ── Main generation ────────────────────────────────────────────────────────────

def generate(data):
    layout = data['layout']
    tap_dances = data.get('tap_dance', [])
    combos = data.get('combo', [])

    pos_map = build_pos_map(layout, tap_dances)

    # Assign combo colors and build key highlight map (base layer only)
    active_combos = [(c, i) for i, c in enumerate(combos) if c[0] != 'KC_NO']
    key_colors = {}
    combo_rows = []

    for ci, (combo, _) in enumerate(active_combos):
        trigger_kcs = [k for k in combo[:4] if k != 'KC_NO']
        output_kc = combo[4]
        cp = COMBO_COLORS[ci % len(COMBO_COLORS)]
        for tk in trigger_kcs:
            for (li, gi, col) in pos_map.get(tk, []):
                if li == 0:
                    key_colors[(0, gi, col)] = cp
        trigger_labels = [kc_name(k) for k in trigger_kcs]
        out_label, _, _ = decode(output_kc, tap_dances)
        combo_rows.append((cp[0], trigger_labels, out_label))

    # Active tap dances
    active_tds = [(i, td) for i, td in enumerate(tap_dances) if td[0] != 'KC_NO']

    # Nav: only non-empty layers
    visible = [(li, l) for li, l in enumerate(layout) if not is_layer_empty(l)]
    nav = '<nav>' + ''.join(
        f'<a href="#l{li}">{LAYER_NAMES[li] if li < len(LAYER_NAMES) else f"L{li}"}</a>'
        for li, _ in visible
    ) + '</nav>'

    # Layer sections
    layers_html = ''
    for li, layer in visible:
        name = LAYER_NAMES[li] if li < len(LAYER_NAMES) else f'Layer {li}'
        layers_html += (
            f'<section class="layer" id="l{li}">'
            f'<h2>Layer {li} — {name}</h2>'
            + render_layer(layer, li, tap_dances, key_colors if li == 0 else {})
            + '</section>'
        )

    # Combos section
    combo_html = ''
    if combo_rows:
        rows = ''.join(
            f'<tr>'
            f'<td><span class="dot" style="background:{c}"></span></td>'
            f'<td>{" + ".join(esc(k) for k in keys)}</td>'
            f'<td class="out">{esc(out)}</td>'
            f'</tr>'
            for c, keys, out in combo_rows
        )
        combo_html = (
            '<section class="extra" id="combos"><h2>Combos</h2>'
            '<table><tr><th></th><th>Keys</th><th>Output</th></tr>'
            + rows + '</table></section>'
        )

    # Tap dance section
    td_html = ''
    if active_tds:
        def td_cell(v):
            if v in ('KC_NO', ''):
                return '—'
            label, _, _ = decode(v, tap_dances)
            return esc(label) if label else '—'
        rows = ''.join(
            f'<tr>'
            f'<td>TD{i}</td>'
            f'<td>{td_cell(td[0])}</td>'
            f'<td>{td_cell(td[1])}</td>'
            f'<td>{td_cell(td[2])}</td>'
            f'<td>{td_cell(td[3])}</td>'
            f'<td>{td[4]}ms</td>'
            f'</tr>'
            for i, td in active_tds
        )
        td_html = (
            '<section class="extra" id="td"><h2>Tap Dances</h2>'
            '<table>'
            '<tr><th>ID</th><th>Tap</th><th>2× Tap</th>'
            '<th>Hold</th><th>Tap+Hold</th><th>Timeout</th></tr>'
            + rows + '</table></section>'
        )

    return HTML_TEMPLATE.format(
        nav=nav, layers=layers_html, combos=combo_html, tap_dances=td_html,
    )


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width">
<title>Silakka54 Layout</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0f1117;color:#c9d1d9;font-family:'JetBrains Mono',monospace;font-size:13px;padding:24px 32px;line-height:1.4}}
h1{{font-size:1.3em;color:#a78bfa;margin-bottom:12px}}
h2{{font-size:.75em;color:#6e7681;text-transform:uppercase;letter-spacing:.1em;margin-bottom:14px}}
nav{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:32px}}
nav a{{text-decoration:none;color:#58a6ff;background:#161b22;border:1px solid #30363d;border-radius:4px;padding:4px 10px;font-size:.8em}}
nav a:hover{{background:#1f2937}}
section.layer{{margin-bottom:44px}}
section.extra{{margin-bottom:32px}}
.keyboard{{display:flex;gap:36px;align-items:flex-start}}
.half{{display:flex;flex-direction:column;gap:4px}}
.row{{display:flex;gap:4px}}
.gap{{width:36px}}
.key{{width:50px;height:50px;border:1px solid #30363d;border-radius:6px;background:#161b22;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:3px;transition:none}}
.key.phantom{{background:transparent;border-color:transparent;pointer-events:none}}
.key.trans{{background:#0d1117;border-color:#1e2530;color:#3a4150}}
.key.empty{{background:#0d1117;border-color:#1a1f28;color:#2a303a}}
.key .main{{font-size:.85em;font-weight:600;line-height:1.2}}
.key .sub{{font-size:.72em;color:#8b949e;margin-top:3px}}
table{{border-collapse:collapse;min-width:280px}}
th,td{{padding:6px 12px;border:1px solid #21262d;text-align:left}}
th{{background:#0d1117;color:#6e7681;font-weight:500;font-size:.75em;text-transform:uppercase;letter-spacing:.05em}}
td{{background:#161b22;font-size:.85em}}
td.out{{font-weight:700;color:#e2e8f0}}
.dot{{display:inline-block;width:10px;height:10px;border-radius:50%;vertical-align:middle}}
</style>
</head>
<body>
<h1>Silakka54 Keyboard Layout</h1>
{nav}
{layers}
{combos}
{tap_dances}
</body>
</html>"""


def main():
    args = sys.argv[1:]
    vil = Path(args[0]) if args else Path('silakka54.vil')
    out = Path(args[1]) if len(args) > 1 else vil.with_suffix('.html')
    data = json.loads(vil.read_text(encoding='utf-8'))
    out.write_text(generate(data), encoding='utf-8')
    print(f'Generated: {out}')


if __name__ == '__main__':
    main()
