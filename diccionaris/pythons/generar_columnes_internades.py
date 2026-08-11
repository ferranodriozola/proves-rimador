import sys
from pathlib import Path

# Interna les columnes 1 a 8: en lloc de repetir el mateix text milers de
# vegades, en desa una taula amb els valors diferents i, per a cada fila, el
# número que hi apunta.
#
# El perquè: la col_8 (si la paraula surt al DIEC) té 619.783 files i
# exactament DOS valors diferents. Al navegador, cada fila era un objecte de
# text separat, i això vol dir 14 MB de memòria per dir dues coses. Set de les
# nou columnes tenen aquesta mateixa forma i entre totes se n'enduien 111 MB.
# Internades en són 11,6, i el diccionari doblat hi passa de ~250 MB a ~50.
#
# Es fa aquí i no al navegador perquè així no s'ha de fer a cada visita, però
# sobretot perquè el navegador ja no ha de crear mai els 619.783 objectes de
# text: els números van directes a un array de mida fixa. Internant-ho allà, hi
# hauria un moment amb les dues representacions a la memòria alhora, que amb el
# diccionari doblat és justament el que volem evitar.
#
# El format és text i no binari a posta. Per la xarxa pesen igual (1,42 MB
# contra 1,29 un cop comprimits), però un .txt és text/plain i GitHub Pages el
# comprimeix segur, mentre que un .bin se serviria com a application/octet-
# stream, que els CDN normalment no comprimeixen: seria passar de 1,4 MB a 7,8.
# I de retruc els fitxers continuen sortint al git diff.
#
# La col_0 (paraula) no s'interna: 529.206 valors diferents de 619.783 files,
# el 85% són únics i no hi ha res a estalviar. La col_9 (transcripcions) tampoc,
# pel mateix motiu i perquè ja es baixa a part i només quan cal.
#
# Les col_N.txt continuen sent la font de veritat: les llegeixen els altres
# scripts d'aquesta carpeta i el bot. Aquí només se'n deriva una segona forma.

BASE = Path(__file__).resolve().parent
DIRECTORI_COLUMNES = BASE / "separat"
COLUMNES = list(range(1, 9))

# Columnes que són nombres i que no s'internen "a cegues".
#
# A la resta, el número de cada valor és l'ordre en què ha aparegut, que no vol
# dir res: a la col_2, el 0 és el primer codi que hi havia i prou. A la col_5,
# en canvi, els valors SÓN el nombre de síl·labes, i seria absurd que la síl·laba
# 5 s'amagués darrere d'un número qualsevol. Aquí la taula va del 0 al 14 i cada
# valor cau al seu lloc: idx[i] és directament el nombre de síl·labes de la
# paraula, i condicions com "6 o més" es poden escriure idx[i] >= 6 sense haver
# de mirar la taula ni convertir cap text.
#
# No costa memòria: un Uint8Array ocupa un byte per fila tant si la taula té 13
# entrades com si en té 15. Només queden un parell de caselles sense fer servir.
COLUMNES_NUMERIQUES = {5: 14}  # columna -> valor màxim admès


def llegir_columna(cami):
    dades = cami.read_bytes()
    # L'últim salt de línia no és una fila buida, és el final de l'última fila.
    if dades.endswith(b"\n"):
        dades = dades[:-1]
    return dades.split(b"\n")


def internar(valors):
    taula = []
    numero = {}
    indexs = []

    for valor in valors:
        n = numero.get(valor)
        if n is None:
            n = len(taula)
            numero[valor] = n
            taula.append(valor)
        indexs.append(n)

    return taula, indexs


def internar_numerica(valors, maxim, nom):
    # La taula és 0, 1, 2... fins al màxim, i l'índex de cada fila és el seu
    # propi valor. Retorna None si hi ha res que no encaixi: val més aturar-ho
    # tot que deixar una columna on el número no vol dir el que sembla.
    taula = [str(n).encode() for n in range(maxim + 1)]
    indexs = []

    for fila, valor in enumerate(valors):
        try:
            n = int(valor)
        except ValueError:
            print(f"ERROR: {nom}, fila {fila + 1}: {valor!r} no és cap nombre.")
            return None, None

        if not 0 <= n <= maxim:
            print(f"ERROR: {nom}, fila {fila + 1}: {n} surt del marge 0-{maxim}.")
            print(f"       Puja el màxim a COLUMNES_NUMERIQUES i torna-ho a passar.")
            return None, None

        # Descarta "01", " 3" i companyia: si el text no torna a sortir igual,
        # la columna no es reconstruiria byte a byte.
        if taula[n] != valor:
            print(f"ERROR: {nom}, fila {fila + 1}: {valor!r} no s'escriu com {taula[n]!r}.")
            return None, None

        indexs.append(n)

    return taula, indexs


def tipus_darray(quants_distints):
    # Informatiu: el navegador ho torna a deduir de la mida de la taula, i per
    # això no ho escrivim en cap fitxer. Deduir-ho és més segur que declarar-ho,
    # perquè no es pot desincronitzar quan el diccionari creixi.
    if quants_distints <= 256:
        return "Uint8Array", 1
    if quants_distints <= 65536:
        return "Uint16Array", 2
    return "Uint32Array", 4


def main():
    if not DIRECTORI_COLUMNES.is_dir():
        print(f"ERROR: no hi ha el directori {DIRECTORI_COLUMNES}")
        return 1

    columnes = {}
    for i in COLUMNES:
        cami = DIRECTORI_COLUMNES / f"col_{i}.txt"
        if not cami.exists():
            print(f"ERROR: falta {cami}")
            return 1
        columnes[i] = llegir_columna(cami)

    # Són un sol diccionari partit en columnes: si no van a l'una, la fila 500
    # d'una columna no és la mateixa paraula que la fila 500 d'una altra, i
    # internar-ho només consagraria el desori.
    files = {i: len(v) for i, v in columnes.items()}
    if len(set(files.values())) > 1:
        print("ERROR: les columnes no tenen el mateix nombre de files:")
        for i in COLUMNES:
            print(f"  col_{i}.txt: {files[i]} files")
        return 1

    total_files = files[COLUMNES[0]]
    print(f"Internant {len(COLUMNES)} columnes de {total_files} files:\n")

    for i in COLUMNES:
        if i in COLUMNES_NUMERIQUES:
            taula, indexs = internar_numerica(columnes[i], COLUMNES_NUMERIQUES[i], f"col_{i}.txt")
            if taula is None:
                return 1
        else:
            taula, indexs = internar(columnes[i])

        # Que el que escrivim reconstrueixi exactament el que hem llegit. Si
        # això falla, val més no deixar cap fitxer que deixar-ne un de dolent.
        if [taula[n] for n in indexs] != columnes[i]:
            print(f"ERROR: la col_{i} internada no reconstrueix l'original")
            return 1
        if max(indexs) >= len(taula):
            print(f"ERROR: la col_{i} té un índex fora de la seva taula")
            return 1

        # Sense salt de línia al final, com les col_N.txt d'origen. Si n'hi
        # posàvem un, el navegador, que munta l'array comptant salts de línia,
        # es trobaria amb una fila de més que no existeix.
        cami_taula = DIRECTORI_COLUMNES / f"col_{i}.taula.txt"
        cami_indexs = DIRECTORI_COLUMNES / f"col_{i}.idx.txt"
        cami_taula.write_bytes(b"\n".join(taula))
        cami_indexs.write_bytes(b"\n".join(str(n).encode() for n in indexs))

        nom_tipus, bytes_per_fila = tipus_darray(len(taula))
        abans = (DIRECTORI_COLUMNES / f"col_{i}.txt").stat().st_size
        despres = cami_taula.stat().st_size + cami_indexs.stat().st_size
        memoria = len(taula) * 24 + total_files * bytes_per_fila

        marca = " (numèrica)" if i in COLUMNES_NUMERIQUES else ""
        print(
            f"  col_{i}: {len(taula):>6} valors -> {nom_tipus:<12}"
            f" disc {abans/1048576:5.1f} MB -> {despres/1048576:4.1f} MB"
            f" | memòria ~{memoria/1048576:4.1f} MB{marca}"
        )

    print(
        "\nFet. Recorda passar el generar_versions.py: els fitxers nous han"
        "\nd'entrar al versions.json perquè el navegador els pugui desar a la"
        "\nmemòria cau i sàpiga quan han canviat."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
