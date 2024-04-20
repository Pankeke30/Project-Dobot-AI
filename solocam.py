import cv2

# Obtener una lista de cámaras disponibles
def listar_camaras_conectadas():
    lista_camaras = []
    for i in range(10):  # Comprobar hasta 10 índices de cámaras
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            lista_camaras.append(i)
            cap.release()
    return lista_camaras

# Imprimir la lista de cámaras conectadas
camaras_conectadas = listar_camaras_conectadas()
print("Cámaras conectadas:")
for i, indice_camara in enumerate(camaras_conectadas):
    print(f"{i+1}. Cámara {indice_camara}")

# Pedir al usuario que elija una cámara
camara_seleccionada = int(input("Ingresa el número de la cámara que deseas usar: ")) - 1

# Verificar si la cámara seleccionada es válida
if camara_seleccionada < 0 or camara_seleccionada >= len(camaras_conectadas):
    print("Selección de cámara no válida. Por favor, elige un número de cámara válido.")
else:
    print(f"Cámara seleccionada: Cámara {camaras_conectadas[camara_seleccionada]}")
