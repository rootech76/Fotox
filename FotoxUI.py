import tkinter as tk
from tkinter import ttk, filedialog
import threading
import os
import hashlib
import shutil
from datetime import datetime
from collections import defaultdict
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

# ─── Control de cancelación ──────────────────────────────────
cancelar = threading.Event()

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

def cancelar_proceso():
    cancelar.set()
    log_mensaje("⚠️ Cancelando proceso...")
    boton_cancelar.config(state='disabled')

# ─── Lógica principal de Fotox ───────────────────────────────
def ejecutar_fotox():
    cancelar.clear()

    ruta_fotos      = os.path.normpath(entry_fotos.get())
    ruta_cuarentena = os.path.join(os.path.normpath(entry_cuarentena.get()), 'CUARENTENA')
    recursivo       = var_recursivo.get()
    umbral          = int(spinbox_umbral.get())

    log_mensaje(f"Ruta fotos: {ruta_fotos}")
    log_mensaje(f"Cuarentena: {ruta_cuarentena}")
    log_mensaje(f"Recursivo: {recursivo}")
    log_mensaje(f"Umbral pHash+dHash: {umbral}")

    # Crear cuarentena
    os.makedirs(ruta_cuarentena, exist_ok=True)
    if os.path.exists(ruta_cuarentena):
        log_mensaje(f"✅ Cuarentena lista: {ruta_cuarentena}")
    else:
        log_mensaje(f"❌ Error al crear cuarentena")
        boton_ejecutar.config(state='normal')
        boton_cancelar.config(state='disabled')
        return

    extensiones_img   = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    extensiones_video = {'.mp4', '.mov', '.avi'}
    extensiones       = extensiones_img | extensiones_video

    # ── Recopilar archivos ───────────────────────────────────
    log_mensaje("Buscando archivos...")
    fotos = []
    if recursivo:
        for raiz, _, archivos in os.walk(ruta_fotos):
            if cancelar.is_set():
                break
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

    if cancelar.is_set():
        log_mensaje("❌ Proceso cancelado.")
        boton_ejecutar.config(state='normal')
        boton_cancelar.config(state='disabled')
        return

    total        = len(fotos)
    total_imgs   = sum(1 for f in fotos if os.path.splitext(f)[1].lower() in extensiones_img)
    total_videos = sum(1 for f in fotos if os.path.splitext(f)[1].lower() in extensiones_video)
    log_mensaje(f"Archivos encontrados: {total} ({total_imgs} fotos, {total_videos} videos)")

    if total == 0:
        log_mensaje("⚠️ No se encontraron archivos.")
        boton_ejecutar.config(state='normal')
        boton_cancelar.config(state='disabled')
        return

    # ── Fase 1 — Calcular MD5 ────────────────────────────────
    log_mensaje("Fase 1 — Calculando hashes MD5...")
    grupos_md5 = defaultdict(list)
    for i, foto in enumerate(fotos):
        if cancelar.is_set():
            break
        try:
            with open(foto, 'rb') as f:
                md5 = hashlib.md5(f.read()).hexdigest()
            grupos_md5[md5].append(foto)
        except Exception as e:
            log_mensaje(f"Error MD5: {os.path.basename(foto)} → {e}")
        actualizar_progreso((i + 1) / total * 30, f"Fase 1 — {i+1} de {total}")

    if cancelar.is_set():
        log_mensaje("❌ Proceso cancelado.")
        boton_ejecutar.config(state='normal')
        boton_cancelar.config(state='disabled')
        return

    # ── Fase 2 — Mover duplicados exactos ────────────────────
    log_mensaje("Fase 2 — Moviendo duplicados exactos...")
    fotos_movidas   = set()
    fotos_restantes = []
    grupo_actual    = 0

    for md5, archivos in grupos_md5.items():
        if cancelar.is_set():
            break
        if len(archivos) > 1:
            grupo_actual += 1
            for idx, archivo in enumerate(archivos):
                if not os.path.exists(archivo):
                    continue
                ext       = os.path.splitext(archivo)[1]
                timestamp = datetime.now().strftime("%d%m%Y%H%M%S%f")[:17]
                if idx == 0:
                    destino = os.path.join(ruta_cuarentena, f"md5-{grupo_actual}_{timestamp}{ext}")
                else:
                    destino = os.path.join(ruta_cuarentena, f"md5-{grupo_actual}-{idx}_{timestamp}{ext}")
                shutil.move(archivo, destino)
                fotos_movidas.add(archivo)
        else:
            fotos_restantes.append(archivos[0])

    if cancelar.is_set():
        log_mensaje("❌ Proceso cancelado.")
        boton_ejecutar.config(state='normal')
        boton_cancelar.config(state='disabled')
        return

    log_mensaje(f"Duplicados exactos: {grupo_actual} grupos")
    log_mensaje(f"Archivos para análisis visual: {len(fotos_restantes)}")

    if len(fotos_restantes) == 0:
        actualizar_progreso(100, "¡Completado!")
        log_mensaje("✅ ¡Proceso completado!")
        boton_ejecutar.config(state='normal')
        boton_cancelar.config(state='disabled')
        return

    # ── Fase 3 — Calcular pHash + dHash (solo imágenes) ─────
    log_mensaje("Fase 3 — Calculando pHash y dHash...")
    hashes_p      = {}
    hashes_d      = {}
    errores_hash  = 0
    imgs_restantes = [f for f in fotos_restantes if os.path.splitext(f)[1].lower() in extensiones_img]

    for i, ruta in enumerate(imgs_restantes):
        if cancelar.is_set():
            break
        try:
            img          = Image.open(ruta)
            hashes_p[ruta] = imagehash.phash(img)
            hashes_d[ruta] = imagehash.dhash(img)
        except Exception as e:
            errores_hash += 1
            log_mensaje(f"Error hash: {os.path.basename(ruta)} → {e}")
        actualizar_progreso(30 + (i + 1) / len(imgs_restantes) * 40,
                            f"Fase 3 — {i+1} de {len(imgs_restantes)}")

    if cancelar.is_set():
        log_mensaje("❌ Proceso cancelado.")
        boton_ejecutar.config(state='normal')
        boton_cancelar.config(state='disabled')
        return

    log_mensaje(f"Hashes calculados: {len(hashes_p)} | Errores: {errores_hash}")

    # ── Fase 4 — Comparar pHash AND dHash ────────────────────
    log_mensaje("Fase 4 — Comparando similares visuales (pHash AND dHash)...")
    rutas_lista   = list(hashes_p.keys())
    movidas_phash = set()
    grupo_phash   = 0

    for i in range(len(rutas_lista)):
        if cancelar.is_set():
            break
        if rutas_lista[i] in movidas_phash:
            continue

        hubo = False
        cont = 0

        for c in range(i + 1, len(rutas_lista)):
            if cancelar.is_set():
                break
            if rutas_lista[c] in movidas_phash:
                continue

            dist_p = hashes_p[rutas_lista[i]] - hashes_p[rutas_lista[c]]
            dist_d = hashes_d[rutas_lista[i]] - hashes_d[rutas_lista[c]]

            # AND — ambos deben detectar similitud
            if dist_p <= umbral and dist_d <= umbral:
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

    if cancelar.is_set():
        log_mensaje("❌ Proceso cancelado.")
    else:
        actualizar_progreso(100, "¡Completado!")
        log_mensaje(f"Similares visuales: {len(movidas_phash)}")
        log_mensaje("✅ ¡Proceso completado!")

    boton_ejecutar.config(state='normal')
    boton_cancelar.config(state='disabled')

def iniciar_ejecucion():
    boton_ejecutar.config(state='disabled')
    boton_cancelar.config(state='normal')
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

# Fila 4 - Botones
frame_botones = tk.Frame(ventana)
frame_botones.grid(row=4, column=1, pady=10)
boton_ejecutar = tk.Button(frame_botones, text="Ejecutar Fotox", width=20,
                           state='disabled', command=iniciar_ejecucion)
boton_ejecutar.pack(side='left', padx=5)
boton_cancelar = tk.Button(frame_botones, text="Cancelar", width=10,
                           state='disabled', command=cancelar_proceso, fg='red')
boton_cancelar.pack(side='left', padx=5)

# Fila 5 - Barra de progreso
barra_progreso = ttk.Progressbar(ventana, length=600, mode='determinate')
barra_progreso.grid(row=5, column=0, columnspan=3, padx=10, pady=5)
label_progreso = tk.Label(ventana, text="", fg='gray', font=('Arial', 8))
label_progreso.grid(row=6, column=0, columnspan=3)

# Fila 7 - Log
log = tk.Text(ventana, height=8, width=76, state='disabled', font=('Courier', 8))
log.grid(row=7, column=0, columnspan=3, padx=10, pady=10)

ventana.mainloop()
