# BioScopeAI Core

[![CI/CD](https://github.com/aleksanderbialka/bioscopeai-core/actions/workflows/main_bioscopeai_core.yml/badge.svg?branch=dev)](https://github.com/aleksanderbialka/bioscopeai-core/actions/workflows/main_bioscopeai_core.yml)
![Docker](https://img.shields.io/badge/Docker-2496ED.svg?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.120-009688.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)
![Kafka](https://img.shields.io/badge/Kafka-3.x-231F20.svg)
![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)


Core backend service for BioScopeAI application - a microscopy image classification system powered by AI.

## Overview

BioScopeAI Core is a FastAPI-based backend service that manages microscopy images, runs AI-powered classifications, and provides results through a RESTful API. The system uses an event-driven architecture with Kafka for asynchronous job processing.

## Architecture

### System Overview

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Frontend]
    end

    subgraph "API Gateway"
        API[FastAPI Server<br/>Port 8000]
    end

    subgraph "Authentication"
        JWT[JWT Auth<br/>OAuth2 + Argon2]
    end

    subgraph "Core Services"
        AUTH[Auth Service]
        USER[User Service]
        DEVICE[Device Service]
        DATASET[Dataset Service]
        IMAGE[Image Service]
        CLASS[Classification Service]
        RESULT[Classification Result Service]
    end

    subgraph "Message Queue"
        KAFKA[Apache Kafka]
        PRODUCER[Classification<br/>Producer]
        CONSUMER[Classification Result<br/>Consumer]
    end

    subgraph "Storage Layer"
        POSTGRES[(PostgreSQL<br/>Metadata)]
        MINIO[(MinIO<br/>Image Files)]
    end

    subgraph "External Services"
        CLASSIFIER[AI Classifier<br/>Service]
    end

    WEB -->|HTTPS| API
    API --> JWT
    JWT --> AUTH
    API --> USER
    API --> DEVICE
    API --> DATASET
    API --> IMAGE
    API --> CLASS
    API --> RESULT

    CLASS --> PRODUCER
    PRODUCER --> KAFKA
    KAFKA --> CLASSIFIER
    CLASSIFIER -->|Results| KAFKA
    KAFKA --> CONSUMER
    CONSUMER --> RESULT

    USER --> POSTGRES
    DEVICE --> POSTGRES
    DATASET --> POSTGRES
    IMAGE --> POSTGRES
    CLASS --> POSTGRES
    RESULT --> POSTGRES

    IMAGE --> MINIO

    style API fill:#009688
    style KAFKA fill:#231F20,color:#fff
    style POSTGRES fill:#336791,color:#fff
    style MINIO fill:#C72E49,color:#fff
    style CLASSIFIER fill:#FF6F00,color:#fff
```

### Data Flow

**1. Image Upload Flow:**
```
Client → API → Image Service → MinIO (file) + PostgreSQL (metadata)
```

**2. Classification Request Flow:**
```
Client → API → Classification Service → Kafka Producer → Kafka Topic
→ AI Classifier Service → Processing → Results to Kafka
→ Result Consumer → Result Service → PostgreSQL
```

**3. Query Results Flow:**
```
Client → API → Result Service → PostgreSQL → Response
```

### Tech Stack
- **Framework:** FastAPI (Python 3.13)
- **Database:** PostgreSQL (via Tortoise ORM)
- **Message Queue:** Apache Kafka (bitnami Kafka image)
- **Object Storage:** MinIO (S3-compatible)
- **Authentication:** JWT with OAuth2
- **Password Hashing:** Argon2

### Core Components

- **API Layer:** RESTful endpoints for resource management
- **Authentication:** JWT-based auth with role-based access control (Admin, Analyst, User)
- **Classification Engine:** Kafka-driven async job processing
- **Storage:** MinIO for image files, PostgreSQL for metadata
- **Migrations:** Aerich for database version control

## Features

### Authentication & Authorization
- JWT tokens (access + refresh)
- Role-based permissions (Admin, Analyst, User)
- Service-to-service authentication

### Resource Management
- **Users:** User account management
- **Devices:** Microscopy device registration
- **Datasets:** Image collection organization
- **Images:** Upload, retrieve, and manage microscopy images
- **Classifications:** Run AI models on images/datasets
- **Results:** Store and query classification outputs

### Event-Driven Processing
- Kafka producer for classification jobs
- Kafka consumer for processing results
- Asynchronous job status tracking

## API Endpoints

```
/api/health          - Health check
/api/auth            - Authentication (login, refresh, logout)
/api/users           - User management
/api/devices         - Device management
/api/datasets        - Dataset management
/api/images          - Image upload/retrieval
/api/classifications - Classification jobs
/api/classification-results - Query results
```

## Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    User ||--o{ Dataset : owns
    User ||--o{ Classification : creates
    User ||--o{ RefreshToken : has

    Device ||--o{ Image : captures

    Dataset ||--o{ Image : contains
    Dataset ||--o{ Classification : "classified by"

    Image ||--o{ Classification : "classified by"
    Image ||--o{ ClassificationResult : "has results"

    Classification ||--o{ ClassificationResult : produces

    User {
        uuid id PK
        string email UK
        string username UK
        string hashed_password
        enum role
        datetime created_at
        datetime updated_at
    }

    Device {
        uuid id PK
        string name UK
        string device_type
        jsonb metadata
        datetime created_at
    }

    Dataset {
        uuid id PK
        string name
        string description
        uuid owner_id FK
        datetime created_at
        datetime updated_at
    }

    Image {
        uuid id PK
        string filename
        string storage_path
        int file_size
        string content_type
        jsonb metadata
        uuid dataset_id FK
        uuid device_id FK
        uuid uploaded_by_id FK
        datetime created_at
    }

    Classification {
        uuid id PK
        uuid image_id FK "nullable"
        uuid dataset_id FK "nullable"
        string model_name
        enum status
        uuid created_by_id FK
        datetime created_at
        datetime updated_at
    }

    ClassificationResult {
        uuid id PK
        uuid image_id FK
        uuid classification_id FK
        string label
        float confidence
        string model_name
        datetime created_at
    }

    RefreshToken {
        uuid id PK
        string token UK
        uuid user_id FK
        datetime expires_at
        datetime created_at
    }
```

### Key Models
- **User:** System users with roles
- **Device:** Microscopy devices
- **Dataset:** Collections of images
- **Image:** Individual microscopy images
- **Classification:** Classification jobs (pending/running/completed/failed)
- **ClassificationResult:** AI model predictions with confidence scores

### Relationships
- Images belong to Datasets
- ClassificationResults link to both Images and Classifications
- CASCADE deletes: removing Dataset/Image deletes related Classifications

## Setup

### Prerequisites
- Python 3.13
- PostgreSQL
- Apache Kafka
- MinIO

Services:
- Core API: `localhost:8000`
- API docs: `localhost:8000/api/docs`

## Configuration

Configuration via YAML file (`bioscopeai-core-config.yaml`):

- **App:** Port, CORS, logging level
- **Database:** PostgreSQL connection
- **Kafka:** Brokers, topics
- **S3/MinIO:** Bucket configuration
- **Auth:** JWT keys, token expiration

## Development

### Project Structure
```
bioscopeai_core/
├── app/
│   ├── api/           # API routers and endpoints
│   ├── auth/          # Authentication logic
│   ├── core/          # Configuration, logging
│   ├── crud/          # Database operations
│   ├── db/            # Database initialization
│   ├── kafka/         # Producers and consumers
│   ├── models/        # Tortoise ORM models
│   ├── schemas/       # Pydantic schemas
│   ├── serializers/   # Model-to-schema converters
│   ├── services/      # Business logic
│   └── utils/         # Utilities
├── migrations/        # Database migrations
└── tests/            # Test suite
```

### Code Quality Tools
- **Ruff:** Linting and formatting
- **MyPy:** Type checking
- **Pytest:** Testing framework
- **Pre-commit:** Git hooks

### Running Tests

```bash
source scipts/run_tests.sh
```


## Contact

Maintainer: aleksanderbialka (aleksander.bialka@icloud.com)
