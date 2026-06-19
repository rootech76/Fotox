# Fotox

Fotox es una herramienta de línea de comandos desarrollada en PowerShell y Python para detectar y organizar fotos duplicadas o visualmente similares en una biblioteca de imágenes.

## ¿Qué hace?

Fotox analiza una biblioteca de fotos en dos fases:

1. **Detección de duplicados exactos (MD5)** — Identifica archivos idénticos byte a byte, independientemente de su nombre o ubicación.
2. **Detección de similares visuales (pHash)** — Identifica fotos visualmente parecidas aunque hayan sido recomprimidas, descargadas de redes sociales o tengan pequeñas diferencias.

Las fotos detectadas son movidas a una carpeta de **cuarentena** para revisión manual antes de cualquier eliminación definitiva.

## Requisitos

- Windows con PowerShell 5.1 o superior
- Python 3.x
- Librerías Python:
  - Pillow
  - imagehash

```bash
pip install Pillow imagehash
```

## Estructura del proyecto
Fotox/

DFotos.ps1          # Script principal en PowerShell

Compara_phash.py    # Script de comparación visual en Python

README.md           # Este archivo



## Uso

```powershell
& 'R:\WorkStation\Scripts\Fotox\DFotos.ps1'
```

El script procesará las fotos y moverá los duplicados a la carpeta CUARENTENA definida en la configuración.

## Sistema de nombrado en cuarentena

Los archivos movidos a cuarentena siguen esta convención:

| Prefijo | Significado | Ejemplo |
|---|---|---|
| `md5-N` | Original del grupo N (duplicado exacto) | `md5-1_18062026200310542.jpg` |
| `md5-N-X` | Copia X del grupo N (duplicado exacto) | `md5-1-1_18062026200310891.jpg` |
| `phash-N` | Original del grupo N (similar visual) | `phash-1_18062026200615123.jpg` |
| `phash-N-X` | Similar X del grupo N (similar visual) | `phash-1-1_18062026200615456.jpg` |

El timestamp al final (`ddMMyyyyHHmmssfff`) garantiza nombres únicos.

## Flujo de trabajo recomendado

1. Ejecutar Fotox apuntando al directorio de fotos
2. Revisar manualmente la carpeta CUARENTENA
3. Eliminar definitivamente las fotos duplicadas confirmadas
4. Devolver al directorio original las fotos que no sean duplicadas

## Configuración

Las rutas se configuran directamente en `DFotos.ps1`:

```powershell
$RutaFotos      = 'R:\Midia\Fotos'
$RutaCUARENTENA = 'R:\Midia\Fotos\CUARENTENA'
$RutaScript     = 'R:\WorkStation\Scripts\Fotox'
```

## Tecnologías utilizadas

- **PowerShell** — Orquestación del proceso, cálculo MD5, movimiento de archivos
- **Python + Pillow** — Procesamiento de imágenes
- **imagehash** — Cálculo de hash perceptual (pHash)
- **Git** — Control de versiones del proyecto
