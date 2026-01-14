# Port Manager - Project Tracking

## Project Overview
A web-based GUI application to monitor and manage all processes running on network ports.

## Features
- Display all processes using network ports
- **App Type Detection** - Identifies Node.js, React, Next.js, Python, Flask, PHP, MySQL, etc.
- **Filter by App Type** - Filter buttons to show only specific frameworks
- Kill process functionality (using Windows taskkill)
- Real-time auto-refresh (every 2 seconds)
- Manual refresh button
- Separate sections for System and User processes
- Modern dark theme UI with dark scrollbars

## Tech Stack
- **Backend**: Python Flask with psutil
- **Frontend**: HTML, CSS, JavaScript
- **Port**: 5000

## Files
- `app.py` - Flask backend server with app type detection
- `index.html` - Main HTML structure with filter bar
- `styles.css` - Dark theme styling with filter buttons and app badges
- `script.js` - Frontend logic with filter functionality
- `requirements.txt` - Python dependencies
- `start.bat` - Windows startup script
- `PortManager.bat` - Local startup script
- `C:\Users\kshit\Desktop\Port Manager.lnk` - Desktop shortcut with icon

## How to Run
1. Double-click `Port Manager` shortcut on Desktop (runs as admin)
2. Or manually: `python app.py` in this folder

## App Types Detected
- Node.js, React, Next.js, Vue, Angular, Express
- Python, Flask, Django, FastAPI
- PHP, Laravel
- Java, Spring
- .NET
- MySQL, PostgreSQL, MongoDB, Redis
- Nginx, Apache
- Browser processes

## Bug Fixes (2026-01-10)
- Fixed scrollbar styling (dark theme)
- Fixed kill functionality using Windows taskkill /F
- Fixed empty rows issue after killing
- Added desktop admin shortcut with icon
- Added app type filter feature

## Status
- [x] Backend API created
- [x] Frontend UI created
- [x] Real-time updates implemented
- [x] Kill functionality fixed
- [x] System/User process separation
- [x] Dark scrollbars added
- [x] Desktop admin shortcut created
- [x] App type detection added
- [x] Filter by app type added
- [x] Desktop GUI created (port_manager_gui.py)

## Last Updated
2026-01-10 22:50
