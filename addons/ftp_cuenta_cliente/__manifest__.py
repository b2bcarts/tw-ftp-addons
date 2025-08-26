{
    'name': 'FTP Cuenta Cliente',
    'version': '16.0.2.0.0',
    'category': 'Tools',
    'license': 'LGPL-3',
    'summary': 'Automated file transfer and Excel processing for customer accounts',
    'description': """
        Advanced file transfer module with multi-protocol support for automated Excel processing.
        
        Key Features:
        =============
        • Multi-protocol support: FTP, FTPS, SFTP, and SCP
        • Configurable credentials via Odoo frontend
        • Scheduled cron jobs for automatic file processing
        • Excel file download and parsing (.xlsx, .xls)
        • JSON content storage with metadata
        • Automatic file organization (move processed files)
        • Detailed logging and error handling
        • Connection testing and status monitoring
        
        Supported Protocols:
        ===================
        • FTP: Standard File Transfer Protocol
        • FTPS: FTP with TLS/SSL encryption
        • SFTP: SSH File Transfer Protocol  
        • SCP: Secure Copy Protocol over SSH
        
        Technical Requirements:
        ======================
        • Python libraries: paramiko, openpyxl, pandas
        • Network access to target servers
        • Appropriate user permissions on remote servers
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'sale', 'fieldservice'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron_data.xml',
        'views/ftp_config_views.xml',
        'views/ftp_file_views.xml',
        'views/ftp_file_type_views.xml',
        'wizard/ftp_column_mapping_wizard_views.xml',
        'views/menu_views.xml',
        'data/ftp_file_type_data.xml',
    ],
    'external_dependencies': {
        'python': ['paramiko', 'openpyxl', 'pandas'],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 0.00,
    'currency': 'USD',
}