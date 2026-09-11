// Banner d'instal·lació de l'aplicació (PWA).
//
// A Chrome, Edge i Samsung, el navegador dispara l'event
// "beforeinstallprompt" quan el lloc compleix els criteris d'instal·lació.
// Aquí el capturem, ensenyem un bàner discret i, si l'usuari vol,
// llancem el diàleg natiu d'instal·lació.
//
// A iOS Safari no hi ha cap event equivalent: ensenyem unes instruccions
// per fer-ho a mà (compartir > afegir a la pantalla d'inici).
//
// No és cap dialog modal a posta: el diàleg de la nova versió (banner.js)
// i l'avís de donatius (avis.js) ja en fan servir, i apilar-ne un tercer
// seria massa. Aquí és una barra fixa al peu de la pantalla, que no
// interromp res.
(function () {
    'use strict';

    var CLAU = 'rimador_instal_descartat';
    var RETARD_MS = 4000;

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

    var promptEvent = null;
    var bannerMostrat = false;

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

        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                barra.classList.add('instal-visible');
            });
        });

        barra.querySelector('.instal-tanca').addEventListener('click', function () {
            descartar();
            tancar(barra);
        });

        var botoInstal = barra.querySelector('.instal-boto');
        if (botoInstal && promptEvent) {
            botoInstal.addEventListener('click', function () {
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

    window.addEventListener('beforeinstallprompt', function (e) {
        e.preventDefault();
        promptEvent = e;
        if (!jaDescartat()) {
            setTimeout(function () { mostrar('prompt'); }, RETARD_MS);
        }
    });

    if (esSafariIOS()) {
        window.addEventListener('load', function () {
            setTimeout(function () { mostrar('ios'); }, RETARD_MS);
        });
    }

    window.addEventListener('appinstalled', function () {
        descartar();
        var barra = document.querySelector('.instal-banner');
        if (barra) tancar(barra);
    });
})();
