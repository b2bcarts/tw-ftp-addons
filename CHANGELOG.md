# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## [2.3.0] - 2025-01-02

### 🔄 Cambio Arquitectural: Búsqueda Solo en FSM Location

#### Eliminada búsqueda directa en res.partner
- **CRÍTICO**: La función `_get_partner` ya NO busca en `res.partner` directamente
- Ahora busca exclusivamente en `fsm.location` y retorna el `partner_id` asociado
- Esto asegura que solo se usen técnicos registrados en Field Service Management

### 🔄 Modificado
- `_get_partner()` reescrita completamente para buscar solo en `fsm.location`
- Búsqueda por RUT del técnico en `fsm.location.partner_id.vat`
- Búsqueda por nombre del técnico en `fsm.location.partner_id.name`
- Mantiene sistema de mapeo dinámico con `ftp.file.type.column`
- Sistema de fallback mejorado cuando no hay mapeo configurado

### 🗑️ Eliminado
- Todas las búsquedas directas en tabla `res.partner`
- Lógica de creación/búsqueda de clientes genéricos
- Referencias a campos de cliente (`rut_cliente`, `nombre_cliente`)

## [2.2.0] - 2025-01-02

### 🔄 Sistema de Mapeo Dinámico de Columnas

#### Nueva funcionalidad de mapeo configurable
- **NUEVO**: Sistema de mapeo dinámico usando `ftp.file.type.column`
- Búsqueda de clientes y técnicos ahora utiliza configuración de columnas
- Soporte para múltiples variaciones de nombres de columnas
- Identificación automática del tipo de archivo

### ✨ Añadido
- Método `_get_file_type()` para identificar tipo de archivo automáticamente
- Método `_get_column_mappings()` para cargar configuración de columnas
- Método `_get_mapped_value()` para obtener valores según mapeo configurado
- Búsqueda inteligente de RUT técnico en columnas: `rut.tecnico`, `rut_tecnico`, `tecnico_rut`
- Búsqueda de cliente en múltiples columnas: `rut`, `rut.cliente`, `rut_cliente`, `vat`, `nit`

### 🔄 Modificado
- `_get_partner()` ahora usa mapeo dinámico de columnas con fallback
- `_get_fsm_location()` actualizado para buscar técnicos con mapeo dinámico
- Mejorada búsqueda con soporte para puntos en nombres de columnas
- Sistema de fallback cuando no hay mapeo configurado

## [2.1.0] - 2025-01-02

### 🔒 Cambios de Seguridad

#### Eliminada creación automática de registros
- **CRÍTICO**: El sistema ahora **NO crea nuevos clientes, productos o técnicos**
- Solo busca y utiliza registros existentes en la base de datos
- Si no encuentra un cliente, producto o técnico, la fila se omite con advertencia

### 🔄 Modificado
- Función `_get_or_create_partner` renombrada a `_get_partner` - solo busca, no crea
- Mejorada búsqueda de clientes con múltiples variaciones de RUT
- Búsqueda de clientes por nombre cuando no hay RUT disponible
- Limpiados imports no utilizados (api, ValidationError, json, datetime)

## [2.0.0] - 2025-01-02

### 🚀 Cambios Principales

#### Refactorización completa del procesamiento de órdenes
- **IMPORTANTE**: Ahora se crea **una orden de venta por cada fila** del archivo Excel
- Anteriormente se agrupaban por `id.mochila`, ahora cada fila genera su propia orden independiente

### ✨ Añadido
- Documentación completa en español para todos los métodos y clases
- Comentarios detallados explicando cada función del addon
- Validación mejorada de datos mínimos requeridos por fila
- Sistema de logs más detallado con emojis para mejor visualización (✓, ✗, ⚠)
- Contador de filas procesadas y omitidas
- Resumen de procesamiento al final del log
- Búsqueda flexible de SKUs en múltiples campos posibles
- Búsqueda flexible de cantidades en múltiples campos posibles
- Soporte para campos alternativos de RUT y nombres de cliente
- Referencia única por fila en `client_order_ref`: `FTP-{hoja}-Row{número}`

### 🔄 Modificado
- `sale_order_processor.py` completamente reescrito y comentado
- `ftp_config.py` ahora incluye documentación completa en español
- Campos de formulario traducidos al español
- Mensajes de error y notificaciones traducidos al español
- Lógica de creación de órdenes: una orden por fila en lugar de agrupar por mochila
- Mejorada la búsqueda de técnicos (fsm_location) por RUT y nombre
- Mejorada la creación de partners con valores por defecto más descriptivos

### 🐛 Corregido
- Eliminado código no utilizado de `ftp_service.py` relacionado con agrupación por mochila
- Corregida la validación de filas vacías o incompletas
- Mejorado manejo de errores cuando no se encuentra un producto por SKU
- Corregido problema de duplicación de órdenes

### 🗑️ Eliminado
- Código legacy de creación directa de órdenes en `ftp_service.py`
- Lógica de agrupación por `id.mochila` 
- Métodos no utilizados para movimientos de inventario simulados
- Imports no utilizados y código comentado

### 📝 Documentación
- Agregado CHANGELOG.md con historial de cambios
- README.md actualizado con instrucciones de instalación y uso
- Todos los métodos ahora incluyen docstrings en formato Sphinx
- Agregados type hints en la documentación

### ⚙️ Técnico
- Compatible con Odoo 16.0
- Requiere módulos: `base`, `sale`, `fieldservice`
- Dependencias Python: `paramiko`, `openpyxl`, `pandas==2.0.3`, `numpy==1.24.3`

## [1.0.0] - 2024-12-01

### Versión Inicial
- Implementación básica de conexión FTP/SFTP/SCP
- Descarga y procesamiento de archivos Excel
- Creación de órdenes agrupadas por `id.mochila`
- Integración con Field Service Management
- Cron job para procesamiento automático cada 30 minutos