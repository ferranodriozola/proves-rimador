"""
Ortografia i fonètica de l'enclisi: verb + pronom feble.

Aquest mòdul és l'única definició de com s'escriu, com es pronuncia, quantes
síl·labes té i quina rima fa una forma verbal amb un pronom enganxat al darrere.
Substitueix la lògica que estava triplicada (i divergida) als tres scripts
generar_infinitius / generar_gerundis / generar_imperatius.

No llegeix ni escriu fitxers, no sap res de llicències de verbs: només transforma
(forma verbal, transcripció, pronom) -> (forma nova, transcripció nova, ...).

Documentació de les decisions: pronoms/pla.md i pronoms/pla_un_pronom.md; el
cas de 2 pronoms, a pronoms/pla_dos_pronoms.md.
"""

# ---------------------------------------------------------------- alfabets

# Vocals GRÀFIQUES, per decidir guionet o apòstrof. La 'u' en queda fora
# expressament: la regla normativa és "forma plena darrere consonant O DIFTONG",
# i una -u final sempre fa diftong (canteu-me, no *canteu'm).
#
# La dièresi hi ÉS justament perquè marca el contrari: que la vocal no fa
# diftong. Els 396 imperatius de vostè acabats en -ï (actuï, canviï, estudiï)
# acaben en vocal plena i demanen la forma reduïda -- actuï'l, no *actuï-lo.
VOCALS_GRAFIQUES = set("aeioàèéíòóúïü")

# Vocals de l'AFI, per decidir sonoritzacions i semivocalitzacions.
VOCALS_AFI = set("aeiouəɛɔ")

# Consonants sonores de l'AFI, per a la sonorització de la -s final.
CONSONANTS_SONORES_AFI = set("bdgβðɣmnɲŋlʎrɾzʒjw")

# Nasals de l'AFI. Són l'únic context on una oclusiva sonora es queda
# oclusiva: el diccionari fa bum-bum /bˈumbˈum/ però pèl-blanc /pˈɛlβlˈaŋ/,
# corba /kˈorβə/ i arbre /ˈaβɾə/.
NASALS_AFI = set("mnɲŋɱ")


# ------------------------------------------------------- taula de l'enclisi

# pronom -> (forma darrere consonant o diftong, forma darrere vocal)
# Verificat contra el quadre normatiu (CPNL, GEIEC 13.4.2); vegeu pla.md §2.1.
ENCLISI = {
    "em":  ("-me",  "'m"),
    "et":  ("-te",  "'t"),
    "es":  ("-se",  "'s"),
    "ens": ("-nos", "'ns"),
    "us":  ("-vos", "-us"),
    "el":  ("-lo",  "'l"),
    "la":  ("-la",  "-la"),
    "els": ("-los", "'ls"),
    "les": ("-les", "-les"),
    "li":  ("-li",  "-li"),
    "en":  ("-ne",  "'n"),
    "ho":  ("-ho",  "-ho"),
    "hi":  ("-hi",  "-hi"),
}

# Transcripció AFI de cada forma enclítica, amb la reducció vocàlica del
# català central ja aplicada (-lo -> [lu], -nos -> [nus]...).
FONEMA = {
    "-me": "mə",  "'m": "m",
    "-te": "tə",  "'t": "t",
    "-se": "sə",  "'s": "s",
    "-nos": "nus", "'ns": "ns",
    "-vos": "bus", "-us": "us",
    "-lo": "lu",  "'l": "l",
    "-la": "lə",
    "-los": "lus", "'ls": "ls",
    "-les": "ləs",
    "-li": "li",
    "-ne": "nə",  "'n": "n",
    "-ho": "u",
    "-hi": "i",
}

# Codi de 2 lletres per pronom, tret de la forma enclítica per ser mnemònic i
# no xocar (-ne -> NE, -nos -> NS, -los -> LS). Vegeu pla_un_pronom.md §4.
PRONOM_CODI = {
    "em": "EM", "et": "ET", "es": "ES", "ens": "NS", "us": "US",
    "el": "EL", "la": "LA", "els": "LS", "les": "LE", "li": "LI",
    "en": "NE", "ho": "HO", "hi": "HI",
}

# Ordre gramatical de col·locació, per escriure els codis de 2 pronoms sempre
# igual (pla_un_pronom.md §4). Amb 1 pronom només serveix per ordenar la sortida.
ORDRE_PRONOMS = ["es", "et", "us", "em", "ens", "li", "els",
                 "el", "la", "les", "en", "hi", "ho"]

# Grups consonàntics on la segona consonant POT ser muda en posició final i
# reaparèixer davant de vocal (sensibilització): cantant /kəntˈan/ -> cantant-hi
# /kəntˈanti/. La clau és la grafia final; el valor, el fonema que reapareix.
#
# Que hi surti un grup NO vol dir que la consonant sigui sempre muda: en aquest
# mateix diccionari 'ressurt' fa /rəsˈur/ (muda) però 'port' fa /pˈɔrt/ (sona).
# Per això _consonant_muda() no es fia d'aquesta llista tota sola, sinó que
# comprova sempre contra la transcripció real.
GRUPS_MUTS = {
    "nt": "t", "mp": "p", "lt": "t", "rt": "t",
    "nc": "k", "lc": "k", "mb": "b", "nd": "d", "ld": "d", "rd": "d",
    "ng": "g", "lg": "g", "rg": "g", "rb": "b", "rc": "k",
}

# Com es pot realitzar cada consonant final al diccionari. Cal per no confondre
# una consonant MUDA amb una consonant ASSORDIDA: 'perd' es transcriu /pˈɛrt/,
# o sigui que la -d sí que sona (com a [t]) i no s'ha de recuperar cap [d].
REALITZACIONS = {
    "t": "t", "d": "td",          # perd -> pˈɛrt
    "p": "p", "b": "bpβ",         # tomb -> tˈom / corb -> kˈorp
    "k": "k", "g": "gkɣ",
    "r": "rɾ",
}

# Assimilació de la nasal: una -n final agafa el punt d'articulació de la
# consonant següent. El diccionari ho fa sistemàticament, també a través de
# límits de morfema: enmig -> əmmˈitʃ, tanmateix -> tˌammətˈeʃ,
# granment -> ɡɾˈammˈen, canvi -> kˈambi, enfront -> əɱfɾˈon, encara -> əŋkˈaɾə.
#
# Amb els 13 pronoms només s'activa la branca bilabial (-me, 'm i -vos);
# cap enclític no comença per labiodental ni per velar. Les altres files hi
# són perquè la regla quedi escrita sencera i no com un cas particular.
ASSIMILACIO_NASAL = {
    "m": "bpmβ",     # bilabial:    -me, 'm, -vos
    "ɱ": "fv",       # labiodental: (cap enclític, avui)
    "ŋ": "kgɣ",      # velar:       (cap enclític, avui)
}


# ----------------------------------------------------------------- ortografia

def acaba_en_vocal(forma):
    """Regla gràfica de l'enclisi: mira l'última lletra del verb ESCRIT."""
    return forma[-1].lower() in VOCALS_GRAFIQUES


def forma_enclitica(pronom, forma):
    """
    Forma plena (guionet) darrere consonant o diftong; reduïda (apòstrof)
    darrere vocal. 'hi', 'ho', 'la', 'les' i 'li' no tenen forma reduïda.
    """
    plena, reduida = ENCLISI[pronom]
    return reduida if acaba_en_vocal(forma) else plena


def escriure(forma, enclitic):
    """La forma gràfica sencera. L'apòstrof i el guionet ja venen a l'enclític."""
    return forma + enclitic


# ------------------------------------------------------------------ fonètica

def _consonant_muda(forma, transcripcio):
    """
    Quina consonant final del verb escrit NO sona quan el verb va sol.
    Retorna (tipus, fonema) o (None, None).

      · ('r', 'r')  -> la -r d'infinitiu: cantar /kəntˈa/, conèixer /kunˈɛʃə/
      · ('grup', X) -> la 2a consonant d'un grup: cantant /kəntˈan/, romp /rˈom/

    Es detecta comparant la grafia amb la transcripció, no per tipus de forma
    verbal: així funciona igual per a infinitius, gerundis i imperatius, i no
    s'activa quan la consonant sí que sona, ni tan sols quan sona assordida
    (bat /bˈat/ no recupera cap 't'; perd /pˈɛrt/ no recupera cap 'd').
    """
    f = forma.lower()

    if f.endswith("r") and not transcripcio.endswith(tuple(REALITZACIONS["r"])):
        return "r", "r"

    if len(f) >= 2 and f[-2:] in GRUPS_MUTS:
        fonema = GRUPS_MUTS[f[-2:]]
        if not transcripcio.endswith(tuple(REALITZACIONS.get(fonema, fonema))):
            return "grup", fonema

    return None, None


def _sensibilitzar(forma, transcripcio, fonema_seguent):
    """
    Regles (1) i (2): recupera la consonant final muda del verb quan hi ha
    alguna cosa enganxada al darrere. Necessita la GRAFIA, i per això va a
    part del sàndhi pur, que només mira els sons.
    """
    comenca_en_vocal = fonema_seguent[0] in VOCALS_AFI
    tipus, muda = _consonant_muda(forma, transcripcio)
    if tipus == "r":
        return transcripcio + ("ɾ" if comenca_en_vocal else "r")
    if tipus == "grup" and comenca_en_vocal:
        return transcripcio + muda
    return transcripcio


def _sandhi(esquerra, dreta):
    """
    Regles (3), (4) i (5): el que passa al LÍMIT entre dos trossos d'AFI.

    Retorna els dos trossos modificats. Com que només mira sons, serveix tant
    per al límit verb|pronom com per al límit pronom1|pronom2 dels grups de
    dos pronoms (digues-los-ho /dˈiɣəzluzu/: la mateixa regla, dues vegades).
    """
    if not esquerra or not dreta:
        return esquerra, dreta

    # (3) sonorització de la -s final davant vocal o consonant sonora.
    #     Només si la -s fa CODA: un fragment d'un sol so ('-s'hi', '-t'ho')
    #     és l'obertura de la síl·laba següent, no una coda, i no sonoritza
    #     (renta-s'hi /rˈentəsi/, mai *[zi]).
    if len(esquerra) > 1 and esquerra.endswith("s") and (
            dreta[0] in VOCALS_AFI or dreta[0] in CONSONANTS_SONORES_AFI):
        esquerra = esquerra[:-1] + "z"

    # (4) espirantització de la v- de '-vos'. L'única cosa que la manté
    #     oclusiva és una nasal al davant, no pas el fet de no ser vocal:
    #     canteu-vos /kəntˈɛwβus/ i cantar-vos /kəntˈarβus/ (cf. corba
    #     /kˈorβə/, pèl-blanc /pˈɛlβlˈaŋ/), però cantem-vos /kəntˈɛmbus/
    #     (cf. bum-bum /bˈumbˈum/).
    if dreta.startswith("b") and esquerra[-1] not in NASALS_AFI:
        dreta = "β" + dreta[1:]

    # (5) assimilació de la -n final al punt d'articulació del que ve.
    #     És la mateixa -n que acaba de deixar '-vos' en [b] a la (4): el
    #     resultat és cantant-vos /kəntˈambus/, amb les dues coses alhora.
    if esquerra.endswith("n"):
        for nasal, contextos in ASSIMILACIO_NASAL.items():
            if dreta[0] in contextos:
                esquerra = esquerra[:-1] + nasal
                break

    return esquerra, dreta


def _semivocal(anterior, enclitic, fonema):
    """
    Regla (6): '-hi' i '-ho' es realitzen en semivocal [j]/[w] darrere vocal,
    i es fonen amb la vocal anterior dins el mateix nucli sil·làbic.
    """
    if anterior and anterior[-1] in VOCALS_AFI:
        if enclitic == "-hi":
            return "j"
        if enclitic == "-ho":
            return "w"
    return fonema


def transcriure(forma, transcripcio, enclitic):
    """
    Munta la transcripció AFI del grup verb+enclític a partir de la del verb sol.

    Retorna (transcripcio_completa, fonema_de_l'enclitic). El fonema el necessita
    silabes() per saber si l'enclític ha quedat en semivocal.

    Regles de sàndhi, totes amb precedent al diccionari (pla.md §6.2):

      1) La -r muda de l'infinitiu SONA sempre que hi ha enclític (decisió D5):
         entre vocals, bategant [ɾ]  -> anar-hi   /ənˈaɾi/   (cf. escenari /əsənˈaɾi/)
         en coda, davant consonant [r] -> cantar-ne /kəntˈarnə/ (cf. abaderna /əβəðˈɛrnə/)

      2) La consonant muda d'un grup final (-nt, -mp, -rt...) es recupera NOMÉS
         davant de vocal; davant de consonant continua elidida:
             cantant-hi /kəntˈanti/  (cf. vint-i-set /bˈintisˈɛt/)
             cantant-ne /kəntˈannə/  (cf. Mont-real /mˈonreˈal/)
         Aquesta asimetria amb la -r és volguda: una -r sola pot fer coda,
         mentre que la 2a consonant d'un grup no.

      3) La -s final es sonoritza en [z] davant de vocal o consonant sonora:
             digues-hi /dˈiɣəzi/, digues-ne /dˈiɣəznə/
         (cf. esdevenir /əzðəβənˈi/, despús-ahir /dəspˈuzəˈi/)

      4) La v- de '-vos' s'espirantitza en [β] a tot arreu MENYS darrere nasal:
             canteu-vos /kəntˈɛwβus/  (cf. vis-a-vis /bˈizəβˈis/)
             cantar-vos /kəntˈarβus/  (cf. corba /kˈorβə/, pèl-blanc /pˈɛlβlˈaŋ/)
             cantem-vos /kəntˈɛmbus/  (cf. bum-bum /bˈumbˈum/)

      5) Una -n final assimila el punt d'articulació de l'enclític:
             cantant-me  /kəntˈammə/   (cf. granment /ɡɾˈammˈen/)
             cantant-vos /kəntˈambus/  (cf. canvi /kˈambi/)

      6) Darrere vocal, '-hi' i '-ho' es realitzen com a semivocal [j] / [w],
         que es fon amb la vocal anterior (decisió P5):
             veure-hi /bˈɛwɾəj/, canta-ho /kˈantəw/
         (cf. aire /ˈajɾə/, taula /tˈawlə/)
    """
    fonema = FONEMA[enclitic]
    transcripcio = _sensibilitzar(forma, transcripcio, fonema)       # (1) i (2)
    transcripcio, fonema = _sandhi(transcripcio, fonema)             # (3), (4) i (5)
    fonema = _semivocal(transcripcio, enclitic, fonema)              # (6)
    return transcripcio + fonema, fonema


# -------------------------------------------------------- rima i síl·labes

def calcular_rimes(transcripcio):
    """
    Rima consonant i assonant, amb el MATEIX càlcul que
    'creador_rima + dicc (a partir de col_10).py', perquè no divergeixin mai.
    """
    consonant = transcripcio.split("ˈ")[-1]
    assonant = "".join(l for l in consonant if l in "ɔəaeiou@Eɛˈ")
    return consonant, assonant


def silabes(silabes_base, enclitic, fonema):
    """
    L'enclític amb guionet suma una síl·laba; el d'apòstrof no
    (cf. abans-d'ahir = 4 síl·labes al diccionari).

    Excepció: si l'enclític ha quedat en semivocal ([j] de '-hi', [w] de '-ho'),
    es fon amb la vocal anterior dins el mateix nucli sil·làbic i tampoc no en
    suma (veure-hi = 2 síl·labes, com veure).
    """
    if enclitic.startswith("'") or fonema in ("j", "w"):
        extra = 0
    else:
        extra = 1
    return int(silabes_base) + extra


# ------------------------------------------------------------------- el codi

def construir_codi(forma_verbal, persona, pronoms):
    """
    Codi propi, amplada fixa de 10 caràcters i posicional (pla_un_pronom.md §4):

        W  F  PPP  N  A1A2  B1B2
        0  1  2-4  5  6-7   8-9

    forma_verbal: 'N' infinitiu, 'G' gerundi, 'M' imperatiu
    persona:      None o '000' per a infinitiu/gerundi; '02S'/'01P'/'02P'/'03S'/'03P'
    pronoms:      llista d'1 o 2 pronoms, en ordre gramatical
    """
    if forma_verbal not in ("N", "G", "M"):
        raise ValueError(f"forma verbal desconeguda: {forma_verbal!r}")
    if not 1 <= len(pronoms) <= 2:
        raise ValueError(f"calen 1 o 2 pronoms, no {len(pronoms)}")

    pers = "000" if persona is None else persona
    if len(pers) != 3:
        raise ValueError(f"la persona ha de fer 3 caràcters: {pers!r}")

    codis = [PRONOM_CODI[p] for p in pronoms]
    if len(codis) == 1:
        codis.append("00")

    codi = f"W{forma_verbal}{pers}{len(pronoms)}{''.join(codis)}"
    assert len(codi) == 10, codi
    return codi


def ordenar_pronoms(pronoms):
    """Ordre gramatical de col·locació, perquè el codi sigui sempre el mateix."""
    return sorted(pronoms, key=ORDRE_PRONOMS.index)


# ------------------------------------------------------- tot d'una vegada

def generar_forma(forma, transcripcio, silabes_base, pronoms,
                  forma_verbal, persona=None):
    """
    Conveniència: de (forma verbal, transcripció, síl·labes, pronoms) a tot el
    que necessita una línia del diccionari.

    Retorna un dict amb: paraula, codi, rima_consonant, rima_assonant,
    silabes, transcripcio.
    """
    pronoms = ordenar_pronoms(pronoms)
    if len(pronoms) == 2:
        return _generar_forma_2(forma, transcripcio, silabes_base, pronoms,
                                 forma_verbal, persona)
    if len(pronoms) != 1:
        raise ValueError(f"calen 1 o 2 pronoms, no {len(pronoms)}")

    enclitic = forma_enclitica(pronoms[0], forma)
    transcripcio_nova, fonema = transcriure(forma, transcripcio, enclitic)
    consonant, assonant = calcular_rimes(transcripcio_nova)

    return {
        "paraula": escriure(forma, enclitic),
        "codi": construir_codi(forma_verbal, persona, pronoms),
        "rima_consonant": consonant,
        "rima_assonant": assonant,
        "silabes": silabes(silabes_base, enclitic, fonema),
        "transcripcio": transcripcio_nova,
    }


def _generar_forma_2(forma, transcripcio, silabes_base, pronoms, forma_verbal, persona):
    """
    Cas de 2 pronoms (pla_dos_pronoms.md). L'ORTOGRAFIA surt literalment del
    Quadre 8.9, transcrit a llicencies.PARELLES: no es deriva aquí amb cap
    regla. La FONÈTICA parteix dels dos fragments d'AFI del quadre i hi aplica
    les mateixes regles de sàndhi que amb 1 pronom, ara als DOS límits que hi
    ha (verb|pronom1 i pronom1|pronom2):

        cantar-los-els  /kəntˈarluzəls/   (1) la -r d'infinitiu reapareix
        digues-los-ho   /dˈiɣəzluzu/      (3) les dues -s sonoritzen
        cantant-me'l    /kəntˈamməl/     (5) la -n assimila
        porta-li-ho     /pˈɔrtəliw/       (6) '-ho' en semivocal
        porta-la-hi     /pˈɔrtələj/       (6) també per la via li+la

    `pronoms` ja ve en ordre gramatical (li abans que el/la/els/les, etc.); el
    codi es construeix amb aquest ordre encara que la parella s'hagi
    transformat ortogràficament (li+el -> "l'hi", però el codi és LI+EL).
    """
    import llicencies   # importació diferida: llicencies també importa enclisi

    p1, p2 = pronoms
    # La parella EFECTIVA (li+la -> la+hi) és la que mana en tot el que és
    # so i grafia; la original només sobreviu al codi. Es desa sencera perquè
    # la (6) necessita saber quin pronom sona AL FINAL de debò: a li+la el
    # que es diu és "-la-hi", i és aquell '-hi' el que fa semivocal.
    efectiva = llicencies.parella_efectiva(p1, p2)
    escrit, fonemes = llicencies.PARELLES[efectiva]
    if isinstance(escrit, tuple):
        vocal = acaba_en_vocal(forma)
        escrit = escrit[1] if vocal else escrit[0]
        fonemes = fonemes[1] if vocal else fonemes[0]
    fon1, fon2 = fonemes

    transcripcio = _sensibilitzar(forma, transcripcio, fon1)         # (1) i (2)
    transcripcio, fon1 = _sandhi(transcripcio, fon1)                 # límit verb|pronom1
    fon1, fon2 = _sandhi(fon1, fon2)                                 # límit pronom1|pronom2
    fon2 = _semivocal(fon1, "-" + efectiva[1], fon2)                 # (6)

    cua = fon1 + fon2
    transcripcio_nova = transcripcio + cua
    consonant, assonant = calcular_rimes(transcripcio_nova)

    return {
        "paraula": escriure(forma, escrit),
        "codi": construir_codi(forma_verbal, persona, pronoms),
        "rima_consonant": consonant,
        "rima_assonant": assonant,
        # cada nucli vocàlic de la cua és una síl·laba nova; una semivocal
        # ([j]/[w]) no ho és, i per això no cal cap excepció a part.
        "silabes": int(silabes_base) + sum(1 for c in cua if c in VOCALS_AFI),
        "transcripcio": transcripcio_nova,
    }
