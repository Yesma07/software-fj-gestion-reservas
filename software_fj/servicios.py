# ==========================================================
# Nombre del estudiante: Yesid David Marín González
# Grupo: 213023_189
# Programa: Ingeniería de Sistemas
# Curso: Programación (213023) - Fase 4
# Código Fuente: Autoría propia
#
# Módulo: servicios.py
# Descripción:
# Define la clase abstracta Servicio y los tres servicios que ofrece
# Software FJ: reserva de salas, alquiler de equipos y asesorías
# especializadas. Los valores se manejan en pesos colombianos (COP).
#
# Conceptos aplicados:
# - Herencia: Servicio hereda de EntidadBase y los tres servicios
#   heredan de Servicio.
# - Polimorfismo: cada servicio sobrescribe calcular_costo_base(),
#   describir() y validar_parametros() con sus propias reglas.
# - Sobrecarga: calcular_costo() admite tres formas de invocación
#   mediante parámetros opcionales (base, con impuesto, con impuesto y
#   descuento).
# - Encadenamiento de excepciones: los errores técnicos de conversión
#   (ValueError, TypeError) se transforman en errores del negocio con
#   'raise ... from error', conservando la causa original.
# ==========================================================


import math                            # Verificación de números finitos
from abc import abstractmethod         # Métodos que cada servicio debe implementar

# Entidad base del sistema y validación de datos obligatorios
from entidades import EntidadBase, texto_obligatorio
# Excepciones personalizadas que usa este módulo
from excepciones import (
    CalculoInconsistenteError,         # Costos o porcentajes imposibles
    ParametroFaltanteError,            # Datos ausentes
    ReservaInvalidaError,              # Duración de reserva incorrecta
    ServicioInvalidoError,             # Datos del servicio incorrectos
    ServicioNoDisponibleError,         # Servicio desactivado
)

# Tarifa del IVA en Colombia, usada por defecto al calcular costos con impuesto
IVA = 0.19


def formato_moneda(valor):
    """Formato de pesos colombianos con separador de miles: $1.234.567"""
    return "$" + f"{valor:,.0f}".replace(",", ".")         # Comas -> puntos de miles


def convertir_numero(valor, campo, excepcion):
    """
    Convierte un valor a número decimal. Si falta, lanza
    ParametroFaltanteError; si no es numérico, lanza la excepción del
    negocio indicada, ENCADENADA al error original de Python.
    """
    if valor is None or str(valor).strip() == "":          # Dato ausente
        raise ParametroFaltanteError(f"El campo '{campo}' es obligatorio.")  # Falta el dato
    try:                                                                # La conversión puede fallar
        numero = float(valor)                              # Intento de conversión
    except (TypeError, ValueError) as error:               # No es un número
        # Encadenamiento: el error del negocio guarda el ValueError original
        raise excepcion(f"El campo '{campo}' debe ser numérico (recibido: '{valor}').") from error
    if not math.isfinite(numero):                          # Rechaza 'inf' y 'nan'
        raise excepcion(f"El campo '{campo}' debe ser un número finito.")  # Número imposible
    return numero                                          # Número válido


def convertir_entero(valor, campo, excepcion):
    """Convierte a número entero; rechaza valores con decimales."""
    numero = convertir_numero(valor, campo, excepcion)     # Primero, número válido
    if not numero.is_integer():                            # Debe ser entero
        raise excepcion(f"El campo '{campo}' debe ser un número entero.")  # Tiene decimales
    return int(numero)                                     # Entero válido


# ----------------------------------------------------------
# 1. Clase abstracta Servicio
# Contiene los datos comunes a todo servicio (nombre, tarifa base y
# disponibilidad) y el cálculo de costos con sus variantes. Las reglas
# específicas de cada servicio las definen sus clases hijas.
# ----------------------------------------------------------
class Servicio(EntidadBase):           # Un servicio es una entidad del sistema

    PREFIJO = "SRV"            # IDs de la forma SRV-001
    TIPO = "Servicio"          # Nombre del tipo, mostrado en la interfaz
    UNIDAD = "unidades"        # Unidad de la duración (horas, días...)
    DURACION_MAXIMA = 1        # Duración máxima permitida por reserva

    def __init__(self, nombre, tarifa_base, disponible=True):
        """Valida y guarda los datos comunes a todos los servicios."""
        self._nombre = texto_obligatorio(nombre, "nombre del servicio")      # Obligatorio
        tarifa = convertir_numero(tarifa_base, "tarifa", ServicioInvalidoError)  # Debe ser número
        if tarifa <= 0:                                                      # Debe ser positiva
            # Tarifa cero o negativa
            raise ServicioInvalidoError("La tarifa del servicio debe ser mayor que cero.")
        self._tarifa_base = tarifa                                           # Tarifa aceptada
        self._disponible = bool(disponible)                                  # Estado inicial
        super().__init__()                                                   # Se asigna el ID

    # --- Propiedades -----------------------------------------------------

    @property
    def nombre(self):
        """Nombre del servicio (solo lectura)."""
        return self._nombre                                          # Nombre guardado

    @property
    def tarifa_base(self):
        """Tarifa base por unidad de duración (solo lectura)."""
        return self._tarifa_base                                     # Tarifa guardada

    @property
    def disponible(self):
        """True si el servicio se puede reservar."""
        return self._disponible                                      # Estado actual

    def cambiar_disponibilidad(self, disponible):
        """Marca el servicio como disponible o no disponible."""
        self._disponible = bool(disponible)                          # Nuevo estado

    def verificar_disponibilidad(self):
        """Lanza ServicioNoDisponibleError si el servicio no se puede reservar."""
        if not self._disponible:                                     # Servicio desactivado
            raise ServicioNoDisponibleError(                         # No se puede reservar
                f"El servicio {self.id} ({self._nombre}) no está disponible."
            )

    # --- Validación de la duración ---------------------------------------

    def validar_parametros(self, duracion):
        """
        Valida la duración solicitada para una reserva y la retorna como
        número. Las clases hijas lo sobrescriben para agregar sus reglas,
        llamando primero a esta versión común.
        """
        duracion = convertir_numero(duracion, "duración", ReservaInvalidaError)  # Debe ser número
        if duracion <= 0:                                            # Debe ser positiva
            raise ReservaInvalidaError("La duración debe ser mayor que cero.")  # Duración cero o negativa
        if duracion > self.DURACION_MAXIMA:                          # Límite del servicio
            raise ReservaInvalidaError(                              # Duración excesiva
                f"{self.TIPO}: la duración máxima es {self.DURACION_MAXIMA} "
                f"{self.UNIDAD} (solicitado: {duracion:g})."
            )
        return duracion                                              # Duración válida

    # --- Métodos abstractos (polimorfismo) -------------------------------

    @abstractmethod
    def calcular_costo_base(self, duracion):
        """Costo del servicio sin impuestos ni descuentos."""

    @abstractmethod
    def _detalle(self):
        """Características propias del servicio (capacidad, equipo, área...)."""

    def obtener_detalle(self):
        """Acceso público al detalle propio del servicio (usado por la interfaz)."""
        return self._detalle()                                       # Detalle según el tipo

    def describir(self):
        """Descripción común; el detalle varía según el tipo de servicio."""
        estado = "Disponible" if self._disponible else "No disponible"  # Texto del estado
        return (f"{self.TIPO} {self.id}: {self._nombre} | {self._detalle()} | "  # Datos y detalle
                f"Tarifa {formato_moneda(self._tarifa_base)} | {estado}")         # Tarifa y estado

    def validar(self):
        """Verifica que los datos del servicio sigan siendo consistentes."""
        if self._tarifa_base <= 0:                                   # Tarifa imposible
            # Error de tarifa
            raise CalculoInconsistenteError(f"El servicio {self.id} tiene una tarifa inválida.")
        return True                                                  # Servicio consistente

    # --- Método sobrecargado ---------------------------------------------

    def calcular_costo(self, duracion, impuesto=None, descuento=None):
        """
        Sobrecarga simulada con parámetros opcionales:

        - calcular_costo(duracion)
              -> Costo base.
        - calcular_costo(duracion, impuesto=0.19)
              -> Costo base + impuesto.
        - calcular_costo(duracion, impuesto=0.19, descuento=0.10)
              -> Se aplica el descuento y luego el impuesto.

        Los porcentajes se expresan como fracción (0.19 = 19 %).
        """
        duracion = self.validar_parametros(duracion)                 # Validación polimórfica
        total = self.calcular_costo_base(duracion)                   # Cálculo polimórfico

        if descuento is not None:                                    # Variante con descuento
            # Descuento como número
            descuento = convertir_numero(descuento, "descuento", CalculoInconsistenteError)
            if not 0 <= descuento < 1:                               # Entre 0 % y 99,99 %
                raise CalculoInconsistenteError(                     # Descuento imposible
                    f"Descuento inconsistente: {descuento:.0%}. Debe estar entre 0 % y 99 %."
                )
            total *= (1 - descuento)                                 # Se aplica el descuento

        if impuesto is not None:                                     # Variante con impuesto
            # Impuesto como número
            impuesto = convertir_numero(impuesto, "impuesto", CalculoInconsistenteError)
            if not 0 <= impuesto <= 1:                               # Entre 0 % y 100 %
                raise CalculoInconsistenteError(                     # Impuesto imposible
                    f"Impuesto inconsistente: {impuesto:.0%}. Debe estar entre 0 % y 100 %."
                )
            total *= (1 + impuesto)                                  # Se aplica el impuesto

        if not math.isfinite(total) or total <= 0:                   # Resultado imposible
            # Costo imposible
            raise CalculoInconsistenteError(f"El costo calculado ({total}) es inconsistente.")
        return round(total, 2)                                       # Costo final


# ----------------------------------------------------------
# 2. Servicio: Reserva de salas
# Se cobra por hora. Las salas tienen una capacidad máxima de personas.
# ----------------------------------------------------------
class ReservaSala(Servicio):           # Hereda de Servicio

    TIPO = "Reserva de sala"       # Nombre del tipo
    UNIDAD = "horas"               # Se reserva por horas
    DURACION_MAXIMA = 12           # Una sala se reserva máximo 12 horas

    def __init__(self, nombre, tarifa_base, capacidad, disponible=True):
        """Valida la capacidad de la sala y luego los datos comunes."""
        capacidad = convertir_entero(capacidad, "capacidad", ServicioInvalidoError)  # Entero
        if not 1 <= capacidad <= 200:                                # Rango permitido
            # Capacidad fuera de rango
            raise ServicioInvalidoError("La capacidad de la sala debe estar entre 1 y 200 personas.")
        self._capacidad = capacidad                                  # Capacidad aceptada
        super().__init__(nombre, tarifa_base, disponible)            # Datos comunes

    def validar_parametros(self, duracion):
        """Sobrescritura: además de la regla común, exige horas completas o medias."""
        duracion = super().validar_parametros(duracion)              # Regla común
        if (duracion * 2) % 1 != 0:                                  # Bloques de 30 minutos
            # No es múltiplo de media hora
            raise ReservaInvalidaError("Las salas se reservan en bloques de media hora.")
        return duracion                                              # Duración válida

    def calcular_costo_base(self, duracion):
        """Sobrescritura: tarifa por hora x horas reservadas."""
        return self._tarifa_base * duracion                          # Costo de la sala

    def _detalle(self):
        """Sobrescritura: detalle propio de la sala."""
        return f"Capacidad {self._capacidad} personas"               # Capacidad de la sala


# ----------------------------------------------------------
# 3. Servicio: Alquiler de equipos
# Se cobra por día y por cada unidad de equipo alquilada.
# ----------------------------------------------------------
class AlquilerEquipo(Servicio):        # Hereda de Servicio

    TIPO = "Alquiler de equipo"    # Nombre del tipo
    UNIDAD = "días"                # Se alquila por días
    DURACION_MAXIMA = 30           # Un alquiler dura máximo 30 días

    def __init__(self, nombre, tarifa_base, tipo_equipo, cantidad, disponible=True):
        """Valida el tipo y la cantidad de equipos y luego los datos comunes."""
        self._tipo_equipo = texto_obligatorio(tipo_equipo, "tipo de equipo")   # Obligatorio
        cantidad = convertir_entero(cantidad, "cantidad", ServicioInvalidoError)  # Entero
        if not 1 <= cantidad <= 50:                                  # Rango permitido
            # Cantidad fuera de rango
            raise ServicioInvalidoError("La cantidad de equipos debe estar entre 1 y 50.")
        self._cantidad = cantidad                                    # Cantidad aceptada
        super().__init__(nombre, tarifa_base, disponible)            # Datos comunes

    def validar_parametros(self, duracion):
        """Sobrescritura: los equipos se alquilan por días completos."""
        duracion = super().validar_parametros(duracion)              # Regla común
        if not float(duracion).is_integer():                         # Días enteros
            raise ReservaInvalidaError("Los equipos se alquilan por días completos.")  # Días con decimales
        return duracion                                              # Duración válida

    def calcular_costo_base(self, duracion):
        """Sobrescritura: tarifa diaria x cantidad de equipos x días."""
        return self._tarifa_base * self._cantidad * duracion         # Costo del alquiler

    def _detalle(self):
        """Sobrescritura: detalle propio del alquiler."""
        return f"{self._cantidad} x {self._tipo_equipo}"             # Cantidad y tipo de equipo


# ----------------------------------------------------------
# 4. Servicio: Asesorías especializadas
# Se cobra por hora y la tarifa aumenta según el nivel del asesor.
# ----------------------------------------------------------
class AsesoriaEspecializada(Servicio):  # Hereda de Servicio

    TIPO = "Asesoría especializada"  # Nombre del tipo
    UNIDAD = "horas"                 # Se contrata por horas
    DURACION_MAXIMA = 8              # Una asesoría dura máximo 8 horas
    # Multiplicador de la tarifa según el nivel del asesor
    NIVELES = {"Junior": 1.0, "Senior": 1.5, "Experto": 2.0}

    def __init__(self, nombre, tarifa_base, area, nivel, disponible=True):
        """Valida el área y el nivel del asesor y luego los datos comunes."""
        self._area = texto_obligatorio(area, "área")                 # Obligatorio
        nivel = texto_obligatorio(nivel, "nivel").capitalize()       # Ej: "senior" -> "Senior"
        if nivel not in self.NIVELES:                                # Nivel reconocido
            raise ServicioInvalidoError(                             # Nivel desconocido
                f"Nivel '{nivel}' inválido. Opciones: {', '.join(self.NIVELES)}."
            )
        self._nivel = nivel                                          # Nivel aceptado
        super().__init__(nombre, tarifa_base, disponible)            # Datos comunes

    def validar_parametros(self, duracion):
        """Sobrescritura: una asesoría dura al menos 1 hora."""
        duracion = super().validar_parametros(duracion)              # Regla común
        if duracion < 1:                                             # Mínimo de una hora
            raise ReservaInvalidaError("Una asesoría debe durar al menos 1 hora.")  # Menos de una hora
        return duracion                                              # Duración válida

    def calcular_costo_base(self, duracion):
        """Sobrescritura: tarifa por hora x horas x multiplicador del nivel."""
        return self._tarifa_base * duracion * self.NIVELES[self._nivel]  # Costo de la asesoría

    def _detalle(self):
        """Sobrescritura: detalle propio de la asesoría."""
        return f"Área: {self._area} (nivel {self._nivel})"           # Área y nivel del asesor
