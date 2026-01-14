# Port Manager - Project Tracking

## Project Overview
A web-based GUI application to monitor and manage all processes running on network ports.

## Features
- Display all processes using network ports
- **WebSocket Real-time Updates** - Server pushes updates only when changes occur
- **Kill Tree Feature** - Kills process AND its parent controller to prevent respawn
- **Parent Process Detection** - Shows indicator when process has a controller parent
- **App Type Detection** - Identifies Node.js, React, Next.js, Python, Flask, PHP, MySQL, etc.
- **Filter by App Type** - Filter buttons to show only specific frameworks
- Kill process functionality (using Windows taskkill)
- Connection status indicator (Live/Offline)
- Manual refresh button (fallback)
- Separate sections for System and User processes
- Modern dark theme UI with dark scrollbars

## Tech Stack
- **Backend**: Python Flask with Flask-SocketIO and eventlet
- **Frontend**: HTML, CSS, JavaScript with Socket.IO client
- **Port**: 5000
- **Protocol**: WebSocket (with HTTP fallback)

## Files
- `app.py` - Flask backend with WebSocket + Kill Tree API
- `index.html` - Main HTML structure with filter bar
- `styles.css` - Dark theme styling with Kill Tree button styles
- `script.js` - Frontend logic with WebSocket + handleKillTree
- `requirements.txt` - Python dependencies (flask-socketio, eventlet)
- `start.bat` - Windows startup script
- `PortManager.bat` - Local startup script with dependency installation
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

## Kill Tree Feature (2026-01-14)
- **Problem**: When killing PHP/Node processes, parent `artisan serve` restarts them
- **Solution**: Added "Kill Tree" button that kills BOTH child and parent process
- Detects parent controller processes (php.exe, node.exe, python.exe, etc.)
- Shows orange recycle icon (↻) next to process name when parent detected
- Orange "Kill Tree" button appears instead of red "Kill" button
- Uses `/api/kill-tree/<pid>` endpoint with `/T` flag for tree kill

## WebSocket Implementation (2026-01-14)
- Replaced 2-second polling with WebSocket connection
- Server monitors ports every 2 seconds in background
- Only pushes updates when process list changes (uses MD5 hash comparison)
- Connection status shown in UI (Live/Offline)
- Fallback to REST API if WebSocket fails

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
- [x] WebSocket implementation (no more polling)
- [x] Kill Tree feature (kills parent + child)

## Last Updated
2026-01-14 11:30
