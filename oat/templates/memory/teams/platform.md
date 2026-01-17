# Team: Platform

## Team Overview

The Platform team is responsible for infrastructure, tooling, and developer experience across the organization.

## Domain Knowledge

### Key Concepts
- **Infrastructure as Code**: All infrastructure defined in code (Terraform, Ansible)
- **Container Orchestration**: Kubernetes for container management
- **CI/CD Pipelines**: Automated testing and deployment
- **Monitoring & Observability**: Prometheus, Grafana, ELK stack

### Common Patterns
- **Microservices Architecture**: Services communicate via APIs
- **Event-Driven Architecture**: Services communicate via events
- **Service Mesh**: Istio for service-to-service communication

## Team-Specific Rules

### Infrastructure Changes
- All infrastructure changes must be reviewed by platform team
- Changes must be tested in staging first
- Rollback plan required for production changes

### Tooling
- Standardize on organization-approved tools
- New tools require platform team approval
- Documentation required for all tools

## Related Teams

- **Product Team**: Provides requirements for platform features
- **DevOps**: Collaborates on deployment pipelines
