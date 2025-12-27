"""
Servicio de reconocimiento facial con DeepFace
Sistema de nivel bancario con anti-spoofing y liveness detection
"""
import base64
import io
import logging
from typing import Tuple, TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np
    from PIL import Image
    import cv2

logger = logging.getLogger(__name__)

# Lazy imports - solo se cargan cuando se necesitan
def _import_dependencies():
    """Import heavy dependencies only when needed"""
    try:
        import numpy as np
        from PIL import Image
        import cv2
        return np, Image, cv2
    except ImportError as e:
        logger.error(f"Failed to import face recognition dependencies: {e}")
        raise ImportError(
            "Face recognition dependencies not installed. "
            "Run: pip install deepface opencv-python tf-keras numpy retina-face"
        )

# Configuración de DeepFace
FACE_MODEL = "Facenet512"  # Modelo más robusto: VGG-Face, Facenet, Facenet512, OpenFace, DeepFace, DeepID, ArcFace
DISTANCE_METRIC = "cosine"  # cosine, euclidean, euclidean_l2
DETECTOR_BACKEND = "retinaface"  # opencv, ssd, dlib, mtcnn, retinaface, mediapipe
VERIFICATION_THRESHOLD = 0.40  # Threshold para Facenet512 con cosine (más bajo = más estricto)


class FaceRecognitionError(Exception):
    """Error base para reconocimiento facial"""
    pass


class NoFaceDetectedError(FaceRecognitionError):
    """No se detectó ningún rostro en la imagen"""
    pass


class MultipleFacesError(FaceRecognitionError):
    """Se detectaron múltiples rostros"""
    pass


class LowQualityImageError(FaceRecognitionError):
    """Imagen de baja calidad"""
    pass


class LivenessCheckFailedError(FaceRecognitionError):
    """Falló la verificación de vida (posible spoofing)"""
    pass


def decode_base64_image(base64_string: str) -> Any:
    """
    Decodifica una imagen base64 a formato numpy array (BGR)

    Args:
        base64_string: Imagen codificada en base64

    Returns:
        np.ndarray: Imagen en formato BGR para OpenCV

    Raises:
        ValueError: Si la imagen no se puede decodificar
    """
    np, Image, cv2 = _import_dependencies()

    try:
        # Remover prefijo data:image si existe
        if "base64," in base64_string:
            base64_string = base64_string.split("base64,")[1]

        # Decodificar base64
        image_bytes = base64.b64decode(base64_string)

        # Convertir a PIL Image
        pil_image = Image.open(io.BytesIO(image_bytes))

        # Convertir RGB a BGR para OpenCV
        image_array = np.array(pil_image)
        if len(image_array.shape) == 2:  # Grayscale
            image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2BGR)
        elif image_array.shape[2] == 4:  # RGBA
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2BGR)
        elif image_array.shape[2] == 3:  # RGB
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

        return image_array
    except Exception as e:
        logger.error(f"Error decoding base64 image: {e}")
        raise ValueError("Imagen inválida o corrupta")


def check_image_quality(image: Any) -> Tuple[bool, float]:
    """
    Verifica la calidad de la imagen usando métricas avanzadas

    Args:
        image: Imagen en formato numpy array (BGR)

    Returns:
        Tuple[bool, float]: (es_buena_calidad, puntaje_calidad)
    """
    np, _, cv2 = _import_dependencies()
    # Convertir a escala de grises para análisis
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 1. Verificar resolución mínima
    height, width = gray.shape
    if height < 200 or width < 200:
        return False, 0.0

    # 2. Verificar nitidez usando Laplacian variance
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    sharpness_score = min(laplacian_var / 500.0, 1.0)  # Normalizar

    # 3. Verificar brillo
    mean_brightness = np.mean(gray)
    brightness_score = 1.0 - abs(mean_brightness - 128) / 128  # Óptimo en 128

    # 4. Verificar contraste
    contrast = gray.std()
    contrast_score = min(contrast / 64.0, 1.0)  # Normalizar

    # Calcular puntaje final (ponderado)
    quality_score = (
        sharpness_score * 0.5 +
        brightness_score * 0.3 +
        contrast_score * 0.2
    )

    # Threshold de calidad mínima
    is_good_quality = quality_score >= 0.6 and laplacian_var >= 100

    return is_good_quality, quality_score


def perform_liveness_detection(image: Any) -> Tuple[bool, str]:
    """
    Realiza detección de vida para prevenir spoofing
    Técnicas: análisis de textura, detección de patrones de pantalla, etc.

    Args:
        image: Imagen en formato numpy array (BGR)

    Returns:
        Tuple[bool, str]: (es_persona_real, razón)
    """
    np, _, cv2 = _import_dependencies()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 1. Detectar patrones de moiré (común en fotos de pantallas)
    # Aplicar FFT para detectar patrones repetitivos
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1)

    # Si hay picos muy pronunciados, puede ser una pantalla
    peak_threshold = np.percentile(magnitude_spectrum, 99.5)
    mean_magnitude = np.mean(magnitude_spectrum)

    if peak_threshold > mean_magnitude * 3:
        return False, "Patrón de pantalla detectado (posible foto de foto)"

    # 2. Análisis de textura usando LBP (Local Binary Patterns)
    # Las fotos reales tienen más variación de textura que las falsas
    # Simplificado: verificar varianza de gradientes
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
    texture_variance = np.var(gradient_magnitude)

    if texture_variance < 50:
        return False, "Textura demasiado uniforme (posible impresión o pantalla)"

    # 3. Verificar que no sea una imagen muy plana (foto impresa)
    # Las fotos reales tienen más variación en diferentes regiones
    h, w = gray.shape
    region_size = h // 3
    regions_std = []

    for i in range(3):
        for j in range(3):
            y1, y2 = i * region_size, (i + 1) * region_size
            x1, x2 = j * region_size, (j + 1) * region_size
            if y2 <= h and x2 <= w:
                region = gray[y1:y2, x1:x2]
                regions_std.append(np.std(region))

    std_variance = np.var(regions_std)
    if std_variance < 10:
        return False, "Iluminación demasiado uniforme (posible foto impresa)"

    return True, "Verificaciones de vida pasadas"


async def extract_face_embedding(image_base64: str) -> bytes:
    """
    Extrae el embedding facial de una imagen usando DeepFace

    Args:
        image_base64: Imagen codificada en base64

    Returns:
        bytes: Embedding facial serializado

    Raises:
        NoFaceDetectedError: No se detectó rostro
        MultipleFacesError: Se detectaron múltiples rostros
        LowQualityImageError: Imagen de baja calidad
        LivenessCheckFailedError: Falló la verificación de vida
    """
    try:
        # Importar dependencias
        np, _, _ = _import_dependencies()
        from deepface import DeepFace

        # Decodificar imagen
        image = decode_base64_image(image_base64)

        # Verificar calidad de imagen
        is_good_quality, quality_score = check_image_quality(image)
        if not is_good_quality:
            raise LowQualityImageError(
                f"Imagen de baja calidad (puntaje: {quality_score:.2f}). "
                "Asegúrate de tener buena iluminación y que la imagen esté enfocada."
            )

        # Realizar liveness detection
        is_live, liveness_reason = perform_liveness_detection(image)
        if not is_live:
            raise LivenessCheckFailedError(f"Verificación de vida fallida: {liveness_reason}")

        # Detectar rostros primero
        try:
            faces = DeepFace.extract_faces(
                img_path=image,
                detector_backend=DETECTOR_BACKEND,
                enforce_detection=True,
                align=True
            )
        except ValueError as e:
            if "Face could not be detected" in str(e):
                raise NoFaceDetectedError(
                    "No se detectó ningún rostro en la imagen. "
                    "Asegúrate de que tu rostro esté centrado y bien iluminado."
                )
            raise

        # Verificar que solo haya un rostro
        if len(faces) > 1:
            raise MultipleFacesError(
                f"Se detectaron {len(faces)} rostros. "
                "Asegúrate de que solo tu rostro esté visible en la imagen."
            )

        # Extraer embedding del rostro
        embedding_objs = DeepFace.represent(
            img_path=image,
            model_name=FACE_MODEL,
            detector_backend=DETECTOR_BACKEND,
            enforce_detection=True,
            align=True
        )

        # Obtener el primer (y único) embedding
        embedding = embedding_objs[0]["embedding"]

        # Convertir a bytes para almacenamiento
        embedding_array = np.array(embedding, dtype=np.float32)
        embedding_bytes = embedding_array.tobytes()

        logger.info(f"Embedding extraído exitosamente (tamaño: {len(embedding_bytes)} bytes)")

        return embedding_bytes

    except (NoFaceDetectedError, MultipleFacesError, LowQualityImageError, LivenessCheckFailedError):
        raise
    except Exception as e:
        logger.error(f"Error extracting face embedding: {e}")
        raise FaceRecognitionError(f"Error procesando imagen: {str(e)}")


async def verify_face(image_base64: str, stored_embedding: bytes) -> Tuple[bool, float]:
    """
    Verifica si un rostro coincide con un embedding almacenado

    Args:
        image_base64: Imagen del rostro a verificar (base64)
        stored_embedding: Embedding facial almacenado en la base de datos

    Returns:
        Tuple[bool, float]: (coincide, confianza)

    Raises:
        NoFaceDetectedError: No se detectó rostro
        MultipleFacesError: Se detectaron múltiples rostros
        LowQualityImageError: Imagen de baja calidad
    """
    try:
        # Importar dependencias
        np, _, _ = _import_dependencies()
        from deepface import DeepFace

        # Extraer embedding de la imagen actual
        current_embedding_bytes = await extract_face_embedding(image_base64)

        # Convertir bytes a arrays numpy
        current_embedding = np.frombuffer(current_embedding_bytes, dtype=np.float32)
        stored_embedding_array = np.frombuffer(stored_embedding, dtype=np.float32)

        # Calcular distancia (usamos cosine distance)
        if DISTANCE_METRIC == "cosine":
            # Distancia coseno: 1 - similaridad
            from sklearn.metrics.pairwise import cosine_similarity
            similarity = cosine_similarity(
                current_embedding.reshape(1, -1),
                stored_embedding_array.reshape(1, -1)
            )[0][0]
            distance = 1 - similarity
        elif DISTANCE_METRIC == "euclidean":
            distance = np.linalg.norm(current_embedding - stored_embedding_array)
        elif DISTANCE_METRIC == "euclidean_l2":
            distance = np.sqrt(np.sum((current_embedding - stored_embedding_array) ** 2))
        else:
            distance = np.linalg.norm(current_embedding - stored_embedding_array)

        # Verificar si la distancia está dentro del threshold
        is_match = distance <= VERIFICATION_THRESHOLD

        # Calcular confianza (0-100%)
        # Para cosine: 0 = idéntico, 1 = completamente diferente
        confidence = max(0, min(100, (1 - distance) * 100))

        logger.info(
            f"Face verification: match={is_match}, distance={distance:.4f}, "
            f"confidence={confidence:.2f}%, threshold={VERIFICATION_THRESHOLD}"
        )

        return is_match, confidence

    except (NoFaceDetectedError, MultipleFacesError, LowQualityImageError, LivenessCheckFailedError):
        raise
    except Exception as e:
        logger.error(f"Error verifying face: {e}")
        raise FaceRecognitionError(f"Error verificando rostro: {str(e)}")
