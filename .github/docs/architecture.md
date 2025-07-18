# Architecture & Services

## Service Structure

### Core Services
```
src/
├── pseudonymizer/     # FF3 FPE anonymization engine
├── metafier/         # ChatGPT-based metadata conversion  
├── verifier/         # Data integrity validation
├── nmdose/           # Nuclear medicine dose analysis
└── nmiq/             # Nuclear medicine image quality
```

### Security Infrastructure
- **Vault**: Secret management & PKI certificates
- **Keycloak**: Authentication & authorization
- **ELK Stack**: Centralized logging & audit
- **Bitwarden**: Password management

## Directory Structure

### Development Environment
```plaintext
projects/ai4rm/
├── src/                    # Service source code
├── logger/                 # Centralized logging system
├── config/                 # Configuration management
├── templates/              # Service templates
├── docker/                 # Runtime data volumes
├── scripts/                # Automation scripts
├── tests/                  # Test suites
└── wiki/                   # Documentation
```

### Production Environment
```plaintext
/opt/ai4rm/
├── src/                    # Application code
├── docker/                 # Service data
│   ├── vault/
│   ├── elk/
│   ├── keycloak/
│   └── openldap/
└── bitwarden/              # Password management
```

## Service Communication

### Inter-Service Patterns
- **API Gateway**: Centralized routing and authentication
- **Service Mesh**: mTLS communication between services
- **Event Bus**: Asynchronous processing with audit trails
- **Shared Vault**: Centralized secret management

### Data Flow
1. **Input**: Medical data ingestion with validation
2. **Processing**: Multi-stage anonymization pipeline
3. **Validation**: Integrity and compliance checking
4. **Output**: Anonymized data with audit trail
5. **Monitoring**: Real-time metrics and alerts
