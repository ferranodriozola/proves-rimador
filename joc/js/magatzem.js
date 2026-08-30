// Tot el que el joc recorda entre partides: els records de cada modalitat i si
// avui ja s'ha jugat la paraula del dia.
//
// Si el localStorage no hi es (navegacio privada, cookies bloquejades) el joc ha
// de seguir funcionant igual; simplement no es recorda res.

const CLAU_RECORDS = 'rimador.joc.records.v2';
const CLAU_RECORDS_V1 = 'rimador.joc.records.v1';
const CLAU_DIARIA = 'rimador.joc.diaria.v2';
const CLAU_SOBRENOM = 'rimador.joc.sobrenom.v1';

// El dialecte que tenien els records d'abans que se'n pogues triar cap. Fa
// falta per a la migracio de sota i per a les modalitats velles que arriben de
// la classificacio sense dialecte.
export const DIALECTE_ANTIC = 'ca';

function llegir(clau) {
    try {
        const cru = localStorage.getItem(clau);
        return cru ? JSON.parse(cru) : null;
    } catch (error) {
        return null;
    }
}

function desar(clau, valor) {
    try {
        localStorage.setItem(clau, JSON.stringify(valor));
        return true;
    } catch (error) {
        return false;
    }
}

/** La data d'avui en horari local, en format AAAA-MM-DD. */
export function avui() {
    const ara = new Date();
    const mes = String(ara.getMonth() + 1).padStart(2, '0');
    const dia = String(ara.getDate()).padStart(2, '0');
    return `${ara.getFullYear()}-${mes}-${dia}`;
}

// --------------------------------------------------------------- Records

// Els records van per mode, dificultat, rellotge i dialecte: no es el mateix
// trobar rimes en 45 segons que en 3 minuts, ni en central que en valencia (son
// paraules diferents i grups de rima diferents).
export function identificadorRecord({ mode, dificultat, segons, dialecte }) {
    return `${mode}|${dificultat}|${segons}|${dialecte}`;
}

// Els records de quan el joc nomes es jugava en central no duien el dialecte a
// l'identificador. Se'ls hi posa el central, que es el que eren, en lloc de
// deixar-los com a modalitats fantasma que no es podrien igualar mai. Nomes es
// fa un cop: despres de copiar-los, la clau v1 s'esborra.
function migrarRecords() {
    const antics = llegir(CLAU_RECORDS_V1);
    if (!antics) return;

    const records = llegir(CLAU_RECORDS) || {};
    for (const [id, punts] of Object.entries(antics)) {
        // Les que ja duen dialecte no s'han de tocar; les de tres trossos, si.
        const identificador = id.split('|').length === 3 ? `${id}|${DIALECTE_ANTIC}` : id;
        if (!(Number(records[identificador]) >= Number(punts))) {
            records[identificador] = Number(punts);
        }
    }
    if (desar(CLAU_RECORDS, records)) {
        try {
            localStorage.removeItem(CLAU_RECORDS_V1);
        } catch (error) {
            // Si no es pot esborrar, la propera migracio nomes tornara a
            // copiar el mateix: es idempotent i no fa cap mal.
        }
    }
}

migrarRecords();

export function llegirRecord(identificador) {
    const records = llegir(CLAU_RECORDS) || {};
    return Number(records[identificador]) || 0;
}

/** Desa la puntuacio si supera l'anterior. Torna true si es record nou. */
export function desarRecord(identificador, punts) {
    const records = llegir(CLAU_RECORDS) || {};
    const anterior = Number(records[identificador]) || 0;
    if (punts <= anterior) return false;
    records[identificador] = punts;
    desar(CLAU_RECORDS, records);
    return true;
}

/**
 * Tots els records desats, ja desxifrats de l'identificador
 * "mode|dificultat|segons|dialecte". Ordenats de mes punts a menys.
 */
export function llegirTotsElsRecords() {
    const records = llegir(CLAU_RECORDS) || {};
    return Object.entries(records)
        .map(([id, punts]) => {
            const [mode, dificultat, segons, dialecte] = id.split('|');
            return {
                mode, dificultat,
                segons: Number(segons),
                dialecte: dialecte || DIALECTE_ANTIC,
                punts: Number(punts),
            };
        })
        .filter((r) => r.punts > 0)
        .sort((a, b) => b.punts - a.punts);
}

// --------------------------------------------------- Paraula del dia

// Nomes guardem el dia d'avui: si canvia la data, l'entrada vella se substitueix
// i el magatzem no creix mai.
//
// El bloqueig va per dialecte, no nomes per dificultat. Cada dialecte te la seva
// paraula del dia (vegeu clauDelDia a objectius.js), o sigui que bloquejar-los
// tots alhora seria barrar-li a algu una paraula que no ha vist mai.
function partidesDelDia(data) {
    const desat = llegir(CLAU_DIARIA);
    return desat && desat.data === data ? desat.partides || {} : {};
}

function clauDiaria(dialecte, dificultat) {
    return `${dialecte}|${dificultat}`;
}

/** El resultat d'avui en un dialecte i dificultat, o null si no s'ha jugat. */
export function resultatDiari(data, dialecte, dificultat) {
    return partidesDelDia(data)[clauDiaria(dialecte, dificultat)] || null;
}

/** Quines dificultats s'han jugat avui EN AQUEST dialecte. */
export function dificultatsJugades(data, dialecte) {
    return Object.keys(partidesDelDia(data))
        .filter((clau) => clau.startsWith(`${dialecte}|`))
        .map((clau) => clau.split('|')[1]);
}

export function desarResultatDiari(data, dialecte, dificultat, resultat) {
    const partides = partidesDelDia(data);
    partides[clauDiaria(dialecte, dificultat)] = resultat;
    desar(CLAU_DIARIA, { data, partides });
}

// ------------------------------------------------------------- Sobrenom

export function llegirSobrenom() {
    return llegir(CLAU_SOBRENOM) || '';
}

export function desarSobrenom(sobrenom) {
    desar(CLAU_SOBRENOM, sobrenom);
}
