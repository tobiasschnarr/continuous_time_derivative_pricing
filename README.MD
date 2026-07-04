# Continuous-Time Derivative Pricing, 2026

This repository contains the code for the 2026 assignment of the course Continuous-Time Derivative Pricing. If you encounter any questions regarding the setup, please feel free to reach out to me via email.

## Setup

The notebook should be run from the project root. You can set up a virtual environment and install the required dependencies as follows:

**On macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
````

**On Windows:**

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

All results of the assignment are produced within the notebook `analysis.ipynb`. The notebook contains the main analysis, while selected helper functions are stored in separate Python scripts under `src/`.

## Project Structure

```text
ctdp/
├── requirements.txt                                <--- Quickstart to install the necessary dependencies
├── README.md                                       <--- Project overview and setup instructions
├── src/                                            <--- Python source code
│   ├── __init__.py                                 <--- Package marker
│   ├── valuation.py                                <--- Functions for Part 2
│   ├── portfolio_insurance.py                      <--- Functions for Part 3
│   └── utils.py                                    <--- Path helpers and project root
│
├── analysis.ipynb                                  <--- Notebook containing the assignment solutions
│
├── data/                                           <--- Contains ASML and certificate market data
│   ├── asml_express.csv                            <--- Express Plus Certificate, WKN HV4YPG / ISIN DE000HV4YPG2
│   └── asml.csv                                    <--- ASML Holding N.V., WKN A1J4U4 / ISIN NL0010273215
│
├── docs/                                           <--- Reference documents and product specifications
│   ├── FT_de_DE000HV4YPG2.pdf                      <--- Final Terms, WKN HV4YPG / ISIN DE000HV4YPG2
│   └── KID_DE000HV4YPG2.pdf                        <--- Key Information Document, WKN HV4YPG / ISIN DE000HV4YPG2
│
├── svensson_params/                                <--- Contains the Svensson yield-curve parameters
│
├── figs/                                           <--- Figures generated for the poster
└── .gitignore
```
