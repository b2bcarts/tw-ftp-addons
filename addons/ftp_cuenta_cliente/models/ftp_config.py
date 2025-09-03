# -*- coding: utf-8 -*-
"""
Modelo de Configuración FTP
Maneja las credenciales y configuraciones para conexiones FTP/SFTP/SCP.
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import ftplib
import logging

_logger = logging.getLogger(__name__)

class FtpConfig(models.Model):
    """
    Modelo para almacenar configuraciones de conexión FTP/SFTP/SCP.
    Soporta múltiples protocolos y gestiona las credenciales de acceso.
    """
    _name = 'ftp.config'
    _description = 'Configuración FTP para lectura de archivos'
    _rec_name = 'name'

    # Campos de configuración básica
    name = fields.Char(
        string='Nombre de Configuración', 
        required=True,
        help='Nombre descriptivo para identificar esta configuración FTP'
    )
    host = fields.Char(
        string='Servidor FTP', 
        required=True,
        help='Dirección IP o nombre del servidor FTP/SFTP'
    )
    port = fields.Integer(
        string='Puerto', 
        default=21,
        help='Puerto de conexión (21 para FTP, 22 para SFTP/SCP)'
    )
    username = fields.Char(
        string='Usuario', 
        required=True,
        help='Nombre de usuario para autenticación'
    )
    password = fields.Char(
        string='Contraseña', 
        required=True,
        help='Contraseña para autenticación'
    )
    active = fields.Boolean(
        string='Activo', 
        default=True,
        help='Si está activo, se procesarán archivos de esta configuración'
    )
    use_tls = fields.Boolean(
        string='Usar TLS/SSL', 
        default=False,
        help='Habilitar seguridad TLS/SSL para conexiones FTP'
    )
    # Tipo de conexión
    connection_type = fields.Selection([
        ('ftp', 'FTP'),
        ('ftps', 'FTPS (FTP con TLS)'),
        ('sftp', 'SFTP (SSH)'),
        ('scp', 'SCP (Copia Segura)')
    ], 
    string='Tipo de Conexión', 
    default='ftp', 
    required=True,
    help='Protocolo a utilizar para la conexión')
    # Rutas de procesamiento
    download_path = fields.Char(
        string='Ruta de Descarga', 
        default='/', 
        help='Ruta en el servidor FTP donde se encuentran los archivos a procesar'
    )
    processed_path = fields.Char(
        string='Ruta de Procesados', 
        default='/files_read', 
        help='Ruta donde se moverán los archivos después de procesarlos'
    )
    
    # Programación y sincronización
    cron_interval = fields.Integer(
        string='Intervalo (minutos)', 
        default=30, 
        help='Frecuencia para verificar nuevos archivos en el servidor FTP'
    )
    last_sync = fields.Datetime(
        string='Última Sincronización', 
        readonly=True,
        help='Fecha y hora de la última sincronización exitosa'
    )
    
    # Estado de conexión
    connection_status = fields.Selection([
        ('not_tested', 'No Probado'),
        ('success', 'Conectado'),
        ('failed', 'Conexión Fallida')
    ], 
    string='Estado de Conexión',
    default='not_tested', 
    readonly=True,
    help='Estado actual de la conexión FTP')
    
    
    @api.constrains('port')
    def _check_port(self):
        """
        Valida que el puerto esté en el rango válido (1-65535).
        
        :raises ValidationError: Si el puerto está fuera del rango válido
        """
        for record in self:
            if record.port <= 0 or record.port > 65535:
                raise ValidationError("El puerto debe estar entre 1 y 65535")
    
    @api.constrains('cron_interval')
    def _check_interval(self):
        """
        Valida que el intervalo de sincronización sea mayor a 0.
        
        :raises ValidationError: Si el intervalo es menor o igual a 0
        """
        for record in self:
            if record.cron_interval <= 0:
                raise ValidationError("El intervalo debe ser mayor a 0 minutos")
    
    
    def test_connection(self):
        """
        Prueba la conexión FTP/SFTP/SCP con los parámetros configurados.
        
        Intenta establecer una conexión según el tipo configurado y realiza
        operaciones básicas para verificar que las credenciales y permisos
        son correctos.
        
        :return: Acción de cliente para mostrar notificación del resultado
        :rtype: dict
        """
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
        """
        Ejecuta manualmente el procesamiento de archivos FTP.
        
        Dispara el procesamiento inmediato de archivos en el servidor FTP
        configurado, sin esperar al siguiente ciclo del cron job.
        
        :return: Acción de cliente para mostrar notificación
        :rtype: dict
        """
        for record in self:
            if record.active:
                self.env['ftp.service'].process_ftp_files(record.id)
                _logger.info(f"Procesamiento manual iniciado para: {record.name}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Procesamiento Iniciado',
                'message': 'El procesamiento de archivos FTP ha sido iniciado',
                'type': 'info',
            }
        }
    
