# Entity Documentation - Virtual Tax Professional System

## Overview
This document provides comprehensive descriptions of all entities in the Virtual Tax Professional System, including their relationships, attributes, and business rules.

---

## 1. USER Entity

### Description
Represents a registered user of the Virtual Tax Professional System. Users can be individuals, business owners, or tax professionals seeking tax guidance and accounting assistance.

### Attributes
| Attribute | Type | Constraint | Description |
|-----------|------|-----------|-------------|
| `user_id` | INT | PK | Unique identifier for the user |
| `username` | VARCHAR(255) | UNIQUE, NOT NULL | Username for login |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User's email address |
| `password_hash` | VARCHAR(255) | NOT NULL | Hashed password (bcrypt) |
| `user_level` | ENUM | NOT NULL | Beginner, Intermediate, Advanced |
| `phone` | VARCHAR(20) | OPTIONAL | Contact phone number |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Account creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last profile update timestamp |

### Relationships
- **Has Many**: `CHAT_MESSAGE` (One user can have multiple chat messages)
- **Has Many**: `USER_SESSION` (One user can have multiple sessions)
- **Has Many**: `USER_PREFERENCE` (One user has one preference record)
- **Has Many**: `CHAT_CONTEXT` (One user can have multiple conversation contexts)

### Business Rules
- Email must be unique and valid
- Password must be at least 8 characters, hashed with bcrypt
- User level determines response complexity (beginner = simple, advanced = detailed)
- User account must be created before accessing chat

---

## 2. CHAT_MESSAGE Entity

### Description
Records every message exchange between the user and the tax assistant. Maintains complete chat history for audit trail and continuous learning.

### Attributes
| Attribute | Type | Constraint | Description |
|-----------|------|-----------|-------------|
| `message_id` | INT | PK | Unique message identifier |
| `user_id` | INT | FK | Reference to USER |
| `message_text` | TEXT | NOT NULL | User's input question |
| `response_text` | TEXT | NOT NULL | Agent's generated response |
| `agent_type` | ENUM | NOT NULL | GST, IncomeTax, Accounting |
| `mode` | ENUM | NOT NULL | TRAINING or EXECUTION |
| `module_type` | ENUM | NOT NULL | Specific module used |
| `timestamp` | TIMESTAMP | DEFAULT NOW() | When message was sent |
| `context_id` | INT | FK | Reference to CHAT_CONTEXT |

### Relationships
- **Belongs To**: `USER` (Every message belongs to one user)
- **Belongs To**: `CHAT_CONTEXT` (Message is part of a conversation)
- **References**: `KNOWLEDGE_BASE` (Query results used in response)

### Business Rules
- Every message must be associated with a user
- Response cannot be empty
- Agent type must match message content
- Timestamp is automatically set to current time
- Messages are immutable (no updates, only inserts)

---

## 3. CHAT_CONTEXT Entity

### Description
Maintains conversation context and state for multi-turn dialogues. Allows the system to understand related questions within a conversation thread.

### Attributes
| Attribute | Type | Constraint | Description |
|-----------|------|-----------|-------------|
| `context_id` | INT | PK | Unique context identifier |
| `user_id` | INT | FK | Reference to USER |
| `conversation_summary` | TEXT | OPTIONAL | Brief summary of conversation |
| `last_module` | VARCHAR(50) | OPTIONAL | Last module accessed (GST/IT/Acct) |
| `user_intent` | VARCHAR(255) | OPTIONAL | Detected user intent |
| `last_updated` | TIMESTAMP | DEFAULT NOW() | Last activity timestamp |

### Relationships
- **Belongs To**: `USER` (One user per context)
- **Has Many**: `CHAT_MESSAGE` (One context contains many messages)

### Business Rules
- Context is created when user starts a new conversation thread
- Context is updated with each new message
- Conversation summary is periodically regenerated
- Intent detection helps route future questions correctly

---

## 4. USER_SESSION Entity

### Description
Manages user authentication sessions. Tracks login/logout and validates token-based authentication for API requests.

### Attributes
| Attribute | Type | Constraint | Description |
|-----------|------|-----------|-------------|
| `session_id` | INT | PK | Unique session identifier |
| `user_id` | INT | FK | Reference to USER |
| `token` | VARCHAR(255) | UNIQUE, NOT NULL | JWT authentication token |
| `ip_address` | VARCHAR(45) | OPTIONAL | User's IP address |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Session start time |
| `expires_at` | TIMESTAMP | NOT NULL | Token expiration time |
| `is_active` | BOOLEAN | DEFAULT TRUE | Session active status |

### Relationships
- **Belongs To**: `USER` (Multiple sessions per user allowed)

### Business Rules
- Token must be unique and valid JWT
- Session expires after 24 hours (configurable)
- Only one active session per user recommended
- IP address logged for security audit
- Expired sessions are automatically invalidated

---

## 5. USER_PREFERENCE Entity

### Description
Stores user preferences and customization settings for personalized experience.

### Attributes
| Attribute | Type | Constraint | Description |
|-----------|------|-----------|-------------|
| `preference_id` | INT | PK | Unique preference record ID |
| `user_id` | INT | FK | Reference to USER |
| `language` | VARCHAR(10) | DEFAULT 'en' | Preferred language (en, hi, etc.) |
| `notifications` | BOOLEAN | DEFAULT TRUE | Enable/disable notifications |
| `theme` | ENUM | DEFAULT 'light' | Light or Dark theme |
| `complexity_level` | ENUM | DEFAULT 'intermediate' | Response detail level |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation time |

### Relationships
- **Belongs To**: `USER` (One preference per user)

### Business Rules
- One preference record per user
- Complexity level affects response length and detail
- Language setting applies to responses and UI
- Preferences are user-editable

---

## 6. KNOWLEDGE_BASE Entity

### Description
Central repository of tax knowledge covering GST, Income Tax, and Accounting topics. Contains training content and execution guidelines.

### Attributes
| Attribute | Type | Constraint | Description |
|-----------|------|-----------|-------------|
| `kb_id` | INT | PK | Unique knowledge entry ID |
| `topic` | VARCHAR(255) | NOT NULL | Topic name (e.g., "GST Registration") |
| `content` | TEXT | NOT NULL | Detailed content/explanation |
| `example` | TEXT | OPTIONAL | Real-world example or scenario |
| `agent_type` | ENUM | NOT NULL | GST, IncomeTax, or Accounting |
| `compliance_note` | TEXT | OPTIONAL | Latest compliance updates |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last content update |

### Relationships
- **Referenced By**: `CHAT_MESSAGE` (Messages query this KB)
- **Has Many**: `TOPIC` (One KB entry covers multiple topics)

### Business Rules
- Content must be accurate and compliant with current tax laws
- Compliance notes updated with regulatory changes
- Multiple topics can reference same KB entry
- KB is read-only for agents (updates via admin panel)
- Examples should be realistic and relatable

---

## 7. TOPIC Entity

### Description
Categorizes knowledge base entries into logical tax topics. Enables efficient search and filtering.

### Attributes
| Attribute | Type | Constraint | Description |
|-----------|------|-----------|-------------|
| `topic_id` | INT | PK | Unique topic identifier |
| `topic_name` | VARCHAR(255) | UNIQUE, NOT NULL | Name of the topic |
| `category` | ENUM | NOT NULL | GST, IncomeTax, Accounting |
| `description` | TEXT | OPTIONAL | Brief topic description |

### Relationships
- **Referenced By**: `KNOWLEDGE_BASE` (KB entries categorized by topic)

### Business Rules
- Topic names must be unique within a category
- Categories align with the three main agent modules
- Topics enable hierarchical organization of knowledge

---

## Agent Entities (Logical)

### 8. CHAT_AGENT

**Description**: Orchestrator agent that routes user queries to appropriate specialized agents.

**Attributes**:
- `agent_mode`: TRAINING, EXECUTION, or HYBRID
- `current_module`: GST, IncomeTax, or Accounting
- `conversation_history`: Previous messages context

**Methods**:
- `detect_intent()`: Analyzes user query for TRAINING vs EXECUTION mode
- `route_to_module()`: Determines which specialized agent handles the query
- `generate_response()`: Assembles final response
- `maintain_context()`: Updates conversation state

---

### 9. GST_AGENT

**Description**: Specialized agent for Goods and Services Tax guidance.

**Topics Covered**:
1. GST Registration process
2. GST filing requirements
3. GST rules and regulations
4. Input Tax Credit (ITC)
5. Return filing procedures
6. Compliance deadlines
7. Common GST errors and remedies
8. Multi-state tax requirements

**Methods**:
- `handle_registration()`: Guides GST registration
- `handle_filing()`: Explains filing procedures
- `explain_gst_rules()`: Provides rule clarification

---

### 10. INCOME_TAX_AGENT

**Description**: Specialized agent for Income Tax and tax planning.

**Topics Covered**:
1. Income classification (Salary, Business, Capital Gains, etc.)
2. Deduction optimization (Section 80C, 80D, etc.)
3. Capital gains calculation and reporting
4. ITR (Income Tax Return) filing
5. TDS (Tax Deducted at Source)
6. Tax planning strategies
7. HRA calculation
8. Business expense deduction
9. Professional fees
10. Investment-linked tax benefits
11. Dividend income taxation
12. Agricultural income exemptions
13. Senior citizen benefits
14. Loss carry-forward
15. Tax audit requirements

**Methods**:
- `calculate_tax()`: Computes tax liability
- `optimize_deductions()`: Recommends tax-saving strategies
- `handle_capital_gains()`: Explains capital gains taxation
- `prepare_itr()`: Guides ITR preparation

---

### 11. ACCOUNTING_AGENT

**Description**: Specialized agent for bookkeeping and accounting practices.

**Topics Covered**:
1. Journal entry recording
2. Account reconciliation
3. Financial statement preparation
4. Trial balance compilation
5. Accounts receivable management
6. Accounts payable management
7. Bank reconciliation
8. Balance sheet analysis
9. Profit & Loss statement
10. Cash flow management

**Methods**:
- `handle_journal_entry()`: Guides journal entries
- `reconcile_accounts()`: Explains reconciliation
- `generate_reports()`: Helps create financial reports
- `track_transactions()`: Manages transaction recording

---

## Data Flows

### User Registration Flow
```
User → Frontend → API → User Service → PostgreSQL (USER table)
```

### Chat Query Flow
```
User Message → Frontend → API → ChatAgent → Specialized Agent 
→ Knowledge Base → Response Generation → ChatMessage Save 
→ PostgreSQL → Frontend → User Display
```

### Session Management Flow
```
Login → API Auth → Generate JWT Token → USER_SESSION Create
→ Token Stored in Frontend → Each Request: Token Validation
→ Session Lookup → Continue or Redirect
```

---

## Key Relationships Summary

| Entity | Relationship | Target Entity | Cardinality |
|--------|-------------|----------------|-------------|
| USER | has | CHAT_MESSAGE | 1 to Many |
| USER | creates | USER_SESSION | 1 to Many |
| USER | has | USER_PREFERENCE | 1 to 1 |
| USER | generates | CHAT_CONTEXT | 1 to Many |
| CHAT_MESSAGE | belongs to | USER | Many to 1 |
| CHAT_MESSAGE | queries | KNOWLEDGE_BASE | Many to Many |
| CHAT_MESSAGE | part of | CHAT_CONTEXT | Many to 1 |
| KNOWLEDGE_BASE | categorized into | TOPIC | Many to Many |
| USER_SESSION | authenticates | USER | Many to 1 |
| USER_PREFERENCE | customizes | USER | 1 to 1 |

---

## Compliance & Audit Considerations

1. **Data Retention**: Chat messages retained for 2 years for audit trail
2. **Access Control**: Only user can view their own messages
3. **Encryption**: Passwords hashed, sensitive data encrypted at rest
4. **Authentication**: JWT tokens for API authentication
5. **Logging**: All agent decisions and responses logged for compliance
6. **GDPR Compliance**: Users can request data export or deletion

---

## Performance Optimization

1. **Indexing**: 
   - `USER.email`, `USER.username`
   - `CHAT_MESSAGE.user_id`, `CHAT_MESSAGE.timestamp`
   - `USER_SESSION.token`, `USER_SESSION.user_id`

2. **Caching**:
   - Frequently accessed KB entries in Redis
   - User sessions cached with TTL
   - Recent chat contexts in memory cache

3. **Partitioning**:
   - CHAT_MESSAGE table partitioned by year
   - Archive old messages to improve query performance

---

## Document Version
- **Version**: 1.0
- **Last Updated**: May 12, 2026
- **Status**: Complete
