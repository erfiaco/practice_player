# Prueba este código simple
from gpiozero import Button
import time

# Pon aquí el GPIO que falla (ej: 6 o 22)
btn = Button(5, pull_up=True, bounce_time=0.1)

contador = 0
def conteo():
    global contador
    contador += 1
    print(f"Pulsación #{contador} detectada")

btn.when_pressed = conteo

print("Pulsa el botón 20 veces...")
while True:
    time.sleep(0.1)
