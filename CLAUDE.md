# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is an Odoo 16 FTP addon development environment using Docker Compose. The project provides a containerized setup for developing custom FTP functionality as an Odoo addon.

## Development Environment Setup

### Starting the Environment
```bash
# Start PostgreSQL first, then Odoo
docker compose up -d db && docker compose up web

# Or start both services in background
docker compose up -d
```

### Initializing Odoo Database
```bash
# Initialize Odoo with base modules (required on first run)
docker exec -it addon-ftp-web-1 odoo -i base -d postgres --stop-after-init

# Or run initialization as one-time command
docker compose run --rm web odoo -i base -d postgres --stop-after-init
```

### Accessing the Application
- Odoo Web Interface: http://localhost:8069
- PostgreSQL Database: localhost:5432

### Managing Services
```bash
# Stop all services
docker compose down

# View logs
docker compose logs web
docker compose logs db

# Access Odoo container shell
docker exec -it addon-ftp-web-1 bash
```

## Project Structure
```
├── docker-compose.yml    # Docker orchestration (Odoo 16 + PostgreSQL 15)
├── .env                 # Database configuration
├── addons/              # Custom Odoo addons directory (mounted to /mnt/extra-addons)
├── config/              # Odoo configuration files (mounted to /etc/odoo)
└── CLAUDE.md           # This file
```

## Addon Development

### Creating a New Addon
Custom addons should be placed in the `addons/` directory with standard Odoo structure:
```
addons/my_ftp_addon/
├── __manifest__.py      # Addon manifest
├── __init__.py         # Module initialization
├── models/             # Data models
├── views/              # XML views
├── controllers/        # Web controllers
└── static/             # Static assets
```

### Database Credentials
- Database: `postgres`
- User: `odoo`
- Password: Managed via Docker secrets

## Architecture Notes
- **Container Setup**: Two-service architecture with separate web and database containers
- **Volume Persistence**: Odoo data and PostgreSQL data are persisted in Docker volumes
- **Addon Loading**: Custom addons are mounted from `./addons` to `/mnt/extra-addons` in the container
- **Configuration**: Odoo configuration can be placed in `./config` directory

## Development Guidelines
- Place all custom addons in the `addons/` directory
- Use Docker secrets for password management in production
- The database needs initialization with base modules on first run
- Custom addons will need to be installed/upgraded through Odoo's module management