"""Download the Noto Sans (weight 600) subsets the generators read into fonts/.

Google Fonts serves a per-request subset through the css2 API's `text=` parameter.
A family that holds none of the requested characters answers with an error page;
that family is skipped, and the generators skip a missing font file too.
"""
import os, re, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
FAMS = ['Noto Sans', 'Noto Sans JP', 'Noto Sans KR', 'Noto Sans SC', 'Noto Sans Thai',
        'Noto Sans Arabic', 'Noto Sans Hebrew', 'Noto Sans Devanagari', 'Noto Sans Bengali',
        'Noto Sans Tamil', 'Noto Sans Telugu', 'Noto Sans Georgian', 'Noto Sans Armenian',
        'Noto Sans Ethiopic', 'Noto Sans Cherokee', 'Noto Sans Canadian Aboriginal']
text = open(os.path.join(HERE, 'glyphs.txt'), encoding='utf-8').read().strip()
os.makedirs(os.path.join(HERE, 'fonts'), exist_ok=True)
for fam in FAMS:
    url = ('https://fonts.googleapis.com/css2?family=' + fam.replace(' ', '+')
           + ':wght@600&text=' + urllib.parse.quote(text))
    try:
        css = urllib.request.urlopen(url).read().decode()
        src = re.findall(r'url\((https://[^)]+)\)', css)[0]
    except Exception as e:
        print(f'skip {fam}: {e}')
        continue
    dst = os.path.join(HERE, 'fonts', fam.replace(' ', '_') + '.ttf')
    with open(dst, 'wb') as f:
        f.write(urllib.request.urlopen(src).read())
    print('ok', fam)
