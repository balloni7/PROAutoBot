@echo off
choice /c yn /m "Create virtual environment? (y/n)"
if %errorlevel%==1 (
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    echo Virtual env setup complete!
) else (
    pip install -r requirements.txt
    echo Requirements installed globally.
)
pause