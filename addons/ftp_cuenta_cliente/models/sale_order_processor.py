# -*- coding: utf-8 -*-
"""
Procesador de Órdenes de Venta desde archivos FTP
Crea una orden de venta por cada fila del archivo Excel procesado.
"""

from odoo import models, fields
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class SaleOrderProcessor(models.Model):
    """
    Modelo para procesar archivos FTP y convertirlos en órdenes de venta.
    Crea una orden de venta por cada fila del archivo, validando productos y técnicos.
    """
    _name = 'sale.order.processor'
    _description = 'Procesador de Archivos FTP a Órdenes de Venta'
    
    def process_ftp_file_to_sale_order(self, ftp_file_id):
        """
        Procesa un archivo FTP y crea órdenes de venta desde su contenido.
        Crea una orden de venta por cada fila del archivo Excel.
        
        :param ftp_file_id: ID del archivo FTP a procesar
        :return: Diccionario con los resultados del procesamiento
        :rtype: dict
        """
        ftp_file = self.env['ftp.file'].browse(ftp_file_id)
        if not ftp_file.exists():
            raise UserError("Archivo FTP no encontrado")
        
        # Obtener el tipo de archivo y configuración de columnas
        self.file_type = self._get_file_type(ftp_file)
        self.column_mappings = self._get_column_mappings(self.file_type) if self.file_type else {}
        
        # Inicializar estructura de resultados
        results = {
            'success': False,
            'orders_created': 0,
            'errors': [],
            'warnings': [],
            'skus_not_found': [],
            'orders': [],
            'processing_log': [],
            'rows_processed': 0,
            'rows_skipped': 0
        }
        
        try:
            # Parsear contenido JSON del archivo
            content = ftp_file.get_content_as_dict()
            if not content:
                results['errors'].append("No se encontró contenido en el archivo")
                return results
            
            # Procesar cada hoja del archivo Excel
            for sheet_name, rows in content.items():
                _logger.info(f"Procesando hoja: {sheet_name} con {len(rows)} filas")
                results['processing_log'].append(f"=== Procesando hoja: {sheet_name} ===")
                
                # Procesar cada fila individualmente
                for row_idx, row_data in enumerate(rows, 1):
                    try:
                        # Validar que la fila tenga datos mínimos requeridos
                        if not self._validate_row_data(row_data):
                            results['rows_skipped'] += 1
                            results['warnings'].append(f"Fila {row_idx} omitida: datos incompletos")
                            results['processing_log'].append(
                                f"⚠ Fila {row_idx} omitida - Datos incompletos"
                            )
                            continue
                        
                        # Crear orden de venta para esta fila
                        sale_order = self._create_sale_order_from_row(row_data, row_idx, sheet_name, results)
                        
                        if sale_order:
                            results['orders'].append({
                                'id': sale_order.id,
                                'name': sale_order.name,
                                'row': row_idx,
                                'sheet': sheet_name
                            })
                            results['orders_created'] += 1
                            results['rows_processed'] += 1
                            
                            # Registrar éxito en el log
                            log_entry = (
                                f"✓ Fila {row_idx} procesada exitosamente | "
                                f"Orden: {sale_order.name} | "
                                f"Cliente: {sale_order.partner_id.name} | "
                                f"SKU: {row_data.get('sku', 'N/A')} | "
                                f"Técnico: {row_data.get('tecnico', 'N/A')}"
                            )
                            results['processing_log'].append(log_entry)
                            _logger.info(log_entry)
                        else:
                            results['rows_skipped'] += 1
                            
                    except Exception as e:
                        results['errors'].append(f"Error en fila {row_idx}: {str(e)}")
                        results['rows_skipped'] += 1
                        
                        # Registrar error en el log
                        log_entry = (
                            f"✗ Error procesando fila {row_idx} | "
                            f"Error: {str(e)} | "
                            f"SKU: {row_data.get('sku', 'N/A')}"
                        )
                        results['processing_log'].append(log_entry)
                        _logger.error(log_entry)
            
            # Actualizar archivo FTP con los resultados del procesamiento
            processing_log_text = '\n'.join(results['processing_log']) if results['processing_log'] else ''
            ftp_file.write({
                'sale_orders_created': results['orders_created'],
                'status': 'processed' if results['orders_created'] > 0 else 'error',
                'error_message': '\n'.join(results['errors']) if results['errors'] else False,
                'processing_log': processing_log_text
            })
            
            # Agregar resumen al log
            summary = (
                f"\n=== RESUMEN DE PROCESAMIENTO ===\n"
                f"Órdenes creadas: {results['orders_created']}\n"
                f"Filas procesadas: {results['rows_processed']}\n"
                f"Filas omitidas: {results['rows_skipped']}\n"
                f"Errores: {len(results['errors'])}\n"
                f"Advertencias: {len(results['warnings'])}"
            )
            results['processing_log'].append(summary)
            
            # Registrar SKUs no encontrados
            if results['skus_not_found']:
                self._log_missing_skus(ftp_file, results['skus_not_found'])
            
            results['success'] = results['orders_created'] > 0
            
        except Exception as e:
            _logger.error(f"Error general procesando archivo: {str(e)}")
            results['errors'].append(str(e))
            ftp_file.write({
                'status': 'error',
                'error_message': str(e)
            })
        
        return results
    
    def _validate_row_data(self, row_data):
        """
        Valida que una fila tenga los datos mínimos requeridos para procesamiento.
        
        :param row_data: Diccionario con los datos de la fila
        :return: True si la fila es válida, False en caso contrario
        :rtype: bool
        """
        # Verificar que al menos tenga SKU o descripción
        has_sku = bool(row_data.get('sku', '').strip())
        has_description = bool(row_data.get('descripcion', '').strip())
        
        return has_sku or has_description
    
    def _create_sale_order_from_row(self, row_data, row_idx, sheet_name, results):
        """
        Crea una orden de venta a partir de los datos de una fila.
        
        :param row_data: Diccionario con los datos de la fila
        :param row_idx: Índice de la fila en la hoja
        :param sheet_name: Nombre de la hoja Excel
        :param results: Diccionario de resultados para registrar warnings/errors
        :return: Orden de venta creada o False si no se pudo crear
        :rtype: sale.order or bool
        """
        try:
            # Buscar el cliente existente (no crear nuevo)
            partner = self._get_partner(row_data)
            if not partner:
                results['warnings'].append(
                    f"Fila {row_idx}: No se encontró cliente con RUT {row_data.get('rut', 'N/A')}"
                )
                return False
            
            # Buscar el técnico (fsm_location)
            fsm_location = self._get_fsm_location(row_data)
            
            # Buscar el producto por SKU
            product = self._get_product_by_sku(row_data, results)
            
            if not product:
                # Si no se encuentra el producto, crear uno genérico o saltar
                results['warnings'].append(
                    f"Fila {row_idx}: No se encontró producto con SKU {row_data.get('sku', 'N/A')}"
                )
                return False
            
            # Obtener cantidad
            quantity = self._get_quantity_from_row(row_data)
            
            # Preparar valores de la orden de venta
            order_vals = {
                'partner_id': partner.id,
                'partner_invoice_id': partner.id,
                'partner_shipping_id': partner.id,
                'date_order': fields.Datetime.now(),
                'state': 'draft',
                'client_order_ref': f"FTP-{sheet_name}-Row{row_idx}",
                'note': self._prepare_order_notes(row_data, sheet_name, row_idx),
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'name': product.name,
                    'product_uom_qty': quantity,
                    'price_unit': product.list_price,
                })]
            }
            
            # Agregar campo de ubicación FSM si existe
            if fsm_location:
                order_vals['fsm_location_id'] = fsm_location.id
            
            # Crear la orden de venta
            sale_order = self.env['sale.order'].sudo().create(order_vals)
            
            _logger.info(
                f"Orden de venta creada: {sale_order.name} | "
                f"Cliente: {partner.name} | "
                f"Producto: {product.name} | "
                f"Cantidad: {quantity}"
            )
            
            return sale_order
            
        except Exception as e:
            _logger.error(f"Error creando orden para fila {row_idx}: {str(e)}")
            raise
    
    def _get_file_type(self, ftp_file):
        """
        Identifica el tipo de archivo basándose en el nombre o contenido.
        
        :param ftp_file: Registro del archivo FTP
        :return: Registro ftp.file.type o None
        :rtype: ftp.file.type or None
        """
        # Intentar identificar por nombre de archivo
        file_type_model = self.env['ftp.file.type']
        file_type = file_type_model.identify_file_type(ftp_file.name)
        
        if file_type:
            _logger.info(f"Tipo de archivo identificado: {file_type.name}")
        else:
            _logger.warning(f"No se pudo identificar el tipo de archivo para: {ftp_file.name}")
        
        return file_type
    
    def _get_column_mappings(self, file_type):
        """
        Obtiene el mapeo de columnas configurado para el tipo de archivo.
        
        :param file_type: Registro del tipo de archivo
        :return: Diccionario con mapeos de columnas
        :rtype: dict
        """
        mappings = {}
        
        if not file_type:
            return mappings
        
        for column in file_type.column_ids:
            if column.target_model and column.target_field:
                key = f"{column.target_model}.{column.target_field}"
                mappings[key] = {
                    'column_name': column.name,
                    'technical_name': column.technical_name or column.name,
                    'data_type': column.data_type,
                    'mapping_type': column.mapping_type,
                    'is_required': column.is_required,
                    'default_value': column.default_value,
                }
                _logger.debug(f"Mapeo configurado: {key} -> {column.name}")
        
        return mappings
    
    def _get_mapped_value(self, row_data, model_name, field_name):
        """
        Obtiene el valor de una columna basándose en el mapeo configurado.
        
        :param row_data: Datos de la fila
        :param model_name: Nombre del modelo objetivo
        :param field_name: Nombre del campo objetivo
        :return: Valor mapeado o None
        :rtype: any
        """
        mapping_key = f"{model_name}.{field_name}"
        
        if mapping_key not in self.column_mappings:
            # Si no hay mapeo configurado, intentar búsqueda directa
            return None
        
        mapping = self.column_mappings[mapping_key]
        column_name = mapping['column_name']
        
        # Obtener el valor de la columna
        value = row_data.get(column_name, mapping.get('default_value'))
        
        if value and str(value).strip():
            return str(value).strip()
        
        return None
    
    def _get_partner(self, row_data):
        """
        Busca un partner (cliente) en fsm.location usando el mapeo dinámico de columnas.
        Ya NO busca en res.partner directamente, solo en fsm.location.
        Utiliza la configuración de ftp.file.type.column para buscar técnicos por RUT.
        
        :param row_data: Datos de la fila
        :return: Partner del técnico encontrado en fsm.location o None
        :rtype: res.partner or None
        """
        # Buscar FSM Location (técnico) y obtener su partner asociado
        fsm_location = self._get_fsm_location(row_data)
        
        if fsm_location and fsm_location.partner_id:
            _logger.info(f"Partner encontrado desde FSM Location: {fsm_location.partner_id.name} (Técnico: {fsm_location.name})")
            return fsm_location.partner_id
        
        # Si no hay mapeo configurado o no se encuentra fsm_location, intentar búsqueda directa
        if hasattr(self, 'column_mappings'):
            # Buscar columnas que contengan RUT del técnico según mapeo configurado
            rut_value = self._get_mapped_value(row_data, 'fsm.location', 'partner_id')
            
            # Si no hay mapeo específico, buscar en columnas comunes de RUT técnico
            if not rut_value:
                for col_name in ['rut', 'rut.tecnico', 'rut_tecnico', 'tecnico_rut', 'rut.del.tecnico']:
                    if col_name in row_data and row_data[col_name]:
                        rut_value = str(row_data[col_name]).strip()
                        break
            
            if rut_value:
                # Limpiar y formatear RUT
                rut_clean = str(rut_value).upper()
                
                # Buscar fsm.location por RUT del partner asociado
                rut_variations = [
                    rut_clean,
                    rut_clean.replace('-', ''),
                    rut_clean.replace('.', ''),
                    rut_clean.replace('-', '').replace('.', '')
                ]
                
                for rut_var in rut_variations:
                    # Buscar FSM locations cuyos partners tengan este RUT
                    fsm_locations = self.env['fsm.location'].search([
                        ('partner_id.vat', '=', rut_var)
                    ])
                    
                    if fsm_locations:
                        # Tomar la primera ubicación encontrada
                        fsm_location = fsm_locations[0]
                        _logger.info(f"Partner encontrado por RUT en FSM Location: {fsm_location.partner_id.name} (RUT: {rut_var})")
                        return fsm_location.partner_id
                
                _logger.warning(f"No se encontró FSM Location con partner que tenga RUT: {rut_value}")
            
            # Buscar por nombre del técnico
            technician_name = None
            for col_name in ['tecnico', 'nombre.tecnico', 'nombre_tecnico', 'tecnico.nombre']:
                if col_name in row_data and row_data[col_name]:
                    technician_name = str(row_data[col_name]).strip()
                    break
            
            if technician_name:
                # Buscar FSM location por nombre del partner
                fsm_locations = self.env['fsm.location'].search([
                    ('partner_id.name', 'ilike', technician_name)
                ])
                
                if fsm_locations:
                    fsm_location = fsm_locations[0]
                    _logger.info(f"Partner encontrado por nombre en FSM Location: {fsm_location.partner_id.name}")
                    return fsm_location.partner_id
                
                _logger.warning(f"No se encontró FSM Location con partner que tenga nombre: {technician_name}")
        
        else:
            # Fallback: búsqueda sin mapeo configurado
            _logger.warning("No hay mapeo de columnas configurado, buscando técnico por defecto")
            
            # Buscar RUT del técnico
            rut_tecnico = None
            for field in ['rut', 'rut.tecnico', 'rut_tecnico']:
                if field in row_data and row_data[field]:
                    rut_tecnico = str(row_data[field]).strip()
                    break
            
            if rut_tecnico:
                rut_clean = rut_tecnico.upper()
                for variation in [rut_clean, rut_clean.replace('-', ''), rut_clean.replace('.', '')]:
                    fsm_locations = self.env['fsm.location'].search([
                        ('partner_id.vat', '=', variation)
                    ])
                    if fsm_locations:
                        _logger.info(f"Partner encontrado (fallback) en FSM: {fsm_locations[0].partner_id.name}")
                        return fsm_locations[0].partner_id
            
            # Buscar por nombre del técnico
            nombre_tecnico = row_data.get('tecnico', '') or row_data.get('nombre_tecnico', '')
            if nombre_tecnico:
                fsm_locations = self.env['fsm.location'].search([
                    ('partner_id.name', 'ilike', str(nombre_tecnico).strip())
                ])
                if fsm_locations:
                    _logger.info(f"Partner encontrado por nombre (fallback) en FSM: {fsm_locations[0].partner_id.name}")
                    return fsm_locations[0].partner_id
        
        _logger.warning("No se pudo identificar el partner/técnico desde FSM Location")
        return None
    
    def _get_fsm_location(self, row_data):
        """
        Busca la ubicación FSM (técnico) usando el mapeo dinámico de columnas.
        Utiliza la configuración de ftp.file.type.column para buscar técnicos.
        
        :param row_data: Datos de la fila
        :return: fsm.location encontrado o None
        :rtype: fsm.location or None
        """
        fsm_location = None
        
        # Intentar buscar usando mapeo configurado
        if hasattr(self, 'column_mappings'):
            # Buscar mapeo directo para fsm.location
            location_id = self._get_mapped_value(row_data, 'fsm.location', 'partner_id')
            
            # Buscar RUT del técnico con mapeo o en columnas comunes
            technician_rut = None
            for col_name in ['rut.tecnico', 'rut_tecnico', 'tecnico_rut', 'rut.del.tecnico']:
                if col_name in row_data and row_data[col_name]:
                    technician_rut = str(row_data[col_name]).strip()
                    break
            
            if technician_rut:
                # Limpiar RUT
                rut_clean = technician_rut.upper()
                rut_variations = [
                    rut_clean,
                    rut_clean.replace('-', ''),
                    rut_clean.replace('.', ''),
                    rut_clean.replace('-', '').replace('.', '')
                ]
                
                # Buscar partner por RUT
                for rut_var in rut_variations:
                    partner = self.env['res.partner'].search([
                        ('vat', '=', rut_var)
                    ], limit=1)
                    
                    if partner:
                        # Buscar fsm.location asociada al partner
                        fsm_location = self.env['fsm.location'].search([
                            ('partner_id', '=', partner.id)
                        ], limit=1)
                        
                        if fsm_location:
                            _logger.info(f"FSM Location encontrada por RUT técnico: {partner.name} (RUT: {rut_var})")
                            return fsm_location
                
                _logger.warning(f"No se encontró FSM Location para técnico con RUT: {technician_rut}")
            
            # Buscar por nombre del técnico
            technician_name = None
            for col_name in ['tecnico', 'nombre.tecnico', 'nombre_tecnico', 'tecnico.nombre']:
                if col_name in row_data and row_data[col_name]:
                    technician_name = str(row_data[col_name]).strip()
                    break
            
            if technician_name:
                # Buscar partner por nombre
                partner = self.env['res.partner'].search([
                    ('name', '=', technician_name)
                ], limit=1)
                
                if not partner:
                    # Búsqueda parcial
                    partner = self.env['res.partner'].search([
                        ('name', 'ilike', technician_name)
                    ], limit=1)
                
                if partner:
                    fsm_location = self.env['fsm.location'].search([
                        ('partner_id', '=', partner.id)
                    ], limit=1)
                    
                    if fsm_location:
                        _logger.info(f"FSM Location encontrada por nombre: {technician_name}")
                        return fsm_location
                
                _logger.warning(f"No se encontró FSM Location para técnico: {technician_name}")
        
        else:
            # Fallback: búsqueda tradicional sin mapeo
            _logger.warning("No hay mapeo de columnas configurado para FSM, usando búsqueda por defecto")
            
            # Buscar técnico por nombre o RUT
            technician_name = row_data.get('tecnico', '') or row_data.get('nombre_tecnico', '')
            technician_rut = row_data.get('rut_tecnico', '') or row_data.get('rut.tecnico', '')
            
            if technician_rut:
                partner = self.env['res.partner'].search([
                    ('vat', '=', str(technician_rut).strip())
                ], limit=1)
                
                if partner:
                    fsm_location = self.env['fsm.location'].search([
                        ('partner_id', '=', partner.id)
                    ], limit=1)
                    
                    if fsm_location:
                        return fsm_location
            
            if technician_name:
                partner = self.env['res.partner'].search([
                    ('name', 'ilike', str(technician_name).strip())
                ], limit=1)
                
                if partner:
                    fsm_location = self.env['fsm.location'].search([
                        ('partner_id', '=', partner.id)
                    ], limit=1)
                    
                    if fsm_location:
                        return fsm_location
        
        return None
    
    def _get_product_by_sku(self, row_data, results):
        """
        Busca un producto por SKU (default_code).
        
        :param row_data: Datos de la fila
        :param results: Diccionario de resultados para registrar SKUs no encontrados
        :return: Producto encontrado o None
        :rtype: product.product or None
        """
        sku = row_data.get('sku', '') or row_data.get('codigo', '') or row_data.get('codigo_producto', '')
        
        if not sku or not str(sku).strip():
            return None
        
        sku = str(sku).strip()
        
        # Buscar producto por default_code
        product = self.env['product.product'].search([
            ('default_code', '=', sku)
        ], limit=1)
        
        if not product:
            # Intentar buscar en product.template
            product_tmpl = self.env['product.template'].search([
                ('default_code', '=', sku)
            ], limit=1)
            
            if product_tmpl and product_tmpl.product_variant_ids:
                product = product_tmpl.product_variant_ids[0]
        
        if not product:
            # Registrar SKU no encontrado
            results['skus_not_found'].append({
                'sku': sku,
                'description': row_data.get('descripcion', 'Sin descripción'),
                'quantity': row_data.get('cantidad', 1)
            })
            _logger.warning(f"Producto no encontrado con SKU: {sku}")
        
        return product
    
    def _get_quantity_from_row(self, row_data):
        """
        Extrae la cantidad de la fila, con valor por defecto 1.
        
        :param row_data: Datos de la fila
        :return: Cantidad a ordenar
        :rtype: float
        """
        # Buscar cantidad en diferentes posibles campos
        quantity_fields = ['cantidad', 'qty', 'quantity', 'cant', 'unidades']
        
        for field in quantity_fields:
            if field in row_data and row_data[field]:
                try:
                    qty = float(row_data[field])
                    if qty > 0:
                        return qty
                except (ValueError, TypeError):
                    continue
        
        # Si no se encuentra cantidad válida, retornar 1
        return 1.0
    
    def _prepare_order_notes(self, row_data, sheet_name, row_idx):
        """
        Prepara las notas para la orden de venta con toda la información relevante.
        
        :param row_data: Datos de la fila
        :param sheet_name: Nombre de la hoja
        :param row_idx: Índice de la fila
        :return: Texto de notas formateado
        :rtype: str
        """
        notes = []
        notes.append(f"=== Importado desde FTP ===")
        notes.append(f"Hoja: {sheet_name} | Fila: {row_idx}")
        notes.append("")
        
        # Agregar información del técnico
        if row_data.get('tecnico'):
            notes.append(f"Técnico asignado: {row_data.get('tecnico')}")
        
        # Agregar fecha de agenda si existe
        if row_data.get('fecha_agenda') or row_data.get('fecha.agenda'):
            fecha = row_data.get('fecha_agenda') or row_data.get('fecha.agenda')
            notes.append(f"Fecha programada: {fecha}")
        
        # Agregar región si existe
        if row_data.get('region'):
            notes.append(f"Región: {row_data.get('region')}")
        
        # Agregar tipo de solicitud si existe
        if row_data.get('tipo_solicitud') or row_data.get('tipo.solicitud'):
            tipo = row_data.get('tipo_solicitud') or row_data.get('tipo.solicitud')
            notes.append(f"Tipo de solicitud: {tipo}")
        
        # Agregar observaciones si existen
        if row_data.get('observacion') or row_data.get('observaciones'):
            obs = row_data.get('observacion') or row_data.get('observaciones')
            notes.append(f"Observaciones: {obs}")
        
        # Agregar ID mochila si existe
        if row_data.get('id.mochila') or row_data.get('id_mochila'):
            mochila = row_data.get('id.mochila') or row_data.get('id_mochila')
            notes.append(f"ID Mochila: {mochila}")
        
        return '\n'.join(notes)
    
    def _log_missing_skus(self, ftp_file, missing_skus):
        """
        Registra los SKUs no encontrados en el archivo FTP.
        
        :param ftp_file: Registro del archivo FTP
        :param missing_skus: Lista de SKUs no encontrados
        """
        if not missing_skus:
            return
        
        note = "=== SKUs NO ENCONTRADOS EN EL CATÁLOGO ===\n"
        for sku_info in missing_skus:
            note += (
                f"- SKU: {sku_info['sku']} | "
                f"Descripción: {sku_info.get('description', 'N/A')} | "
                f"Cantidad: {sku_info.get('quantity', 1)}\n"
            )
        
        # Agregar a los mensajes de error del archivo
        existing_error = ftp_file.error_message or ''
        ftp_file.error_message = existing_error + '\n\n' + note if existing_error else note