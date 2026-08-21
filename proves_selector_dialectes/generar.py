# -*- coding: utf-8 -*-
"""
Fa les pàgines de prova a partir de l'index.html de debò.

No són copies fetes a mà a posta: si l'index.html canvia, es torna a passar
aquest script i les proves tornen a ser el lloc de veritat amb el selector a
sobre. L'única cosa que hi canvia és el mínim imprescindible:

  - les rutes, que ara pengen d'una carpeta més endins;
  - el que no ha de ser mai a una pàgina de proves (canonical, sitemap,
    dades estructurades, og:) i el noindex, que és el que fa que el
    "Regenerar el sitemap.xml" de deploy.yml la deixi fora;
  - el data-prova del <body>, que és el que fa sortir la cinta del comparador;
  - i dues línies de <link>/<script>: la prova i el que comparteixen totes.

Fixeu-vos que NO hi ha cap marca del selector a l'HTML. Cada prova-X.js
l'injecta al DOM que ja hi ha, tal com faria el js/components.js el dia que
això sigui de debò: així es veu de seguida on aniria a parar el codi bo.
"""

import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
ARREL = os.path.dirname(AQUI)

PROVES = [
    ('a', 'Desplegable natiu a la capçalera'),
    ('b', 'Bombolla amb menú a la capçalera'),
    ('c', 'A la franja rosa, a la dreta'),
    ('d', 'Barra pròpia sota la capçalera'),
    ('e', 'Pastilles (sense desplegable)'),
    ('f', 'Bombolla flotant amb panell'),
]


def transformar(html, lletra, titol):
    # Fora tot el que parla amb els cercadors: aquestes pàgines no s'indexen.
    html = html.replace(
        '<meta name="robots" content="index, follow">',
        '<meta name="robots" content="noindex, nofollow">')
    html = re.sub(r'\n *<link rel="canonical"[^>]*>', '', html)
    html = re.sub(r'\n *<meta property="og:[^>]*>', '', html)
    html = re.sub(r'\n *<meta name="twitter:[^>]*>', '', html)
    html = re.sub(r'\n *<!--\n        Dades estructurades.*?</script>', '', html, flags=re.S)

    html = html.replace(
        '<title>Rimador.cat</title>',
        '<title>Prova %s · %s</title>' % (lletra.upper(), titol))
    html = re.sub(r'<meta name="description"[^>]*>',
                  '<meta name="description" content="Prova de disseny del selector de dialecte.">',
                  html)

    # Una carpeta endins. El JS no cal tocar-lo: l'ARREL de js/components.js
    # se la calcula a partir del src d'aquell mateix <script>.
    for ruta in ('assets/', 'dist/css/', 'dist/js/', 'avis/'):
        html = html.replace('"%s' % ruta, '"../%s' % ruta)

    html = html.replace('<body id="principal">',
                        '<body id="principal" data-prova="%s">' % lletra)

    # Darrere de tot el que ja hi ha: el comu.js fa servir el <body> i cada
    # prova-X.js fa servir el DOM que hi deixa el components.js. Amb defer,
    # l'ordre d'execució és l'ordre en què surten aquí.
    html = html.replace(
        '</head>',
        '\n    <!-- La prova de selector de dialecte. Res d\'això no és al lloc de debò. -->\n'
        '    <link rel="stylesheet" href="comu.css">\n'
        '    <link rel="stylesheet" href="prova-%s.css">\n'
        '    <script src="comu.js" defer></script>\n'
        '    <script src="prova-%s.js" defer></script>\n'
        '</head>' % (lletra, lletra))

    return html


def main():
    with open(os.path.join(ARREL, 'index.html'), encoding='utf-8') as f:
        original = f.read()

    for lletra, titol in PROVES:
        desti = os.path.join(AQUI, 'prova-%s.html' % lletra)
        with open(desti, 'w', encoding='utf-8') as f:
            f.write(transformar(original, lletra, titol))
        print('prova-%s.html  %s' % (lletra, titol))


if __name__ == '__main__':
    main()
