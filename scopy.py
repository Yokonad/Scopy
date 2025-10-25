#!/usr/bin/env python3

import psutil
import os
import sys
import time
import argparse
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.text import Text


class PythonProcessMonitor:
    
    def __init__(self, user_filter=None, name_pattern=None, refresh_interval=1):
        self.user_filter = user_filter
        self.name_pattern = name_pattern
        self.refresh_interval = refresh_interval
        self.previous_pids = set()
        self.console = Console()
        self.own_pid = os.getpid()
        
        self.system_scripts = [
            '/usr/bin/wsdd',
            '/usr/bin/networkd-dispatcher',
            '/usr/lib/',
            '/usr/share/',
        ]
        
    def is_system_script(self, script_path):
        if script_path == "N/A":
            return False
        
        for system_path in self.system_scripts:
            if script_path.startswith(system_path):
                return True
        return False
    
    def get_python_processes(self):
        python_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline', 'create_time', 'cpu_percent', 'memory_info']):
            try:
                if proc.info['pid'] == self.own_pid:
                    continue
                
                proc_name = proc.info['name'].lower()
                if 'python' not in proc_name:
                    continue
                
                if self.user_filter and proc.info['username'] != self.user_filter:
                    continue
                
                cmdline = proc.info['cmdline'] or []
                if len(cmdline) < 2:
                    script_path = "N/A"
                    full_command = ' '.join(cmdline) if cmdline else "N/A"
                else:
                    script_path = cmdline[1] if len(cmdline) > 1 else "N/A"
                    full_command = ' '.join(cmdline)
                
                if self.is_system_script(script_path):
                    continue
                
                if self.name_pattern and self.name_pattern.lower() not in script_path.lower():
                    continue
                
                create_time = proc.info['create_time']
                runtime = time.time() - create_time
                
                mem_info = proc.info['memory_info']
                memory_mb = mem_info.rss / (1024 * 1024) if mem_info else 0
                
                process_info = {
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'username': proc.info['username'],
                    'script_path': script_path,
                    'full_command': full_command,
                    'create_time': datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S'),
                    'runtime': runtime,
                    'cpu_percent': proc.info['cpu_percent'] or 0.0,
                    'memory_mb': memory_mb
                }
                
                python_processes.append(process_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return python_processes
    
    def format_runtime(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def create_display(self, processes):
        current_pids = {p['pid'] for p in processes}
        new_pids = current_pids - self.previous_pids
        terminated_pids = self.previous_pids - current_pids
        self.previous_pids = current_pids
        
        header_info = Text()
        header_info.append(f"[{datetime.now().strftime('%H:%M:%S')}] ", style="#8b949e")
        header_info.append(f"Processes: {len(processes)}", style="#f0f6fc")
        if new_pids:
            header_info.append(f" [+{len(new_pids)}]", style="#3fb950")
        if terminated_pids:
            header_info.append(f" [-{len(terminated_pids)}]", style="#f85149")
        
        table = Table(
            show_header=True,
            header_style="bold #58a6ff",
            box=None,
            show_lines=False,
            border_style="#30363d",
            padding=(0, 1),
            collapse_padding=True,
            show_edge=False,
            title=header_info,
            title_justify="left"
        )
        
        table.add_column("PID", style="#79c0ff", justify="right", width=7)
        table.add_column("USER", style="#f0f6fc", width=9)
        table.add_column("CPU", style="#ffa657", justify="right", width=6)
        table.add_column("MEM", style="#a5d6ff", justify="right", width=7)
        table.add_column("TIME", style="#8b949e", width=9)
        table.add_column("STATUS", style="#a5d6ff", width=6)
        table.add_column("COMMAND", style="#c9d1d9", overflow="fold")
        
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        for proc in processes:
            if proc['cpu_percent'] > 50:
                cpu_color = "bold #f85149"
            elif proc['cpu_percent'] > 20:
                cpu_color = "#ffa657"
            else:
                cpu_color = "#3fb950"
            
            if proc['memory_mb'] > 500:
                mem_color = "bold #f85149"
            elif proc['memory_mb'] > 100:
                mem_color = "#ffa657"
            else:
                mem_color = "#79c0ff"
            
            if proc['script_path'] != "N/A":
                script_display = proc['script_path']
            else:
                script_display = proc['full_command']
            
            if len(script_display) > 70:
                script_display = "..." + script_display[-67:]
            
            cpu_text = Text(f"{proc['cpu_percent']:.1f}%", style=cpu_color)
            mem_text = Text(f"{proc['memory_mb']:.1f}", style=mem_color)
            
            if proc['pid'] in new_pids:
                status = Text("NEW", style="bold #3fb950")
            elif proc['cpu_percent'] > 50:
                status = Text("HIGH", style="bold #f85149")
            elif proc['cpu_percent'] > 20:
                status = Text("WARN", style="#ffa657")
            else:
                status = Text("OK", style="#8b949e")
            
            table.add_row(
                str(proc['pid']),
                proc['username'][:9],
                cpu_text,
                mem_text,
                self.format_runtime(proc['runtime']),
                status,
                script_display
            )
        
        return table
    
    def run(self):
        self.console.print()
        try:
            with Live(console=self.console, refresh_per_second=1) as live:
                while True:
                    processes = self.get_python_processes()
                    display = self.create_display(processes)
                    live.update(display)
                    time.sleep(self.refresh_interval)
                    
        except KeyboardInterrupt:
            self.console.clear()
            sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description='Monitor de procesos Python en tiempo real',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos de uso:
  %(prog)s                              # Monitorear todos los procesos Python
  %(prog)s -u yokonad                   # Filtrar por usuario 'yokonad'
  %(prog)s -p "main.py"                 # Filtrar procesos que ejecutan 'main.py'
  %(prog)s -u yokonad -p "server"       # Combinar filtros
  %(prog)s -i 5                         # Actualizar cada 5 segundos
        '''
    )
    
    parser.add_argument(
        '-u', '--user',
        help='Filtrar procesos por nombre de usuario',
        default=None
    )
    
    parser.add_argument(
        '-p', '--pattern',
        help='Filtrar procesos por patrón en el nombre del archivo',
        default=None
    )
    
    parser.add_argument(
        '-i', '--interval',
        type=float,
        help='Intervalo de actualización en segundos (por defecto: 1)',
        default=1.0
    )
    
    args = parser.parse_args()
    
    if args.interval < 0.5:
        print("Error: El intervalo mínimo es 0.5 segundos")
        sys.exit(1)
    
    monitor = PythonProcessMonitor(
        user_filter=args.user,
        name_pattern=args.pattern,
        refresh_interval=args.interval
    )
    
    monitor.run()

if __name__ == '__main__':
    main()
