@echo off

:: Virtual environment management
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

:: Check for existing config
if exist "CONFIG.ini" (
    echo Config file already exists, skipping creation.
) else (
    echo Creating default config file...
    python -c "import sys; sys.path.append('PythonScripts'); from ConfigHandler import ConfigHandler; ConfigHandler('CONFIG.ini').generate_default_config_file()"
    if exist "CONFIG.ini" (
        echo Default config.ini created in PythonScripts folder
    ) else (
        echo Failed to create config file!
    )
)

pause

