"""El programador manual de tuits: serveix la pàgina i toca els publicades_*.json.

Per què existeix: abans dos bots penjaven un tuit al dia tots sols amb l'API
de Twitter, que val diners; la web de X deixa programar tuits de franc. Això
genera els mateixos tuits que dirien ells, te'ls dona d'un en un perquè els
enganxis i els programis allà, i només apunta la rima a publicades_*.json quan
tu confirmes que ja està programada. Així la rima no es crema si al final no la
publiques.

QUÈ HI HA A CADA LOT: una rima i una paraula nàufraga de cada dialecte, en
l'ordre de generador.dialectes() —central, nord-occidental, valencià i balear—,
o sigui vuit tuits, un per dia. No es tria: el lot és tots els dialectes o no
és res, que per això s'ha fet. Si un dia n'hi ha cinc, el lot en tindrà deu tot
sol. Si un tuit concret no fa el pes, el "Un altre" en dona un altre a l'atzar
i el cercador deixa triar, escrivint-hi una paraula, què ha de dir aquell dia.

Com s'engega:

    python3 bot/programador/servidor.py

(o doble clic a bot/programador/programador.command). S'obre el navegador tot
sol. Per aturar-ho: Ctrl+C.

Si n'hi ha un que ja corre amb el MATEIX codi, aquest no s'engega (no hi
guanyaries res). Quan el que ha canviat són les dades i no pas el codi, no ho
pot saber i cal dir-li que el faci fora:

    python3 bot/programador/servidor.py reengega

Per què un servidor i no pas un HTML i prou: un fitxer obert amb file:// no pot
ni llegir els JSON del costat (el navegador ho barra) ni desar res al disc. Amb
això, els fitxers els llegeix i els escriu el Python, i el navegador només fa
d'interfície. És tot de la biblioteca estàndard: no cal instal·lar res.

La pàgina NO s'ha de publicar mai a Pages: només té sentit amb aquest servidor
al darrere. Per això el deploy.yml esborra bot/programador/ del paquet abans de
pujar-lo (vegeu-hi el pas "Aprimar el paquet abans de publicar").
"""

import hashlib
import json
import os
import random
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIR_BOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, DIR_BOT)

import generador_tuits as generador  # noqa: E402  (cal el sys.path de sobre)

PAGINA = os.path.join(BASE_DIR, 'programador.html')
PORT_PER_DEFECTE = 8765
# Quants ports es miren a partir del de per defecte, tant per veure si ja hi ha
# cap programador engegat com per buscar-ne un de lliure.
PORTS_A_MIRAR = 20

# Com es fa conèixer a la capçalera Server, amb l'empremta del codi al darrere:
# "ProgramadorDeTuits/6f2a1c9b04e7". Serveix per a dues coses alhora quan
# s'engega: saber si el que ja corre en un port és un dels nostres (i no pas
# qualsevol altre servidor de proves) i si duu el mateix codi que hi ha al disc
# o un de vell.
NOM_DEL_SERVIDOR = 'ProgramadorDeTuits'


def empremta_del_codi():
    """Un resum del codi que es carrega en engegar.

    Els DOS mòduls de Python i prou: el programador.html es torna a llegir a
    cada petició i canviar-lo no demana reengegar res. Es mira el contingut i
    no pas la data del fitxer perquè el Dropbox toca les dates sense que el
    codi hagi canviat, i llavors es reengegaria per no res.
    """
    resum = hashlib.sha256()

    for ruta in (os.path.abspath(__file__), os.path.abspath(generador.__file__)):
        try:
            with open(ruta, 'rb') as f:
                resum.update(f.read())
        except OSError:
            return ''

    return resum.hexdigest()[:12]


EMPREMTA = empremta_del_codi()

# Un pany per a les escriptures: el navegador pot engegar dues peticions
# alhora (dos clics seguits) i les dues llegeixen, afegeixen i desen el mateix
# fitxer. Sense això, la segona podria desar-se damunt de la primera i perdre
# una rima acabada d'apuntar.
PANY = threading.Lock()

FITXERS_PUBLICADES = {
    'normal': generador.FITXER_PUBLICADES_NORMAL,
    'naufragues': generador.FITXER_PUBLICADES_NAUFRAGUES,
}

# L'ordre en què es van dient: la rima d'un dialecte, l'endemà la seva paraula
# nàufraga, i al cap de dos dies el dialecte següent.
TIPUS_PER_DIALECTE = ('normal', 'naufragues')

# Quants en surten com a molt, del cercador. Prou per triar i prou pocs per
# llegir-los d'un cop d'ull.
MAXIM_RESULTATS = 12

# Menys de dues lletres no és una cerca: sortiria mig diccionari.
MINIM_A_CERCAR = 2


class Dades:
    """Les dades grosses, carregades un sol cop.

    Aplegar les rimes de les columnes del diccionari costa mig segon per
    dialecte: fer-ho a cada petició deixaria la pàgina inservible. Com que no
    canvien mentre el servidor corre, es queden a la memòria. Els
    publicades_*.json, en canvi, es rellegeixen sempre del disc: són petits i
    poden haver canviat per fora (un git pull, posem).

    CADA DIALECTE TÉ LA SEVA LLISTA DE PARAULES: el diccionari, que és igual
    per a tothom, i les seves paraules pròpies ("cante", "servisc", "tenc").
    Per això paraules, planes, noms_propis i rimes van indexats pel dialecte.

    El tros del diccionari es llegeix i s'aplana UNA sola vegada i les quatre
    llistes el comparteixen: així les cadenes són les mateixes en comptes de
    tenir-ne quatre còpies, que és la diferència entre 90 MB i 240 MB.
    """

    def __init__(self):
        self.dialectes = generador.dialectes()
        noms = ', '.join(generador.nom_dialecte(dialecte) for dialecte in self.dialectes)
        print(f'Aplegant les rimes de les columnes del diccionari ({noms})...')

        # El tros compartit, un sol cop: les paraules i les mateixes aplanades
        # per al cercador (sense això, cada tecla aplanaria les 620.000 una
        # altra vegada).
        self.paraules_base = generador.carregar_paraules_del_diccionari()
        planes_base = generador.aplanar_paraules(self.paraules_base)
        del_diccionari = len(self.paraules_base)

        self.paraules = {}
        self.planes = {}
        self.noms_propis = {}
        for dialecte in self.dialectes:
            seves = generador.carregar_paraules(dialecte, self.paraules_base)
            self.paraules[dialecte] = seves
            # El tros del diccionari ja està aplanat i es comparteix; només cal
            # aplanar les paraules pròpies d'aquest dialecte.
            self.planes[dialecte] = planes_base + generador.aplanar_paraules(
                seves[del_diccionari:])
            # Les formes que només són nom propi: no surten a la llista de cap
            # rima si hi ha res més (vegeu paraules_del_tuit()).
            self.noms_propis[dialecte] = generador.carregar_noms_propis(dialecte, seves)

        # De la fila a la rima (per al cercador) i de la rima a les paraules
        # (per al tuit). Es llegeix la columna un sol cop i surten les dues.
        self.columna_rima = {dialecte: generador.carregar_columna_rima(dialecte)
                             for dialecte in self.dialectes}
        self.rimes = {dialecte: generador.carregar_rimes(dialecte,
                                                         self.paraules[dialecte],
                                                         self.columna_rima[dialecte])
                      for dialecte in self.dialectes}
        self.naufragues = {dialecte: generador.carregar_naufragues(dialecte)
                           for dialecte in self.dialectes}

        # Les rimes que són d'una nàufraga: el tuit de la rima no les ha de dir
        # mai (diria "hi rima una paraula" d'una que no rima amb res), i per
        # això queden fora sempre, s'hagin publicat o no.
        self.rimes_naufragues = {dialecte: generador.rimes_de_naufragues(items)
                                 for dialecte, items in self.naufragues.items()}

        # En quins dialectes és nàufraga cada paraula: és el que diu el tuit.
        self.dialectes_de_naufraga = generador.dialectes_de_cada_naufraga(self.naufragues)

        for dialecte in self.dialectes:
            diuen = generador.naufragues_disponibles(self.naufragues[dialecte], set())
            propies = len(self.paraules[dialecte]) - del_diccionari
            print(f'  {generador.nom_dialecte(dialecte)}: {len(self.rimes[dialecte])} rimes'
                  f' i {len(diuen)} paraules nàufragues'
                  f' ({len(self.rimes_naufragues[dialecte]) - len(diuen)} noms propis fora)'
                  f'{f", {propies} paraules pròpies" if propies else ""}.')

        if not self.dialectes:
            print(f'AVÍS: no s\'ha trobat cap dialecte a {generador.DIR_DIALECTES}.')
        if not self.paraules_base:
            print(f'AVÍS: no s\'ha trobat {generador.FITXER_PARAULES}.')
        for dialecte in self.dialectes:
            if not self.rimes[dialecte]:
                print(f'AVÍS: no s\'han trobat les columnes de {generador.nom_dialecte(dialecte)}:')
                print(f'      {generador.FITXER_PARAULES}')
                print(f'      {generador.fitxer_rimacons(dialecte)}')
            if not self.naufragues[dialecte]:
                print(f'AVÍS: no s\'ha trobat {generador.fitxer_naufragues(dialecte)}.')
                print('      El genera llistes/generar_naufragues.py.')


# El servidor l'omple a principal(): llegir mig diccionari no s'ha de fer
# només per importar el mòdul.
DADES = None


def publicades(tipus):
    return generador.carregar_json(FITXERS_PUBLICADES[tipus], [])


def fora_de_rimes(pub_normal, dialecte):
    """Les rimes d'un dialecte que no es poden dir: les dites i les nàufragues."""
    return generador.rimes_publicades(pub_normal, dialecte) | DADES.rimes_naufragues[dialecte]


def estat():
    """Quantes en queden a cada dialecte i quines ja s'han dit."""
    pub_normal = publicades('normal')
    pub_naufragues = publicades('naufragues')
    dites = set(pub_naufragues)

    return {
        # Amb quin codi s'ha fet. La pàgina hi marca el lot que desa al
        # navegador i així pot avisar que el que veus a la pantalla el va donar
        # un servidor d'abans (vegeu avisarSiElLotEsVell() al programador.html).
        'empremta': EMPREMTA,
        'dialectes': [{'codi': dialecte, 'nom': generador.nom_dialecte(dialecte)}
                      for dialecte in DADES.dialectes],
        'tuits_per_lot': len(DADES.dialectes) * len(TIPUS_PER_DIALECTE),
        'normal': {
            'publicades': pub_normal,
            'disponibles': {
                dialecte: len(generador.rimes_disponibles(DADES.rimes[dialecte],
                                                          fora_de_rimes(pub_normal, dialecte)))
                for dialecte in DADES.dialectes
            },
            'fitxer': os.path.relpath(FITXERS_PUBLICADES['normal'], os.path.dirname(DIR_BOT)),
        },
        'naufragues': {
            'publicades': pub_naufragues,
            # Per paraula, no per entrada: les homògrafes ("boga" el peix i
            # "boga" del verb bogar) hi són una vegada per categoria gramatical
            # i són el mateix tuit. El que es compta és el que encara es pot dir.
            'disponibles': {
                dialecte: len(generador.naufragues_disponibles(DADES.naufragues[dialecte], dites))
                for dialecte in DADES.dialectes
            },
            'fitxer': os.path.relpath(FITXERS_PUBLICADES['naufragues'], os.path.dirname(DIR_BOT)),
        },
    }


def tuit_de_rima(dialecte, rima, data):
    """La targeta d'un tuit de rima concret, o None si aquella rima no hi és."""
    paraules = DADES.rimes.get(dialecte, {}).get(rima)
    if not paraules:
        return None

    return {
        'tipus': 'normal',
        'dialecte': dialecte,
        'nom_dialecte': generador.nom_dialecte(dialecte),
        'clau': generador.clau_de_rima(dialecte, rima),
        'etiqueta': f'/{rima}/',
        'detall': f'{generador.quantes_hi_rimen(paraules)} paraules hi rimen',
        # Si la rima té més paraules de les que hi caben, refer els exemples en
        # dona uns altres; si no, en sortirien sempre els mateixos i el botó
        # només enganyaria.
        'altres_exemples': generador.quantes_hi_rimen(paraules) > generador.PARAULES_PER_TUIT,
        'data': data,
        'text': generador.tuit_normal(rima, paraules, dialecte, data,
                                      DADES.noms_propis.get(dialecte, set())),
    }


def tuit_de_naufraga(dialecte, paraula, data, items=None):
    """La targeta d'una nàufraga concreta, o None si en aquell dialecte no ho és.

    `items` són les entrades d'aquella paraula si qui ho crida ja les té a mà
    (el lot i el cercador les acaben de trobar); si no, es busquen.
    """
    if items is None:
        items = generador.naufragues_disponibles(DADES.naufragues.get(dialecte, []),
                                                 set()).get(paraula)
    if not items:
        return None

    # Quina de les entrades de la paraula, a l'atzar: canvia el lema, i per
    # tant a quin diccionari va l'enllaç.
    item = random.choice(items)
    dialectes_naufraga = DADES.dialectes_de_naufraga.get(paraula, [dialecte])

    return {
        'tipus': 'naufragues',
        'dialecte': dialecte,
        'nom_dialecte': generador.nom_dialecte(dialecte),
        'clau': paraula,
        'etiqueta': paraula,
        'detall': f"/{item.get('rimacons')}/ · nàufraga en {len(dialectes_naufraga)}"
                  f" de {len(DADES.dialectes)} dialectes",
        'data': data,
        'text': generador.tuit_naufraga(item, dialecte, dialectes_naufraga,
                                        DADES.dialectes, data),
    }


def un_tuit(tipus, dialecte, data, fora):
    """Un tuit a l'atzar d'un tipus i d'un dialecte, o None si ja no en queda cap.

    `fora` són les que no es poden dir: per a les rimes, rimes d'aquest
    dialecte; per a les nàufragues, paraules (que la mateixa paraula pot ser
    nàufraga a més d'un dialecte i el tuit ja ho diu, o sigui que dir-la un cop
    la crema a tots).
    """
    if tipus == 'normal':
        candidates = generador.rimes_disponibles(DADES.rimes[dialecte], fora)
        return tuit_de_rima(dialecte, random.choice(candidates), data) if candidates else None

    per_paraula = generador.naufragues_disponibles(DADES.naufragues[dialecte], fora)
    if not per_paraula:
        return None

    paraula = random.choice(list(per_paraula))
    return tuit_de_naufraga(dialecte, paraula, data, per_paraula[paraula])


def generar(data_inici):
    """El lot sencer: una rima i una nàufraga de cada dialecte. No toca cap fitxer.

    Sempre un tuit per dia i en aquest ordre: la rima d'un dialecte, l'endemà
    la seva paraula nàufraga, i el dia següent la rima del dialecte que ve. No
    es tria: és el ritme del compte, i triar-lo només servia per fer lots que
    no es podien programar tal com sortien.

    Encara no s'ha dit res: els publicades_*.json només es toquen quan es
    confirma tuit per tuit.
    """
    try:
        dia = datetime.strptime(data_inici, '%Y-%m-%d')
    except (TypeError, ValueError):
        dia = datetime.now()

    pub_normal = publicades('normal')
    dites = set(publicades('naufragues'))
    # Dins d'un mateix lot tampoc no es repeteix la rima d'un dialecte a
    # l'altre: /ana/ en central i /ana/ en valencià són dues rimes diferents
    # de debò, però dos tuits seguits que en diuen la mateixa fan de mal llegir.
    rimes_del_lot = set()
    tuits = []

    for numero, dialecte in enumerate(DADES.dialectes):
        for ordre, tipus in enumerate(TIPUS_PER_DIALECTE):
            # El dia surt del LLOC que ocupa i no pas de quants n'han sortit:
            # si d'un dialecte se n'ha quedat sense, els altres no s'han
            # d'endarrerir un dia.
            dies = numero * len(TIPUS_PER_DIALECTE) + ordre
            data = generador.data_curta(dia + timedelta(days=dies))

            if tipus == 'normal':
                fora = fora_de_rimes(pub_normal, dialecte) | rimes_del_lot
            else:
                fora = dites

            tuit = un_tuit(tipus, dialecte, data, fora)
            if not tuit:
                continue

            if tipus == 'normal':
                rimes_del_lot.add(generador.rima_de_clau(tuit['clau']))
            else:
                dites.add(tuit['clau'])

            tuits.append(tuit)

    return tuits


def netejar_data(data):
    """La data que ve del navegador, ja escrita ("5/9/26"), tal com surt al tuit."""
    if not isinstance(data, str) or not data.strip():
        return generador.data_curta()
    return data.strip()[:16]


def un_altre(tipus, dialecte, data, exclou):
    """Un tuit per canviar-ne un del lot: el mateix tipus, el mateix dialecte i el mateix dia.

    `exclou` són les claus que ja hi ha a la pantalla, la del tuit que se
    substitueix inclosa: el que en surti ha de ser un de nou.
    """
    return un_tuit(tipus, dialecte, netejar_data(data), fora_del_lot(tipus, dialecte, exclou))


def fora_del_lot(tipus, dialecte, exclou):
    """El que no es pot dir: el ja publicat i el que ja és a la pantalla."""
    exclou = {clau for clau in (exclou or []) if isinstance(clau, str)}

    if tipus == 'normal':
        return (fora_de_rimes(publicades('normal'), dialecte)
                | {generador.rima_de_clau(clau) for clau in exclou})

    return set(publicades('naufragues')) | exclou


def triat(tipus, dialecte, clau, data):
    """El tuit que s'ha triat al cercador, per al dia que ocupava aquell lloc."""
    data = netejar_data(data)

    if tipus == 'normal':
        return tuit_de_rima(dialecte, generador.rima_de_clau(clau), data)

    return tuit_de_naufraga(dialecte, clau, data)


def cercar(tipus, dialecte, text, exclou):
    """Quines rimes o quines nàufragues d'aquest dialecte casen amb una paraula.

    Es cerquen PARAULES i prou: de les rimes, una que hi rimi ("casa" dona
    /azə/); de les nàufragues, la paraula. La rima en AFI no s'hi busca
    —s'havia pogut— perquè qui programa els tuits sap quina paraula vol dir
    aquell dia i no pas com se'n diu la rima, i buscar-hi les dues coses
    omplia la llista de rimes que no hi tenien res a veure.

    Els accents no compten (vegeu aplanar()): "porfir" troba "pòrfir" i
    "agalloc", "agàl·loc".

    El que ja s'ha dit i el que ja és a la pantalla no hi surt: si sortís,
    triar-ho deixaria el lot amb dos tuits que diuen el mateix.
    """
    cru = str(text or '').strip().lower()
    text = generador.aplanar(cru)
    if len(text) < MINIM_A_CERCAR:
        return []

    fora = fora_del_lot(tipus, dialecte, exclou)
    trobats = []

    if tipus == 'normal':
        # Una sola passada per les files del diccionari, no pas rima per rima:
        # el que es busca és una paraula, i de la fila se'n va a la rima per la
        # columna. Amb les paraules ja aplanades (DADES.planes) la comprovació
        # de cada fila és un "in" i prou, i la cerca costa una dècima de segon.
        millors = {}

        propis = DADES.noms_propis.get(dialecte, set())
        for paraula, plana, rima in zip(DADES.paraules.get(dialecte, []),
                                        DADES.planes.get(dialecte, []),
                                        DADES.columna_rima.get(dialecte, [])):
            if text not in plana or not rima or rima in fora:
                continue

            # Com casa, de millor a pitjor: la paraula tal com s'ha escrit
            # ("casa" i "casà" s'aplanen igual, i qui escriu "casa" vol la
            # casa), la paraula sense accents, una que comenci igual i una que
            # el dugui pel mig. A igualtat, la que NO és nom propi: als tuits
            # els noms propis no hi surten, i ensenyar "Sol" per la rima /ɔl/
            # seria ensenyar una paraula que després no hi serà.
            if plana == text:
                pes = 0 if paraula.lower() == cru else 1
            elif plana.startswith(text):
                pes = 2
            else:
                pes = 3
            pes = (pes, paraula in propis)

            # D'una rima, la paraula que hi casa millor: és la que es mostra
            # perquè es reconegui de què va una rima escrita en AFI.
            anterior = millors.get(rima)
            if anterior is None or pes < anterior[0]:
                millors[rima] = (pes, paraula)

        for rima, (pes, mostra) in millors.items():
            # Al davant la PARAULA i no pas la rima: és el que s'ha escrit al
            # cercador, el que es llegeix per saber de què va una rima en AFI i
            # el que ordena la llista.
            trobats.append((pes, rima, {
                'clau': generador.clau_de_rima(dialecte, rima),
                'etiqueta': mostra,
                'detall': f'/{rima}/ · {generador.quantes_hi_rimen(DADES.rimes[dialecte][rima])}'
                          f' paraules hi rimen',
            }))
    else:
        per_paraula = generador.naufragues_disponibles(DADES.naufragues.get(dialecte, []), fora)

        for paraula, items in per_paraula.items():
            plana = generador.aplanar(paraula)
            if plana == text:
                pes = 0
            elif plana.startswith(text):
                pes = 1
            elif text in plana:
                pes = 2
            else:
                continue

            dialectes_naufraga = DADES.dialectes_de_naufraga.get(paraula, [dialecte])
            trobats.append((pes, paraula, {
                'clau': paraula,
                'etiqueta': paraula,
                'detall': f"/{items[0].get('rimacons')}/ · nàufraga en"
                          f" {len(dialectes_naufraga)} de {len(DADES.dialectes)} dialectes",
            }))

    # Es TRIEN pels que hi casen millor i es MOSTREN per ordre alfabètic. Les
    # dues coses per separat a posta: ordenant alfabèticament abans de tallar a
    # dotze, la paraula que s'ha escrit es podria quedar fora (busca "sol" i
    # "absolut" li passaria al davant).
    trobats.sort(key=lambda trobat: (trobat[0], trobat[1]))
    millors = trobats[:MAXIM_RESULTATS]

    # Per ordre alfabètic de la paraula, amb la "c" i la "C" juntes i els
    # accents on toca (vegeu aplanar()): "Càndia" va entre "canco" i "candir",
    # no pas al capdavant de tot per ser majúscula. La rima desempata, que dues
    # paraules es poden aplanar igual.
    millors.sort(key=lambda trobat: (generador.aplanar(trobat[2]['etiqueta']), trobat[1]))

    return [resultat for _, _, resultat in millors]


def marcar(tipus, clau, programat):
    """Apunta (o desapunta) un tuit al publicades_*.json corresponent."""
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
    server_version = f'{NOM_DEL_SERVIDOR}/{EMPREMTA}'

    def do_GET(self):
        cami = self.path.split('?')[0]

        if cami in ('/', '/index.html', '/programador.html'):
            # Es llegeix a cada petició a posta: així es pot retocar l'HTML i
            # veure-ho amb un F5, sense reengegar el servidor (que vol dir
            # tornar a empassar-se les rimes dels quatre dialectes).
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

        try:
            if cami == '/api/generar':
                return self.respondre_json({
                    'tuits': generar(peticio.get('data')),
                    'estat': estat(),
                })

            tipus = peticio.get('tipus')
            if tipus not in FITXERS_PUBLICADES:
                return self.respondre_error(400, f'Tipus desconegut: {tipus}')

            if cami in ('/api/un_altre', '/api/cercar', '/api/tria'):
                dialecte = peticio.get('dialecte')
                if dialecte not in DADES.dialectes:
                    return self.respondre_error(400, f'Dialecte desconegut: {dialecte}')

                if cami == '/api/cercar':
                    # Cercar no canvia res: no cal tornar l'estat.
                    return self.respondre_json({
                        'resultats': cercar(tipus, dialecte, peticio.get('text'),
                                            peticio.get('exclou')),
                    })

                if cami == '/api/tria':
                    clau = peticio.get('clau')
                    if not clau:
                        return self.respondre_error(400, 'Falta la clau del tuit triat')
                    return self.respondre_json({
                        'tuit': triat(tipus, dialecte, clau, peticio.get('data')),
                        'estat': estat(),
                    })

                return self.respondre_json({
                    'tuit': un_altre(tipus, dialecte, peticio.get('data'), peticio.get('exclou')),
                    'estat': estat(),
                })

            if cami in ('/api/programat', '/api/desfes'):
                clau = peticio.get('clau')
                if not clau:
                    return self.respondre_error(400, 'Falta la clau del tuit')
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


def port_ocupat(port):
    with socket.socket() as s:
        s.settimeout(0.2)
        return s.connect_ex(('127.0.0.1', port)) == 0


def quin_programador(port):
    """Quina empremta de codi duu el programador que hi ha en aquest port.

    Es pregunta amb una petició de debò i no pas mirant si el port està ocupat
    i prou: hi pot haver qualsevol altre servidor de proves, i d'aquell sí que
    val la pena apartar-se en comptes de tocar-lo. Qui identifica el nostre és
    la capçalera Server, que és el server_version de la classe Mans.

    Torna None si allà no hi ha cap programador nostre, i '' si n'hi ha un de
    tan vell que encara no deia quin codi duia (els d'abans d'aquest canvi).
    Aquests darrers també compten com a vells, que és el que són.
    """
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/estat', timeout=0.5) as resposta:
            capçalera = resposta.headers.get('Server', '')
    except urllib.error.HTTPError as error:
        capçalera = error.headers.get('Server', '')
    except Exception:
        return None

    if not capçalera.startswith(NOM_DEL_SERVIDOR):
        return None

    return capçalera.split()[0].partition('/')[2]


def programadors_engegats(a_mes=None):
    """[(port, empremta)] dels programadors que ja corren.

    `a_mes` és el port que s'ha demanat a mà, per si cau fora dels que es
    miren: engegar-ne un damunt d'un altre no ha de petar amb un OSError.
    """
    ports = set(range(PORT_PER_DEFECTE, PORT_PER_DEFECTE + PORTS_A_MIRAR))
    if a_mes is not None:
        ports.add(a_mes)

    trobats = []
    for port in sorted(ports):
        if not port_ocupat(port):
            continue
        empremta = quin_programador(port)
        if empremta is not None:
            trobats.append((port, empremta))

    return trobats


def pid_del_port(port):
    """Quin procés escolta en aquest port, o None.

    El Python de sèrie no sap anar del port al procés i el psutil no és de
    sèrie; l'lsof hi és a qualsevol macOS.
    """
    try:
        sortida = subprocess.run(['lsof', '-nP', f'-iTCP:{port}', '-sTCP:LISTEN', '-t'],
                                 capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None

    pids = [int(linia) for linia in sortida.stdout.split() if linia.strip().isdigit()]

    return pids[0] if pids else None


def es_un_servidor_nostre(pid):
    """Que el procés que anem a matar sigui de debò un servidor.py.

    Entre preguntar al port i enviar el senyal hi ha una escletxa on aquell
    procés pot haver mort i un altre haver-li agafat el port. És barat de
    comprovar i el senyal no es pot desfer.
    """
    try:
        sortida = subprocess.run(['ps', '-o', 'command=', '-p', str(pid)],
                                 capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return False

    return 'servidor.py' in sortida.stdout


def esperar_que_deixi_el_port(port, segons):
    for _ in range(int(segons * 10)):
        if not port_ocupat(port):
            return True
        time.sleep(0.1)

    return not port_ocupat(port)


def aturar_programador(port):
    """Atura el programador que hi ha en aquest port. Diu si se n'ha sortit.

    No s'hi perd res, aturant-ne un: els publicades_*.json s'escriuen a
    l'instant a cada confirmació i el lot de la pantalla és al navegador.
    """
    pid = pid_del_port(port)
    if pid is None or pid == os.getpid() or not es_un_servidor_nostre(pid):
        return False

    for senyal, espera in ((signal.SIGTERM, 3), (signal.SIGKILL, 2)):
        try:
            os.kill(pid, senyal)
        except OSError:
            return not port_ocupat(port)
        if esperar_que_deixi_el_port(port, espera):
            return True

    return False


def port_lliure(preferit):
    """El primer port lliure a partir del que es vol."""
    for port in range(preferit, preferit + PORTS_A_MIRAR):
        if not port_ocupat(port):
            return port
    return preferit


def avisar_dels_engegats(ports, aturar_se):
    """Diu quins programadors amb AQUEST mateix codi ja corren.

    Els de codi vell no arriben fins aquí: aquells es tanquen (vegeu
    principal()). Els que queden duen el mateix que hi ha al disc, i engegar-ne
    un altre només serviria per tenir dos ports que diuen el mateix i no saber
    en quin ets.
    """
    quants = 'un programador de tuits engegat' if len(ports) == 1 \
             else f'{len(ports)} programadors de tuits engegats'
    print()
    print(f'  Ja hi ha {quants} amb aquest mateix codi:')
    for port in ports:
        print(f'    http://localhost:{port}/')
    print()

    if not aturar_se:
        return

    print('  Aquest no s\'engega: no hi guanyaries res. Obre l\'adreça de dalt.')
    print()
    print('  (Si el codi hagués canviat, aquest l\'hauria aturat i s\'hauria posat')
    print('  al seu lloc tot sol. Recorda que l\'HTML es rellegeix a cada F5 i')
    print('  que el lot que veus a la pantalla no es refà fins que no premis')
    print('  "Genera el lot".)')
    print()
    print('  Si el que has refet són les DADES (el diccionari, les columnes de')
    print('  rima, les nàufragues), el codi és el mateix i aquest no se n\'adona:')
    print('  el que corre les va carregar en engegar i les té d\'abans. Fes-lo fora:')
    print('    python3 bot/programador/servidor.py reengega')
    print()
    print('  Per aturar-los a mà: Ctrl+C a la seva finestra, o des d\'aquí:')
    print('    pkill -f servidor.py')
    print()
    print(f'  Si de debò en vols dos alhora, digues-li un port lliure:')
    print(f'    python3 bot/programador/servidor.py {PORT_PER_DEFECTE + PORTS_A_MIRAR}')
    print()


def apartar_els_vells(engegats, tots=False):
    """Tanca els programadors que duen codi d'abans. Diu si tot ha anat bé.

    És el que demana el sentit comú de treballar-hi: si has tocat el
    generador_tuits.py, el que corre des d'abans dona els tuits d'abans, i
    tenir-lo obert en un altre port només serveix per mirar la pantalla que no
    toca. Els que duen el MATEIX codi no es toquen, que no hi ha res a guanyar;
    amb `tots` (el «reengega») hi van també, que és l'única manera de fer que
    es rellegeixin unes dades refetes.
    """
    tot_be = True

    for port, empremta in engegats:
        si_mateix = empremta == EMPREMTA
        if si_mateix and not tots:
            continue

        if si_mateix:
            quin = 'aquest mateix codi'
        elif empremta:
            quin = f'el codi {empremta}'
        else:
            quin = 'codi d\'abans que es pogués saber quin'
        print(f'  Al port {port} hi ha un programador amb {quin}: l\'aturo.')

        if aturar_programador(port):
            print(f'    aturat.')
        else:
            tot_be = False
            print(f'    NO l\'he pogut aturar. Atura\'l tu i torna-ho a provar:')
            print(f'      pkill -f servidor.py')

    return tot_be


PARAULES_DE_REENGEGAR = ('reengega', '-r', '--reengega')


def llegir_arguments():
    """El port que es demana (o None) i si s'ha dit de reengegar.

    Reengegar és per quan el codi és el MATEIX i tot i així el que corre ja no
    serveix: les dades grosses (el diccionari, les columnes de rima, les
    nàufragues) es carreguen un sol cop en engegar i l'empremta no les mira,
    que llegir-les totes a cada arrencada per fer-ne el resum costaria més que
    no pas engegar. Si n'has refet cap, el que corre les té d'abans.
    """
    port = None
    reengegar = False

    for argument in sys.argv[1:]:
        if argument in PARAULES_DE_REENGEGAR:
            reengegar = True
        elif argument.isdigit():
            port = int(argument)
        else:
            print(f'No entenc l\'argument «{argument}».')
            print('  python3 bot/programador/servidor.py [port] [reengega]')
            sys.exit(2)

    return port, reengegar


def principal():
    global DADES

    # Mirar-ho ABANS de carregar les dades: adonar-se'n després seria fer
    # esperar sis segons per no engegar res.
    port_a_ma, reengegar = llegir_arguments()
    port_demanat = PORT_PER_DEFECTE if port_a_ma is None else port_a_ma
    ja_engegats = programadors_engegats(port_a_ma)

    # Primer, fora els que duen codi d'abans: aquests sí que sobren, i el port
    # que deixen lliure sol ser justament el que volem. Amb el reengega, fora
    # també els que duen aquest mateix codi.
    if not apartar_els_vells(ja_engegats, tots=reengegar):
        return

    # Els que queden duen el mateix codi que hi ha al disc (amb el reengega no
    # en queda cap: acaben de marxar tots).
    mateix_codi = [] if reengegar else \
        [port for port, empremta in ja_engegats if empremta == EMPREMTA]

    if mateix_codi:
        # Amb un port dit a mà, s'entén que ja se sap el que es fa i només
        # s'avisa; sense, val més aturar-se que no pas acumular-ne un altre. I
        # damunt d'un que ja corre no s'hi engega mai.
        aturar_se = port_a_ma is None or port_demanat in mateix_codi
        avisar_dels_engegats(mateix_codi, aturar_se)
        if aturar_se:
            return

    DADES = Dades()

    port = port_lliure(port_demanat)
    adreca = f'http://localhost:{port}/'

    # Només 127.0.0.1: això escriu al repositori i no ha de ser a l'abast de
    # ningú més de la xarxa.
    try:
        servidor = ThreadingHTTPServer(('127.0.0.1', port), Mans)
    except OSError as e:
        print(f'\n  No s\'ha pogut engegar al port {port}: {e}')
        print(f'  Prova-ho amb un altre: python3 bot/programador/servidor.py <port>\n')
        return

    print()
    if port != port_demanat:
        print(f'  El port {port_demanat} estava ocupat per una altra cosa.')
    print(f'  El programador de tuits és a {adreca}')
    print('  Per aturar-lo: Ctrl+C (i espera que digui "Apa, adeu").')
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
