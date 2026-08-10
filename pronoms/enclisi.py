"""
Ortografia i fonètica de l'enclisi: verb + pronom feble.

Aquest mòdul és l'única definició de com s'escriu, com es pronuncia, quantes
síl·labes té i quina rima fa una forma verbal amb un pronom enganxat al darrere.
Substitueix la lògica que estava triplicada (i divergida) als tres scripts
generar_infinitius / generar_gerundis / generar_imperatius.

No llegeix ni escriu fitxers, no sap res de llicències de verbs: només transforma
(forma verbal, transcripció, pronom) -> (forma nova, transcripció nova, ...).

Documentació de les decisions: pronoms/pla.md i pronoms/pla_un_pronom.md.
"""

# ---------------------------------------------------------------- alfabets

# Vocals GRÀFIQUES, per decidir guionet o apòstrof. La 'u' en queda fora
# expressament: la regla normativa és "forma plena darrere consonant O DIFTONG",
# i una -u final sempre fa diftong (canteu-me, no *canteu'm).
VOCALS_GRAFIQUES = set("aeioàèéíòóú")

# Vocals de l'AFI, per decidir sonoritzacions i semivocalitzacions.
VOCALS_AFI = set("aeiouəɛɔ")

# Consonants sonores de l'AFI, per a la sonorització de la -s final.
CONSONANTS_SONORES_AFI = set("bdgβðɣmnɲŋlʎrɾzʒjw")


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

      4) La v- de '-vos' s'espirantitza en [β] darrere vocal
         (cf. vis-a-vis /bˈizəβˈis/)

      5) Una -n final assimila el punt d'articulació de l'enclític:
             cantant-me  /kəntˈammə/   (cf. granment /ɡɾˈammˈen/)
             cantant-vos /kəntˈambus/  (cf. canvi /kˈambi/)

      6) Darrere vocal, '-hi' i '-ho' es realitzen com a semivocal [j] / [w],
         que es fon amb la vocal anterior (decisió P5):
             veure-hi /bˈɛwɾəj/, canta-ho /kˈantəw/
         (cf. aire /ˈajɾə/, taula /tˈawlə/)
    """
    fonema = FONEMA[enclitic]
    comenca_en_vocal = fonema[0] in VOCALS_AFI

    # (1) i (2) sensibilització de la consonant final muda
    tipus, muda = _consonant_muda(forma, transcripcio)
    if tipus == "r":
        transcripcio += "ɾ" if comenca_en_vocal else "r"
    elif tipus == "grup" and comenca_en_vocal:
        transcripcio += muda

    # (3) sonorització de la -s final
    if transcripcio.endswith("s") and (comenca_en_vocal or fonema[0] in CONSONANTS_SONORES_AFI):
        transcripcio = transcripcio[:-1] + "z"

    # (4) espirantització de la v- de '-vos'
    if fonema.startswith("b") and transcripcio and transcripcio[-1] in VOCALS_AFI | {"j", "w"}:
        fonema = "β" + fonema[1:]

    # (5) assimilació de la -n final al punt d'articulació de l'enclític.
    #     Va DESPRÉS de l'espirantització: si abans hi ha una -n, l'enclític
    #     '-vos' es queda en [b] (no és darrere vocal) i és la -n qui es mou.
    if transcripcio.endswith("n"):
        for nasal, contextos in ASSIMILACIO_NASAL.items():
            if fonema[0] in contextos:
                transcripcio = transcripcio[:-1] + nasal
                break

    # (6) semivocalització de '-hi' / '-ho' darrere vocal
    if transcripcio and transcripcio[-1] in VOCALS_AFI:
        if enclitic == "-hi":
            fonema = "j"
        elif enclitic == "-ho":
            fonema = "w"

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
    if len(pronoms) != 1:
        raise NotImplementedError(
            "de moment només 1 pronom; les combinacions dobles són la fase 2 "
            "i necessiten les seves pròpies regles d'apòstrof (pla.md §2.4)"
        )

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
