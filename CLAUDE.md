# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is an Odoo 16 Field Service Management platform with FTP integration using Docker Compose. The project provides a comprehensive suite of Field Service Management modules along with custom FTP/SFTP/SCP file transfer capabilities for automated Excel processing.

## Development Commands

### Starting the Environment
```bash
# Start services (database must be healthy before web starts)
docker compose up -d

# View logs
docker compose logs -f web
docker compose logs -f db
```

### Database Initialization (First Run Only)
```bash
# Initialize Odoo with base modules
docker exec -it addon-ftp-web-1 odoo -i base -d odoo --stop-after-init
```

### Addon Management

#### Currently Installed Modules (20 total)
```bash
# Core modules
base_territory, fieldservice

# Field Service Extensions (16 modules)
fieldservice_account, fieldservice_account_analytic, fieldservice_activity,
fieldservice_calendar, fieldservice_crm, fieldservice_isp_account,
fieldservice_isp_flow, fieldservice_portal, fieldservice_project,
fieldservice_recurring, fieldservice_route, fieldservice_sale,
fieldservice_size, fieldservice_skill, fieldservice_stage_validation,
fieldservice_vehicle

# Other modules
ftp_cuenta_cliente, web_domain_field
```

#### Common Commands
```bash
# Install a single addon
docker exec addon-ftp-web-1 odoo -i <addon_name> -d odoo --stop-after-init

# Update addon after code changes
docker exec addon-ftp-web-1 odoo -u <addon_name> -d odoo --stop-after-init

# Update all installed addons
docker exec addon-ftp-web-1 odoo -u all -d odoo --stop-after-init

# Restart web service after changes
docker compose restart web
```

### Container Access
```bash
# Access Odoo container shell
docker exec -it addon-ftp-web-1 bash

# Access PostgreSQL
docker exec -it addon-ftp-db-1 psql -U odoo -d odoo
```

## Architecture

### Installed Module Groups

#### Field Service Management Suite
- **Core**: Complete field service operations management
- **Accounting**: Invoice tracking and analytic accounting
- **CRM/Sales**: Lead conversion and sales order integration  
- **Project Management**: Task and project integration
- **Scheduling**: Calendar, recurring orders, and route planning
- **Resource Management**: Skills, vehicles, and validation rules
- **Customer Portal**: Self-service access for customers
- **ISP Features**: Specialized workflows and time-based billing

### Core Components
The FTP addon (`addons/ftp_cuenta_cliente/`) implements a multi-protocol file transfer system with:

1. **FTP Configuration Model** (`models/ftp_config.py`):
   - Stores connection credentials and settings
   - Supports FTP, FTPS, SFTP, and SCP protocols
   - Manages cron jobs for scheduled file processing
   - Connection testing functionality

2. **FTP Service** (`models/ftp_service.py`):
   - Protocol-specific connection handlers
   - File download and transfer logic
   - Directory management (moving processed files)
   - Error handling and retry mechanisms

3. **FTP File Model** (`models/ftp_file.py`):
   - Stores processed file metadata
   - Excel content parsing to JSON
   - File history tracking

### Key Technical Details
- **Database**: Uses `odoo` database with credentials (user: odoo, password: odoo)
- **Admin Access**: Default admin/admin credentials for web interface
- **Python Dependencies**: 
  - `paramiko` (SSH/SFTP connections)
  - `openpyxl` and `pandas==2.0.3` (Excel processing)
  - `numpy==1.24.3` (Data operations)
  - `bcrypt` and `PyNaCl` (Security)
- **File Processing Flow**: 
  1. Downloads Excel files from configured FTP path
  2. Parses content using first row as JSON keys
  3. Stores in database as JSON
  4. Moves processed files to `/files_read` directory on remote server

### Configuration Files
- `docker-compose.yml`: Defines Odoo 16 web service and PostgreSQL 15 database
- `config/odoo.conf`: Odoo server configuration (ports, database, addons path)
- `addons/ftp_cuenta_cliente/__manifest__.py`: Addon metadata and dependencies

## Access Points
- **Odoo Web Interface**: http://localhost:8069
- **PostgreSQL Database**: localhost:5432
- **Main Menu Structures**:
  - Field Service > Orders / Locations / Teams / Workers
  - FTP Cuenta Cliente > FTP Configurations / Processed Files
  - Sales > Orders / Customers
  - Project > Projects / Tasks

## Development Workflow
1. Make changes to addon files in `addons/ftp_cuenta_cliente/`
2. Update the addon: `docker exec addon-ftp-web-1 odoo -u ftp_cuenta_cliente -d odoo --stop-after-init`
3. Restart if needed: `docker compose restart web`
4. Test via web interface at http://localhost:8069

## Common Tasks

### Testing FTP Connections
Navigate to FTP Cuenta Cliente > FTP Configurations, create/edit a configuration, and use the "Test Connection" button.

### Manual File Processing
Open an FTP configuration and click "Process Files Now" to trigger immediate file download and processing.

### Viewing Logs
```bash
# Odoo application logs
docker compose logs -f web

# Check cron job execution
docker exec addon-ftp-web-1 grep -i "ftp\|cron" /var/log/odoo/odoo.log
```

### Debugging
- Check `models/ftp_service.py` for connection logic
- Review `data/cron_data.xml` for scheduled job configuration
- Examine `security/ir.model.access.csv` for permission issues

## Known Issues & Solutions

### Python Package Compatibility
- Use `numpy==1.24.3` and `pandas==2.0.3` for Odoo 16 compatibility
- Reinstall binary packages if import errors occur:
  ```bash
  docker exec addon-ftp-web-1 pip uninstall -y numpy pandas bcrypt PyNaCl
  docker exec addon-ftp-web-1 pip install numpy==1.24.3 pandas==2.0.3 bcrypt PyNaCl
  ```

### Module Dependencies Not Available
Some modules require additional dependencies not included:
- **fieldservice_geoengine**: Requires `base_geoengine`
- **fieldservice_timeline**: Requires `web_timeline`
- **fieldservice_stock_request**: Requires `stock_request` modules
- **stock_picking_to_batch_group_fields**: Requires `stock_picking_batch`