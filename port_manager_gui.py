"""
Port Manager - Desktop GUI v2
A standalone desktop application with improved design matching the web version.
"""

import customtkinter as ctk
from tkinter import messagebox
import psutil
import threading
import subprocess
import ctypes
from datetime import datetime

# ============================================
# Configuration
# ============================================

COLORS = {
    'bg_primary': '#0a0a0f',
    'bg_secondary': '#12121a',
    'bg_card': '#1a1a25',
    'bg_hover': '#252535',
    'text_primary': '#ffffff',
    'text_secondary': '#a0a0b0',
    'text_muted': '#606070',
    'accent_primary': '#6366f1',
    'accent_secondary': '#818cf8',
    'success': '#10b981',
    'danger': '#ef4444',
    'warning': '#f59e0b',
    'system_color': '#8b5cf6',
    'border_color': '#2a2a35',
}

APP_COLORS = {
    'node': '#68a063', 'react': '#61dafb', 'nextjs': '#ffffff', 'vue': '#42b883',
    'python': '#3776ab', 'flask': '#3776ab', 'django': '#44b78b', 'fastapi': '#009688',
    'php': '#777bb4', 'laravel': '#ff2d20', 'java': '#f44336', 'mysql': '#00758f',
    'postgres': '#336791', 'mongodb': '#4db33d', 'redis': '#dc382d',
    'browser': '#4285f4', 'other': '#606070',
}

APP_LABELS = {
    'node': 'Node.js', 'react': 'React', 'nextjs': 'Next.js', 'vue': 'Vue',
    'python': 'Python', 'flask': 'Flask', 'django': 'Django', 'fastapi': 'FastAPI',
    'php': 'PHP', 'laravel': 'Laravel', 'java': 'Java', 'mysql': 'MySQL',
    'postgres': 'Postgres', 'mongodb': 'MongoDB', 'redis': 'Redis',
    'browser': 'Browser', 'other': 'Other'
}

SYSTEM_PROCESSES = {
    'system', 'svchost.exe', 'services.exe', 'lsass.exe', 'csrss.exe',
    'wininit.exe', 'winlogon.exe', 'smss.exe', 'dwm.exe', 'explorer.exe',
    'spoolsv.exe', 'searchindexer.exe', 'msdtc.exe', 'audiodg.exe',
    'conhost.exe', 'dllhost.exe', 'sihost.exe', 'taskhostw.exe',
    'runtimebroker.exe', 'ctfmon.exe', 'wmiprvse.exe'
}

# ============================================
# Helper Functions
# ============================================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def is_system_process(proc_name, username):
    if proc_name.lower() in SYSTEM_PROCESSES:
        return True
    if username and ('SYSTEM' in username.upper() or 'LOCAL SERVICE' in username.upper()):
        return True
    return False

def detect_app_type(proc_name, cmdline=''):
    proc_lower = proc_name.lower()
    cmd_lower = cmdline.lower() if cmdline else ''
    
    if 'node' in proc_lower:
        if 'next' in cmd_lower: return 'nextjs'
        elif 'react' in cmd_lower or 'vite' in cmd_lower: return 'react'
        return 'node'
    if 'python' in proc_lower:
        if 'flask' in cmd_lower: return 'flask'
        elif 'django' in cmd_lower: return 'django'
        return 'python'
    if 'php' in proc_lower or 'httpd' in proc_lower:
        if 'laravel' in cmd_lower: return 'laravel'
        return 'php'
    if 'mysql' in proc_lower: return 'mysql'
    if 'postgres' in proc_lower: return 'postgres'
    if 'chrome' in proc_lower or 'msedge' in proc_lower or 'firefox' in proc_lower:
        return 'browser'
    return 'other'

def get_port_processes():
    processes = {'system': [], 'user': []}
    seen = set()
    
    try:
        connections = psutil.net_connections(kind='inet')
    except:
        return processes
    
    for conn in connections:
        if conn.laddr and conn.laddr.port:
            port, pid = conn.laddr.port, conn.pid
            if pid is None or pid == 0:
                continue
            key = f"{port}:{pid}"
            if key in seen:
                continue
            seen.add(key)
            
            try:
                proc = psutil.Process(pid)
                info = proc.as_dict(attrs=['name', 'username', 'status', 'cmdline'])
                cmdline = ' '.join(info.get('cmdline', []) or [])
                name = info.get('name', 'Unknown')
                
                data = {
                    'port': port, 'pid': pid, 'name': name,
                    'address': f"{conn.laddr.ip}:{port}",
                    'type': 'TCP' if conn.type == 1 else 'UDP',
                    'status': conn.status if hasattr(conn, 'status') else 'N/A',
                    'app_type': detect_app_type(name, cmdline)
                }
                
                if is_system_process(name, info.get('username', '')):
                    processes['system'].append(data)
                else:
                    processes['user'].append(data)
            except:
                continue
    
    processes['system'].sort(key=lambda x: x['port'])
    processes['user'].sort(key=lambda x: x['port'])
    return processes

def kill_process(pid):
    try:
        result = subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                               capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

# ============================================
# Process Row Widget
# ============================================

class ProcessRow(ctk.CTkFrame):
    def __init__(self, parent, data, on_kill, **kwargs):
        super().__init__(parent, fg_color=COLORS['bg_secondary'], height=45, **kwargs)
        self.data = data
        self.on_kill = on_kill
        self.pack_propagate(False)
        
        # Bind hover
        self.bind('<Enter>', lambda e: self.configure(fg_color=COLORS['bg_hover']))
        self.bind('<Leave>', lambda e: self.configure(fg_color=COLORS['bg_secondary']))
        
        # Columns
        col_widths = [70, 70, 180, 90, 150, 60, 90, 80]
        
        # Port
        self.add_cell(str(data['port']), col_widths[0], COLORS['accent_secondary'], bold=True)
        # PID
        self.add_cell(str(data['pid']), col_widths[1], COLORS['text_muted'])
        # Name
        self.add_cell(data['name'], col_widths[2], COLORS['text_primary'], anchor='w')
        # App Type with color
        app_type = data['app_type']
        app_label = APP_LABELS.get(app_type, app_type.title())
        app_color = APP_COLORS.get(app_type, COLORS['text_muted'])
        self.add_badge(app_label, col_widths[3], app_color)
        # Address
        self.add_cell(data['address'], col_widths[4], COLORS['text_secondary'], size=11)
        # Type
        self.add_cell(data['type'], col_widths[5], COLORS['accent_secondary'], size=11)
        # Status
        status_color = COLORS['success'] if data['status'] == 'LISTEN' else COLORS['warning']
        self.add_cell(data['status'], col_widths[6], status_color, size=11)
        # Kill button
        self.add_kill_button(col_widths[7])
    
    def add_cell(self, text, width, color, bold=False, size=12, anchor='center'):
        cell = ctk.CTkFrame(self, fg_color='transparent', width=width)
        cell.pack(side='left', padx=2)
        cell.pack_propagate(False)
        
        font = ctk.CTkFont(family='Consolas', size=size, weight='bold' if bold else 'normal')
        lbl = ctk.CTkLabel(cell, text=text, font=font, text_color=color, anchor=anchor)
        lbl.pack(expand=True, fill='both', padx=5)
    
    def add_badge(self, text, width, color):
        cell = ctk.CTkFrame(self, fg_color='transparent', width=width)
        cell.pack(side='left', padx=2)
        cell.pack_propagate(False)
        
        badge = ctk.CTkLabel(cell, text=text.upper(), 
                            font=ctk.CTkFont(size=10, weight='bold'),
                            text_color=color,
                            fg_color=self._adjust_color(color, 0.15),
                            corner_radius=8, padx=8, pady=2)
        badge.pack(expand=True)
    
    def _adjust_color(self, hex_color, alpha):
        # Create semi-transparent background
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        # Blend with dark background
        bg = 0x12
        r = int(r * alpha + bg * (1 - alpha))
        g = int(g * alpha + bg * (1 - alpha))
        b = int(b * alpha + bg * (1 - alpha))
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def add_kill_button(self, width):
        cell = ctk.CTkFrame(self, fg_color='transparent', width=width)
        cell.pack(side='left', padx=2)
        cell.pack_propagate(False)
        
        btn = ctk.CTkButton(cell, text="Kill", width=60, height=28,
                           fg_color='transparent',
                           border_width=1,
                           border_color=COLORS['danger'],
                           text_color=COLORS['danger'],
                           hover_color=COLORS['danger'],
                           font=ctk.CTkFont(size=11, weight='bold'),
                           command=lambda: self.on_kill(self.data))
        btn.pack(expand=True)

# ============================================
# Main Application
# ============================================

class PortManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Port Manager")
        self.geometry("1100x750")
        self.minsize(900, 600)
        
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=COLORS['bg_primary'])
        
        self.current_filter = 'all'
        self.auto_refresh = True
        self.all_processes = {'user': [], 'system': []}
        self.system_visible = True
        
        self.create_widgets()
        self.refresh_data()
        self.auto_refresh_loop()
    
    def create_widgets(self):
        # Main scrollable container
        self.main_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_primary'])
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=15)
        
        self.create_header()
        self.create_stats_bar()
        self.create_filter_bar()
        self.create_process_sections()
    
    def create_header(self):
        header = ctk.CTkFrame(self.main_frame, fg_color=COLORS['bg_secondary'], corner_radius=12)
        header.pack(fill="x", pady=(0, 12))
        
        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=12)
        
        # Title
        title = ctk.CTkLabel(inner, text="Port Manager", 
                            font=ctk.CTkFont(size=22, weight="bold"),
                            text_color=COLORS['accent_primary'])
        title.pack(side="left")
        
        # Controls
        controls = ctk.CTkFrame(inner, fg_color="transparent")
        controls.pack(side="right")
        
        if is_admin():
            admin = ctk.CTkLabel(controls, text="ADMIN", 
                               font=ctk.CTkFont(size=11, weight="bold"),
                               text_color=COLORS['success'],
                               fg_color=COLORS['bg_card'], corner_radius=4, padx=8, pady=3)
            admin.pack(side="left", padx=(0, 12))
        
        self.auto_var = ctk.BooleanVar(value=True)
        switch = ctk.CTkSwitch(controls, text="Auto-refresh", variable=self.auto_var,
                              command=lambda: setattr(self, 'auto_refresh', self.auto_var.get()),
                              font=ctk.CTkFont(size=12), text_color=COLORS['text_secondary'])
        switch.pack(side="left", padx=(0, 12))
        
        refresh = ctk.CTkButton(controls, text="Refresh", width=90, height=32,
                               fg_color=COLORS['accent_primary'],
                               hover_color=COLORS['accent_secondary'],
                               command=self.refresh_data)
        refresh.pack(side="left")
    
    def create_stats_bar(self):
        stats = ctk.CTkFrame(self.main_frame, fg_color=COLORS['bg_secondary'], corner_radius=12)
        stats.pack(fill="x", pady=(0, 12))
        
        inner = ctk.CTkFrame(stats, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=12)
        
        self.total_lbl = self._add_stat(inner, "0", "TOTAL PORTS")
        self.user_lbl = self._add_stat(inner, "0", "USER PROCESSES")
        self.system_lbl = self._add_stat(inner, "0", "SYSTEM PROCESSES")
        self.update_lbl = self._add_stat(inner, "--:--:--", "LAST UPDATE")
    
    def _add_stat(self, parent, value, label):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", padx=25)
        
        val = ctk.CTkLabel(frame, text=value, 
                          font=ctk.CTkFont(size=22, weight="bold"),
                          text_color=COLORS['accent_primary'])
        val.pack()
        
        lbl = ctk.CTkLabel(frame, text=label,
                          font=ctk.CTkFont(size=10),
                          text_color=COLORS['text_muted'])
        lbl.pack()
        return val
    
    def create_filter_bar(self):
        bar = ctk.CTkFrame(self.main_frame, fg_color=COLORS['bg_secondary'], corner_radius=12)
        bar.pack(fill="x", pady=(0, 12))
        
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=10)
        
        lbl = ctk.CTkLabel(inner, text="Filter by App:", 
                          font=ctk.CTkFont(size=12),
                          text_color=COLORS['text_secondary'])
        lbl.pack(side="left", padx=(0, 12))
        
        self.filter_btns = {}
        filters = ['all', 'node', 'react', 'nextjs', 'python', 'flask', 'php', 'mysql', 'postgres', 'browser', 'other']
        
        for f in filters:
            label = 'All' if f == 'all' else APP_LABELS.get(f, f.title())
            active = f == 'all'
            btn = ctk.CTkButton(inner, text=label, width=65, height=26, corner_radius=13,
                              fg_color=COLORS['accent_primary'] if active else 'transparent',
                              border_width=1, border_color=COLORS['border_color'],
                              text_color=COLORS['text_primary'] if active else COLORS['text_secondary'],
                              hover_color=COLORS['bg_hover'],
                              font=ctk.CTkFont(size=11),
                              command=lambda x=f: self.set_filter(x))
            btn.pack(side="left", padx=3)
            self.filter_btns[f] = btn
    
    def set_filter(self, f):
        self.current_filter = f
        for key, btn in self.filter_btns.items():
            active = key == f
            btn.configure(fg_color=COLORS['accent_primary'] if active else 'transparent',
                         text_color=COLORS['text_primary'] if active else COLORS['text_secondary'])
        self.update_tables()
    
    def create_process_sections(self):
        # User section
        self.user_section = ctk.CTkFrame(self.main_frame, fg_color=COLORS['bg_secondary'], corner_radius=12)
        self.user_section.pack(fill="both", expand=True, pady=(0, 12))
        
        self._create_section_header(self.user_section, "User Processes", COLORS['accent_primary'], False)
        self.user_scroll = ctk.CTkScrollableFrame(self.user_section, fg_color=COLORS['bg_secondary'])
        self.user_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # System section
        self.system_section = ctk.CTkFrame(self.main_frame, fg_color=COLORS['bg_secondary'], corner_radius=12)
        self.system_section.pack(fill="both", expand=True)
        
        self._create_section_header(self.system_section, "System Processes", COLORS['system_color'], True)
        self.system_scroll = ctk.CTkScrollableFrame(self.system_section, fg_color=COLORS['bg_secondary'])
        self.system_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # Table headers
        self._create_table_header(self.user_scroll)
        self._create_table_header(self.system_scroll)
    
    def _create_section_header(self, parent, title, color, is_system):
        header = ctk.CTkFrame(parent, fg_color=COLORS['bg_card'], corner_radius=0)
        header.pack(fill="x")
        
        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=8)
        
        lbl = ctk.CTkLabel(inner, text=title, font=ctk.CTkFont(size=14, weight="bold"),
                          text_color=color)
        lbl.pack(side="left")
        
        badge = ctk.CTkLabel(inner, text="0", font=ctk.CTkFont(size=11, weight="bold"),
                            text_color=color, fg_color=COLORS['bg_hover'],
                            corner_radius=10, padx=8, pady=2)
        badge.pack(side="left", padx=10)
        
        if is_system:
            self.sys_badge = badge
            toggle = ctk.CTkButton(inner, text="Toggle", width=60, height=24,
                                  fg_color="transparent", hover_color=COLORS['bg_hover'],
                                  text_color=COLORS['text_secondary'],
                                  command=self.toggle_system)
            toggle.pack(side="right")
        else:
            self.user_badge = badge
    
    def _create_table_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color=COLORS['bg_card'], height=35)
        header.pack(fill="x", pady=(0, 2))
        header.pack_propagate(False)
        
        cols = [("PORT", 70), ("PID", 70), ("PROCESS NAME", 180), ("APP TYPE", 90),
                ("ADDRESS", 150), ("TYPE", 60), ("STATUS", 90), ("ACTION", 80)]
        
        for text, width in cols:
            cell = ctk.CTkFrame(header, fg_color='transparent', width=width)
            cell.pack(side='left', padx=2)
            cell.pack_propagate(False)
            
            lbl = ctk.CTkLabel(cell, text=text, font=ctk.CTkFont(size=11, weight='bold'),
                              text_color=COLORS['text_muted'], anchor='center')
            lbl.pack(expand=True, fill='both', padx=5)
    
    def toggle_system(self):
        self.system_visible = not self.system_visible
        if self.system_visible:
            self.system_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        else:
            self.system_scroll.pack_forget()
    
    def on_kill(self, data):
        if messagebox.askyesno("Kill Process", 
                              f"Kill {data['name']} (PID: {data['pid']}) on port {data['port']}?"):
            if kill_process(data['pid']):
                messagebox.showinfo("Success", f"Process killed successfully")
                self.refresh_data()
            else:
                messagebox.showerror("Error", "Failed to kill. Run as Administrator.")
    
    def auto_refresh_loop(self):
        if self.auto_refresh:
            self.refresh_data()
        self.after(2000, self.auto_refresh_loop)
    
    def refresh_data(self):
        def fetch():
            self.all_processes = get_port_processes()
            self.after(0, self.update_ui)
        threading.Thread(target=fetch, daemon=True).start()
    
    def update_ui(self):
        total_u = len(self.all_processes['user'])
        total_s = len(self.all_processes['system'])
        
        self.total_lbl.configure(text=str(total_u + total_s))
        self.user_lbl.configure(text=str(total_u))
        self.system_lbl.configure(text=str(total_s))
        self.update_lbl.configure(text=datetime.now().strftime("%H:%M:%S"))
        
        self.update_tables()
    
    def update_tables(self):
        if self.current_filter == 'all':
            user = self.all_processes['user']
            system = self.all_processes['system']
        else:
            user = [p for p in self.all_processes['user'] if p['app_type'] == self.current_filter]
            system = [p for p in self.all_processes['system'] if p['app_type'] == self.current_filter]
        
        self._populate_table(self.user_scroll, user)
        self._populate_table(self.system_scroll, system)
        
        self.user_badge.configure(text=str(len(user)))
        self.sys_badge.configure(text=str(len(system)))
    
    def _populate_table(self, container, processes):
        # Keep header, remove rest
        children = list(container.winfo_children())
        for child in children[1:]:  # Skip header
            child.destroy()
        
        for proc in processes:
            row = ProcessRow(container, proc, self.on_kill)
            row.pack(fill="x", pady=1)


if __name__ == "__main__":
    app = PortManagerApp()
    app.mainloop()
