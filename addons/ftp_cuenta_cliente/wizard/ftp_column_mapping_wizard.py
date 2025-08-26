from odoo import models, fields, api
from odoo.exceptions import UserError

class FtpColumnMappingWizard(models.TransientModel):
    _name = 'ftp.column.mapping.wizard'
    _description = 'FTP Column Mapping Wizard'
    
    file_type_id = fields.Many2one('ftp.file.type', string='File Type', required=True, readonly=True)
    
    # Target model selection
    target_model = fields.Selection([
        ('sale.order', 'Sale Order'),
        ('product.template', 'Product Template'),
        ('fsm.location', 'Field Service Location'),
    ], string='Target Model', required=True, default='sale.order')
    
    mapping_line_ids = fields.One2many('ftp.column.mapping.wizard.line', 'wizard_id', string='Column Mappings')
    
    @api.onchange('file_type_id', 'target_model')
    def _onchange_file_type_target(self):
        """Load columns and available fields when file type or target model changes"""
        if self.file_type_id and self.target_model:
            lines = []
            columns = self.env['ftp.file.type.column'].search([
                ('file_type_id', '=', self.file_type_id.id)
            ], order='sequence')
            
            for column in columns:
                # Get current mapping if exists
                current_field = self._get_current_mapping(column, self.target_model)
                
                lines.append((0, 0, {
                    'column_id': column.id,
                    'column_name': column.name,
                    'column_description': column.description,
                    'data_type': column.data_type,
                    'is_required': column.is_required,
                    'target_field_name': current_field,
                }))
            
            self.mapping_line_ids = lines
    
    def _get_current_mapping(self, column, target_model):
        """Get the current mapping for a column to a specific model"""
        # This will be extended based on your mapping storage strategy
        if target_model == 'sale.order':
            mapping = {
                'partner_vat': 'partner_id',
                'order_ref': 'client_order_ref',
                'date_order': 'date_order',
                'note': 'note',
            }
            return mapping.get(column.sale_order_field, False)
        return False
    
    def action_save_mapping(self):
        """Save the column mappings"""
        self.ensure_one()
        
        for line in self.mapping_line_ids:
            if line.target_field_name:
                # Update the column with the mapping
                column = line.column_id
                
                # Store mapping based on target model
                if self.target_model == 'sale.order':
                    column.sale_order_field_technical = line.target_field_name
                elif self.target_model == 'product.template':
                    column.product_field_technical = line.target_field_name
                elif self.target_model == 'fsm.location':
                    column.fsm_location_field_technical = line.target_field_name
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Column mappings saved for {self.file_type_id.name}',
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_auto_detect(self):
        """Try to auto-detect mappings based on column names"""
        self.ensure_one()
        
        # Common mapping patterns
        auto_mappings = {
            'sale.order': {
                'rut': 'partner_id',
                'fecha': 'date_order',
                'fecha_agenda': 'date_order',
                'fecha_agendada': 'date_order',
                'ticket': 'client_order_ref',
                'id_mochila': 'client_order_ref',
                'comentario': 'note',
                'observacion': 'note',
                'tecnico': 'user_id',
            },
            'product.template': {
                'sku': 'default_code',
                'codigo': 'default_code',
                'descripcion': 'name',
                'tipo_equipo': 'categ_id',
            },
            'fsm.location': {
                'ubicacion': 'name',
                'direccion': 'street',
                'comuna': 'city',
                'region': 'state_id',
                'cod_comercio': 'ref',
                'nombre_fantasia': 'name',
            }
        }
        
        mappings = auto_mappings.get(self.target_model, {})
        
        for line in self.mapping_line_ids:
            # Try to match by technical name
            technical_name = line.column_id.technical_name or line.column_name.lower().replace('.', '_')
            
            for pattern, field in mappings.items():
                if pattern in technical_name:
                    # Verify field exists in model
                    if self._field_exists(self.target_model, field):
                        line.target_field_name = field
                        break
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Auto-detection Complete',
                'message': 'Auto-detection completed. Please review and adjust mappings as needed.',
                'type': 'info',
                'sticky': False,
            }
        }
    
    def _field_exists(self, model_name, field_name):
        """Check if a field exists in the given model"""
        try:
            model = self.env[model_name]
            return field_name in model._fields
        except:
            return False
    
    def action_clear_mappings(self):
        """Clear all mappings"""
        self.ensure_one()
        for line in self.mapping_line_ids:
            line.target_field_name = False
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Cleared',
                'message': 'All mappings have been cleared.',
                'type': 'warning',
                'sticky': False,
            }
        }


class FtpColumnMappingWizardLine(models.TransientModel):
    _name = 'ftp.column.mapping.wizard.line'
    _description = 'FTP Column Mapping Wizard Line'
    
    wizard_id = fields.Many2one('ftp.column.mapping.wizard', string='Wizard', required=True, ondelete='cascade')
    column_id = fields.Many2one('ftp.file.type.column', string='Column', required=True, readonly=True)
    
    # Column info (readonly)
    column_name = fields.Char('Column Name', readonly=True)
    column_description = fields.Text('Description', readonly=True)
    data_type = fields.Selection([
        ('char', 'Text'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
        ('boolean', 'Boolean'),
    ], string='Data Type', readonly=True)
    is_required = fields.Boolean('Required', readonly=True)
    
    # Mapping configuration
    target_field_name = fields.Char('Target Field', help="Technical name of the target field")
    target_field_selection = fields.Selection('_get_target_field_selection', string='Select Target Field')
    field_type = fields.Char('Field Type', compute='_compute_field_info')
    field_help = fields.Text('Field Help', compute='_compute_field_info')
    is_compatible = fields.Boolean('Compatible', compute='_compute_field_info')
    
    def _get_target_field_selection(self):
        """Return field selection based on target model"""
        if not self.wizard_id or not self.wizard_id.target_model:
            return []
        
        try:
            model = self.env[self.wizard_id.target_model]
            field_selection = []
            
            # Get all stored fields of the model
            for field_name, field in model._fields.items():
                if not field_name.startswith('_') and field.store and not field.related:
                    field_selection.append((field_name, f"{field.string} ({field_name})"))
            
            # Sort by label
            field_selection.sort(key=lambda x: x[1])
            return field_selection
        except:
            return []
    
    @api.depends('wizard_id.target_model', 'target_field_name')
    def _compute_field_info(self):
        """Compute field information for validation"""
        for record in self:
            if record.wizard_id.target_model and record.target_field_name:
                try:
                    model = self.env[record.wizard_id.target_model]
                    if record.target_field_name in model._fields:
                        field = model._fields[record.target_field_name]
                        record.field_type = field.type
                        record.field_help = field.help or field.string
                        
                        # Check compatibility
                        compatible_types = {
                            'char': ['char', 'text', 'html', 'selection'],
                            'integer': ['integer', 'many2one'],
                            'float': ['float', 'monetary'],
                            'date': ['date'],
                            'datetime': ['datetime'],
                            'boolean': ['boolean'],
                        }
                        
                        column_type = record.data_type
                        field_type = field.type
                        
                        record.is_compatible = field_type in compatible_types.get(column_type, [column_type])
                    else:
                        record.field_type = 'Not Found'
                        record.field_help = 'Field not found in model'
                        record.is_compatible = False
                except:
                    record.field_type = 'Error'
                    record.field_help = 'Error accessing model'
                    record.is_compatible = False
            else:
                record.field_type = False
                record.field_help = False
                record.is_compatible = True
    
    
    @api.onchange('target_field_selection')
    def _onchange_target_field_selection(self):
        """Update target field name when selection changes"""
        if self.target_field_selection:
            self.target_field_name = self.target_field_selection