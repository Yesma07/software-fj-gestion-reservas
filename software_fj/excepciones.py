# ==========================================================
# Nombre del estudiante: Yesid David Marín González
# Grupo: 213023_189
# Programa: Ingeniería de Sistemas
# Curso: Programación (213023) - Fase 4
# Código Fuente: Autoría propia
#
# Módulo: excepciones.py
# Descripción:
# Define la jerarquía de excepciones personalizadas del sistema
# Software FJ. Todas heredan de SoftwareFJError, de modo que el resto
# del programa puede capturar cualquier error del negocio con un solo
# bloque except, o capturar cada tipo de error por separado cuando
# necesita reaccionar de forma específica.
#
# Cada excepción tiene un código (SFJ-xxx) que se escribe en el archivo
# de logs para identificar rápidamente el tipo de error ocurrido.
# ==========================================================


# ----------------------------------------------------------
# 1. Excepción base del sistema
# ----------------------------------------------------------
class SoftwareFJError(Exception):                  # Hereda de la excepción estándar de Python
    """Excepción raíz de la que heredan todos los errores del negocio."""

    CODIGO = "SFJ-000"                             # Código por defecto; cada subclase define el suyo

    def __init__(self, mensaje):
        super().__init__(mensaje)                  # Se inicializa Exception con el mensaje
        self.mensaje = mensaje                     # Mensaje disponible sin el código

    def __str__(self):
        return f"[{self.CODIGO}] {self.mensaje}"   # Texto: código del error + mensaje legible


# ----------------------------------------------------------
# 2. Errores relacionados con clientes
# ----------------------------------------------------------
class ClienteInvalidoError(SoftwareFJError):       # Error del negocio sobre clientes
    """Datos de cliente con formato incorrecto."""
    CODIGO = "SFJ-100"                             # Código del error en el log


class ParametroFaltanteError(SoftwareFJError):     # Error del negocio por datos ausentes
    """Un dato obligatorio no fue suministrado (vacío o None)."""
    CODIGO = "SFJ-110"                             # Código del error en el log


# ----------------------------------------------------------
# 3. Errores relacionados con servicios
# ----------------------------------------------------------
class ServicioInvalidoError(SoftwareFJError):      # Error del negocio sobre servicios
    """Parámetros de creación de un servicio incorrectos o tipo desconocido."""
    CODIGO = "SFJ-200"                             # Código del error en el log


class ServicioNoDisponibleError(SoftwareFJError):  # Error del negocio por disponibilidad
    """Se intenta reservar o confirmar un servicio que no está disponible."""
    CODIGO = "SFJ-210"                             # Código del error en el log


# ----------------------------------------------------------
# 4. Errores relacionados con reservas y operaciones
# ----------------------------------------------------------
class ReservaInvalidaError(SoftwareFJError):       # Error del negocio sobre reservas
    """Intento de reserva incorrecto (duración inválida, datos inexistentes)."""
    CODIGO = "SFJ-300"                             # Código del error en el log


class OperacionNoPermitidaError(SoftwareFJError):  # Error del negocio por reglas de estado
    """Operación que no corresponde (ej. cancelar algo procesado o duplicar un cliente)."""
    CODIGO = "SFJ-310"                             # Código del error en el log


# ----------------------------------------------------------
# 5. Errores de cálculo
# ----------------------------------------------------------
class CalculoInconsistenteError(SoftwareFJError):  # Error del negocio en los cálculos
    """Resultado de costo imposible (negativo, no finito) o porcentajes inválidos."""
    CODIGO = "SFJ-400"                             # Código del error en el log
