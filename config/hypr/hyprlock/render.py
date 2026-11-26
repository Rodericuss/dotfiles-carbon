#!/usr/bin/env python3
"""Carbon · Hyprlock: draws the static part of the lock screen (header, sign-in tile, status
bar) per monitor and writes backgrounds.conf for hyprlock.conf. Live text (clock, date, field,
lock time, battery) is drawn by hyprlock on top. Layout is centered on a 1920x1080 artboard."""
import json, os, subprocess
from pathlib import Path
import cairo
import gi
gi.require_version('Pango', '1.0'); gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo

CACHE = Path.home()/'.cache/carbon-lock'
SANS, MONO = 'IBM Plex Sans', 'IBM Plex Mono'
BG, L1, L2, RULE, STRONG = '#161616', '#262626', '#393939', '#393939', '#6f6f6f'
TEXT, TEXT2, MUTED = '#f2f4f8', '#c6c6c6', '#a8a8a8'
BLUE, PURPLE, MAGENTA, TEAL, GREEN = '#78a9ff', '#be95ff', '#ff7eb6', '#3ddbd9', '#42be65'

def rgb(h, a=1.0):
    h = h.lstrip('#'); return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4)) + (a,)

def sh(*a):
    try: return subprocess.check_output(a, text=True, stderr=subprocess.DEVNULL, timeout=2).strip()
    except (OSError, subprocess.SubprocessError): return ''

def text(cr, s, x, base, size, color, font=SANS, weight='Regular', anchor='left'):
    lay = PangoCairo.create_layout(cr)
    fd = Pango.FontDescription.from_string(f'{font} {weight}')
    fd.set_absolute_size(size*Pango.SCALE); lay.set_font_description(fd); lay.set_text(s, -1)
    w = lay.get_extents()[1].width/Pango.SCALE
    if anchor == 'right': x -= w
    cr.set_source_rgba(*rgb(color)); cr.move_to(x, base - lay.get_baseline()/Pango.SCALE)
    PangoCairo.show_layout(cr, lay)
    return x + w

def rect(cr, color, x, y, w, h):
    cr.set_source_rgba(*rgb(color)); cr.rectangle(x, y, w, h); cr.fill()

def status_values():
    net = ''
    for line in sh('nmcli', '-t', '-f', 'DEVICE,TYPE,STATE', 'dev').splitlines():
        dev, typ, state = (line.split(':') + ['', '', ''])[:3]
        if state == 'connected' and typ in ('wifi', 'ethernet'): net = dev; break
    opts = {k: sh('hyprctl', 'getoption', f'input:{k}', '-j') for k in ('kb_layout', 'kb_variant')}
    val = {k: (json.loads(v).get('str', '') if v else '') for k, v in opts.items()}
    lay = (val['kb_layout'].split(',')[0] or 'br').lower()
    var = (val['kb_variant'].split(',')[0] or ('abnt2' if lay == 'br' else '')).lower()
    return net, f'{lay}-{var}' if var else lay

def render(w, h, path, user, net, kb):
    s = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h); cr = cairo.Context(s)
    rect(cr, BG, 0, 0, w, h)
    X = lambda dx: w/2 + dx - 960
    Y = lambda dy: h/2 + dy - 540

    # header, same as the Waybar shell header
    rect(cr, RULE, 0, 32, w, 1)
    x = text(cr, 'carbon ', 16, 21, 14, TEXT, weight='SemiBold')
    text(cr, 'workstation', x, 21, 14, MUTED)
    rect(cr, RULE, x + 88, 0, 1, 32)

    # sign-in tile: 480 wide on layer 01, form inside with 24px padding
    tx, ty, tw, th = X(720), Y(540), 480, 232
    rect(cr, L1, tx, ty, tw, th)
    rect(cr, BLUE, tx, ty, tw, 2)
    L, R = tx + 24, tx + tw - 24
    text(cr, 'Sessão travada', L, ty + 48, 20, TEXT)
    text(cr, user, R, ty + 48, 13, MUTED, font=MONO, anchor='right')
    text(cr, 'Senha', L, ty + 88, 12, TEXT2)
    rect(cr, L2, L, ty + 98, tw - 48, 48)          # field; hyprlock draws the live field on top
    rect(cr, STRONG, L, ty + 145, tw - 48, 1)      # bottom rule of the Carbon text input
    text(cr, '↵ destravar', L, ty + 176, 12, MUTED, font=MONO)
    text(cr, 'esc limpar', R, ty + 176, 12, MUTED, font=MONO, anchor='right')
    # four type squares, as in the app icon
    for i, c in enumerate((BLUE, PURPLE, MAGENTA, TEAL)):
        rect(cr, c, L + i*14, ty + th - 30, 10, 10)

    # status bar, bottom edge
    rect(cr, RULE, 0, h - 33, w, 1)
    x = 16
    for color, label in ((GREEN if net else '#525252', net or 'offline'), (MUTED, kb)):
        rect(cr, color, x, h - 20, 8, 8)
        x = text(cr, label, x + 14, h - 12, 12, TEXT2, font=MONO) + 24
    s.write_to_png(str(path))

def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    mons = json.loads(sh('hyprctl', 'monitors', '-j') or '[]')
    user = os.environ.get('USER', 'operador'); net, kb = status_values()
    blocks = []
    for m in mons:
        w, h = round(m['width']), round(m['height'])
        p = CACHE/f"{m['name']}.png"; render(w, h, p, user, net, kb)
        blocks.append(f"background {{\n    monitor = {m['name']}\n    path = {p}\n    color = rgb(161616)\n}}\n")
    (CACHE/'backgrounds.conf').write_text('\n'.join(blocks))

if __name__ == '__main__':
    main()
