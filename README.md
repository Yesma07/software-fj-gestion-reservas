# Software FJ – Sistema Integral de Gestión de Clientes, Servicios y Reservas

Proyecto de la **Fase 4 – Prácticas simuladas** del curso **Programación (213023)** de la
Universidad Nacional Abierta y a Distancia (UNAD).

Es una aplicación de escritorio en **Python con Tkinter** para la empresa *Software FJ*, que ofrece reserva de
salas, alquiler de equipos y asesorías especializadas. El sistema gestiona clientes, servicios
y reservas **sin base de datos**: toda la información vive en objetos y listas en memoria, y el único archivo
que usa es el **registro de logs** de eventos y errores.

Su objetivo es aplicar la programación orientada a objetos y el **manejo avanzado de excepciones**, de modo que
el sistema siga funcionando aunque ocurran errores durante la ejecución.

---

## Ejecución

Requisitos: **Python 3.10 o superior**. Tkinter viene incluido en la instalación estándar de Python.

```bash
cd software_fj
python main.py              # Interfaz gráfica
python main.py --consola    # Solo la simulación de 13 operaciones, en la consola
```

El archivo de logs se crea automáticamente en `software_fj/logs/software_fj.log` y cada ejecución agrega
sus registros al final. Esta carpeta está excluida del repositorio en `.gitignore`.

---

## Estructura del proyecto

```
software-fj-gestion-reservas/
├── README.md
├── .gitignore
└── software_fj/
    ├── excepciones.py     # Jerarquía de excepciones personalizadas (SFJ-xxx)
    ├── registro_logs.py   # Registro de eventos y errores en el archivo de logs
    ├── entidades.py       # Clase abstracta EntidadBase y clase Cliente
    ├── servicios.py       # Clase abstracta Servicio y los 3 servicios especializados
    ├── reservas.py        # Clase Reserva y GestorReservas (listas internas)
    ├── main.py            # Interfaz Tkinter y simulación automática
    └── logs/              # Se crea automáticamente al ejecutar (no se versiona)
        └── software_fj.log
```

---

## Diseño orientado a objetos

| Clase | Tipo | Responsabilidad |
|---|---|---|
| `EntidadBase` | Abstracta | Entidad general del sistema: ID consecutivo, fecha de creación, `describir()` y `validar()` abstractos |
| `Cliente` | Hereda de `EntidadBase` | Datos personales privados con validación (nombre, documento, correo, teléfono) |
| `Servicio` | Abstracta, hereda de `EntidadBase` | Tarifa, disponibilidad y cálculo de costos con sus variantes |
| `ReservaSala` | Hereda de `Servicio` | Cobro por hora; capacidad de 1 a 200 personas; máximo 12 horas en bloques de 30 minutos |
| `AlquilerEquipo` | Hereda de `Servicio` | Cobro por día y por unidad; máximo 30 días completos |
| `AsesoriaEspecializada` | Hereda de `Servicio` | Cobro por hora según el nivel del asesor (Junior x1, Senior x1,5, Experto x2) |
| `Reserva` | Hereda de `EntidadBase` | Integra cliente, servicio, duración y estado; `confirmar()`, `cancelar()` y `procesar()` |
| `GestorReservas` | Concreta | Listas internas de clientes, servicios y reservas |

**Polimorfismo:** cada servicio sobrescribe `calcular_costo_base()`, `describir()` y `validar_parametros()`.

**Sobrecarga** (simulada con parámetros opcionales) en `Servicio.calcular_costo()`:

```python
servicio.calcular_costo(3)                                  # Costo base
servicio.calcular_costo(3, impuesto=0.19)                   # Con IVA
servicio.calcular_costo(3, impuesto=0.19, descuento=0.10)   # Con IVA y descuento
```

**Ciclo de vida de una reserva:**

```
Pendiente --confirmar()--> Confirmada --procesar()--> Procesada
Pendiente / Confirmada --cancelar()--> Cancelada
```

---

## Manejo de excepciones

### Excepciones personalizadas

| Excepción | Código | Cuándo se lanza |
|---|---|---|
| `SoftwareFJError` | SFJ-000 | Base de todos los errores del negocio |
| `ClienteInvalidoError` | SFJ-100 | Nombre, documento, correo o teléfono con formato inválido |
| `ParametroFaltanteError` | SFJ-110 | Falta un dato obligatorio o un parámetro del constructor |
| `ServicioInvalidoError` | SFJ-200 | Tarifa, capacidad, cantidad o nivel inválidos; tipo de servicio desconocido |
| `ServicioNoDisponibleError` | SFJ-210 | Se intenta reservar un servicio no disponible |
| `ReservaInvalidaError` | SFJ-300 | Duración fuera de rango; cliente, servicio o reserva inexistente |
| `OperacionNoPermitidaError` | SFJ-310 | Operación que no corresponde al estado (ej. cancelar una reserva procesada) o documento duplicado |
| `CalculoInconsistenteError` | SFJ-400 | Descuento o impuesto fuera de rango, costo imposible o error inesperado de cálculo |

### Estructuras utilizadas

| Estructura | Ubicación |
|---|---|
| `try/except` | `main.py` → `_ejecutar_seguro()`: todas las acciones de la interfaz |
| `try/except/else` | `reservas.py` → `registrar_cliente()`, `registrar_servicio()`, `crear_reserva()`: el `else` agrega el objeto a la lista solo si no hubo errores. También en `main.py` → `ejecutar_simulacion()` |
| `try/except/else/finally` | `reservas.py` → `Reserva.procesar()`: el `finally` registra el cierre del intento siempre |
| `try/except/finally` | `main.py` → `_ejecutar_seguro()`: el `finally` actualiza la interfaz siempre |
| Encadenamiento `raise ... from ...` | `servicios.py` → `convertir_numero()` (ValueError → error del negocio); `reservas.py` → `registrar_servicio()` (TypeError → `ParametroFaltanteError`) y `Reserva.procesar()` (error inesperado → `CalculoInconsistenteError`) |

### Estabilidad de la aplicación

- Cada operación registra su resultado en el log: los éxitos con nivel `INFO` y los errores con nivel `ERROR`,
  incluyendo la **causa original** cuando la excepción fue encadenada.
- Los errores no previstos se registran con nivel `CRITICAL` y la traza completa.
- `report_callback_exception` captura cualquier error que escape a los bloques `try` de la interfaz, así que
  **la aplicación nunca se cierra por un error**.
- Si no se puede crear el archivo de logs, el registro se envía a la consola y el sistema sigue funcionando.

---

## Simulación de operaciones

La pestaña **Simulación y logs** (o `python main.py --consola`) ejecuta 13 operaciones completas:

| # | Operación | Resultado esperado |
|---|---|---|
| 1 | Registrar cliente válido | ✔ Éxito |
| 2 | Registrar cliente con correo inválido | ✖ `ClienteInvalidoError` |
| 3 | Registrar cliente sin documento | ✖ `ParametroFaltanteError` |
| 4 | Crear servicio válido: Reserva de sala | ✔ Éxito |
| 5 | Crear servicio de equipos con cantidad negativa | ✖ `ServicioInvalidoError` |
| 6 | Crear servicio con tarifa no numérica | ✖ `ServicioInvalidoError` encadenado a `ValueError` |
| 7 | Crear servicio válido: Asesoría especializada | ✔ Éxito |
| 8 | Reserva válida: crear, confirmar y procesar con IVA | ✔ Éxito (muestra las 3 variantes de costo) |
| 9 | Reservar sala por 20 horas (máximo 12) | ✖ `ReservaInvalidaError` |
| 10 | Reservar un servicio no disponible | ✖ `ServicioNoDisponibleError` |
| 11 | Cancelar una reserva ya procesada | ✖ `OperacionNoPermitidaError` |
| 12 | Reserva válida y luego cancelada | ✔ Éxito |
| 13 | Procesar reserva con descuento del 150 % | ✖ `CalculoInconsistenteError` |

Resultado: **5 éxitos y 8 errores controlados, 13/13 según lo esperado**, y el sistema sigue activo al terminar.
Cada ejecución agrega sus eventos y errores al archivo `software_fj/logs/software_fj.log`, que también puede
consultarse desde la pestaña **Simulación y logs**.

---

## Autor

**Yesid David Marín González** – Ingeniería de Sistemas, UNAD
Curso Programación (213023), grupo 213023_189 – Noviembre de 2026
