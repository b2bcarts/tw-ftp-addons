# FTP Cuenta Cliente - Addon Odoo 16

## 📋 Descripción

Addon para Odoo 16 que automatiza la lectura de archivos Excel desde servidores FTP/SFTP/SCP y crea órdenes de venta automáticamente. El sistema valida el formato del archivo, busca coincidencias con productos (product_template) y técnicos (fsm_location), creando una orden de venta por cada fila del archivo procesado. **Importante**: Solo trabaja con técnicos registrados en Field Service Management.

## ✨ Características Principales

- 🔄 **Multi-protocolo**: Soporte para FTP, FTPS, SFTP y SCP
- 📊 **Procesamiento Excel**: Lee archivos .xlsx y .xls automáticamente
- 🛒 **Creación de Órdenes**: Genera una orden de venta por cada fila del archivo
- 🗺️ **Mapeo Dinámico**: Sistema configurable de mapeo de columnas usando `ftp.file.type.column`
- 🔍 **Validación Estricta**: Solo utiliza SKUs y técnicos existentes (no crea nuevos)
- 🔒 **Seguridad**: No crea automáticamente registros nuevos en la base de datos
- 🎯 **Solo Técnicos FSM**: Busca exclusivamente en fsm.location (no en res.partner directamente)
- 🎯 **Búsqueda Inteligente**: Soporta múltiples variaciones de RUT y nombres de columnas
- 📝 **Logs Detallados**: Registro completo de procesamiento con éxitos y errores
- ⏰ **Procesamiento Automático**: Cron job configurable para procesamiento periódico
- 🌐 **Integración Field Service**: Compatible con módulos de Field Service Management

## 🚀 Instalación

### Prerrequisitos

- Odoo 16.0
- Docker y Docker Compose
- Python 3.8+

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/addon-ftp.git
cd addon-ftp
```

2. **Iniciar los contenedores Docker**
```bash
docker compose up -d
```

3. **Esperar a que la base de datos esté lista**
```bash
# Verificar el estado de los servicios
docker compose ps
```

4. **Instalar dependencias Python en el contenedor**
```bash
docker exec addon-ftp-web-1 pip install numpy==1.24.3 pandas==2.0.3 openpyxl paramiko
```

5. **Instalar el addon en Odoo**
```bash
# Instalar módulos base y el addon FTP
docker exec addon-ftp-web-1 odoo -i base,sale,fieldservice,ftp_cuenta_cliente -d odoo --stop-after-init

# Reiniciar el servicio web
docker compose restart web
```

6. **Acceder a Odoo**
- URL: http://localhost:8069
- Usuario: admin
- Contraseña: admin

## 📖 Uso

### Configuración Inicial

1. **Crear una configuración FTP**
   - Navegar a: `FTP Cuenta Cliente > Configuraciones FTP`
   - Hacer clic en "Crear"
   - Completar los campos:
     - Nombre de Configuración
     - Servidor FTP
     - Puerto (21 para FTP, 22 para SFTP)
     - Usuario y Contraseña
     - Tipo de Conexión
     - Ruta de Descarga
     - Ruta de Procesados

2. **Probar la conexión**
   - En la configuración creada, hacer clic en "Probar Conexión"
   - Verificar que aparezca el mensaje de éxito

### Formato del Archivo Excel

El archivo Excel debe contener las siguientes columnas (los nombres pueden variar):

| Columna | Descripción | Obligatorio | Mapeo Dinámico |
|---------|-------------|-------------|----------------|
| sku / codigo | Código del producto | Sí (o descripción) | product.template.default_code |
| descripcion | Descripción del producto | Sí (o SKU) | product.template.name |
| cantidad | Cantidad a ordenar | No (default: 1) | sale.order.line.product_uom_qty |
| tecnico | Nombre del técnico | No | fsm.location.partner_id.name |
| rut / rut.tecnico | RUT del técnico | No | fsm.location.partner_id.vat |
| fecha_agenda | Fecha programada | No | sale.order.date_order |
| region | Región | No | sale.order.note |
| observaciones | Observaciones | No | sale.order.note |

**⚠️ CAMBIO IMPORTANTE**: 
- El sistema ya **NO busca clientes en res.partner** directamente
- Solo busca **técnicos en fsm.location** y usa su partner asociado
- **Eliminadas columnas**: `rut_cliente`, `cliente`, `nombre_cliente`

**Nota**: El sistema busca automáticamente variaciones de nombres de columnas del técnico:
- RUT técnico: `rut`, `rut.tecnico`, `rut_tecnico`, `tecnico_rut`, `rut.del.tecnico`
- Nombre técnico: `tecnico`, `nombre.tecnico`, `nombre_tecnico`, `tecnico.nombre`

### ⚠️ Importante: Preparación de Datos

Antes de procesar archivos, asegúrate de que:

1. **Productos existentes**: Todos los SKUs del archivo deben existir en `Inventario > Productos`
2. **Técnicos en FSM**: Los técnicos deben estar registrados en `Field Service > Ubicaciones`
3. **Partners de técnicos**: Cada ubicación FSM debe tener un partner asociado con RUT

**El sistema NO creará automáticamente**:
- ❌ Nuevos productos
- ❌ Nuevos técnicos (fsm.location)
- ❌ Nuevos partners

**🔥 CRÍTICO**: Ya no se buscan clientes genéricos. Solo se usan partners asociados a técnicos en Field Service Management.

Si algún registro no existe, la fila será omitida y se registrará una advertencia.

### Procesamiento de Archivos

#### Procesamiento Manual
1. Ir a `FTP Cuenta Cliente > Configuraciones FTP`
2. Seleccionar la configuración deseada
3. Hacer clic en "Procesar Archivos Ahora"

#### Procesamiento Automático
- El sistema ejecuta automáticamente cada 30 minutos (configurable)
- Revisa todas las configuraciones activas
- Descarga y procesa archivos Excel nuevos
- Mueve archivos procesados a la carpeta configurada

### Visualización de Resultados

1. **Ver archivos procesados**
   - Navegar a: `FTP Cuenta Cliente > Archivos Procesados`
   - Ver el estado, órdenes creadas y logs de procesamiento

2. **Ver órdenes creadas**
   - Navegar a: `Ventas > Órdenes`
   - Las órdenes tendrán referencia: `FTP-{hoja}-Row{número}`

## 🔧 Configuración Avanzada

### Configurar Mapeo de Columnas

1. **Crear tipo de archivo**:
   - Ir a `FTP Cuenta Cliente > Tipos de Archivo`
   - Crear nuevo tipo con código identificador (ej: "RF", "INSTALACIONES")

2. **Configurar columnas**:
   - En el tipo de archivo, ir a "Columnas"
   - Para cada columna del Excel, configurar:
     - Nombre de columna (exacto como aparece en Excel)
     - Modelo objetivo (sale.order, product.template, fsm.location)
     - Campo objetivo (vat, name, partner_id, etc.)
     - Tipo de mapeo (direct, m2o_search, etc.)

3. **Ejemplo de configuración**:
```
Columna: "rut.tecnico"
Modelo: res.partner
Campo: vat
Tipo: m2o_search
```

### Modificar Intervalo del Cron

```python
# En data/cron_data.xml
<field name="interval_number">30</field>  <!-- Cambiar este valor -->
<field name="interval_type">minutes</field>
```

## 📊 Estructura del Proyecto

```
addon-ftp/
├── addons/
│   └── ftp_cuenta_cliente/
│       ├── models/
│       │   ├── ftp_config.py          # Configuración FTP
│       │   ├── ftp_service.py         # Servicio de conexión
│       │   ├── ftp_file.py            # Modelo de archivos
│       │   ├── ftp_file_type.py       # Tipos de archivo
│       │   └── sale_order_processor.py # Procesador de órdenes
│       ├── views/                     # Vistas XML
│       ├── data/                      # Datos y cron
│       ├── security/                  # Permisos
│       └── __manifest__.py            # Metadatos del módulo
├── config/
│   └── odoo.conf                      # Configuración Odoo
├── docker-compose.yml                 # Configuración Docker
├── CHANGELOG.md                       # Historial de cambios
├── README.md                          # Este archivo
└── CLAUDE.md                          # Guía para Claude Code
```

## 🐛 Solución de Problemas

### Error: "Producto no encontrado"
- Verificar que el producto existe con el SKU correcto en `Inventario > Productos`
- El SKU debe coincidir exactamente con el campo `default_code` del producto
- **Solución**: Crear el producto manualmente antes de procesar el archivo

### Error: "No se encontró técnico/partner"
- Verificar que el técnico existe en `Field Service > Ubicaciones`
- El RUT debe coincidir con el campo `vat` del partner asociado al técnico
- **Solución**: Crear la ubicación FSM y asociarla al partner con RUT correcto

### Error: "No se encuentra el técnico"
- Verificar que existe en `Field Service > Ubicaciones`
- Debe estar asociado con un partner que tenga el nombre o RUT correcto
- **Solución**: Crear la ubicación FSM y asociarla al partner del técnico

### Error de conexión FTP
- Verificar credenciales y puerto
- Confirmar acceso de red al servidor FTP
- Para SFTP/SCP usar puerto 22

### Archivos no se procesan
- Verificar que la extensión sea .xlsx o .xls
- Confirmar que el archivo no fue procesado anteriormente
- Revisar logs en: `docker compose logs -f web`

## 📝 Logs y Depuración

### Ver logs del contenedor
```bash
docker compose logs -f web
```

### Ver logs específicos del addon
```bash
docker exec addon-ftp-web-1 grep -i "ftp\|sale.order" /var/log/odoo/odoo.log
```

### Activar modo debug en Odoo
1. Ir a Ajustes
2. Activar "Modo Desarrollador"
3. Ver más detalles en los mensajes de error

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está licenciado bajo LGPL-3 - ver el archivo LICENSE para más detalles.

## 👥 Autores

- Tu Nombre - Desarrollo inicial

## 🙏 Agradecimientos

- Comunidad Odoo
- OCA (Odoo Community Association) por los módulos Field Service