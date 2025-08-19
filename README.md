# PRO AutoCatcher 

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)  
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)  

A bot to autummatically hunt pokemons in PRO (Pokemon Revolution Online)

NOTE: ONLY TESTED FOR WINDOWS

[//]: # "![Screenshot or GIF](screenshot.png) *(Optional but highly recommended)*"  

---

## **Table of Contents**  
- [PRO AutoCatcher](#pro-autocatcher)
  - [**Table of Contents**](#table-of-contents)
  - [**Features**](#features)
  - [**Installation**](#installation)
    - [**Prerequisites**](#prerequisites)
    - [**Steps**](#steps)
  - [Usage](#usage)
  - [License](#license)


## **Features**  
- Automatically detects Pokemon Names (using OCR)
- Saves the encounters and does statistics
- Automatically Moves from side to side

## **Installation**  
### **Prerequisites**  
- Python 3.12+ ([Download](https://www.python.org/downloads/))  
- (Optional) Git (if cloning the repo)
- Tesseract ([Download Windows](https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe))
   - Just run the default instalation for Tesseract
   - Note: The Bot expects Tesseract to be installed at the default location: 'C:\Program Files\Tesseract-OCR\tesseract.exe'
   - [Github Repo](https://github.com/UB-Mannheim/tesseract/wiki)

### **Steps** 
0. Install all the [**Prerequisites**](#prerequisites)
1. **Clone the repository** (or download the ZIP):  
   ```bash
   git clone https://github.com/balloni7/PROAutoBot.git
   ```
2. Double click the **Installation.bat**
   - NOTE: Virtual environments are RECOMMENDED as they are a way to isolate python "instalations" so they dont interefere with one another ([venv documentation](https://docs.python.org/3/library/venv.html))

## Usage
1. Run the **Installation.bat**
2. Run the **RunCalibrationTool.bat** file and configure the name area
3. Edit the CONFIG.ini values file at your will. The most relevant are the **Movement** ones:  
4. Run the **RunAutoCatcher.bat** to start the bot 
   - After runing the script you need to focus the game window
   - Its recommended that the Windows is almost fully visible, as the bot uses image recognition
   
## License
Distributed under the MIT License. See [LICENSE](LICENSE.md) for details.