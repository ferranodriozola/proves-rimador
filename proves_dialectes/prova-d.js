/*
    PROVA D · Barra pròpia entre la capçalera i la franja rosa.

    L'única de totes que explica què és allò abans que ningú ho demani: en
    comptes d'un control que s'ha de descobrir, hi ha una frase que diu en què
    estàs cercant ("Ara cerques rimes en català central") i, al costat, el botó
    per canviar-ho.

    Això la fa la millor per al dia del llançament, quan ningú no sap encara
    que el rimador té dialectes, i la pitjor sis mesos després, quan tothom ja
    ho sap i la barra continua ocupant una franja sencera de pantalla per dir
    cada dia el mateix.

    El desplegable que s'obre és exactament el de la prova B: el que es compara
    aquí és el lloc i el rètol, no la llista.
*/
(function provaD() {
    const capcalera = document.getElementById('header');
    if (!capcalera) return;

    let actual = provaDialecteActual();

    const barra = document.createElement('div');
    barra.className = 'pd-d';

    const frase = document.createElement('p');
    frase.className = 'pd-d-frase';

    const capsa = document.createElement('div');
    capsa.className = 'pd-d-capsa';

    const boto = document.createElement('button');
    boto.type = 'button';
    boto.className = 'pd-d-boto';
    boto.innerHTML = 'Canvia de dialecte <span aria-hidden="true">▾</span>';

    function pintarFrase() {
        const d = provaTrobaDialecte(actual);
        frase.innerHTML = 'Ara cerques rimes en <strong>català ' +
                          d.nom.toLowerCase() + '</strong>' +
                          '<span class="pd-d-on"> · ' + d.on + '</span>';
    }
    pintarFrase();

    const panell = provaConstruirPanell(actual, codi => {
        actual = codi;
        provaDesarDialecte(codi);
        provaMarcarTriada(panell, codi);
        pintarFrase();
        provaAvisar(codi);
        desplegable.tancar(true);
    });

    capsa.appendChild(boto);
    capsa.appendChild(panell);
    barra.appendChild(frase);
    barra.appendChild(capsa);
    capcalera.insertAdjacentElement('afterend', barra);

    const desplegable = provaLligarDesplegable(boto, panell);
})();
