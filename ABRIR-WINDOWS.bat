@echo off
chcp 65001 >nul
title Estudio do Cantor (portatil)
cd /d "%~dp0EstudioDoCantor" 2>nul || cd /d "%~dp0"
EstudioDoCantor.exe
if errorlevel 1 pause
