// La classificacio (leaderboard): enviar la teva puntuacio i llegir la de tothom.
//
// Funciona igual que el registre de cerques de la web (js/registre.js): el
// navegador fa un POST "no-cors" a un Google Apps Script, que apunta la fila a un
// full de calcul. Despres, joc/eines/compilar_classificacio.py llegeix el full
// publicat en CSV, en fa el rànquing i escriu joc/dades/classificacio.json, que
// es el que es veu a la pantalla de classificacio.
//
// PER POSAR-HO EN MARXA cal omplir aquestes dues constants (mira el README i
// joc/eines/apps_script_classificacio.gs):
const URL_ENVIAMENT = 'https://script.google.com/macros/s/AKfycbz6mXph0DU7jZPKg-EAHSbVPJoFLDgvNbocAGv4HGkruOH_ZoauwNKAxUu3SaRLbxPbzg/exec';
const URL_CLASSIFICACIO = 'dades/classificacio.json';

// S'envia des d'on sigui: de rimador.cat, del repositori de proves i de local.
//
// El registre de cerques de la web no ho fa (vegeu ES_WEB_OFICIAL a
// js/script.js, que nomes deixa passar rimador.cat i rimador.github.io), pero
// aqui es a posta: la classificacio s'ha de poder provar mentre es fa, i un joc
// que no deixa enviar res mentre el proves no es pot provar de veritat.
//
// El preu es que les partides de prova van al full de debo. Qui filtra de debo
// es el compilador (joc/eines/compilar_classificacio.py), que es qui decideix
// que es publica: si un dia hi ha soroll, s'esborra la fila del full o s'afina
// alla, que es on es pot fer sense deixar el joc coix mentre s'hi treballa.


// sobrenom

const LLARG_MIN = 3;
const LLARG_MAX = 16;
const CARACTERS_OK = /^[\p{L}\p{N} _.\-]+$/u;

export function validarSobrenom(text) {
    const net = String(text).trim().replace(/\s+/g, ' ');

    if (net.length < LLARG_MIN) {
        return { ok: false, motiu: `El sobrenom ha de tenir com a mínim ${LLARG_MIN} lletres.` };
    }
    if (net.length > LLARG_MAX) {
        return { ok: false, motiu: `El sobrenom no pot passar de ${LLARG_MAX} lletres.` };
    }
    if (!CARACTERS_OK.test(net)) {
        return { ok: false, motiu: 'Fes servir només lletres, xifres i espais.' };
    }

    // La validacio de debo (les paraules vetades, la desduplicacio) la fa
    // joc/eines/compilar_classificacio.py: aixo d'aqui nomes es per dir-ho de
    // seguida a qui escriu, i no es cap garantia de res.
    return { ok: true, sobrenom: net };
}

export function estaConfigurat() {
    return URL_ENVIAMENT.length > 0;
}

// enviar

function usuariID() {
    let id = null;
    try {
        id = localStorage.getItem('rimador_usuari_id');
        if (!id) {
            id = 'usr_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 7);
            localStorage.setItem('rimador_usuari_id', id);
        }
    } catch (error) {
        id = 'usr_anonim';
    }
    return id;
}

export async function enviarPuntuacio({ sobrenom, mode, dificultat, segons, dialecte, punts, paraula, data }) {
    if (!estaConfigurat()) {
        return { estat: 'sense-backend' };
    }

    const cos = new URLSearchParams();
    cos.append('sobrenom', sobrenom);
    cos.append('mode', mode);
    cos.append('dificultat', dificultat);
    cos.append('segons', String(segons));
    cos.append('dialecte', dialecte);
    cos.append('punts', String(punts));
    cos.append('paraula', paraula || '');
    // El dia de la PARTIDA, que no es el mateix que quan s'envia: qui juga a
    // dos quarts de dotze de la nit i ho envia a les dotze i cinc, envia una
    // paraula del dia d'ahir. El full en guarda les dues dates en columnes
    // diferents (vegeu apps_script_classificacio.gs).
    cos.append('data', data);
    cos.append('usuari', usuariID());

    try {
        await fetch(URL_ENVIAMENT, { method: 'POST', mode: 'no-cors', body: cos });
        return { estat: 'enviat' };
    } catch (error) {
        return { estat: 'error', motiu: error.message };
    }
}

// llegir

let classificacioPromesa = null;

export function carregarClassificacio() {
    if (!classificacioPromesa) {
        // Amb ?t= i prou: el rànquing canvia cada cop que es passa el
        // compilador, sense que canviï cap versió de res. És la mateixa regla
        // que el versions.json (vegeu joc/js/dades.js): el fitxer que diu com
        // estan les coses ara no es pot cachejar mai.
        classificacioPromesa = fetch(`${URL_CLASSIFICACIO}?t=${Date.now()}`)
            .then((resposta) => {
                if (!resposta.ok) throw new Error(`classificacio.json: ${resposta.status}`);
                return resposta.json();
            })
            .catch((error) => {
                classificacioPromesa = null;
                throw error;
            });
    }
    return classificacioPromesa;
}
