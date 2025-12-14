# Requirements Document

## Introduction

This document specifies the requirements for deploying the Canvalo application (FastAPI backend and React frontend) to AWS using a multi-account staged pipeline. The deployment infrastructure uses AWS CDK with CDK Pipelines to enable automated deployments across Beta, Gamma, and Production environments hosted in separate AWS accounts. The backend runs on ECS Fargate, and the frontend is served via S3 and CloudFront.

## Implementation Status Summary

| Requirement | Status | Notes |
|-------------|--------|-------|
| 1. Backend Containerization | ✅ Complete | Dockerfile with health check, graceful shutdown |
| 2. Backend Infrastructure | ✅ Complete | VPC, ECS Fargate, ALB with HTTPS, auto-scaling |
| 3. Frontend Infrastructure | ✅ Complete | S3, CloudFront with OAC, bucket deployment |
| 4. Multi-Account Pipeline | ⏳ Stub Only | PipelineStack exists but not implemented |
| 5. Secrets Management | ✅ Complete | Secrets Manager with ECS integration |
| 6. CDK Project Structure | ✅ Complete | Separate repo, TypeScript, organized stacks |
| 7. Environment Configuration | ✅ Complete | Beta/Gamma/Prod configs in environments.ts |
| 8. Frontend-Backend Connectivity | ✅ Partial | HTTPS works, custom domains per env, CORS TBD |
| 9. Configuration Migration | ✅ Complete | Secrets Manager with .env fallback |
| 10. Automated Testing | ❌ Not Started | Pipeline not implemented |
| 11. Monitoring & Observability | ⏳ Partial | CloudWatch Logs done, alarms/dashboard TBD |

## Glossary

- **CDK**: AWS Cloud Development Kit - an infrastructure-as-code framework
- **CDK Pipelines**: A CDK construct library for creating self-mutating CI/CD pipelines
- **ECS Fargate**: AWS Elastic Container Service with serverless compute for containers
- **ECR**: Elastic Container Registry - AWS managed Docker container registry
- **ALB**: Application Load Balancer - AWS managed load balancer for HTTP/HTTPS traffic
- **CloudFront**: AWS content delivery network (CDN) service
- **Secrets Manager**: AWS service for storing and retrieving secrets
- **Pipeline Account**: The AWS account that hosts the CDK Pipeline and orchestrates deployments (can be the Beta account or a dedicated tooling account)
- **Stage Account**: An AWS account representing a deployment environment (Beta, Gamma, or Prod)
- **Cross-Account Trust**: IAM configuration allowing one account to deploy resources to another

## Requirements

### Requirement 1: Backend Containerization

**User Story:** As a developer, I want the FastAPI backend containerized with Docker, so that it can be deployed consistently across all environments.

#### Acceptance Criteria

1. WHEN a developer builds the Docker image THEN the Build_System SHALL produce a container that includes all Python dependencies from pyproject.toml
2. WHEN the container starts THEN the Backend_Container SHALL expose the FastAPI application on a configurable port (default 8000)
3. WHEN the container runs THEN the Backend_Container SHALL read configuration from environment variables for Supabase credentials, AWS region, and Bedrock model ID
4. WHEN the container receives a health check request THEN the Backend_Container SHALL respond with a 200 status code within 5 seconds
5. WHEN the container starts THEN the Backend_Container SHALL support graceful shutdown handling for SIGTERM signals

### Requirement 2: Backend Infrastructure

**User Story:** As a platform engineer, I want the backend deployed on ECS Fargate with an Application Load Balancer, so that the API is scalable and highly available.

#### Acceptance Criteria

1. WHEN the backend stack deploys THEN the Infrastructure SHALL create an ECS Fargate service with at least 2 running tasks for high availability
2. WHEN traffic arrives at the ALB THEN the Load_Balancer SHALL route requests to healthy ECS tasks using round-robin distribution
3. WHEN an ECS task becomes unhealthy THEN the Service SHALL replace the unhealthy task with a new task within 60 seconds
4. WHEN the backend stack deploys THEN the Infrastructure SHALL configure the ECS tasks to retrieve secrets from AWS Secrets Manager
5. WHEN the backend stack deploys THEN the Infrastructure SHALL create a VPC with public and private subnets across at least 2 availability zones
6. WHEN the ECS service scales THEN the Service SHALL maintain between 2 and 10 tasks based on CPU utilization thresholds

### Requirement 3: Frontend Infrastructure

**User Story:** As a platform engineer, I want the React frontend deployed to S3 with CloudFront distribution, so that users experience fast load times globally.

#### Acceptance Criteria

1. WHEN the frontend stack deploys THEN the Infrastructure SHALL create an S3 bucket configured for static website hosting with public access blocked
2. WHEN the frontend stack deploys THEN the Infrastructure SHALL create a CloudFront distribution with the S3 bucket as origin
3. WHEN a user requests the frontend THEN CloudFront SHALL serve cached content from edge locations with a default TTL of 24 hours
4. WHEN the frontend is updated THEN the Deployment_Process SHALL invalidate the CloudFront cache for changed files
5. WHEN the frontend builds THEN the Build_System SHALL inject environment-specific API URLs via build-time environment variables

### Requirement 4: Multi-Account Pipeline

**User Story:** As a platform engineer, I want a CDK Pipeline that deploys to Beta, Gamma, and Prod accounts sequentially, so that changes are validated before reaching production.

#### Acceptance Criteria

1. WHEN code is pushed to the configured branch THEN the Pipeline SHALL trigger a new deployment automatically
2. WHEN the pipeline runs THEN the Pipeline SHALL deploy to Beta account first, then Gamma, then Prod in sequence
3. WHEN deploying to the Prod account THEN the Pipeline SHALL require manual approval before proceeding
4. WHEN the pipeline infrastructure code changes THEN the Pipeline SHALL update itself (self-mutation) before deploying application changes
5. WHEN a deployment to any stage fails THEN the Pipeline SHALL halt progression to subsequent stages and notify via SNS
6. WHEN the pipeline deploys to a stage account THEN the Pipeline SHALL use cross-account IAM roles with least-privilege permissions
7. WHEN the pipeline is configured THEN the Pipeline SHALL reside in the Beta account to minimize the number of AWS accounts required
8. WHEN deploying to the Beta account THEN the Pipeline SHALL deploy to the same account where it resides (no cross-account needed for Beta stage)
9. WHEN the pipeline is configured THEN the Pipeline SHALL accept a configurable branch name (default: main) via CDK context
10. WHEN a developer needs to deploy a different branch THEN the Developer SHALL update the branch configuration and redeploy the pipeline stack

### Requirement 5: Secrets Management

**User Story:** As a security engineer, I want secrets stored in AWS Secrets Manager per account, so that each environment has isolated credentials.

#### Acceptance Criteria

1. WHEN the infrastructure deploys THEN the Secrets_Manager SHALL store Supabase URL, service key, and pub key as separate secret values
2. WHEN the ECS task starts THEN the Task SHALL retrieve secrets from Secrets Manager at runtime without embedding them in the container image
3. WHEN secrets are accessed THEN the IAM_Policy SHALL restrict access to only the ECS task execution role for that specific account
4. WHEN a secret is rotated THEN the ECS_Service SHALL pick up the new secret value on the next task restart without redeployment

### Requirement 6: CDK Project Structure

**User Story:** As a developer, I want a well-organized CDK project in a separate repository, so that infrastructure code is maintainable and independent from application code.

#### Acceptance Criteria

1. WHEN the CDK project is initialized THEN the Project SHALL use TypeScript as the implementation language
2. WHEN the CDK project is structured THEN the Project SHALL separate stacks for backend, frontend, and pipeline concerns
3. WHEN environment-specific configuration is needed THEN the Project SHALL use CDK context or environment variables rather than hardcoded values
4. WHEN the CDK project builds THEN the Build_System SHALL pass TypeScript compilation with strict mode enabled
5. WHEN the infrastructure is organized THEN the CDK_Project SHALL reside in a separate repository (canvalo-infrastructure) from the application code
6. WHEN the pipeline accesses source code THEN the Pipeline SHALL use CodeStar Connections to access the infrastructure, backend, and frontend repositories

### Requirement 7: Environment-Specific Configuration

**User Story:** As a developer, I want clear separation between development, beta, gamma, and production environments, so that each environment has appropriate settings and resource sizing.

#### Acceptance Criteria

1. WHEN deploying to Beta THEN the Infrastructure SHALL use smaller instance sizes (0.25 vCPU, 512MB memory) and minimum task count of 1
2. WHEN deploying to Gamma THEN the Infrastructure SHALL use medium instance sizes (0.5 vCPU, 1GB memory) and minimum task count of 2
3. WHEN deploying to Prod THEN the Infrastructure SHALL use production instance sizes (1 vCPU, 2GB memory) and minimum task count of 2 with auto-scaling enabled
4. WHEN the backend starts in any environment THEN the Backend SHALL read the ENVIRONMENT variable to determine authentication enforcement level
5. WHEN deploying to any environment THEN the Infrastructure SHALL configure environment-specific Supabase credentials from that account's Secrets Manager
6. WHEN deploying to Prod THEN the Infrastructure SHALL enable deletion protection on stateful resources (S3 buckets, CloudWatch log groups)
7. WHEN a developer runs locally THEN the Developer SHALL use .env files with development credentials without requiring AWS infrastructure

### Requirement 8: Frontend-Backend Connectivity

**User Story:** As a user, I want the frontend to communicate with the backend API securely, so that my data is protected and the application works reliably.

#### Acceptance Criteria

1. WHEN the frontend is built for an environment THEN the Build_System SHALL inject the environment-specific backend API URL via VITE_API_URL environment variable
2. WHEN the frontend makes API requests in Beta or Gamma THEN the Requests SHALL be sent to the auto-generated ALB DNS name for that environment
3. WHEN the frontend makes API requests in Prod THEN the Requests SHALL be sent to the custom domain endpoint (e.g., api.canvalo.com)
4. WHEN deploying to Beta or Gamma THEN the ALB SHALL use HTTP on the auto-generated DNS name without ACM certificate
5. WHEN deploying to Prod THEN the ALB SHALL terminate TLS using an ACM certificate and forward HTTP to ECS tasks
6. WHEN the frontend and backend are in the same environment THEN the CloudFront_Distribution SHALL configure CORS headers to allow requests from the frontend origin
7. WHEN deploying to Prod with custom domains THEN the Infrastructure SHALL create Route53 records pointing to ALB and CloudFront endpoints

### Requirement 9: Configuration Migration

**User Story:** As a developer, I want the application to support both .env files and AWS Secrets Manager, so that the transition to cloud deployment is seamless and local development remains simple.

#### Acceptance Criteria

1. WHEN the backend starts THEN the Backend SHALL first check for AWS Secrets Manager configuration, then fall back to environment variables and .env files
2. WHEN AWS_SECRETS_NAME environment variable is set THEN the Backend SHALL retrieve all configuration from the specified Secrets Manager secret
3. WHEN AWS_SECRETS_NAME is not set THEN the Backend SHALL use the existing .env file and environment variable loading behavior
4. WHEN migrating to Secrets Manager THEN the Migration_Process SHALL support the same configuration keys as the current .env files (SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_PUB_KEY, BEDROCK_MODEL_ID, etc.)
5. WHEN the backend loads configuration THEN the Backend SHALL log which configuration source is being used (Secrets Manager or environment variables) at startup

### Requirement 10: Automated Testing in Pipeline

**User Story:** As a developer, I want automated tests to run in the pipeline, so that broken code is not deployed and deployments are validated.

#### Acceptance Criteria

1. WHEN the pipeline deploys to Beta THEN the Pipeline SHALL run all Python unit tests using pytest before deployment
2. WHEN the pipeline deploys to Beta THEN the Pipeline SHALL run all TypeScript/JavaScript tests using the configured test runner before deployment
3. WHEN the pipeline deploys to Beta THEN the Pipeline SHALL run all CDK assertion tests using Jest before deployment
4. WHEN any test fails in Beta THEN the Pipeline SHALL halt and prevent deployment to any environment
5. WHEN Beta deployment completes THEN the Pipeline SHALL run integration tests against the deployed Beta environment
6. WHEN Gamma deployment completes THEN the Pipeline SHALL run smoke tests (health checks) against the deployed Gamma environment
7. WHEN Prod deployment completes THEN the Pipeline SHALL run smoke tests (health checks) against the deployed Prod environment
8. WHEN post-deployment tests fail THEN the Pipeline SHALL halt progression and notify via SNS

### Requirement 11: Monitoring and Observability

**User Story:** As an operations engineer, I want CloudWatch alarms and logs configured, so that I can monitor application health and troubleshoot issues.

#### Acceptance Criteria

1. WHEN the backend runs THEN the ECS_Service SHALL stream container logs to CloudWatch Logs with a 30-day retention period
2. WHEN the ALB receives requests THEN the Load_Balancer SHALL emit access logs to an S3 bucket
3. WHEN the ECS service has fewer than 2 healthy tasks THEN CloudWatch SHALL trigger an alarm and send notification via SNS
4. WHEN the ALB 5xx error rate exceeds 5% over 5 minutes THEN CloudWatch SHALL trigger an alarm and send notification via SNS
5. WHEN deploying to Prod THEN the Infrastructure SHALL create a CloudWatch dashboard showing key metrics (request count, latency, error rates, task health)
