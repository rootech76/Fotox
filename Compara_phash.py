import sys
import warnings
from PIL import Image
import imagehash


ruta1 = sys.argv[1]
ruta2 = sys.argv[2]

warnings.filterwarnings('ignore')

hash1 = imagehash.phash(Image.open(ruta1))
hash2 = imagehash.phash(Image.open(ruta2))

diferencia = hash1 - hash2

print(diferencia)
