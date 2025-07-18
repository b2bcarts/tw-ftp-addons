# FTP Cuenta Cliente - Odoo 16 Addon

This project provides a Docker-based Odoo 16 environment with a custom FTP addon for automated file transfer and Excel processing.

## Project Structure

```
addon-ftp/
├── docker-compose.yml          # Docker orchestration
├── .env                        # Environment variables
├── config/
│   └── odoo.conf              # Odoo configuration
├── addons/
│   └── ftp_cuenta_cliente/    # Custom FTP addon
└── README.md                  # This file
```

## Quick Start

1. **Start the services:**
   ```bash
   docker compose up -d
   ```

2. **Access Odoo:**
   - URL: http://localhost:8069
   - Database: odoo
   - Username: admin
   - Password: admin

3. **Install the FTP addon:**
   - Go to Apps
   - Search for "FTP Cuenta Cliente"
   - Install the addon

## Services

### Odoo Web Service
- **Image:** odoo:16
- **Port:** 8069
- **Volumes:** 
  - `./addons:/mnt/extra-addons` (Custom addons)
  - `./config:/etc/odoo` (Configuration)

### PostgreSQL Database
- **Image:** postgres:15
- **Port:** 5432
- **Database:** odoo
- **User:** odoo
- **Password:** odoo

## FTP Addon Features

### Multi-Protocol Support
- **FTP**: Standard File Transfer Protocol
- **FTPS**: FTP with TLS/SSL encryption
- **SFTP**: SSH File Transfer Protocol
- **SCP**: Secure Copy Protocol over SSH

### Core Functionality
- ✅ Configurable FTP/SFTP/SCP connections via web interface
- ✅ Scheduled cron jobs for automatic file processing
- ✅ Excel file download and parsing (.xlsx, .xls)
- ✅ JSON content storage with metadata
- ✅ Automatic file organization (move processed files)
- ✅ Connection testing and status monitoring
- ✅ Detailed logging and error handling

### File Processing
- Downloads Excel files from configured FTP path (`/` by default)
- Parses Excel content using first row as JSON keys
- Stores file metadata (name, size, content) in database
- Moves processed files to designated folder (`/files_read`)

## Configuration

### Environment Variables (.env)
```env
POSTGRES_DB=odoo
POSTGRES_USER=odoo
POSTGRES_PASSWORD=odoo
```

### FTP Configuration
Access via: **FTP Cuenta Cliente > FTP Configurations**

Required fields:
- **Name**: Configuration identifier
- **Host**: FTP server address
- **Username/Password**: Authentication credentials
- **Connection Type**: FTP, FTPS, SFTP, or SCP
- **Paths**: Download and processed file paths
- **Scheduling**: Cron interval in minutes

## Usage

### 1. Create FTP Configuration
```
Menu: FTP Cuenta Cliente > FTP Configurations
- Click "Create"
- Fill in server details
- Test connection
- Save configuration
```

### 2. Manual File Processing
```
- Open FTP configuration
- Click "Process Files Now"
- Check "Processed Files" menu for results
```

### 3. View Processed Files
```
Menu: FTP Cuenta Cliente > Processed Files
- View file metadata
- Check JSON content
- Monitor processing status
```

## Technical Requirements

### Python Dependencies
- `paramiko` - SSH/SFTP connections
- `openpyxl` - Excel file processing
- `pandas` - Data manipulation

### Installation Commands
```bash
# Update addon after changes
docker exec addon-ftp-web-1 odoo -u ftp_cuenta_cliente -d odoo --stop-after-init

# Restart services
docker compose restart web
```

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Check server credentials and network access
   - Verify firewall settings
   - Test with different connection types

2. **File Processing Failures**
   - Ensure Excel files are readable
   - Check file permissions on FTP server
   - Review Odoo logs for detailed errors

3. **Database Issues**
   - Wait for PostgreSQL health check
   - Check database connection in logs

### Logs
```bash
# View Odoo logs
docker logs addon-ftp-web-1

# View database logs  
docker logs addon-ftp-db-1
```

## Development

### Adding New Features
1. Modify addon files in `addons/ftp_cuenta_cliente/`
2. Update addon: `docker exec addon-ftp-web-1 odoo -u ftp_cuenta_cliente -d odoo --stop-after-init`
3. Restart services: `docker compose restart web`

### File Structure
```
addons/ftp_cuenta_cliente/
├── __manifest__.py           # Addon manifest
├── models/
│   ├── __init__.py
│   ├── ftp_config.py        # FTP configuration
│   ├── ftp_file.py          # File processing
│   └── ftp_service.py       # Core service logic
├── views/
│   ├── ftp_config_views.xml # Configuration views
│   ├── ftp_file_views.xml   # File views
│   └── menu_views.xml       # Menu structure
├── security/
│   └── ir.model.access.csv  # Access permissions
└── data/
    └── cron_data.xml        # Scheduled jobs
```

## License

This project is licensed under LGPL-3.

## Support

For issues and feature requests, please check the addon logs and configuration settings.