/*
    El que comparteixen totes les proves de selector de dialecte.

    Aquí hi ha NOMÉS el que no és el disseny: la llista de dialectes, on es
    desa la tria i el rètol que recorda que això és una prova. Cada prova-X.js
    té el seu disseny i res més, perquè la comparació sigui justa: si el que es
    vol decidir és ON va el selector i com s'obre, la llista de dialectes ha de
    ser idèntica a totes.

    IMPORTANT: cap d'aquestes proves canvia la rima de debò. El dialecte que
    se serveix és el `const DIALECTE = 'ca'` de js/script.js, que és una
    constant de mòdul i no es pot tocar des de fora; canviar-la de veritat vol
    dir refer carregarColumnaInternada() perquè torni a baixar la col_3 i la
    col_4 de l'altra carpeta i reindexi. Això és la feina de després: primer
    triem el disseny.

    Els noms hi són en dos nivells (nom + on es parla) perquè és una de les
    coses a decidir: si el subtítol val la pena, els dissenys que no hi caben
    (el <select> natiu) queden descartats tot sols.
*/

// Els quatre primers ja tenen carpeta a dialectes_col/ i rima generada. El
// rossellonès i l'alguerès encara no: hi són per veure com aguanta cada
// disseny amb sis opcions i, sobretot, com ensenya que dues encara no s'hi
// poden triar. Els codis són provisionals (el dia que existeixin, manen les
// carpetes de dialectes_col/, vegeu dialectes() a diccionaris/python/camins.py).
const PROVA_DIALECTES = [
    { codi: 'ca', nom: 'Central',        on: 'Barcelona, Girona, Tarragona', disponible: true  },
    { codi: 'nw', nom: 'Nord-occidental', on: 'Lleida, Tortosa, Andorra',    disponible: true  },
    { codi: 'va', nom: 'Valencià',       on: 'País Valencià',                disponible: true  },
    { codi: 'ba', nom: 'Balear',         on: 'Mallorca, Menorca, Eivissa',   disponible: true  },
    { codi: 'ro', nom: 'Rossellonès',    on: 'Catalunya del Nord',           disponible: false },
    { codi: 'al', nom: 'Alguerès',       on: "l'Alguer",                     disponible: false }
];

// El de sempre, i el que js/script.js serveix mentre no hi hagi selector.
const PROVA_PER_DEFECTE = 'ca';

// Clau pròpia de les proves: no ha de tocar res del lloc de debò, i quan es
// faci la de veritat ja es decidirà si va a localStorage, a la URL (/central)
// o a totes dues bandes.
const PROVA_CLAU = 'prova-dialecte';

function provaTrobaDialecte(codi) {
    return PROVA_DIALECTES.find(d => d.codi === codi) || PROVA_DIALECTES[0];
}

function provaDialecteActual() {
    let desat = null;
    try { desat = localStorage.getItem(PROVA_CLAU); } catch (e) { /* mode privat */ }
    const trobat = PROVA_DIALECTES.find(d => d.codi === desat && d.disponible);
    return trobat ? trobat.codi : PROVA_PER_DEFECTE;
}

function provaDesarDialecte(codi) {
    try { localStorage.setItem(PROVA_CLAU, codi); } catch (e) { /* mode privat */ }
}

/*
    L'avís que apareix en triar. Fa dues feines alhora: confirma la tria (que
    és el que faria el web de debò, encara que sigui refent la cerca) i recorda
    que els resultats que hi ha a sota continuen sent del central. Sense això,
    provar els dissenys enganya: sembla que funcioni.
*/
let provaTemporitzador = null;
function provaAvisar(codi) {
    const dialecte = provaTrobaDialecte(codi);
    let avis = document.getElementById('prova-avis');
    if (!avis) {
        avis = document.createElement('div');
        avis.id = 'prova-avis';
        avis.setAttribute('role', 'status');
        document.body.appendChild(avis);
    }
    avis.innerHTML = 'Ara cercaries en <strong>' + dialecte.nom + '</strong>' +
                     '<span>En aquesta prova la rima encara surt del central.</span>';
    avis.classList.add('vist');
    clearTimeout(provaTemporitzador);
    provaTemporitzador = setTimeout(() => avis.classList.remove('vist'), 3200);
}

/*
    La cinta de sota a l'esquerra. El botó de Ko-fi també viu a baix a
    l'esquerra (vegeu css/boto_ko-fi.scss), per això aquesta va a la dreta;
    a sota de 750px el Ko-fi salta a la dreta i llavors la cinta ja no hi és.
*/
(function cintaDeProva() {
    const quina = document.body.dataset.prova;
    if (!quina) return;
    const cinta = document.createElement('a');
    cinta.id = 'prova-cinta';
    cinta.href = 'index.html';
    cinta.innerHTML = '<strong>Prova ' + quina.toUpperCase() + '</strong> · torna al comparador';
    document.body.appendChild(cinta);
})();

/*
    La llista desplegada, compartida per les proves B, D i F.

    Va aquí i no a cada prova a posta: entre aquelles tres l'única cosa que
    canvia és D'ON penja la llista i què l'obre, que és justament el que s'ha
    de decidir. Si cada una tingués la seva llista acabaríem comparant tipografies.

    La prova A i la C no la fan servir: van amb <select> natiu, que no admet ni
    subtítols ni marques. Que no hi càpiguen és part del que s'ha de veure.
*/
function provaConstruirPanell(codiActual, alTriar) {
    const panell = document.createElement('div');
    panell.className = 'pd-panell';
    panell.setAttribute('role', 'listbox');
    panell.setAttribute('aria-label', 'Dialecte');

    const titol = document.createElement('p');
    titol.className = 'pd-titol';
    titol.textContent = 'En quin català vols que rimi?';
    panell.appendChild(titol);

    const llista = document.createElement('ul');
    llista.className = 'pd-llista';

    PROVA_DIALECTES.forEach(d => {
        const li = document.createElement('li');
        const boto = document.createElement('button');
        boto.type = 'button';
        boto.className = 'pd-opcio' + (d.codi === codiActual ? ' triada' : '');
        boto.dataset.codi = d.codi;
        boto.setAttribute('role', 'option');
        boto.setAttribute('aria-selected', d.codi === codiActual ? 'true' : 'false');
        if (!d.disponible) {
            boto.disabled = true;
            boto.title = 'Encara no hi és: falta la transcripció.';
        }
        boto.innerHTML =
            '<span class="pd-codi">' + d.codi.toUpperCase() + '</span>' +
            '<span class="pd-noms"><strong>' + d.nom + '</strong><small>' + d.on + '</small></span>' +
            (d.disponible ? '<span class="pd-marca" aria-hidden="true">✓</span>'
                          : '<span class="pd-aviat">aviat</span>');
        if (d.disponible) {
            boto.addEventListener('click', () => alTriar(d.codi));
        }
        li.appendChild(boto);
        llista.appendChild(li);
    });

    panell.appendChild(llista);
    return panell;
}

// Marcar la triada sense refer el panell: així no es perd el focus del teclat.
function provaMarcarTriada(panell, codi) {
    panell.querySelectorAll('.pd-opcio').forEach(b => {
        const es = b.dataset.codi === codi;
        b.classList.toggle('triada', es);
        b.setAttribute('aria-selected', es ? 'true' : 'false');
    });
}

/*
    Obrir i tancar un desplegable ancorat (proves B i D).

    És la part avorrida i sempre igual: el botó l'obre, l'Escape i un clic a
    fora el tanquen, les fletxes van d'opció en opció i el Tab no se n'ha de
    poder escapar sense tancar-lo. Que sigui aquí i no a cada prova vol dir que
    B i D es comporten exactament igual i només es distingeixen pel lloc.

    El <select> natiu de les proves A i C tot això ja ho porta de sèrie i no
    demana ni una línia: també és una manera de mesurar què costa cada disseny.
*/
function provaLligarDesplegable(boto, panell) {
    let obert = false;

    function obrir() {
        obert = true;
        panell.classList.add('obert');
        boto.setAttribute('aria-expanded', 'true');
        const triada = panell.querySelector('.pd-opcio.triada') ||
                       panell.querySelector('.pd-opcio:not(:disabled)');
        if (triada) triada.focus();
    }

    function tancar(tornarAlBoto) {
        if (!obert) return;
        obert = false;
        panell.classList.remove('obert');
        boto.setAttribute('aria-expanded', 'false');
        if (tornarAlBoto) boto.focus();
    }

    boto.setAttribute('aria-haspopup', 'listbox');
    boto.setAttribute('aria-expanded', 'false');
    boto.addEventListener('click', e => {
        e.stopPropagation();
        obert ? tancar(true) : obrir();
    });

    panell.addEventListener('click', e => e.stopPropagation());
    document.addEventListener('click', () => tancar(false));

    document.addEventListener('keydown', e => {
        if (!obert) return;
        if (e.key === 'Escape') { e.preventDefault(); tancar(true); return; }
        if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
        e.preventDefault();
        const opcions = Array.from(panell.querySelectorAll('.pd-opcio:not(:disabled)'));
        const ara = opcions.indexOf(document.activeElement);
        const cap = e.key === 'ArrowDown' ? 1 : -1;
        const seguent = (ara + cap + opcions.length) % opcions.length;
        opcions[seguent].focus();
    });

    // Sortir del panell amb el tabulador l'ha de tancar: si no, es queda obert
    // darrere mentre el focus ja és al cercador.
    panell.addEventListener('focusout', () => {
        setTimeout(() => {
            if (obert && !panell.contains(document.activeElement) &&
                document.activeElement !== boto) tancar(false);
        }, 0);
    });

    return { tancar };
}
