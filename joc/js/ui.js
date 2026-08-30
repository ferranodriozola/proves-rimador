// Tot el que toca el DOM. La resta de moduls no en saben res.

export const el = {};

const NOMS = [
    'pantalla-inici', 'pantalla-config', 'pantalla-joc', 'pantalla-final',
    'pantalla-records', 'pantalla-classificacio',
    'etiqueta-diaria', 'config-titol', 'config-avis', 'config-record', 'config-dialecte',
    'tira-dialectes',
    'opcions-dificultat', 'opcions-temps', 'grup-temps', 'boto-comencar',
    'rellotge', 'punts', 'barra-temps', 'objectiu', 'objectiu-etiqueta',
    'formulari', 'camp', 'toast', 'trobades',
    'resultat-punts', 'resultat-text', 'etiqueta-record', 'resum',
    'boto-compartir', 'boto-repetir', 'trobades-final', 'titol-llista',
    'bloc-classificacio', 'camp-sobrenom', 'boto-enviar-record', 'estat-enviament',
    'records-buit', 'llista-records',
    'classificacio-selector', 'classificacio-estat', 'classificacio-llista', 'classificacio-data',
    'classificacio-subtitol',
    'carregant', 'carregant-text',
];

export function preparar() {
    for (const nom of NOMS) {
        el[aCamell(nom)] = document.getElementById(nom);
    }
}

function aCamell(text) {
    return text.replace(/-([a-z])/g, (_, lletra) => lletra.toUpperCase());
}

// ------------------------------------------------------------- Pantalles

const PANTALLES = ['inici', 'config', 'joc', 'final', 'records', 'classificacio'];

export function mostrarPantalla(nom) {
    for (const pantalla of PANTALLES) {
        el[aCamell(`pantalla-${pantalla}`)].hidden = pantalla !== nom;
    }
    window.scrollTo({ top: 0, behavior: 'instant' });
}

export function mostrarCarregant(visible, text) {
    if (text) el.carregantText.textContent = text;
    el.carregant.hidden = !visible;
}

// Alguns botons (els de l'arc de Sant Martí) porten el text dins d'un <span>.
// Escriure directament a textContent l'esborraria, o sigui que si hi ha span,
// hi escrivim a dins.
export function texteBoto(boto, text) {
    const span = boto.querySelector('span');
    (span || boto).textContent = text;
}

// ---------------------------------------------------------------- Opcions

/**
 * Un grup de botons que fa de radiogroup. Torna una funcio per llegir el valor
 * escollit i una per canviar-lo.
 */
export function grupOpcions(contenidor, atribut, alCanviar) {
    const botons = [...contenidor.querySelectorAll('.opcio')];

    function seleccionar(valor) {
        for (const boto of botons) {
            boto.setAttribute('aria-checked', String(boto.dataset[atribut] === valor));
        }
        if (alCanviar) alCanviar(valor);
    }

    contenidor.addEventListener('click', (esdeveniment) => {
        const boto = esdeveniment.target.closest('.opcio');
        if (boto && !boto.disabled) seleccionar(boto.dataset[atribut]);
    });

    return {
        valor: () => {
            const triat = botons.find((boto) => boto.getAttribute('aria-checked') === 'true');
            return triat ? triat.dataset[atribut] : botons[0].dataset[atribut];
        },
        seleccionar,
        activar: (valor, actiu) => {
            const boto = botons.find((b) => b.dataset[atribut] === valor);
            if (boto) boto.disabled = !actiu;
        },
    };
}

// ------------------------------------------------------ Tira de dialectes

/**
 * La tira per triar el dialecte, com la del cercador (vegeu el DIALECTES de
 * js/components.js). La llista ve de dades/versions.json i ja arriba ordenada:
 * aqui nomes es pinta tal com ve, sense saber quins dialectes hi ha ni com es
 * diuen.
 */
export function pintarTiraDialectes(dialectes, actiu, alTriar) {
    el.tiraDialectes.replaceChildren(
        ...dialectes.map(({ codi, nom }) => {
            const boto = document.createElement('button');
            boto.type = 'button';
            boto.className = 'dialecte';
            boto.dataset.dialecte = codi;
            boto.setAttribute('role', 'radio');
            boto.setAttribute('aria-checked', String(codi === actiu));
            boto.textContent = nom;
            boto.addEventListener('click', () => alTriar(codi));
            return boto;
        })
    );
}

export function marcarDialecte(codi) {
    for (const boto of el.tiraDialectes.querySelectorAll('.dialecte')) {
        boto.setAttribute('aria-checked', String(boto.dataset.dialecte === codi));
    }
}

// ----------------------------------------------------------------- Partida

export function pintarObjectiu(paraula, dificultat) {
    el.objectiu.textContent = paraula;
    el.objectiuEtiqueta.textContent = dificultat === 'dificil'
        ? 'Rimes consonants amb'
        : 'Rimes assonants amb';
}

export function actualitzarPunts(punts) {
    el.punts.textContent = String(punts);
}

export function actualitzarRellotge(segonsRestants, segonsTotals, textFormatat) {
    el.rellotge.textContent = textFormatat;
    const percentatge = Math.max(0, Math.min(100, (segonsRestants / segonsTotals) * 100));
    el.barraTemps.style.width = `${percentatge}%`;

    const alerta = segonsRestants <= 10;
    el.rellotge.classList.toggle('marcador__valor--alerta', alerta);
    el.barraTemps.classList.toggle('barra-temps__interior--alerta', alerta);
}

let temporitzadorToast = null;

export function avisar(text, tipus) {
    el.toast.textContent = text;
    el.toast.className = `toast toast--visible toast--${tipus}`;
    clearTimeout(temporitzadorToast);
    temporitzadorToast = setTimeout(() => {
        el.toast.className = 'toast';
    }, 1200);
}

let temporitzadorAnimacio = null;

export function animarEntrada(tipus) {
    const forma = el.formulari;
    forma.classList.remove('entrada--encert', 'entrada--error');
    // Forcem un reflow perque l'animacio es torni a disparar si es repeteix.
    void forma.offsetWidth;
    forma.classList.add(`entrada--${tipus}`);
    clearTimeout(temporitzadorAnimacio);
    temporitzadorAnimacio = setTimeout(() => {
        forma.classList.remove('entrada--encert', 'entrada--error');
    }, 400);
}

export function afegirTrobada(paraula) {
    const item = document.createElement('li');
    item.textContent = paraula;
    el.trobades.prepend(item);
}

export function buidarPartida() {
    el.trobades.replaceChildren();
    el.toast.className = 'toast';
    el.toast.textContent = '';
    el.camp.value = '';
    el.camp.disabled = false;
    el.formulari.querySelector('button').disabled = false;
}

export function bloquejarEntrada() {
    el.camp.disabled = true;
    el.formulari.querySelector('button').disabled = true;
    el.camp.blur();
}

// ------------------------------------------------------------------- Final

export function pintarFinal({ punts, paraules, objectiu, rimesPossibles, recordNou, record, titolLlista }) {
    el.resultatPunts.textContent = String(punts);
    el.resultatText.textContent = punts === 1 ? 'rima trobada' : 'rimes trobades';
    el.etiquetaRecord.hidden = !recordNou;

    const trobables = `«${objectiu}» tenia ${rimesPossibles.toLocaleString('ca-ES')} rimes possibles.`;
    el.resum.textContent = recordNou || !record
        ? trobables
        : `${trobables} El teu rècord en aquesta modalitat és ${record}.`;

    el.titolLlista.textContent = titolLlista;
    el.titolLlista.hidden = paraules.length === 0;
    el.trobadesFinal.replaceChildren(
        ...paraules.map((paraula) => {
            const item = document.createElement('li');
            item.textContent = paraula;
            return item;
        })
    );
}

// -------------------------------------------------- Noms de les modalitats

const NOM_MODE = { illimitat: 'Il·limitat', diaria: 'Paraula del dia' };
const NOM_DIFICULTAT = { facil: 'Fàcil', dificil: 'Difícil' };
const NOM_TEMPS = { 45: 'Llampec', 60: '1 minut', 90: 'Estàndard', 180: 'Lent' };

// Els noms dels dialectes els diu el versions.json (els escriu el generador a
// partir del NOMS_DE_DIALECTE de generar_dades.py). Aqui nomes se'n guarda una
// copia per poder titular els records sense haver d'anar a buscar-la cada cop.
let nomsDeDialecte = {};

export function recordarNomsDeDialecte(dialectes) {
    nomsDeDialecte = Object.fromEntries(dialectes.map((d) => [d.codi, d.nom]));
}

export function nomDialecte(codi) {
    return nomsDeDialecte[codi] || codi;
}

export function titolModalitat({ mode, dificultat, segons, dialecte }) {
    const parts = [NOM_MODE[mode] || mode, NOM_DIFICULTAT[dificultat] || dificultat];
    if (mode !== 'diaria') parts.push(NOM_TEMPS[segons] || `${segons}s`);
    if (dialecte) parts.push(nomDialecte(dialecte));
    return parts.join(' · ');
}

function filaRecord({ posicio, etiqueta, subtitol, punts, destacada }) {
    const fila = document.createElement('div');
    fila.className = 'fila-record';
    if (posicio && posicio <= 3) fila.classList.add(`fila-record--${posicio}`);
    if (destacada) fila.classList.add('fila-record--jo');

    const nom = document.createElement('div');
    nom.className = 'fila-record__nom';
    if (posicio) {
        const pos = document.createElement('span');
        pos.className = 'fila-record__pos';
        pos.textContent = posicio <= 3 ? ['🥇', '🥈', '🥉'][posicio - 1] : posicio;
        nom.appendChild(pos);
    }
    const text = document.createElement('div');
    text.className = 'fila-record__etiqueta';
    text.textContent = etiqueta;
    if (subtitol) {
        const sub = document.createElement('span');
        sub.className = 'fila-record__sub';
        sub.textContent = subtitol;
        text.appendChild(sub);
    }
    nom.appendChild(text);

    const valor = document.createElement('span');
    valor.className = 'fila-record__punts';
    valor.textContent = punts;

    fila.append(nom, valor);
    return fila;
}

// ------------------------------------------------------- Els meus rècords

export function pintarRecords(records) {
    el.recordsBuit.hidden = records.length > 0;
    el.llistaRecords.hidden = records.length === 0;
    el.llistaRecords.replaceChildren(
        ...records.map((r) => filaRecord({
            etiqueta: titolModalitat(r),
            punts: r.punts,
        }))
    );
}

// ------------------------------------------------------------ Classificació

export function pintarSelectorModalitats(modalitats, actiu, alTriar) {
    el.classificacioSelector.replaceChildren(
        ...modalitats.map(({ clau, titol }) => {
            const boto = document.createElement('button');
            boto.type = 'button';
            boto.className = 'pastilla';
            boto.textContent = titol;
            boto.setAttribute('aria-pressed', String(clau === actiu));
            boto.addEventListener('click', () => alTriar(clau));
            return boto;
        })
    );
}

export function pintarClassificacio(entrades, elMeuSobrenom) {
    el.classificacioLlista.replaceChildren(
        ...entrades.map((e, i) => filaRecord({
            posicio: i + 1,
            etiqueta: e.sobrenom,
            subtitol: e.paraula ? `amb «${e.paraula}»` : '',
            punts: e.punts,
            destacada: elMeuSobrenom && e.sobrenom.toLowerCase() === elMeuSobrenom.toLowerCase(),
        }))
    );
}

export function estatClassificacio(text) {
    el.classificacioEstat.textContent = text || '';
    el.classificacioEstat.hidden = !text;
    if (text) el.classificacioLlista.replaceChildren();
}

export function subtitolClassificacio(text) {
    el.classificacioSubtitol.textContent = text;
}

/** Quina pestanya de la classificació es veu: 'modalitats' o 'diaria'. */
export function marcarPestanya(quina) {
    for (const boto of document.querySelectorAll('.pestanya')) {
        boto.setAttribute('aria-selected', String(boto.dataset.taula === quina));
    }
}

// -------------------------------------------------- Classificació del dia

const MESOS = ['gen.', 'febr.', 'març', 'abr.', 'maig', 'juny',
               'jul.', 'ag.', 'set.', 'oct.', 'nov.', 'des.'];

/** "2026-08-26" -> "26 d'ag." — prou curt per cabre en una pastilla. */
export function diaCurt(dia) {
    const [, mes, numero] = dia.split('-');
    const nom = MESOS[Number(mes) - 1] || mes;
    const de = 'aeiou'.includes(nom[0]) ? "d'" : 'de ';
    return `${Number(numero)} ${de}${nom}`;
}

export function pintarSelectorDies(dies, actiu, alTriar) {
    el.classificacioSelector.replaceChildren(
        ...dies.map((dia) => {
            const boto = document.createElement('button');
            boto.type = 'button';
            boto.className = 'pastilla';
            boto.textContent = diaCurt(dia);
            boto.setAttribute('aria-pressed', String(dia === actiu));
            boto.addEventListener('click', () => alTriar(dia));
            return boto;
        })
    );
}

/**
 * El rànquing d'un dia: la paraula que tocava i una taula per dificultat.
 * Ve del bloc "diaria" de dades/classificacio.json, que munta
 * joc/eines/compilar_classificacio.py.
 */
export function pintarDiaria(bloc, elMeuSobrenom) {
    const trossos = [];

    if (bloc.paraula) {
        const capcalera = document.createElement('p');
        capcalera.className = 'diaria-paraula';
        capcalera.textContent = `La paraula era «${bloc.paraula}»`;
        trossos.push(capcalera);
    }

    for (const dificultat of ['facil', 'dificil']) {
        const entrades = bloc[dificultat];
        if (!entrades || entrades.length === 0) continue;

        const titol = document.createElement('h3');
        titol.className = 'mini-titol mini-titol--taula';
        titol.textContent = NOM_DIFICULTAT[dificultat];
        trossos.push(titol);

        trossos.push(...entrades.map((e, i) => filaRecord({
            posicio: i + 1,
            etiqueta: e.sobrenom,
            punts: e.punts,
            destacada: elMeuSobrenom && e.sobrenom.toLowerCase() === elMeuSobrenom.toLowerCase(),
        })));
    }

    el.classificacioLlista.replaceChildren(...trossos);
}

// ------------------------------------------------ Enviament a la classificació

export function reiniciarEnviament() {
    el.blocClassificacio.hidden = false;
    el.campSobrenom.disabled = false;
    el.botoEnviarRecord.disabled = false;
    el.estatEnviament.textContent = '';
    el.estatEnviament.className = 'estat-enviament';
}

export function estatEnviament(text, tipus) {
    el.estatEnviament.textContent = text;
    el.estatEnviament.className = `estat-enviament${tipus ? ' estat-enviament--' + tipus : ''}`;
}

export function enviamentFet(missatge) {
    el.campSobrenom.disabled = true;
    el.botoEnviarRecord.disabled = true;
    estatEnviament(missatge, 'ok');
}
