# Backend Documentation Index

Welcome to the Canvalo FastAPI Backend documentation.

## Getting Started

- **[Quick Start Guide](QUICK_START.md)** - Get up and running in 5 minutes
  - Installation
  - Configuration
  - Running the server
  - Testing

## Reference Documentation

- **[API Reference](API_REFERENCE.md)** - Complete reference
  - Architecture overview
  - API endpoints
  - Configuration options
  - Error handling
  - Deployment guide
  - Security considerations

## Implementation Notes

- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Task 15 completion details
  - What was implemented
  - Files created
  - Requirements validation
  - Testing results
  - Architecture decisions

- **[Context Management](CONTEXT_MANAGEMENT.md)** - Task 16 completion details
  - Context building and formatting
  - Token limit management
  - Context summarization
  - Message persistence
  - Testing and validation

- **[Performance Optimization](PERFORMANCE_OPTIMIZATION.md)** - Task 23 completion details
  - Database query optimization with indexes
  - Streaming latency optimization
  - Pagination support for conversations and messages
  - Token batching for reduced SSE overhead

## Security

- **[Security Guide](SECURITY.md)** - Production security implementation
  - Row Level Security (RLS) policies
  - JWT authentication
  - User-scoped database clients
  - Environment configuration (development vs production)
  - Production configuration validation
  - Admin operation authentication
  - Security best practices

## Testing

- **[Tests README](../../tests/README.md)** - Test documentation
  - Unit tests for agents and tools
  - Integration tests for Supabase
  - End-to-end tests for the complete system
  - Running tests locally

- **[UV Migration Guide](UV_MIGRATION.md)** - Package manager migration
  - Command changes
  - Benefits of using UV
  - Quick reference

## Quick Links

### For Developers
1. Start here: [Quick Start Guide](QUICK_START.md)
2. Understand the architecture: [API Reference - Architecture](API_REFERENCE.md#architecture)
3. Learn about error handling: [API Reference - Error Handling](API_REFERENCE.md#error-handling)

### For DevOps
1. Deployment guide: [API Reference - Deployment](API_REFERENCE.md#deployment)
2. Configuration: [API Reference - Configuration](API_REFERENCE.md#configuration)
3. Monitoring: [API Reference - Monitoring](API_REFERENCE.md#monitoring)

### For Project Managers
1. Implementation summary: [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
2. Requirements validation: [Implementation Summary - Requirements](IMPLEMENTATION_SUMMARY.md#requirements-validation)
3. Testing results: [Implementation Summary - Testing](IMPLEMENTATION_SUMMARY.md#testing)

## Document Organization

```
docs/
├── INDEX.md                      # This file - documentation index
├── QUICK_START.md               # Quick start guide (5 min read)
├── README.md                    # Full documentation (30 min read)
├── API_REFERENCE.md             # API endpoints and usage (15 min read)
├── SECURITY.md                  # Production security guide (10 min read)
├── IMPLEMENTATION_SUMMARY.md    # Task 15 summary (10 min read)
├── CONTEXT_MANAGEMENT.md        # Task 16 summary (15 min read)
├── PERFORMANCE_OPTIMIZATION.md  # Task 23 summary (10 min read)
├── UV_MIGRATION.md              # UV migration notes (5 min read)
└── ORGANIZATION.md              # Documentation structure guide (3 min read)
```

See [ORGANIZATION.md](ORGANIZATION.md) for details on how documentation is structured.

## Need Help?

1. Check the [Quick Start Guide](QUICK_START.md) for common issues
2. Review the [Full Documentation](README.md) for detailed information
3. Check the implementation notes for architecture decisions
4. Contact the development team

## Contributing

When updating documentation:
1. Keep the Quick Start Guide concise (< 200 lines)
2. Add detailed information to the Full Documentation
3. Update this index when adding new documents
4. Use clear headings and code examples
