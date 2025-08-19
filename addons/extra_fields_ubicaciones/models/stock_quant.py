from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'
    
    expiration_date = fields.Datetime(
        string='Fecha de Expiración',
        related='lot_id.expiration_date',
        store=True,
        help="La fecha de expiración del lote/número de serie"
    )
    
    default_code = fields.Char(
        string='Referencia Interna',
        related='product_id.default_code',
        store=True,
        help="Referencia interna del producto"
    )
    
    location_name = fields.Char(
        string='Nombre de Ubicación',
        related='location_id.name',
        store=True,
        help="Nombre de la ubicación"
    )
    
    product_name = fields.Char(
        string='Nombre de Producto',
        related='product_id.name',
        store=True,
        help="Nombre del producto"
    )