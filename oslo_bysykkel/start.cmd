@echo off
rem Wrapper so ".\start up" / ".\start down" works without changing PowerShell's ExecutionPolicy.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0bysykkel.ps1" %*
