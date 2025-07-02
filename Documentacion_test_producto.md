# Documentación del Test CRUD de Productos

## Descripción General

Este archivo documenta el test automatizado `test_crud_activity_product` para el ciclo CRUD de productos tipo actividad en la API, así como los cambios más importantes realizados en el proyecto para que el test funcione correctamente.

---

## Cambios más importantes realizados

1. **Cambio de la base de datos a SQLite3**  
   Se modificó la configuración en `settings.py` para usar SQLite3 en vez de una base de datos externa.

2. **Ajuste del fixture `ninja_client`**  
   Se adaptó el fixture para registrar solo los endpoints de productos y evitar errores de configuración con otros routers.

3. **Registro manual de endpoints en el router de test**  
   Se agregaron manualmente los endpoints CRUD de productos al router de pruebas.

4. **Creación de un endpoint auxiliar de listado sin paginación**  
   Se implementó una función `list_products_no_pagination` para devolver una lista simple de productos en el entorno de test, evitando conflictos con la paginación de Ninja.

5. **Uso de `serialize_product_metadata` en el listado de test**  
   Se utilizó esta función para asegurar que la estructura de los productos listados coincida con el schema esperado.

6. **Corrección de la estructura de respuesta esperada en el test**  
   Se ajustó el test para iterar sobre una lista simple en vez de acceder a `"items"`.

7. **Registro correcto del status 204 en el endpoint DELETE**  
   Se especificó `response={204: None}` al registrar el endpoint de borrado para evitar errores de configuración de Ninja.

8. **Filtrado del campo `currency` en la creación de productos**  
   Se eliminó el campo `currency` antes de instanciar modelos de Django que no lo aceptan.

9. **Cambio del schema de actualización para aceptar updates anidados**  
   Se usó `ProductsMetadataUpdateWithProduct` en el endpoint PATCH para permitir updates anidados.

---

## Documentación del test: `test_crud_activity_product`

### Ubicación
`myweb/api/products/tests/test_crud_products.py`

### Objetivo

Este test automatizado valida el ciclo completo **CRUD** (Crear, Leer, Actualizar, Borrar) para productos de tipo **actividad** en la API de productos, asegurando que los endpoints principales funcionen correctamente y que las validaciones de negocio sean respetadas.

### Flujo y pruebas realizadas

1. **Creación de producto (POST `/products/create/`)**
   - Prueba la creación correcta de un producto tipo actividad.
   - Valida status, tipo, precio, nombre y existencia en base de datos.

2. **Consulta de producto (GET `/products/{id}/`)**
   - Prueba la obtención del producto recién creado.
   - Valida status, ID y nombre.

3. **Actualización de producto (PATCH `/products/{id}/`)**
   - Prueba la actualización de campos de metadata y del objeto anidado.
   - Valida status, nombre, descripción y precio actualizados.

4. **Listado de productos (GET `/products/`)**
   - Prueba que el producto actualizado aparece en el listado.
   - Valida status y presencia del ID en la lista.

5. **Borrado (DELETE `/products/{id}/`)**
   - Prueba la desactivación lógica del producto.
   - Valida status 204.

6. **Errores tras borrado**
   - Prueba que no se puede acceder, actualizar ni borrar de nuevo un producto desactivado.
   - Valida status 404 o 400 en cada caso.

7. **Creación con datos inválidos (falta campo requerido)**
   - Prueba la validación de campos obligatorios.
   - Valida status 422 y mensaje de error.

8. **Creación con valor inválido (fecha en el pasado)**
   - Prueba la validación de reglas de negocio.
   - Valida status 422 y mensaje de error.

### Cobertura y consideraciones

- El test cubre el ciclo CRUD completo, validaciones de negocio y errores comunes.
- El listado de productos en el entorno de test devuelve una lista simple, no paginada, para evitar conflictos con la paginación de Ninja.
- El test utiliza fixtures para crear proveedores y ubicaciones de prueba.
- Se usan asserts claros para cada validación.
- El test es fácilmente extensible para otros tipos de productos.

### Limitaciones

- No prueba la paginación real del endpoint de listado.
- No cubre productos de tipo vuelo, alojamiento o transporte (pero puede adaptarse fácilmente).
- No prueba relaciones complejas ni lógica de disponibilidad. 