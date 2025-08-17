@echo off
:: Look for venv in standard locations
if exist "%~dp0venv\Scripts\python.exe" (
    echo Found venv - Running with virtual environment...
    call "%~dp0venv\Scripts\activate.bat"
    python "%~dp0PythonScripts\PokemonElementsOCR.py" %*
    pause
) else (
    echo No venv found - Running with system Python...
    python "%~dp0PythonScripts\PokemonElementsOCR.py" %*
    pause
)