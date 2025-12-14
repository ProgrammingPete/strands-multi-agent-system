# Requirements Document

## Introduction

This specification addresses the critical security vulnerabilities in the multi-agent system's current implementation, which uses a Supabase secret key that bypasses Row Level Security (RLS). The system must be migrated to a production-ready architecture that enforces user data isolation through RLS policies and user-scoped authentication. This ensures that users can only access their own data, adhering to the principle of least privilege and meeting production security standards.

## Glossary

- **RLS (Row Level Security)**: PostgreSQL feature that restricts which rows users can access in database tables based on policies
- **JWT (JSON Web Token)**: Cryptographically signed token containing user identity and claims
- **Supabase Client**: SDK client for interacting with Supabase backend services
- **Secret Key**: Administrative API key that bypasses all RLS policies (service_role key)
- **Anon Key**: Public API key that respects RLS policies (publishable key)
- **User-Scoped Client**: Supabase client configured with a user's JWT to enforce RLS
- **Backend API**: FastAPI server that processes agent requests and interacts with Supabase
- **Frontend Application**: React application that sends user requests to the Backend API
- **Agent Tools**: Python functions decorated with @tool that perform operations on behalf of users
- **Auth Middleware**: Code layer that validates JWTs and creates user-scoped clients
- **System User**: Special user account used for testing and system operations

## Requirements

### Requirement 1

**User Story:** As a system architect, I want to implement user-scoped authentication, so that all database operations respect Row Level Security policies and users can only access their own data.

#### Acceptance Criteria

1. WHEN the Backend API receives a request THEN the system SHALL validate the user JWT token before processing
2. WHEN creating a Supabase client for user operations THEN the system SHALL use the pub key with the user's JWT token
3. WHEN a user JWT is invalid or expired THEN the system SHALL reject the request and return an authentication error
4. WHEN the Backend API makes database queries THEN the system SHALL use user-scoped clients that enforce RLS policies
5. WHERE user authentication is required THEN the system SHALL extract the user_id from the validated JWT

### Requirement 2

**User Story:** As a database administrator, I want to add user_id columns and RLS policies to all data tables, so that data isolation is enforced at the database level.

#### Acceptance Criteria

1. WHEN the api schema tables are modified THEN the system SHALL add user_id columns to invoices, projects, appointments, proposals, contacts, reviews, campaigns, tasks, and goals tables
2. WHEN user_id columns are added THEN the system SHALL create foreign key references to auth.users(id)
3. WHEN RLS is enabled on data tables THEN the system SHALL enforce policies for SELECT, INSERT, UPDATE, and DELETE operations
4. WHEN a user queries any data table THEN the system SHALL return only rows where user_id matches auth.uid()
5. WHEN a user attempts to insert a record THEN the system SHALL verify that the user_id matches auth.uid()
6. WHEN a user attempts to update or delete a record THEN the system SHALL verify that the user_id matches auth.uid()
7. WHERE performance optimization is needed THEN the system SHALL create indexes on all user_id columns
8. WHEN existing data is present THEN the system SHALL backfill user_id values before making the column NOT NULL

### Requirement 3

**User Story:** As a database administrator, I want to grant proper schema permissions to all Postgres roles, so that authenticated users and service roles can access the api schema.

#### Acceptance Criteria

1. WHEN the api schema is accessed THEN the system SHALL grant USAGE permission to authenticated, anon, and service_role roles
2. WHEN tables in the api schema are accessed THEN the system SHALL grant appropriate permissions to authenticated, anon, and service_role roles
3. WHEN sequences in the api schema are accessed THEN the system SHALL grant ALL permissions to authenticated, anon, and service_role roles
4. WHEN functions in the api schema are accessed THEN the system SHALL grant ALL permissions to authenticated, anon, and service_role roles
5. WHERE permission errors occur THEN the system SHALL provide clear error messages indicating the missing permission

### Requirement 4

**User Story:** As a backend developer, I want to refactor all agent tools to use user JWTs instead of the secret key, so that all operations are user-scoped and secure.

#### Acceptance Criteria

1. WHEN an agent tool is invoked THEN the system SHALL receive the user_id parameter
2. WHEN an agent tool creates a Supabase client THEN the system SHALL use the create_user_scoped_client function with the user JWT
3. WHEN agent tools query data THEN the system SHALL rely on RLS policies for filtering instead of manual user_id filtering
4. WHEN the Backend API processes agent requests THEN the system SHALL extract user_id from the JWT and pass it to all agent tool invocations
5. WHERE the secret key was previously used THEN the system SHALL replace it with user-scoped client creation
6. WHEN invoice_tools are updated THEN the system SHALL remove the SYSTEM_USER_ID fallback and require user_id parameter

### Requirement 5

**User Story:** As a frontend developer, I want to send user JWT tokens to the backend, so that the backend can perform user-scoped operations.

#### Acceptance Criteria

1. WHEN a user sends a message to the agent THEN the Frontend Application SHALL retrieve the user's session token from Supabase Auth
2. WHEN the Frontend Application makes API requests THEN the system SHALL include the JWT in the Authorization header
3. WHEN a user is not authenticated THEN the Frontend Application SHALL prevent API requests and display an authentication error
4. WHEN the user session expires THEN the Frontend Application SHALL refresh the token or prompt for re-authentication
5. WHERE API calls are made to the Backend API THEN the system SHALL include the Bearer token in all requests

### Requirement 6

**User Story:** As a security engineer, I want to remove the secret key from production environments, so that administrative privileges cannot be misused.

#### Acceptance Criteria

1. WHEN deploying to production THEN the system SHALL not include the SUPABASE_SERVICE_KEY environment variable
2. WHEN the Backend API starts in production mode THEN the system SHALL verify that only the pub key is configured
3. WHERE the secret key is needed THEN the system SHALL restrict its use to admin-only operations with separate authentication
4. WHEN admin operations are performed THEN the system SHALL validate admin credentials before using the secret key
5. WHERE testing or development environments are used THEN the system SHALL allow the secret key for system operations with SYSTEM_USER_ID

### Requirement 7

**User Story:** As a backend developer, I want to implement rate limiting on API endpoints, so that the system is protected from abuse and denial-of-service attacks.

#### Acceptance Criteria

1. WHEN a user makes API requests THEN the Backend API SHALL enforce a rate limit of 10 requests per minute per user
2. WHEN a user exceeds the rate limit THEN the Backend API SHALL return a 429 Too Many Requests error with a JSON error response
3. WHEN rate limiting is applied THEN the Backend API SHALL identify users by authenticated user_id for authenticated requests and by IP address for unauthenticated requests
4. WHERE rate limits are configured THEN the Backend API SHALL allow different limits for different endpoint types via configuration
5. WHEN rate limit errors occur THEN the Backend API SHALL include a retry-after header with the number of seconds until the limit resets

### Requirement 8

**User Story:** As a security auditor, I want comprehensive audit logging of all data access operations, so that security incidents can be investigated and compliance requirements met.

#### Acceptance Criteria

1. WHEN a user accesses data THEN the Backend API SHALL log the user_id, table name, operation type, timestamp, and request ID
2. WHEN audit logs are created THEN the Backend API SHALL include the request path, response status code, and execution duration
3. WHEN more than 5 authentication failures occur from the same IP address within 1 minute THEN the Backend API SHALL generate an alert for security review
4. WHERE audit logs are stored THEN the Backend API SHALL write logs to a structured logging system with append-only semantics
5. WHEN data operations fail THEN the Backend API SHALL log the failure reason, error code, and user context

### Requirement 9

**User Story:** As a QA engineer, I want a comprehensive testing strategy that validates security controls, so that the production system is verified to be secure before deployment.

#### Acceptance Criteria

1. WHEN testing user isolation THEN the Test Infrastructure SHALL verify that users cannot access other users' data
2. WHEN testing RLS policies THEN the Test Infrastructure SHALL confirm that all CRUD operations respect user_id filtering
3. WHEN testing JWT validation THEN the Test Infrastructure SHALL verify that invalid or expired tokens are rejected
4. WHEN testing with multiple users THEN the Test Infrastructure SHALL confirm complete data isolation between users
5. WHERE staging environments are used THEN the Test Infrastructure SHALL test with real user JWTs and enabled RLS policies
6. WHEN running batch tests THEN the Test Infrastructure SHALL use the SYSTEM_USER_ID for creating test data

### Requirement 10

**User Story:** As a database administrator, I want to execute the add_user_id_and_rls.sql migration script, so that the database schema is prepared for production with user_id columns and RLS policies.

#### Acceptance Criteria

1. WHEN the migration script is executed THEN the system SHALL add user_id columns to all api schema tables
2. WHEN the migration script is executed THEN the system SHALL create indexes on all user_id columns for performance
3. WHEN the migration script is executed THEN the system SHALL enable RLS on all api schema tables
4. WHEN the migration script is executed THEN the system SHALL create RLS policies for SELECT, INSERT, UPDATE, and DELETE operations
5. WHEN the migration script completes THEN the system SHALL run verification queries to confirm schema changes
6. WHERE existing data is present THEN the system SHALL provide options for backfilling user_id values
7. WHEN the migration script is run THEN the system SHALL display success messages and next steps for backend code updates

### Requirement 11

**User Story:** As a system administrator, I want a phased migration plan, so that the transition to production security can be executed safely without data loss or downtime.

#### Acceptance Criteria

1. WHEN migrating the database schema THEN the system SHALL execute the add_user_id_and_rls.sql script in the Supabase SQL Editor
2. WHEN backfilling existing data THEN the system SHALL choose between system user assignment or first user assignment
3. WHEN enabling RLS policies THEN the system SHALL verify that all policies are correct before making user_id columns NOT NULL
4. WHEN updating backend code THEN the system SHALL deploy changes in a way that maintains backward compatibility during migration
5. WHERE rollback is needed THEN the system SHALL have procedures to safely revert changes at each migration phase

### Requirement 12

**User Story:** As a test engineer, I want test infrastructure that supports mock users and system users, so that tests can validate security controls without requiring real user accounts.

#### Acceptance Criteria

1. WHEN running batch tests THEN the system SHALL use a designated SYSTEM_USER_ID environment variable for test data operations
2. WHEN creating test fixtures THEN the system SHALL associate test data with the system user account
3. WHEN testing agent tools THEN the system SHALL pass user_id parameters to all tool invocations
4. WHEN running integration tests THEN the system SHALL verify that RLS policies correctly isolate data between test users
5. WHERE test cleanup is required THEN the system SHALL track created test data and remove it after test completion
6. WHEN the invoices table has user_id column THEN the system SHALL update get_invoices tool to filter by user_id
7. WHEN the invoices table has user_id column THEN the system SHALL update create_invoice tool to set user_id on new records

### Requirement 13

**User Story:** As a backend developer, I want a centralized Supabase client factory, so that all database connections use the correct authentication method based on the environment.

#### Acceptance Criteria

1. WHEN creating a Supabase client for user operations THEN the system SHALL accept a user JWT parameter
2. WHEN a user JWT is provided THEN the system SHALL create a client with the pub key and user JWT in the Authorization header
3. WHEN no user JWT is provided in development mode THEN the system SHALL use the secret key for system operations
4. WHEN the application starts THEN the system SHALL verify the configured Supabase key type and log warnings for incorrect keys
5. WHERE the secret key is used THEN the system SHALL log a warning that RLS policies are bypassed

### Requirement 14

**User Story:** As a DevOps engineer, I want monitoring and alerting for security events, so that unauthorized access attempts and security violations are detected immediately.

#### Acceptance Criteria

1. WHEN unauthorized access is attempted THEN the Backend API SHALL log the attempt with user context and generate an alert
2. WHEN more than 10 authentication failures occur from the same user_id or IP address within 5 minutes THEN the Backend API SHALL flag the activity as a potential brute-force attack
3. WHEN RLS policy violations are detected THEN the Backend API SHALL log the violation details including user_id, table, and attempted operation
4. WHERE monitoring is configured THEN the Backend API SHALL track authentication success rate, failure rate, and request latency metrics
5. WHEN authentication failure rate exceeds 20% over a 5-minute window THEN the Backend API SHALL trigger an automated alert
