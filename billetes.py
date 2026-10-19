import argparse
import csv
import os
import sys
from collections import Counter, deque
from glob import glob

import cv2
import numpy as np

# --------------------------------------------------------------------------
# Configuracion
# --------------------------------------------------------------------------
DENOMINACIONES = (20, 50, 100, 200, 500, 1000)
CARPETA_PLANTILLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plantillas")
EXTENSIONES = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

ANCHO, ALTO = 600, 280          
PESO_COLOR, PESO_ORB = 0.35, 0.65
INLIERS_REF = 40                
UMBRAL_ACEPTACION = 0.35        
FRAMES_VOTO = 7                 
VOTOS_MINIMOS = 4

_orb = cv2.ORB_create(nfeatures=1500)
_clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
_bf = cv2.BFMatcher(cv2.NORM_HAMMING)


# --------------------------------------------------------------------------
# 1. Segmentacion del billete
# --------------------------------------------------------------------------
def _ordenar_puntos(pts):
    """Devuelve los 4 puntos como tl, tr, br, bl."""
    pts = np.asarray(pts, dtype=np.float32)
    suma = pts.sum(axis=1)
    dif = np.diff(pts, axis=1).ravel()
    return np.array([pts[np.argmin(suma)], pts[np.argmin(dif)],
                     pts[np.argmax(suma)], pts[np.argmax(dif)]], dtype=np.float32)


def segmentar(img):
    """
    Localiza el billete y lo endereza.
    Devuelve (recorte 600x280, caja 4x2 en coords originales o None, valido).
    Si no encuentra un billete plausible devuelve la imagen completa
    redimensionada y valido=False.
    """
    h, w = img.shape[:2]
    escala = min(1.0, 640.0 / max(h, w))
    peq = cv2.resize(img, None, fx=escala, fy=escala) if escala < 1 else img.copy()

    gris = cv2.cvtColor(peq, cv2.COLOR_BGR2GRAY)
    gris = cv2.GaussianBlur(gris, (5, 5), 0)
    bordes = cv2.Canny(gris, 40, 120)
    k = np.ones((5, 5), np.uint8)
    bordes = cv2.dilate(bordes, k, iterations=2)
    bordes = cv2.morphologyEx(bordes, cv2.MORPH_CLOSE, k, iterations=3)

    contornos, _ = cv2.findContours(bordes, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    fallback = cv2.resize(img, (ANCHO, ALTO))
    if not contornos:
        return fallback, None, False

    c = max(contornos, key=cv2.contourArea)
    area = cv2.contourArea(c)
    if area < 0.08 * peq.shape[0] * peq.shape[1]:
        return fallback, None, False

    rect = cv2.minAreaRect(c)
    (rw, rh) = rect[1]
    if rw < 1 or rh < 1:
        return fallback, None, False
    relleno = area / (rw * rh)
    aspecto = max(rw, rh) / min(rw, rh)

    caja = cv2.boxPoints(rect) / escala
    pts = _ordenar_puntos(caja)
    ancho = np.linalg.norm(pts[1] - pts[0])
    alto = np.linalg.norm(pts[3] - pts[0])
    if alto > ancho:                      
        pts = np.roll(pts, -1, axis=0)

    dst = np.array([[0, 0], [ANCHO - 1, 0], [ANCHO - 1, ALTO - 1], [0, ALTO - 1]], np.float32)
    M = cv2.getPerspectiveTransform(pts, dst)
    recorte = cv2.warpPerspective(img, M, (ANCHO, ALTO))

    valido = relleno > 0.70 and 1.4 < aspecto < 3.2
    return recorte, caja.astype(int), valido


# --------------------------------------------------------------------------
# 2. Caracteristicas
# --------------------------------------------------------------------------
def extraer(recorte):
    recorte = cv2.resize(recorte, (ANCHO, ALTO))
    hsv = cv2.cvtColor(recorte, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [18, 8], [0, 180, 0, 256])
    hist = cv2.normalize(hist, None, alpha=1.0, norm_type=cv2.NORM_L1).astype(np.float32).ravel()

    gris = _clahe.apply(cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY))
    kp, des = _orb.detectAndCompute(gris, None)
    pts = np.float32([p.pt for p in kp]) if kp else np.zeros((0, 2), np.float32)
    return {"hist": hist, "pts": pts, "des": des}


def puntaje_color(f1, f2):
    r = cv2.compareHist(f1["hist"], f2["hist"], cv2.HISTCMP_CORREL)
    return float(max(0.0, r))


def puntaje_orb(consulta, plantilla):
    """Inliers RANSAC / INLIERS_REF, recortado a [0,1]."""
    dq, dt = consulta["des"], plantilla["des"]
    if dq is None or dt is None or len(dq) < 8 or len(dt) < 8:
        return 0.0, 0
    pares = _bf.knnMatch(dq, dt, k=2)
    buenos = [p[0] for p in pares if len(p) == 2 and p[0].distance < 0.75 * p[1].distance]
    if len(buenos) < 8:
        return 0.0, len(buenos)
    src = consulta["pts"][[m.queryIdx for m in buenos]].reshape(-1, 1, 2)
    dst = plantilla["pts"][[m.trainIdx for m in buenos]].reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    if H is None or mask is None:
        return 0.0, len(buenos)
    inliers = int(mask.sum())
    return min(inliers / INLIERS_REF, 1.0), inliers


# --------------------------------------------------------------------------
# 3. Plantillas y clasificacion
# --------------------------------------------------------------------------
def listar_imagenes(carpeta):
    return sorted(f for f in glob(os.path.join(carpeta, "*"))
                  if f.lower().endswith(EXTENSIONES))


def cargar_plantillas(carpeta=CARPETA_PLANTILLAS):
    plantillas = []
    for den in DENOMINACIONES:
        for archivo in listar_imagenes(os.path.join(carpeta, str(den))):
            img = cv2.imread(archivo)
            if img is None:
                continue
            f = extraer(img)
            f["den"], f["archivo"] = den, archivo
            plantillas.append(f)
    return plantillas


def clasificar(recorte, plantillas):
    """
    Devuelve (denominacion o None, puntaje_mejor, detalle{den: puntaje}).
    """
    if not plantillas:
        raise RuntimeError("No hay plantillas. Usa primero el modo 'registrar'.")
    f = extraer(recorte)
    detalle = {}
    for p in plantillas:
        s = PESO_COLOR * puntaje_color(f, p) + PESO_ORB * puntaje_orb(f, p)[0]
        if s > detalle.get(p["den"], -1):
            detalle[p["den"]] = s
    mejor = max(detalle, key=detalle.get)
    if detalle[mejor] < UMBRAL_ACEPTACION:
        return None, detalle[mejor], detalle
    return mejor, detalle[mejor], detalle


# --------------------------------------------------------------------------
# Utilidades de dibujo
# --------------------------------------------------------------------------
def anotar(img, caja, texto, color=(0, 200, 0)):
    out = img.copy()
    if caja is not None:
        cv2.polylines(out, [np.asarray(caja, np.int32).reshape(-1, 1, 2)], True, color, 3)
        x, y = int(caja[:, 0].min()), int(caja[:, 1].min())
    else:
        x, y = 10, 40
    y = max(y - 10, 30)
    cv2.putText(out, texto, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 5, cv2.LINE_AA)
    cv2.putText(out, texto, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2, cv2.LINE_AA)
    return out


def etiqueta(den, conf):
    return "No reconocido" if den is None else "$%d MXN (%d%%)" % (den, round(conf * 100))


# --------------------------------------------------------------------------
# Modos
# --------------------------------------------------------------------------
def modo_registrar(args):
    carpeta = os.path.join(CARPETA_PLANTILLAS, str(args.den))
    os.makedirs(carpeta, exist_ok=True)
    n = len(listar_imagenes(carpeta))

    if args.imagen:
        for ruta in args.imagen:
            img = cv2.imread(ruta)
            if img is None:
                print("No se pudo leer", ruta)
                continue
            recorte, _, valido = segmentar(img)
            n += 1
            destino = os.path.join(carpeta, "%d_%02d.jpg" % (args.den, n))
            cv2.imwrite(destino, recorte)
            print("Guardada %s (segmentacion %s)" % (destino, "OK" if valido else "NO detectada, se uso la foto completa"))
        return

    cap = cv2.VideoCapture(args.camara)
    if not cap.isOpened():
        sys.exit("No se pudo abrir la camara %d" % args.camara)
    print("ESPACIO = guardar plantilla de $%d | Q = salir" % args.den)
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        recorte, caja, valido = segmentar(frame)
        vista = anotar(frame, caja if valido else None,
                       "Plantillas $%d: %d  (ESPACIO guarda)" % (args.den, n),
                       (0, 200, 0) if valido else (0, 0, 255))
        cv2.imshow("Registrar plantillas", vista)
        k = cv2.waitKey(1) & 0xFF
        if k in (ord("q"), 27):
            break
        if k == 32 and valido:
            n += 1
            destino = os.path.join(carpeta, "%d_%02d.jpg" % (args.den, n))
            cv2.imwrite(destino, recorte)
            print("Guardada", destino)
    cap.release()
    cv2.destroyAllWindows()


def modo_imagen(args):
    plantillas = cargar_plantillas()
    img = cv2.imread(args.ruta)
    if img is None:
        sys.exit("No se pudo leer " + args.ruta)
    recorte, caja, valido = segmentar(img)
    den, conf, detalle = clasificar(recorte, plantillas)
    print("Segmentacion:", "OK" if valido else "no detectada (se usa la imagen completa)")
    print("Resultado   :", etiqueta(den, conf))
    for d in sorted(detalle):
        print("   $%-5d puntaje %.3f" % (d, detalle[d]))
    if args.salida:
        cv2.imwrite(args.salida, anotar(img, caja, etiqueta(den, conf)))
        print("Imagen anotada:", args.salida)


def modo_camara(args):
    plantillas = cargar_plantillas()
    if not plantillas:
        sys.exit("No hay plantillas. Corre antes: python billetes.py registrar --den 100")
    cap = cv2.VideoCapture(args.camara)
    if not cap.isOpened():
        sys.exit("No se pudo abrir la camara %d" % args.camara)
    historial = deque(maxlen=FRAMES_VOTO)
    n = 0
    print("Q = salir | S = guardar captura")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        recorte, caja, valido = segmentar(frame)
        if valido:
            den, conf, _ = clasificar(recorte, plantillas)
            historial.append(den)
            votos = Counter(d for d in historial if d is not None)
            if votos and votos.most_common(1)[0][1] >= VOTOS_MINIMOS:
                ganador = votos.most_common(1)[0][0]
                vista = anotar(frame, caja, etiqueta(ganador, conf))
            else:
                vista = anotar(frame, caja, "Analizando...", (0, 200, 255))
        else:
            historial.clear()
            vista = anotar(frame, None, "Muestra un billete a la camara", (0, 0, 255))
        cv2.imshow("Reconocedor de billetes", vista)
        k = cv2.waitKey(1) & 0xFF
        if k in (ord("q"), 27):
            break
        if k == ord("s"):
            n += 1
            cv2.imwrite("captura_%02d.jpg" % n, vista)
    cap.release()
    cv2.destroyAllWindows()


def modo_evaluar(args):
    """Carpeta de pruebas: <carpeta>/<denominacion>/*.jpg"""
    plantillas = cargar_plantillas()
    if not plantillas:
        sys.exit("No hay plantillas. Usa primero el modo 'registrar'.")
    etiquetas = list(DENOMINACIONES) + [None]
    matriz = {r: Counter() for r in DENOMINACIONES}
    filas = []
    total = aciertos = 0
    for real in DENOMINACIONES:
        for ruta in listar_imagenes(os.path.join(args.carpeta, str(real))):
            img = cv2.imread(ruta)
            if img is None:
                continue
            recorte, _, valido = segmentar(img)
            pred, conf, _ = clasificar(recorte, plantillas)
            matriz[real][pred] += 1
            total += 1
            aciertos += int(pred == real)
            filas.append((ruta, real, pred, round(conf, 3), valido))
    if total == 0:
        sys.exit("No se encontraron imagenes en %s/<denominacion>/" % args.carpeta)

    print("\nMatriz de confusion (filas = real, columnas = predicho; ? = no reconocido)")
    print("real\\pred " + "".join("%7s" % ("?" if e is None else e) for e in etiquetas))
    for r in DENOMINACIONES:
        if sum(matriz[r].values()):
            print("%-9d " % r + "".join("%7d" % matriz[r][e] for e in etiquetas))
    print("\nExactitud global: %d/%d = %.1f%%" % (aciertos, total, 100.0 * aciertos / total))
    for r in DENOMINACIONES:
        t = sum(matriz[r].values())
        if t:
            print("   $%-5d %d/%d (%.0f%%)" % (r, matriz[r][r], t, 100.0 * matriz[r][r] / t))

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["archivo", "real", "predicho", "puntaje", "segmentacion_ok"])
            w.writerows(filas)
        print("Detalle guardado en", args.csv)


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Reconocedor de billetes mexicanos (avance)")
    sub = ap.add_subparsers(dest="modo", required=True)

    p = sub.add_parser("registrar", help="guardar plantillas de una denominacion")
    p.add_argument("--den", type=int, required=True, choices=DENOMINACIONES)
    p.add_argument("--imagen", nargs="+", help="fotos en lugar de camara")
    p.add_argument("--camara", type=int, default=0)
    p.set_defaults(f=modo_registrar)

    p = sub.add_parser("imagen", help="clasificar una foto")
    p.add_argument("ruta")
    p.add_argument("--salida", help="guardar la imagen anotada")
    p.set_defaults(f=modo_imagen)

    p = sub.add_parser("camara", help="reconocimiento en vivo")
    p.add_argument("--camara", type=int, default=0)
    p.set_defaults(f=modo_camara)

    p = sub.add_parser("evaluar", help="exactitud sobre fotos etiquetadas")
    p.add_argument("carpeta", help="carpeta con subcarpetas 20, 50, 100, ...")
    p.add_argument("--csv", help="guardar detalle por imagen")
    p.set_defaults(f=modo_evaluar)

    args = ap.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
