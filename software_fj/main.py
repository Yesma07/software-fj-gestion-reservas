# ==========================================================
# Nombre del estudiante: Yesid David Marín González
# Grupo: 213023_189
# Programa: Ingeniería de Sistemas
# Curso: Programación (213023) - Fase 4
# Código Fuente: Autoría propia
#
# Módulo: main.py
# Descripción:
# Punto de entrada del Sistema Integral de Gestión de Clientes,
# Servicios y Reservas de Software FJ. Ofrece una interfaz gráfica en
# Tkinter con cuatro pestañas:
# - Clientes: registro y listado de clientes.
# - Servicios: creación de salas, equipos y asesorías, y su disponibilidad.
# - Reservas: creación, confirmación, cancelación y procesamiento.
# - Simulación y logs: ejecuta automáticamente 13 operaciones (válidas e
#   inválidas) y muestra el contenido del archivo de logs.
#
# Robustez: toda acción de la interfaz se ejecuta dentro de bloques
# try/except, y cualquier error no previsto de Tkinter se captura con
# report_callback_exception. Así la aplicación nunca se cierra por un
# error: lo informa, lo registra en el log y sigue funcionando.
#
# Ejecución:
#   python main.py              -> interfaz gráfica
#   python main.py --consola    -> solo la simulación, en la consola
# ==========================================================


import sys                                    # Argumentos de la línea de comandos
import tkinter as tk                          # Interfaz gráfica
from tkinter import messagebox, ttk           # Ventanas de mensaje y widgets modernos

from entidades import EntidadBase             # Para reiniciar la numeración de IDs
# Excepciones que la interfaz necesita reconocer
from excepciones import CalculoInconsistenteError, SoftwareFJError
# Funciones del archivo de logs
from registro_logs import (
    leer_log,                                 # Lee el contenido del log
    registrar_error,                          # Registra errores controlados
    registrar_error_critico,                  # Registra errores inesperados
    registrar_evento,                         # Registra eventos normales
)
from reservas import GestorReservas, Reserva  # Gestor de listas y estados de reserva
# Servicios y utilidades de cálculo
from servicios import (
    IVA,                                      # Tarifa del IVA (19 %)
    AlquilerEquipo,                           # Servicio de alquiler de equipos
    AsesoriaEspecializada,                    # Servicio de asesorías
    ReservaSala,                              # Servicio de reserva de salas
    convertir_numero,                         # Conversión numérica con encadenamiento
    formato_moneda,                           # Formato $1.234.567
)


# ----------------------------------------------------------
# 1. Simulación automática de operaciones
# Cada operación es una tupla (descripción, resultado esperado, función).
# Las funciones comparten el diccionario "ctx" para reutilizar los
# objetos creados en operaciones anteriores.
# ----------------------------------------------------------
def construir_operaciones(gestor):
    """Define las 13 operaciones de la simulación sobre el gestor recibido."""
    ctx = {}                                   # Objetos creados durante la simulación

    def op_cliente_valido():
        """Operación 1: cliente con todos sus datos correctos."""
        ctx["cliente"] = gestor.registrar_cliente(                        # Se guarda para reutilizarlo
            "Laura Gómez", "1032456789", "laura.gomez@correo.com", "3104567890")
        return ctx["cliente"].describir()                                 # Resultado a mostrar

    def op_cliente_correo_invalido():
        """Operación 2: correo sin '@' (ClienteInvalidoError)."""
        return gestor.registrar_cliente(                                  # Debe fallar
            "Pedro Ramírez", "80123456", "pedro.correo.com", "3157894561").describir()

    def op_cliente_sin_documento():
        """Operación 3: documento vacío (ParametroFaltanteError)."""
        return gestor.registrar_cliente(                                  # Debe fallar
            "Ana Torres", "", "ana.torres@correo.com", "3209876543").describir()

    def op_sala_valida():
        """Operación 4: sala con datos correctos."""
        ctx["sala"] = gestor.registrar_servicio(                          # Se guarda para reutilizarla
            ReservaSala.TIPO, nombre="Sala Innovación", tarifa_base=50000, capacidad=20)
        return ctx["sala"].describir()                                    # Resultado a mostrar

    def op_equipo_cantidad_negativa():
        """Operación 5: cantidad de equipos negativa (ServicioInvalidoError)."""
        return gestor.registrar_servicio(                                 # Debe fallar
            AlquilerEquipo.TIPO, nombre="Portátiles", tarifa_base=60000,
            tipo_equipo="Portátil", cantidad=-3).describir()

    def op_servicio_tarifa_texto():
        """Operación 6: tarifa en texto; ServicioInvalidoError encadenado a ValueError."""
        return gestor.registrar_servicio(                                 # Debe fallar
            ReservaSala.TIPO, nombre="Sala Auditorio", tarifa_base="cien mil",
            capacidad=80).describir()

    def op_asesoria_valida():
        """Operación 7: asesoría con datos correctos."""
        ctx["asesoria"] = gestor.registrar_servicio(                      # Se guarda para reutilizarla
            AsesoriaEspecializada.TIPO, nombre="Arquitectura de software",
            tarifa_base=120000, area="Arquitectura", nivel="Senior")
        return ctx["asesoria"].describir()                                # Resultado a mostrar

    def op_reserva_completa():
        """Operación 8: ciclo completo de una reserva válida."""
        reserva = gestor.crear_reserva("1032456789", ctx["sala"].id, 3)   # Estado Pendiente
        ctx["procesada"] = reserva                                        # Se reutiliza en la op. 11
        costos = gestor.simular_costos(reserva.id)                        # 3 variantes del costo
        gestor.confirmar_reserva(reserva.id)                              # Estado Confirmada
        gestor.procesar_reserva(reserva.id, impuesto=IVA)                 # Estado Procesada
        variantes = "; ".join(f"{k}: {formato_moneda(v)}" for k, v in costos.items())  # Texto
        return f"{reserva.describir()} | Variantes de costo -> {variantes}"  # Resultado a mostrar

    def op_reserva_duracion_invalida():
        """Operación 9: 20 horas en una sala que admite máximo 12 (ReservaInvalidaError)."""
        return gestor.crear_reserva("1032456789", ctx["sala"].id, 20).describir()  # Debe fallar

    def op_reserva_no_disponible():
        """Operación 10: reservar un servicio desactivado (ServicioNoDisponibleError)."""
        gestor.cambiar_disponibilidad(ctx["asesoria"].id, False)          # Se desactiva el servicio
        return gestor.crear_reserva("1032456789", ctx["asesoria"].id, 2).describir()  # Debe fallar

    def op_cancelar_procesada():
        """Operación 11: cancelar una reserva procesada (OperacionNoPermitidaError)."""
        return gestor.cancelar_reserva(ctx["procesada"].id).describir()   # Debe fallar

    def op_reserva_cancelada():
        """Operación 12: reserva válida que luego se cancela."""
        reserva = gestor.crear_reserva("1032456789", ctx["sala"].id, 2)   # Estado Pendiente
        gestor.cancelar_reserva(reserva.id)                               # Estado Cancelada
        return reserva.describir()                                        # Resultado a mostrar

    def op_descuento_inconsistente():
        """Operación 13: descuento del 150 % (CalculoInconsistenteError)."""
        reserva = gestor.crear_reserva("1032456789", ctx["sala"].id, 1.5) # Estado Pendiente
        gestor.confirmar_reserva(reserva.id)                              # Estado Confirmada
        return gestor.procesar_reserva(reserva.id, impuesto=IVA, descuento=1.5)  # Debe fallar

    # Lista de operaciones: (descripción, ¿se espera éxito?, función)
    return [
        ("Registrar cliente válido (Laura Gómez)", True, op_cliente_valido),
        ("Registrar cliente con correo inválido", False, op_cliente_correo_invalido),
        ("Registrar cliente sin documento", False, op_cliente_sin_documento),
        ("Crear servicio válido: Reserva de sala", True, op_sala_valida),
        ("Crear servicio de equipos con cantidad negativa", False, op_equipo_cantidad_negativa),
        ("Crear servicio con tarifa no numérica (encadenamiento)", False, op_servicio_tarifa_texto),
        ("Crear servicio válido: Asesoría especializada", True, op_asesoria_valida),
        ("Reserva válida: crear, confirmar y procesar con IVA", True, op_reserva_completa),
        ("Reservar sala por 20 horas (máximo 12)", False, op_reserva_duracion_invalida),
        ("Reservar un servicio no disponible", False, op_reserva_no_disponible),
        ("Cancelar una reserva ya procesada", False, op_cancelar_procesada),
        ("Reserva válida y luego cancelada", True, op_reserva_cancelada),
        ("Procesar reserva con descuento del 150 %", False, op_descuento_inconsistente),
    ]


def ejecutar_simulacion(gestor):
    """
    Ejecuta todas las operaciones de la simulación. Cada una se protege
    con try/except/else, de modo que un error no detiene a las demás.
    Retorna las líneas de texto con el resultado de cada operación.
    """
    registrar_evento("===== Inicio de la simulación automática =====")  # Inicio en el log
    lineas = []                                  # Resultado en texto
    exitos = errores = coincidencias = 0         # Contadores del resumen
    operaciones = construir_operaciones(gestor)  # Lista de operaciones

    # Se recorre cada operación con su número consecutivo (desde 1)
    for numero, (descripcion, esperado_exito, funcion) in enumerate(operaciones, start=1):
        lineas.append(f"[{numero:02d}] {descripcion}")                   # Título de la operación
        # Resultado esperado
        lineas.append(f"     Esperado: {'éxito' if esperado_exito else 'error controlado'}")
        try:                                                            # La operación puede fallar
            detalle = funcion()                                  # Se ejecuta la operación
        except SoftwareFJError as error:                         # Error del negocio
            errores += 1                                         # Se cuenta el error
            lineas.append(f"     Resultado: ✖ ERROR CONTROLADO -> {error}")  # Mensaje del error
            if error.__cause__ is not None:                      # Excepción encadenada
                causa = error.__cause__                          # Error original de Python
                lineas.append(f"     Causa original: {type(causa).__name__}: {causa}")  # Causa encadenada
            coincidencias += not esperado_exito                  # Correcto si se esperaba error
        except Exception as error:                               # Error no previsto
            errores += 1                                         # Se cuenta el error
            registrar_error_critico(f"Error inesperado en la operación {numero}", error)  # Al log
            # Mensaje del error inesperado
            lineas.append(f"     Resultado: ✖ ERROR INESPERADO -> {type(error).__name__}: {error}")
        else:                                                    # Sin errores
            exitos += 1                                          # Se cuenta el éxito
            lineas.append(f"     Resultado: ✔ ÉXITO -> {detalle}")  # Resultado de la operación
            coincidencias += esperado_exito                      # Correcto si se esperaba éxito
        lineas.append("")                                        # Línea en blanco de separación

    # Resumen final de la simulación
    lineas.append("=" * 70)                                      # Línea divisoria
    # Totales de la simulación
    lineas.append(f"Operaciones ejecutadas: {len(operaciones)} | Éxitos: {exitos} | "
                  f"Errores controlados: {errores}")
    # Operaciones correctas
    lineas.append(f"Resultados iguales a lo esperado: {coincidencias}/{len(operaciones)}")
    lineas.append("El sistema sigue activo: ningún error detuvo la aplicación.")  # Estabilidad del sistema
    registrar_evento(f"===== Fin de la simulación: {exitos} éxitos, {errores} errores "  # Fin en el log
                     f"controlados ({coincidencias}/{len(operaciones)} según lo esperado) =====")
    return lineas                                                # Texto completo del resultado


# ----------------------------------------------------------
# 2. Configuración de los formularios de servicio
# Para cada tipo de servicio: etiqueta de la tarifa y campos propios
# (nombre del parámetro del constructor, etiqueta, opciones o None).
# ----------------------------------------------------------
CAMPOS_SERVICIO = {
    ReservaSala.TIPO: ("Tarifa por hora (COP):", [                   # Salas: tarifa por hora
        ("capacidad", "Capacidad (personas):", None),                # Campo de texto
    ]),
    AlquilerEquipo.TIPO: ("Tarifa por día (COP):", [                 # Equipos: tarifa por día
        ("tipo_equipo", "Tipo de equipo:", None),                    # Campo de texto
        ("cantidad", "Cantidad:", None),                             # Campo de texto
    ]),
    AsesoriaEspecializada.TIPO: ("Tarifa por hora (COP):", [         # Asesorías: tarifa por hora
        ("area", "Área:", None),                                     # Campo de texto
        ("nivel", "Nivel:", list(AsesoriaEspecializada.NIVELES)),    # Lista desplegable
    ]),
}


# ----------------------------------------------------------
# 3. Ventana principal
# ----------------------------------------------------------
class SoftwareFJApp(tk.Tk):                   # La ventana principal es una ventana de Tkinter

    def __init__(self):
        """Construye la ventana, sus cuatro pestañas y el gestor del sistema."""
        super().__init__()                                                   # Inicializa Tkinter
        self.title("Software FJ - Gestión de Clientes, Servicios y Reservas")  # Título
        self.geometry("1180x660")                                            # Tamaño inicial
        self.minsize(1050, 600)                                              # Tamaño mínimo

        # Cualquier excepción no capturada en un evento de Tkinter llega
        # aquí en lugar de interrumpir la aplicación.
        self.report_callback_exception = self._error_no_controlado

        self._gestor = GestorReservas()          # Modelo: listas internas del sistema
        self._entradas_servicio = {}             # Campos propios del tipo de servicio

        cuaderno = ttk.Notebook(self)            # Contenedor de pestañas
        cuaderno.pack(fill="both", expand=True, padx=8, pady=8)  # Ocupa toda la ventana
        self._crear_pestana_clientes(cuaderno)   # Pestaña 1
        self._crear_pestana_servicios(cuaderno)  # Pestaña 2
        self._crear_pestana_reservas(cuaderno)   # Pestaña 3
        self._crear_pestana_simulacion(cuaderno) # Pestaña 4

        registrar_evento("Aplicación Software FJ iniciada.")  # Evento de inicio en el log
        self._refrescar_todo()                   # Carga inicial de tablas y log

    # ======================================================
    # Manejo centralizado de errores de la interfaz
    # ======================================================

    def _ejecutar_seguro(self, funcion):
        """
        Ejecuta una acción de la interfaz. Los errores del negocio ya
        fueron registrados por el modelo y solo se muestran; los errores
        inesperados se registran como críticos. En todos los casos el
        bloque finally actualiza las tablas y la aplicación sigue activa.
        """
        try:                                                            # La acción puede fallar
            return funcion()                                         # Acción solicitada
        except SoftwareFJError as error:                             # Error controlado
            messagebox.showerror("Operación rechazada", str(error))  # Se informa al usuario
        except Exception as error:                                   # Error no previsto
            registrar_error_critico("Error inesperado en la interfaz", error)  # Al log
            messagebox.showerror(                                    # Se informa al usuario
                "Error inesperado",
                f"Ocurrió un error no previsto:\n{error}\n\nEl sistema sigue funcionando.")
        finally:                                                     # Se ejecuta siempre
            self._refrescar_todo()                                   # Se actualiza la interfaz
        return None                                                  # Hubo error: sin resultado

    def _error_no_controlado(self, tipo, valor, traza):
        """Última barrera: registra cualquier error que escape a los bloques try."""
        registrar_error_critico("Error no controlado en un evento de la interfaz", valor)  # Al log
        messagebox.showerror("Error inesperado",                    # Se informa sin cerrar la app
                             f"{tipo.__name__}: {valor}\n\nEl sistema sigue funcionando.")

    # ======================================================
    # Pestaña 1: Clientes
    # ======================================================

    def _crear_pestana_clientes(self, cuaderno):
        """Construye el formulario de registro y la tabla de clientes."""
        pestana = ttk.Frame(cuaderno)                                # Contenedor de la pestaña
        cuaderno.add(pestana, text="Clientes")                       # Se agrega al cuaderno

        # Formulario de registro
        formulario = ttk.LabelFrame(pestana, text="Registrar cliente")  # Marco con título
        formulario.pack(fill="x", padx=8, pady=8)                    # Ancho completo
        self._entradas_cliente = {}                                  # campo -> Entry
        campos = [("nombre", "Nombre:"), ("documento", "Documento:"),  # Campos del cliente
                  ("correo", "Correo:"), ("telefono", "Teléfono:")]
        for columna, (campo, etiqueta) in enumerate(campos):         # Un par etiqueta/campo por dato
            # Etiqueta del campo
            ttk.Label(formulario, text=etiqueta).grid(row=0, column=columna * 2, padx=5, pady=8)
            entrada = ttk.Entry(formulario, width=24)                # Campo de texto
            entrada.grid(row=0, column=columna * 2 + 1, padx=5)      # Junto a su etiqueta
            self._entradas_cliente[campo] = entrada                  # Se guarda para leerlo
        ttk.Button(formulario, text="Registrar cliente",             # Botón de registro
                   command=self._registrar_cliente).grid(row=0, column=8, padx=10)

        # Tabla de clientes registrados
        columnas = {"id": "ID", "nombre": "Nombre", "documento": "Documento",  # Columnas
                    "correo": "Correo", "telefono": "Teléfono"}
        self.tabla_clientes = self._crear_tabla(pestana, columnas)   # Tabla de clientes

    def _registrar_cliente(self):
        """Lee el formulario y registra el cliente mediante el gestor."""
        datos = {campo: e.get() for campo, e in self._entradas_cliente.items()}  # Datos escritos
        cliente = self._ejecutar_seguro(lambda: self._gestor.registrar_cliente(**datos))  # Registro
        if cliente is not None:                                      # Registro exitoso
            for entrada in self._entradas_cliente.values():          # Cada campo del formulario
                entrada.delete(0, "end")                             # Se limpia
            messagebox.showinfo("Cliente registrado", cliente.describir())  # Confirmación

    # ======================================================
    # Pestaña 2: Servicios
    # ======================================================

    def _crear_pestana_servicios(self, cuaderno):
        """Construye el formulario de servicios, su tabla y los botones de disponibilidad."""
        pestana = ttk.Frame(cuaderno)                                # Contenedor de la pestaña
        cuaderno.add(pestana, text="Servicios")                      # Se agrega al cuaderno

        formulario = ttk.LabelFrame(pestana, text="Crear servicio")  # Marco con título
        formulario.pack(fill="x", padx=8, pady=8)                    # Ancho completo

        # Tipo de servicio: define la clase y los campos adicionales
        ttk.Label(formulario, text="Tipo:").grid(row=0, column=0, padx=5, pady=6, sticky="e")
        self.combo_tipo_servicio = ttk.Combobox(                     # Lista de tipos
            formulario, values=list(CAMPOS_SERVICIO), state="readonly", width=24)
        self.combo_tipo_servicio.current(0)                          # Primer tipo seleccionado
        self.combo_tipo_servicio.grid(row=0, column=1, padx=5, sticky="w")  # Ubicación de la lista
        self.combo_tipo_servicio.bind("<<ComboboxSelected>>",        # Al cambiar el tipo...
                                      lambda evento: self._actualizar_campos_servicio())

        ttk.Label(formulario, text="Nombre:").grid(row=0, column=2, padx=5, sticky="e")  # Etiqueta del nombre
        self.entrada_nombre_servicio = ttk.Entry(formulario, width=28)  # Nombre del servicio
        self.entrada_nombre_servicio.grid(row=0, column=3, padx=5, sticky="w")  # Ubicación del campo

        self.etiqueta_tarifa = ttk.Label(formulario, text="")        # Cambia según el tipo
        self.etiqueta_tarifa.grid(row=0, column=4, padx=5, sticky="e")  # Ubicación de la etiqueta
        self.entrada_tarifa = ttk.Entry(formulario, width=14)        # Tarifa base
        self.entrada_tarifa.grid(row=0, column=5, padx=5, sticky="w")   # Ubicación del campo

        self.marco_campos_servicio = ttk.Frame(formulario)           # Campos propios del tipo
        # Debajo de la primera fila
        self.marco_campos_servicio.grid(row=1, column=0, columnspan=6, sticky="w", pady=4)

        ttk.Button(formulario, text="Crear servicio",                # Botón de creación
                   command=self._registrar_servicio).grid(row=0, column=6, rowspan=2, padx=10)

        columnas = {"id": "ID", "tipo": "Tipo", "nombre": "Nombre", "detalle": "Detalle",  # Columnas
                    "tarifa": "Tarifa", "disponible": "Disponibilidad"}
        self.tabla_servicios = self._crear_tabla(pestana, columnas)  # Tabla de servicios

        acciones = ttk.Frame(pestana)                                # Barra de botones inferior
        acciones.pack(fill="x", padx=8, pady=(0, 8))                    # Ancho completo
        ttk.Button(acciones, text="Marcar disponible",               # Activa el servicio
                   command=lambda: self._cambiar_disponibilidad(True)).pack(side="left", padx=5)
        ttk.Button(acciones, text="Marcar no disponible",            # Desactiva el servicio
                   command=lambda: self._cambiar_disponibilidad(False)).pack(side="left", padx=5)

        self._actualizar_campos_servicio()                           # Campos del primer tipo

    def _actualizar_campos_servicio(self):
        """Muestra los campos propios del tipo de servicio seleccionado."""
        etiqueta_tarifa, campos = CAMPOS_SERVICIO[self.combo_tipo_servicio.get()]  # Configuración
        self.etiqueta_tarifa.config(text=etiqueta_tarifa)            # Por hora o por día
        for widget in self.marco_campos_servicio.winfo_children():   # Campos del tipo anterior
            widget.destroy()                                         # Se eliminan
        self._entradas_servicio = {}                                 # Se reinicia el registro
        for columna, (campo, etiqueta, opciones) in enumerate(campos):  # Un campo por parámetro
            ttk.Label(self.marco_campos_servicio, text=etiqueta).grid(   # Etiqueta del campo
                row=0, column=columna * 2, padx=5, sticky="e")
            if opciones:                                             # Hay opciones fijas
                widget = ttk.Combobox(self.marco_campos_servicio, values=opciones,  # Lista
                                      state="readonly", width=12)
            else:                                                    # Valor libre
                widget = ttk.Entry(self.marco_campos_servicio, width=16)  # Campo de texto
            widget.grid(row=0, column=columna * 2 + 1, padx=5, sticky="w")  # Junto a su etiqueta
            self._entradas_servicio[campo] = widget                  # Se guarda para leerlo

    def _registrar_servicio(self):
        """Crea el servicio del tipo seleccionado con los datos del formulario."""
        tipo = self.combo_tipo_servicio.get()                        # Tipo elegido
        datos = {campo: w.get() for campo, w in self._entradas_servicio.items()}  # Campos propios
        datos["nombre"] = self.entrada_nombre_servicio.get()         # Nombre del servicio
        datos["tarifa_base"] = self.entrada_tarifa.get()             # Tarifa base
        # Creación protegida
        servicio = self._ejecutar_seguro(lambda: self._gestor.registrar_servicio(tipo, **datos))
        if servicio is not None:                                     # Creación exitosa
            self.entrada_nombre_servicio.delete(0, "end")            # Limpia el nombre
            self.entrada_tarifa.delete(0, "end")                     # Limpia la tarifa
            self._actualizar_campos_servicio()                       # Limpia campos propios
            messagebox.showinfo("Servicio creado", servicio.describir())  # Confirmación

    def _cambiar_disponibilidad(self, disponible):
        """Activa o desactiva el servicio seleccionado en la tabla."""
        seleccion = self.tabla_servicios.selection()                 # Fila seleccionada
        if not seleccion:                                            # No hay selección
            messagebox.showwarning("Sin selección", "Seleccione un servicio de la tabla.")  # Aviso al usuario
            return                                                   # No se hace nada
        self._ejecutar_seguro(                                       # El ID es el iid de la fila
            lambda: self._gestor.cambiar_disponibilidad(seleccion[0], disponible))

    # ======================================================
    # Pestaña 3: Reservas
    # ======================================================

    def _crear_pestana_reservas(self, cuaderno):
        """Construye el formulario, la tabla, el panel de detalle y las acciones de reservas."""
        pestana = ttk.Frame(cuaderno)                                # Contenedor de la pestaña
        cuaderno.add(pestana, text="Reservas")                       # Se agrega al cuaderno

        formulario = ttk.LabelFrame(pestana, text="Crear reserva")   # Marco con título
        formulario.pack(fill="x", padx=8, pady=8)                    # Ancho completo

        ttk.Label(formulario, text="Cliente:").grid(row=0, column=0, padx=5, pady=8)  # Etiqueta del cliente
        self.combo_cliente = ttk.Combobox(formulario, state="readonly", width=30)  # Clientes
        self.combo_cliente.grid(row=0, column=1, padx=5)                # Ubicación de la lista

        ttk.Label(formulario, text="Servicio:").grid(row=0, column=2, padx=5)  # Etiqueta del servicio
        self.combo_servicio = ttk.Combobox(formulario, state="readonly", width=40)  # Servicios
        self.combo_servicio.grid(row=0, column=3, padx=5)               # Ubicación de la lista
        self.combo_servicio.bind("<<ComboboxSelected>>",             # Al elegir un servicio...
                                 lambda evento: self._actualizar_unidad())

        self.etiqueta_duracion = ttk.Label(formulario, text="Duración:")  # Muestra la unidad
        self.etiqueta_duracion.grid(row=0, column=4, padx=5)            # Ubicación de la etiqueta
        self.entrada_duracion = ttk.Entry(formulario, width=8)       # Duración solicitada
        self.entrada_duracion.grid(row=0, column=5, padx=5)             # Ubicación del campo

        ttk.Button(formulario, text="Crear reserva",                 # Botón de creación
                   command=self._crear_reserva).grid(row=0, column=6, padx=10)

        # Zona central: tabla de reservas + panel de detalle
        centro = ttk.Frame(pestana)                                  # Contenedor central
        centro.pack(fill="both", expand=True, padx=8)                   # Ocupa el espacio disponible
        columnas = {"id": "ID", "cliente": "Cliente", "servicio": "Servicio",  # Columnas
                    "duracion": "Duración", "estado": "Estado", "costo": "Costo total"}
        self.tabla_reservas = self._crear_tabla(centro, columnas, lado="left")  # Tabla a la izquierda
        self.tabla_reservas.tag_configure(Reserva.PROCESADA, foreground="#1b7f3b")   # Verde
        self.tabla_reservas.tag_configure(Reserva.CANCELADA, foreground="#8a8a8a")   # Gris
        self.tabla_reservas.tag_configure(Reserva.CONFIRMADA, foreground="#1f5fbf")  # Azul

        marco_detalle = ttk.LabelFrame(centro, text="Detalle")       # Panel a la derecha
        marco_detalle.pack(side="right", fill="both", padx=(8, 0), pady=4)  # A la derecha de la tabla
        self.texto_detalle = self._crear_texto(marco_detalle, ancho=44)  # Texto de solo lectura

        # Acciones sobre la reserva seleccionada
        acciones = ttk.LabelFrame(pestana, text="Acciones sobre la reserva seleccionada")
        acciones.pack(fill="x", padx=8, pady=8)                         # Ancho completo
        ttk.Button(acciones, text="Confirmar",                       # Pendiente -> Confirmada
                   command=self._confirmar_reserva).pack(side="left", padx=5, pady=6)
        ttk.Button(acciones, text="Cancelar",                        # -> Cancelada
                   command=self._cancelar_reserva).pack(side="left", padx=5)
        ttk.Button(acciones, text="Ver variantes de costo",          # Las 3 formas de calcular_costo()
                   command=self._ver_costos).pack(side="left", padx=5)
        ttk.Separator(acciones, orient="vertical").pack(side="left", fill="y", padx=10)  # Separador vertical
        self.var_iva = tk.BooleanVar(value=True)                     # Aplicar IVA (marcado)
        ttk.Checkbutton(acciones, text="Aplicar IVA (19 %)",         # Casilla del IVA
                        variable=self.var_iva).pack(side="left", padx=5)
        ttk.Label(acciones, text="Descuento (%):").pack(side="left", padx=(10, 2))  # Etiqueta del descuento
        self.entrada_descuento = ttk.Entry(acciones, width=6)        # Descuento opcional
        self.entrada_descuento.pack(side="left")                        # Junto a su etiqueta
        ttk.Button(acciones, text="Procesar",                        # Confirmada -> Procesada
                   command=self._procesar_reserva).pack(side="left", padx=10)

    def _actualizar_unidad(self):
        """Muestra en la etiqueta la unidad de duración del servicio elegido."""
        servicio = self._gestor.buscar_servicio(self._id_de_combo(self.combo_servicio))  # Servicio
        unidad = servicio.UNIDAD if servicio else ""                 # Horas, días o nada
        # Etiqueta con la unidad
        self.etiqueta_duracion.config(text=f"Duración ({unidad}):" if unidad else "Duración:")

    @staticmethod
    def _id_de_combo(combo):
        """Extrae el identificador (texto antes de ' - ') de una opción del combo."""
        return combo.get().split(" - ")[0].strip()                   # Ej: "SRV-001 - Sala" -> "SRV-001"

    def _reserva_seleccionada(self):
        """Identificador de la reserva seleccionada en la tabla, o None."""
        seleccion = self.tabla_reservas.selection()                  # Fila seleccionada
        if not seleccion:                                            # No hay selección
            messagebox.showwarning("Sin selección", "Seleccione una reserva de la tabla.")  # Aviso al usuario
            return None                                              # Sin reserva
        return seleccion[0]                                          # El iid es el ID de la reserva

    def _mostrar_detalle(self, texto):
        """Escribe un texto en el panel de detalle (solo lectura)."""
        self._escribir_texto(self.texto_detalle, texto)              # Reemplaza el contenido

    def _crear_reserva(self):
        """Crea una reserva con el cliente, el servicio y la duración elegidos."""
        documento = self._id_de_combo(self.combo_cliente)            # Documento del cliente
        id_servicio = self._id_de_combo(self.combo_servicio)         # ID del servicio
        duracion = self.entrada_duracion.get()                       # Duración escrita
        reserva = self._ejecutar_seguro(                             # Creación protegida
            lambda: self._gestor.crear_reserva(documento, id_servicio, duracion))
        if reserva is not None:                                      # Creación exitosa
            self.entrada_duracion.delete(0, "end")                   # Limpia la duración
            self._mostrar_detalle("Reserva creada.\n\n" + reserva.describir())  # Detalle

    def _confirmar_reserva(self):
        """Confirma la reserva seleccionada."""
        id_reserva = self._reserva_seleccionada()                    # Reserva elegida
        if id_reserva:                                               # Hay selección
            # Confirmación protegida
            reserva = self._ejecutar_seguro(lambda: self._gestor.confirmar_reserva(id_reserva))
            if reserva is not None:                                  # Confirmación exitosa
                # Detalle de la reserva
                self._mostrar_detalle("Reserva confirmada.\n\n" + reserva.describir())

    def _cancelar_reserva(self):
        """Cancela la reserva seleccionada."""
        id_reserva = self._reserva_seleccionada()                    # Reserva elegida
        if id_reserva:                                               # Hay selección
            # Cancelación protegida
            reserva = self._ejecutar_seguro(lambda: self._gestor.cancelar_reserva(id_reserva))
            if reserva is not None:                                  # Cancelación exitosa
                self._mostrar_detalle("Reserva cancelada.\n\n" + reserva.describir())  # Detalle de la reserva

    def _ver_costos(self):
        """Muestra las tres formas de invocar el método sobrecargado calcular_costo()."""
        id_reserva = self._reserva_seleccionada()                    # Reserva elegida
        if not id_reserva:                                           # No hay selección
            return                                                   # No se hace nada
        costos = self._ejecutar_seguro(lambda: self._gestor.simular_costos(id_reserva))  # Variantes
        if costos is not None:                                       # Cálculo exitoso
            reserva = self._gestor.buscar_reserva(id_reserva)        # Reserva consultada
            lineas = [f"VARIANTES DE calcular_costo() - {reserva.id}", ""]  # Encabezado
            # Una línea por variante
            lineas += [f"{nombre}: {formato_moneda(valor)}" for nombre, valor in costos.items()]
            self._mostrar_detalle("\n".join(lineas))                 # Se muestran en el panel

    def _leer_descuento(self):
        """
        Convierte el descuento escrito en porcentaje (ej. 10) a fracción
        (0.10). Si está vacío retorna None (variante sin descuento). Un
        texto no numérico se convierte en CalculoInconsistenteError
        encadenado al ValueError original, y se registra en el log.
        """
        texto = self.entrada_descuento.get().strip()                 # Descuento escrito
        if texto == "":                                              # Campo vacío
            return None                                              # Sin descuento
        try:                                                            # La conversión puede fallar
            # Conversión con encadenamiento; se divide entre 100 para obtener la fracción
            return convertir_numero(texto, "descuento", CalculoInconsistenteError) / 100
        except SoftwareFJError as error:                             # Texto no numérico
            registrar_error("Descuento ingresado inválido", error)   # Se registra en el log
            raise                                                    # La interfaz informa el error

    def _procesar_reserva(self):
        """Procesa la reserva seleccionada con o sin IVA y con el descuento indicado."""
        id_reserva = self._reserva_seleccionada()                    # Reserva elegida
        if not id_reserva:                                           # No hay selección
            return                                                   # No se hace nada
        impuesto = IVA if self.var_iva.get() else None               # Variante con o sin IVA

        def procesar():
            """Lee el descuento y procesa; ambos pasos pueden lanzar errores."""
            descuento = self._leer_descuento()                       # Puede lanzar error
            return self._gestor.procesar_reserva(id_reserva, impuesto, descuento)  # Costo final

        costo = self._ejecutar_seguro(procesar)                      # Procesamiento protegido
        if costo is not None:                                        # Procesamiento exitoso
            reserva = self._gestor.buscar_reserva(id_reserva)        # Reserva actualizada
            self._mostrar_detalle(f"Reserva procesada.\n\n{reserva.describir()}\n\n"  # Detalle y costo final
                                  f"Costo total: {formato_moneda(costo)}")

    # ======================================================
    # Pestaña 4: Simulación y logs
    # ======================================================

    def _crear_pestana_simulacion(self, cuaderno):
        """Construye el panel de la simulación y el visor del archivo de logs."""
        pestana = ttk.Frame(cuaderno)                                # Contenedor de la pestaña
        cuaderno.add(pestana, text="Simulación y logs")              # Se agrega al cuaderno

        # Panel izquierdo: simulación automática
        marco_simulacion = ttk.LabelFrame(pestana, text="Simulación automática de operaciones")
        marco_simulacion.pack(side="left", fill="both", expand=True, padx=8, pady=8)  # Mitad izquierda
        # Botón que inicia la simulación
        ttk.Button(marco_simulacion, text="Ejecutar simulación (13 operaciones)",
                   command=self._ejecutar_simulacion).pack(anchor="w", padx=5, pady=5)
        self.texto_simulacion = self._crear_texto(marco_simulacion, ancho=70)  # Resultados

        # Panel derecho: contenido del archivo de logs
        marco_log = ttk.LabelFrame(pestana, text="Archivo de logs (logs/software_fj.log)")
        marco_log.pack(side="right", fill="both", expand=True, padx=8, pady=8)  # Mitad derecha
        ttk.Button(marco_log, text="Actualizar log",                 # Recarga el archivo
                   command=self._refrescar_log).pack(anchor="w", padx=5, pady=5)
        self.texto_log = self._crear_texto(marco_log, ancho=70)      # Contenido del log

    def _ejecutar_simulacion(self):
        """Reinicia los datos y ejecuta la simulación sobre un sistema limpio."""
        if self._gestor.obtener_clientes() or self._gestor.obtener_servicios():  # Hay datos
            if not messagebox.askyesno(                              # Se pide confirmación
                    "Reiniciar datos",
                    "La simulación reinicia los datos registrados. ¿Desea continuar?"):
                return                                               # El usuario canceló
        EntidadBase.reiniciar_contadores()                           # IDs desde 001
        self._gestor = GestorReservas()                              # Sistema limpio
        registrar_evento("Datos del sistema reiniciados para la simulación.")  # Evento en el log
        lineas = self._ejecutar_seguro(lambda: ejecutar_simulacion(self._gestor))  # Simulación
        if lineas is not None:                                       # Terminó sin errores graves
            self._escribir_texto(self.texto_simulacion, "\n".join(lineas))  # Se muestran resultados

    def _refrescar_log(self):
        """Muestra el contenido del archivo de logs, desplazado al final."""
        self._escribir_texto(self.texto_log, leer_log())             # Contenido actual del log
        self.texto_log.see("end")                                    # Muestra las últimas líneas

    # ======================================================
    # Utilidades de la interfaz
    # ======================================================

    @staticmethod
    def _crear_tabla(padre, columnas, lado=None):
        """Crea un Treeview con las columnas dadas (clave interna -> encabezado)."""
        tabla = ttk.Treeview(padre, columns=list(columnas), show="headings", height=12)  # Tabla
        for clave, encabezado in columnas.items():                   # Cada columna
            tabla.heading(clave, text=encabezado)                    # Título visible
            tabla.column(clave, anchor="center", width=140)          # Ancho y alineación
        if lado:                                                     # Ubicación lateral
            tabla.pack(side=lado, fill="both", expand=True, pady=4)     # Tabla al lado indicado
        else:                                                        # Ubicación a lo ancho
            tabla.pack(fill="both", expand=True, padx=8, pady=(0, 8))   # Tabla a lo ancho
        return tabla                                                 # Tabla lista

    @staticmethod
    def _crear_texto(padre, ancho):
        """Crea un cuadro de texto de solo lectura con barra de desplazamiento."""
        barra = ttk.Scrollbar(padre)                                 # Barra vertical
        texto = tk.Text(padre, width=ancho, height=20, font=("Consolas", 9),  # Fuente de ancho fijo
                        wrap="word", state="disabled", yscrollcommand=barra.set)
        barra.config(command=texto.yview)                            # Conecta barra y texto
        barra.pack(side="right", fill="y", pady=5)                   # Barra a la derecha
        texto.pack(fill="both", expand=True, padx=5, pady=5)         # Texto ocupa el resto
        return texto                                                 # Cuadro de texto listo

    @staticmethod
    def _escribir_texto(widget, contenido):
        """Reemplaza el contenido de un cuadro de texto de solo lectura."""
        widget.config(state="normal")                                # Se habilita la escritura
        widget.delete("1.0", "end")                                  # Se borra el contenido
        widget.insert("1.0", contenido)                              # Se escribe el nuevo
        widget.config(state="disabled")                              # Vuelve a solo lectura

    def _refrescar_todo(self):
        """
        Actualiza tablas, listas desplegables y el visor de logs,
        conservando la fila que el usuario tenía seleccionada en cada tabla.
        """
        tablas = (self.tabla_clientes, self.tabla_servicios, self.tabla_reservas)  # Las 3 tablas
        seleccion = {tabla: tabla.selection() for tabla in tablas}   # Selección actual
        self._cargar_tablas()                                        # Datos actualizados
        for tabla, filas in seleccion.items():                       # Cada tabla
            filas = [f for f in filas if tabla.exists(f)]            # Filas que siguen existiendo
            if filas:                                                # Había selección
                tabla.selection_set(filas)                           # Se restaura
        self._refrescar_log()                                        # Log actualizado

    def _cargar_tablas(self):
        """Vuelve a llenar las tablas y las listas desplegables desde el gestor."""
        # Clientes
        self.tabla_clientes.delete(*self.tabla_clientes.get_children())  # Vacía la tabla
        for c in self._gestor.obtener_clientes():                    # Cada cliente
            self.tabla_clientes.insert("", "end", iid=c.id, values=( # Una fila por cliente
                c.id, c.nombre, c.documento, c.correo, c.telefono))
        # Servicios
        self.tabla_servicios.delete(*self.tabla_servicios.get_children())  # Vacía la tabla
        for s in self._gestor.obtener_servicios():                   # Cada servicio
            self.tabla_servicios.insert("", "end", iid=s.id, values=(  # Una fila por servicio
                s.id, s.TIPO, s.nombre, s.obtener_detalle(), formato_moneda(s.tarifa_base),
                "Disponible" if s.disponible else "No disponible"))
        # Reservas
        self.tabla_reservas.delete(*self.tabla_reservas.get_children())  # Vacía la tabla
        for r in self._gestor.obtener_reservas():                    # Cada reserva
            costo = formato_moneda(r.costo_total) if r.costo_total is not None else "-"  # Costo
            self.tabla_reservas.insert("", "end", iid=r.id, tags=(r.estado,), values=(  # Color por estado
                r.id, r.cliente.nombre, r.servicio.nombre,
                f"{r.duracion:g} {r.servicio.UNIDAD}", r.estado, costo))
        # Opciones de las listas desplegables de la pestaña Reservas
        self.combo_cliente["values"] = [                             # "documento - nombre"
            f"{c.documento} - {c.nombre}" for c in self._gestor.obtener_clientes()]
        self.combo_servicio["values"] = [                            # "ID - nombre (tipo)"
            f"{s.id} - {s.nombre} ({s.TIPO})" for s in self._gestor.obtener_servicios()]


# ----------------------------------------------------------
# 4. Punto de entrada
# ----------------------------------------------------------
def main():
    """Inicia la interfaz gráfica, o solo la simulación si se usa --consola."""
    if "--consola" in sys.argv:                  # Modo consola: solo la simulación
        print("\n".join(ejecutar_simulacion(GestorReservas())))  # Resultados en pantalla
        return                                   # Termina sin abrir ventanas
    app = SoftwareFJApp()                        # Modo gráfico (por defecto)
    app.mainloop()                               # Ciclo de eventos de la ventana


if __name__ == "__main__":                       # Solo al ejecutar este archivo directamente
    main()                                       # Inicio del programa
