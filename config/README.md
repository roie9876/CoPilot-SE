# Configuration Files

This directory contains YAML configuration files for data sources and service mappings.

## Files

### `trusted_sources.yaml`
Defines the 30+ trusted data sources for online retrieval:
- Official cloud provider documentation (AWS, GCP, Azure, Oracle)
- Pricing pages
- Community resources (Stack Overflow, Reddit, GitHub Discussions)
- YouTube channels (official cloud providers)
- Case studies and whitepapers

### `service_mapping.yaml`
Maps equivalent services across cloud providers:
- Compute: EC2 (AWS) ↔ Compute Engine (GCP) ↔ Virtual Machines (Azure) ↔ Compute (Oracle)
- Storage: S3 ↔ Cloud Storage ↔ Blob Storage ↔ Object Storage
- Databases, networking, AI/ML services, etc.

### `pricing_sources.yaml`
Direct links to pricing calculators and APIs:
- AWS Pricing API
- GCP Pricing Calculator
- Azure Pricing Calculator
- Oracle Cloud Cost Estimator

## Usage

```python
import yaml

# Load trusted sources
with open('config/trusted_sources.yaml', 'r') as f:
    trusted_sources = yaml.safe_load(f)

# Load service mappings
with open('config/service_mapping.yaml', 'r') as f:
    service_mapping = yaml.safe_load(f)
```

## Implementation Status

⚠️ **Phase 2**: Configuration files will be created during the POC development phase based on docs/04-data-sources-strategy.md.
