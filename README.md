# NSE Multi-EMA Stock Scanner & Dashboard

A modern, interactive Streamlit web app for advanced stock screening, analytics, and dashboards for Indian markets (NSE/BSE). Scan for high-momentum stocks above key EMAs, visualize price bands, and export results—all with a beautiful, responsive UI.

---

## 🚀 Features

- **Multi-EMA Scanner:**
  - Find stocks trading above 50, 150, and 200-day EMAs.
  - Filter by exchange, volume, and more.
  - Copy tickers by sector/industry, export CSV, and view key metrics.
- **Price Bands Dashboard:**
  - Visualize stocks by price bands with donut charts and metrics.
  - Export band data and see last update times.
- **Results Calendar:**
  - View, filter, and export results by date or criteria.
  - Quick refresh and cache clearing.
- **Stock News:**
  - Fetch latest news from Google Sheets.
  - Manual refresh and auto-update.
- **Modern UI/UX:**
  - Clean, mobile-friendly layout with cards, tabs, and responsive tables.
  - Export buttons, copy-to-clipboard, and interactive widgets.

---

## 📦 Installation

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

---

## 🌐 Deployment

- **Streamlit Cloud:** Just push to GitHub—Streamlit Cloud will auto-install from `requirements.txt`.
- **Other servers:** Use Docker, Heroku, or any Python host supporting Streamlit.

---

## ⚙️ Configuration & Customization
- **Edit scan logic:** See `pages/02_Advanced_Scanner.py` for scanner logic and layout.
- **Add new dashboards:** Create new files in `pages/` and import your data.
- **Change styles:** Edit or add to `style.css` for custom theming.

---

## 📝 Requirements
See [`requirements.txt`](./requirements.txt) for all dependencies. Key packages:
- streamlit
- pandas
- numpy
- plotly
- openpyxl

---

## 🤝 Contributing
Pull requests and feature suggestions are welcome! Please open an issue to discuss your idea.

---

## 📄 License
MIT License. See [LICENSE](./LICENSE) for details.

---

## 📬 Contact
For questions, suggestions, or help, open an issue or contact [your-email@example.com].

---

## 🛠️ Technical Implementation

### 1. **Framework & Architecture**
- **Framework:** Built with [Streamlit](https://streamlit.io/), enabling rapid development of data apps with a focus on interactivity and modern UI.
- **Directory Structure:**
  - `streamlit_app.py` – Main entry point.
  - `pages/` – Contains modular app pages: Advanced Scanner, Price Bands, Results, Stock News, etc.
  - `requirements.txt` – All Python dependencies for reproducible deployment.
  - `style.css` – Custom CSS for advanced theming and layout tweaks.

### 2. **Data Sources & Fetching**
- **Stock Data:**
  - Uses the `tradingview-screener` package to query NSE/BSE stock data via TradingView’s API.
  - Data is fetched with custom SQL-like queries, supporting filtering, sorting, and multi-field selection.
- **Google Sheets:**
  - News and some dashboard data are fetched from public Google Sheets using pandas’ `read_csv` on published CSV links.
- **Caching:**
  - Streamlit’s `@st.cache_data` decorator is used to cache expensive data fetches for improved performance and to minimize API calls.

### 3. **Scanner Logic**
- **Multi-EMA Scan:**
  - Filters stocks trading above 50, 150, and 200-day EMAs.
  - Additional filters for price, volume, and market cap.
  - Computes derived metrics (e.g., percent above EMA, percent from 52W high).
  - Results are grouped by industry and sector for easy copy/export.
- **Results Export:**
  - Results can be exported as CSV using Streamlit’s `st.download_button`.
  - Date parsing and sorting handled with custom helper functions.

### 4. **Visualization & UI**
- **Data Tables:**
  - Uses `st.dataframe` for interactive, scrollable tables with custom column widths and responsive design.
- **Charts:**
  - Donut and box plots are rendered with `plotly.express` for rich, interactive visualizations.
- **Layout:**
  - Responsive two-column layout (parameters/results) on desktop, vertical stacking on mobile.
  - Cards, tabs, and containers organize content for clarity and usability.
  - Custom CSS ensures a modern, clean appearance and fixes for mobile/tablet.
- **Buttons & Interactivity:**
  - Export, refresh, and copy-to-clipboard buttons are contextually placed for usability.
  - All refresh logic uses `st.rerun()` for compatibility with latest Streamlit versions.

### 5. **Deployment & Environment**
- **requirements.txt** lists all dependencies for reproducible setup on Streamlit Cloud or any server.
- **No secrets or API keys** are required for public Google Sheets or TradingView public data.
- **Error Handling:**
  - All data fetches are wrapped in try/except blocks with user-friendly error messages in the UI.

### 6. **Extensibility**
- **Adding Pages:**
  - New dashboards or analytics can be added as new scripts in the `pages/` directory.
- **Custom Styling:**
  - Easily modify or extend `style.css` for branding or layout tweaks.
- **Integration:**
  - Designed for easy integration with new data sources, additional visualizations, or custom logic.

---

**Happy Scanning!**
