#!/usr/bin/env python3
"""Replace the user-visible product name ReactOS -> Lumen in resource/translation
files, leaving copyright lines, credits, URLs, paths and identifiers alone."""
import os, re, sys

ROOT = sys.argv[1]
SKIP_DIRS = ('modules/rostests', '/wine/', 'sdk/tools', '/.git/', 'modules/rosapps')
KEEP = re.compile(r'copyright|\(c\)|©|http|www\.|reactos\.org|project|team|developer|adaptation|'
                  r'written by|contributor|based on|thanks|authors?\b|\\\\reactos|reactos\\\\|'
                  r'#include|#define|IDS_REACTOS|IDB_|IDI_|\.bmp|\.ico|\.png|jira|\bgit\b|forum|wiki|irc|'
                  r'mailing|apache|freetype|wine\b', re.I)
WORD = re.compile(r'(?:(?<=\\n)|(?<=\\t)|\b)ReactOS\b')
changed = files = 0
for dirpath, dirs, names in os.walk(ROOT):
    rel = dirpath.replace(ROOT, '')
    if any(s in rel + '/' for s in SKIP_DIRS):
        continue
    langdir = os.path.basename(dirpath).lower() in ('lang', 'langs', 'po')
    for n in names:
        p = os.path.join(dirpath, n)
        low = n.lower()
        if not (low.endswith('.rc') and (langdir or low in ('en-us.rc',)) or
                (langdir and low.endswith('.h') and 'usetup' in p) or
                (langdir and low.endswith('.inf'))):
            continue
        raw = open(p, 'rb').read()
        for enc in ('utf-8', 'cp1252'):
            try:
                text = raw.decode(enc); break
            except UnicodeDecodeError:
                continue
        else:
            continue
        out = []
        n_here = 0
        for line in text.splitlines(True):
            if WORD.search(line) and not KEEP.search(line):
                line, k = WORD.subn('Lumen', line)
                n_here += k
            out.append(line)
        if n_here:
            open(p, 'wb').write(''.join(out).encode(enc))
            changed += n_here; files += 1
print('replaced', changed, 'in', files, 'files')
