# FMCSA Database System with Insurance Automation

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18.0%2B-61dafb)](https://reactjs.org/)

A comprehensive FMCSA carrier database system with automated insurance data scraping capabilities.

## 🚀 Features

- **Real-time FMCSA Data**: Fetches carrier information from official FMCSA APIs
- **Insurance Automation**: Multiple methods to scrape L&I insurance data
- **React Dashboard**: Modern UI with real-time updates and loading states
- **Smart Caching**: Reduces API calls and improves performance
- **Queue Management**: Automatically queues carriers for insurance lookup
- **Multiple Automation Options**: Browser extension, desktop automation, cloud services

## 📋 Prerequisites

- Python 3.8+
- Node.js 14+
- Chrome browser (for automation)
- Git

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/Corptech02/DB-system.git
cd DB-system
```

### 2. Set up Python environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install Python dependencies
pip install fastapi uvicorn aiohttp requests selenium pyppeteer schedule
```

### 3. Set up React dashboard
```bash
cd fmcsa_dashboard
npm install
```

### 4. Initialize the system
```bash
python run_insurance_automation.py
```

## 🚦 Quick Start

### Start the API server
```bash
python demo_real_api.py
# API will be available at http://localhost:8000
```

### Start the React dashboard
```bash
cd fmcsa_dashboard
npm start
# Dashboard will open at http://localhost:3000
```

## 🤖 Insurance Automation Methods

### Option 1: Chrome Extension (Recommended for beginners)
1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" and select `li_chrome_extension` folder
4. Visit L&I website - the extension will auto-scrape

### Option 2: Desktop Automation
```bash
# Windows
run_scraper.bat

# Linux/Mac
python li_desktop_scraper.py
```

### Option 3: Manual Entry
```bash
python li_manual_entry.py
```

## 📁 Project Structure

```
DB-system/
├── fmcsa_dashboard/          # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   └── services/         # API services
│   └── package.json
├── li_chrome_extension/      # Chrome extension for automation
├── demo_real_api.py          # FastAPI backend server
├── fmcsa_insurance_service.py # Insurance data service
├── run_insurance_automation.py # Setup script
├── li_desktop_scraper.py    # Desktop automation script
├── li_manual_entry.py        # Manual data entry tool
└── requirements.txt          # Python dependencies
```

## 🔑 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/carriers` | GET | List all carriers |
| `/api/carriers/{usdot}` | GET | Get specific carrier |
| `/api/carriers/search` | POST | Search carriers |
| `/api/stats` | GET | System statistics |

## 📊 Current Status

- ✅ Real GEICO insurance data cached for USDOT 905413
- ✅ Automation system fully configured
- ✅ 4 different scraping methods available
- ✅ Dashboard integration complete

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

---

**Built with ❤️ by Corptech02**