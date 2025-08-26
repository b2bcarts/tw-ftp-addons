from odoo import models, fields, api
import json

class FtpFile(models.Model):
    _name = 'ftp.file'
    _description = 'FTP Processed Files'
    _order = 'create_date desc'

    name = fields.Char('File Name', required=True)
    file_size = fields.Float('File Size (KB)', digits=(10, 2))
    ftp_config_id = fields.Many2one('ftp.config', 'FTP Configuration', required=True)
    content_json = fields.Text('File Content (JSON)')
    processed_date = fields.Datetime('Processed Date', default=fields.Datetime.now)
    original_path = fields.Char('Original Path')
    moved_path = fields.Char('Moved Path')
    
    # Processing status
    status = fields.Selection([
        ('downloaded', 'Downloaded'),
        ('processed', 'Processed'),
        ('moved', 'Moved'),
        ('error', 'Error')
    ], default='downloaded')
    
    error_message = fields.Text('Error Message')
    
    # Content analysis
    row_count = fields.Integer('Number of Rows')
    column_count = fields.Integer('Number of Columns')
    sheet_names = fields.Text('Sheet Names')
    sale_orders_created = fields.Integer('Sale Orders Created', default=0)
    inventory_moves_created = fields.Integer('Inventory Moves Created', default=0)
    processing_log = fields.Text('Processing Log', help="Detailed log of each row processing with results")
    
    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} ({record.processed_date})"
    
    def get_content_as_dict(self):
        """Return file content as Python dictionary"""
        if self.content_json:
            try:
                return json.loads(self.content_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_content_from_dict(self, content_dict):
        """Store dictionary content as JSON"""
        self.content_json = json.dumps(content_dict, ensure_ascii=False, indent=2)
    
    def view_content(self):
        """Action to view file content in a popup"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Content: {self.name}',
            'res_model': 'ftp.file',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('ftp_cuenta_cliente.ftp_file_content_view').id,
            'target': 'new',
        }
    
    def reprocess_file(self):
        """Reprocess this file"""
        self.env['ftp.service'].reprocess_file(self.id)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Reprocessing',
                'message': f'File {self.name} is being reprocessed',
                'type': 'info',
            }
        }
    
    def create_mapping_wizard(self):
        """Open column mapping wizard"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Column Mapping Wizard',
            'res_model': 'ftp.mapping.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'default_ftp_file_id': self.id,
            }
        }
    
    def process_to_sale_orders(self):
        """Process this file to create sale orders"""
        processor = self.env['sale.order.processor']
        results = processor.process_ftp_file_to_sale_order(self.id)
        
        # Prepare notification message
        if results['success']:
            message = f"Processing completed successfully!\n"
            message += f"Orders created: {results['orders_created']}\n"
            
            if results['skus_not_found']:
                message += f"\nWarning: {len(results['skus_not_found'])} SKUs not found in catalog\n"
                for sku_info in results['skus_not_found'][:5]:  # Show first 5
                    message += f"- {sku_info['sku']}: {sku_info['description']}\n"
                if len(results['skus_not_found']) > 5:
                    message += f"... and {len(results['skus_not_found']) - 5} more\n"
            
            notification_type = 'warning' if results['skus_not_found'] else 'success'
        else:
            message = "Processing failed!\n"
            message += '\n'.join(results['errors'][:5])  # Show first 5 errors
            notification_type = 'danger'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sale Order Processing',
                'message': message,
                'type': notification_type,
                'sticky': True if results['errors'] or results['skus_not_found'] else False,
            }
        }