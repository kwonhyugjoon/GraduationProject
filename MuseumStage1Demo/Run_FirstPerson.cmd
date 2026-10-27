@echo off
setlocal
set "UE_EDITOR=C:\Program Files\Epic Games\UE_5.7\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
if not exist "%UE_EDITOR%" (
  echo Unreal Engine 5.7 was not found. Edit UE_EDITOR in this file.
  pause
  exit /b 1
)
start "Museum Stage 1" "%UE_EDITOR%" "%~dp0MuseumStage1Demo.uproject" /Game/Stage1/Maps/L_MuseumStage1 -game -windowed -ResX1280 -ResY720 -nosplash
