"""El programador manual de tuits: serveix la pàgina i toca els publicades_*.json.

Per què existeix: abans dos bots penjaven un tuit al dia tots sols amb l'API
de Twitter, que val diners; la web de X deixa programar tuits de franc. Això
genera els mateixos tuits que dirien ells, te'ls dona d'un en un perquè els
enganxis i els programis allà, i només apunta la rima a publicades_*.json quan
tu confirmes que ja està programada. Així la rima no es crema si al final no la
publiques.

Com s'engega:

    python3 bot/programador/servidor.py

(o doble clic a bot/programador/programador.command). S'obre el navegador tot
sol. Per aturar-ho: Ctrl+C.

Per què un servidor i no pas un HTML i prou: un fitxer obert amb file:// no pot
ni llegir els JSON del costat (el navegador ho barra) ni desar res al disc. Amb
això, els fitxers els llegeix i els escriu el Python, i el navegador només fa
d'interfície. És tot de la biblioteca estàndard: no cal instal·lar res.

La pàgina NO s'ha de publicar mai a Pages: només té sentit amb aquest servidor
al darrere. Per això el deploy.yml esborra bot/programador/ del paquet abans de
pujar-lo (vegeu-hi el pas "Aprimar el paquet abans de publicar").
"""

import json
import os
import random
import socket
import sys
import threading
import webbrowser
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_BOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, DIR_BOT)

import generador_tuits as generador  # noqa: E402  (cal el sys.path de sobre)

PAGINA = os.path.join(BASE_DIR, 'programador.html')
PORT_PER_DEFECTE = 8765
MAXIM_PER_LOT = 60

# Un pany per a les escriptures: el navegador pot engegar dues peticions
# alhora (dos clics seguits) i les dues llegeixen, afegeixen i desen el mateix
# fitxer. Sense això, la segona podria desar-se damunt de la primera i perdre
# una rima acabada d'apuntar.
PANY = threading.Lock()

FITXERS_PUBLICADES = {
    'normal': generador.FITXER_PUBLICADES_NORMAL,
    'naufragues': generador.FITXER_PUBLICADES_NAUFRAGUES,
}


class Dades:
    """Les dades grosses, carregades un sol cop.

    Aplegar les rimes de les columnes del diccionari costa un segon: fer-ho a
    cada petició deixaria la pàgina inservible. Com que no canvien mentre el
    servidor corre, es queden a la memòria. Els publicades_*.json, en canvi, es
    rellegeixen sempre del disc: són petits i poden haver canviat per fora (un
    git pull, posem).
    """

    def __init__(self):
        print('Aplegant les rimes de les columnes del diccionari...')
        self.rimes = generador.carregar_rimes()
        self.naufragues = generador.carregar_json(generador.FITXER_NAUFRAGUES, [])
        print(f'  {len(self.rimes)} rimes i {len(self.naufragues)} paraules nàufragues.')

        if not self.rimes:
            print(f'AVÍS: no s\'han trobat les columnes del diccionari:')
            print(f'      {generador.FITXER_PARAULES}')
            print(f'      {generador.FITXER_RIMACONS}')
        if not self.naufragues:
            print(f'AVÍS: no s\'ha trobat {generador.FITXER_NAUFRAGUES}.')
            print('      El genera llistes/generar_naufragues.py.')


# El servidor l'omple a principal(): llegir mig diccionari no s'ha de fer
# només per importar el mòdul.
DADES = None


def publicades(tipus):
    return generador.carregar_json(FITXERS_PUBLICADES[tipus], [])


def estat():
    """Quantes en queden i quines ja s'han dit, per als dos tipus de tuit."""
    pub_normal = publicades('normal')
    pub_naufragues = publicades('naufragues')

    return {
        'normal': {
            'publicades': pub_normal,
            'disponibles': len(generador.rimes_disponibles(DADES.rimes, pub_normal, DADES.naufragues)),
            'fitxer': os.path.relpath(FITXERS_PUBLICADES['normal'], os.path.dirname(DIR_BOT)),
        },
        'naufragues': {
            'publicades': pub_naufragues,
            # Per rima, no per paraula: dues nàufragues poden compartir rima
            # (rimen entre elles i amb res més), i el bot les descarta totes
            # dues alhora. El que es compta és el que encara es pot dir.
            'disponibles': len({item.get('rimacons')
                                for item in generador.naufragues_disponibles(DADES.naufragues, pub_naufragues)}),
            'fitxer': os.path.relpath(FITXERS_PUBLICADES['naufragues'], os.path.dirname(DIR_BOT)),
        },
    }


def generar(tipus, quantitat, data_inici, un_dia_per_tuit, exclou):
    """Un lot de tuits a punt de copiar. No toca cap fitxer: encara no s'ha dit res."""
    quantitat = max(1, min(MAXIM_PER_LOT, int(quantitat)))
    fora = set(publicades(tipus)) | set(exclou or [])

    try:
        dia = datetime.strptime(data_inici, '%Y-%m-%d')
    except (TypeError, ValueError):
        dia = datetime.now()

    tuits = []

    if tipus == 'normal':
        candidates = [r for r in generador.rimes_disponibles(DADES.rimes, fora, DADES.naufragues)]
        random.shuffle(candidates)

        for rima in candidates[:quantitat]:
            paraules = DADES.rimes[rima]
            data = generador.data_curta(dia + timedelta(days=len(tuits) if un_dia_per_tuit else 0))
            tuits.append({
                'clau': rima,
                'etiqueta': f'/{rima}/',
                'detall': f'{len(paraules)} paraules hi rimen',
                'data': data,
                'text': generador.tuit_normal(rima, paraules, data),
            })
    else:
        candidates = generador.naufragues_disponibles(DADES.naufragues, fora)
        random.shuffle(candidates)
        rimes_del_lot = set()

        for item in candidates:
            if len(tuits) >= quantitat:
                break
            rima = item.get('rimacons')
            # Dins d'un mateix lot, tampoc no es repeteix la rima: apuntar-ne
            # una crema totes les paraules que la comparteixen, i el segon tuit
            # quedaria contradit pel primer.
            if rima in rimes_del_lot:
                continue
            rimes_del_lot.add(rima)

            data = generador.data_curta(dia + timedelta(days=len(tuits) if un_dia_per_tuit else 0))
            tuits.append({
                'clau': rima,
                'etiqueta': item.get('paraula'),
                'detall': f'/{rima}/',
                'data': data,
                'text': generador.tuit_naufraga(item, data),
            })

    return tuits


def marcar(tipus, clau, programat):
    """Apunta (o desapunta) una rima al publicades_*.json corresponent."""
    fitxer = FITXERS_PUBLICADES[tipus]

    with PANY:
        llista = generador.carregar_json(fitxer, [])

        if programat and clau not in llista:
            llista.append(clau)
            generador.guardar_json(llista, fitxer)
            print(f'  ✓ {clau} apuntada a {os.path.basename(fitxer)} ({len(llista)} en total)')
        elif not programat and clau in llista:
            llista.remove(clau)
            generador.guardar_json(llista, fitxer)
            print(f'  ✗ {clau} tornada a treure de {os.path.basename(fitxer)} ({len(llista)} en total)')

    return estat()


class Mans(BaseHTTPRequestHandler):
    server_version = 'ProgramadorDeTuits'

    def do_GET(self):
        cami = self.path.split('?')[0]

        if cami in ('/', '/index.html', '/programador.html'):
            # Es llegeix a cada petició a posta: així es pot retocar l'HTML i
            # veure-ho amb un F5, sense reengegar el servidor (que vol dir
            # tornar a empassar-se els 17 MB de rimes).
            try:
                with open(PAGINA, 'rb') as f:
                    cos = f.read()
            except FileNotFoundError:
                return self.respondre_error(404, f'No es troba {PAGINA}')
            return self.respondre(cos, 'text/html; charset=utf-8')

        if cami == '/api/estat':
            return self.respondre_json(estat())

        return self.respondre_error(404, 'Això aquí no hi és')

    def do_POST(self):
        cami = self.path.split('?')[0]

        try:
            llargada = int(self.headers.get('Content-Length') or 0)
            peticio = json.loads(self.rfile.read(llargada) or b'{}')
        except (ValueError, json.JSONDecodeError):
            return self.respondre_error(400, 'La petició no és un JSON vàlid')

        tipus = peticio.get('tipus')
        if tipus not in FITXERS_PUBLICADES:
            return self.respondre_error(400, f'Tipus desconegut: {tipus}')

        try:
            if cami == '/api/generar':
                return self.respondre_json({
                    'tuits': generar(
                        tipus,
                        peticio.get('quantitat', 1),
                        peticio.get('data'),
                        bool(peticio.get('un_dia_per_tuit', True)),
                        peticio.get('exclou', []),
                    ),
                    'estat': estat(),
                })

            if cami in ('/api/programat', '/api/desfes'):
                clau = peticio.get('clau')
                if not clau:
                    return self.respondre_error(400, 'Falta la clau de la rima')
                return self.respondre_json(marcar(tipus, clau, cami == '/api/programat'))
        except Exception as e:  # que un error d'aquests no tombi el servidor
            print(f'ERROR a {cami}: {e}')
            return self.respondre_error(500, str(e))

        return self.respondre_error(404, 'Això aquí no hi és')

    def respondre(self, cos, tipus_contingut):
        self.send_response(200)
        self.send_header('Content-Type', tipus_contingut)
        self.send_header('Content-Length', str(len(cos)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(cos)

    def respondre_json(self, dades):
        self.respondre(json.dumps(dades, ensure_ascii=False).encode('utf-8'),
                       'application/json; charset=utf-8')

    def respondre_error(self, codi, missatge):
        cos = json.dumps({'error': missatge}, ensure_ascii=False).encode('utf-8')
        self.send_response(codi)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(cos)))
        self.end_headers()
        self.wfile.write(cos)

    def log_message(self, format, *args):
        pass  # el registre d'accessos només faria soroll: ja hi ha els avisos d'apuntar


def port_lliure(preferit):
    for port in range(preferit, preferit + 20):
        with socket.socket() as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return preferit


def principal():
    global DADES
    DADES = Dades()

    port = port_lliure(int(sys.argv[1]) if len(sys.argv) > 1 else PORT_PER_DEFECTE)
    adreca = f'http://localhost:{port}/'

    # Només 127.0.0.1: això escriu al repositori i no ha de ser a l'abast de
    # ningú més de la xarxa.
    servidor = ThreadingHTTPServer(('127.0.0.1', port), Mans)

    print()
    print(f'  El programador de tuits és a {adreca}')
    print('  Per aturar-lo: Ctrl+C.')
    print()

    threading.Timer(0.5, lambda: webbrowser.open(adreca)).start()

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print('\nApa, adeu.')
    finally:
        servidor.server_close()


if __name__ == '__main__':
    principal()
