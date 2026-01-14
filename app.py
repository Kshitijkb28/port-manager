"""
Port Manager - Flask Backend with WebSocket Support
Monitors all processes running on network ports and provides kill functionality.
Uses WebSockets for real-time updates instead of polling.
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import psutil
import os
import ctypes
import json
import hashlib

app = Flask(__name__, static_folder='.')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Store previous state to detect changes
previous_state_hash = None

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
                proc_info = proc.as_dict(attrs=['name', 'username', 'status', 'create_time', 'cmdline', 'ppid'])
                cmdline = ' '.join(proc_info.get('cmdline', []) or [])
                proc_name = proc_info.get('name', 'Unknown')
                
                # Detect app type
                app_type = detect_app_type(proc_name, cmdline)
                
                # Get root controller by tracing up the parent chain
                controller_names = ['php.exe', 'node.exe', 'python.exe', 'java.exe', 'ruby.exe']
                wrapper_names = ['cmd.exe', 'powershell.exe', 'conhost.exe']
                
                parent_pid = proc_info.get('ppid', None)
                root_controller_pid = None
                root_controller_name = None
                has_parent_controller = False
                
                # Trace up the parent chain
                current_pid = parent_pid
                visited = set()
                while current_pid and current_pid > 0 and current_pid not in visited:
                    visited.add(current_pid)
                    try:
                        parent_proc = psutil.Process(current_pid)
                        parent_name = parent_proc.name().lower()
                        parent_ppid = parent_proc.ppid()
                        
                        if parent_name in controller_names:
                            # Found a controller, this is the root (or check further)
                            root_controller_pid = current_pid
                            root_controller_name = parent_proc.name()
                            has_parent_controller = True
                        
                        # Keep going up if parent is a wrapper or controller
                        if parent_name in wrapper_names or parent_name in controller_names:
                            current_pid = parent_ppid
                            continue
                        break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
                
                process_data = {
                    'port': port,
                    'pid': pid,
                    'name': proc_name,
                    'username': proc_info.get('username', 'Unknown'),
                    'status': proc_info.get('status', 'Unknown'),
                    'address': f"{conn.laddr.ip}:{conn.laddr.port}",
                    'type': 'TCP' if conn.type == 1 else 'UDP',
                    'conn_status': conn.status if hasattr(conn, 'status') else 'N/A',
                    'app_type': app_type,
                    'parent_pid': root_controller_pid or parent_pid,
                    'parent_name': root_controller_name,
                    'has_parent_controller': has_parent_controller
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

def get_state_hash(processes):
    """Generate a hash of the current process state to detect changes."""
    # Create a consistent string representation
    state_str = json.dumps(processes, sort_keys=True)
    return hashlib.md5(state_str.encode()).hexdigest()

def background_monitor():
    """Background task to monitor port changes and emit updates."""
    global previous_state_hash
    
    while True:
        socketio.sleep(2)  # Check every 2 seconds
        
        try:
            processes = get_port_processes()
            current_hash = get_state_hash(processes)
            
            # Only emit if state has changed
            if current_hash != previous_state_hash:
                previous_state_hash = current_hash
                socketio.emit('ports_update', {
                    'success': True,
                    'data': processes,
                    'is_admin': is_admin(),
                    'counts': {
                        'system': len(processes['system']),
                        'user': len(processes['user'])
                    }
                })
        except Exception as e:
            print(f"Background monitor error: {e}")

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
    """API endpoint to get all port processes (fallback for initial load)."""
    global previous_state_hash
    
    try:
        processes = get_port_processes()
        previous_state_hash = get_state_hash(processes)
        
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

@app.route('/api/kill-tree/<int:pid>', methods=['POST'])
def kill_process_tree(pid):
    """API endpoint to kill a process and its root controller (to prevent respawn)."""
    import subprocess
    killed_processes = []
    
    def find_root_controller(start_pid):
        """Trace up the parent chain to find the root controller process."""
        controller_names = ['php.exe', 'node.exe', 'python.exe', 'java.exe', 'ruby.exe']
        wrapper_names = ['cmd.exe', 'powershell.exe', 'conhost.exe']
        
        current_pid = start_pid
        root_controller = None
        visited = set()
        
        while current_pid and current_pid > 0 and current_pid not in visited:
            visited.add(current_pid)
            try:
                proc = psutil.Process(current_pid)
                proc_name = proc.name().lower()
                parent_pid = proc.ppid()
                
                # If this is a controller (not a wrapper), remember it as potential root
                if proc_name in controller_names:
                    root_controller = (current_pid, proc.name())
                
                # If parent is a shell/wrapper, keep going up
                if parent_pid and parent_pid > 0:
                    try:
                        parent_proc = psutil.Process(parent_pid)
                        parent_name = parent_proc.name().lower()
                        
                        # If parent is a controller, it might be the real root
                        if parent_name in controller_names:
                            root_controller = (parent_pid, parent_proc.name())
                        
                        # Keep going up if parent is a wrapper or controller
                        if parent_name in wrapper_names or parent_name in controller_names:
                            current_pid = parent_pid
                            continue
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
        
        return root_controller
    
    try:
        proc = psutil.Process(pid)
        proc_name = proc.name()
        
        # Find the root controller in the parent chain
        root_controller = find_root_controller(pid)
        
        if root_controller:
            root_pid, root_name = root_controller
            # Kill the root controller with /T to kill all children
            result = subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(root_pid)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                killed_processes.append(f'{root_name} (PID: {root_pid}) + children')
            else:
                # Fallback: kill just the target process
                result = subprocess.run(
                    ['taskkill', '/F', '/PID', str(pid)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    killed_processes.append(f'{proc_name} (PID: {pid})')
        else:
            # No controller found, just kill the process
            result = subprocess.run(
                ['taskkill', '/F', '/PID', str(pid)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                killed_processes.append(f'{proc_name} (PID: {pid})')
        
        if killed_processes:
            return jsonify({
                'success': True,
                'message': f'Killed: {", ".join(killed_processes)}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to kill process'
            }), 500
            
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

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print("Client connected")
    # Send initial data immediately
    try:
        processes = get_port_processes()
        emit('ports_update', {
            'success': True,
            'data': processes,
            'is_admin': is_admin(),
            'counts': {
                'system': len(processes['system']),
                'user': len(processes['user'])
            }
        })
    except Exception as e:
        print(f"Error sending initial data: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print("Client disconnected")

@socketio.on('request_refresh')
def handle_refresh_request():
    """Handle manual refresh request from client."""
    try:
        processes = get_port_processes()
        emit('ports_update', {
            'success': True,
            'data': processes,
            'is_admin': is_admin(),
            'counts': {
                'system': len(processes['system']),
                'user': len(processes['user'])
            }
        })
    except Exception as e:
        emit('error', {'message': str(e)})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  PORT MANAGER - Process Monitor (WebSocket Mode)")
    print("="*60)
    print(f"  Admin Mode: {'Yes' if is_admin() else 'No (Run as Admin for full access)'}")
    print("  URL: http://localhost:5000")
    print("  Mode: WebSocket (real-time updates)")
    print("="*60 + "\n")
    
    # Start background monitor
    socketio.start_background_task(background_monitor)
    
    # Run with eventlet
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
