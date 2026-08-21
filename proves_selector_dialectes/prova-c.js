/*
    PROVA C · A la franja rosa, a la dreta.

    La franja rosa és l'únic tros del lloc que es queda enganxat a dalt mentre
    es fa scroll (position: sticky a css/container.scss). Posar-hi el selector
    vol dir que en què estàs cercant no marxa mai de la pantalla, ni quan ja
    ets a la meitat de tres-centes rimes. La capçalera, en canvi, se'n va
    amunt i no torna fins que puges del tot.

    L'inconvenient és de qui és la franja: ara hi ha el rètol de novetats, i
    tots dos s'han de repartir 40px d'alçada. Sobre paper hi caben perquè el
    rètol és curt; el dia que en digui una de llarga, es barallaran.

    A sota de 750px la franja deixa de ser sticky (el mateix container.scss),
    i llavors aquest disseny perd justament el que el feia bo.
*/
(function provaC() {
    const franja = document.getElementById('separador_rosa1');
    if (!franja) return;

    const actual = provaDialecteActual();

    const capsa = document.createElement('div');
    capsa.className = 'pd-c';

    const etiqueta = document.createElement('label');
    etiqueta.setAttribute('for', 'pd-c-select');
    etiqueta.textContent = 'Rimes en';

    const selector = document.createElement('select');
    selector.id = 'pd-c-select';
    PROVA_DIALECTES.forEach(d => {
        const opcio = document.createElement('option');
        opcio.value = d.codi;
        opcio.textContent = d.disponible ? d.nom : d.nom + ' (aviat)';
        opcio.disabled = !d.disponible;
        opcio.selected = d.codi === actual;
        selector.appendChild(opcio);
    });

    selector.addEventListener('change', () => {
        provaDesarDialecte(selector.value);
        provaAvisar(selector.value);
    });

    capsa.appendChild(etiqueta);
    capsa.appendChild(selector);
    franja.appendChild(capsa);
})();
