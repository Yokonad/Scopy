# Scopy

Monitor en tiempo real de procesos Python con interfaz minimalista.

## Instalación

```bash
git clone https://github.com/Yokonad/scopy.git
cd scopy
```

**Dependencias:**

```bash
# Arch Linux / Manjaro
sudo pacman -S python-psutil python-rich

# Ubuntu / Debian
sudo apt install python3-psutil python3-rich

# pip
pip install psutil rich
```

**Alias (opcional):**

```bash
chmod +x scopy.py
echo "alias scopy='python3 $(pwd)/scopy.py'" >> ~/.bashrc
source ~/.bashrc
```

## Uso

```bash
scopy              # Monitorear todos los procesos
scopy -u usuario   # Filtrar por usuario
scopy -p "app.py"  # Filtrar por nombre de archivo
scopy -i 2         # Cambiar intervalo de actualización (segundos)
```

## Información mostrada

| Columna | Descripción |
|---------|-------------|
| PID | ID del proceso |
| USER | Usuario propietario |
| CPU | Uso de CPU (%) |
| MEM | Memoria (MB) |
| TIME | Tiempo de ejecución |
| STATUS | NEW / OK / WARN / HIGH |
| COMMAND | Ruta del script |

**Colores:**
- Verde: CPU < 20% / MEM < 100MB
- Naranja: CPU 20-50% / MEM 100-500MB
- Rojo: CPU > 50% / MEM > 500MB

## Vista previa

```
[14:30:45] Processes: 3 [+1]
     PID  USER         CPU     MEM  TIME      STATUS  COMMAND
   12345  yokonad      0.5%   45.2  5m 23s    OK      /home/yokonad/code/main.py
   12346  yokonad     35.2%   89.4  2m 10s    WARN    /home/yokonad/app.py
   12347  yokonad      0.1%   12.8  10s       NEW     /home/yokonad/test.py
```


