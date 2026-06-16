# Continuous-Time Derivative Pricing, 2026

This repository contains the code for the 2026 assignment of the course Continuous-Time Derivative Pricing. If you encounter any questions regarding the setup, please feel free to reach out to me via email at X. 

## Setup

You can set up a virtual environment and install the required dependencies as follows:

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

```

**On Windows:**

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

```

All results of the assignment are produced within the notebook `analysis.ipynb`. The code is fully commented to ensure a better understanding of the applied logic and navigation. Specific helper functions are written in a separate Python script and stored under `src/`.

## Project Structure

```text
ctdp/                                   
├── requirements.txt                                <--- Quickstart to install necessary dependencies
├── README.md                                       <--- Project overview and quickstart
├── src/                                            <--- Python source code
│   ├── __init__.py                                 <--- Package marker
│   └── utils.py                                    <--- Path helpers and project root
│
├── analysis.ipynb                                  <--- Notebook containing the solutions to the tasks                     
│
├── data/                                           <--- Contains the stock data
│   ├── asml_express.csv                            <--- WKN HV4Z9V / ISIN DE000HV4Z9V9
│   └── asml.csv                                    <--- WKN A1J4U4 / ISIN NL0010273215
│
├── svensson_params/                                <--- Contains the Svensson parameters
│
├── figs/                                           <--- Figures used within the poster                              
└── .gitignore                                      

```
