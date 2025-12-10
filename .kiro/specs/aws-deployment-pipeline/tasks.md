# Implementation Plan

**Note:** The CDK infrastructure is in a separate repository (`canvalo-infrastructure`). The pipeline will reference three repositories: infrastructure, backend (strands-multi-agent-system), and frontend (CanvaloFrontend).

## Completed Tasks

- [x] 1. Set up CDK project structure
  - [x] 1.1 Create `canvalo-infrastructure` repository with CDK TypeScript project
  - [x] 1.2 Create environment configuration module (`lib/config/environments.ts`)
    - EnvironmentConfig interface with CPU, memory, task counts, VPC CIDR
    - Beta: 0.25 vCPU, 512MB, 1-2 tasks
    - Gamma: 0.5 vCPU, 1GB, 2-4 tasks  
    - Prod: 1 vCPU, 2GB, 2-10 tasks, auto-scaling, deletion protection
  - [ ]* 1.3 Write property test for environment configuration

- [x] 2. Create Dockerfile for backend
  - [x] 2.1 Dockerfile in `strands-multi-agent-system/` with Python 3.11+, uv, health check
  - [x] 2.2 .dockerignore file

- [x] 3. Implement backend configuration migration
  - [x] 3.1 Backend config.py supports Secrets Manager with .env fallback
  - [x] 3.2 Property test for configuration source fallback
  - [ ]* 3.3 Unit tests for Secrets Manager integration

- [x] 4. Create DNS Stack (`lib/stacks/dns-stack.ts`)
  - [x] Route53 hosted zone per environment subdomain
  - [x] Exports hostedZoneId for other stacks

- [x] 5. Create Certificate Stack (`lib/stacks/certificate-stack.ts`)
  - [x] ACM certificate in us-east-1 for CloudFront
  - [x] DNS validation via Route53 hosted zone

- [x] 6. Create Backend Stack (`lib/stacks/backend-stack.ts`)
  - [x] 6.1 VPC with multi-AZ subnets (public/private), NAT gateway
  - [x] 6.2 ECS Cluster with Container Insights
  - [x] 6.3 Secrets Manager secret (Supabase, Bedrock, CORS config)
  - [x] 6.4 CloudWatch Log Group (30-day retention)
  - [x] 6.5 IAM roles (task execution + task role with Bedrock access)
  - [x] 6.6 Docker image via DockerImageAsset
  - [x] 6.7 ECS Fargate service with ALB (HTTPS, health checks)
  - [x] 6.8 ACM certificate for backend domain with DNS validation
  - [x] 6.9 Auto-scaling for production (CPU-based, 70% target)
  - [x] 6.10 Route53 A record pointing to ALB
  - [x] 6.11 HTTP to HTTPS redirect
  - [ ]* 6.12 Property tests for backend stack

- [x] 7. Create Frontend Stack (`lib/stacks/frontend-stack.ts`)
  - [x] 7.1 S3 bucket with public access blocked, versioning for prod
  - [x] 7.2 CloudFront distribution with S3 OAC origin
  - [x] 7.3 Geo-restriction (US only)
  - [x] 7.4 Route53 A record pointing to CloudFront
  - [x] 7.5 S3 bucket deployment from local build
  - [x] 7.6 Deletion protection for production (RETAIN policy)
  - [ ]* 7.7 Property tests for frontend stack

- [x] 8. Create CDK App entry point (`bin/app.ts`)
  - [x] Loops through all environments (beta, gamma, prod)
  - [x] Creates stack dependency chain: DNS → Certificate → Backend → Frontend
  - [x] Domain structure: `canvalofrontend.{env}.{domain}`, `api.{env}.{domain}`

## Remaining Tasks

- [ ] 9. Create Monitoring Stack
  - [x] 9.1 CloudWatch log groups (implemented in BackendStack)
    - Log group `/ecs/canvalo-{env}` with 30-day retention
  - [ ] 9.2 Create CloudWatch alarms
    - Alarm for unhealthy task count
    - Alarm for ALB 5xx error rate
    - SNS notifications
  - [ ] 9.3 Configure ALB access logging
    - S3 bucket for ALB logs
  - [ ] 9.4 Create CloudWatch dashboard for production

- [ ] 10. Implement Pipeline Stack (`lib/stacks/pipeline-stack.ts`)
  - [x] 10.1 Stub exists with PipelineStackProps interface
  - [ ] 10.2 Set up CodeStar Connection for GitHub
  - [ ] 10.3 Create CDK Pipeline with self-mutation
  - [ ] 10.4 Add pre-deployment test steps (pytest, npm test, jest)
  - [ ] 10.5 Configure Beta stage deployment
  - [ ] 10.6 Configure Gamma stage with cross-account deployment
  - [ ] 10.7 Configure Prod stage with manual approval
  - [ ] 10.8 Configure SNS notifications for failures

- [ ] 11. Property Tests
  - [ ]* 11.1 Environment configuration property test
  - [ ]* 11.2 VPC multi-AZ property test
  - [ ]* 11.3 Secrets Manager integration property test
  - [ ]* 11.4 IAM least-privilege property test
  - [ ]* 11.5 S3 bucket security property test
  - [ ]* 11.6 CloudFront cache configuration property test
  - [ ]* 11.7 ALB TLS termination property test
  - [ ]* 11.8 Auto-scaling configuration property test
  - [ ]* 11.9 Deletion protection property test
  - [ ]* 11.10 Pipeline stage ordering property test

- [ ] 12. Documentation
  - [ ] 12.1 Create README for infrastructure project
  - [ ] 12.2 Document CDK bootstrap commands
  - [ ] 12.3 Document CodeStar Connection setup
  - [ ] 12.4 Document Route53/ACM setup

---

## Known Issues / TODOs in Code

1. **Hardcoded paths in stacks:**
   - `BackendStack`: Docker image path hardcoded to `/Users/user/git_projects/amazon_bedrock/strands-multi-agent-system`
   - `FrontendStack`: Build path hardcoded to `/Users/user/git_projects/canvalo/CanvaloFrontend/build`
   - These need to be parameterized for pipeline deployment

2. **Account IDs:**
   - Beta account hardcoded: `910345601959`
   - Gamma/Prod accounts read from env vars (empty string fallback)

3. **Pipeline Stack:** Stub only, not implemented

4. **CloudFront TTL:** Using default, not explicitly set to 24 hours

5. **CORS headers:** Not explicitly configured on CloudFront

---

## Future Enhancements

- [ ] 13. Multi-account pipeline with cross-account IAM roles
- [ ] 14. Custom domains for all environments
- [ ] 15. CloudWatch dashboard for production
- [ ] 16. ALB access logging
- [ ] 17. WAF integration for CloudFront/ALB
