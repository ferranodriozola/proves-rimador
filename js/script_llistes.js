const formatarEntrada = ({ paraula, infinitiu, codi, sil, vicc, viq, diec }) => 
    [paraula, infinitiu, codi, sil, vicc, viq, diec];

function compleixFiltres({ paraula = '', codi = '', sil = '' }, numSeleccionat, comenca, incPropis, incPlurals) {
    const silabes = String(sil);

    if (numSeleccionat === '6') {
        if (parseInt(silabes, 10) < 6) return false;
    } else if (numSeleccionat && numSeleccionat !== '0' && silabes !== numSeleccionat) {
        return false;
    }

    if (comenca) {
        const esVocalOH = 'haeiou'.includes(paraula.trim().toLowerCase().charAt(0));
        if (comenca === 'vocal+h' && !esVocalOH) return false;
        if (comenca === 'consonant' && esVocalOH) return false;
    }

    if (incPropis === 'no' && codi.startsWith('NP')) return false;

    if (incPlurals === 'no') {
        const c0 = codi[0], c3 = codi[3], c4 = codi[4];
        if ((c4 === 'P' && (c0 === 'D' || c0 === 'A' || c0 === 'P')) || (c3 === 'P' && c0 === 'N')) {
            return false;
        }
    }

    return true;
}

function actualitzarLlista() {
    const getVal = id => {
        const el = document.getElementById(id);
        return el ? el.value : null;
    };

    const numSeleccionat = getVal('numeroSelector');
    const comenca = getVal('categoriaSelector');
    const incPropis = getVal('nomsPropis');
    const incPlurals = getVal('plurals');

    const dadesFiltrades = window.matches_base.filter(entrada =>
        compleixFiltres(entrada, numSeleccionat, comenca, incPropis, incPlurals)
    );

    window.matches = dadesFiltrades.map(formatarEntrada);
    window.matches_provisionals = [...window.matches];
    window.paraulacerca = window.matches.length > 0 ? window.matches[0] : [0, 0, 0, 0, 0, 0, 0];

    if (typeof actualitzarRimes === 'function') actualitzarRimes();
    if (typeof mostrarTotesLesLlistes === 'function') mostrarTotesLesLlistes();
}

// Gestió de versions de les llistes: igual que el diccionari principal
// (vegeu carregarVersions i llegirFitxerAmbIndexedDB a js/script.js), amb la
// mateixa memòria cau d'IndexedDB i el mateix format de versions (un resum
// sha256 del contingut, no un comptador manual). Es fonen amb VERSIONS_FITXERS
// en lloc de tenir el seu propi mapa perquè és la variable que fa servir
// llegirFitxerAmbIndexedDB per saber si una còpia guardada encara val; les
// claus no es trepitgen amb les del diccionari perquè els noms de fitxer no
// es repeteixen entre tots dos mons.
async function carregarVersionsLlistes() {
    try {
        const resposta = await fetch(`${ARREL}llistes/versions_llistes.json?t=${Date.now()}`);
        const dades = await resposta.json();
        if (!dades.fitxers) throw new Error("versions_llistes.json no porta la llista de fitxers");

        Object.assign(VERSIONS_FITXERS, dades.fitxers);
        console.log("Versions de les llistes carregades correctament:", dades.fitxers);
    } catch (err) {
        // Sense versió de confiança, llegirFitxerAmbIndexedDB no en desa cap
        // còpia i el fitxer es baixa del servidor cada cop (vegeu allà mateix).
        console.error("Error carregant versions_llistes.json: la llista es baixarà sense memòria cau", err);
    }
}

// Si la llista ja s'ha muntat un cop: el botó d'actualitzar i les caselles de
// categoria només s'han de preparar la primera vegada. En un canvi de dialecte
// es torna a cridar el carregarDades, i sense això s'hi enganxaria un segon
// escoltador al botó (dos actualitzarLlista i dos registraUs per clic) i es
// tornarien a marcar totes les caselles, esborrant els filtres de qui mira la
// llista.
let llistaJaMuntada = false;

async function carregarDades(arxiuJson) {
    // Torna a sortir en un canvi de dialecte: la primera vegada ja hi és (el
    // CSS el pinta), però a la segona l'havíem amagat aquí sota.
    const loaderInicial = document.getElementById('loader');
    if (loaderInicial) loaderInicial.style.display = '';

    const loaderText2 = document.getElementById('loader-text2');
    if (loaderText2) loaderText2.textContent = "Carregant fitxer...";

    try {
        await carregarVersionsLlistes();

        const dades = await llegirFitxerAmbIndexedDB(`${ARREL}llistes/${arxiuJson}`, JSON.parse);
        window.matches_base = dades;

        actualitzarLlista();

        if (!llistaJaMuntada) {
            llistaJaMuntada = true;

            const btnActualitza = document.getElementById('actualitzaButton');
            if (btnActualitza) btnActualitza.addEventListener('click', () => {
                actualitzarLlista();

                // Filtrar una llista compta com un dia d'ús per a l'avís
                // periòdic de donatius (avis/avis.js). Va enganxat al clic
                // del botó i no pas dins d'actualitzarLlista() perquè
                // aquesta també es crida en carregar la pàgina (unes línies
                // més amunt), i llavors una simple visita ja comptaria.
                if (window.AvisRimador) window.AvisRimador.registraUs();
            });

            document.querySelectorAll('.clickable-checkbox').forEach(cb => cb.checked = true);
        }
        
        if (typeof mostrarTotesLesLlistes === 'function') mostrarTotesLesLlistes();
        
        const divImpressio = document.querySelector('.impressio');
        if (divImpressio) divImpressio.style.display = 'flex';
        
        const loader = document.getElementById('loader');
        if (loader) loader.style.display = 'none';

    } catch (error) {
        console.error(error);
        const textNombre = document.getElementById('nombre');
        if (textNombre) textNombre.textContent = `Error carregant les dades de ${arxiuJson}`;
        
        const rimaEnllac = document.getElementById('rima_enllac');
        if (rimaEnllac) rimaEnllac.innerHTML = `<ul><li>No s'ha pogut llegir el fitxer ${arxiuJson}.</li></ul>`;
        
        const loader = document.getElementById('loader');
        if (loader) loader.style.display = 'none';
    }
}

// Ser nàufraga depèn de com es parli: qui no rima amb ningú en central pot
// rimar amb algú en valencià, on la a i la e àtones finals no es confonen. Per
// això cada dialecte té la seva llista (vegeu llistes/generar_naufragues.py) i
// el codi va dins del nom del fitxer, com a les columnes de rima: la memòria
// cau d'IndexedDB s'indexa pel nom del fitxer sol (vegeu
// llegirFitxerAmbIndexedDB a js/script.js).
//
// Les altres dues llistes (els mots de 7) encara surten només del central.
const fitxerDeNaufragues = codi => `paraules_naufragues_${codi}.json`;

// Es registra aquí dalt i no pas dins del DOMContentLoaded a posta: el
// js/script.js es llegeix just abans que aquest fitxer i ja hi deixa els clics
// de la tira enganxats, o sigui que entremig hi hauria una escletxa on un clic
// mouria la pastilla sense tornar a llegir la llista.
if (document.body && document.body.dataset.llista === 'naufragues') {
    quanEsCanviaDeDialecte(codi => {
        carregarDades(fitxerDeNaufragues(codi));
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const tipusLlista = document.body.dataset.llista;

    if (tipusLlista === 'naufragues') {
        carregarDades(fitxerDeNaufragues(dialecteActiu));

    } else if (tipusLlista === 'mots_de7_real') {
        carregarDades('mots_de7_real.json');

    } else if (tipusLlista === 'mots_de7_glosa') {
        carregarDades('mots_de7_glosa.json');

    } else {
        console.warn('Tipus de llista desconegut o no definit al data-llista de l\'etiqueta body.');
    }
});