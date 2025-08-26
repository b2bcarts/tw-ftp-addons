from odoo import models, fields, api

class FtpFileType(models.Model):
    _name = 'ftp.file.type'
    _description = 'FTP File Type Configuration'
    _rec_name = 'name'
    _order = 'sequence, name'
    
    name = fields.Char('Type Name', required=True, help="Name of the file type (e.g., 'Instalaciones', 'RF')")
    code = fields.Char('Type Code', required=True, help="Short code identifier for the file type")
    description = fields.Text('Description', help="Detailed description of this file type and its purpose")
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10, help="Sequence order when listing file types")
    
    # Configuration fields
    file_extension = fields.Selection([
        ('xlsx', 'Excel (XLSX)'),
        ('xls', 'Excel (XLS)'),
        ('csv', 'CSV'),
        ('txt', 'Text File'),
        ('xml', 'XML'),
    ], string='Expected Extension', default='xlsx', required=True)
    
    delimiter = fields.Char('CSV Delimiter', default=',', help="Delimiter for CSV files")
    encoding = fields.Selection([
        ('utf-8', 'UTF-8'),
        ('latin-1', 'Latin-1'),
        ('iso-8859-1', 'ISO-8859-1'),
    ], string='File Encoding', default='utf-8')
    
    # Processing configuration
    create_sale_orders = fields.Boolean('Create Sale Orders', default=False, 
        help="If enabled, this file type will be processed to create sale orders")
    group_by_field = fields.Char('Group By Field', 
        help="Field name to group records for sale order creation (e.g., 'id.mochila')")
    
    # Related fields
    column_ids = fields.One2many('ftp.file.type.column', 'file_type_id', string='Columns')
    column_count = fields.Integer('Column Count', compute='_compute_column_count')
    
    # Sample data
    sample_file_path = fields.Char('Sample File Path', help="Path to a sample file for this type")
    sample_data = fields.Text('Sample Data', help="JSON representation of sample data")
    
    @api.depends('column_ids')
    def _compute_column_count(self):
        for record in self:
            record.column_count = len(record.column_ids)
    
    def action_view_columns(self):
        """Open columns configuration"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Columns for {self.name}',
            'res_model': 'ftp.file.type.column',
            'view_mode': 'tree,form',
            'domain': [('file_type_id', '=', self.id)],
            'context': {'default_file_type_id': self.id},
        }
    
    def action_open_column_mapping(self):
        """Open column mapping view for manual configuration"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Column Mapping for {self.name}',
            'res_model': 'ftp.file.type.column',
            'view_mode': 'tree,form',
            'view_id': self.env.ref('ftp_cuenta_cliente.view_ftp_file_type_column_mapping_tree').id,
            'domain': [('file_type_id', '=', self.id)],
            'context': {
                'default_file_type_id': self.id,
                'create': True,
                'edit': True,
            },
        }
    
    def action_manual_mapping_setup(self):
        """Setup manual mapping for all columns"""
        self.ensure_one()
        # Reset all auto-detected mappings to manual
        for column in self.column_ids:
            if not column.target_model:
                column.write({
                    'target_model': 'sale.order',  # Default to sale orders
                    'target_field': False,
                })
        return self.action_open_column_mapping()
    
    @api.model
    def identify_file_type(self, filename, headers=None):
        """
        Try to identify the file type based on filename or headers
        Returns the file type record or False
        """
        # First try by filename pattern
        for file_type in self.search([('active', '=', True)]):
            if file_type.code.lower() in filename.lower():
                return file_type
        
        # If headers provided, try to match by column structure
        if headers:
            for file_type in self.search([('active', '=', True)]):
                expected_columns = file_type.column_ids.filtered('is_required').mapped('name')
                if all(col in headers for col in expected_columns):
                    return file_type
        
        return False


class FtpFileTypeColumn(models.Model):
    _name = 'ftp.file.type.column'
    _description = 'FTP File Type Column Definition'
    _order = 'sequence, name'
    
    file_type_id = fields.Many2one('ftp.file.type', string='File Type', required=True, ondelete='cascade')
    name = fields.Char('Column Name', required=True, help="Exact column name as it appears in the file")
    technical_name = fields.Char('Technical Name', help="Internal field name for processing")
    description = fields.Text('Description', help="Description of what this column contains")
    sequence = fields.Integer('Sequence', default=10, help="Column order in the file")
    
    # Data type configuration
    data_type = fields.Selection([
        ('char', 'Text'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
        ('boolean', 'Boolean'),
    ], string='Data Type', default='char', required=True)
    
    # Validation
    is_required = fields.Boolean('Required', default=False, help="Is this column required for processing?")
    is_key = fields.Boolean('Is Key Field', default=False, help="Is this a key field for grouping or identification?")
    
    # Target model selection
    target_model = fields.Selection([
        ('sale.order', 'Sale Order'),
        ('product.template', 'Product Template'), 
        ('fsm.location', 'FSM Location'),
    ], string='Target Model', help="Select which model this column should map to")
    
    # Dynamic field selection based on target model
    target_field = fields.Char('Target Field', help="Field name in the target model")
    
    # Mapping configuration for different models
    sale_order_field = fields.Selection([
        ('partner_vat', 'Customer VAT (RUT)'),
        ('partner_name', 'Customer Name'),
        ('order_ref', 'Order Reference'),
        ('note', 'Order Notes'),
        ('product_sku', 'Product SKU'),
        ('product_qty', 'Product Quantity'),
        ('date_order', 'Order Date'),
        ('custom', 'Custom Field'),
        ('ignore', 'Ignore'),
    ], string='Sale Order Mapping', default='ignore', 
        help="How this column maps to sale order fields")
    
    # Technical field mappings for different models
    sale_order_field_technical = fields.Selection('_get_sale_order_fields', 
        string='Sale Order Field', help="Technical field name in sale.order model")
    product_field_technical = fields.Selection('_get_product_fields',
        string='Product Field', help="Technical field name in product.template model")
    fsm_location_field_technical = fields.Selection('_get_fsm_location_fields',
        string='FSM Location Field', help="Technical field name in fsm.location model")
    
    # Keep these for backwards compatibility
    partner_field_technical = fields.Char('Partner Field', 
        help="Technical field name in res.partner model")
    fsm_person_field_technical = fields.Char('FSM Person Field', 
        help="Technical field name in fsm.person model")
    order_line_field_technical = fields.Char('Order Line Field', 
        help="Technical field name in sale.order.line model")
    
    # Mapping type and configuration
    mapping_type = fields.Selection([
        ('direct', 'Direct Mapping'),
        ('m2o_create', 'Many2One - Create if not exists'),
        ('m2o_search', 'Many2One - Search only'),
        ('concatenate', 'Concatenate to field'),
        ('compute', 'Compute/Transform'),
        ('ignore', 'Ignore'),
    ], string='Mapping Type', default='direct',
        help="How to process this field during import")
    
    transformation_code = fields.Text('Transformation Code', 
        help="Python code to transform the value (for compute type)")
    search_domain = fields.Text('Search Domain', 
        help="Domain to search for Many2One fields (as Python expression)")
    
    custom_mapping = fields.Text('Custom Mapping Logic', 
        help="Python code for custom field mapping (advanced)")
    
    # Format configuration
    date_format = fields.Char('Date Format', default='%d-%m-%Y', 
        help="Date format for parsing date fields (e.g., %d-%m-%Y)")
    default_value = fields.Char('Default Value', help="Default value if column is empty")
    
    # Examples
    example_values = fields.Text('Example Values', help="Example values from sample files")
    
    _sql_constraints = [
        ('unique_column_per_type', 'UNIQUE(file_type_id, name)', 
         'Column name must be unique per file type!'),
    ]
    
    @api.onchange('name')
    def _onchange_name(self):
        if self.name and not self.technical_name:
            # Convert column name to technical name (replace dots and spaces with underscores)
            self.technical_name = self.name.lower().replace('.', '_').replace(' ', '_')
    
    @api.model
    def get_model_fields(self, model_name):
        """Get available fields for a model"""
        if not model_name:
            return []
        
        try:
            model = self.env[model_name]
            fields_info = model.fields_get()
            return [(name, field_info['string']) for name, field_info in fields_info.items() 
                   if not field_info.get('readonly', False) or name in ['id', 'name']]
        except Exception:
            return []
    
    def get_target_field_options(self):
        """Get field options for the selected target model"""
        self.ensure_one()
        if not self.target_model:
            return []
        return self.get_model_fields(self.target_model)
    
    @api.model
    def _get_sale_order_fields(self):
        """Get selection list of sale order fields"""
        try:
            sale_order_fields = self.env['sale.order'].fields_get()
            common_fields = [
                ('name', 'Order Reference'),
                ('partner_id', 'Customer'),
                ('date_order', 'Order Date'),
                ('amount_total', 'Total Amount'),
                ('state', 'Status'),
                ('client_order_ref', 'Customer Reference'),
                ('note', 'Terms and Conditions'),
                ('user_id', 'Salesperson'),
                ('team_id', 'Sales Team'),
                ('company_id', 'Company'),
            ]
            # Add only existing fields
            result = []
            for field_name, field_label in common_fields:
                if field_name in sale_order_fields:
                    result.append((field_name, field_label))
            return result
        except Exception:
            return [('name', 'Order Reference')]
    
    @api.model
    def _get_product_fields(self):
        """Get selection list of product template fields"""
        try:
            product_fields = self.env['product.template'].fields_get()
            common_fields = [
                ('name', 'Product Name'),
                ('default_code', 'Internal Reference'),
                ('list_price', 'Sales Price'),
                ('standard_price', 'Cost Price'),
                ('categ_id', 'Product Category'),
                ('uom_id', 'Unit of Measure'),
                ('type', 'Product Type'),
                ('active', 'Active'),
                ('description', 'Description'),
                ('barcode', 'Barcode'),
            ]
            result = []
            for field_name, field_label in common_fields:
                if field_name in product_fields:
                    result.append((field_name, field_label))
            return result
        except Exception:
            return [('name', 'Product Name')]
    
    @api.model
    def _get_fsm_location_fields(self):
        """Get selection list of FSM location fields"""
        try:
            fsm_fields = self.env['fsm.location'].fields_get()
            common_fields = [
                ('name', 'Location Name'),
                ('partner_id', 'Contact'),
                ('owner_id', 'Location Owner'),
                ('street', 'Street'),
                ('city', 'City'),
                ('state_id', 'State'),
                ('zip', 'ZIP Code'),
                ('country_id', 'Country'),
                ('phone', 'Phone'),
                ('email', 'Email'),
                ('ref', 'Reference'),
                ('active', 'Active'),
            ]
            result = []
            for field_name, field_label in common_fields:
                if field_name in fsm_fields:
                    result.append((field_name, field_label))
            return result
        except Exception:
            return [('name', 'Location Name')]