#!/bin/bash

echo "Iniciant la transcripció en Català Central (ca)..."
pv col_0.txt | src/espeak-ng --ipa -v ca -q -l 100 > col_0_transcripcio_ca.txt

echo "Iniciant la transcripció en Valencià (ca-va)..."
pv col_0.txt | src/espeak-ng --ipa -v ca-va -q -l 100 > col_0_transcripcio_ca_va.txt

echo "Iniciant la transcripció en Català Nord-occidental (ca-nw)..."
pv col_0.txt | src/espeak-ng --ipa -v ca-nw -q -l 100 > col_0_transcripcio_ca_nw.txt

echo "Iniciant la transcripció en Balear (ca-ba)..."
pv col_0.txt | src/espeak-ng --ipa -v ca-ba -q -l 100 > col_0_transcripcio_ca_ba.txt

echo "Calculant les diferències amb col_9.txt..."
diff -u col_9.txt col_0_transcripcio_ca.txt > diferencies.txt

echo "Procés completat amb èxit! Pots revisar 'diferencies.txt' per veure els canvis."