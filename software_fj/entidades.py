# ==========================================================
# Nombre del estudiante: Yesid David Marín González
# Grupo: 213023_189
# Programa: Ingeniería de Sistemas
# Curso: Programación (213023) - Fase 4
# Código Fuente: Autoría propia
#
# Módulo: entidades.py
# Descripción:
# Contiene la clase abstracta EntidadBase, que representa cualquier
# entidad general del sistema (clientes, servicios y reservas), y la
# clase Cliente con sus validaciones y datos personales encapsulados.
#
# Conceptos aplicados:
# - Abstracción: EntidadBase no puede instanciarse; define los métodos
#   abstractos describir() y validar() que toda entidad debe implementar.
# - Encapsulación: los datos del cliente son privados (prefijo _) y solo
#   se modifican mediante propiedades que validan cada valor.
# - Excepciones personalizadas: los datos faltantes lanzan
#   ParametroFaltanteError y los datos inválidos ClienteInvalidoError.
# ==========================================================


import re                              # Expresiones regulares para validar formatos
from abc import ABC, abstractmethod    # Herramientas para definir clases abstractas
from datetime import datetime          # Fecha y hora de creación de cada entidad

# Excepciones que pueden lanzar las validaciones de este módulo
from excepciones import ClienteInvalidoError, ParametroFaltanteError


def texto_obligatorio(valor, campo):
    """
    Valida que un dato obligatorio exista y no esté vacío. Retorna el
    texto sin espacios al inicio ni al final. Es usada por todas las
    entidades del sistema.
    """
    if valor is None or str(valor).strip() == "":      # Dato ausente o vacío
        raise ParametroFaltanteError(f"El campo '{campo}' es obligatorio.")  # Falta el dato
    return str(valor).strip()                          # Texto limpio


# ----------------------------------------------------------
# 1. Clase abstracta EntidadBase
# Representa las características comunes a todas las entidades del
# sistema: un identificador único y la fecha en que fue creada.
# ----------------------------------------------------------
class EntidadBase(ABC):                # Hereda de ABC: no se puede instanciar directamente

    # Prefijo del identificador; cada subclase define el suyo (CLI, SRV, RES)
    PREFIJO = "ENT"
    # Contador de identificadores por prefijo, compartido por todas las entidades
    _contadores = {}

    def __init__(self):
        # El identificador se asigna al final de la construcción de cada
        # subclase, cuando sus datos ya fueron validados; así un objeto
        # rechazado no consume números de identificación.
        self._id = EntidadBase._generar_id(self.PREFIJO)   # Ej: CLI-001
        self._fecha_creacion = datetime.now()               # Momento de creación

    @staticmethod
    def _generar_id(prefijo):
        """Genera un identificador consecutivo para el prefijo dado."""
        siguiente = EntidadBase._contadores.get(prefijo, 0) + 1  # Siguiente número
        EntidadBase._contadores[prefijo] = siguiente             # Se actualiza el contador
        return f"{prefijo}-{siguiente:03d}"                      # Formato: PRE-001

    @staticmethod
    def reiniciar_contadores():
        """Reinicia la numeración de identificadores (se usa al reiniciar el sistema)."""
        EntidadBase._contadores.clear()                          # Todos los contadores a cero

    @property
    def id(self):
        """Identificador único de la entidad (solo lectura)."""
        return self._id                                          # ID asignado

    @property
    def fecha_creacion(self):
        """Fecha y hora de creación (solo lectura)."""
        return self._fecha_creacion                              # Momento de creación

    @abstractmethod
    def describir(self):
        """Retorna una descripción en texto de la entidad."""

    @abstractmethod
    def validar(self):
        """
        Verifica que el estado completo de la entidad sea consistente.
        Retorna True o lanza la excepción correspondiente.
        """


# ----------------------------------------------------------
# 2. Clase Cliente
# Representa a un cliente de Software FJ. Sus datos personales son
# privados y cada uno se valida al asignarse mediante su propiedad.
# ----------------------------------------------------------
class Cliente(EntidadBase):            # Un cliente es una entidad del sistema

    PREFIJO = "CLI"                    # IDs de la forma CLI-001

    # Patrones de validación de cada dato
    PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]{3,60}$")   # Letras y espacios
    PATRON_DOCUMENTO = re.compile(r"^\d{6,12}$")                      # 6 a 12 dígitos
    PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")       # usuario@dominio.ext
    PATRON_TELEFONO = re.compile(r"^\d{7,10}$")                       # 7 a 10 dígitos

    def __init__(self, nombre, documento, correo, telefono):
        # Cada asignación pasa por su propiedad, que valida el dato
        self.nombre = nombre                          # Valida nombre
        self._documento = self._validar_documento(documento)  # Documento: no modificable
        self.correo = correo                          # Valida correo
        self.telefono = telefono                      # Valida teléfono
        super().__init__()                            # Datos válidos: se asigna el ID

    # --- Validaciones internas -------------------------------------------

    def _validar_documento(self, documento):
        """El documento es obligatorio y debe tener solo dígitos (6 a 12)."""
        documento = texto_obligatorio(documento, "documento")       # Obligatorio
        if not self.PATRON_DOCUMENTO.match(documento):             # Formato numérico
            raise ClienteInvalidoError(                            # Documento inválido
                f"Documento '{documento}' inválido: debe tener entre 6 y 12 dígitos."
            )
        return documento                                           # Documento válido

    # --- Propiedades (encapsulación) -------------------------------------

    @property
    def nombre(self):
        """Nombre del cliente."""
        return self._nombre                                        # Valor guardado

    @nombre.setter
    def nombre(self, valor):
        """Nombre obligatorio, solo letras y espacios, de 3 a 60 caracteres."""
        valor = texto_obligatorio(valor, "nombre")                 # Obligatorio
        if not self.PATRON_NOMBRE.match(valor):                    # Solo letras
            raise ClienteInvalidoError(                            # Nombre inválido
                f"Nombre '{valor}' inválido: use solo letras (3 a 60 caracteres)."
            )
        self._nombre = valor                                       # Valor aceptado

    @property
    def documento(self):
        """Documento de identidad (solo lectura: no cambia una vez creado)."""
        return self._documento                                     # Valor guardado

    @property
    def correo(self):
        """Correo electrónico del cliente."""
        return self._correo                                        # Valor guardado

    @correo.setter
    def correo(self, valor):
        """Correo obligatorio con formato usuario@dominio.ext."""
        valor = texto_obligatorio(valor, "correo")                 # Obligatorio
        if not self.PATRON_CORREO.match(valor):                    # Formato de correo
            raise ClienteInvalidoError(f"Correo '{valor}' inválido.")  # Correo inválido
        self._correo = valor.lower()                               # Se guarda en minúsculas

    @property
    def telefono(self):
        """Teléfono del cliente."""
        return self._telefono                                      # Valor guardado

    @telefono.setter
    def telefono(self, valor):
        """Teléfono obligatorio, solo dígitos (7 a 10)."""
        valor = texto_obligatorio(valor, "teléfono")               # Obligatorio
        if not self.PATRON_TELEFONO.match(valor):                  # Formato numérico
            raise ClienteInvalidoError(                            # Teléfono inválido
                f"Teléfono '{valor}' inválido: debe tener entre 7 y 10 dígitos."
            )
        self._telefono = valor                                     # Valor aceptado

    # --- Métodos abstractos implementados --------------------------------

    def describir(self):
        """Descripción del cliente para mostrar en pantalla."""
        return (f"Cliente {self.id}: {self._nombre} | Doc. {self._documento} | "  # ID, nombre, documento
                f"{self._correo} | Tel. {self._telefono}")                       # Correo y teléfono

    def validar(self):
        """
        Revalida todos los datos del cliente. Se usa antes de confirmar
        una reserva para garantizar que el cliente sigue siendo válido.
        """
        self.nombre = self._nombre              # Reaplica la validación del nombre
        self._validar_documento(self._documento)  # Revalida el documento
        self.correo = self._correo              # Reaplica la validación del correo
        self.telefono = self._telefono          # Reaplica la validación del teléfono
        return True                             # Todos los datos son válidos
