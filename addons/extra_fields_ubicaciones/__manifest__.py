{
    'name': 'Extra Fields Ubicaciones',
    'version': '1.0',
    'summary': 'Añadir fecha de expiración al informe de ubicaciones de inventario',
    'description': """
        Este módulo añade el campo fecha de expiración al informe de ubicaciones de inventario.
        La fecha de expiración se obtiene desde la relación lot_id con stock.lot.
    """,
    'category': 'Inventory',
    'author': 'Tu Nombre',
    'depends': ['stock'],
    'data': [
        'views/stock_quant_views.xml',
        'reports/report_stockinventory.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}