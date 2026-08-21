/*
    PROVA B · Bombolla amb menú propi, a la capçalera.

    El mateix lloc que la prova A (dins de .header-icons, al costat del peixet
    i del menú) però amb desplegable fet a mà en comptes de <select>. El que es
    guanya és tot el que a l'A no hi cabia: cada dialecte duu a sota on es
    parla, el triat porta marca, i els dos que encara no hi són surten amb un
    "aviat" en lloc de fer veure que és una opció més.

    El botó ensenya el codi de dues lletres en una pastilla i el nom al costat;
    a sota de 550px es queda només el codi, i com que la llista de dins també
    duu el codi (vegeu .pd-codi a comu.css) no cal aprendre res per lligar-los.

    El preu: unes 50 línies de comu.js (provaLligarDesplegable) que el <select>
    de l'A regala.
*/
(function provaB() {
    const icones = document.querySelector('.header-icons');
    if (!icones) return;

    let actual = provaDialecteActual();

    const capsa = document.createElement('div');
    capsa.className = 'pd-b';

    const boto = document.createElement('button');
    boto.type = 'button';
    boto.className = 'pd-b-boto';
    boto.setAttribute('title', 'Tria el dialecte');

    function pintarBoto() {
        const d = provaTrobaDialecte(actual);
        boto.innerHTML =
            '<span class="pd-codi">' + d.codi.toUpperCase() + '</span>' +
            '<span class="pd-b-nom">' + d.nom + '</span>' +
            '<span class="pd-b-fletxa" aria-hidden="true">▾</span>';
        boto.setAttribute('aria-label', 'Dialecte: ' + d.nom + '. Canvia\'l.');
    }
    pintarBoto();

    const panell = provaConstruirPanell(actual, codi => {
        actual = codi;
        provaDesarDialecte(codi);
        provaMarcarTriada(panell, codi);
        pintarBoto();
        provaAvisar(codi);
        desplegable.tancar(true);
    });

    capsa.appendChild(boto);
    capsa.appendChild(panell);
    icones.insertBefore(capsa, icones.firstChild);

    const desplegable = provaLligarDesplegable(boto, panell);
})();
