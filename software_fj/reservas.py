# ==========================================================
# Nombre del estudiante: Yesid David Marín González
# Grupo: 213023_189
# Programa: Ingeniería de Sistemas
# Curso: Programación (213023) - Fase 4
# Código Fuente: Autoría propia
#
# Módulo: reservas.py
# Descripción:
# Contiene la clase Reserva, que integra un cliente, un servicio, una
# duración y un estado, y la clase GestorReservas, que administra las
# listas internas de clientes, servicios y reservas (sin base de datos).
#
# Ciclo de vida de una reserva:
#   Pendiente --confirmar()--> Confirmada --procesar()--> Procesada
#   Pendiente / Confirmada --cancelar()--> Cancelada
#
# Manejo de excepciones aplicado:
# - try/except/else: registrar clientes, servicios y reservas; el bloque
#   else agrega el objeto a la lista solo si no hubo errores.
# - try/except/else/finally: Reserva.procesar(); el bloque finally
#   registra en el log el cierre del intento, haya funcionado o no.
# - Encadenamiento: errores inesperados (TypeError, ZeroDivisionError...)
#   se transforman en errores del negocio con 'raise ... from error'.
# ==========================================================


# Clases de entidades y validación de datos obligatorios
from entidades import Cliente, EntidadBase, texto_obligatorio
# Excepciones personalizadas que usa este módulo
from excepciones import (
    CalculoInconsistenteError,      # Errores de cálculo del costo
    OperacionNoPermitidaError,      # Acciones que no corresponden al estado
    ParametroFaltanteError,         # Datos o parámetros ausentes
    ReservaInvalidaError,           # Intentos de reserva incorrectos
    ServicioInvalidoError,          # Servicios inexistentes o mal definidos
    SoftwareFJError,                # Base de todos los errores del negocio
)
# Funciones para escribir eventos y errores en el archivo de logs
from registro_logs import registrar_error, registrar_evento
# Servicios disponibles y formato de moneda
from servicios import (
    AlquilerEquipo,                 # Servicio de alquiler de equipos
    AsesoriaEspecializada,          # Servicio de asesorías
    ReservaSala,                    # Servicio de reserva de salas
    Servicio,                       # Clase abstracta base de los servicios
    formato_moneda,                 # Formato $1.234.567
)


# ----------------------------------------------------------
# 1. Clase Reserva
# Integra cliente, servicio, duración y estado. Sus operaciones
# (confirmar, cancelar, procesar) verifican el estado actual y lanzan
# OperacionNoPermitidaError cuando la acción no corresponde.
# ----------------------------------------------------------
class Reserva(EntidadBase):                                         # Una reserva es una entidad del sistema

    PREFIJO = "RES"                                                 # IDs de la forma RES-001

    # Estados posibles de una reserva
    PENDIENTE = "Pendiente"                                         # Recién creada
    CONFIRMADA = "Confirmada"                                       # Aprobada, lista para procesar
    CANCELADA = "Cancelada"                                         # Anulada (estado final)
    PROCESADA = "Procesada"                                         # Cobrada (estado final)
    ESTADOS = (PENDIENTE, CONFIRMADA, CANCELADA, PROCESADA)         # Todos los estados válidos

    def __init__(self, cliente, servicio, duracion):
        """Crea una reserva Pendiente validando cliente, servicio y duración."""
        if not isinstance(cliente, Cliente):                        # Debe ser un objeto Cliente
            raise ReservaInvalidaError("La reserva requiere un cliente registrado.")  # No es un Cliente
        if not isinstance(servicio, Servicio):                      # Debe ser un objeto Servicio
            raise ReservaInvalidaError("La reserva requiere un servicio registrado.")  # No es un Servicio
        servicio.verificar_disponibilidad()                         # Error si no está disponible
        self._duracion = servicio.validar_parametros(duracion)      # Duración válida (polimórfico)
        self._cliente = cliente                                     # Cliente de la reserva
        self._servicio = servicio                                   # Servicio reservado
        self._estado = Reserva.PENDIENTE                            # Estado inicial
        self._costo_total = None                                    # Se define al procesar
        super().__init__()                                          # Datos válidos: se asigna el ID

    # --- Propiedades (solo lectura) --------------------------------------

    @property
    def cliente(self):
        """Cliente que hizo la reserva."""
        return self._cliente                                        # Objeto Cliente

    @property
    def servicio(self):
        """Servicio reservado."""
        return self._servicio                                       # Objeto Servicio

    @property
    def duracion(self):
        """Duración reservada, en la unidad del servicio."""
        return self._duracion                                       # Horas o días

    @property
    def estado(self):
        """Estado actual de la reserva."""
        return self._estado                                         # Uno de ESTADOS

    @property
    def costo_total(self):
        """Costo final; None mientras la reserva no se haya procesado."""
        return self._costo_total                                    # Número o None

    # --- Operaciones de la reserva ---------------------------------------

    def confirmar(self):
        """Pasa la reserva de Pendiente a Confirmada."""
        if self._estado != Reserva.PENDIENTE:                       # Solo desde Pendiente
            raise OperacionNoPermitidaError(                        # Operación no permitida
                f"No se puede confirmar la reserva {self.id}: su estado es '{self._estado}'."
            )
        self.validar()                                              # Cliente y servicio válidos
        self._servicio.verificar_disponibilidad()                   # El servicio sigue disponible
        self._estado = Reserva.CONFIRMADA                           # Cambio de estado
        registrar_evento(f"Reserva {self.id} confirmada.")          # Evento en el log

    def cancelar(self):
        """Cancela la reserva si todavía no ha sido procesada ni cancelada."""
        if self._estado in (Reserva.PROCESADA, Reserva.CANCELADA):  # Estados finales
            raise OperacionNoPermitidaError(                        # Operación no permitida
                f"No se puede cancelar la reserva {self.id}: su estado es '{self._estado}'."
            )
        self._estado = Reserva.CANCELADA                            # Cambio de estado
        registrar_evento(f"Reserva {self.id} cancelada.")           # Evento en el log

    def procesar(self, impuesto=None, descuento=None):
        """
        Calcula el costo final de una reserva confirmada y la marca como
        Procesada. Usa la estructura completa try/except/else/finally:
        - try: verifica el estado y calcula el costo.
        - except: registra el error y lo propaga (o lo encadena si es inesperado).
        - else: solo si no hubo error, guarda el costo y cambia el estado.
        - finally: siempre registra que el intento terminó.
        """
        registrar_evento(f"Inicia el procesamiento de la reserva {self.id}.")  # Inicio del intento
        try:                                                            # El estado o el cálculo pueden fallar
            if self._estado != Reserva.CONFIRMADA:                  # Solo reservas confirmadas
                raise OperacionNoPermitidaError(                    # Operación no permitida
                    f"Solo se procesan reservas confirmadas; {self.id} está '{self._estado}'."
                )
            # Cálculo del costo con el método sobrecargado del servicio
            costo = self._servicio.calcular_costo(self._duracion, impuesto, descuento)
        except SoftwareFJError as error:                            # Error del negocio
            registrar_error(f"Falló el procesamiento de la reserva {self.id}", error)  # Al log
            raise                                                   # Se propaga a quien llamó
        except Exception as error:                                  # Error no previsto de Python
            registrar_error(f"Error inesperado al procesar la reserva {self.id}", error)  # Al log
            # Encadenamiento: se convierte en error del negocio conservando la causa
            raise CalculoInconsistenteError(
                f"Error inesperado al calcular el costo de la reserva {self.id}."
            ) from error
        else:                                                       # Solo si no hubo errores
            self._costo_total = costo                               # Costo definitivo
            self._estado = Reserva.PROCESADA                        # Cambio de estado
            registrar_evento(                                       # Evento de éxito en el log
                f"Reserva {self.id} procesada. Costo total: {formato_moneda(costo)}."
            )
            return costo                                            # Se retorna el costo final
        finally:                                                    # Se ejecuta siempre
            registrar_evento(                                       # Cierre del intento en el log
                f"Finaliza el intento de procesamiento de {self.id} (estado: {self._estado})."
            )

    # --- Métodos abstractos implementados --------------------------------

    def describir(self):
        """Descripción de la reserva para mostrar en pantalla."""
        costo = (formato_moneda(self._costo_total)                  # Costo final con formato...
                 if self._costo_total is not None else "Sin procesar")  # ...o aviso si no hay
        return (f"Reserva {self.id}: {self._cliente.nombre} -> {self._servicio.nombre} | "  # Datos
                f"{self._duracion:g} {self._servicio.UNIDAD} | {self._estado} | {costo}")    # principales

    def validar(self):
        """Verifica que cliente, servicio y estado sean consistentes."""
        self._cliente.validar()                                     # Cliente válido
        self._servicio.validar()                                    # Servicio válido
        if self._estado not in Reserva.ESTADOS:                     # Estado reconocido
            raise ReservaInvalidaError(f"Estado desconocido: {self._estado}.")  # Estado imposible
        return True                                                 # Reserva consistente


# ----------------------------------------------------------
# 2. Clase GestorReservas
# Administra las listas internas de clientes, servicios y reservas.
# Cada operación registra en el log su resultado: los éxitos como
# eventos y los fallos como errores, sin detener el sistema.
# ----------------------------------------------------------
class GestorReservas:

    # Relación entre el tipo de servicio y su clase. Para agregar un
    # nuevo servicio basta con crear la subclase y registrarla aquí.
    TIPOS_SERVICIO = {
        ReservaSala.TIPO: ReservaSala,                              # "Reserva de sala"
        AlquilerEquipo.TIPO: AlquilerEquipo,                        # "Alquiler de equipo"
        AsesoriaEspecializada.TIPO: AsesoriaEspecializada,          # "Asesoría especializada"
    }

    def __init__(self):
        """Crea el gestor con las tres listas internas vacías."""
        self._clientes = []                                         # Lista interna de clientes
        self._servicios = []                                        # Lista interna de servicios
        self._reservas = []                                         # Lista interna de reservas

    # --- Consultas -------------------------------------------------------

    def obtener_clientes(self):
        """Copia de la lista de clientes (protege la lista interna)."""
        return list(self._clientes)                                 # Copia, no la lista original

    def obtener_servicios(self):
        """Copia de la lista de servicios."""
        return list(self._servicios)                                # Copia, no la lista original

    def obtener_reservas(self):
        """Copia de la lista de reservas."""
        return list(self._reservas)                                 # Copia, no la lista original

    def buscar_cliente(self, documento):
        """Retorna el cliente con ese documento o None."""
        # Primera coincidencia del documento (sin espacios), o None si no existe
        return next((c for c in self._clientes if c.documento == str(documento).strip()), None)

    def buscar_servicio(self, id_servicio):
        """Retorna el servicio con ese ID o None."""
        return next((s for s in self._servicios if s.id == id_servicio), None)  # Primera coincidencia

    def buscar_reserva(self, id_reserva):
        """Retorna la reserva con ese ID o lanza ReservaInvalidaError si no existe."""
        reserva = next((r for r in self._reservas if r.id == id_reserva), None)  # Búsqueda por ID
        if reserva is None:                                         # No se encontró
            raise ReservaInvalidaError(f"No existe la reserva '{id_reserva}'.")  # Reserva inexistente
        return reserva                                              # Reserva encontrada

    # --- Registro de clientes (try/except/else) --------------------------

    def registrar_cliente(self, nombre, documento, correo, telefono):
        """Crea y registra un cliente; rechaza documentos duplicados."""
        try:                                                            # La validación puede fallar
            if self.buscar_cliente(documento or "") is not None:     # Documento ya registrado
                raise OperacionNoPermitidaError(                    # No se permiten duplicados
                    f"Ya existe un cliente con el documento {documento}."
                )
            cliente = Cliente(nombre, documento, correo, telefono)  # Valida todos los datos
        except SoftwareFJError as error:                            # Cualquier error del negocio
            registrar_error("Registro de cliente rechazado", error) # Se registra en el log
            raise                                                   # La interfaz informa el error
        else:                                                       # Solo si no hubo errores
            self._clientes.append(cliente)                          # Se agrega a la lista
            registrar_evento(f"Cliente registrado: {cliente.describir()}")  # Evento en el log
            return cliente                                          # Cliente creado

    # --- Registro de servicios (try/except/else + encadenamiento) --------

    def registrar_servicio(self, tipo, **datos):
        """
        Crea un servicio del tipo indicado con los datos recibidos. Si
        falta un parámetro del constructor (TypeError de Python), se
        encadena como ParametroFaltanteError.
        """
        try:                                                            # El tipo o los datos pueden fallar
            clase = self.TIPOS_SERVICIO.get(tipo)                   # Clase según el tipo
            if clase is None:                                       # Tipo desconocido
                raise ServicioInvalidoError(f"Tipo de servicio desconocido: '{tipo}'.")  # Tipo no registrado
            try:                                                        # La creación puede fallar
                servicio = clase(**datos)                           # Crea y valida el servicio
            except TypeError as error:                              # Faltan o sobran argumentos
                # Encadenamiento: error técnico de Python -> error del negocio
                raise ParametroFaltanteError(
                    f"Parámetros incompletos o incorrectos para '{tipo}'."
                ) from error
        except SoftwareFJError as error:                            # Cualquier error del negocio
            registrar_error("Creación de servicio rechazada", error)  # Se registra en el log
            raise                                                   # La interfaz informa el error
        else:                                                       # Solo si no hubo errores
            self._servicios.append(servicio)                        # Se agrega a la lista
            registrar_evento(f"Servicio creado: {servicio.describir()}")  # Evento en el log
            return servicio                                         # Servicio creado

    def cambiar_disponibilidad(self, id_servicio, disponible):
        """Activa o desactiva la disponibilidad de un servicio."""
        servicio = self.buscar_servicio(id_servicio)                # Servicio a modificar
        if servicio is None:                                        # No existe
            error = ServicioInvalidoError(f"No existe el servicio '{id_servicio}'.")  # Se crea el error
            registrar_error("Cambio de disponibilidad rechazado", error)  # Se registra en el log
            raise error                                             # Y se lanza
        servicio.cambiar_disponibilidad(disponible)                 # Nuevo estado del servicio
        estado = "disponible" if disponible else "no disponible"    # Texto para el log
        registrar_evento(f"Servicio {servicio.id} marcado como {estado}.")  # Evento en el log
        return servicio                                             # Servicio actualizado

    # --- Reservas --------------------------------------------------------

    def crear_reserva(self, documento_cliente, id_servicio, duracion):
        """Crea una reserva en estado Pendiente (try/except/else)."""
        try:                                                            # Los datos pueden ser inválidos
            documento_cliente = texto_obligatorio(documento_cliente, "cliente")  # Obligatorio
            id_servicio = texto_obligatorio(id_servicio, "servicio")            # Obligatorio
            cliente = self.buscar_cliente(documento_cliente)        # Cliente registrado
            if cliente is None:                                     # No existe
                raise ReservaInvalidaError(                         # Reserva incorrecta
                    f"No existe un cliente con el documento '{documento_cliente}'."
                )
            servicio = self.buscar_servicio(id_servicio)            # Servicio registrado
            if servicio is None:                                    # No existe
                raise ReservaInvalidaError(f"No existe el servicio '{id_servicio}'.")  # Servicio inexistente
            reserva = Reserva(cliente, servicio, duracion)          # Valida la reserva
        except SoftwareFJError as error:                            # Cualquier error del negocio
            registrar_error("Intento de reserva rechazado", error)  # Se registra en el log
            raise                                                   # La interfaz informa el error
        else:                                                       # Solo si no hubo errores
            self._reservas.append(reserva)                          # Se agrega a la lista
            registrar_evento(f"Reserva creada: {reserva.describir()}")  # Evento en el log
            return reserva                                          # Reserva creada

    def confirmar_reserva(self, id_reserva):
        """Confirma una reserva registrando el error si no es posible."""
        try:                                                            # Búsqueda y confirmación
            reserva = self.buscar_reserva(id_reserva)               # Reserva a confirmar
            reserva.confirmar()                                     # Cambio a Confirmada
        except SoftwareFJError as error:                            # No se pudo confirmar
            registrar_error(f"No se pudo confirmar la reserva {id_reserva}", error)  # Al log
            raise                                                   # La interfaz informa el error
        return reserva                                              # Reserva confirmada

    def cancelar_reserva(self, id_reserva):
        """Cancela una reserva registrando el error si no es posible."""
        try:                                                            # Búsqueda y cancelación
            reserva = self.buscar_reserva(id_reserva)               # Reserva a cancelar
            reserva.cancelar()                                      # Cambio a Cancelada
        except SoftwareFJError as error:                            # No se pudo cancelar
            registrar_error(f"No se pudo cancelar la reserva {id_reserva}", error)  # Al log
            raise                                                   # La interfaz informa el error
        return reserva                                              # Reserva cancelada

    def procesar_reserva(self, id_reserva, impuesto=None, descuento=None):
        """
        Procesa una reserva. Si la reserva existe, el registro de errores
        del cálculo lo hace Reserva.procesar().
        """
        try:                                                            # La búsqueda puede fallar
            reserva = self.buscar_reserva(id_reserva)               # Reserva a procesar
        except SoftwareFJError as error:                            # No existe
            registrar_error(f"No se pudo procesar la reserva {id_reserva}", error)  # Al log
            raise                                                   # La interfaz informa el error
        return reserva.procesar(impuesto, descuento)                # Costo final

    def simular_costos(self, id_reserva):
        """
        Calcula las tres variantes del método sobrecargado calcular_costo()
        para una reserva, sin modificar su estado.
        """
        reserva = self.buscar_reserva(id_reserva)                   # Reserva consultada
        servicio, duracion = reserva.servicio, reserva.duracion     # Datos para el cálculo
        return {
            "Base": servicio.calcular_costo(duracion),              # Forma 1: costo base
            "Con IVA (19 %)": servicio.calcular_costo(duracion, impuesto=0.19),  # Forma 2: con IVA
            "Con IVA y 10 % de descuento": servicio.calcular_costo(  # Forma 3: con IVA y descuento
                duracion, impuesto=0.19, descuento=0.10),
        }
