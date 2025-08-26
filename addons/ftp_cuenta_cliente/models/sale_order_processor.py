from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import json
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class SaleOrderProcessor(models.Model):
    _name = 'sale.order.processor'
    _description = 'Process FTP Files to Create Sale Orders'
    
    def process_ftp_file_to_sale_order(self, ftp_file_id):
        """
        Process an FTP file and create sale orders from its content
        Returns a dictionary with processing results
        """
        ftp_file = self.env['ftp.file'].browse(ftp_file_id)
        if not ftp_file.exists():
            raise UserError("FTP file not found")
        
        results = {
            'success': False,
            'orders_created': 0,
            'errors': [],
            'warnings': [],
            'skus_not_found': [],
            'orders': [],
            'processing_log': []
        }
        
        try:
            # Parse JSON content
            content = ftp_file.get_content_as_dict()
            if not content:
                results['errors'].append("No content found in file")
                return results
            
            # Process each sheet in the Excel file
            for sheet_name, rows in content.items():
                _logger.info(f"Processing sheet: {sheet_name} with {len(rows)} rows")
                
                # Group rows by id.mochila to create one order per mochila
                orders_data = {}
                for row in rows:
                    mochila_id = row.get('id.mochila', '')
                    if not mochila_id:
                        results['warnings'].append(f"Row without id.mochila: {row}")
                        continue
                    
                    if mochila_id not in orders_data:
                        orders_data[mochila_id] = {
                            'lines': [],
                            'data': row
                        }
                    orders_data[mochila_id]['lines'].append(row)
                
                # Create sale orders
                for mochila_id, order_info in orders_data.items():
                    try:
                        sale_order = self._create_sale_order(order_info, results)
                        if sale_order:
                            results['orders'].append({
                                'id': sale_order.id,
                                'name': sale_order.name,
                                'mochila_id': mochila_id
                            })
                            results['orders_created'] += 1
                            
                            # Log success for each row in this mochila
                            for row in order_info['lines']:
                                log_entry = f"✓ Fila procesada exitosamente - Mochila: {mochila_id} | SKU: {row.get('sku', 'N/A')} | Orden: {sale_order.name} | Cantidad: {row.get('cantidad', 1)} | Técnico: {row.get('tecnico', 'N/A')}"
                                results['processing_log'].append(log_entry)
                        else:
                            # Log failure for rows without valid products
                            for row in order_info['lines']:
                                log_entry = f"✗ Error procesando fila - Mochila: {mochila_id} | SKU: {row.get('sku', 'N/A')} | Error: No se encontraron productos válidos | Técnico: {row.get('tecnico', 'N/A')}"
                                results['processing_log'].append(log_entry)
                    except Exception as e:
                        _logger.error(f"Error creating order for mochila {mochila_id}: {str(e)}")
                        results['errors'].append(f"Error for mochila {mochila_id}: {str(e)}")
                        
                        # Log error for each row in this mochila
                        for row in order_info['lines']:
                            log_entry = f"✗ Error procesando fila - Mochila: {mochila_id} | SKU: {row.get('sku', 'N/A')} | Error: {str(e)} | Técnico: {row.get('tecnico', 'N/A')}"
                            results['processing_log'].append(log_entry)
            
            # Update FTP file with processing results
            processing_log_text = '\n'.join(results['processing_log']) if results['processing_log'] else ''
            ftp_file.write({
                'sale_orders_created': results['orders_created'],
                'status': 'processed' if results['orders_created'] > 0 else ftp_file.status,
                'error_message': '\n'.join(results['errors']) if results['errors'] else False,
                'processing_log': processing_log_text
            })
            
            # Add processing notes
            if results['skus_not_found']:
                note = f"SKUs not found in product catalog:\n"
                for sku_info in results['skus_not_found']:
                    note += f"- SKU: {sku_info['sku']} (Descripción: {sku_info['description']})\n"
                
                # Create a note in the FTP file
                existing_error = ftp_file.error_message or ''
                ftp_file.error_message = existing_error + '\n' + note if existing_error else note
            
            results['success'] = True
            
        except Exception as e:
            _logger.error(f"General error processing file: {str(e)}")
            results['errors'].append(str(e))
            ftp_file.write({
                'status': 'error',
                'error_message': str(e)
            })
        
        return results
    
    def _create_sale_order(self, order_info, results):
        """Create a single sale order from order data"""
        data = order_info['data']
        lines = order_info['lines']
        
        # Get or create partner
        partner = self._get_or_create_partner(data)
        
        # Get default warehouse for current company
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        # Prepare sale order values
        order_vals = {
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner.id,
            'date_order': fields.Datetime.now(),
            'state': 'draft',
            'client_order_ref': data.get('id.mochila', ''),
            'note': self._prepare_order_notes(data),
            'pricelist_id': 1,  # Default pricelist
            'warehouse_id': warehouse.id if warehouse else False,
            'picking_policy': 'direct',
            'order_line': []
        }
        
        # Add order lines
        for line_data in lines:
            sku = line_data.get('sku', '')
            quantity = float(line_data.get('cantidad', 1))
            
            # Search for product by default_code (SKU)
            product = self.env['product.product'].search([
                ('default_code', '=', sku)
            ], limit=1)
            
            if not product:
                # Try searching in product.template
                product_tmpl = self.env['product.template'].search([
                    ('default_code', '=', sku)
                ], limit=1)
                
                if product_tmpl:
                    # Get the first variant
                    product = product_tmpl.product_variant_ids[0] if product_tmpl.product_variant_ids else False
            
            if product:
                line_vals = {
                    'product_id': product.id,
                    'name': product.name,
                    'product_uom_qty': quantity,
                    'price_unit': product.list_price,
                    'customer_lead': 0.0,  # Required field
                }
                order_vals['order_line'].append((0, 0, line_vals))
            else:
                # SKU not found, add to warnings and detailed log
                results['skus_not_found'].append({
                    'sku': sku,
                    'description': line_data.get('descripcion', 'N/A'),
                    'quantity': quantity,
                    'mochila_id': line_data.get('id.mochila', '')
                })
                results['warnings'].append(
                    f"SKU not found: {sku} - {line_data.get('descripcion', 'N/A')} "
                    f"(Cantidad: {quantity}) for mochila {line_data.get('id.mochila', '')}"
                )
                # Add to processing log for individual row tracking
                log_entry = f"⚠ SKU no encontrado - Mochila: {line_data.get('id.mochila', 'N/A')} | SKU: {sku} | Descripción: {line_data.get('descripcion', 'N/A')} | Cantidad: {quantity} | Técnico: {line_data.get('tecnico', 'N/A')}"
                results['processing_log'].append(log_entry)
        
        # Create the sale order only if we have lines
        if order_vals['order_line']:
            sale_order = self.env['sale.order'].sudo().create(order_vals)
            _logger.info(f"Created sale order: {sale_order.name} for mochila {data.get('id.mochila', '')}")
            return sale_order
        else:
            results['warnings'].append(
                f"No valid products found for mochila {data.get('id.mochila', '')}, order not created"
            )
            return False
    
    def _get_or_create_partner(self, data):
        """Get or create a partner based on RUT"""
        rut = data.get('rut', '')
        if not rut:
            # Return a default partner or raise error
            default_partner = self.env['res.partner'].search([
                ('name', '=', 'Generic Customer')
            ], limit=1)
            
            if not default_partner:
                default_partner = self.env['res.partner'].sudo().create({
                    'name': 'Generic Customer',
                    'customer_rank': 1,
                })
            return default_partner
        
        # Search for existing partner by VAT (RUT)
        partner = self.env['res.partner'].search([
            ('vat', '=', rut)
        ], limit=1)
        
        if not partner:
            # Create new partner
            partner_name = data.get('proveedor', '') or f"Customer {rut}"
            partner = self.env['res.partner'].sudo().create({
                'name': partner_name,
                'vat': rut,
                'customer_rank': 1,
                'comment': f"Created from FTP import - Technician: {data.get('tecnico', '')}",
            })
            _logger.info(f"Created new partner: {partner.name} with RUT: {rut}")
        
        return partner
    
    def _prepare_order_notes(self, data):
        """Prepare notes for the sale order"""
        notes = []
        
        if data.get('fecha.agenda'):
            notes.append(f"Fecha Agenda: {data.get('fecha.agenda')}")
        
        if data.get('tecnico'):
            notes.append(f"Técnico: {data.get('tecnico')}")
        
        if data.get('region'):
            notes.append(f"Región: {data.get('region')}")
        
        if data.get('bodega'):
            notes.append(f"Bodega: {data.get('bodega')}")
        
        if data.get('codigo.iata'):
            notes.append(f"Código IATA: {data.get('codigo.iata')}")
        
        if data.get('comentario'):
            notes.append(f"Comentario: {data.get('comentario')}")
        
        return '\n'.join(notes) if notes else ''