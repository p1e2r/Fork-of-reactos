#!/usr/bin/env python3
"""Apply the Lumen (Windows 11-style) colors and metrics to the Light INI files."""
import re, sys

SYS = {
    'ActiveCaption': '243 243 243',
    'GradientActiveCaption': '243 243 243',
    'InactiveCaption': '243 243 243',
    'GradientInactiveCaption': '243 243 243',
    'InactiveCaptionText': '128 128 128',
    'CaptionText': '26 26 26',
    'Background': '0 84 166',
    'Btnface': '243 243 243',
    'BtnShadow': '200 200 200',
    'DkShadow3d': '160 160 160',
    'Light3d': '249 249 249',
    'GrayText': '160 160 160',
    'Highlight': '0 95 184',
    'HighlightText': '255 255 255',
    'HotTracking': '0 95 184',
    'Menu': '249 249 249',
    'MenuBar': '243 243 243',
    'MenuHilight': '0 95 184',
    'MenuText': '26 26 26',
    'Window': '255 255 255',
}


def set_key(section_text, key, value):
    pat = re.compile(r'^(%s\s*=\s*)[^;\r\n]*' % re.escape(key), re.M | re.I)
    if pat.search(section_text):
        return pat.sub(lambda m: m.group(1) + value, section_text, count=1)
    return section_text.rstrip('\r\n') + '\n%s = %s\n\n' % (key, value)


def del_key(section_text, key):
    return re.sub(r'^%s\s*=.*\n' % re.escape(key), '', section_text, flags=re.M | re.I)


def edit(path, regular):
    s = open(path, encoding='utf-8', errors='surrogateescape').read()
    parts = re.split(r'(?m)^(?=\[)', s)
    out = []
    for p in parts:
        m = re.match(r'\[([^\]]+)\]', p)
        name = m.group(1).lower() if m else ''
        if name == 'sysmetrics':
            for k, v in SYS.items():
                p = set_key(p, k, v)
            if regular:
                p = set_key(p, 'CaptionBarHeight', '30')
                p = set_key(p, 'CaptionFont', 'Tahoma, 9')
                p = set_key(p, 'SmallCaptionFont', 'Tahoma, 8')
        elif name == 'button.pushbutton':
            p = set_key(p, 'TextColor', '26 26 26')
            p = set_key(p, 'SizingMargins', '5, 5, 5, 5')
            p = del_key(p, 'TEXTSHADOWOFFSET')
        elif name == 'button.pushbutton(defaulted)':
            pass
        elif name in ('window.caption', 'window.mincaption', 'window.maxcaption', 'window.smallcaption'):
            p = set_key(p, 'FillColorHint', '243 243 243')
            p = set_key(p, 'SizingMargins', '2, 2, 2, 2')
            p = del_key(p, 'Transparent')
        elif name in ('window.caption(active)', 'window.maxcaption(active)'):
            p = set_key(p, 'TextColor', '26 26 26')
        elif name in ('window.closebutton', 'window.maxbutton', 'window.minbutton', 'window.restorebutton',
                      'window.helpbutton'):
            p = set_key(p, 'SizingMargins', '2, 2, 2, 2')
            p = set_key(p, 'FillColorHint', '196 43 28' if name == 'window.closebutton' else '243 243 243')
        elif name == 'window.dialog':
            p = set_key(p, 'BorderColor', '243 243 243')
            p = set_key(p, 'FillColor', '243 243 243')
        elif name == 'toolbar':
            p = set_key(p, 'FillColor', '243 243 243')
        elif name in ('progress.chunk', 'progress.chunkvert'):
            p = del_key(p, 'Transparent'); p = del_key(p, 'TransparentColor')
            p = set_key(p, 'sizingMargins', '3, 3, 3, 3')
        elif name in ('progress.bar', 'progress.barvert'):
            p = set_key(p, 'sizingMargins', '3, 3, 3, 3')
        elif name.startswith('taskbar.background'):
            p = set_key(p, 'FillColorHint', '243 243 243')
            p = set_key(p, 'SizingMargins', '1, 1, 1, 1')
            p = del_key(p, 'Transparent'); p = del_key(p, 'TransparentColor')
        elif name.startswith('taskbar.sizingbar'):
            p = set_key(p, 'FillColorHint', '243 243 243')
        elif name in ('taskband::toolbar.button', 'taskbandvert::toolbar.button', 'taskbarvert::toolbar.button',
                      'taskbar::toolbar.button'):
            p = set_key(p, 'FillColorHint', '243 243 243')
            p = set_key(p, 'SizingMargins', '8, 8, 6, 6')
            p = set_key(p, 'ContentMargins', '4, 4, 2, 4')
            p = set_key(p, 'TextColor', '26 26 26')
            p = del_key(p, 'Transparent'); p = del_key(p, 'TransparentColor')
        elif name.startswith('taskband::toolbar') or name.startswith('taskbandvert::toolbar('):
            p = set_key(p, 'TextColor', '26 26 26')
            p = del_key(p, 'TextShadowColor'); p = del_key(p, 'TextShadowType')
        elif name == 'start::button':
            p = set_key(p, 'ContentMargins', '0, 0, 0, 0')
            p = set_key(p, 'SizingMargins', '6, 6, 6, 6')
            p = set_key(p, 'SizingType', 'Stretch')
            p = set_key(p, 'FillColorHint', '243 243 243')
            p = set_key(p, 'TextColor', '26 26 26')
            p = del_key(p, 'TextShadowColor'); p = del_key(p, 'TEXTSHADOWOFFSET')
            p = del_key(p, 'Transparent'); p = del_key(p, 'TransparentColor')
        elif name == 'traynotify::clock':
            p = set_key(p, 'TextColor', '26 26 26')
        elif name == 'traynotifyhoriz::traynotify.background' or name == 'traynotifyvert::traynotify.background':
            p = set_key(p, 'FillColorHint', '243 243 243')
            p = set_key(p, 'SizingMargins', '1, 1, 1, 1')
            p = set_key(p, 'ContentMargins', '8, 4, 0, 0')
        elif name in ('taskbar::rebar',):
            p = set_key(p, 'TextColor', '26 26 26')
        out.append(p)
    open(path, 'w', encoding='utf-8', errors='surrogateescape', newline='\r\n').write(''.join(out))


for f in sys.argv[1:]:
    edit(f, 'Regular' in f)
    print('edited', f)

# Fonts: Selawik (OFL, bundled in media/fonts) in place of Tahoma.
def fonts(path):
    s = open(path, encoding='utf-8', errors='surrogateescape', newline='').read()
    s = s.replace('Tahoma, 8', 'Selawik, 9').replace('Tahoma', 'Selawik')
    open(path, 'w', encoding='utf-8', errors='surrogateescape', newline='').write(s)


for f in sys.argv[1:]:
    fonts(f)
