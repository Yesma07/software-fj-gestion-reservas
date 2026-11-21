# ==========================================================
# Nombre del estudiante: Yesid David Marín González
# Grupo: 213023_189
# Programa: Ingeniería de Sistemas
# Curso: Programación (213023) - Fase 4
# Código Fuente: Autoría propia
#
# Módulo: registro_logs.py
# Descripción:
# Centraliza el registro de eventos y errores del sistema en el archivo
# logs/software_fj.log, usando el módulo estándar logging. Cada línea
# del archivo incluye fecha, hora, nivel (INFO / ERROR / CRITICAL) y el
# mensaje. Cuando un error proviene de otro (encadenamiento de
# excepciones), también se registra la causa original.
#
# El archivo de logs es el único uso de archivos del sistema: la
# información de clientes, servicios y reservas vive solo en memoria.
# ==========================================================


import logging                     # Módulo estándar para registrar eventos
import sys                         # Se usa como salida alternativa si el archivo falla
from pathlib import Path           # Manejo de rutas independiente del sistema operativo


# Carpeta "logs" ubicada junto a este archivo, sin importar desde dónde se ejecute
CARPETA_LOGS = Path(__file__).resolve().parent / "logs"
# Ruta completa del archivo de logs
ARCHIVO_LOG = CARPETA_LOGS / "software_fj.log"
# Formato de cada línea: fecha y hora | nivel | mensaje
FORMATO = "%(asctime)s | %(levelname)-8s | %(message)s"
# Formato de la fecha y la hora
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"


def _configurar_logger():
    """
    Crea y configura el logger del sistema. Si no es posible crear el
    archivo de logs (por ejemplo, por falta de permisos), el sistema no
    se detiene: los registros se envían a la consola como respaldo.
    """
    logger = logging.getLogger("software_fj")      # Logger con nombre propio del sistema
    if logger.handlers:                            # Si ya estaba configurado, se reutiliza
        return logger                                                   # Ya configurado: se reutiliza
    logger.setLevel(logging.INFO)                  # Se registran INFO y niveles superiores
    formato = logging.Formatter(FORMATO, FORMATO_FECHA)  # Formato común de las líneas

    try:                                           # La creación del archivo puede fallar
        CARPETA_LOGS.mkdir(exist_ok=True)          # Se crea la carpeta si no existe
        manejador = logging.FileHandler(ARCHIVO_LOG, encoding="utf-8")  # Escritura en archivo
    except OSError as error:
        manejador = logging.StreamHandler(sys.stderr)  # Respaldo: escribir en consola
        print(f"No se pudo crear el archivo de logs ({error}); se usará la consola.",  # Aviso
              file=sys.stderr)
    manejador.setFormatter(formato)                # Se aplica el formato al manejador
    logger.addHandler(manejador)                   # Se conecta el manejador al logger
    return logger                                  # Logger listo para usarse


# Logger único compartido por todo el sistema
_logger = _configurar_logger()                 # Se configura una sola vez al importar


def registrar_evento(mensaje):
    """Registra un evento normal del sistema (nivel INFO)."""
    _logger.info(mensaje)                                      # Línea INFO en el archivo


def registrar_error(mensaje, error=None):
    """
    Registra un error controlado (nivel ERROR). Si se recibe la
    excepción, se agrega su tipo y, si fue encadenada con
    'raise ... from ...', también la causa original.
    """
    if error is not None:                                      # Se recibió la excepción
        mensaje = f"{mensaje} -> {type(error).__name__}: {error}"  # Tipo y detalle del error
        causa = error.__cause__                                # Excepción original encadenada
        if causa is not None:                                  # Existe una causa original
            mensaje += f" | Causa original: {type(causa).__name__}: {causa}"  # Se agrega la causa original
    _logger.error(mensaje)                                     # Se escribe en el archivo


def registrar_error_critico(mensaje, error):
    """
    Registra un error inesperado (nivel CRITICAL) incluyendo la traza
    completa, para poder diagnosticarlo sin detener la aplicación.
    """
    # Línea CRITICAL con el tipo de error y su traza completa
    _logger.critical(f"{mensaje} -> {type(error).__name__}: {error}", exc_info=error)


def leer_log():
    """
    Retorna el contenido actual del archivo de logs. Si aún no existe
    o no se puede leer, retorna un mensaje en lugar de lanzar un error.
    """
    try:                                                       # La lectura puede fallar
        return ARCHIVO_LOG.read_text(encoding="utf-8")         # Lectura completa del archivo
    except FileNotFoundError:
        return "El archivo de logs todavía no tiene registros."  # Aún no se ha creado
    except OSError as error:
        return f"No fue posible leer el archivo de logs: {error}"  # Otro problema de lectura
