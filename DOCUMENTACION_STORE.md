# Documentación del Módulo Store

## Índice
1. [Arquitectura General](#arquitectura-general)
2. [Modelos de Datos](#modelos-de-datos)
3. [Enums y Choices](#enums-y-choices)
4. [Lógica de Negocio](#lógica-de-negocio)
5. [Relaciones entre Modelos](#relaciones-entre-modelos)
6. [Ejemplos de Uso](#ejemplos-de-uso)

---

## Arquitectura General

El módulo **Store** maneja toda la lógica de ventas, pedidos, pagos y gestión de clientes. Está diseñado para un sistema de viajes y turismo con las siguientes características principales:

### Componentes Principales

1. **Gestión de Pedidos**: Orders y OrderDetails
2. **Sistema de Ventas**: Sales con múltiples tipos de pago
3. **Gestión de Vales**: Vouchers para servicios turísticos
4. **Sistema de Facturación**: Bills con diferentes estados
5. **Gestión de Acompañantes**: Companions para viajes grupales
6. **Sistema de Notificaciones**: Notifications para comunicación con clientes

### Flujo de Negocio

```
Cliente → Order → OrderDetails → Sales → Vouchers → Bills
                ↓
            Notifications
```

---

## Modelos de Datos

### 1. Companions (Acompañantes)

**Propósito**: Gestiona la información de acompañantes en viajes grupales.

```python
class Companions(models.Model):
    id = models.AutoField("companion_id", primary_key=True)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    identity_document_type = models.CharField(choices=IdentityDocumentType.choices())
    identity_document = models.CharField(max_length=255)
    born_date = models.DateField()
    sex = models.CharField(choices=SexType.choices())
    observations = models.TextField()
```

**Características**:
- **Identificación**: Tipo y número de documento de identidad
- **Información Personal**: Nombre, apellido, fecha de nacimiento, sexo
- **Observaciones**: Campo de texto para notas adicionales

### 2. Orders (Pedidos)

**Propósito**: Representa los pedidos principales de los clientes.

```python
class Orders(models.Model):
    id = models.AutoField("order_id", primary_key=True)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    date = models.DateTimeField()
    state = models.CharField(choices=OrderTravelPackageStatus.choices())
    total = models.FloatField(validators=[MinValueValidator(0)])
    address = models.ForeignKey(Addresses, on_delete=models.CASCADE)
    notes = models.TextField()
```

**Características**:
- **Cliente**: Referencia al cliente que realiza el pedido
- **Estado**: Seguimiento del estado del pedido (Pending, Confirmed, etc.)
- **Total**: Monto total del pedido con validación de valor mínimo
- **Dirección**: Dirección de entrega/facturación
- **Notas**: Observaciones adicionales del pedido

### 3. OrderDetails (Detalles del Pedido)

**Propósito**: Detalla los productos específicos en cada pedido.

```python
class OrderDetails(models.Model):
    id = models.AutoField("order_detail_id", primary_key=True)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    product_metadata = models.ForeignKey(ProductsMetadata, on_delete=models.CASCADE)
    package = models.ForeignKey(Packages, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    unit_price = models.FloatField(validators=[MinValueValidator(0)])
    subtotal = models.FloatField(validators=[MinValueValidator(0)])
    discount_applied = models.FloatField(validators=[MinValueValidator(0)])
```

**Características**:
- **Producto**: Referencia al producto específico y su paquete
- **Cantidad y Precios**: Cantidad, precio unitario y subtotal
- **Descuentos**: Campo para aplicar descuentos específicos
- **Validaciones**: Todos los campos numéricos tienen validación de valor mínimo

### 4. Sales (Ventas)

**Propósito**: Registra las transacciones de venta con información de pago.

```python
class Sales(models.Model):
    id = models.AutoField("sale_id", primary_key=True)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    transaction_number = models.IntegerField()
    sale_date = models.DateTimeField()
    total = models.FloatField(validators=[MinValueValidator(0)])
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.DUE
    )
    sale_type = models.CharField(
        max_length=20,
        choices=SaleType.choices,
        default=SaleType.RETAIL
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.ONLINE
    )
```

**Características**:
- **Número de Transacción**: Identificador único de la transacción
- **Estado de Pago**: Due, Paid (Cash/Cheque/Online), Cancelled
- **Tipo de Venta**: Retail, Wholesale, Online, In-Store, Backorder
- **Tipo de Pago**: Cash, Cheque, Credit/Debit Card, Online, Wire Transfer

### 5. Vouchers (Vales)

**Propósito**: Gestiona los vales para servicios turísticos específicos.

```python
class Vouchers(models.Model):
    id = models.AutoField("voucher_id", primary_key=True)
    sale = models.ForeignKey(Sales, on_delete=models.CASCADE)
    emission_date = models.DateTimeField()
    voucher_code = models.CharField(max_length=128)
    passenger_type = models.CharField(
        choices=PassengerType.choices,
        default=PassengerType.Cl,
    )
    passenger = models.ForeignKey(Companions, on_delete=models.CASCADE, null=True)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, null=True)
    state = models.CharField(
        choices=VoucherState.choices,
        default=VoucherState.AVAILABLE,
    )
```

**Características**:
- **Código de Vale**: Identificador único del vale
- **Tipo de Pasajero**: Client o Company (acompañante)
- **Estado del Vale**: Available, Issued, Redeemed, Expired, Retracted
- **Pasajero**: Puede ser el cliente principal o un acompañante

### 6. VoucherDetails (Detalles del Vale)

**Propósito**: Especifica los servicios incluidos en cada vale.

```python
class VoucherDetails(models.Model):
    id = models.AutoField("voucher_detail_id", primary_key=True)
    voucher = models.ForeignKey(Vouchers, on_delete=models.CASCADE)
    product_metadata = models.ForeignKey(ProductsMetadata, on_delete=models.CASCADE)
    package = models.ForeignKey(Packages, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=32)
    product_type = models.CharField(choices=VoucherState.choices)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    order = models.CharField(max_length=32)
```

**Características**:
- **Servicio**: Nombre específico del servicio incluido
- **Tipo de Producto**: Clasificación del servicio
- **Cantidad**: Número de unidades del servicio
- **Orden**: Secuencia o prioridad del servicio

### 7. Bills (Facturas)

**Propósito**: Gestiona la facturación con diferentes tipos y estados.

```python
class Bills(models.Model):
    id = models.AutoField("bill_id", primary_key=True)
    sale = models.ForeignKey(Sales, on_delete=models.CASCADE)
    bill_number = models.PositiveIntegerField()
    emission_date = models.DateTimeField()
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, null=True)
    items_details = models.TextField()
    total = models.FloatField(validators=[MinValueValidator(0)])
    state = models.CharField(
        max_length=20,
        choices=InvoiceState.choices,
        default=InvoiceState.DRAFT
    )
    bill_type = models.CharField(
        max_length=15,
        choices=BillType.choices,
        default=BillType.STANDARD
    )
```

**Características**:
- **Número de Factura**: Identificador único de la factura
- **Detalles de Items**: Descripción detallada de los productos/servicios
- **Estado de Factura**: Draft, Unpaid, Paid, Refunded, etc.
- **Tipo de Factura**: Standard, Pro Forma, Credit, Debit, etc.

### 8. Notifications (Notificaciones)

**Propósito**: Sistema de comunicación automatizada con clientes.

```python
class Notifications(models.Model):
    id = models.AutoField("notification_id", primary_key=True)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    email_destination = models.EmailField()
    subject = models.CharField()
    body = models.TextField()
    date = models.DateTimeField()
    notification_type = models.CharField(choices=NotificationType.choices())
    shipping_state = models.CharField(choices=OrderTravelPackageStatus.choices())
```

**Características**:
- **Destinatario**: Email del cliente
- **Tipo de Notificación**: Booking Pending, Confirmed, Trip Started, etc.
- **Estado de Envío**: Seguimiento del estado de la notificación
- **Contenido**: Asunto y cuerpo del mensaje

---

## Enums y Choices

### 1. SexType
```python
class SexType(Enum):
    M = "M"
    F = "F"
```

### 2. OrderTravelPackageStatus
```python
class OrderTravelPackageStatus(str, Enum):
    PENDING       = "Pending"
    CONFIRMED     = "Confirmed"
    UPCOMING      = "Upcoming"
    IN_PROGRESS   = "In Progress"
    COMPLETED     = "Completed"
    CANCELLED     = "Cancelled"
    REFUNDED      = "Refunded"
```

### 3. NotificationType
```python
class NotificationType(Enum):
    BOOKING_PENDING       = ("BOOKING_PENDING",       "Booking Pending")
    BOOKING_CONFIRMED     = ("BOOKING_CONFIRMED",     "Booking Confirmed")
    TRIP_UPCOMING_REMINDER = ("TRIP_UPCOMING_REMINDER","Upcoming Trip Reminder")
    TRIP_STARTED          = ("TRIP_STARTED",          "Trip Started")
    TRIP_COMPLETED        = ("TRIP_COMPLETED",        "Trip Completed")
    BOOKING_CANCELLED     = ("BOOKING_CANCELLED",     "Booking Cancelled")
    REFUND_ISSUED         = ("REFUND_ISSUED",         "Refund Issued")
```

### 4. PaymentStatus
```python
class PaymentStatus(models.TextChoices):
    DUE       = "DUE", "Due"
    PAID_CASH = "PAID_CASH", "Paid (Cash)"
    PAID_CHEQUE = "PAID_CHEQUE", "Paid (Cheque)"
    PAID_ONLINE = "PAID_ONLINE", "Paid (Online)"
    CANCELLED = "CANCELLED", "Cancelled"
```

### 5. SaleType
```python
class SaleType(models.TextChoices):
    RETAIL    = "RETAIL", "Retail"
    WHOLESALE = "WHOLESALE", "Wholesale"
    ONLINE    = "ONLINE", "Online"
    IN_STORE  = "IN_STORE", "In‑Store"
    BACKORDER = "BACKORDER", "Backorder"
```

### 6. PaymentType
```python
class PaymentType(models.TextChoices):
    CASH         = "CASH", "Cash"
    CHEQUE       = "CHEQUE", "Cheque"
    CREDIT_CARD  = "CREDIT_CARD", "Credit Card"
    DEBIT_CARD   = "DEBIT_CARD", "Debit Card"
    ONLINE       = "ONLINE", "Online Payment"
    WIRE_TRANSFER = "WIRE_TRANSFER", "Wire Transfer"
```

### 7. PassengerType
```python
class PassengerType(models.TextChoices):
    Cl = "CLIENT", "Client"
    CO = "COMPANY", "Companion"
```

### 8. VoucherState
```python
class VoucherState(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Available"     # Vale creado y listo para asignarse
    ISSUED    = "ISSUED",    "Issued"        # Vale entregado a un destinatario
    REDEEMED  = "REDEEMED",  "Redeemed"      # Vale ya utilizado
    EXPIRED   = "EXPIRED",   "Expired"       # Fecha de caducidad superada
    RETRACTED = "RETRACTED", "Retracted"     # Vale devuelto al emisor (cancelado)
```

### 9. InvoiceState
```python
class InvoiceState(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    UNPAID = "UNPAID", "Unpaid"
    SCHEDULED = "SCHEDULED", "Scheduled"
    PARTIALLY_PAID = "PARTIALLY_PAID", "Partially Paid"
    PAID = "PAID", "Paid"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED", "Partially Refunded"
    REFUNDED = "REFUNDED", "Refunded"
    CANCELED = "CANCELED", "Canceled"
    FAILED = "FAILED", "Failed"
```

### 10. BillType
```python
class BillType(models.TextChoices):
    STANDARD = "STANDARD", "Standard"
    PROFORMA = "PROFORMA", "Pro Forma"
    INTERIM = "INTERIM", "Interim"
    FINAL = "FINAL", "Final"
    RECURRING = "RECURRING", "Recurring"
    CREDIT = "CREDIT", "Credit"
    DEBIT = "DEBIT", "Debit"
    TIMESHEET = "TIMESHEET", "Timesheet"
    COMMERCIAL = "COMMERCIAL", "Commercial"
    EXPENSE = "EXPENSE", "Expense"
    COMPOSITE = "COMPOSITE", "Composite"
    PAST_DUE = "PAST_DUE", "Past Due"
```

---

## Lógica de Negocio

### 1. Flujo de Creación de Pedido

1. **Cliente crea pedido** → Se crea registro en `Orders`
2. **Se agregan productos** → Se crean registros en `OrderDetails`
3. **Se procesa la venta** → Se crea registro en `Sales`
4. **Se generan vales** → Se crean registros en `Vouchers` y `VoucherDetails`
5. **Se emite factura** → Se crea registro en `Bills`
6. **Se envían notificaciones** → Se crean registros en `Notifications`

### 2. Estados de Pedido

- **Pending**: Pedido creado, pendiente de confirmación
- **Confirmed**: Pedido confirmado, listo para procesar
- **Upcoming**: Viaje próximo a comenzar
- **In Progress**: Viaje en curso
- **Completed**: Viaje finalizado
- **Cancelled**: Pedido cancelado
- **Refunded**: Pedido reembolsado

### 3. Gestión de Vales

- **Available**: Vale creado y disponible
- **Issued**: Vale entregado al pasajero
- **Redeemed**: Vale utilizado en el servicio
- **Expired**: Vale vencido por fecha
- **Retracted**: Vale cancelado y devuelto

### 4. Estados de Factura

- **Draft**: Borrador de factura
- **Unpaid**: Factura emitida, pendiente de pago
- **Paid**: Factura pagada completamente
- **Partially Paid**: Factura pagada parcialmente
- **Refunded**: Factura reembolsada
- **Cancelled**: Factura cancelada

---

## Relaciones entre Modelos

### Diagrama de Relaciones

```
Clients (1) ←→ (N) Orders (1) ←→ (N) OrderDetails
    ↓                                    ↓
Addresses                           ProductsMetadata
    ↓                                    ↓
Companions (1) ←→ (N) Vouchers ←→ (N) VoucherDetails
    ↓              ↓
Orders (1) ←→ (N) Sales (1) ←→ (N) Bills
    ↓
Notifications
```

### Relaciones Clave

1. **Orders → Clients**: Un cliente puede tener múltiples pedidos
2. **Orders → OrderDetails**: Un pedido puede tener múltiples productos
3. **Sales → Orders**: Una venta corresponde a un pedido
4. **Vouchers → Sales**: Los vales se generan a partir de una venta
5. **Vouchers → Companions/Clients**: Los vales pueden ser para clientes o acompañantes
6. **Bills → Sales**: Las facturas se generan a partir de las ventas
7. **Notifications → Orders**: Las notificaciones se envían por pedido

---

## Ejemplos de Uso

### 1. Crear un Pedido Completo

```python
# 1. Crear el pedido
order = Orders.objects.create(
    client=client,
    date=timezone.now(),
    state=OrderTravelPackageStatus.PENDING,
    total=1500.00,
    address=client_address,
    notes="Pedido para viaje familiar"
)

# 2. Agregar productos al pedido
OrderDetails.objects.create(
    order=order,
    product_metadata=flight_product,
    package=flight_package,
    quantity=4,
    unit_price=300.00,
    subtotal=1200.00,
    discount_applied=0.00
)

# 3. Crear la venta
sale = Sales.objects.create(
    order=order,
    transaction_number=12345,
    sale_date=timezone.now(),
    total=1500.00,
    payment_status=PaymentStatus.PAID_ONLINE,
    sale_type=SaleType.ONLINE,
    payment_type=PaymentType.ONLINE
)

# 4. Generar vales para cada pasajero
for i, passenger in enumerate([client] + companions):
    voucher = Vouchers.objects.create(
        sale=sale,
        emission_date=timezone.now(),
        voucher_code=f"VOUCHER-{sale.id}-{i+1}",
        passenger_type=PassengerType.Cl if i == 0 else PassengerType.CO,
        passenger=passenger if isinstance(passenger, Companions) else None,
        client=passenger if isinstance(passenger, Clients) else None,
        state=VoucherState.AVAILABLE
    )
    
    # Agregar detalles del vale
    VoucherDetails.objects.create(
        voucher=voucher,
        product_metadata=flight_product,
        package=flight_package,
        service_name="Vuelo Internacional",
        product_type="FLIGHT",
        quantity=1,
        order="1"
    )

# 5. Emitir factura
bill = Bills.objects.create(
    sale=sale,
    bill_number=67890,
    emission_date=timezone.now(),
    client=client,
    items_details="Vuelo internacional para 4 pasajeros",
    total=1500.00,
    state=InvoiceState.PAID,
    bill_type=BillType.STANDARD
)

# 6. Enviar notificación
Notifications.objects.create(
    order=order,
    email_destination=client.email,
    subject="Pedido Confirmado",
    body="Su pedido ha sido confirmado exitosamente...",
    date=timezone.now(),
    notification_type=NotificationType.BOOKING_CONFIRMED,
    shipping_state=OrderTravelPackageStatus.CONFIRMED
)
```

### 2. Actualizar Estado de Pedido

```python
# Cambiar estado del pedido
order.state = OrderTravelPackageStatus.CONFIRMED
order.save()

# Enviar notificación de confirmación
Notifications.objects.create(
    order=order,
    email_destination=order.client.email,
    subject="Pedido Confirmado",
    body="Su pedido ha sido confirmado...",
    date=timezone.now(),
    notification_type=NotificationType.BOOKING_CONFIRMED,
    shipping_state=OrderTravelPackageStatus.CONFIRMED
)
```

### 3. Gestionar Vales

```python
# Marcar vale como emitido
voucher.state = VoucherState.ISSUED
voucher.save()

# Cuando se usa el servicio
voucher.state = VoucherState.REDEEMED
voucher.save()
```

### 4. Procesar Reembolso

```python
# Actualizar estado del pedido
order.state = OrderTravelPackageStatus.REFUNDED
order.save()

# Actualizar estado de la venta
sale.payment_status = PaymentStatus.CANCELLED
sale.save()

# Actualizar estado de la factura
bill.state = InvoiceState.REFUNDED
bill.save()

# Cancelar vales
vouchers = Vouchers.objects.filter(sale=sale)
vouchers.update(state=VoucherState.RETRACTED)

# Enviar notificación de reembolso
Notifications.objects.create(
    order=order,
    email_destination=order.client.email,
    subject="Reembolso Procesado",
    body="Su reembolso ha sido procesado...",
    date=timezone.now(),
    notification_type=NotificationType.REFUND_ISSUED,
    shipping_state=OrderTravelPackageStatus.REFUNDED
)
```

---

## Consideraciones de Implementación

### 1. Validaciones

- Todos los campos monetarios tienen validación de valor mínimo (0)
- Los campos de cantidad tienen validación de valor mínimo (0)
- Los emails deben tener formato válido
- Las fechas deben ser coherentes (emisión antes que vencimiento)

### 2. Integridad de Datos

- Las relaciones entre modelos mantienen la integridad referencial
- Los estados de los modelos deben ser consistentes entre sí
- Los totales deben coincidir con la suma de los subtotales

### 3. Seguridad

- Los códigos de vale deben ser únicos y seguros
- Las transacciones deben ser atómicas
- Los datos sensibles deben estar protegidos

### 4. Escalabilidad

- Los índices en campos frecuentemente consultados
- La paginación para listas grandes
- El cache para consultas frecuentes 