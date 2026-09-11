// Banner d'instal·lació de l'aplicació (PWA).
//
// A Chrome, Edge i Samsung, el navegador dispara l'event
// "beforeinstallprompt" quan el lloc compleix els criteris d'instal·lació.
// Aquí el fem servir per ensenyar un bàner discret i, si l'usuari vol,
// llancem el diàleg natiu d'instal·lació.
//
// A iOS Safari no hi ha cap event equivalent: ensenyem unes instruccions
// per fer-ho a mà (compartir > afegir a la pantalla d'inici).
//
// COMPTE AMB QUAN ARRIBA L'EVENT: aquest fitxer va amb defer, o sigui que no
// s'executa fins que l'HTML està analitzat del tot. El Chrome, en canvi,
// dispara el beforeinstallprompt tan bon punt té el manifest i un service
// worker actiu, i en una segona visita això passa MENTRE l'index encara
// s'analitza. L'event es dispara un sol cop: si no hi ha ningú escoltant, es
// perd per sempre i el bàner no surt mai més. Per això cada pàgina el captura
// amb un bocí de <script> al <head> i el desa a window.__rimadorPrompt, i
// aquí el recollim d'allà.
//
// No és cap dialog modal a posta: el diàleg de la nova versió (banner.js)
// i l'avís de donatius (avis.js) ja en fan servir, i apilar-ne un tercer
// seria massa. Aquí és una barra fixa al peu de la pantalla, que no
// interromp res.
(function () {
    'use strict';

    var CLAU = 'rimador_instal_descartat';
    var RETARD_MS = 3000;

    var jo = document.currentScript;
    var ARREL = (jo && jo.src) ? new URL('../../', jo.src).pathname : '/';

    function jaInstalLat() {
        try {
            return window.matchMedia('(display-mode: standalone)').matches
                || window.navigator.standalone === true;
        } catch (e) { return false; }
    }

    function jaDescartat() {
        try { return !!localStorage.getItem(CLAU); } catch (e) { return true; }
    }

    function descartar() {
        try { localStorage.setItem(CLAU, '1'); } catch (e) {}
    }

    if (jaInstalLat()) return;

    function esIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent)
            || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    }

    function esSafariIOS() {
        if (!esIOS()) return false;
        return !/CriOS|FxiOS|OPiOS|EdgiOS/.test(navigator.userAgent);
    }

    // El que hagi pogut capturar el bocí del <head> abans que arribéssim.
    var promptEvent = window.__rimadorPrompt || null;
    var bannerMostrat = false;
    var programat = false;

    // El banner.js i l'avis.js obren <dialog> modals, que deixen inert tot el
    // que hi ha a sota: si traguéssim la barra mentre n'hi ha un d'obert,
    // quedaria darrere la cortina i no s'hi podria tocar. S'espera que es
    // tanqui.
    function quanNoHiHagiDialeg(fer) {
        if (!document.querySelector('dialog[open]')) { fer(); return; }
        var mirador = setInterval(function () {
            if (!document.querySelector('dialog[open]')) {
                clearInterval(mirador);
                fer();
            }
        }, 500);
    }

    function programar(tipus) {
        if (programat || bannerMostrat || jaDescartat() || jaInstalLat()) return;
        programat = true;
        setTimeout(function () {
            quanNoHiHagiDialeg(function () { mostrar(tipus); });
        }, RETARD_MS);
    }

    function mostrar(tipus) {
        if (bannerMostrat || jaDescartat() || jaInstalLat()) return;
        bannerMostrat = true;

        var barra = document.createElement('div');
        barra.className = 'instal-banner';
        barra.setAttribute('role', 'complementary');
        barra.setAttribute('aria-label', "Instal·lar l'aplicació");

        var icona = ARREL + 'assets/icon-192.png';

        if (tipus === 'ios') {
            barra.innerHTML =
                '<button class="instal-tanca" aria-label="Tanca">×</button>'
                + '<div class="instal-contingut">'
                + '<img class="instal-icona" src="' + icona + '" alt="" width="40" height="40">'
                + '<p class="instal-text">Per afegir el <strong>Rimador</strong> a la pantalla d’inici, '
                + 'toca <svg class="instal-share-icona" viewBox="0 0 50 50" aria-hidden="true">'
                + '<path d="M30.3 13.7L25 8.4l-5.3 5.3-1.4-1.4L25 5.6l6.7 6.7z"/>'
                + '<path d="M24 7h2v21h-2z"/>'
                + '<path d="M35 40H15c-1.7 0-3-1.3-3-3V19c0-1.7 1.3-3 3-3h7v2h-7c-.6 0-1 .4-1 1v18c0 .6.4 1 1 1h20c.6 0 1-.4 1-1V19c0-.6-.4-1-1-1h-7v-2h7c1.7 0 3 1.3 3 3v18c0 1.7-1.3 3-3 3z"/>'
                + '</svg> i després <strong>«Afegir a pantalla d’inici»</strong>.</p>'
                + '</div>';
        } else {
            barra.innerHTML =
                '<button class="instal-tanca" aria-label="Tanca">×</button>'
                + '<div class="instal-contingut">'
                + '<img class="instal-icona" src="' + icona + '" alt="" width="40" height="40">'
                + '<p class="instal-text"><strong>Afegeix el Rimador</strong> al teu dispositiu per accedir-hi ràpidament.</p>'
                + '<button class="instal-boto">Instal·la</button>'
                + '</div>';
        }

        document.body.appendChild(barra);

        // El doble requestAnimationFrame és el que deixa el navegador pintar la
        // barra a baix abans de posar-li la classe, que si no no hi ha
        // transició. El setTimeout hi és perquè el rAF no corre a les pestanyes
        // que no es veuen: sense ell, qui canviés de pestanya durant l'espera
        // es trobaria la barra plantada fora de pantalla.
        var mostrada = false;
        function apareix() {
            if (mostrada) return;
            mostrada = true;
            barra.classList.add('instal-visible');
        }
        requestAnimationFrame(function () { requestAnimationFrame(apareix); });
        setTimeout(apareix, 100);

        barra.querySelector('.instal-tanca').addEventListener('click', function () {
            descartar();
            tancar(barra);
        });

        var botoInstal = barra.querySelector('.instal-boto');
        if (botoInstal) {
            // El promptEvent es mira aquí dins i no pas en crear el botó: pot
            // haver arribat després de treure la barra.
            botoInstal.addEventListener('click', function () {
                if (!promptEvent) return;
                promptEvent.prompt();
                promptEvent.userChoice.then(function (result) {
                    if (result.outcome === 'accepted') descartar();
                    tancar(barra);
                    promptEvent = null;
                });
            });
        }
    }

    function tancar(barra) {
        barra.classList.remove('instal-visible');
        barra.addEventListener('transitionend', function () { barra.remove(); }, { once: true });
        setTimeout(function () { if (barra.parentNode) barra.remove(); }, 500);
    }

    // Encara escoltem l'event pel nostre compte: si el lloc compleix els
    // criteris més tard (el service worker s'acaba d'activar, la primera
    // visita), el Chrome el dispara ara i el bocí del <head> ja no hi és sol.
    window.addEventListener('beforeinstallprompt', function (e) {
        e.preventDefault();
        promptEvent = e;
        programar('prompt');
    });

    if (promptEvent) {
        programar('prompt');
    } else if (esSafariIOS()) {
        programar('ios');
    }

    window.addEventListener('appinstalled', function () {
        descartar();
        promptEvent = null;
        var barra = document.querySelector('.instal-banner');
        if (barra) tancar(barra);
    });
})();
