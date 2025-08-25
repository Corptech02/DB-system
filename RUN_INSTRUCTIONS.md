# FMCSA Dashboard - Running Instructions

## Prerequisites
Make sure you have:
1. Python 3.x installed
2. Node.js and npm installed
3. The `all_carriers.json` file (2.2M+ carriers) already downloaded

## Step 1: Start the Backend API Server

Open a **PowerShell** or **Command Prompt** window and run:

```powershell
cd D:\context-engineering-intro
python demo_real_api.py
```

Or if you have python3:
```powershell
cd D:\context-engineering-intro
python3 demo_real_api.py
```

**IMPORTANT**: Keep this terminal open! The API server must be running for the frontend to work.

You should see:
```
============================================================
FMCSA API with REAL DATA
============================================================

Data source: https://data.transportation.gov/resource/az4n-8mr2.json
Starting server on http://localhost:8000
API Documentation: http://localhost:8000/docs

Loading real carrier data...
------------------------------------------------------------
Loading complete dataset (2.2M+ carriers)...
This may take 30-60 seconds...
✓ Loaded 2,200,000+ real carriers from complete dataset!
```

## Step 2: Start the Frontend Dashboard

Open a **SECOND** PowerShell or Command Prompt window (keep the first one running!) and run:

```powershell
cd D:\context-engineering-intro\fmcsa_dashboard
npm run dev
```

You should see:
```
  VITE v4.4.9  ready in XXX ms

  ➜  Local:   http://localhost:3002/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

## Step 3: Open the Dashboard

Open your web browser and go to: **http://localhost:3002**

## How to Use

### Search Features:
1. **USDOT Number Search**: Enter a USDOT number (e.g., "1000003") in the USDOT field
2. **Company Name Search**: Enter a company name or part of it in the Legal Name field
3. **State Filter**: Select a state from the dropdown
4. **Advanced Filters**: Click "Show Advanced Filters" for more options:
   - Operating Status (Active, Inactive, Out of Service)
   - Fleet size (Min/Max Power Units)
   - Driver count (Min/Max Drivers)
   - Safety Rating
   - Hazmat Only checkbox

### Viewing Carrier Details:
- Click the external link icon (↗) in the Actions column to view full carrier profile
- The profile shows:
  - Basic information (address, phone, email)
  - Operating status and fleet size
  - Insurance status and expiration
  - Safety rating and compliance info

### Other Features:
- **Statistics Tab**: View overall statistics and top states
- **Leads Tab**: Find carriers with expiring insurance
- **Export**: Export search results to CSV or Excel

## Troubleshooting

### If search doesn't work:
1. Check that BOTH terminals are running (API server and frontend)
2. Make sure the API server shows "Loaded X carriers" message
3. Check browser console (F12) for any error messages
4. Try refreshing the page (Ctrl+F5)

### If carrier profiles don't open:
1. Make sure you're clicking the external link icon (↗) in the Actions column
2. Check browser console for errors
3. Try a hard refresh (Ctrl+Shift+R)

### If "can't reach this page" error:
1. Make sure you started the frontend server (Step 2)
2. Check that it's running on port 3002
3. Try http://localhost:3002 (not https)

### API Not Responding:
1. Make sure the API server (Step 1) is still running
2. Check the first terminal for any error messages
3. Try restarting the API server

## Stopping the Servers

To stop the servers:
1. Go to each terminal window
2. Press `Ctrl+C` to stop the server
3. Type `Y` if prompted to terminate