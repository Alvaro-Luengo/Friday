' Script para iniciar Friday de forma 100% invisible y silenciosa
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\Friday"
WshShell.Run "cmd.exe /c pythonw main.py", 0, False
