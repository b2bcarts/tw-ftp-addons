# FTP Cuenta Cliente - Odoo 16 Addon

Advanced file transfer module with multi-protocol support for automated Excel processing in Odoo 16.

## Overview

This addon provides automated connectivity to download and process Excel files from remote servers using multiple file transfer protocols. It's designed for customer account management scenarios where Excel files need to be processed automatically on a scheduled basis.

## Features

### 🔗 Multi-Protocol Support
- **FTP**: Standard File Transfer Protocol
- **FTPS**: FTP with TLS/SSL encryption
- **SFTP**: SSH File Transfer Protocol
- **SCP**: Secure Copy Protocol over SSH

### 📊 Excel Processing
- Support for `.xlsx` and `.xls` files
- Automatic header detection (first row as JSON keys)
- Multi-sheet processing
- JSON format storage with structured data
- Metadata extraction (file size, row count, column count)

### ⏰ Automated Processing
- Configurable cron jobs for scheduled processing
- Customizable intervals (minutes)
- Manual processing triggers
- Connection status monitoring

### 📁 File Management
- Automatic file organization
- Move processed files to designated folders
- Error handling and logging
- Processing history and status tracking

### 🔐 Security & Monitoring
- Secure credential storage
- Connection testing
- Detailed logging and error reporting
- Processing status tracking

## Installation

### Prerequisites

1. **Odoo 16** environment
2. **Python dependencies**:
   ```bash
   pip install paramiko openpyxl pandas
   ```

### Installation Steps

1. **Clone or copy** the addon to your Odoo addons directory:
   ```
   addons/
   └── ftp_cuenta_cliente/
   ```

2. **Update apps list** in Odoo:
   - Go to Apps → Update Apps List

3. **Install the addon**:
   - Search for "FTP Cuenta Cliente"
   - Click Install

## Configuration

### 1. Create FTP Configuration

Navigate to **FTP Cuenta Cliente → FTP Configurations** and create a new configuration:

#### Connection Settings
- **Configuration Name**: Descriptive name for your connection
- **Connection Type**: Choose from FTP, FTPS, SFTP, or SCP
- **Host**: Server hostname or IP address
- **Port**: Server port (21 for FTP/FTPS, 22 for SFTP/SCP)
- **Username**: Authentication username
- **Password**: Authentication password
- **Use TLS/SSL**: Enable for FTPS (ignored for SFTP/SCP)

#### Path Configuration
- **Download Path**: Remote directory to download files from (default: `/`)
- **Processed Path**: Remote directory to move processed files (default: `/files_read`)

#### Scheduling
- **Interval (minutes)**: How often to check for new files (default: 30)

### 2. Test Connection

Use the **Test Connection** button to verify your configuration before enabling automatic processing.

### 3. Enable Processing

Set the configuration as **Active** to enable automatic file processing.

## Usage

### Automatic Processing

Once configured and active, the addon will:

1. **Connect** to the remote server at scheduled intervals
2. **Download** Excel files from the specified directory
3. **Process** each file and extract data with headers as JSON keys
4. **Store** the content in the database with metadata
5. **Move** processed files to the designated folder
6. **Log** all operations for monitoring

### Manual Processing

You can trigger manual processing using:
- **Process Files Now** button in the configuration form
- **Process Files Now** action in the configuration list view

### Viewing Processed Files

Navigate to **FTP Cuenta Cliente → Processed Files** to view:
- File processing history
- File content in JSON format
- Processing status and errors
- File metadata (size, rows, columns, sheets)

## JSON Data Format

The addon converts Excel files to JSON using the first row as object keys:

### Excel File Example
```
| ticket      | fecha      | monto  |
|-------------|------------|--------|
| TBK15258525 | 2025-01-15 | 150.00 |
| TBK15258526 | 2025-01-16 | 200.00 |
```

### Resulting JSON
```json
{
  "Sheet1": [
    {
      "ticket": "TBK15258525",
      "fecha": "2025-01-15",
      "monto": "150.00"
    },
    {
      "ticket": "TBK15258526",
      "fecha": "2025-01-16",
      "monto": "200.00"
    }
  ]
}
```

## Protocol-Specific Notes

### FTP/FTPS
- **Port**: Usually 21
- **Security**: FTPS provides encryption, plain FTP does not
- **Use Case**: Traditional file servers

### SFTP
- **Port**: Usually 22 (SSH)
- **Security**: Full SSH encryption
- **Use Case**: Linux/Unix servers with SSH access

### SCP
- **Port**: Usually 22 (SSH)
- **Security**: Full SSH encryption
- **Use Case**: Simple file copying over SSH
- **Limitation**: File moving not supported (files remain in original location)

## Logging and Monitoring

### Log Levels
The addon provides detailed logging for:
- **INFO**: Connection attempts, successful operations
- **WARNING**: Non-critical issues, fallback operations
- **ERROR**: Connection failures, processing errors

### Log Examples
```
INFO: === CONNECTION ATTEMPT ===
INFO: Config: My FTP Server
INFO: Host: ftp.example.com
INFO: Port: 21
INFO: Connection Type: ftp
INFO: ✓ FTP connection established to ftp.example.com:21
INFO: ✓ FTP login successful for user myuser
INFO: ✓ Connected to FTP successfully
```

### Viewing Logs
```bash
# Docker environment
docker compose logs -f web

# Direct Odoo installation
tail -f /var/log/odoo/odoo.log
```

## Error Handling

The addon handles various error scenarios:

### Connection Errors
- **DNS Resolution**: Invalid hostname
- **Connection Timeout**: Server not responding
- **Authentication**: Wrong credentials
- **Permission**: Insufficient access rights

### File Processing Errors
- **Invalid Excel Files**: Corrupted or unsupported formats
- **Empty Files**: Files with no data
- **Permission Issues**: Cannot read or move files

All errors are logged and stored in the file processing records for review.

## Troubleshooting

### Common Issues

#### "Connection Refused"
- **Cause**: Server not running or wrong port
- **Solution**: Verify server status and port configuration

#### "Authentication Failed"
- **Cause**: Wrong username/password
- **Solution**: Verify credentials and user permissions

#### "Directory Not Found"
- **Cause**: Invalid download/processed paths
- **Solution**: Verify paths exist on remote server

#### "Permission Denied"
- **Cause**: User lacks read/write permissions
- **Solution**: Grant appropriate permissions on remote server

### Debug Mode

Enable debug logging by setting log level to DEBUG in Odoo configuration:
```ini
[options]
log_level = debug
```

## Security Considerations

### Credential Storage
- Passwords are stored in Odoo database
- Use strong passwords for file transfer accounts
- Consider key-based authentication for SSH protocols

### Network Security
- Use FTPS, SFTP, or SCP for encrypted transfers
- Avoid plain FTP over public networks
- Configure firewall rules appropriately

### File Access
- Limit file transfer user permissions
- Use dedicated directories for file processing
- Regularly clean up processed files

## Development

### File Structure
```
ftp_cuenta_cliente/
├── __manifest__.py          # Addon manifest
├── __init__.py             # Module initialization
├── README.md               # This file
├── models/                 # Data models
│   ├── __init__.py
│   ├── ftp_config.py       # FTP configuration model
│   ├── ftp_file.py         # File processing model
│   └── ftp_service.py      # Core processing logic
├── views/                  # XML views
│   ├── ftp_config_views.xml
│   ├── ftp_file_views.xml
│   └── menu_views.xml
├── data/
│   └── cron_data.xml       # Scheduled job configuration
├── security/
│   └── ir.model.access.csv # Access control
└── static/
    └── description/
        └── icon.png        # Addon icon
```

### Extending the Addon

To add support for additional file formats:

1. Extend the `_process_excel_file` method in `ftp_service.py`
2. Add new file extensions to the filter logic
3. Implement format-specific processing

## Support

### Documentation
- Odoo Documentation: https://www.odoo.com/documentation/16.0/
- Python Paramiko: https://docs.paramiko.org/

### Issues
For bugs or feature requests, please contact your system administrator.

## License

This addon is licensed under LGPL-3.

## Version History

### v16.0.2.0.0
- Added multi-protocol support (FTP, FTPS, SFTP, SCP)
- Implemented JSON format with header keys
- Enhanced error handling and logging
- Added connection testing functionality

### v16.0.1.0.0
- Initial release with basic FTP support
- Excel file processing
- Scheduled automation