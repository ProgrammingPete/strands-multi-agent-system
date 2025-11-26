# Implementation Plan

## Overview

This implementation plan breaks down the multi-agent chat integration into discrete, manageable tasks. Each task builds incrementally on previous work, with checkpoints to ensure tests pass before proceeding.

**Context Documents Available:**
- Requirements: `.kiro/specs/multi-agent-chat/requirements.md`
- Design: `.kiro/specs/multi-agent-chat/design.md`
- Database Schema: `src/supabase/functions/server/schema.sql`

---

## Phase 1: Database and Backend Foundation

- [x] 1. Set up database schema for AI chat
  - Run the updated schema.sql to create `api.agent_conversations` and `api.agent_messages` tables
  - Verify RLS policies are working correctly
  - Test triggers for auto-updating conversation metadata
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Migrate existing multi-agent system
  - [x] 2.1 Rename orchestrator.py to supervisor.py in strands-multi-agent-system
    - Update all imports and references
    - Update system prompt to reflect new name
    - _Requirements: 1.1_
  
  - [x] 2.2 Remove old AWS-focused agents
    - Delete coder.py, alarm_manager.py, aws_researcher.py, aws_manager.py
    - Remove imports from supervisor.py
    - Verify no orphaned references remain
    - _Requirements: 1.2_
  
  - [x] 2.3 Update supervisor routing logic
    - Adapt existing routing patterns for business domain agents
    - Update system prompt with new agent descriptions
    - _Requirements: 1.3_

- [x] 3. Create Supabase tool utilities
  - [x] 3.1 Implement base Supabase client wrapper
    - Create Python module for Supabase client initialization
    - Add error handling and retry logic
    - Configure connection pooling
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_
  
  - [x] 3.2 Create generic CRUD tool generators
    - Implement get_records tool generator
    - Implement create_record tool generator
    - Implement update_record tool generator
    - Implement delete_record tool generator
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [x] 4. Checkpoint - Verify foundation
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 2: Specialized Agent Implementation

- [x] 5. Implement Invoices Agent
  - [x] 5.1 Create invoices_agent.py with system prompt
    - Define agent with invoicing expertise
    - Configure with Bedrock model
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 5.2 Implement Supabase tools for invoices
    - get_invoices tool
    - create_invoice tool
    - update_invoice tool
    - delete_invoice tool
    - _Requirements: 3.2, 3.4_
  
  - [x] 5.3 Add invoices agent to supervisor
    - Import invoices_agent_tool
    - Add to supervisor's tools list
    - Update routing logic
    - _Requirements: 12.5_

- [ ] 6. Implement Appointments Agent
  - [ ] 6.1 Create appointments_agent.py with system prompt
    - Define agent with scheduling expertise
    - Configure with Bedrock model
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [ ] 6.2 Implement Supabase tools for appointments
    - get_appointments tool
    - create_appointment tool
    - update_appointment tool
    - delete_appointment tool
    - check_availability tool
    - _Requirements: 4.2, 4.4_
  
  - [ ] 6.3 Add appointments agent to supervisor
    - Import appointments_agent_tool
    - Add to supervisor's tools list
    - Update routing logic
    - _Requirements: 12.3_

- [ ] 7. Implement Projects Agent
  - [ ] 7.1 Create projects_agent.py with system prompt
    - Define agent with project management expertise
    - Configure with Bedrock model
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ] 7.2 Implement Supabase tools for projects
    - get_projects tool
    - create_project tool
    - update_project tool
    - delete_project tool
    - get_project_analytics tool
    - _Requirements: 5.2, 5.3_
  
  - [ ] 7.3 Add projects agent to supervisor
    - Import projects_agent_tool
    - Add to supervisor's tools list
    - Update routing logic
    - _Requirements: 12.2_

- [ ] 8. Implement Proposals Agent
  - [ ] 8.1 Create proposals_agent.py with system prompt
    - Define agent with proposal creation expertise
    - Configure with Bedrock model
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ] 8.2 Implement Supabase tools for proposals
    - get_proposals tool
    - create_proposal tool
    - update_proposal tool
    - delete_proposal tool
    - calculate_totals tool
    - _Requirements: 6.2, 6.3_
  
  - [ ] 8.3 Add proposals agent to supervisor
    - Import proposals_agent_tool
    - Add to supervisor's tools list
    - Update routing logic
    - _Requirements: 12.4_

- [ ] 9. Implement Contacts Agent
  - [ ] 9.1 Create contacts_agent.py with system prompt
    - Define agent with contact management expertise
    - Configure with Bedrock model
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ] 9.2 Implement Supabase tools for contacts
    - get_contacts tool
    - create_contact tool
    - update_contact tool
    - delete_contact tool
    - search_contacts tool
    - _Requirements: 7.2, 7.4_
  
  - [ ] 9.3 Add contacts agent to supervisor
    - Import contacts_agent_tool
    - Add to supervisor's tools list
    - Update routing logic
    - _Requirements: 12.1_

- [ ] 10. Implement Reviews Agent
  - [ ] 10.1 Create reviews_agent.py with system prompt
    - Define agent with review management expertise
    - Configure with Bedrock model
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [ ] 10.2 Implement Supabase tools for reviews
    - get_reviews tool
    - create_review_response tool
    - request_review tool
    - get_review_analytics tool
    - _Requirements: 8.1, 8.2_
  
  - [ ] 10.3 Add reviews agent to supervisor
    - Import reviews_agent_tool
    - Add to supervisor's tools list
    - Update routing logic
    - _Requirements: 12.6_

- [ ] 11. Implement Campaign Agent
  - [ ] 11.1 Create campaigns_agent.py with system prompt
    - Define agent with marketing campaign expertise
    - Configure with Bedrock model
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [ ] 11.2 Implement Supabase tools for campaigns
    - get_campaigns tool
    - create_campaign tool
    - update_campaign tool
    - delete_campaign tool
    - get_campaign_analytics tool
    - _Requirements: 9.2, 9.4_
  
  - [ ] 11.3 Add campaigns agent to supervisor
    - Import campaigns_agent_tool
    - Add to supervisor's tools list
    - Update routing logic
    - _Requirements: 12.7_

- [ ] 12. Implement Tasks Agent
  - [ ] 12.1 Create tasks_agent.py with system prompt
    - Define agent with task management expertise
    - Configure with Bedrock model
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ] 12.2 Implement Supabase tools for tasks
    - get_tasks tool
    - create_task tool
    - update_task tool
    - delete_task tool
    - get_task_analytics tool
    - _Requirements: 10.2, 10.3_
  
  - [ ] 12.3 Add tasks agent to supervisor
    - Import tasks_agent_tool
    - Add to supervisor's tools list
    - Update routing logic
    - _Requirements: 12.8_

- [ ] 13. Implement Settings Agent
  - [ ] 13.1 Create settings_agent.py with system prompt
    - Define agent with settings and goals expertise
    - Configure with Bedrock model
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [ ] 13.2 Implement Supabase tools for settings
    - get_settings tool
    - update_settings tool
    - get_goals tool
    - update_goals tool
    - get_business_analytics tool
    - _Requirements: 11.1, 11.3_
  
  - [ ] 13.3 Add settings agent to supervisor
    - Import settings_agent_tool
    - Add to supervisor's tools list
    - Update routing logic
    - _Requirements: 12.9_

- [ ] 14. Checkpoint - Verify all agents
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 3: Backend API and Streaming

- [x] 15. Create FastAPI backend service
  - [x] 15.1 Set up FastAPI application structure
    - Create main.py with FastAPI app
    - Configure CORS for frontend
    - Set up environment configuration
    - _Requirements: 19.1, 19.2_
  
  - [x] 15.2 Implement chat endpoint with SSE streaming
    - Create POST /api/chat/stream endpoint
    - Implement SSE response streaming
    - Handle supervisor agent invocation
    - Stream tokens as they're generated
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_
  
  - [x] 15.3 Implement conversation management endpoints
    - GET /api/conversations - list user conversations
    - POST /api/conversations - create new conversation
    - GET /api/conversations/:id - get conversation with messages
    - DELETE /api/conversations/:id - delete conversation
    - _Requirements: 15.1, 15.2_
  
  - [x] 15.4 Add error handling and retry logic
    - Implement exponential backoff for LLM failures
    - Add user-friendly error messages
    - Handle network errors gracefully
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [x] 16. Implement context management
  - [x] 16.1 Create context builder utility
    - Load conversation history from database
    - Format messages for LLM context
    - Add user profile information
    - _Requirements: 15.1, 15.2_
  
  - [x] 16.2 Implement context summarization
    - Detect when context exceeds token limits
    - Summarize older messages
    - Preserve recent messages
    - _Requirements: 15.3_
  
  - [x] 16.3 Add context persistence
    - Save messages to database after each exchange
    - Update conversation metadata
    - _Requirements: 15.2_

- [x] 17. Checkpoint - Verify backend
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 4: Frontend Integration

- [x] 18. Create AgentService for frontend
  - [x] 18.1 Implement AgentService class
    - Create src/services/AgentService.ts
    - Implement sendMessage with SSE handling
    - Implement sendVoiceMessage
    - Add conversation management methods
    - _Requirements: 14.1, 14.2, 14.3_
  
  - [x] 18.2 Add error handling and retries
    - Implement retry logic with exponential backoff
    - Handle network errors
    - Display user-friendly error messages
    - _Requirements: 16.1, 16.2, 16.3_
  
  - [x] 18.3 Implement streaming response parser
    - Parse SSE chunks
    - Handle token, tool_call, complete, and error types
    - Update UI incrementally
    - _Requirements: 14.1, 14.2_

- [x] 19. Update BottomBar component
  - [x] 19.1 Integrate AgentService
    - Replace mock AI responses with AgentService calls
    - Handle streaming responses
    - Update message state incrementally
    - _Requirements: 14.1, 14.2, 14.3_
  
  - [x] 19.2 Add conversation persistence
    - Load conversation history on mount
    - Save new messages to backend
    - Handle conversation switching
    - _Requirements: 15.1, 15.2_
  
  - [x] 19.3 Update voice mode integration
    - Send voice transcripts to AgentService
    - Wait for complete response before TTS
    - Handle voice errors
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_
  
  - [x] 19.4 Add loading and error states
    - Show typing indicator during streaming
    - Display error messages
    - Handle interruptions
    - _Requirements: 14.2, 14.4, 16.1_

- [ ] 20. Implement analytics overlay integration
  - [ ] 20.1 Add analytics trigger detection
    - Detect when agents request analytics display
    - Parse analytics data from agent responses
    - _Requirements: 18.1, 18.2_
  
  - [ ] 20.2 Update statData prop handling
    - Pass analytics data to BottomBar
    - Trigger stat overlay display
    - Handle overlay close
    - _Requirements: 18.3, 18.4, 18.5_

- [x] 21. Checkpoint - Verify frontend integration
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 5: Testing and Polish

- [ ] 22. End-to-end testing
  - [ ] 22.1 Test basic chat flow
    - Send message and receive response
    - Verify streaming works correctly
    - Check message persistence
    - _Requirements: 14.1, 14.2, 14.3, 15.2_
  
  - [ ] 22.2 Test agent routing
    - Send queries for each business domain
    - Verify correct agent is invoked
    - Check response quality
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9_
  
  - [ ] 22.3 Test multi-agent coordination
    - Send queries requiring multiple agents
    - Verify responses are merged correctly
    - _Requirements: 12.12_
  
  - [ ] 22.4 Test voice mode
    - Activate voice mode
    - Send voice transcript
    - Verify TTS works
    - _Requirements: 17.1, 17.2, 17.3, 17.4_
  
  - [ ] 22.5 Test error scenarios
    - Network failures
    - API errors
    - Invalid data
    - LLM failures
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [ ] 23. Performance optimization
  - [ ] 23.1 Optimize database queries
    - Add missing indexes
    - Optimize conversation loading
    - _Requirements: 21.2_
  
  - [ ] 23.2 Optimize streaming
    - Tune chunk sizes
    - Minimize latency
    - _Requirements: 21.3_

- [ ] 24. Security audit
  - [ ] 24.1 Verify RLS policies
    - Test that users can only see their own data
    - Verify authentication is required
    - _Requirements: 20.3_
  
  - [ ] 24.2 Check data encryption
    - Verify HTTPS/TLS is used
    - Check sensitive data handling
    - _Requirements: 20.1, 20.2, 20.4_

- [ ] 25. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

---

## Phase 6: Deployment

- [ ] 26. Prepare for deployment
  - [ ] 26.1 Set up environment variables
    - Configure production API keys
    - Set up Supabase credentials
    - Configure Bedrock access
    - _Requirements: 19.1, 19.2_
  
  - [ ] 26.2 Set up logging and monitoring
    - Configure structured logging
    - Set up error tracking
    - Add performance monitoring
    - _Requirements: 19.4_
  
  - [ ] 26.3 Configure rate limiting
    - Implement per-user rate limits
    - Add queue for high load
    - _Requirements: 19.5_

- [ ] 27. Deploy backend
  - [ ] 27.1 Deploy FastAPI service
    - Deploy to production environment
    - Configure load balancer
    - Set up health checks
    - _Requirements: 19.1, 19.2_
  
  - [ ] 27.2 Verify deployment
    - Test all endpoints
    - Check streaming works
    - Verify error handling

- [ ] 28. Deploy frontend
  - [ ] 28.1 Build and deploy frontend
    - Build production bundle
    - Deploy to hosting
    - Update API URLs
    - _Requirements: 19.1_
  
  - [ ] 28.2 Verify frontend deployment
    - Test chat functionality
    - Test voice mode
    - Check analytics overlay

- [ ] 29. Final verification
  - Ensure all tests pass, ask the user if questions arise.
