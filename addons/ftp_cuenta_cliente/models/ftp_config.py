from odoo import models, fields, api
from odoo.exceptions import ValidationError
import ftplib

class FtpConfig(models.Model):
    _name = 'ftp.config'
    _description = 'FTP Configuration'
    _rec_name = 'name'

    name = fields.Char('Configuration Name', required=True)
    host = fields.Char('FTP Host', required=True)
    port = fields.Integer('FTP Port', default=21)
    username = fields.Char('Username', required=True)
    password = fields.Char('Password', required=True)
    active = fields.Boolean('Active', default=True)
    use_tls = fields.Boolean('Use TLS/SSL', default=False)
    connection_type = fields.Selection([
        ('ftp', 'FTP'),
        ('ftps', 'FTPS (FTP with TLS)'),
        ('sftp', 'SFTP (SSH)'),
        ('scp', 'SCP (Secure Copy)')
    ], string='Connection Type', default='ftp', required=True)
    download_path = fields.Char('Download Path', default='/', help='FTP path to download files from')
    processed_path = fields.Char('Processed Path', default='/files_read', help='FTP path to move processed files')
    
    # Scheduling
    cron_interval = fields.Integer('Interval (minutes)', default=30, help='How often to check for new files')
    last_sync = fields.Datetime('Last Sync', readonly=True)
    
    # Status
    connection_status = fields.Selection([
        ('not_tested', 'Not Tested'),
        ('success', 'Connected'),
        ('failed', 'Connection Failed')
    ], default='not_tested', readonly=True)
    
    
    @api.constrains('port')
    def _check_port(self):
        for record in self:
            if record.port <= 0 or record.port > 65535:
                raise ValidationError("Port must be between 1 and 65535")
    
    @api.constrains('cron_interval')
    def _check_interval(self):
        for record in self:
            if record.cron_interval <= 0:
                raise ValidationError("Interval must be greater than 0")
    
    
    def test_connection(self):
        """Test FTP/SFTP connection"""
        import logging
        import paramiko
        _logger = logging.getLogger(__name__)
        
        for record in self:
            try:
                if record.connection_type in ['sftp', 'scp']:
                    _logger.info(f"Try to connect {record.connection_type.upper()} to {record.host}:{record.port} with user {record.username}")
                    
                    # Create SSH client
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    
                    # Connect via SSH
                    ssh.connect(
                        hostname=record.host,
                        port=record.port,
                        username=record.username,
                        password=record.password,
                        timeout=30
                    )
                    _logger.info(f"SSH connection established to {record.host}")
                    
                    if record.connection_type == 'sftp':
                        # Create SFTP client
                        sftp = ssh.open_sftp()
                        _logger.info(f"SFTP session opened for user {record.username}")
                        
                        # Test basic operations
                        try:
                            current_dir = sftp.getcwd() or '/'
                            _logger.info(f"Current SFTP directory: {current_dir}")
                        except:
                            pass
                        
                        sftp.close()
                        ssh.close()
                        _logger.info("Connected to SFTP successfully")
                        record.connection_status = 'success'
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': 'Success',
                                'message': 'SFTP connection successful!',
                                'type': 'success',
                            }
                        }
                    
                    elif record.connection_type == 'scp':
                        # For SCP, we test with a simple command execution
                        stdin, stdout, stderr = ssh.exec_command('pwd')
                        result = stdout.read().decode().strip()
                        _logger.info(f"SCP test command successful: pwd returned {result}")
                        
                        # Test if we can list files in the download path
                        try:
                            stdin, stdout, stderr = ssh.exec_command(f'ls -la {record.download_path}')
                            result = stdout.read().decode().strip()
                            _logger.info(f"SCP directory listing successful for {record.download_path}")
                        except Exception as e:
                            _logger.warning(f"SCP directory listing failed: {str(e)}")
                        
                        ssh.close()
                        _logger.info("Connected to SCP successfully")
                        record.connection_status = 'success'
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': 'Success',
                                'message': 'SCP connection successful!',
                                'type': 'success',
                            }
                        }
                else:
                    # FTP/FTPS connection
                    _logger.info(f"Try to connect FTP to {record.host}:{record.port} with user {record.username}")
                    
                    if record.connection_type == 'ftps' or record.use_tls:
                        ftp = ftplib.FTP_TLS()
                    else:
                        ftp = ftplib.FTP()
                    
                    ftp.connect(record.host, record.port)
                    _logger.info(f"FTP connection established to {record.host}")
                    
                    ftp.login(record.username, record.password)
                    _logger.info(f"FTP login successful for user {record.username}")
                    
                    if record.connection_type == 'ftps' or record.use_tls:
                        ftp.prot_p()
                        _logger.info("FTP TLS protection enabled")
                    
                    ftp.quit()
                    _logger.info("Connected to FTP successfully")
                    record.connection_status = 'success'
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': 'Success',
                            'message': 'FTP connection successful!',
                            'type': 'success',
                        }
                    }
            except Exception as e:
                _logger.error(f"Connection failed to {record.host}: {str(e)}")
                record.connection_status = 'failed'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Connection Error',
                        'message': f'Failed to connect: {str(e)}',
                        'type': 'danger',
                    }
                }
    
    def process_files_now(self):
        """Manual trigger for file processing"""
        for record in self:
            if record.active:
                self.env['ftp.service'].process_ftp_files(record.id)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Processing Started',
                'message': 'FTP file processing has been triggered',
                'type': 'info',
            }
        }
    
