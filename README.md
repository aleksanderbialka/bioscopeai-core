# BioScopeAI Core

Core backend service for BioScopeAI application - a microscopy image analysis platform.

## Overview

BioScopeAI Core provides the backend infrastructure for managing microscopy images, datasets, classifications, and user authentication.

## Documentation

### Database Schema

For a comprehensive view of the data structure and entity relationships, see:

- **[Entity-Relationship Diagram (ERD)](docs/ERD.md)** - Full documentation with Mermaid diagrams, entity descriptions, and relationship details
- **[ERD Mermaid Diagram](docs/ERD.mmd)** - Standalone Mermaid diagram (viewable in GitHub)
- **[ERD PlantUML Diagram](docs/ERD.puml)** - PlantUML format for various rendering tools

## Technology Stack

- **Framework**: FastAPI
- **ORM**: Tortoise ORM
- **Database**: PostgreSQL (asyncpg)
- **Migration Tool**: Aerich
- **Authentication**: JWT with Argon2 password hashing
- **Python Version**: 3.13

## Key Features

- Role-based access control (ADMIN, RESEARCHER, ANALYST, VIEWER)
- User authentication and authorization
- Device management for microscope integration
- Dataset organization and management
- Image upload and storage
- AI-powered image classification
- Classification result tracking with confidence scores

## Project Structure

```
bioscopeai_core/
├── app/
│   ├── api/          # API endpoints and routers
│   ├── db/           # Database configuration
│   └── models/       # Data models (ORM)
├── docs/             # Documentation including ERD
└── migrations/       # Database migrations
```

## Development

### Prerequisites

- Python 3.13
- PostgreSQL
- Poetry (dependency management)

### Setup

```bash
# Install dependencies
poetry install

# Run database migrations
aerich upgrade

# Start development server
uvicorn bioscopeai_core.app.main:app --reload
```

### Code Quality

The project uses several tools for maintaining code quality:

- **Ruff**: Linting and formatting
- **MyPy**: Type checking
- **Vulture**: Dead code detection
- **Pre-commit**: Git hooks for automated checks

## License

See LICENSE file for details.

## Author

Aleksander Białka (aleksander.bialka@icloud.com)
