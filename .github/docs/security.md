# Security & Compliance

## GDPR/HIPAA Requirements

### Data Processing Principles
- **Data Minimization**: Process only necessary data
- **Purpose Limitation**: Use data only for stated purposes  
- **Storage Minimization**: Retain data for minimum required period
- **Transparency**: Document all processing activities
- **Accountability**: Identify clear data controllers

### Implementation Standards

#### Patient Data Handling
```python
# SHA-256 + salt for patient IDs
import hashlib
def hash_patient_id(patient_id: str, salt: str) -> str:
    return hashlib.sha256(f"{patient_id}{salt}".encode()).hexdigest()

# FF3 FPE for structured data
from pseudonymizer.ff3_engine import FF3Engine
engine = FF3Engine(key=vault.get_key("ff3_key"))
anonymized_id = engine.encrypt(patient_id)
```

#### Secure Logging
```python
# ✅ Correct audit logging
logger.audit({
    "action": "patient_data_anonymized",
    "user_id": current_user.id,
    "record_count": len(processed_records),
    "timestamp": datetime.utcnow().isoformat(),
    "compliance_check": "GDPR_Article_25"
})

# ❌ NEVER log sensitive data
logger.info(f"Patient ID: {patient_id}")  # FORBIDDEN
```

## Security Architecture

### Zero Trust Implementation
- **Identity Verification**: Every request authenticated
- **Least Privilege**: Minimal required permissions
- **Continuous Monitoring**: Real-time security analysis
- **Encrypted Communications**: TLS 1.3 for all traffic

### Vault Integration
```python
# Standard Vault client pattern
from vault_utils.auto_unseal import VaultManager

class SecureService:
    def __init__(self):
        self.vault = VaultManager()
        self.secrets = self.vault.get_secrets("service/secrets")
    
    def get_encryption_key(self, key_name: str) -> str:
        return self.vault.get_secret(f"encryption/{key_name}")
```

## Compliance Checklist

### Required Security Measures
- ✅ Vault integration for all secrets
- ✅ Audit logging for data access
- ✅ TLS encryption for communications
- ✅ Role-based access control
- ✅ Data retention policies
- ✅ Incident response procedures

### Prohibited Practices
- ❌ Hardcoded credentials
- ❌ Unencrypted personal data storage
- ❌ Logging sensitive information
- ❌ Direct database access without authentication
- ❌ Cross-border data transfer without safeguards

## Incident Response

### Data Breach Protocol
1. **Detection**: Automated monitoring alerts
2. **Assessment**: Classify breach severity
3. **Containment**: Isolate affected systems
4. **Notification**: GDPR 72-hour requirement
5. **Recovery**: Restore secure operations
6. **Review**: Post-incident analysis
