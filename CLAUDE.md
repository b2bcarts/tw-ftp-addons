# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Odoo 16 Field Service Management platform with custom FTP integration for automated Excel file processing and sale order generation. The system uses Docker Compose for containerization and supports multiple file transfer protocols (FTP/FTPS/SFTP/SCP).

## Development Commands

### Environment Management
```bash
# Start services (database must be healthy before web starts)
docker compose up -d

# Stop services
docker compose down

# Restart web service after code changes
docker compose restart web

# View logs
docker compose logs -f web
docker compose logs -f db
```

### Database Initialization (First Run Only)
```bash
# Initialize Odoo with base modules
docker exec -it addon-ftp-web-1 odoo -i base -d odoo --stop-after-init
```

### Addon Development Commands
```bash
# Install a new addon
docker exec addon-ftp-web-1 odoo -i <addon_name> -d odoo --stop-after-init

# Update addon after code changes (most common during development)
docker exec addon-ftp-web-1 odoo -u <addon_name> -d odoo --stop-after-init

# Update FTP addon specifically
docker exec addon-ftp-web-1 odoo -u ftp_cuenta_cliente -d odoo --stop-after-init

# Update all installed addons
docker exec addon-ftp-web-1 odoo -u all -d odoo --stop-after-init

# Check addon installation status
docker exec addon-ftp-web-1 odoo shell -d odoo -c "env['ir.module.module'].search([('name','=','<addon_name>')]).state"
```

### Container Access
```bash
# Access Odoo container shell
docker exec -it addon-ftp-web-1 bash

# Access PostgreSQL
docker exec -it addon-ftp-db-1 psql -U odoo -d odoo

# Python shell with Odoo environment
docker exec -it addon-ftp-web-1 odoo shell -d odoo
```

### Python Package Management
```bash
# Install/reinstall packages for Odoo 16 compatibility
docker exec addon-ftp-web-1 pip install numpy==1.24.3 pandas==2.0.3 openpyxl paramiko bcrypt PyNaCl

# Fix binary package issues
docker exec addon-ftp-web-1 pip uninstall -y numpy pandas bcrypt PyNaCl
docker exec addon-ftp-web-1 pip install --no-cache-dir numpy==1.24.3 pandas==2.0.3 bcrypt PyNaCl
```

## Architecture

### Core System Components

#### Docker Services
- **web**: Odoo 16 application server (port 8069)
  - Auto-installs base module on startup
  - Mounts custom addons from `./addons`
  - Configuration from `./config/odoo.conf`
- **db**: PostgreSQL 15 database (port 5432)
  - Health checks ensure availability before Odoo starts
  - Credentials: odoo/odoo

#### FTP Addon Architecture (`addons/ftp_cuenta_cliente/`)

The addon follows Odoo's MVC pattern with clear separation of concerns:

1. **Models Layer** (`models/`)
   - `ftp_config.py`: Multi-protocol connection configuration (FTP/FTPS/SFTP/SCP)
   - `ftp_service.py`: Protocol handlers and file transfer logic
   - `ftp_file.py`: File metadata and Excel-to-JSON parsing
   - `ftp_file_type.py`: File type definitions with column mappings
   - `sale_order_processor.py`: Excel-to-sale-order conversion engine

2. **Views Layer** (`views/`)
   - Configuration forms for FTP connections
   - File processing monitoring interfaces
   - Column mapping configuration screens

3. **Wizard Layer** (`wizard/`)
   - `ftp_column_mapping_wizard.py`: Dynamic field mapping between Excel columns and Odoo models

4. **Data Files** (`data/`)
   - `cron_data.xml`: Scheduled job (30-minute intervals)
   - `ftp_file_type_data.xml`: Predefined file type configurations

### File Processing Workflow

1. **Connection Phase**: FTP service connects using configured protocol
2. **Download Phase**: Retrieves Excel files from remote path
3. **Parse Phase**: Converts Excel to JSON using first row as keys
4. **Store Phase**: Saves parsed data in `ftp.file` records
5. **Process Phase**: Creates sale orders grouped by 'id.mochila'
6. **Cleanup Phase**: Moves processed files to `/files_read` on remote

### Sale Order Generation Logic

The system maps Excel data to Odoo sale orders:
- Groups products by `id.mochila` field
- Matches products via SKU (`default_code`)
- Creates/updates customers using RUT field
- Generates detailed processing logs

### Currently Installed Modules (20 total)

**Core Modules:**
- `base_territory`: Territory management
- `fieldservice`: Core field service functionality

**Field Service Extensions (16 modules):**
- Account integration: `fieldservice_account`, `fieldservice_account_analytic`
- CRM/Sales: `fieldservice_crm`, `fieldservice_sale`
- Scheduling: `fieldservice_calendar`, `fieldservice_recurring`, `fieldservice_route`
- Resources: `fieldservice_skill`, `fieldservice_vehicle`, `fieldservice_size`
- Project: `fieldservice_project`, `fieldservice_activity`
- ISP: `fieldservice_isp_account`, `fieldservice_isp_flow`
- Other: `fieldservice_portal`, `fieldservice_stage_validation`

**Custom Modules:**
- `ftp_cuenta_cliente`: FTP file processing
- `web_domain_field`: Domain field widget

## Access Points
- **Odoo Web**: http://localhost:8069 (admin/admin)
- **PostgreSQL**: localhost:5432 (odoo/odoo)
- **Main Menus**:
  - FTP Cuenta Cliente > FTP Configurations / Processed Files
  - Field Service > Orders / Locations / Teams / Workers
  - Sales > Orders / Customers

## Common Development Tasks

### Testing FTP Connections
1. Navigate to FTP Cuenta Cliente > FTP Configurations
2. Create/edit configuration
3. Click "Test Connection" button

### Manual File Processing
1. Open FTP configuration record
2. Click "Process Files Now" action button

### Creating Sale Orders from Excel
1. Navigate to FTP Cuenta Cliente > Processed Files
2. Select processed file
3. Click "Create Sale Orders" button

### Debugging Cron Jobs
```bash
# Check cron execution
docker exec addon-ftp-web-1 grep -i "cron\|ftp" /var/log/odoo/odoo.log

# Test cron method manually
docker exec -it addon-ftp-web-1 odoo shell -d odoo
>>> env['ftp.service'].cron_process_ftp_files()
```

## Troubleshooting

### Module Update Not Reflecting
```bash
# Force update with cache clear
docker exec addon-ftp-web-1 odoo -u ftp_cuenta_cliente -d odoo --stop-after-init
docker compose restart web
```

### Sale Order Creation Failures
Check for:
- Products with matching `default_code` (SKU)
- Valid RUT in customer data
- Non-empty `id.mochila` for grouping
- Correct Excel column headers

### Connection Issues
- Verify network access to FTP server
- Check protocol-specific ports (21 for FTP, 22 for SFTP/SCP)
- Validate credentials and paths
- Review `models/ftp_service.py` connection handlers

### Missing Dependencies
Some field service modules have unmet dependencies:
- `fieldservice_geoengine`: Requires `base_geoengine`
- `fieldservice_timeline`: Requires `web_timeline`
- `fieldservice_stock_request`: Requires `stock_request`