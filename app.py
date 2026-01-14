"""
Port Manager - Flask Backend
Monitors all processes running on network ports and provides kill functionality.
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import psutil
import os
import ctypes

app = Flask(__name__, static_folder='.')
CORS(app)

# System process names (common Windows system processes)
SYSTEM_PROCESSES = {
    'system', 'svchost.exe', 'services.exe', 'lsass.exe', 'csrss.exe',
    'wininit.exe', 'winlogon.exe', 'smss.exe', 'dwm.exe', 'explorer.exe',
    'spoolsv.exe', 'searchindexer.exe', 'msdtc.exe', 'fontdrvhost.exe',
    'registry', 'memory compression', 'ntoskrnl.exe', 'audiodg.exe',
    'conhost.exe', 'dllhost.exe', 'sihost.exe', 'taskhostw.exe',
    'runtimebroker.exe', 'shellexperiencehost.exe', 'startmenuexperiencehost.exe',
    'ctfmon.exe', 'securityhealthservice.exe', 'sgrmbroker.exe',
    'microsoftedgeupdate.exe', 'wmiprvse.exe', 'wudfhost.exe'
}

def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def is_system_process(proc_name, username):
    """Determine if a process is a system process."""
    if proc_name.lower() in SYSTEM_PROCESSES:
        return True
    if username and ('SYSTEM' in username.upper() or 
                     'LOCAL SERVICE' in username.upper() or 
                     'NETWORK SERVICE' in username.upper()):
        return True
    return False

def detect_app_type(proc_name, cmdline=''):
    """Detect the application type based on process name and command line."""
    proc_lower = proc_name.lower()
    cmd_lower = cmdline.lower() if cmdline else ''
    
    # Node.js / JavaScript frameworks
    if 'node' in proc_lower or 'npm' in proc_lower:
        if 'next' in cmd_lower or 'next-server' in cmd_lower:
            return 'nextjs'
        elif 'react' in cmd_lower or 'vite' in cmd_lower:
            return 'react'
        elif 'vue' in cmd_lower:
            return 'vue'
        elif 'angular' in cmd_lower:
            return 'angular'
        elif 'express' in cmd_lower:
            return 'express'
        elif 'serve' in cmd_lower:
            return 'static'
        return 'node'
    
    # Python
    if 'python' in proc_lower or 'python3' in proc_lower or 'pythonw' in proc_lower:
        if 'flask' in cmd_lower:
            return 'flask'
        elif 'django' in cmd_lower or 'manage.py' in cmd_lower:
            return 'django'
        elif 'fastapi' in cmd_lower or 'uvicorn' in cmd_lower:
            return 'fastapi'
        return 'python'
    
    # PHP
    if 'php' in proc_lower or 'httpd' in proc_lower or 'apache' in proc_lower:
        if 'laravel' in cmd_lower or 'artisan' in cmd_lower:
            return 'laravel'
        return 'php'
    
    # Java
    if 'java' in proc_lower:
        if 'spring' in cmd_lower:
            return 'spring'
        return 'java'
    
    # .NET
    if 'dotnet' in proc_lower or proc_lower.endswith('.exe') and 'aspnet' in cmd_lower:
        return 'dotnet'
    
    # Databases
    if 'mysql' in proc_lower or 'mysqld' in proc_lower:
        return 'mysql'
    if 'postgres' in proc_lower or 'postgresql' in proc_lower:
        return 'postgres'
    if 'mongo' in proc_lower:
        return 'mongodb'
    if 'redis' in proc_lower:
        return 'redis'
    
    # Web servers
    if 'nginx' in proc_lower:
        return 'nginx'
    if 'apache' in proc_lower or 'httpd' in proc_lower:
        return 'apache'
    
    # Other common
    if 'chrome' in proc_lower or 'msedge' in proc_lower or 'firefox' in proc_lower:
        return 'browser'
    
    return 'other'

def get_port_processes():
    """Get all processes with network connections."""
    processes = {'system': [], 'user': []}
    seen = set()  # Track unique port+pid combinations
    
    try:
        connections = psutil.net_connections(kind='inet')
    except psutil.AccessDenied:
        connections = psutil.net_connections(kind='inet')
    
    for conn in connections:
        if conn.laddr and conn.laddr.port:
            port = conn.laddr.port
            pid = conn.pid
            
            if pid is None or pid == 0:
                continue
            
            key = f"{port}:{pid}"
            if key in seen:
                continue
            seen.add(key)
            
            try:
                proc = psutil.Process(pid)
                proc_info = proc.as_dict(attrs=['name', 'username', 'status', 'create_time', 'cmdline'])
                cmdline = ' '.join(proc_info.get('cmdline', []) or [])
                proc_name = proc_info.get('name', 'Unknown')
                
                # Detect app type
                app_type = detect_app_type(proc_name, cmdline)
                
                process_data = {
                    'port': port,
                    'pid': pid,
                    'name': proc_name,
                    'username': proc_info.get('username', 'Unknown'),
                    'status': proc_info.get('status', 'Unknown'),
                    'address': f"{conn.laddr.ip}:{conn.laddr.port}",
                    'type': 'TCP' if conn.type == 1 else 'UDP',
                    'conn_status': conn.status if hasattr(conn, 'status') else 'N/A',
                    'app_type': app_type
                }
                
                if is_system_process(proc_name, proc_info.get('username', '')):
                    processes['system'].append(process_data)
                else:
                    processes['user'].append(process_data)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    
    # Sort by port number
    processes['system'].sort(key=lambda x: x['port'])
    processes['user'].sort(key=lambda x: x['port'])
    
    return processes

@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory('.', filename)

@app.route('/api/ports')
def get_ports():
    """API endpoint to get all port processes."""
    try:
        processes = get_port_processes()
        return jsonify({
            'success': True,
            'data': processes,
            'is_admin': is_admin(),
            'counts': {
                'system': len(processes['system']),
                'user': len(processes['user'])
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/kill/<int:pid>', methods=['POST'])
def kill_process(pid):
    """API endpoint to kill a process by PID."""
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()
        
        # Try using Windows taskkill for more reliable termination
        import subprocess
        result = subprocess.run(
            ['taskkill', '/F', '/PID', str(pid)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': f'Process {proc_name} (PID: {pid}) terminated successfully'
            })
        else:
            # Fallback to psutil if taskkill fails
            proc.kill()
            return jsonify({
                'success': True,
                'message': f'Process {proc_name} (PID: {pid}) terminated successfully'
            })
            
    except psutil.NoSuchProcess:
        return jsonify({
            'success': False,
            'error': f'Process with PID {pid} not found'
        }), 404
    except psutil.AccessDenied:
        return jsonify({
            'success': False,
            'error': f'Access denied. Run as Administrator to kill this process.'
        }), 403
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  PORT MANAGER - Process Monitor")
    print("="*60)
    print(f"  Admin Mode: {'Yes' if is_admin() else 'No (Run as Admin for full access)'}")
    print("  URL: http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
