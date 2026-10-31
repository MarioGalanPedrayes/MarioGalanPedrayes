#!/usr/bin/env sh
set -eu
python -m pip install -r requirements.txt
python -m pygbag --build --ume_block 0 --title "VOIDRUN: SECTOR 9" .
printf '\nBuild terminado. Sirve build/web/ mediante HTTP; no uses file://.\n'
