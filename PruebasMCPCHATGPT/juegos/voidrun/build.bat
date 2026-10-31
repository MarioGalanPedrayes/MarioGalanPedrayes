@echo off
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
python -m pygbag --build --ume_block 0 --title "VOIDRUN: SECTOR 9" .
if errorlevel 1 exit /b 1
echo Build terminado. Sirve build/web/ mediante HTTP; no uses file://.
