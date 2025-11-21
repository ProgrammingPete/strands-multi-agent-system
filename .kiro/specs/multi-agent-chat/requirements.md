# Requirements Document

## Introduction

This specification defines the integration of a multi-agent AI system into Canvalo's existing chat bar interface. The system will replace the current mock AI responses with a sophisticated multi-agent architecture where specialized agents handle different business domains (invoicing, scheduling, project management, etc.). The agents will have access to real business data through the existing Supabase API and can perform actions on behalf of the user.

## Glossary

- **Multi-Agent System**: An AI architecture where multiple specialized agents collaborate to handle different aspects of user requests
- **Agent**: A specialized AI component responsible for a specific business domain (e.g., Invoice Agent, Project Agent)
- **Supervisor Agent**: The central coordinator that routes user requests to appropriate agents and manages agent collaboration
- **Tool**: A function that an agent can execute to interact with the system (e.g., create invoice, fetch project data)
- **Context**: Business data and conversation history available to agents for decision-making
- **Chat Bar**: The existing bottom bar UI component that handles user interactions
- **LLM**: Large Language Model (e.g., GPT-4, Claude) that powers agent reasoning
- **Streaming Response**: Real-time token-by-token delivery of AI responses to the UI

## Requirements

### Requirement 1: Migration from Existing Multi-Agent System

**User Story:** As a developer, I want to migrate from the existing AWS-focused multi-agent system to a new Canvalo-focused system, so that the agents align with the frontend business domain.

#### Acceptance Criteria

1. WHEN migrating the system THEN the existing Orchestrator Agent SHALL be renamed to Supervisor Agent
2. WHEN removing old agents THEN the system SHALL delete the Coder Agent, Alarm Manager Agent, AWS Researcher Agent, and AWS Manager Agent
3. WHEN preserving existing functionality THEN the Supervisor Agent routing logic SHALL be retained and adapted for new agents
4. WHEN the migration is complete THEN the system SHALL contain only the Supervisor Agent and the new business domain agents
5. WHEN the system initializes THEN the Supervisor Agent SHALL verify all old agent references are removed from the codebase

### Requirement 2: Agent Architecture

**User Story:** As a system architect, I want a modular multi-agent architecture, so that different business domains can be handled by specialized agents with clear responsibilities.

#### Acceptance Criteria

1. WHEN the system initializes THEN the Supervisor Agent SHALL create specialized agents for each business domain (invoices, appointments, projects, proposals, contacts, reviews, campaigns, tasks, settings)
2. WHEN a user message is received THEN the Supervisor Agent SHALL analyze the intent and route to the appropriate agent(s)
3. WHEN multiple agents are needed THEN the Supervisor Agent SHALL coordinate their collaboration and merge responses
4. WHEN an agent completes a task THEN the Supervisor Agent SHALL return control and allow other agents to contribute
5. WHERE an agent requires data THEN the agent SHALL have access to relevant Supabase API endpoints through defined tools

### Requirement 3: Invoice Agent

**User Story:** As a painting contractor, I want an AI agent that understands invoicing, so that I can create, view, update, and send invoices through natural conversation.

#### Acceptance Criteria

1. WHEN a user requests invoice creation THEN the Invoice Agent SHALL collect required information (client, items, dates) through conversational prompts
2. WHEN invoice data is complete THEN the Invoice Agent SHALL call the Supabase API to create the invoice record
3. WHEN a user asks about invoice status THEN the Invoice Agent SHALL fetch and summarize invoice data from the database
4. WHEN a user requests invoice modifications THEN the Invoice Agent SHALL update the existing invoice through the API
5. WHEN displaying invoice information THEN the Invoice Agent SHALL format currency, dates, and line items in a readable manner

### Requirement 4: Appointment Agent

**User Story:** As a painting contractor, I want an AI agent that manages my calendar, so that I can schedule, reschedule, and view appointments conversationally.

#### Acceptance Criteria

1. WHEN a user requests appointment scheduling THEN the Appointment Agent SHALL collect client name, date, time, location, and notes
2. WHEN checking availability THEN the Appointment Agent SHALL query existing appointments to identify conflicts
3. WHEN an appointment conflict exists THEN the Appointment Agent SHALL suggest alternative times
4. WHEN a user requests appointment changes THEN the Appointment Agent SHALL update the appointment through the API
5. WHEN displaying appointments THEN the Appointment Agent SHALL format dates and times in a user-friendly manner

### Requirement 5: Project Agent

**User Story:** As a painting contractor, I want an AI agent that tracks my projects, so that I can manage project status, tasks, budgets, and crew assignments through conversation.

#### Acceptance Criteria

1. WHEN a user creates a project THEN the Project Agent SHALL collect all required project details (client, type, dates, budget, materials, crew)
2. WHEN a user asks about project status THEN the Project Agent SHALL fetch project data and calculate progress metrics
3. WHEN a user updates project tasks THEN the Project Agent SHALL modify task completion status through the API
4. WHEN displaying project information THEN the Project Agent SHALL show progress percentages, budget utilization, and task completion
5. WHEN a user requests project analytics THEN the Project Agent SHALL trigger the stat data overlay with relevant charts

### Requirement 6: Proposal Agent

**User Story:** As a painting contractor, I want an AI agent that helps create proposals, so that I can build professional proposals with sections and pricing through conversation.

#### Acceptance Criteria

1. WHEN a user starts a proposal THEN the Proposal Agent SHALL guide through sections, items, pricing, and terms
2. WHEN calculating proposal totals THEN the Proposal Agent SHALL sum all section items and display the total cost
3. WHEN a user modifies proposal sections THEN the Proposal Agent SHALL update the proposal structure through the API
4. WHEN displaying proposals THEN the Proposal Agent SHALL format sections, line items, and totals clearly
5. WHEN a proposal is complete THEN the Proposal Agent SHALL offer to send or save the proposal

### Requirement 7: Contact Agent

**User Story:** As a painting contractor, I want an AI agent that manages my contacts, so that I can add, search, and update client and supplier information conversationally.

#### Acceptance Criteria

1. WHEN a user adds a contact THEN the Contact Agent SHALL collect name, email, phone, company, address, type, and notes
2. WHEN a user searches contacts THEN the Contact Agent SHALL query the database and return matching results
3. WHEN displaying contact information THEN the Contact Agent SHALL format contact details with appropriate labels
4. WHEN a user updates contact details THEN the Contact Agent SHALL modify the contact record through the API
5. WHEN a user requests contact analytics THEN the Contact Agent SHALL summarize contact counts by type (clients, leads, suppliers, contractors)

### Requirement 8: Review Agent

**User Story:** As a painting contractor, I want an AI agent that manages customer reviews, so that I can view, respond to, and request reviews through conversation.

#### Acceptance Criteria

1. WHEN a user asks about reviews THEN the Review Agent SHALL fetch and summarize review data including ratings and platforms
2. WHEN a user wants to respond to a review THEN the Review Agent SHALL draft a professional response for approval
3. WHEN a user requests review analytics THEN the Review Agent SHALL calculate average ratings and sentiment trends
4. WHEN displaying reviews THEN the Review Agent SHALL show customer name, rating, comment, date, and platform
5. WHEN a user wants to request reviews THEN the Review Agent SHALL identify recent completed projects and suggest clients to contact

### Requirement 9: Campaign Agent

**User Story:** As a painting contractor, I want an AI agent that manages marketing campaigns, so that I can create, schedule, and track email and SMS campaigns conversationally.

#### Acceptance Criteria

1. WHEN a user creates a campaign THEN the Campaign Agent SHALL collect name, type (email/SMS), content, audience, and schedule
2. WHEN a user asks about campaign performance THEN the Campaign Agent SHALL fetch and display open rates, click rates, and recipient counts
3. WHEN displaying campaigns THEN the Campaign Agent SHALL show status (draft, scheduled, active, completed) with appropriate formatting
4. WHEN a user modifies campaign content THEN the Campaign Agent SHALL update the campaign through the API
5. WHEN a user requests campaign analytics THEN the Campaign Agent SHALL trigger the stat data overlay with performance charts

### Requirement 10: Tasks Agent

**User Story:** As a painting contractor, I want an AI agent that manages my tasks and to-do items, so that I can track work items, set priorities, and mark tasks complete through conversation.

#### Acceptance Criteria

1. WHEN a user creates a task THEN the Tasks Agent SHALL collect task description, priority, due date, project association, and assignee
2. WHEN a user requests task lists THEN the Tasks Agent SHALL fetch and display tasks filtered by status, priority, or project
3. WHEN a user marks a task complete THEN the Tasks Agent SHALL update the task status through the API
4. WHEN displaying tasks THEN the Tasks Agent SHALL show priority indicators, due dates, and completion status
5. WHEN a user requests task analytics THEN the Tasks Agent SHALL calculate completion rates and overdue task counts

### Requirement 11: Settings Agent

**User Story:** As a business owner, I want an AI agent that manages system settings and business goals, so that I can configure preferences and track business objectives conversationally.

#### Acceptance Criteria

1. WHEN a user requests settings changes THEN the Settings Agent SHALL update user preferences, notification settings, or business configuration
2. WHEN a user sets business goals THEN the Settings Agent SHALL store goal targets (revenue, projects, client acquisition) with timeframes
3. WHEN a user asks about goal progress THEN the Settings Agent SHALL calculate current performance against targets
4. WHEN displaying settings THEN the Settings Agent SHALL show current configuration with clear labels and values
5. WHEN a user requests business analytics THEN the Settings Agent SHALL summarize overall business performance metrics

### Requirement 12: Supervisor Agent Routing

**User Story:** As a painting contractor, I want my queries routed to the right business specialist, so that I get accurate responses for different types of painting business operations.

#### Acceptance Criteria

1. WHEN a user asks about client contacts or customers THEN the Supervisor Agent SHALL route the query to the Contacts Agent
2. WHEN a user asks about painting projects or job details THEN the Supervisor Agent SHALL route the query to the Projects Agent
3. WHEN a user asks about scheduling or appointments THEN the Supervisor Agent SHALL route the query to the Appointments Agent
4. WHEN a user asks about proposals or estimates THEN the Supervisor Agent SHALL route the query to the Proposals Agent
5. WHEN a user asks about invoices or billing THEN the Supervisor Agent SHALL route the query to the Invoices Agent
6. WHEN a user asks about reviews or customer feedback THEN the Supervisor Agent SHALL route the query to the Reviews Agent
7. WHEN a user asks about marketing or promotional campaigns THEN the Supervisor Agent SHALL route the query to the Campaign Agent
8. WHEN a user asks about tasks or to-do items THEN the Supervisor Agent SHALL route the query to the Tasks Agent
9. WHEN a user asks about settings, goals, or configuration THEN the Supervisor Agent SHALL route the query to the Settings Agent
10. WHEN routing occurs THEN the Supervisor Agent SHALL pass the original query unchanged to the selected agent
11. WHEN an agent responds THEN the Supervisor Agent SHALL return the response without modification
12. WHEN a user request involves multiple domains THEN the Supervisor Agent SHALL identify all relevant agents and coordinate their execution
13. WHEN a user request is ambiguous THEN the Supervisor Agent SHALL ask clarifying questions before routing to agents

### Requirement 13: Tool Execution

**User Story:** As a system, I want agents to execute actions through well-defined tools, so that all API interactions are safe, validated, and auditable.

#### Acceptance Criteria

1. WHEN an agent needs to read data THEN the agent SHALL use GET tools that query the Supabase API
2. WHEN an agent needs to create data THEN the agent SHALL use POST tools that validate input before API calls
3. WHEN an agent needs to update data THEN the agent SHALL use PUT tools that verify record existence before modification
4. WHEN an agent needs to delete data THEN the agent SHALL use DELETE tools that confirm user intent before execution
5. WHEN a tool execution fails THEN the agent SHALL receive the error message and explain the issue to the user

### Requirement 14: Streaming Responses

**User Story:** As a user, I want to see AI responses appear in real-time, so that I know the system is working and can read responses as they're generated.

#### Acceptance Criteria

1. WHEN an agent generates a response THEN the Chat Bar SHALL display tokens as they stream from the LLM
2. WHEN streaming is active THEN the Chat Bar SHALL show a typing indicator or cursor
3. WHEN streaming completes THEN the Chat Bar SHALL mark the message as final and enable user input
4. WHEN streaming is interrupted THEN the Chat Bar SHALL display the partial response and indicate the interruption
5. WHEN voice mode is active THEN the system SHALL wait for complete response before speaking

### Requirement 15: Context Management

**User Story:** As a user, I want the AI to remember our conversation history, so that I can refer to previous topics without repeating information.

#### Acceptance Criteria

1. WHEN a conversation starts THEN the system SHALL initialize an empty context with user profile information
2. WHEN messages are exchanged THEN the system SHALL append messages to the conversation context
3. WHEN context exceeds token limits THEN the system SHALL summarize older messages to maintain recent context
4. WHEN a user references previous information THEN agents SHALL access conversation history to resolve references
5. WHEN a user starts a new topic THEN the system SHALL maintain context but allow topic transitions

### Requirement 16: Error Handling

**User Story:** As a user, I want clear error messages when things go wrong, so that I understand what happened and how to proceed.

#### Acceptance Criteria

1. WHEN an API call fails THEN the agent SHALL explain the error in user-friendly language
2. WHEN an LLM request fails THEN the system SHALL retry with exponential backoff up to 3 attempts
3. WHEN network connectivity is lost THEN the system SHALL queue messages and notify the user
4. WHEN an agent encounters invalid data THEN the agent SHALL explain what's wrong and request corrections
5. WHEN the system is unavailable THEN the Chat Bar SHALL display a maintenance message and disable input

### Requirement 17: Voice Integration

**User Story:** As a user, I want voice mode to work seamlessly with the multi-agent system, so that I can have natural spoken conversations with specialized agents.

#### Acceptance Criteria

1. WHEN voice mode is active THEN the system SHALL transcribe speech and send to the Supervisor Agent
2. WHEN an agent responds in voice mode THEN the system SHALL speak the complete response using text-to-speech
3. WHEN voice mode is active THEN the system SHALL disable streaming and wait for complete responses
4. WHEN multiple agents contribute in voice mode THEN the system SHALL merge responses before speaking
5. WHEN voice recognition fails THEN the system SHALL explain the issue and offer to retry

### Requirement 18: Analytics Integration

**User Story:** As a user, I want agents to display analytics and charts when relevant, so that I can visualize data without leaving the conversation.

#### Acceptance Criteria

1. WHEN a user requests analytics THEN the relevant agent SHALL trigger the stat data overlay with appropriate charts
2. WHEN displaying analytics THEN the agent SHALL provide a summary explanation of the data
3. WHEN analytics are shown THEN the Chat Bar SHALL expand to accommodate the charts
4. WHEN a user closes analytics THEN the Chat Bar SHALL return to normal chat mode
5. WHEN multiple analytics are requested THEN the agent SHALL allow navigation between different stat views

### Requirement 19: Configuration and Deployment

**User Story:** As a developer, I want the multi-agent system to be configurable and deployable, so that I can adjust agent behavior and deploy to production.

#### Acceptance Criteria

1. WHEN the system initializes THEN configuration SHALL be loaded from environment variables (API keys, endpoints, model names)
2. WHEN deploying to production THEN the system SHALL use secure credential management for API keys
3. WHEN agent prompts are updated THEN the system SHALL reload agent configurations without redeployment
4. WHEN monitoring system health THEN the system SHALL log agent interactions, tool calls, and errors
5. WHEN rate limits are reached THEN the system SHALL queue requests and notify users of delays

### Requirement 20: Security and Privacy

**User Story:** As a business owner, I want my data to be secure and private, so that sensitive business information is protected.

#### Acceptance Criteria

1. WHEN sending data to LLM providers THEN the system SHALL use encrypted connections (HTTPS/TLS)
2. WHEN storing conversation history THEN the system SHALL encrypt sensitive data at rest
3. WHEN accessing Supabase APIs THEN the system SHALL use authenticated requests with proper authorization
4. WHEN logging interactions THEN the system SHALL redact sensitive information (passwords, API keys, personal data)
5. WHEN a user requests data deletion THEN the system SHALL remove all conversation history and cached data

### Requirement 21: Performance and Scalability

**User Story:** As a user, I want fast AI responses, so that conversations feel natural and responsive.

#### Acceptance Criteria

1. WHEN a user sends a message THEN the Supervisor Agent SHALL route to agents within 100ms
2. WHEN an agent queries the database THEN the response SHALL return within 500ms
3. WHEN streaming responses THEN the first token SHALL appear within 2 seconds
4. WHEN multiple users are active THEN the system SHALL handle concurrent requests without degradation
5. WHEN system load is high THEN the system SHALL queue requests and display wait times to users
