# Odoo 16 Field Service & FTP Integration Platform

This project provides a Docker-based Odoo 16 environment with comprehensive Field Service Management capabilities and custom FTP automation for Excel file processing.

## Project Structure

```
addon-ftp/
├── docker-compose.yml          # Docker orchestration
├── .env                        # Environment variables
├── config/
│   └── odoo.conf              # Odoo configuration
├── addons/                    # All Odoo addons
│   ├── ftp_cuenta_cliente/    # Custom FTP addon
│   ├── fieldservice/          # Core FSM module
│   ├── fieldservice_*/        # FSM extensions (22 modules)
│   ├── extra_fields_ubicaciones/  # Stock location enhancements
│   ├── stock_picking_to_batch_group_fields/  # Batch picking
│   └── web_domain_field/      # Web UI enhancements
└── README.md                  # This file
```

## Quick Start

1. **Start the services:**
   ```bash
   docker compose up -d
   ```

2. **Fix Python dependencies (if fresh install):**
   ```bash
   docker exec addon-ftp-web-1 pip uninstall -y numpy pandas bcrypt PyNaCl
   docker exec addon-ftp-web-1 pip install numpy==1.24.3 pandas==2.0.3 bcrypt PyNaCl
   ```

3. **Access Odoo:**
   - URL: http://localhost:8069
   - Database: odoo
   - Username: admin
   - Password: admin

4. **Modules Status:**
   - ✅ 20 modules already installed and active
   - Main menus: Field Service, FTP Cuenta Cliente, Sales, Project
   - All Field Service features are operational

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

## Available Addons

### ✅ Installed Modules (20 modules active)

#### 🔧 Field Service Management Suite (18 modules)
- **fieldservice** (v16.0.1.9.0): Core FSM system ✅
- **fieldservice_account**: Invoice tracking ✅
- **fieldservice_account_analytic**: Analytic accounting ✅
- **fieldservice_activity**: Activity checklists ✅
- **fieldservice_calendar**: Calendar integration ✅
- **fieldservice_crm**: CRM integration ✅
- **fieldservice_isp_account**: ISP billing ✅
- **fieldservice_isp_flow**: ISP workflows ✅
- **fieldservice_portal**: Customer portal ✅
- **fieldservice_project**: Project integration ✅
- **fieldservice_recurring**: Recurring orders ✅
- **fieldservice_route**: Route planning ✅
- **fieldservice_sale**: Sales integration ✅
- **fieldservice_size**: Size management ✅
- **fieldservice_skill**: Skills management ✅
- **fieldservice_stage_validation**: Stage validation ✅
- **fieldservice_vehicle**: Vehicle management ✅

#### 🌐 Other Active Modules
- **web_domain_field**: Advanced filtering ✅
- **ftp_cuenta_cliente**: FTP/Excel processing ✅

### ⏳ Available but Not Installed
- **fieldservice_equipment_stock**: Equipment inventory (requires additional dependencies)
- **fieldservice_geoengine**: Geographic mapping (requires base_geoengine)
- **fieldservice_stock**: Inventory movements (requires additional stock modules)
- **fieldservice_stock_request**: Stock requests (requires stock_request modules)
- **fieldservice_timeline**: Timeline view (requires web_timeline)
- **extra_fields_ubicaciones**: Stock location fields
- **stock_picking_to_batch_group_fields**: Batch picking (requires stock_picking_batch)

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

#### Quick Install (Already Installed Modules)
```bash
# All currently installed modules (20 modules)
docker exec addon-ftp-web-1 odoo -i base_territory,fieldservice,fieldservice_account,fieldservice_account_analytic,fieldservice_activity,fieldservice_calendar,fieldservice_crm,fieldservice_isp_account,fieldservice_isp_flow,fieldservice_portal,fieldservice_project,fieldservice_recurring,fieldservice_route,fieldservice_sale,fieldservice_size,fieldservice_skill,fieldservice_stage_validation,fieldservice_vehicle,web_domain_field,ftp_cuenta_cliente -d odoo --stop-after-init
```

#### Fix Python Dependencies (if needed)
```bash
# Reinstall compatible versions
docker exec addon-ftp-web-1 pip uninstall -y numpy pandas bcrypt PyNaCl
docker exec addon-ftp-web-1 pip install numpy==1.24.3 pandas==2.0.3 bcrypt PyNaCl
```

#### Update Addons After Changes
```bash
# Update specific addon
docker exec addon-ftp-web-1 odoo -u ftp_cuenta_cliente -d odoo --stop-after-init

# Update all installed addons
docker exec addon-ftp-web-1 odoo -u all -d odoo --stop-after-init

# Restart services
docker compose restart web
```

## Troubleshooting

### Common Issues

1. **Python Import Errors (numpy/pandas)**
   ```bash
   # Fix: Reinstall with compatible versions
   docker exec addon-ftp-web-1 pip uninstall -y numpy pandas
   docker exec addon-ftp-web-1 pip install numpy==1.24.3 pandas==2.0.3
   ```

2. **Module Dependencies Missing**
   - Some modules require additional OCA addons not included
   - Check error logs for specific missing dependencies
   - Install base modules first (base_territory, fieldservice)

3. **FTP Connection Errors**
   - Check server credentials and network access
   - Verify firewall settings
   - Test with different connection types

4. **Database Issues**
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