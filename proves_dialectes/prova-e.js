/*
    PROVA E · Pastilles, sense cap desplegable.

    Aquesta hi és per contrast: no era el que demanaves, però val la pena
    veure-la al costat de les altres abans de descartar-la. Els sis dialectes
    hi són tots alhora, i triar-ne un és un sol clic en comptes de dos.

    El que es guanya és que la funció no s'ha de descobrir: qui entri al lloc
    veurà que hi ha dialectes encara que no els busqui. El que es perd és que
    això no creix: amb sis ja va just a l'ample d'un portàtil, i a mòbil s'ha
    de fer una tira que llisca de costat, que és justament el patró on la gent
    no arriba mai a l'última opció.

    O sigui que si algun dia n'hi ha set, aquest disseny s'ha de refer. Els
    desplegables (A, B, C, D, F) no.
*/
(function provaE() {
    const capcalera = document.getElementById('header');
    if (!capcalera) return;

    let actual = provaDialecteActual();

    const tira = document.createElement('div');
    tira.className = 'pd-e';
    tira.setAttribute('role', 'radiogroup');
    tira.setAttribute('aria-label', 'Dialecte');

    const rotul = document.createElement('span');
    rotul.className = 'pd-e-rotul';
    rotul.textContent = 'Rimes en';
    tira.appendChild(rotul);

    const pastilles = document.createElement('div');
    pastilles.className = 'pd-e-pastilles';

    PROVA_DIALECTES.forEach(d => {
        const boto = document.createElement('button');
        boto.type = 'button';
        boto.className = 'pd-e-pastilla' + (d.codi === actual ? ' triada' : '');
        boto.dataset.codi = d.codi;
        boto.setAttribute('role', 'radio');
        boto.setAttribute('aria-checked', d.codi === actual ? 'true' : 'false');
        boto.innerHTML = d.nom + (d.disponible ? '' : ' <span class="pd-e-aviat">aviat</span>');
        if (!d.disponible) {
            boto.disabled = true;
            boto.title = 'Encara no hi és: falta la transcripció.';
        } else {
            boto.addEventListener('click', () => {
                actual = d.codi;
                provaDesarDialecte(d.codi);
                pastilles.querySelectorAll('.pd-e-pastilla').forEach(b => {
                    const es = b.dataset.codi === d.codi;
                    b.classList.toggle('triada', es);
                    b.setAttribute('aria-checked', es ? 'true' : 'false');
                });
                provaAvisar(d.codi);
            });
        }
        pastilles.appendChild(boto);
    });

    tira.appendChild(pastilles);
    capcalera.insertAdjacentElement('afterend', tira);
})();
