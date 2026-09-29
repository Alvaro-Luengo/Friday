@echo off
title Compilando Friday APK (App Nativa de Android)
cd /d "%~dp0android_app"
set "JAVA_HOME=C:\Program Files\Android\Android Studio\jbr"
echo =======================================================
echo     COMPILADOR DE FRIDAY ASSISTANT APK PARA ANDROID
echo =======================================================
echo.
echo [*] Iniciando compilacion Gradle con Java 21 y Android SDK...
call .\gradlew.bat assembleDebug
if %errorlevel% equ 0 (
    copy /Y "app\build\outputs\apk\debug\app-debug.apk" "..\\Friday.apk" >nul
    echo.
    echo =======================================================
    echo   [+] APK GENERADO CON EXITO: D:\Friday\Friday.apk
    echo.
    echo   Para instalarlo en tu POCO X8 Pro Max:
    echo   1. Descargalo directamente desde el enlace de Friday:
    echo      /download/friday.apk
    echo   2. O copialo por USB / Google Drive / Telegram.
    echo =======================================================
) else (
    echo.
    echo [-] Ocurrio un error en la compilacion de Gradle.
)
pause
