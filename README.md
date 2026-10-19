# Reconocedor de billetes mexicanos (avance)

Reconoce la denominación de un billete (20, 50, 100, 200, 500, 1000) con la cámara usando Python + OpenCV.

## Instalación
```
pip install -r requirements.txt
```

## Uso (4 pasos)

1. **Registrar plantillas** (2–3 fotos por denominación, frente y reverso; fondo liso y buena luz):
   ```
   python billetes.py registrar --den 100            # con la cámara (ESPACIO guarda, Q sale)
   python billetes.py registrar --den 100 --imagen foto1.jpg foto2.jpg
   ```
2. **Probar con una foto:**
   ```
   python billetes.py imagen foto.jpg --salida resultado.jpg
   ```
3. **Cámara en vivo:**
   ```
   python billetes.py camara
   ```
4. **Medir exactitud con fotos reales** (carpeta `pruebas/20/`, `pruebas/50/`, ... con fotos DISTINTAS a las plantillas):
   ```
   python billetes.py evaluar pruebas --csv detalle.csv
   ```

## Cómo funciona
1. Segmentación: Canny + contorno más grande + rectángulo rotado + corrección de perspectiva (billete de 600×280).
2. Características: histograma de color HSV + puntos ORB con verificación RANSAC.
3. Clasificación: puntaje = 0.35·color + 0.65·ORB contra las plantillas de cada denominación; gana el mayor. Bajo 0.35 → "No reconocido".
4. En cámara en vivo se suaviza con votación de los últimos 7 cuadros.

`generar_sinteticos.py` crea billetes falsos solo para comprobar que el código corre; **no** mide la exactitud real.
