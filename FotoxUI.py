import tkinter as tk
from tkinter import filedialog

ventana = tk.Tk()
ventana.title("Fotox")
ventana.geometry("600x400")

def buscar_fotos():
    ruta=filedialog.askdirectory(title="Selecciona el directorio de fotos")

    if(ruta):
        entry_fotos.delete(0,tk.END)
        entry_fotos.insert(0,ruta)




def buscar_cuarentena():
    ruta=filedialog.askdirectory(title="Selecciona el directorio de cuarentena")

    if(ruta):
        entry_cuarentena.delete(0,tk.END)
        entry_cuarentena.insert(0,ruta)







#fila 0 - Ruta de Fotos
label_fotos = tk.Label(ventana, text="Ruta de Fotos:")
label_fotos.grid(row=0, column=0, padx=10, pady=10)

entry_fotos = tk.Entry(ventana, width=50)
entry_fotos.grid(row=0,column=1, padx=10, pady=10)

boton_fotos = tk.Button(ventana, text="Buscar", command=buscar_fotos)
boton_fotos.grid(row=0, column=2, padx=10, pady=10)



#fila 1 - Ruta de Cuarentena 
label_cuarentena = tk.Label(ventana, text="Ruta de Cuarentena:")
label_cuarentena.grid(row=1, column=0, padx=10, pady=10)

entry_cuarentena = tk.Entry(ventana, width=50)
entry_cuarentena.grid(row=1,column=1, padx=10, pady=10)

boton_cuarentena = tk.Button(ventana, text="Buscar", command=buscar_cuarentena)
boton_cuarentena.grid(row=1, column=2, padx=10, pady=10)



#fila 2 - Ruta de Cuarentena 
var_recursivo = tk.BooleanVar(value=True)
checkbox =tk.Checkbutton(ventana, text="Buscar en Sub-Carpetas", variable=var_recursivo)
checkbox.grid(row=2, column=1, padx=10, pady=10)


# Fila 3 - Umbral pHash
label_umbral = tk.Label(ventana, text="Nivel de Similitud:")
label_umbral.grid(row=3, column=0, padx=10, pady=10)

spinbox_umbral = tk.Spinbox(ventana, from_=0, to=64, width=5)
spinbox_umbral.delete(0, tk.END)
spinbox_umbral.insert(0, 10)
spinbox_umbral.grid(row=3, column=1, padx=10, pady=10, sticky='w')


# Descripción debajo del spinbox
label_desc_umbral = tk.Label(ventana, text="Menor número = solo fotos casi idénticas | Mayor número = fotos más diferentes", 
                              fg='gray', font=('Arial', 8))
label_desc_umbral.grid(row=4, column=1, padx=10, sticky='w')




ventana.mainloop()
