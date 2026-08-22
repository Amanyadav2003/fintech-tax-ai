# System Design & Architecture Patterns - Virtual Tax Professional

## Document Overview
Complete technical documentation covering system architecture, design patterns, integration architecture, and deployment considerations.

---

## Part 1: System Architecture

### 1.1 High-Level Architecture

The Virtual Tax Professional System follows a **Layered Architecture** pattern:

```
┌─────────────────────────────────────────────────────────┐
│              Frontend Layer (React)                      │
│    - Chat UI  - Auth UI  - Session Management          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│          API Gateway Layer (FastAPI/Uvicorn)            │
│    - REST Endpoints  - Request Validation  - Auth       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│           Agent Orchestration Layer                      │
│    - ChatAgent  - Router  - Intent Detector             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│         Specialized Agent Layer                         │
│   - GST Agent  - IncomeTax Agent  - Accounting Agent   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│         Backend Services Layer                          │
│   - User Service  - Chat Service  - Knowledge Base      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│         Data & Cache Layer                              │
│    - PostgreSQL  - Redis Cache  - File Storage          │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Component Responsibilities

#### Frontend Layer
- **React Application**: User interface for chat, authentication, dashboard
- **State Management**: Redux/Context for user state and chat history
- **Session Cache**: LocalStorage for tokens and session data
- **HTTP Client**: Axios for API communication

#### API Gateway
- **Route Registration**: Maps /api/* endpoints to handlers
- **Request Validation**: Validates request schemas
- **Authentication Middleware**: Verifies JWT tokens
- **Error Handling**: Centralized exception handling
- **CORS Management**: Handles cross-origin requests

#### Agent Orchestration
- **ChatAgent**: Main orchestrator that:
  - Parses incoming messages
  - Detects user intent (TRAINING vs EXECUTION)
  - Routes to appropriate specialized agent
  - Maintains conversation context
  - Formats final response

#### Specialized Agents
- **GST Agent**: Handles Goods & Services Tax queries
- **Income Tax Agent**: Manages Income Tax & tax planning
- **Accounting Agent**: Guides accounting & bookkeeping

#### Backend Services
- **User Service**: Registration, login, profile management
- **Chat Service**: Message storage and retrieval
- **Knowledge Base**: Topic retrieval and management

#### Data Layer
- **PostgreSQL**: Primary database (Users, Messages, Sessions)
- **Redis**: Caching and session management
- **File Storage**: Document storage for reports/exports

---

## Part 2: Design Patterns

### 2.1 Architectural Patterns

#### 1. **Agent Pattern**
Specialized agents handle domain-specific logic independently:
- Each agent (GST, IncomeTax, Accounting) operates autonomously
- Agents share common interfaces
- Easy to add new agent types

**Benefits**:
- Separation of concerns
- Easy to test individual agents
- Scalable architecture

#### 2. **Observer Pattern**
Used in chat message processing:
- Message sent → triggers handlers
- Handlers update context, save history, send to frontend

**Benefits**:
- Loose coupling
- Event-driven architecture
- Extensible event handling

#### 3. **Strategy Pattern**
Different response generation strategies based on user level:
- **Beginner**: Simple, step-by-step explanations
- **Intermediate**: Balanced detail with examples
- **Advanced**: Comprehensive, technical details

**Benefits**:
- Runtime strategy selection
- Easy to add new complexity levels

#### 4. **Chain of Responsibility Pattern**
Message processing chain:
```
Input Validation → Intent Detection → Module Routing 
→ Agent Processing → Response Formatting → DB Storage
```

**Benefits**:
- Clear processing pipeline
- Easy to add/remove processing steps
- Each step handles specific responsibility

#### 5. **Template Method Pattern**
Agent response generation:
```python
class Agent:
    def generate_response(self, query):
        content = self.retrieve_knowledge(query)
        formatted = self.format_by_level(content)
        enhanced = self.add_examples(formatted)
        return self.verify_compliance(enhanced)
```

#### 6. **Decorator Pattern**
Response enhancement:
- Base response + examples decorator
- Base response + compliance notes decorator
- Base response + formatting decorator

---

### 2.2 Service Patterns

#### 1. **Service Locator Pattern**
Central registry for services:
```python
class ServiceRegistry:
    services = {
        'user_service': UserService(),
        'chat_service': ChatService(),
        'kb_service': KnowledgeBaseService(),
    }
```

#### 2. **Dependency Injection Pattern**
Services injected into agents:
```python
class ChatAgent:
    def __init__(self, chat_service, kb_service, user_service):
        self.chat_service = chat_service
        self.kb_service = kb_service
        self.user_service = user_service
```

#### 3. **Repository Pattern**
Data access abstraction:
```python
class UserRepository:
    def find_by_id(self, user_id): ...
    def find_by_email(self, email): ...
    def save(self, user): ...
    def delete(self, user_id): ...
```

---

### 2.3 Behavioral Patterns

#### 1. **State Pattern**
Chat session states:
- **NEW**: User just logged in
- **ACTIVE**: User in conversation
- **CONTEXT_SET**: System has identified focus area
- **RESPONSE_PENDING**: Waiting for agent
- **COMPLETE**: Response sent

#### 2. **Mediator Pattern**
ChatAgent acts as mediator between user and specialized agents:
- Receives all user messages
- Coordinates between agents
- Manages communication

#### 3. **Iterator Pattern**
Traverse chat history:
```python
class ChatHistoryIterator:
    def get_recent_messages(self, user_id, limit=10):
        # Returns messages in reverse chronological order
```

---

## Part 3: Integration Architecture

### 3.1 API Endpoints

#### Authentication Endpoints
```
POST   /api/auth/register     → Register new user
POST   /api/auth/login        → Login user
POST   /api/auth/logout       → Logout user
POST   /api/auth/refresh      → Refresh token
GET    /api/auth/validate     → Validate current token
```

#### Chat Endpoints
```
POST   /api/tax/chat          → Send chat message
GET    /api/tax/chat/history  → Get chat history
GET    /api/tax/chat/context  → Get conversation context
DELETE /api/tax/chat/history  → Clear history
```

#### User Endpoints
```
GET    /api/user/profile      → Get user profile
PUT    /api/user/profile      → Update profile
GET    /api/user/preferences  → Get preferences
PUT    /api/user/preferences  → Update preferences
```

#### Knowledge Base Endpoints
```
GET    /api/kb/topics         → List all topics
GET    /api/kb/topics/:id     → Get topic details
GET    /api/kb/search         → Search knowledge base
```

### 3.2 Request/Response Schemas

#### Chat Request
```json
{
  "message": "How to register for GST?",
  "user_id": 123,
  "context_id": 456,
  "timestamp": "2026-05-12T10:30:00Z"
}
```

#### Chat Response
```json
{
  "message_id": 789,
  "response": "To register for GST, you need to...",
  "agent_type": "GST",
  "mode": "TRAINING",
  "confidence": 0.95,
  "sources": ["KB_ID_1", "KB_ID_2"],
  "timestamp": "2026-05-12T10:30:05Z"
}
```

#### Error Response
```json
{
  "error": "Unauthorized",
  "code": 401,
  "message": "Invalid or expired token",
  "timestamp": "2026-05-12T10:30:00Z"
}
```

---

## Part 4: Data Flow & Processing

### 4.1 Chat Message Processing Flow

```
1. RECEIVE
   ├─ Frontend sends message via POST /api/tax/chat
   ├─ API Gateway receives request
   └─ Validates request schema & JWT token

2. PARSE
   ├─ Extract message text
   ├─ Identify user_id from token
   └─ Initialize processing context

3. INTENT DETECTION
   ├─ Tokenize message
   ├─ Analyze keywords
   ├─ Classify as TRAINING or EXECUTION
   └─ Calculate confidence score

4. ROUTING
   ├─ Identify relevant module (GST/IT/Acct)
   ├─ Select specialized agent
   └─ Prepare agent context

5. PROCESSING
   ├─ Agent retrieves relevant knowledge
   ├─ Agent adapts response to user level
   ├─ Agent adds examples & compliance notes
   └─ Agent formats response

6. STORAGE
   ├─ Save message to CHAT_MESSAGE table
   ├─ Update CHAT_CONTEXT
   ├─ Update user last_activity
   └─ Cache recent messages in Redis

7. RESPOND
   ├─ Format response JSON
   ├─ Add metadata (confidence, sources)
   ├─ Return to API
   └─ API sends to frontend

8. DISPLAY
   ├─ Frontend receives response
   ├─ Updates chat UI
   ├─ Updates conversation history
   └─ Waits for next user input
```

### 4.2 Session Management Flow

```
LOGIN
├─ User submits credentials
├─ UserService validates password hash
├─ Generate JWT token (expires 24h)
├─ Create USER_SESSION record
└─ Return token to frontend

REQUEST
├─ Frontend includes token in header
├─ API Gateway verifies token signature
├─ Check token expiration
├─ Validate session in USER_SESSION table
└─ Allow/reject request

REFRESH
├─ Token near expiration (< 1 hour left)
├─ Frontend sends refresh request
├─ API generates new token
├─ Update USER_SESSION
└─ Return new token

LOGOUT
├─ User clicks logout
├─ Frontend clears local token
├─ Frontend calls DELETE /api/auth/logout
├─ Backend marks session inactive
└─ Token becomes invalid for future requests
```

---

## Part 5: Security Architecture

### 5.1 Authentication & Authorization

```
┌──────────────────────────────────────┐
│        User Credentials              │
│   Username & Password                │
└──────────────────┬───────────────────┘
                   ↓
            ┌─────────────┐
            │  Validate   │
            │  Credentials│
            └──────┬──────┘
                   ↓
        ┌─────────────────────┐
        │  Check User Active  │
        │  Check Permissions  │
        └──────────┬──────────┘
                   ↓
        ┌─────────────────────┐
        │  Generate JWT Token │
        │  exp: 24 hours      │
        │  sub: user_id       │
        └──────────┬──────────┘
                   ↓
        ┌─────────────────────┐
        │  Return Token +     │
        │  User Profile       │
        └─────────────────────┘
```

### 5.2 Data Security

- **Password**: Hashed with bcrypt (salt rounds: 10)
- **API Keys**: Encrypted in environment variables
- **Session Tokens**: JWT with HS256 signature
- **Database**: Encrypted connections (SSL/TLS)
- **Sensitive Data**: Encrypted at rest (AES-256)

### 5.3 Access Control

```
User Role → Permission Level → Resource Access

BEGINNER
├─ Can view basic tax information
├─ Can ask questions in chat
└─ Limited to training mode

INTERMEDIATE
├─ All beginner permissions
├─ Can access advanced topics
├─ Can use execution mode
└─ Can view examples

ADVANCED
├─ All permissions
├─ Can access pro features
├─ Can generate reports
└─ Can export data
```

---

## Part 6: Performance Optimization

### 6.1 Caching Strategy

```
Level 1: Browser Cache (Frontend)
├─ Session tokens: LocalStorage
├─ Recent responses: In-memory
└─ User preferences: LocalStorage

Level 2: Redis Cache (Backend)
├─ User sessions: TTL 24 hours
├─ Popular KB entries: TTL 7 days
├─ Frequent query results: TTL 1 hour
└─ Message context: TTL 24 hours

Level 3: Database Indexes
├─ CHAT_MESSAGE (user_id, timestamp)
├─ USER_SESSION (token, user_id)
├─ KNOWLEDGE_BASE (topic, agent_type)
└─ USER (email, username)
```

### 6.2 Query Optimization

```sql
-- Optimized: Indexed and filtered
SELECT * FROM CHAT_MESSAGE 
WHERE user_id = ? AND timestamp > NOW() - INTERVAL 7 DAYS
ORDER BY timestamp DESC LIMIT 50;

-- Avoid: Full table scan
SELECT * FROM CHAT_MESSAGE WHERE message_text LIKE '%tax%';

-- Better: Use search table or index
SELECT * FROM CHAT_MESSAGE_SEARCH 
WHERE content @@ plainto_tsquery('tax');
```

### 6.3 Response Time Targets

```
Chat Response Generation: < 2 seconds
  ├─ Intent detection: 50-100ms
  ├─ KB retrieval: 100-200ms
  ├─ Response generation: 500-1000ms
  ├─ Formatting & validation: 100-200ms
  └─ Database storage: 50-100ms

API Response: < 500ms
  ├─ Network latency: 50-100ms
  ├─ Server processing: 100-200ms
  └─ Serialization: 50-100ms
```

---

## Part 7: Scalability Architecture

### 7.1 Horizontal Scaling

```
Load Balancer (Nginx/HAProxy)
├─ Backend Instance 1 (Port 5000)
├─ Backend Instance 2 (Port 5001)
└─ Backend Instance 3 (Port 5002)

All instances share:
├─ PostgreSQL database (with connection pooling)
├─ Redis cluster
└─ Shared Knowledge Base
```

### 7.2 Database Scaling

```
Master PostgreSQL (Write)
├─ Replica 1 (Read-only)
├─ Replica 2 (Read-only)
└─ Replica 3 (Read-only)

Connection Pool: pgbouncer (min: 10, max: 100)
Partitioning: CHAT_MESSAGE by year
```

### 7.3 Caching Layer Scaling

```
Redis Cluster
├─ Node 1 (slots 0-5460)
├─ Node 2 (slots 5461-10922)
└─ Node 3 (slots 10923-16383)

Replication: Each node has 1 replica
TTL Management: Automatic eviction policy
```

---

## Part 8: Deployment Architecture

### 8.1 Development Environment

```
localhost:3000  → React Frontend
localhost:5000  → FastAPI Backend
localhost:5432  → PostgreSQL
localhost:6379  → Redis
```

### 8.2 Production Environment (Docker Compose)

```
docker-compose.prod.yml:
├─ nginx (Reverse Proxy, Port 80/443)
├─ frontend (React, Port 3000)
├─ backend (FastAPI, Port 5000)
├─ postgres (Database, Port 5432)
├─ redis (Cache, Port 6379)
└─ pgadmin (DB Admin, Port 5050)
```

### 8.3 Cloud Deployment (Azure)

```
Azure Container Registry
├─ Frontend image
├─ Backend image
└─ Database image

Azure Container Instances / AKS
├─ Frontend container
├─ Backend container (replicated)
├─ Postgres managed database
└─ Redis managed cache
```

---

## Part 9: Error Handling & Resilience

### 9.1 Error Handling Strategy

```
Try-Catch Blocks:
├─ API routes: Catch and format errors
├─ Agent logic: Handle missing KB entries
├─ Database queries: Handle connection errors
└─ External APIs: Fallback to cached data

Error Logging:
├─ ERROR: Critical failures
├─ WARNING: Recoverable issues
├─ INFO: Normal operations
└─ DEBUG: Diagnostic information
```

### 9.2 Resilience Patterns

```
Circuit Breaker:
├─ Knowledge Base unavailable → Use cache
├─ Database connection lost → Return cached responses
└─ External API timeout → Fallback to default

Retry Strategy:
├─ Database query fails → Retry 3 times
├─ API call fails → Exponential backoff
└─ Message storage fails → Queue for retry

Fallback:
├─ KB empty → Use generic response
├─ User not found → Create new session
└─ Response generation fails → Return error message
```

---

## Part 10: Monitoring & Observability

### 10.1 Metrics to Track

```
Application Metrics:
├─ Request count (by endpoint)
├─ Response time (p50, p95, p99)
├─ Error rate (4xx, 5xx)
├─ Agent response quality
└─ User engagement

Infrastructure Metrics:
├─ CPU usage
├─ Memory usage
├─ Disk I/O
├─ Network throughput
└─ Database connections

Business Metrics:
├─ New user registrations
├─ Chat conversations per day
├─ Average session duration
├─ User retention rate
└─ Revenue per user
```

### 10.2 Logging Format

```json
{
  "timestamp": "2026-05-12T10:30:00Z",
  "level": "INFO",
  "service": "chat_agent",
  "user_id": 123,
  "request_id": "req_abc123",
  "message": "Chat message processed",
  "agent_type": "GST",
  "response_time_ms": 1250,
  "status": "success"
}
```

---

## Part 11: Testing Strategy

### 11.1 Unit Tests

```python
# Test individual components
- UserService.register()
- ChatAgent.detect_intent()
- GST_Agent.handle_registration()
- Knowledge_Base.search()
```

### 11.2 Integration Tests

```python
# Test component interactions
- User registration → Session creation
- Chat message → Agent processing → Response
- Message save → History retrieval
```

### 11.3 End-to-End Tests

```python
# Test complete flows
- User login → Chat query → Response display
- Multiple conversation turns
- Session expiration → Logout
```

---

## Document Version
- **Version**: 1.0
- **Last Updated**: May 12, 2026
- **Architecture**: Layered with Agent Pattern
- **Status**: Complete
