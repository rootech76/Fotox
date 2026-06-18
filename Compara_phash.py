import sys
import warnings
from PIL import Image
import imagehash

warnings.filterwarnings('ignore')

archivo_entrada = sys.argv[1]
archivo_salida = sys.argv[2]
UMBRAL = 10

with open(archivo_entrada, 'r', encoding='utf-8') as f:
    rutas = f.read().splitlines()

# Calcular todos los pHash
print(f"Calculando pHash de {len(rutas)} fotos...")
hashes = {}
for i, ruta in enumerate(rutas):
    try:
        hashes[ruta] = imagehash.phash(Image.open(ruta))
        print(f"\rCalculando pHash {i+1} de {len(rutas)}", end='')
    except Exception:
        pass

print("\nComparando pares...")
rutas_lista = list(hashes.keys())
movidas = set()
grupo = 0
similares = []

for i in range(len(rutas_lista)):
    if rutas_lista[i] in movidas:
        continue
    
    hubo = False
    cont = 0
    
    for c in range(i + 1, len(rutas_lista)):
        if rutas_lista[c] in movidas:
            continue
        
        distancia = hashes[rutas_lista[i]] - hashes[rutas_lista[c]]
        if distancia <= UMBRAL:
            if not hubo:
                grupo += 1
                hubo = True
            cont += 1
            similares.append(f"{grupo}-{cont}||{rutas_lista[c]}")
            movidas.add(rutas_lista[c])
    
    if hubo:
        similares.append(f"{grupo}||{rutas_lista[i]}")
        movidas.add(rutas_lista[i])

with open(archivo_salida, 'w', encoding='utf-8') as f:
    f.write('\n'.join(similares))

print(f"Similares encontrados: {len(movidas)}")
