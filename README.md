# NSE Multi-EMA Stock Screener & Dashboard

A comprehensive, production-grade Streamlit web app for advanced stock screening, analytics, and dashboards focused on Indian and global markets (NSE/BSE and beyond). Effortlessly scan for high-momentum stocks above multiple EMAs, visualize price bands, analyze company financials, and export results—all with an intuitive, responsive UI. **Supports cross-asset, cross-exchange, cross-border, and global instrument scanning—including equities, indices, forex, crypto, and more—using TradingView's global data universe.**

---

## 📚 Table of Contents
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Screenshots](#screenshots)
4. [Installation & Quickstart](#installation--quickstart)
5. [Usage Guide](#usage-guide)
6. [Configuration & Customization](#configuration--customization)
7. [Technical Architecture](#technical-architecture)
8. [Developer Guide](#developer-guide)
9. [Advanced Topics](#advanced-topics)
10. [FAQ & Troubleshooting](#faq--troubleshooting)
11. [Contributing](#contributing)
12. [License](#license)
13. [Contact](#contact)

---

## 🏁 Project Overview
NSE Multi-EMA Stock Screener & Dashboard is a robust, extensible platform for:
- **Active traders & investors** seeking momentum stocks using advanced technical filters.
- **Analysts** needing quick, interactive dashboards for Indian and global equities, indices, forex, crypto, and more.
- **Developers** who want a modular, customizable stock analytics toolkit.

**Key Value Propositions:**
- **Global Reach:** Scan all instruments—equities, indices, forex, crypto, ETFs, and more—across all major exchanges and borders using TradingView's global data. No limitations to a single country or asset class.
- No vendor lock-in: 100% open source, no API keys required for core features.
- Modular: Add new dashboards, screens, or data sources with minimal effort.
- Modern UI: Mobile-first, responsive, and highly interactive.

---

## 🚀 Features

### Cross-Asset & Global Scanning
- **All Instruments Supported:**
  - Scan equities, indices, commodities, forex, cryptocurrencies, ETFs, and more.
  - Cross-exchange: NSE, BSE, NYSE, NASDAQ, LSE, crypto exchanges, and many others.
  - Cross-border: Effortlessly scan global markets and compare instruments worldwide.

### Stock Scanners
- **Multi-EMA Scanner:**
  - Find stocks and other instruments trading above 50, 150, and 200-day EMAs.
  - Advanced filters: exchange, volume, price, market cap, sector, asset class, and more.
  - Copy tickers by sector/industry, export CSV, and view key metrics.
- **Custom EMA Scanner:**
  - Define custom EMA periods and thresholds for personalized scans on any instrument.

### Dashboards & Analytics
- **Price Bands Dashboard:**
  - Visualize stocks and instruments by price bands with interactive donut charts and metrics.
  - Export band data and see last update times.
- **Company Financials:**
  - Deep-dive into financials, ratios, and performance for any listed company.
- **Results Calendar:**
  - View, filter, and export scan results by date or criteria.
  - Quick refresh and cache clearing.
- **Stock News:**
  - Fetch latest news from Google Sheets.
  - Manual refresh and auto-update.

### UI/UX & Interactivity
- Modern, mobile-friendly layout with cards, tabs, and responsive tables.
- Export buttons, copy-to-clipboard, and interactive widgets.
- Customizable themes via CSS.

### Extensibility
- Add new dashboards, custom logic, or styling with ease.
- Modular directory structure for easy feature addition.

---

## 📸 Screenshots

> _Add screenshots or GIFs of the app here for visual reference._

---

## 📦 Installation & Quickstart

### Prerequisites
- **Python 3.8+** (Recommended: 3.10+)
- **pip** (Python package manager)
- OS: Windows, macOS, or Linux
- Browser: Chrome, Firefox, or Edge (latest)

### Steps
1. **Clone this repository:**
   ```bash
   git clone https://github.com/yourusername/globallivescanning.github.io.git
   cd globallivescanning.github.io
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the app locally:**
   ```bash
   streamlit run streamlit_app.py
   ```

#### Troubleshooting
- If you encounter `ModuleNotFoundError`, ensure you're in the correct directory and using the right Python environment.
- For Playwright-related errors, run: `playwright install` after pip install.
- For port conflicts, use `streamlit run streamlit_app.py --server.port 8502`.

---

## 🧑‍💻 Usage Guide

### 1. Cross-Asset, Cross-Exchange Scanning
- Select any asset class (stocks, indices, forex, crypto, etc.) and any exchange or region.
- Define scan parameters and filters (EMA, price, volume, sector, etc.).
- Run the scan to get results from across the globe in one unified dashboard.

### 2. Multi-EMA Scanner
- Navigate to **Advanced Scanner**.
- Select desired EMAs, filters, and run the scan.
- View results, copy tickers, or export to CSV.

### 3. Custom EMA Scanner
- Go to **Custom EMA Scanner**.
- Define your own EMA periods and thresholds.
- Run and analyze results interactively.

### 4. Price Bands & Financials
- Explore **Price Bands** for visual analytics.
- Dive into **Company Financials** for detailed metrics.

### 5. News & Calendar
- Check **Stock News** for latest updates.
- Use **Results Calendar** to review results date

### 6. Mobile/Tablet Usage
- The app is fully responsive. For best experience, use in landscape mode on mobile.

---

## ⚙️ Configuration & Customization

### Editing Scan Logic
- Main scanner logic: `pages/02_Advanced_Scanner.py`
- Custom EMA logic: `pages/03_Custom_EMA_Scanner.py`
- Add new dashboards: Create Python scripts in `pages/`

### Styling
- Modify `style.css` for colors, layout, and branding.
- Example: Change `--primary-color` in `:root` for a new theme.

### Data Sources
- **TradingView Screener:** Powers cross-asset, cross-exchange, global scanning with SQL-like queries for all instrument types.
- **Google Sheets:** News/dashboard data fetched as CSV via pandas.

### Caching
- Uses Streamlit’s `@st.cache_data` for fast reloads and reduced API calls.

---

## 🏗️ Technical Architecture

```
+-------------------+
|  User Interface   |
|  (Streamlit App)  |
+-------------------+
          |
          v
+---------------------------+
|      App Logic (Python)   |
| - Scanner modules         |
| - Data processing         |
| - Visualization           |
+---------------------------+
          |
          v
+-------------------------------+
|   Data Sources & APIs         |
| - TradingView Screener (NSE,  |
|   global, crypto, forex, etc) |
| - Google Sheets (news, etc.)  |
+-------------------------------+
```

- **Directory Structure:**
  - `streamlit_app.py` – Main entry point.
  - `pages/` – Modular app pages: Advanced Scanner, Custom EMA, Price Bands, Financials, News, etc.
  - `requirements.txt` – All Python dependencies.
  - `style.css` – Custom CSS for UI/UX.

- **Main Dependencies:**
  - `streamlit`, `tradingview-screener`, `pandas`, `numpy`, `plotly`, `openpyxl`, `beautifulsoup4`, `playwright`, `flask`, `werkzeug`, `requests`, `scikit-learn`, `tqdm`

- **Security:**
  - No secrets or API keys required for public data sources.
  - All data fetches are wrapped in `try/except` with user-friendly error messages.

---

## 👩‍💻 Developer Guide

### Coding Standards
- Follow PEP8 for Python code.
- Use descriptive variable/function names.
- Add docstrings to all public functions.

### Linting & Testing
- Lint: `ruff .`
- Test: `pytest`
- Type-check: `pyright`

### Adding Features
- New dashboards: Add scripts to `pages/` and update navigation if needed.
- New data sources: Integrate in a modular way (see `utils.py` for helpers).

### Branching & PRs
- Use feature branches for new features.
- Open PRs with clear descriptions and reference related issues.

---

## ⚡ Advanced Topics

### Performance Tuning
- Use caching for expensive API/data calls.
- Optimize pandas operations for large datasets.
- Monitor Streamlit resource usage on cloud deployments.

### Deployment
- **Streamlit Cloud:** Push to GitHub and connect repo.
- **Docker:** Use a Dockerfile for containerized deployment.
- **Heroku/Other:** Ensure all dependencies in `requirements.txt`.

### Integrating New APIs
- Use `requests` or custom modules for new data sources.
- Always wrap fetches in `try/except` and provide user feedback.

---

## ❓ FAQ & Troubleshooting

**Q: Can I scan instruments outside India?**
A: Yes! The app supports global, cross-asset, cross-exchange scanning for all instrument types—equities, forex, crypto, indices, and more.

**Q: Why do I get a ModuleNotFoundError?**
A: Ensure you have installed all dependencies with `pip install -r requirements.txt` and are using the correct Python environment.

**Q: Data not updating?**
A: Try clearing Streamlit cache or restarting the app. Check your internet connection.

**Q: Playwright errors?**
A: Run `playwright install` after installing requirements.

**Q: How to add a new scan or dashboard?**
A: Create a new script in `pages/`, following the structure of existing modules.

---

## 🤝 Contributing

Pull requests, issues, and feature suggestions are welcome! Please open an issue to discuss your ideas or submit a PR. See [Developer Guide](#developer-guide) for more.

---

## 📄 License

MIT License. See [LICENSE](./LICENSE) for details.

---

## 📬 Contact

For questions, suggestions, or help, open an issue or contact [your-email@example.com].

---

**Happy Scanning!**
