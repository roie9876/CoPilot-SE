# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

### Reporting Process

1. **DO NOT** report security vulnerabilities through public GitHub issues.

2. **Report via:**
   - GitHub Security Advisories (preferred): Navigate to the Security tab
   - Or email: [security contact email]

3. **Include in report:**
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Affected versions
   - Suggested fix (if known)

**Immediate reporting required for:**
   - Exposed API keys or credentials
   - Authentication/authorization bypass
   - Data leakage issues
   - Injection vulnerabilities

### Response Timeline

- **Acknowledgment:** Within 24 hours
- **Initial assessment:** Within 3 business days
- **Fix timeline:** Depends on severity
  - Critical: Immediate (within 24-48 hours)
  - High: Within 1 week
  - Medium: Within 2 weeks
  - Low: Next sprint

## Security Best Practices

### For Developers

1. **Never commit secrets:**
   - Use `.env` for local development
   - Use Azure Key Vault for production
   - Review `.gitignore` before commits

2. **API keys and tokens:**
   - Rotate keys regularly
   - Use least-privilege access
   - Store in Azure Key Vault

3. **Authentication:**
   - Always use Azure AD
   - Implement RBAC correctly
   - Validate tokens server-side

4. **Input validation:**
   - Sanitize all user inputs
   - Validate against schemas (Pydantic)
   - Protect against injection attacks

5. **Dependencies:**
   - Keep dependencies updated
   - Review security advisories
   - Use `pip-audit` and `npm audit`

### Checking for Security Issues

```bash
# Python dependencies
pip install pip-audit
pip-audit

# Node.js dependencies
cd mcp-server
npm audit

# Check for exposed secrets (use git-secrets)
git secrets --scan
```

## Secure Configuration

### Environment Variables

- **NEVER** commit `.env` files
- Use `.env.example` as template only
- Store production secrets in Azure Key Vault

### Azure Resources

- Enable Azure AD authentication
- Use Managed Identities where possible
- Enable Azure Security Center
- Configure network security groups
- Enable diagnostic logging

## Data Classification

### Sensitive Data
- API keys and credentials
- User data (if any in POC)
- Authentication tokens

### Handling Requirements

- Never commit secrets to version control
- Use environment variables or secure vaults
- Encrypt sensitive data in transit and at rest
- Implement proper access controls

## Compliance

Security best practices for this project:
- Data residency considerations (configurable)
- Authentication: Azure AD or configurable auth
- Audit logging: Application Insights or equivalent
- Encryption: In transit (HTTPS) and at rest

## Known Security Considerations (POC)

1. **Public pricing sources:**
   - ±30% accuracy acceptable
   - No cloud provider authentication
   - Clear disclaimers required

2. **No RAG for POC:**
   - No document upload = reduced attack surface
   - Online-only data strategy

3. **Limited to 10 users:**
   - Simplified authentication
   - Less complex authorization

4. **Post-POC security enhancements** (Phase 6-7):
   - Add cloud provider authentication
   - Implement compliance validation
   - Add document upload with scanning
   - Enhanced audit logging

## Contact

For security concerns:
- Use GitHub Security Advisories
- Or create a private issue for discussion

---

**Last Updated:** October 31, 2025  
**Version:** 2.0 (Multi-Cloud POC)
