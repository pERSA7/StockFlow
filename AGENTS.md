# AGENTS.md

This file provides key developer context and operational guidance for working in `taller-escuela` (StockFlow).

## Setup & Environment
- **Dependencies:** `pip install -r requirements.txt` (Python 3.x, PyQt6, PyMySQL, python-dotenv).
- **Database Configuration:** Copy `.env.example` to `.env` in the root directory and configure MySQL/MariaDB credentials (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`).

## Running & Building
- **Run App:** `python -m paniol` or `python paniol/main.py`
- **Build Executable (cx_Freeze):** `python setup.py build` (generates `StockFlow.exe`)

## Architecture & Code Structure
- **Core Package (`paniol/`):**
  - Entrypoint: `paniol/main.py` / `paniol/__main__.py`
  - UI Framework: PyQt6 widgets in `paniol/widgets/` (Main window: `paniol/widgets/ventana.py`). Global stylesheet: `paniol/style/estilo.qss`.
  - Data / Database: `paniol/data/db_manager.py` (PyMySQL connection manager using `.env`).
  - Assets: `paniol/assets/`
