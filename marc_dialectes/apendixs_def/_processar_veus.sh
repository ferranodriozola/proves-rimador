#!/bin/bash

echo "Iniciant la transcripció en Català Central (ca)..."
pv 0ca_x_transc.txt | src/espeak-ng --ipa -v ca -q -l 100 > appendix_ca_transcrit.txt

echo "Iniciant la transcripció en Valencià (ca-va)..."
pv 0va_x_transc.txt | src/espeak-ng --ipa -v ca-va -q -l 100 > appendix_va_transcrit.txt

echo "Iniciant la transcripció en Català Nord-occidental (ca-nw)..."
pv 0ca_x_transc.txt | src/espeak-ng --ipa -v ca-nw -q -l 100 > appendix_nw_transcrit.txt

echo "Iniciant la transcripció en Balear (ca-ba)..."
pv 0ba_x_transc.txt | src/espeak-ng --ipa -v ca-ba -q -l 100 > appendix_ba_transcrit.txt

echo "Procés completat amb èxit!"