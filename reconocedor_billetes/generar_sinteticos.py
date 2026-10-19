#!/usr/bin/env python3
"""
Genera billetes SINTETICOS (no son billetes reales) solo para comprobar que el
pipeline corre de punta a punta sin necesidad de fotos. NO sirve para medir la
exactitud real: eso se hace con fotos reales (ver README).

Uso: python generar_sinteticos.py salida/
Crea salida/plantillas/<den>/*.jpg y salida/pruebas/<den>/*.jpg
"""
import os
import sys

import cv2
import numpy as np

COLORES_BGR = {20: (200, 120, 40), 50: (150, 60, 200), 100: (50, 50, 210),
               200: (70, 170, 60), 500: (60, 110, 150), 1000: (110, 50, 120)}


def billete(den, ancho=600, alto=280):
    rng = np.random.default_rng(den)                     
    img = np.full((alto, ancho, 3), COLORES_BGR[den], np.uint8)
    for _ in range(120):                                 
        c = tuple(int(v) for v in rng.integers(0, 255, 3))
        p1 = tuple(int(v) for v in rng.integers(0, [ancho, alto]))
        p2 = tuple(int(v) for v in rng.integers(0, [ancho, alto]))
        if rng.random() < 0.5:
            cv2.line(img, p1, p2, c, int(rng.integers(1, 4)))
        else:
            cv2.circle(img, p1, int(rng.integers(5, 30)), c, int(rng.integers(1, 3)))
    cv2.putText(img, str(den), (30, 170), cv2.FONT_HERSHEY_DUPLEX, 3.5, (255, 255, 255), 8, cv2.LINE_AA)
    cv2.putText(img, "BANCO DE MEXICO", (230, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (240, 240, 240), 2, cv2.LINE_AA)
    cv2.rectangle(img, (4, 4), (ancho - 5, alto - 5), (255, 255, 255), 4)
    return img


def escena(den, semilla):
    rng = np.random.default_rng(1000 * den + semilla)
    fondo = np.full((720, 960, 3), 110, np.uint8)
    fondo = cv2.add(fondo, rng.integers(0, 40, fondo.shape, dtype=np.uint8))
    b = billete(den)
    b = cv2.convertScaleAbs(b, alpha=rng.uniform(0.75, 1.2), beta=rng.uniform(-25, 25))
    h, w = b.shape[:2]
    esc = rng.uniform(0.8, 1.15)
    ang = rng.uniform(-35, 35)
    cx, cy = 480 + rng.uniform(-60, 60), 360 + rng.uniform(-40, 40)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), ang, esc)
    M[:, 2] += (cx - w / 2, cy - h / 2)
    capa = cv2.warpAffine(b, M, (960, 720))
    mask = cv2.warpAffine(np.full((h, w), 255, np.uint8), M, (960, 720))
    out = np.where(mask[..., None] > 0, capa, fondo)
    out = cv2.GaussianBlur(out, (3, 3), 0)
    ruido = rng.normal(0, 6, out.shape)
    return np.clip(out + ruido, 0, 255).astype(np.uint8)


def main(destino):
    for den in COLORES_BGR:
        os.makedirs(os.path.join(destino, "plantillas", str(den)), exist_ok=True)
        os.makedirs(os.path.join(destino, "pruebas", str(den)), exist_ok=True)
        cv2.imwrite(os.path.join(destino, "plantillas", str(den), "%d_01.jpg" % den), billete(den))
        for i in range(8):
            cv2.imwrite(os.path.join(destino, "pruebas", str(den), "%d_%02d.jpg" % (den, i)), escena(den, i))
    print("Listo en", destino)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sinteticos")
