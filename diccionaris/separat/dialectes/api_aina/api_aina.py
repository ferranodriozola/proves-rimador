# -*- coding: utf-8 -*-
"""
Transcripció fonètica multidialectal (API del Projecte Aina) amb:

  · CACHÉ REPRENIBLE  -> si peta a l'hora 99, en tornar a executar continua on era.
  · PETICIONS PER LOTS -> ~25 mots per petició en comptes d'1 (unes 25x més ràpid).
  · REGULADOR DE RITME -> pauses aleatòries + frenada automàtica si el servidor es queixa.
  · REINTENTS amb espera creixent i, si cal, mot a mot.
  · UNA PETICIÓ CADA COP -> el servidor barreja les respostes si en rep dues
    alhora, i llavors hi ha mots que reben la transcripció d'un altre.

Ús:
    python3 api_aina.py                      # perfil normal
    python3 api_aina.py --perfil discret     # més lent, menys visible (ordinador ràpid)
    python3 api_aina.py --dialectes Central,Balear
    python3 api_aina.py --entrada ../../col_1.txt
    python3 api_aina.py --estat              # només mostra quant queda i surt
    python3 api_aina.py --marge 500          # descarta més cua de caché en començar
    python3 api_aina.py --mostra 500         # comprova 500 mots per dialecte al final
    python3 api_aina.py --sense-comprova     # no passa comprova.py en acabar

En acabar es passa comprova.py tot sol: revisió interna dels fitxers i, si
--mostra no és 0, verificació contra l'API d'uns quants mots per dialecte.
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
import threading
import time
from collections import deque
from itertools import zip_longest

import requests

# ---------------------------------------------------------------- configuració

URL = ("https://projecte-aina-transcripcio-fonetica-catala.hf.space"
       "/gradio_api/call/get-results")

DIALECTES = ["Central", "Alguerès", "Rosellonès", "Balear", "Valencia", "Occidental"]

# Límits reals del servidor (vistos al codi font del space, app.py):
#   MAX_INPUT_TEXT_LEN = 325  -> text més llarg = avís i resposta buida
#   concurrency_limit  = 2    -> més de 2-3 peticions alhora només genera errors
MAX_CARACTERS_LOT = 300

# Quantes entrades de la cua de la caché es llencen en començar. El que es pot
# haver quedat a mig escriure és, com a molt, l'últim lot (~25 mots), perquè
# desa() fa flush+fsync lot a lot; 200 és vuit vegades això i només costa uns
# segons de tornar-los a demanar.
MARGE_SEGURETAT = 200

PERFILS = {
    # nom          fils  pausa entre peticions  peticions/minut  descans llarg
    # Sempre 1 fil, i no és negociable. Amb 2 o més, el servidor (que té
    # concurrency_limit=2) barreja les respostes de les peticions simultànies i
    # un 2% dels mots torna la transcripció d'un altre. A vegades es veu
    # ("rəstɾinʒˈen" surt com "ənsərkəɾˈa  rəstɾinʒˈen") i a vegades no es veu
    # gens ("conegudes" -> "insistiɾˈiəm", que és una transcripció perfecta...
    # d'un altre mot). Mesurat sobre 3.000 mots transcrits dues vegades:
    # 1 fil -> 0 discrepàncies; 3 fils -> 61 (2,03%).
    # I no perdem res: 1 fil fa 100 mots/s i 3 fils en fan 94, perquè cada lot
    # brut s'ha de repetir mot a mot.
    "rapid":    dict(fils=1, pausa=(0.05, 0.20), per_minut=0,   descans_cada=0,   descans=(0, 0)),
    "normal":   dict(fils=1, pausa=(0.15, 0.50), per_minut=150, descans_cada=600, descans=(20, 45)),
    "discret":  dict(fils=1, pausa=(0.40, 1.20), per_minut=90,  descans_cada=300, descans=(45, 120)),
    "paranoic": dict(fils=1, pausa=(1.50, 4.00), per_minut=40,  descans_cada=150, descans=(120, 300)),
}

NAVEGADORS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

# ------------------------------------------------------------------ regulador


class Regulador:
    """Controla el ritme global: pauses aleatòries, sostre de peticions per minut
    i frenada automàtica (AIMD) quan el servidor comença a fallar."""

    def __init__(self, perfil):
        self.pausa_min, self.pausa_max = perfil["pausa"]
        self.per_minut = perfil["per_minut"]
        self.descans_cada = perfil["descans_cada"]
        self.descans = perfil["descans"]
        self.factor = 1.0            # multiplicador de frenada
        self.peticions = 0
        self.demanats_sols = 0       # mots reenviats d'un en un pel sedàs
        self.finestra = deque()      # marques de temps de l'últim minut
        self.pany = threading.Lock()

    def abans_de_peticio(self):
        with self.pany:
            ara = time.time()
            # sostre de peticions per minut
            if self.per_minut:
                while self.finestra and ara - self.finestra[0] > 60:
                    self.finestra.popleft()
                if len(self.finestra) >= self.per_minut:
                    espera = 60 - (ara - self.finestra[0]) + 0.1
                else:
                    espera = 0
            else:
                espera = 0
            self.peticions += 1
            toca_descans = (self.descans_cada
                            and self.peticions % self.descans_cada == 0)
            factor = self.factor
            self.finestra.append(ara + espera)
        if espera > 0:
            time.sleep(espera)
        # pausa curta aleatòria (mai el mateix interval: no fem tic-tac de robot)
        time.sleep(random.uniform(self.pausa_min, self.pausa_max) * factor)
        if toca_descans:
            llarg = random.uniform(*self.descans)
            print(f"\n  · descans de {llarg:.0f} s després de {self.peticions} peticions…",
                  flush=True)
            time.sleep(llarg)

    def apunta_demanats_sols(self, quants):
        with self.pany:
            self.demanats_sols += quants

    def buida_demanats_sols(self):
        """Torna el compte i el posa a zero (per fer un resum per dialecte)."""
        with self.pany:
            quants, self.demanats_sols = self.demanats_sols, 0
        return quants

    def ha_anat_be(self):
        with self.pany:
            self.factor = max(1.0, self.factor * 0.97)   # afluixa a poc a poc

    def frenar(self, factor=4.0):
        with self.pany:
            self.factor = max(self.factor, factor)

    def ha_fallat(self, greu=False):
        with self.pany:
            self.factor = min(20.0, self.factor * (2.0 if greu else 1.4))
            factor = self.factor
        return factor

# ------------------------------------------------------------------- peticions


def sessio_nova():
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(NAVEGADORS),
        "Accept": "*/*",
        "Accept-Language": "ca-ES,ca;q=0.9,es;q=0.8,en;q=0.7",
        "Origin": "https://projecte-aina-transcripcio-fonetica-catala.hf.space",
        "Referer": "https://projecte-aina-transcripcio-fonetica-catala.hf.space/",
    })
    return s


class ErrorAPI(Exception):
    def __init__(self, missatge, greu=False):
        super().__init__(missatge)
        self.greu = greu


def demanar(sessio, text, dialecte, regulador):
    """Una petició a l'API. Torna el text transcrit o llança ErrorAPI."""
    regulador.abans_de_peticio()
    r = sessio.post(URL, json={"data": [text, dialecte]}, timeout=60)
    if r.status_code in (429, 503):
        raise ErrorAPI(f"HTTP {r.status_code} (ens estan frenant)", greu=True)
    r.raise_for_status()
    event_id = r.json()["event_id"]

    # Cal buidar l'stream SENCER abans de sortir del "with". Si en sortim a
    # mitges (fent return dins del bucle), la connexió keep-alive torna al pool
    # amb dades pendents i la petició següent d'aquesta mateixa sessió es
    # menja les restes: apareixen transcripcions com "bərɣˈos  dəzðunˈaβən",
    # amb el final de la resposta anterior enganxat al davant.
    esdeveniment = None
    resultat = None
    error = False
    with sessio.get(f"{URL}/{event_id}", stream=True, timeout=300) as r2:
        if r2.status_code in (429, 503):
            raise ErrorAPI(f"HTTP {r2.status_code} (ens estan frenant)", greu=True)
        r2.raise_for_status()
        for linia in r2.iter_lines(decode_unicode=True):
            if not linia:
                continue
            if linia.startswith("event:"):
                esdeveniment = linia[6:].strip()
                if esdeveniment == "error":
                    error = True
            elif linia.startswith("data:"):
                dades = json.loads(linia[5:])
                valor = dades[0] if isinstance(dades, list) and dades else None
                if valor is not None and not error:
                    resultat = valor
    if resultat is None:
        raise ErrorAPI("resposta buida/error del servidor")
    return resultat


def demanar_amb_reintents(sessio, text, dialecte, regulador, intents=6):
    for i in range(intents):
        try:
            resultat = demanar(sessio, text, dialecte, regulador)
            regulador.ha_anat_be()
            return resultat
        except (ErrorAPI, requests.RequestException) as e:
            greu = isinstance(e, ErrorAPI) and e.greu
            factor = regulador.ha_fallat(greu)
            if i == intents - 1:
                return None
            espera = min(300, (3 ** i) * random.uniform(0.7, 1.4) * (3 if greu else 1))
            print(f"\n  ! {dialecte}: {e} → reintent {i+1}/{intents-1} "
                  f"d'aquí {espera:.0f}s (ritme x{factor:.1f})", flush=True)
            time.sleep(espera)
    return None

# ----------------------------------------------------------------------- lots


def fer_lots(mots, max_caracters=MAX_CARACTERS_LOT):
    """Agrupa mots en blocs que no superin el límit del servidor."""
    lots, actual, llarg = [], [], 0
    for mot in mots:
        cost = len(mot) + 2          # el mot + ".\n"
        if actual and llarg + cost > max_caracters:
            lots.append(actual)
            actual, llarg = [], 0
        actual.append(mot)
        llarg += cost
    if actual:
        lots.append(actual)
    return lots


def transcriure_lot(sessio, lot, dialecte, regulador):
    """Transcriu un bloc de mots. Torna {mot: transcripció}.

    Els mots s'envien separats per '.\\n': el punt evita la fonètica de frase
    (que canviaria la transcripció segons el mot del costat) i el salt de línia
    es conserva a la resposta, cosa que dona correspondència 1:1.
    """
    text = ".\n".join(lot) + "."
    resposta = demanar_amb_reintents(sessio, text, dialecte, regulador)
    resultats, dubtosos = {}, lot
    if resposta is not None:
        linies = [neteja(x) for x in resposta.split("\n")]
        if len(linies) == len(lot):
            # Ens quedem les línies netes i tornem a demanar només les que fan
            # pudor: que una faci mala cara no invalida les altres vint-i-quatre.
            resultats = {m: x for m, x in zip(lot, linies) if not sospitosa(x, m)}
            dubtosos = [m for m in lot if m not in resultats]
            if dubtosos:
                # No ho diem lot per lot: al diccionari hi ha 1.721 mots que es
                # transcriuen amb espais de debò («BlaBlaCar» → «blˈa βlˈa
                # kˈar») i ompliria la pantalla d'avisos per no res. Al final de
                # cada dialecte se'n fa un resum.
                regulador.apunta_demanats_sols(len(dubtosos))
        else:
            # Aquí sí que s'ha de refer tot: sense correspondència 1:1 no sabem
            # quina línia és de quin mot.
            print(f"\n  ! {dialecte}: lot desalineat ({len(lot)} mots → "
                  f"{len(linies)} línies); es fa mot a mot", flush=True)
    # pla B: un per un (lent però segur)
    for mot in dubtosos:
        r = demanar_amb_reintents(sessio, mot + ".", dialecte, regulador)
        if r is None:
            continue
        r = neteja(r)
        if not r:
            continue                    # buida: cap mot no sona a res
        if sospitosa(r) and not confirmat(sessio, mot, r, dialecte, regulador):
            continue
        resultats[mot] = r
    return resultats


def confirmat(sessio, mot, transcripcio, dialecte, regulador):
    """Segona opinió per a un mot que fa mala cara demanat tot sol.

    sospitosa() és una regla de polze, i una regla de polze no pot condemnar cap
    mot per sempre: si un mot es transcrivís de debò amb dos espais seguits,
    rebutjar-lo sempre deixaria el fitxer d'aquell dialecte sense escriure per
    sempre més, per moltes vegades que tornessis a executar l'script. (N'hem
    provat els 1.721 mots del diccionari amb guió, apòstrof o majúscula
    interior, als 6 dialectes: cap dels 10.326 no duu dos espais. Però el
    diccionari en té 529.206 i no els hem vist tots.)

    Ho resolem preguntant-ho un segon cop: les restes d'una altra petició són
    fortuïtes i no tornen a sortir igual, mentre que una transcripció bona sí.
    """
    segon = demanar_amb_reintents(sessio, mot + ".", dialecte, regulador)
    if segon is None or neteja(segon) != transcripcio:
        return False
    print(f"\n  · {dialecte}: «{mot}» → «{transcripcio}» surt igual dos cops "
          f"seguits; ho donem per bo", flush=True)
    return True


def neteja(transcripcio):
    return re.sub(r"\s*\.\s*$", "", transcripcio.strip()).strip()


def sospitosa(transcripcio, mot=None):
    """Detecta restes d'una altra resposta enganxades a la transcripció.

    Sense `mot` el sedàs és el bàsic: buida o amb dos espais seguits. Serveix
    per als mots demanats d'un en un, on no hi ha res a desalinear.

    Amb `mot` és més estricte i es fa servir per als lots: un mot sense espais,
    guions ni apòstrofs no pot donar una transcripció amb espais, i si en duu
    són restes d'una altra petició ('esquilarien' → 'əskiləɾˈiən tisiunˈi').
    Aquí sí que hi ha falsos positius —'JuntsxCat' → 'ʒˈunʃʃ kˈat' és bo—, però
    surten barats: el lot es repeteix mot a mot i allà s'accepten.

    Ull: això no ho enxampa tot. Quan el servidor substitueix una línia sencera
    per la d'un altre mot no queda cap rastre visible. L'únic remei de debò és
    no enviar mai dues peticions alhora: mira el comentari de PERFILS.
    """
    if not transcripcio or "  " in transcripcio:
        return True
    if mot is None:
        return False
    return " " in transcripcio and not re.search(r"[\s'’\-]", mot)

# ---------------------------------------------------------------------- caché


class Cache:
    """Un fitxer TSV per dialecte: mot <TAB> transcripció. S'hi escriu a mesura
    que arriben els resultats, així res del que ja s'ha fet es perd mai."""

    @staticmethod
    def llegir(cami):
        dades = {}
        if not os.path.exists(cami):
            return dades
        with open(cami, "r", encoding="utf-8") as f:
            for linia in f:
                if "\t" not in linia or not linia.endswith("\n"):
                    continue              # línia a mitges d'una aturada brusca
                mot, _, trans = linia.rstrip("\n").partition("\t")
                if mot and trans:
                    dades[mot] = trans
        return dades

    @staticmethod
    def sanejar(cami, marge):
        """Deixa el fitxer llest per continuar-hi escrivint al darrere.

        Si l'script s'atura de cop, l'última línia pot quedar a mitges. Obrir el
        fitxer en mode «afegir» i escriure-hi de dret enganxaria el mot següent
        a aquella resta: 'peix\tpˈe' + 'aigua\tˈajɣwə' dona
        'peix\tpˈeaigua\tˈajɣwə', una entrada falsa que després es donaria per
        bona i acabaria al fitxer final.

        Per no dependre de com va quedar el disc, retallem el fitxer per
        l'última línia sencera, llencem les línies mal formades (les que ja
        haguessin quedat enganxades d'abans) i, de propina, les últimes `marge`
        entrades. Tot això es torna a demanar: costa segons i evita maldecaps.
        """
        if not os.path.exists(cami):
            return
        with open(cami, "rb") as f:
            original = f.read()
        # Partint per "\n", l'últim tros és buit si el fitxer acaba en salt de
        # línia; si no hi acaba, aquest últim tros és la línia a mitges. En tots
        # dos casos el volem fora, així que el descartem sempre.
        senceres = original.split(b"\n")[:-1]
        bones = [l for l in senceres if l.count(b"\t") == 1]
        if marge:
            bones = bones[:max(0, len(bones) - marge)]
        nou = b"".join(l + b"\n" for l in bones)
        if nou == original:
            return
        temporal = cami + ".tmp"
        with open(temporal, "wb") as f:
            f.write(nou)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporal, cami)          # mai una caché a mitges
        a_mitges = " i una línia a mitges" if not original.endswith(b"\n") else ""
        print(f"  · {os.path.basename(cami)}: descarto {len(senceres) - len(bones)} "
              f"entrades del final{a_mitges}; en queden {mil(len(bones))} "
              f"(la resta es tornarà a demanar)", flush=True)

    def __init__(self, cami, marge=MARGE_SEGURETAT):
        self.cami = cami
        self.pany = threading.Lock()
        self.sanejar(cami, marge)           # abans de llegir res
        self.dades = self.llegir(cami)
        self.fitxer = open(cami, "a", encoding="utf-8")

    def desa(self, parells):
        if not parells:
            return
        with self.pany:
            for mot, trans in parells.items():
                self.dades[mot] = trans
                self.fitxer.write(f"{mot}\t{trans}\n")
            self.fitxer.flush()
            os.fsync(self.fitxer.fileno())      # a disc de debò

    def tanca(self):
        with self.pany:
            self.fitxer.close()

# ------------------------------------------------------------------ programa


def mil(n):
    """12345 -> '12.345' (separador de milers a la catalana)."""
    return f"{n:,}".replace(",", ".")


def temps_llegible(segons):
    segons = int(segons)
    h, m = divmod(segons // 60, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m {segons % 60:02d}s"


def processar_dialecte(dialecte, mots_unics, linies_originals, args, regulador):
    """Un dialecte de cap a peus, i després el següent: així tens el primer
    fitxer acabat i utilitzable molt abans que no pas si van tots a mitges."""
    cache = Cache(os.path.join(args.cache, f"{args.prefix}__{dialecte}.tsv"),
                  args.marge)
    pendents = [m for m in mots_unics if m not in cache.dades]
    print(f"\n=== {dialecte}: {mil(len(mots_unics) - len(pendents))} ja fets, "
          f"{mil(len(pendents))} pendents", flush=True)
    try:
        completar([dialecte], {dialecte: cache}, mots_unics, args, regulador)
    except KeyboardInterrupt:
        cache.tanca()
        raise
    resum_demanats_sols(regulador, dialecte)
    escriure_final(dialecte, cache, mots_unics, linies_originals, args)
    cache.tanca()


def completar(dialectes, caches, mots_unics, args, regulador, voltes=4):
    """Passa i repassa fins que no quedi cap mot pendent.

    Si un lot esgota els reintents es prova mot a mot; si un mot també els
    esgota, queda pendent i aquí el repesquem en una volta nova, més lenta i
    amb un sol fil. Res s'escriu mai malament: el que falla, torna a la cua.
    """
    for volta in range(voltes):
        feina = []
        for dialecte in dialectes:
            pendents = [m for m in mots_unics if m not in caches[dialecte].dades]
            feina.append([(dialecte, lot) for lot in fer_lots(pendents)])
        tasques = [t for grup in zip_longest(*feina) for t in grup if t]
        if not tasques:
            return
        total = sum(len(lot) for _, lot in tasques)
        if volta:
            espera = 30 * volta
            print(f"\n  Repesca {volta}: queden {mil(total)} mots. Descans de "
                  f"{espera}s i ho tornem a provar a ritme lent, amb 1 fil.",
                  flush=True)
            time.sleep(espera)
            regulador.frenar(3.0 * volta)
        executar(tasques, caches, total, args, regulador, fils=1 if volta else None)


def resum_demanats_sols(regulador, dialecte=""):
    """Diu quants mots ha hagut de repescar el sedàs, tot d'una vegada."""
    quants = regulador.buida_demanats_sols()
    if not quants:
        return
    qui = f"{dialecte}: " if dialecte else ""
    print(f"  · {qui}{mil(quants)} mots demanats d'un en un perquè al lot "
          f"sortien amb espais. És l'esperat: n'hi ha que en duen de debò "
          f"(«BlaBlaCar» → «blˈa βlˈa kˈar»).", flush=True)


def escriure_final(dialecte, cache, mots_unics, linies_originals, args):
    """Escriu el fitxer final si el dialecte està sencer."""
    perduts = [m for m in mots_unics if m not in cache.dades]
    if perduts:
        cami = os.path.join(args.cache, f"{args.prefix}__{dialecte}__pendents.txt")
        with open(cami, "w", encoding="utf-8") as f:
            f.write("\n".join(perduts) + "\n")
        print(f"  ! {dialecte}: {mil(len(perduts))} mots sense transcriure "
              f"(llista a {cami}). Torna a executar l'script.", flush=True)
        return False
    sortida = f"{args.prefix}_{dialecte.lower()}.txt"
    temporal = sortida + ".tmp"
    with open(temporal, "w", encoding="utf-8") as f:
        for linia in linies_originals:
            f.write(cache.dades[linia] + "\n")
    os.replace(temporal, sortida)      # mai un fitxer final a mitges
    print(f"  ✓ {dialecte} completat → {sortida}", flush=True)
    return True


def processar_alhora(dialectes, mots_unics, linies_originals, args, regulador):
    """Tots els dialectes avancen a la vegada, entrellaçant-ne les peticions."""
    caches = {}
    for dialecte in dialectes:
        cache = Cache(os.path.join(args.cache, f"{args.prefix}__{dialecte}.tsv"),
                      args.marge)
        caches[dialecte] = cache
        pendents = [m for m in mots_unics if m not in cache.dades]
        print(f"  {dialecte:12} {mil(len(mots_unics) - len(pendents)):>9} fets, "
              f"{mil(len(pendents))} pendents", flush=True)

    completar(dialectes, caches, mots_unics, args, regulador)
    resum_demanats_sols(regulador)
    for dialecte in dialectes:
        escriure_final(dialecte, caches[dialecte], mots_unics, linies_originals, args)
        caches[dialecte].tanca()


def executar(tasques, caches, total, args, regulador, fils=None):
    """Reparteix les tasques (dialecte, lot) entre els fils."""
    fils = fils or args.fils
    inici, fets = time.time(), 0
    pany = threading.Lock()
    tall = threading.Event()

    def treballar(indexs):
        nonlocal fets
        sessio = sessio_nova()
        for i in indexs:
            if tall.is_set():
                return
            dialecte, lot = tasques[i]
            caches[dialecte].desa(transcriure_lot(sessio, lot, dialecte, regulador))
            with pany:
                fets += len(lot)
                if fets % 2000 < len(lot):
                    ritme = fets / (time.time() - inici)
                    queda = (total - fets) / ritme if ritme else 0
                    print(f"  {mil(fets)}/{mil(total)} mots ({ritme:.0f} mots/s) "
                          f"— queda ~{temps_llegible(queda)}", flush=True)

    fils = [threading.Thread(target=treballar,
                             args=(range(k, len(tasques), fils),), daemon=True)
            for k in range(fils)]
    for f in fils:
        f.start()
    try:
        for f in fils:
            while f.is_alive():
                f.join(0.5)
    except KeyboardInterrupt:
        tall.set()
        print("\nAturant… (tot el transcrit fins ara queda desat a la caché)", flush=True)
        for f in fils:
            f.join(15)
        raise


def comprovar(args):
    """Passa comprova.py sobre el que s'acaba de generar. Torna el seu codi.

    Es fa en un procés a part, i no important-lo, perquè comprova.py importa
    d'aquest fitxer: cridar-lo des d'aquí faria una importació circular. A més,
    així el que s'executa és exactament la mateixa ordre que faries a mà, amb
    els mateixos arguments que has donat aquí.
    """
    cami = os.path.join(os.path.dirname(os.path.abspath(__file__)), "comprova.py")
    if not os.path.exists(cami):
        print(f"\n  ! no trobo {cami}; no es fa la comprovació", flush=True)
        return 0
    ordre = [sys.executable, cami,
             "--entrada", args.entrada,
             "--dialectes", args.dialectes,
             "--cache", args.cache,
             "--perfil", args.perfil,        # que un perfil discret ho sigui fins al final
             "--mostra", str(args.mostra)]
    print("\n" + "-" * 70)
    print("Comprovació automàtica (comprova.py"
          + (f" --mostra {args.mostra}" if args.mostra else "") + "):\n", flush=True)
    try:
        return subprocess.call(ordre)
    except KeyboardInterrupt:
        print("\nComprovació aturada per l'usuari. Els fitxers ja són fets; "
              "pots comprovar-los quan vulguis amb:\n"
              f"    python3 comprova.py --entrada {args.entrada} --mostra {args.mostra}")
        return 130


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--entrada", default="../../col_0.txt")
#    p.add_argument("--entrada", default="proves.txt")
    p.add_argument("--dialectes", default=",".join(DIALECTES))
    p.add_argument("--perfil", default="normal", choices=list(PERFILS))
    p.add_argument("--fils", type=int, default=None,
                   help="peticions simultànies (per defecte, la del perfil)")
    p.add_argument("--cache", default="cache")
    p.add_argument("--marge", type=int, default=MARGE_SEGURETAT,
                   help="entrades que es descarten del final de cada caché en "
                        "començar, per si l'última escriptura va quedar a "
                        "mitges (per defecte, %(default)s)")
    p.add_argument("--alhora", action="store_true",
                   help="avança els 6 dialectes a la vegada en comptes d'un rere "
                        "l'altre (mateix temps total, però cap fitxer no s'acaba "
                        "fins al final)")
    p.add_argument("--estat", action="store_true", help="només mostra el progrés")
    p.add_argument("--mostra", type=int, default=200,
                   help="mots per dialecte que comprova.py torna a demanar a "
                        "l'API en acabar, per detectar transcripcions que són "
                        "bones però d'un altre mot (0 = només revisió interna; "
                        "per defecte, %(default)s)")
    p.add_argument("--sense-comprova", dest="comprova", action="store_false",
                   help="no passa comprova.py en acabar")
    args = p.parse_args()

    perfil = PERFILS[args.perfil]
    if args.fils is None:
        args.fils = perfil["fils"]
    args.prefix = os.path.splitext(os.path.basename(args.entrada))[0]
    os.makedirs(args.cache, exist_ok=True)

    with open(args.entrada, "r", encoding="utf-8") as f:
        linies_originals = [l.strip() for l in f if l.strip()]
    # dict.fromkeys manté l'ordre d'aparició. Amb sorted() sortirien primer els
    # 14.668 mots en majúscula (els codis de caràcter manen), i la caché
    # s'ompliria de noms propis durant la primera hora.
    mots_unics = list(dict.fromkeys(linies_originals))
    dialectes = [d.strip() for d in args.dialectes.split(",") if d.strip()]

    print(f"Entrada: {args.entrada} — {mil(len(linies_originals))} línies, "
          f"{mil(len(mots_unics))} mots únics")
    print(f"Perfil: {args.perfil} ({args.fils} fil(s), "
          f"{perfil['per_minut'] or 'sense'} peticions/minut)")
    if args.fils > 1:
        print("  ATENCIÓ: amb més d'un fil el servidor barreja les respostes de "
              "les peticions simultànies i un 2% dels mots surt amb la "
              "transcripció d'un altre. No ho facis servir per a la feina bona.",
              flush=True)

    if args.estat:
        for d in dialectes:
            cami = os.path.join(args.cache, f"{args.prefix}__{d}.tsv")
            fets = len(Cache.llegir(cami))
            print(f"  {d:12} {mil(fets):>9}/{mil(len(mots_unics))} "
                  f"({100*fets/len(mots_unics):5.1f}%)")
        return

    regulador = Regulador(perfil)
    inici = time.time()
    try:
        if args.alhora:
            processar_alhora(dialectes, mots_unics, linies_originals, args, regulador)
        else:
            for dialecte in dialectes:
                processar_dialecte(dialecte, mots_unics, linies_originals, args, regulador)
    except KeyboardInterrupt:
        print(f"\nAturat per l'usuari. Temps: {temps_llegible(time.time() - inici)}. "
              f"Torna a executar l'script per continuar on eres.")
        sys.exit(130)
    print(f"\nFet. Temps total: {temps_llegible(time.time() - inici)}")

    if args.comprova:
        codi = comprovar(args)
        if codi:
            sys.exit(codi)


if __name__ == "__main__":
    main()
