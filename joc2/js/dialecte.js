// Quin dialecte es juga.
//
// Funciona igual que la tira del cercador (vegeu dialecteInicial i
// lligarTriaDeDialecte a js/script.js) i COMPARTEIX LA MATEIXA CLAU del
// localStorage: qui hagi triat el valencia al cercador, es troba el joc en
// valencia sense haver de tornar-ho a dir. Es l'unic estat que comparteixen les
// dues meitats del lloc, a banda de l'identificador d'usuari.
//
// Els codis que valen no es declaren aqui: surten de dades/versions.json, que
// els escriu el generador a partir de les carpetes de dialectes_col/. Aixi el
// joc no pot oferir un dialecte del qual no tingui les dades.

const CLAU_DIALECTE = 'rimadorDialecte';

// El de sempre: l'unic amb la transcripcio repassada a ma (els altres surten de
// l'espeak-ng) i el que es dona a qui no ha triat mai res. Es el CENTRAL de
// diccionaris/python/camins.py.
export const DIALECTE_PER_DEFECTE = 'ca';

/**
 * El dialecte demanat per l'adreca: rimador.cat/joc/?d=ba
 *
 * Hi mana per damunt del que hi hagi desat, com al cercador: aixi un resultat
 * compartit ensenya el mateix a qui el rep. Un codi que no existeix s'ignora.
 */
function delAdreca(codis) {
    const demanat = new URLSearchParams(window.location.search).get('d');
    return codis.includes(demanat) ? demanat : null;
}

/**
 * D'on surt el dialecte de la visita, per ordre: l'adreca, el que hi havia
 * desat, i el central.
 *
 * El de l'adreca NO es desa (vegeu desar): obrir l'enllac que t'ha passat algu
 * val per a aquella visita i no t'ha de canviar el dialecte de sempre.
 */
export function inicial(codis) {
    const demanat = delAdreca(codis);
    if (demanat) return demanat;

    try {
        const desat = localStorage.getItem(CLAU_DIALECTE);
        if (codis.includes(desat)) return desat;
    } catch (error) {
        // Mode privat o cookies barrades: s'agafa el de sempre.
    }

    return codis.includes(DIALECTE_PER_DEFECTE) ? DIALECTE_PER_DEFECTE : codis[0];
}

/** Nomes ho crida la tira: la memoria ha de guardar el que algu ha triat. */
export function desar(codi) {
    try {
        localStorage.setItem(CLAU_DIALECTE, codi);
    } catch (error) {
        // Sense memoria, el dialecte val nomes per a aquesta visita.
    }
}

/**
 * Deixar el dialecte a la barra d'adreces, perque el que es veu i el que diu
 * l'adreca no es desdiguin i perque l'enllac es pugui compartir.
 *
 * replaceState i no pas pushState, com al cercador: triar un dialecte no es
 * anar a cap altra pagina i el boto d'enrere no hi ha de passar.
 */
export function escriureALAdreca(codi) {
    try {
        const adreca = new URL(window.location.href);
        adreca.searchParams.set('d', codi);
        window.history.replaceState(null, '', adreca);
    } catch (error) {
        // Si el navegador no ho deixa fer, tant se val: es cosmetic.
    }
}
