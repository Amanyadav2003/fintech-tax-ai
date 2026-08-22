#!/usr/bin/env python3
"""
Export Mermaid Diagrams to PNG/SVG
Converts all system design diagrams to image files
"""

import subprocess
import os
import json
from pathlib import Path

# Define all diagrams
DIAGRAMS = {
    "1_system_design": {
        "title": "System Design - Architecture",
        "mermaid": """graph TB
    subgraph Frontend["🖥️ Frontend Layer"]
        UI["React UI<br/>Chat Interface"]
        Auth["Authentication<br/>Service"]
        Cache["Local Cache<br/>Session Data"]
    end
    
    subgraph API["🔗 API Gateway Layer"]
        Gateway["REST API<br/>Port 5000"]
        Routes["Routes<br/>/api/tax/chat<br/>/api/auth<br/>/api/user"]
    end
    
    subgraph Agent["🤖 Agent Layer"]
        ChatAgent["Chat Agent<br/>Orchestrator"]
        GST["GST Agent<br/>Reg/Filing"]
        IncomeTax["Income Tax Agent<br/>15+ Topics"]
        Accounting["Accounting Agent<br/>Journal/Reconciliation"]
    end
    
    subgraph Backend["💾 Backend Services"]
        UserService["User Service<br/>Registration/Login"]
        ChatService["Chat Service<br/>History & Context"]
        KnowledgeBase["Knowledge Base<br/>23+ Topics"]
    end
    
    subgraph Database["🗄️ Database Layer"]
        PostgreSQL["PostgreSQL<br/>Users<br/>Chat History<br/>User Preferences"]
    end
    
    subgraph External["🌐 External Services"]
        TaxRules["Tax Rules<br/>API"]
        Compliance["Compliance<br/>Updates"]
    end
    
    UI -->|HTTP Request| Gateway
    Auth -->|Token Verify| Gateway
    Gateway -->|Route| Routes
    Routes -->|Chat Query| ChatAgent
    ChatAgent -->|Dispatch| GST
    ChatAgent -->|Dispatch| IncomeTax
    ChatAgent -->|Dispatch| Accounting
    GST -->|Query| KnowledgeBase
    IncomeTax -->|Query| KnowledgeBase
    Accounting -->|Query| KnowledgeBase
    UserService -->|User Data| PostgreSQL
    ChatService -->|Store History| PostgreSQL
    ChatAgent -->|Save Context| ChatService
    KnowledgeBase -->|Fetch| TaxRules
    KnowledgeBase -->|Check| Compliance"""
    },
    
    "2_uml_class_diagram": {
        "title": "UML Class Diagram - Core Entities",
        "mermaid": """classDiagram
    class User {
        +int user_id
        +string username
        +string email
        +string password_hash
        +string user_level
        +datetime created_at
        +datetime updated_at
        +register()
        +login()
        +update_profile()
    }
    
    class ChatMessage {
        +int message_id
        +int user_id
        +string message_text
        +string response_text
        +string agent_type
        +string mode
        +datetime timestamp
        +save_message()
        +get_history()
    }
    
    class ChatAgent {
        +string agent_mode
        +string current_module
        +detect_intent()
        +route_to_module()
        +generate_response()
        +maintain_context()
    }
    
    class GSTAgent {
        +string[] gst_topics
        +handle_registration()
        +handle_filing()
        +explain_gst_rules()
    }
    
    class IncomeTaxAgent {
        +string[] tax_topics
        +calculate_tax()
        +optimize_deductions()
        +handle_capital_gains()
        +prepare_itr()
    }
    
    class AccountingAgent {
        +handle_journal_entry()
        +reconcile_accounts()
        +generate_reports()
        +track_transactions()
    }
    
    class KnowledgeBase {
        +string topic
        +string content
        +string example
        +string compliance_note
        +retrieve_content()
        +search_topics()
        +update_compliance()
    }
    
    class UserSession {
        +int session_id
        +int user_id
        +string token
        +datetime expiry
        +create_session()
        +validate_token()
        +destroy_session()
    }
    
    User "1" --> "*" ChatMessage : writes
    User "1" --> "1" UserSession : has
    ChatAgent "1" --> "*" ChatMessage : creates
    ChatAgent --> GSTAgent : delegates
    ChatAgent --> IncomeTaxAgent : delegates
    ChatAgent --> AccountingAgent : delegates
    ChatMessage --> KnowledgeBase : queries
    GSTAgent --> KnowledgeBase : retrieves
    IncomeTaxAgent --> KnowledgeBase : retrieves
    AccountingAgent --> KnowledgeBase : retrieves"""
    },
    
    "3_user_flow": {
        "title": "User Flow & Chat Workflow",
        "mermaid": """flowchart TD
    Start([User Visits App]) --> Auth{Logged In?}
    Auth -->|No| Register[Register/Login]
    Register --> RegDB[(Save to DB)]
    Auth -->|Yes| Chat[Chat Interface]
    Chat --> Input["Enter Question<br/>e.g., 'How to register for GST?'"]
    Input --> API["POST /api/tax/chat<br/>with message"]
    API --> ChatAgent["ChatAgent<br/>Orchestrator"]
    ChatAgent --> Detect["Detect Intent<br/>TRAINING/EXECUTION"]
    Detect --> Route["Route to Module<br/>GST/IncomeTax/Accounting"]
    Route --> Module{Which Module?}
    Module -->|GST| GSTLogic["GSTAgent:<br/>- Handle registration<br/>- Filing process<br/>- GST rules"]
    Module -->|IncomeTax| ITLogic["IncomeTaxAgent:<br/>- Tax calculation<br/>- Deduction optimizer<br/>- Capital gains"]
    Module -->|Accounting| AcctLogic["AccountingAgent:<br/>- Journal entries<br/>- Reconciliation<br/>- Reports"]
    GSTLogic --> KB["Query Knowledge Base<br/>23+ Topics"]
    ITLogic --> KB
    AcctLogic --> KB
    KB --> Generate["Generate Personalized<br/>Response"]
    Generate --> Save["Save Chat History<br/>to Database"]
    Save --> Response["Return Response<br/>to Frontend"]
    Response --> Display["Display to User"]
    Display --> Continue{Continue?}
    Continue -->|Yes| Input
    Continue -->|No| End([Session End])
    style Start fill:#90EE90
    style End fill:#FFB6C6
    style ChatAgent fill:#87CEEB
    style KB fill:#FFD700"""
    },
    
    "4_data_flow": {
        "title": "Data Flow Diagram",
        "mermaid": """graph LR
    subgraph Sources["Data Sources"]
        U["👤 User Input"]
        DB1["🗄️ User DB"]
        KB["📚 Knowledge Base"]
    end
    
    subgraph Process["Data Processing"]
        P1["Parse Input<br/>Tokenize"]
        P2["Intent Detection<br/>Classify Request"]
        P3["Module Routing<br/>GST/IT/Acct"]
        P4["Agent Processing<br/>Generate Response"]
        P5["Format Output"]
    end
    
    subgraph Storage["Data Storage"]
        DB2["PostgreSQL<br/>Users"]
        DB3["PostgreSQL<br/>Chat History"]
        Cache["Redis Cache<br/>Sessions"]
    end
    
    subgraph Output["Data Output"]
        O1["JSON Response"]
        O2["🖥️ Frontend Display"]
    end
    
    U -->|"Raw Text"| P1
    P1 -->|"Tokens"| P2
    P2 -->|"Intent Label"| P3
    P3 -->|"Module ID"| P4
    KB -->|"Context Data"| P4
    DB1 -->|"User Profile"| P4
    P4 -->|"Generated Text"| P5
    P5 -->|"Formatted"| O1
    O1 -->|"Send"| O2
    P4 -->|"Store"| DB3
    U -->|"User ID"| Cache
    Cache -->|"Session Token"| P1
    O1 -.->|"User Data"| DB2
    
    style U fill:#90EE90
    style P4 fill:#87CEEB
    style DB2 fill:#FFD700
    style DB3 fill:#FFD700
    style O2 fill:#DDA0DD"""
    },
    
    "5_entity_relationship": {
        "title": "Entity Relationship Diagram",
        "mermaid": """erDiagram
    USER ||--o{ CHAT_MESSAGE : sends
    USER ||--o{ USER_SESSION : creates
    USER ||--o{ USER_PREFERENCE : has
    CHAT_MESSAGE ||--o{ CHAT_CONTEXT : contains
    CHAT_MESSAGE }o--|| KNOWLEDGE_BASE : queries
    KNOWLEDGE_BASE ||--o{ TOPIC : covers
    USER_SESSION }o--|| USER : authenticates
    USER_PREFERENCE }o--|| USER : customizes
    
    USER {
        int user_id PK
        string username
        string email UK
        string password_hash
        string user_level
        string phone
        datetime created_at
        datetime updated_at
    }
    
    CHAT_MESSAGE {
        int message_id PK
        int user_id FK
        string message_text
        string response_text
        string agent_type
        string mode
        string module_type
        datetime timestamp
        int context_id FK
    }
    
    CHAT_CONTEXT {
        int context_id PK
        int user_id FK
        string conversation_summary
        string last_module
        string user_intent
        datetime last_updated
    }
    
    USER_SESSION {
        int session_id PK
        int user_id FK
        string token UK
        string ip_address
        datetime created_at
        datetime expires_at
        boolean is_active
    }
    
    USER_PREFERENCE {
        int preference_id PK
        int user_id FK
        string language
        boolean notifications
        string theme
        string complexity_level
        datetime created_at
    }
    
    KNOWLEDGE_BASE {
        int kb_id PK
        string topic
        string content
        string example
        string agent_type
        string compliance_note
        datetime updated_at
    }
    
    TOPIC {
        int topic_id PK
        string topic_name
        string category
        string description
    }"""
    },
    
    "6_sequence_diagram": {
        "title": "Sequence Diagram - Chat Processing",
        "mermaid": """sequenceDiagram
    participant User as 👤 User
    participant Frontend as 🖥️ Frontend
    participant API as 🔗 API Gateway
    participant ChatAgent as 🤖 Chat Agent
    participant Agent as 🔧 Specialized Agent
    participant KB as 📚 Knowledge Base
    participant DB as 🗄️ Database

    User->>Frontend: Enter Question
    Frontend->>API: POST /api/tax/chat
    API->>ChatAgent: Pass message
    ChatAgent->>ChatAgent: Detect Intent (TRAINING/EXECUTION)
    ChatAgent->>ChatAgent: Identify Module (GST/IT/Acct)
    ChatAgent->>Agent: Route to Agent
    Agent->>KB: Query Topic
    KB-->>Agent: Return Content & Examples
    Agent->>Agent: Generate Response (personalized by level)
    Agent-->>ChatAgent: Response Text
    ChatAgent->>ChatAgent: Format Response
    ChatAgent->>DB: Store Chat Message
    DB-->>ChatAgent: Confirm Save
    ChatAgent-->>API: Return Response
    API-->>Frontend: JSON Response
    Frontend->>User: Display Answer"""
    }
}

def create_svg_files():
    """Create SVG versions using mermaid-cli if available"""
    diagrams_dir = Path("diagrams_exported")
    diagrams_dir.mkdir(exist_ok=True)
    
    print("📊 Creating Mermaid Diagram Files...")
    print("=" * 60)
    
    for diagram_id, diagram_data in DIAGRAMS.items():
        # Create .mmd file
        mmd_file = diagrams_dir / f"{diagram_id}.mmd"
        with open(mmd_file, 'w', encoding='utf-8') as f:
            f.write(diagram_data['mermaid'])
        
        print(f"✅ Created: {mmd_file}")
        print(f"   Title: {diagram_data['title']}")
    
    print("\n" + "=" * 60)
    print("📁 All diagram files created in: diagrams_exported/")
    print("\n💡 To export to PNG/SVG, install mermaid-cli:")
    print("   npm install -g @mermaid-js/mermaid-cli")
    print("\n🎨 Then run:")
    print("   mmdc -i diagrams_exported/1_system_design.mmd -o diagrams_exported/1_system_design.png")

def create_html_converter():
    """Create an HTML file to convert diagrams using browser"""
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Export Diagrams as PNG</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body { font-family: Arial; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        .control-panel { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
        button { padding: 10px 20px; margin: 5px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #764ba2; }
        .diagram-container { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .mermaid { display: flex; justify-content: center; }
    </style>
</head>
<body>
    <h1>📊 Mermaid Diagram Exporter</h1>
    
    <div class="control-panel">
        <h3>📥 Export Instructions</h3>
        <p>For each diagram below:</p>
        <ol>
            <li>Right-click on the diagram</li>
            <li>Select "Save image as..."</li>
            <li>Choose format (PNG recommended)</li>
            <li>Save to your desired location</li>
        </ol>
        <button onclick="exportAll()">📥 Export All Diagrams</button>
    </div>

    <div id="diagrams"></div>

    <script>
        mermaid.initialize({ startOnLoad: true, theme: 'default', securityLevel: 'loose' });
        
        const diagrams = {
            "1_system_design": "System Design - Architecture",
            "2_uml_class_diagram": "UML Class Diagram",
            "3_user_flow": "User Flow & Chat Workflow",
            "4_data_flow": "Data Flow Diagram",
            "5_entity_relationship": "Entity Relationship Diagram",
            "6_sequence_diagram": "Sequence Diagram"
        };

        // Fetch and display diagrams
        fetch('diagrams_data.json')
            .then(r => r.json())
            .then(data => {
                const container = document.getElementById('diagrams');
                Object.keys(diagrams).forEach(key => {
                    const div = document.createElement('div');
                    div.className = 'diagram-container';
                    div.innerHTML = `
                        <h2>${diagrams[key]}</h2>
                        <div class="mermaid" id="${key}">
                            ${data[key]}
                        </div>
                        <button onclick="exportDiagram('${key}')">Save ${key}</button>
                    `;
                    container.appendChild(div);
                });
                mermaid.contentLoaded();
            });

        function exportDiagram(diagramId) {
            const element = document.getElementById(diagramId);
            const svg = element.querySelector('svg');
            if (svg) {
                const url = URL.createObjectURL(new Blob([svg.outerHTML], { type: 'image/svg+xml' }));
                const a = document.createElement('a');
                a.href = url;
                a.download = `${diagramId}.svg`;
                a.click();
            }
        }

        function exportAll() {
            Object.keys(diagrams).forEach(key => {
                setTimeout(() => exportDiagram(key), 500);
            });
        }
    </script>
</body>
</html>'''
    
    with open("export_diagrams.html", 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("\n✅ Created: export_diagrams.html")
    print("   Open in browser and click 'Export All Diagrams' button")

def save_diagrams_json():
    """Save diagrams as JSON for the HTML converter"""
    data = {key: value['mermaid'] for key, value in DIAGRAMS.items()}
    with open("diagrams_data.json", 'w', encoding='utf-8') as f:
        json.dump(data, f)
    print("✅ Created: diagrams_data.json")

def create_cli_export_script():
    """Create a shell/batch script for CLI export"""
    
    # Windows batch script
    batch_content = '''@echo off
REM Export Mermaid Diagrams to PNG using mermaid-cli
REM First, install mermaid-cli: npm install -g @mermaid-js/mermaid-cli

echo Creating diagrams folder...
if not exist diagrams_exported mkdir diagrams_exported

echo.
echo Checking if mermaid-cli is installed...
where mmdc >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ mermaid-cli not found. Installing...
    npm install -g @mermaid-js/mermaid-cli
)

echo.
echo 📊 Exporting diagrams to PNG...
echo ======================================

mmdc -i diagrams_exported/1_system_design.mmd -o diagrams_exported/1_system_design.png
mmdc -i diagrams_exported/2_uml_class_diagram.mmd -o diagrams_exported/2_uml_class_diagram.png
mmdc -i diagrams_exported/3_user_flow.mmd -o diagrams_exported/3_user_flow.png
mmdc -i diagrams_exported/4_data_flow.mmd -o diagrams_exported/4_data_flow.png
mmdc -i diagrams_exported/5_entity_relationship.mmd -o diagrams_exported/5_entity_relationship.png
mmdc -i diagrams_exported/6_sequence_diagram.mmd -o diagrams_exported/6_sequence_diagram.png

echo.
echo ✅ Export complete!
echo 📁 Check diagrams_exported folder for PNG files
pause
'''
    
    with open("export_diagrams.bat", 'w', encoding='utf-8') as f:
        f.write(batch_content)
    print("✅ Created: export_diagrams.bat (Windows)")
    
    # Linux/Mac shell script
    shell_content = '''#!/bin/bash
# Export Mermaid Diagrams to PNG using mermaid-cli

echo "Creating diagrams folder..."
mkdir -p diagrams_exported

echo ""
echo "Checking if mermaid-cli is installed..."
if ! command -v mmdc &> /dev/null; then
    echo "❌ mermaid-cli not found. Installing..."
    npm install -g @mermaid-js/mermaid-cli
fi

echo ""
echo "📊 Exporting diagrams to PNG..."
echo "======================================"

mmdc -i diagrams_exported/1_system_design.mmd -o diagrams_exported/1_system_design.png
mmdc -i diagrams_exported/2_uml_class_diagram.mmd -o diagrams_exported/2_uml_class_diagram.png
mmdc -i diagrams_exported/3_user_flow.mmd -o diagrams_exported/3_user_flow.png
mmdc -i diagrams_exported/4_data_flow.mmd -o diagrams_exported/4_data_flow.png
mmdc -i diagrams_exported/5_entity_relationship.mmd -o diagrams_exported/5_entity_relationship.png
mmdc -i diagrams_exported/6_sequence_diagram.mmd -o diagrams_exported/6_sequence_diagram.png

echo ""
echo "✅ Export complete!"
echo "📁 Check diagrams_exported folder for PNG files"
'''
    
    with open("export_diagrams.sh", 'w', encoding='utf-8') as f:
        f.write(shell_content)
    print("✅ Created: export_diagrams.sh (Linux/Mac)")

def create_readme():
    """Create export instructions README"""
    readme = '''# 📊 System Design Diagrams Export Guide

## Created Files

### Diagram Source Files (.mmd)
- `diagrams_exported/1_system_design.mmd`
- `diagrams_exported/2_uml_class_diagram.mmd`
- `diagrams_exported/3_user_flow.mmd`
- `diagrams_exported/4_data_flow.mmd`
- `diagrams_exported/5_entity_relationship.mmd`
- `diagrams_exported/6_sequence_diagram.mmd`

### Export Tools

#### Option 1: Use Browser (Easiest)
1. Open `export_diagrams.html` in a web browser
2. Right-click on any diagram
3. Select "Save image as..."
4. Choose PNG or SVG format

#### Option 2: Use Command Line (Best Quality)
1. Install mermaid-cli:
   ```bash
   npm install -g @mermaid-js/mermaid-cli
   ```

2. **Windows**: Run `export_diagrams.bat`
3. **Linux/Mac**: Run `bash export_diagrams.sh`

#### Option 3: Manual CLI Export
```bash
mmdc -i diagrams_exported/1_system_design.mmd -o diagrams_exported/1_system_design.png
```

## Diagram List

| # | Diagram | Use Case |
|---|---------|----------|
| 1 | System Design | High-level architecture overview |
| 2 | UML Class Diagram | Entity relationships & methods |
| 3 | User Flow | User journey & workflows |
| 4 | Data Flow | Information transformation |
| 5 | Entity Relationship | Database schema |
| 6 | Sequence Diagram | Chat processing flow |

## Output Formats

- **PNG**: Best for presentations, web, documents
- **SVG**: Scalable, editable in design tools
- **PDF**: Printable, professional documents

## Tips

- PNG files are ~100-300KB each
- SVG files are editable in Inkscape, Adobe Illustrator, etc.
- High resolution: Use `--width 1920 --height 1080` with mmdc
- All diagrams use consistent color scheme for professional look

## Troubleshooting

**Issue**: "mmdc command not found"
- Solution: `npm install -g @mermaid-js/mermaid-cli`

**Issue**: PNG quality is poor
- Solution: Use `mmdc --scale 2` for 2x resolution

**Issue**: Can't edit exported PNG
- Solution: Export as SVG instead for editability

---
Generated: May 12, 2026
'''
    
    with open("EXPORT_GUIDE.md", 'w', encoding='utf-8') as f:
        f.write(readme)
    print("✅ Created: EXPORT_GUIDE.md")

if __name__ == "__main__":
    print("\n🎨 Virtual Tax Professional System - Diagram Exporter")
    print("=" * 60)
    
    # Create all files
    create_svg_files()
    save_diagrams_json()
    create_html_converter()
    create_cli_export_script()
    create_readme()
    
    print("\n" + "=" * 60)
    print("✅ All export files created successfully!")
    print("\n📋 Next Steps:")
    print("   1. Open export_diagrams.html in your browser")
    print("   2. Right-click diagrams to save as PNG")
    print("   3. Or install mermaid-cli and run export_diagrams.bat/.sh")
    print("\n📁 Output location: diagrams_exported/")
    print("=" * 60 + "\n")
