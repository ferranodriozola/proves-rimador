/*
    PROVA F · Bombolla flotant i panell al mig.

    La única que no ocupa ni un píxel de la maqueta: no s'afegeix cap franja,
    no s'estreny la capçalera i no es toca la franja rosa. La bombolla sura per
    damunt i el panell s'obre centrat, en dues columnes, que és l'única forma
    en què sis dialectes es veuen tots d'un cop sense fer una llista llarga.

    És la que fa més joc amb el lloc: la capçalera ja és un fons de bombolles
    (css/header.scss) i aquesta n'és una que s'ha escapat.

    Els dos peròs són seriosos. Un: el que sura no es descobreix, i qui no hi
    pari atenció no sabrà mai que el rimador té dialectes. Dos: a baix a
    l'esquerra ja hi ha el botó de Ko-fi, i per sota de 750px aquell salta a la
    dreta (css/boto_ko-fi.scss), o sigui que al mòbil s'han de repartir el
    racó. Aquí està arreglat pujant la bombolla, però són dues coses surant a
    la mateixa cantonada.
*/
(function provaF() {
    let actual = provaDialecteActual();

    const bombolla = document.createElement('button');
    bombolla.type = 'button';
    bombolla.id = 'pd-f-bombolla';

    function pintarBombolla() {
        const d = provaTrobaDialecte(actual);
        bombolla.innerHTML = '<span>' + d.codi.toUpperCase() + '</span>';
        bombolla.setAttribute('aria-label', 'Dialecte: ' + d.nom + '. Canvia\'l.');
        bombolla.setAttribute('title', 'Dialecte: ' + d.nom);
    }
    pintarBombolla();

    const fons = document.createElement('div');
    fons.id = 'pd-f-fons';

    const panell = provaConstruirPanell(actual, codi => {
        actual = codi;
        provaDesarDialecte(codi);
        provaMarcarTriada(panell, codi);
        pintarBombolla();
        provaAvisar(codi);
        tancar();
    });
    panell.classList.add('pd-graella');
    fons.appendChild(panell);

    document.body.appendChild(bombolla);
    document.body.appendChild(fons);

    function obrir() {
        fons.classList.add('obert');
        bombolla.setAttribute('aria-expanded', 'true');
        const triada = panell.querySelector('.pd-opcio.triada') ||
                       panell.querySelector('.pd-opcio:not(:disabled)');
        if (triada) triada.focus();
    }

    function tancar() {
        if (!fons.classList.contains('obert')) return;
        fons.classList.remove('obert');
        bombolla.setAttribute('aria-expanded', 'false');
        bombolla.focus();
    }

    bombolla.setAttribute('aria-haspopup', 'dialog');
    bombolla.setAttribute('aria-expanded', 'false');
    bombolla.addEventListener('click', obrir);

    // Clic al fons, però no al panell: el target ha de ser el fons mateix.
    fons.addEventListener('click', e => { if (e.target === fons) tancar(); });

    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') tancar();
    });
})();
