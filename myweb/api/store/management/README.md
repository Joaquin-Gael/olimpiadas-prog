# Comandos de Management para Store

## Limpieza de Idempotencia

### `clean_idempotency`

Limpia registros de idempotencia antiguos (más de 48 horas por defecto).

```bash
# Limpiar registros de más de 48 horas
python manage.py clean_idempotency

# Limpiar registros de más de 24 horas
python manage.py clean_idempotency --hours 24

# Ver cuántos registros se eliminarían sin ejecutar
python manage.py clean_idempotency --dry-run
```

### Configuración en Cron

Agregar al crontab para ejecutar diariamente:

```bash
# Ejecutar cada día a las 2:00 AM
0 2 * * * cd /path/to/project && python manage.py clean_idempotency
```

## Expiración de Carritos

### `expire_carts`

Expira carritos abiertos que no han sido actualizados en las últimas 24 horas.

```bash
# Expirar carritos de más de 24 horas
python manage.py expire_carts

# Expirar carritos de más de 12 horas
python manage.py expire_carts --hours 12

# Ver cuántos carritos se expirarían sin ejecutar
python manage.py expire_carts --dry-run
```

### Configuración en Cron

Agregar al crontab para ejecutar cada hora:

```bash
# Ejecutar cada hora
0 * * * * cd /path/to/project && python manage.py expire_carts
```

## Notas Importantes

- Los comandos son seguros para ejecutar múltiples veces
- Usar `--dry-run` para verificar antes de ejecutar en producción
- Los carritos expirados liberan automáticamente el stock reservado
- Los registros de idempotencia eliminados no afectan el funcionamiento normal 