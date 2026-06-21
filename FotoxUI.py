import tkinter as tk
from tkinter import ttk, filedialog
import threading
import os
import hashlib
import shutil
from datetime import datetime
from PIL import Image
import imagehash
import warnings

warnings.filterwarnings('ignore')

UMBRAL_DEFAULT = 10

# ─── Ventana principal ───────────────────────────────────────
ventana = tk.Tk()
ventana.title("Fotox")
ventana.geometry("650x520")
ventana.resizable(False, False)

# ─── Funciones de UI ─────────────────────────────────────────
def verificar_rutas():
    if entry_fotos.get() and entry_cuarentena.get():
        boton_ejecutar.config(state='normal')
    else:
        boton_ejecutar.config(state='disabled')

def buscar_fotos():
    ruta = filedialog.askdirectory(title="Selecciona el directorio de fotos")
    if ruta:
        entry_fotos.delete(0, tk.END)
        entry_fotos.insert(0, ruta)
        verificar_rutas()

def buscar_cuarentena():
    ruta = filedialog.askdirectory(title="Selecciona donde crear la carpeta CUARENTENA")
    if ruta:
        entry_cuarentena.delete(0, tk.END)
        entry_cuarentena.insert(0, ruta)
        verificar_rutas()

def log_mensaje(mensaje):
    log.config(state='normal')
    log.insert(tk.END, mensaje + '\n')
    log.see(tk.END)
    log.config(state='disabled')

def actualizar_progreso(valor, texto):
    barra_progreso['value'] = valor
    label_progreso.config(text=texto)
    ventana.update_idletasks()

# ─── Lógica principal de Fotox ───────────────────────────────
def ejecutar_fotox():
    ruta_fotos      = os.path.normpath(entry_fotos.get())
    ruta_cuarentena = os.path.join(os.path.normpath(entry_cuarentena.get()), 'CUARENTENA')
    recursivo       = var_recursivo.get()
    umbral          = int(spinbox_umbral.get())

    log_mensaje(f"Ruta fotos: {ruta_fotos}")
    log_mensaje(f"Cuarentena: {ruta_cuarentena}")
    log_mensaje(f"Recursivo: {recursivo}")
    log_mensaje(f"Umbral pHash: {umbral}")

    # Crear cuarentena
    os.makedirs(ruta_cuarentena, exist_ok=True)
    if os.path.exists(ruta_cuarentena):
        log_mensaje(f"✅ Cuarentena lista: {ruta_cuarentena}")
    else:
        log_mensaje(f"❌ Error al crear cuarentena")
        boton_ejecutar.config(state='normal')
        return

    extensiones = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.mp4', '.mov', '.avi'}

    # ── Recopilar fotos ──────────────────────────────────────
    log_mensaje("Buscando fotos...")
    fotos = []
    if recursivo:
        for raiz, _, archivos in os.walk(ruta_fotos):
            raiz_norm = os.path.normpath(raiz)
            if raiz_norm == ruta_cuarentena or raiz_norm.startswith(ruta_cuarentena + os.sep):
                continue
            for archivo in archivos:
                if os.path.splitext(archivo)[1].lower() in extensiones:
                    fotos.append(os.path.normpath(os.path.join(raiz, archivo)))
    else:
        for archivo in os.listdir(ruta_fotos):
            ruta_completa = os.path.normpath(os.path.join(ruta_fotos, archivo))
            if os.path.isfile(ruta_completa) and os.path.splitext(archivo)[1].lower() in extensiones:
                fotos.append(ruta_completa)

    total = len(fotos)
    log_mensaje(f"Fotos encontradas: {total}")

    if total == 0:
        log_mensaje("⚠️ No se encontraron fotos.")
        boton_ejecutar.config(state='normal')
        return

    # ── Fase 1 — Calcular MD5 ────────────────────────────────
    log_mensaje("Fase 1 — Calculando hashes MD5...")
    diccionario = {}
    for i, foto in enumerate(fotos):
        try:
            with open(foto, 'rb') as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            diccionario[foto] = md5
        except Exception as e:
            log_mensaje(f"Error MD5: {os.path.basename(foto)} → {e}")
        actualizar_progreso((i + 1) / total * 40, f"Fase 1 — {i+1} de {total}")

    # ── Fase 2 — Comparar MD5 ────────────────────────────────
    log_mensaje("Fase 2 — Comparando duplicados exactos...")
    fotos_movidas   = set()
    fotos_restantes = []
    grupo_actual    = 0

    for i in range(len(fotos)):
        if fotos[i] in fotos_movidas:
            continue

        cont_coincidencias = 0
        hubo_coincidencias = False

        for c in range(i + 1, len(fotos)):
            if fotos[c] in fotos_movidas:
                continue
            if diccionario.get(fotos[i]) == diccionario.get(fotos[c]):
                if not hubo_coincidencias:
                    grupo_actual += 1
                cont_coincidencias += 1
                hubo_coincidencias = True
                if os.path.exists(fotos[c]):
                    ext       = os.path.splitext(fotos[c])[1]
                    timestamp = datetime.now().strftime("%d%m%Y%H%M%S%f")[:17]
                    destino   = os.path.join(ruta_cuarentena, f"md5-{grupo_actual}-{cont_coincidencias}_{timestamp}{ext}")
                    shutil.move(fotos[c], destino)
                    fotos_movidas.add(fotos[c])

        if hubo_coincidencias:
            if os.path.exists(fotos[i]):
                ext       = os.path.splitext(fotos[i])[1]
                timestamp = datetime.now().strftime("%d%m%Y%H%M%S%f")[:17]
                destino   = os.path.join(ruta_cuarentena, f"md5-{grupo_actual}_{timestamp}{ext}")
                shutil.move(fotos[i], destino)
                fotos_movidas.add(fotos[i])
        else:
            fotos_restantes.append(fotos[i])

    log_mensaje(f"Duplicados exactos: {grupo_actual} grupos")
    log_mensaje(f"Fotos para pHash: {len(fotos_restantes)}")

    if len(fotos_restantes) == 0:
        actualizar_progreso(100, "¡Completado!")
        log_mensaje("✅ ¡Proceso completado!")
        boton_ejecutar.config(state='normal')
        return

    # ── Fase 3 — Calcular pHash ──────────────────────────────
    log_mensaje("Fase 3 — Calculando pHash...")
    hashes        = {}
    errores_phash = 0
    for i, ruta in enumerate(fotos_restantes):
        try:
            hashes[ruta] = imagehash.phash(Image.open(ruta))
        except Exception as e:
            errores_phash += 1
            log_mensaje(f"Error pHash: {os.path.basename(ruta)} → {e}")
        actualizar_progreso(40 + (i + 1) / len(fotos_restantes) * 40,
                            f"Fase 3 — {i+1} de {len(fotos_restantes)}")

    log_mensaje(f"pHash calculados: {len(hashes)} | Errores: {errores_phash}")

    # ── Fase 4 — Comparar pHash ──────────────────────────────
    log_mensaje("Fase 4 — Comparando similares visuales...")
    rutas_lista   = list(hashes.keys())
    movidas_phash = set()
    grupo_phash   = 0

    for i in range(len(rutas_lista)):
        if rutas_lista[i] in movidas_phash:
            continue

        hubo = False
        cont = 0

        for c in range(i + 1, len(rutas_lista)):
            if rutas_lista[c] in movidas_phash:
                continue
            distancia = hashes[rutas_lista[i]] - hashes[rutas_lista[c]]
            if distancia <= umbral:
                if not hubo:
                    grupo_phash += 1
                    hubo = True
                cont += 1
                if os.path.exists(rutas_lista[c]):
                    ext       = os.path.splitext(rutas_lista[c])[1]
                    timestamp = datetime.now().strftime("%d%m%Y%H%M%S%f")[:17]
                    destino   = os.path.join(ruta_cuarentena,
                                f"phash-{grupo_phash}-{cont}_{timestamp}{ext}")
                    shutil.move(rutas_lista[c], destino)
                    movidas_phash.add(rutas_lista[c])

        if hubo:
            if os.path.exists(rutas_lista[i]):
                ext       = os.path.splitext(rutas_lista[i])[1]
                timestamp = datetime.now().strftime("%d%m%Y%H%M%S%f")[:17]
                destino   = os.path.join(ruta_cuarentena,
                            f"phash-{grupo_phash}_{timestamp}{ext}")
                shutil.move(rutas_lista[i], destino)
                movidas_phash.add(rutas_lista[i])

    actualizar_progreso(100, "¡Completado!")
    log_mensaje(f"Similares visuales: {len(movidas_phash)}")
    log_mensaje("✅ ¡Proceso completado!")
    boton_ejecutar.config(state='normal')

def iniciar_ejecucion():
    boton_ejecutar.config(state='disabled')
    log.config(state='normal')
    log.delete(1.0, tk.END)
    log.config(state='disabled')
    actualizar_progreso(0, "Iniciando...")
    hilo = threading.Thread(target=ejecutar_fotox)
    hilo.daemon = True
    hilo.start()

# ─── Widgets ─────────────────────────────────────────────────

# Fila 0 - Ruta de Fotos
label_fotos = tk.Label(ventana, text="Ruta de Fotos:")
label_fotos.grid(row=0, column=0, padx=10, pady=10)
entry_fotos = tk.Entry(ventana, width=50)
entry_fotos.grid(row=0, column=1, padx=10, pady=10)
boton_fotos = tk.Button(ventana, text="Buscar", command=buscar_fotos)
boton_fotos.grid(row=0, column=2, padx=10, pady=10, sticky='w')

# Fila 1 - Ruta de Cuarentena
label_cuarentena = tk.Label(ventana, text="Carpeta CUARENTENA en:")
label_cuarentena.grid(row=1, column=0, padx=10, pady=10)
entry_cuarentena = tk.Entry(ventana, width=50)
entry_cuarentena.grid(row=1, column=1, padx=10, pady=10)
boton_cuarentena = tk.Button(ventana, text="Buscar", command=buscar_cuarentena)
boton_cuarentena.grid(row=1, column=2, padx=10, pady=10, sticky='w')

# Fila 2 - Recursivo
var_recursivo = tk.BooleanVar(value=True)
checkbox = tk.Checkbutton(ventana, text="Buscar en Sub-Carpetas", variable=var_recursivo)
checkbox.grid(row=2, column=1, padx=10, pady=10, sticky='w')

# Fila 3 - Nivel de similitud
label_umbral = tk.Label(ventana, text="Nivel de Similitud:")
label_umbral.grid(row=3, column=0, padx=10, pady=10)
frame_umbral = tk.Frame(ventana)
frame_umbral.grid(row=3, column=1, sticky='w')
spinbox_umbral = tk.Spinbox(frame_umbral, from_=0, to=64, width=5)
spinbox_umbral.delete(0, tk.END)
spinbox_umbral.insert(0, UMBRAL_DEFAULT)
spinbox_umbral.pack(side='left')
label_desc_umbral = tk.Label(frame_umbral,
                              text="Menor = casi idénticas  |  Mayor = más diferentes",
                              fg='gray', font=('Arial', 8))
label_desc_umbral.pack(side='left', padx=5)

# Fila 4 - Botón Ejecutar
boton_ejecutar = tk.Button(ventana, text="Ejecutar Fotox", width=20,
                           state='disabled', command=iniciar_ejecucion)
boton_ejecutar.grid(row=4, column=1, pady=10)

# Fila 5 - Barra de progreso
barra_progreso = ttk.Progressbar(ventana, length=600, mode='determinate')
barra_progreso.grid(row=5, column=0, columnspan=3, padx=10, pady=5)
label_progreso = tk.Label(ventana, text="", fg='gray', font=('Arial', 8))
label_progreso.grid(row=6, column=0, columnspan=3)

# Fila 7 - Log
log = tk.Text(ventana, height=8, width=76, state='disabled', font=('Courier', 8))
log.grid(row=7, column=0, columnspan=3, padx=10, pady=10)

ventana.mainloop()
