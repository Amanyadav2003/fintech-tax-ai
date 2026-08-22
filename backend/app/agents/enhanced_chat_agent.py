"""
ENHANCED CHAT AGENT - Hybrid Virtual Tax Professional
Handles multi-module tax queries with TRAINING and EXECUTION modes
Supports GST, Income Tax, and Accounting workflows
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
from .tax_agent import TaxAgent
from .risk_agent import RiskAgent
from .strategy_agent import StrategyAgent


class OperatingMode(Enum):
    """Operating modes for the chat agent"""
    TRAINING = "training"  # Teach concepts
    EXECUTION = "execution"  # Execute tasks
    HYBRID = "hybrid"  # Mix both


class TaxModule(Enum):
    """Tax modules supported"""
    GST = "gst"
    INCOME_TAX = "income_tax"
    ACCOUNTING = "accounting"
    GENERAL = "general"


class ConversationContext:
    """Manages conversation state across multiple turns"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.mode: Optional[OperatingMode] = None
        self.module: Optional[TaxModule] = None
        self.sub_module: Optional[str] = None
        self.conversation_history: List[Dict] = []
        self.last_topic: Optional[str] = None
        self.learning_progress: Dict = {}
        self.current_task: Optional[str] = None
        self.timestamp = datetime.now()
        self.user_level = "beginner"  # beginner, intermediate, advanced
    
    def update_context(self, mode: OperatingMode, module: TaxModule, sub_module: str = None):
        """Update conversation context"""
        self.mode = mode
        self.module = module
        self.sub_module = sub_module
        self.timestamp = datetime.now()
    
    def add_to_history(self, role: str, message: str, metadata: Dict = None):
        """Add message to conversation history"""
        self.conversation_history.append({
            "timestamp": datetime.now(),
            "role": role,  # "user" or "bot"
            "message": message,
            "metadata": metadata or {}
        })
    
    def get_context_summary(self) -> Dict:
        """Return context for agent decision-making"""
        return {
            "mode": self.mode.value if self.mode else None,
            "module": self.module.value if self.module else None,
            "history_length": len(self.conversation_history),
            "last_topic": self.last_topic,
            "user_level": self.user_level,
            "current_task": self.current_task
        }


class EnhancedChatAgent:
    """AI Chat Agent with hybrid training/execution capabilities"""

    def __init__(self):
        self.tax_agent = TaxAgent()
        self.risk_agent = RiskAgent()
        self.strategy_agent = StrategyAgent()
        
        # Enhanced knowledge bases for all modules
        self._initialize_knowledge_bases()
        
        # Training mode keywords
        self.training_keywords = [
            "explain", "teach", "learn", "what is", "define", "concept",
            "how does", "understand", "example", "case study", "foundation",
            "basics", "introduction", "background", "difference between"
        ]
        
        # Execution mode keywords (removed "register" as it's ambiguous with training)
        self.execution_keywords = [
            "file", "calculate", "prepare", "submit", "complete",
            "do", "start", "create", "generate", "process", "fill", "action",
            "step", "checklist", "guide", "procedure", "help me"
        ]

    def _initialize_knowledge_bases(self):
        """Initialize knowledge bases for all modules"""
        
        # INCOME TAX KNOWLEDGE BASE (Enhanced)
        self.income_tax_kb = {
            "80c": {
                "patterns": ["80c", "80 c", "section 80c", "investment", "elss", "ppf", "lic", "tax saving", "deduction limit"],
                "training": {
                    "title": "SECTION 80C - Tax Saving Deductions",
                    "content": """Section 80C allows deductions up to ₹1.5 Lakhs for:
                    • ELSS Mutual Funds (3-year lock-in, growth)
                    • PPF (Public Provident Fund) - Safe, tax-free
                    • Life Insurance Premiums - Insurance + tax savings
                    • NSC (National Savings Certificate) - Government security
                    • Fixed Deposits (5-year only)
                    • Home Loan Principal - Self-occupied property
                    • Employee Provident Fund (EPF) contribution
                    • Education Fees - School, college, professional courses
                    
                    IMPORTANT: Only ONE deduction of ₹1.5L total per year!
                    Best mix: 40% PPF (safety) + 60% ELSS (growth)""",
                    "examples": [
                        {
                            "scenario": "Rahul: ₹12L salary, single",
                            "investment": "PPF ₹50K + ELSS ₹50K + LIC ₹35K + Home Loan ₹15K = ₹1.5L",
                            "benefit": "Tax saved @ 20% = ₹30,000"
                        }
                    ],
                    "checkpoints": [
                        "What's the maximum deduction under 80C?",
                        "Can you claim both PPF and ELSS together?",
                        "How is ELSS taxed after 3 years?"
                    ]
                },
                "execution": {
                    "title": "Claim 80C Deduction - Step by Step",
                    "checklist": [
                        "Collect certificates for ELSS, PPF, LIC, NSC",
                        "Total all investments (max ₹1.5L)",
                        "Keep proofs for 6 years",
                        "Enter in ITR Schedule-80C",
                        "Verify with deduction proof documents"
                    ],
                    "documents": ["ELSS statement", "PPF account statement", "LIC premium receipts", "NSC certificate"],
                    "tools": "80C Calculator, Investment Tracker"
                }
            },
            "80d": {
                "patterns": ["80d", "80 d", "section 80d", "health insurance", "medical insurance", "health"],
                "training": {
                    "title": "SECTION 80D - Health Insurance",
                    "content": """Section 80D provides deductions for health insurance:
                    
                    For self/spouse/children:
                    • Premium ≤ ₹25,000 = Full deduction
                    • Premium > ₹25,000 = Only ₹25,000 deducted
                    
                    For senior citizen parents (≥60 years):
                    • Premium ≤ ₹50,000 = Full deduction
                    • Premium > ₹50,000 = Only ₹50,000 deducted
                    
                    NO overlap with 80C - separate deduction!
                    Covers self, spouse, children, parents, and in-laws.""",
                    "examples": [
                        {
                            "scenario": "Family: 2 adults + 1 child + 1 senior parent",
                            "premiums": "Self ₹15K + Spouse ₹10K + Child ₹8K + Parent ₹45K",
                            "deduction": "₹15K + ₹10K + ₹8K + ₹45K = ₹78,000 (if all eligible)"
                        }
                    ]
                },
                "execution": {
                    "title": "Claim 80D - Step by Step",
                    "checklist": [
                        "Collect health insurance policy documents",
                        "Gather all premium receipts/proofs",
                        "Verify coverage for self, spouse, children",
                        "Check parent age (≥60 for enhanced limit)",
                        "Enter in ITR Schedule-80D"
                    ]
                }
            },
            "itr_filing": {
                "patterns": ["itr", "how to file", "e-filing", "income tax return", "file itr", "return filing"],
                "training": {
                    "title": "ITR Filing Basics",
                    "content": """ITR (Income Tax Return) is an annual compliance requirement.
                    
                    Choose your ITR form:
                    • ITR-1 (SAHAJ): Salary + Interest + Family Pension
                    • ITR-2: Capital gains, losses (no business)
                    • ITR-3: Business/Professional income
                    • ITR-4: Presumptive income (turnover <2 Cr)
                    • ITR-5: Partnership/LLP
                    • ITR-6: Corporate/Trust
                    
                    Timeline:
                    • Filing deadline: 31 July (usually)
                    • E-verification required: Within 30 days
                    • Refund processing: 2-4 weeks after verification"""
                },
                "execution": {
                    "title": "File Your ITR - Complete Guide",
                    "steps": [
                        {
                            "step": 1,
                            "title": "Pre-Filing Checklist",
                            "actions": [
                                "Verify PAN-Aadhaar linking",
                                "Collect Form 16 (salary)",
                                "Download Form 26AS",
                                "Gather deduction proofs",
                                "Verify capital gains documents"
                            ]
                        },
                        {
                            "step": 2,
                            "title": "Select ITR Form",
                            "actions": [
                                "List your income sources",
                                "Check applicability for each ITR form",
                                "Choose based on income type"
                            ]
                        },
                        {
                            "step": 3,
                            "title": "Gather Documents",
                            "actions": [
                                "Form 16 (salary)",
                                "Form 26AS (TDS reconciliation)",
                                "Deduction proofs (80C, 80D, etc.)",
                                "Capital gains documents",
                                "Bank statements"
                            ]
                        },
                        {
                            "step": 4,
                            "title": "File Online",
                            "actions": [
                                "Login to incometaxindiaefiling.gov.in",
                                "Fill ITR form",
                                "Validate entries",
                                "Submit digitally"
                            ]
                        },
                        {
                            "step": 5,
                            "title": "E-Verify",
                            "actions": [
                                "E-sign with DSC (within 30 days)",
                                "Or use EVC (OTP method)",
                                "Without verification = Invalid return!"
                            ]
                        }
                    ]
                }
            },
            "capital_gains": {
                "patterns": ["capital gains", "equity gains", "stock sale", "mutual fund sale", "property sale", "long term", "short term"],
                "training": {
                    "title": "Capital Gains Taxation",
                    "content": """Capital gains = Profit from selling assets
                    
                    EQUITY SHARES/MUTUAL FUNDS:
                    • Hold ≤ 12 months = Short-term (30% tax)
                    • Hold > 12 months = Long-term (15% tax)
                    
                    REAL ESTATE:
                    • Hold ≤ 2 years = Short-term (slab rate)
                    • Hold > 2 years = Long-term (20% with indexation)
                    
                    INDEXATION BENEFIT:
                    • Available for long-term property sales
                    • Adjusts cost for inflation
                    • Only old regime benefit"""
                },
                "execution": {
                    "title": "Calculate Capital Gains",
                    "template": {
                        "asset": "Choose: Equity/MF/Property/Others",
                        "purchase_date": "When did you buy?",
                        "purchase_price": "Cost (including brokerage)",
                        "sale_date": "When did you sell?",
                        "sale_price": "Selling price (net)",
                        "calculation": "Gain = Sale - Purchase - Costs"
                    }
                }
            }
        }
        
        # GST KNOWLEDGE BASE
        self.gst_kb = {
            "gst_registration": {
                "patterns": ["register gst", "gst registration", "how to register", "gstin", "apply gst"],
                "training": {
                    "title": "GST Registration Basics",
                    "content": """GST Registration is mandatory if:
                    • Turnover > ₹20 Lakhs (goods)
                    • Turnover > ₹10 Lakhs (services)
                    • Inter-state supplies
                    
                    Documents needed:
                    • PAN (permanent account number)
                    • Aadhaar (proprietor/partners)
                    • Business documents
                    • Bank details
                    • Proof of place of business
                    
                    Timeline: 8-15 days from submission"""
                },
                "execution": {
                    "title": "Register for GST - Step by Step",
                    "steps": [
                        "Create account on GST portal",
                        "Fill Form GST REG-01",
                        "Upload required documents",
                        "Submit application",
                        "Track status (8-15 days)",
                        "Receive GSTIN"
                    ]
                }
            },
            "gstr_1_filing": {
                "patterns": ["gstr-1", "gstr 1", "supplier return", "outward supply", "file gstr-1"],
                "training": {
                    "title": "GSTR-1 Return Filing",
                    "content": """GSTR-1 is the return filed by suppliers.
                    
                    Reports:
                    • All outward supplies (sales)
                    • Exports
                    • Amendments to previous GSTR-1
                    
                    Filing Frequency:
                    • Monthly (11th day of next month)
                    • Quarterly (if turnover < ₹5 Cr and opted)
                    
                    Key points:
                    • Invoice details must match GSTR-2A
                    • High mismatch = ITC blocked for buyer
                    • Amendments allowed"""
                },
                "execution": {
                    "title": "File GSTR-1 - Complete Guide",
                    "checklist": [
                        "Compile all sales invoices",
                        "Classify by tax rate (0%, 5%, 12%, 18%, 28%)",
                        "Separate taxable from exempt supplies",
                        "Prepare summaryby GST rate",
                        "Login to GST portal",
                        "Fill GSTR-1 with summary",
                        "Validate and submit before due date"
                    ]
                }
            }
        }
        
        # ACCOUNTING KNOWLEDGE BASE
        self.accounting_kb = {
            "journal_entry": {
                "patterns": ["journal entry", "debit credit", "double entry", "voucher entry"],
                "training": {
                    "title": "Double Entry Bookkeeping",
                    "content": """Every transaction has two sides:
                    
                    DEBIT:
                    • Increases assets
                    • Increases expenses
                    • Decreases liabilities/income
                    
                    CREDIT:
                    • Decreases assets
                    • Increases income/liabilities
                    • Decreases expenses
                    
                    Rule: Debit = Credit (always balanced!)
                    
                    Examples:
                    • Bought inventory for cash:
                      Dr. Inventory Cr. Cash
                    • Sold goods for profit:
                      Dr. Cash Cr. Sales Income"""
                },
                "execution": {
                    "title": "Make a Journal Entry",
                    "template": {
                        "date": "Transaction date",
                        "debit_account": "What goes up/in?",
                        "debit_amount": "Amount",
                        "credit_account": "What goes out/down?",
                        "credit_amount": "Same amount",
                        "narration": "Brief description"
                    }
                }
            },
            "bank_reconciliation": {
                "patterns": ["bank reconciliation", "reconcile bank", "match bank", "outstanding"],
                "training": {
                    "title": "Bank Reconciliation",
                    "content": """Matching book balance with bank statement.
                    
                    Common differences:
                    • Checks not cleared (outstanding)
                    • Deposits not credited (timing)
                    • Bank fees not recorded
                    • Errors in recording
                    
                    Process:
                    1. Get bank statement
                    2. Check all transactions posted
                    3. Find unmatched items
                    4. Record missing entries
                    5. Reconcile differences"""
                },
                "execution": {
                    "title": "Reconcile Your Bank Account",
                    "steps": [
                        "Get bank statement for period",
                        "List all book transactions",
                        "Check each against statement",
                        "Mark as matched/unmatched",
                        "List unmatched items with reasons",
                        "Record any missing bank items",
                        "Verify final balance matches"
                    ]
                }
            }
        }

    def _normalize_text(self, text: str) -> str:
        """Normalize text for keyword matching"""
        return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

    def _pattern_matches(self, query: str, patterns: List[str]) -> bool:
        """Check if any pattern matches the query"""
        normalized_query = self._normalize_text(query)
        query_lower = query.lower()

        for pattern in patterns:
            normalized_pattern = self._normalize_text(pattern)
            if normalized_pattern in normalized_query:
                return True

            exact_pattern = re.escape(pattern.lower())
            if re.search(rf"(?<![a-z0-9]){exact_pattern}(?![a-z0-9])", query_lower):
                return True

        return False

    def detect_operating_mode(self, query: str) -> OperatingMode:
        """Detect if user wants TRAINING, EXECUTION, or HYBRID"""
        query_lower = query.lower()
        
        training_score = sum(1 for kw in self.training_keywords if kw in query_lower)
        execution_score = sum(1 for kw in self.execution_keywords if kw in query_lower)
        
        # If both training and execution keywords present, it's HYBRID
        if training_score > 0 and execution_score > 0:
            return OperatingMode.HYBRID
        # If training keywords clearly dominate (esp. "teach", "explain", "learn")
        elif training_score > execution_score:
            return OperatingMode.TRAINING
        # If execution keywords present
        elif execution_score > training_score:
            return OperatingMode.EXECUTION
        # Default to HYBRID for ambiguous cases
        else:
            return OperatingMode.HYBRID

    def detect_module(self, query: str) -> TaxModule:
        """Detect which tax module (GST, ITR, Accounting) user is asking about"""
        query_lower = query.lower()
        
        # GST keywords
        gst_keywords = ["gst", "gstin", "gstr", "invoice", "input tax", "itc"]
        if any(kw in query_lower for kw in gst_keywords):
            return TaxModule.GST
        
        # Accounting keywords
        accounting_keywords = ["journal", "ledger", "debit", "credit", "invoice", "reconciliation", "bank", "tally"]
        if any(kw in query_lower for kw in accounting_keywords):
            return TaxModule.ACCOUNTING
        
        # Income tax is default
        return TaxModule.INCOME_TAX

    def find_best_match(self, query: str, knowledge_base: Dict) -> Optional[Tuple[str, Dict]]:
        """Find best matching topic in knowledge base"""
        for topic, data in knowledge_base.items():
            if self._pattern_matches(query, data["patterns"]):
                return topic, data
        return None

    def generate_training_response(self, topic: str, data: Dict, user_level: str = "beginner") -> str:
        """Generate detailed training mode response with comprehensive information"""
        training_data = data.get("training", {})
        title = training_data.get("title", "Tax Topic")
        content = training_data.get("content", "")
        examples = training_data.get("examples", [])
        
        # Start with a detailed introduction
        response = f"📚 **{title}**\n\n"
        response += f"{content}\n"
        
        # Include multiple examples for better understanding
        if examples:
            response += "\n**💡 Real Examples:**\n\n"
            for i, ex in enumerate(examples, 1):
                response += f"**Example {i}:**\n"
                if ex.get('scenario'):
                    response += f"• Situation: {ex.get('scenario')}\n"
                if ex.get('investment') or ex.get('premiums'):
                    response += f"• Details: {ex.get('investment') or ex.get('premiums')}\n"
                if ex.get('benefit') or ex.get('deduction'):
                    response += f"• Benefit: {ex.get('benefit') or ex.get('deduction')}\n"
                response += "\n"
        
        # Add key takeaways
        response += "**🎯 Key Points to Remember:**\n"
        response += "• Consult a tax professional for your specific situation\n"
        response += "• Keep all supporting documents for audit purposes\n"
        response += "• Plan your taxes well in advance\n"
        response += "• Different tax regimes have different benefits\n\n"
        
        response += "**👉 What would you like to know next?** Ask me about:\n"
        response += "• How to claim this benefit\n"
        response += "• Documents you'll need\n"
        response += "• Impact on your tax calculation\n"
        response += "• Comparison with other options\n"
        
        return response

    def generate_execution_response(self, topic: str, data: Dict) -> str:
        """Generate detailed execution mode response with comprehensive guidance"""
        execution_data = data.get("execution", {})
        title = execution_data.get("title", "Task")
        
        response = f"📋 **{title}**\n\n"
        
        # Handle checklist
        if "checklist" in execution_data:
            response += "**Here's your complete checklist:**\n\n"
            for i, item in enumerate(execution_data["checklist"], 1):
                response += f"{i}. **{item}**\n"
            response += "\n"
        
        # Handle steps
        elif "steps" in execution_data:
            response += "**Follow these detailed steps:**\n\n"
            for i, step_info in enumerate(execution_data["steps"], 1):
                if isinstance(step_info, dict):
                    step_title = step_info.get("title", "")
                    response += f"**Step {i}: {step_title}**\n"
                    actions = step_info.get("actions", [])
                    for j, action in enumerate(actions, 1):
                        response += f"  {j}. {action}\n"
                else:
                    response += f"**Step {i}: {step_info}**\n"
                response += "\n"
        
        # Handle documents
        if "documents" in execution_data:
            response += "**📄 Required Documents:**\n"
            for doc in execution_data["documents"]:
                response += f"• {doc}\n"
            response += "\n"
        
        # Add tips and best practices
        response += "**💡 Pro Tips:**\n"
        response += "• Keep digital and physical copies of all documents\n"
        response += "• Maintain a checklist as you complete each step\n"
        response += "• Submit at least 1-2 weeks before the deadline\n"
        response += "• Double-check all entries before final submission\n\n"
        
        response += "**❓ Need help?** Ask me:\n"
        response += "• How to complete any specific step\n"
        response += "• What happens after submission\n"
        response += "• Common mistakes to avoid\n"
        response += "• Timeline and deadlines\n"
        
        return response

    def generate_response(self, query: str, conversation: Optional[ConversationContext] = None) -> Dict:
        """Generate comprehensive response for any tax question"""
        
        # Create or use existing conversation
        if not conversation:
            conversation = ConversationContext("default_user")
        
        # Detect mode and module
        mode = self.detect_operating_mode(query)
        module = self.detect_module(query)
        
        # Update context
        conversation.update_context(mode, module)
        conversation.add_to_history("user", query)
        
        # Find best matching topic
        knowledge_base = self._get_knowledge_base(module)
        match_result = self.find_best_match(query, knowledge_base)
        
        if match_result:
            topic, data = match_result
            conversation.last_topic = topic
            
            if mode == OperatingMode.TRAINING:
                response_text = self.generate_training_response(topic, data, conversation.user_level)
                response_type = "lesson"
            elif mode == OperatingMode.EXECUTION:
                response_text = self.generate_execution_response(topic, data)
                response_type = "guide"
            else:  # HYBRID
                training_part = self.generate_training_response(topic, data, conversation.user_level)
                execution_part = self.generate_execution_response(topic, data)
                response_text = f"{training_part}\n\n**Or need step-by-step instructions?**\n\n{execution_part}"
                response_type = "hybrid"
        else:
            # Generate contextual response for the query
            response_text = self._generate_contextual_response(query, module)
            response_type = "contextual"
        
        # Add to conversation history
        conversation.add_to_history("bot", response_text, {"type": response_type})
        
        # Prepare next steps suggestions
        next_steps = self._get_next_steps(module, conversation)
        
        return {
            "response": response_text,
            "mode": mode.value,
            "module": module.value,
            "response_type": response_type,
            "next_steps": next_steps,
            "conversation": conversation
        }

    def _generate_contextual_response(self, query: str, module: TaxModule) -> str:
        """Generate detailed response for general tax questions"""
        query_lower = query.lower()
        
        # Income Tax related responses
        if module == TaxModule.INCOME_TAX:
            # Handle old regime vs new regime questions
            if any(word in query_lower for word in ["old regime", "new regime", "regime comparison", "which regime"]):
                return """📊 **Tax Regime Comparison: Old vs New**

**OLD REGIME (Till 31-Mar-2024 or optionally beyond):**

*How it works:*
• Keep all exemptions and deductions
• Reduce your taxable income with benefits
• Pay tax on remaining income

*Exemptions (Non-taxable income):*
• HRA (House Rent Allowance) - Only if paid separately
• LTA (Leave Travel Allowance) - Up to ₹36,000/year
• Transport allowance - ₹1,600/month
• Medical allowance - ₹15,000/month
• Special allowances - Check your employment contract

*Major Deductions (₹1.5L max):*
• Section 80C: ELSS, PPF, LIC, NSC, Home Loan Principal
• Section 80D: Health Insurance (₹25K individual, ₹50K family)
• Section 80E: Education Loan Interest (No limit)
• Home Loan Interest: ₹2L for self-occupied property

*Tax Rates (Old Regime FY 2024-25):*
• Up to ₹2.5L: No tax
• ₹2.5L - ₹5L: 5%
• ₹5L - ₹10L: 20%
• Above ₹10L: 30%

---

**NEW REGIME (From 01-Apr-2024):**

*How it works:*
• NO deductions (except few like 80CCD, 80E, 80G)
• Simpler slab structure
• Pay tax on gross income

*Tax Rates (New Regime FY 2024-25):*
• Up to ₹3L: No tax
• ₹3L - ₹6L: 5%
• ₹6L - ₹9L: 10%
• ₹9L - ₹12L: 15%
• ₹12L - ₹15L: 20%
• Above ₹15L: 30%

*Limited Deductions Allowed:*
• Section 80CCD(1B): ₹50K NPS contribution
• Section 80E: Education loan interest
• Section 80G: Charitable donations

---

**WHICH IS BETTER FOR YOU?**

**Choose OLD REGIME if:**
✅ Your income is ≤ ₹10L and you have deductions
✅ You invest regularly (₹1.5L+ in 80C items)
✅ You have home loan with interest
✅ You have health insurance or education expenses
✅ You want HRA/LTA exemptions

**Choose NEW REGIME if:**
✅ Your income is > ₹15L with few deductions
✅ You prefer simpler tax calculation
✅ You don't have major investment plans
✅ You want easier compliance

---

**REAL EXAMPLES:**

**Example 1 - Rahul (₹12L salary, married):**
- HRA ₹4L + LTA ₹2K = ₹4.02L exemption
- Taxable under Old Regime: ₹7.98L
- Tax @ 20% slab = ₹1.16L

- Under New Regime (no exemptions):
- Taxable: ₹12L
- Tax = ₹0 up to ₹3L + 5% on ₹3-6L (₹15K) + 10% on ₹6-9L (₹30K) + 15% on ₹9-12L (₹45K) = ₹90K
- **Old Regime saves: ₹26K** ✓

**Example 2 - Priya (₹25L income, high investments):**
- Old Regime taxable: ₹25L - ₹2.5L deductions = ₹22.5L = ₹5.65L tax
- New Regime taxable: ₹25L = ₹4L tax
- **New Regime saves: ₹1.65L** ✓

---

**KEY TAKEAWAY:**
Most salaried individuals benefit from OLD REGIME due to HRA/LTA exemptions and deductions. Business owners often prefer NEW REGIME for simplicity.

**Want to calculate for your specific situation?** Tell me:
• Your annual income
• Your status (salaried/business owner)
• Major deductions/exemptions you have"""
            
            # Handle Form 16 and TDS questions
            elif any(word in query_lower for word in ["form 16", "form16", "tds", "salary certificate", "26as"]):
                return """📄 **Form 16 & TDS - Complete Guide**

**FORM 16: What It Shows**

Form 16 is your salary income certificate showing:
• Your salary details (basic, HRA, allowances, etc.)
• TDS deducted each month
• Total tax deducted for the year
• Employer's tax details and address

*Form 16 has 2 parts:*
1. **Part A:** Summary of income and TDS
2. **Part B:** Month-by-month breakdown

---

**IMPORTANT INFORMATION IN FORM 16:**

**Employee Information:**
• Name, PAN, Address
• Designation, Department
• Date of joining/leaving

**Salary Details:**
• Basic salary
• HRA (House Rent Allowance)
• Medical allowance
• Travel allowance
• Dearness allowance
• Other allowances/perks

**Tax Details:**
• Gross salary (total of all)
• Taxable salary (after exemptions)
• TDS deducted (month-wise and total)
• Advance tax paid (if any)

---

**HOW TO USE FORM 16 FOR ITR FILING:**

1. **Verify Income:**
   - Check salary matches your bank statements
   - Verify HRA/LTA amounts
   - Check for errors before filing ITR

2. **Verify TDS:**
   - Compare Form 16 TDS with Form 26AS (govt record)
   - TDS should match between them
   - Report discrepancies to employer if difference > ₹100

3. **Use in ITR:**
   - Copy salary info from Part A to ITR Form
   - TDS claimed as tax credit against final tax
   - If TDS > tax due = refund

---

**TDS RECONCILIATION PROCESS:**

**Step 1: Get Form 26AS** (Free from income-tax.gov.in)
- Shows TDS govt has record of
- Compare with Form 16 TDS
- Should be identical

**Step 2: Check for Discrepancies**
- Form 16 TDS ≠ Form 26AS TDS?
- **Likely causes:**
  - TDS deposited late by employer
  - Wrong PAN used
  - Multiple TDS entries by different employers
  - TDS credit not updated yet in ITAX system

**Step 3: Resolve Issues**
- Contact HR immediately if difference > ₹500
- File ITR with Form 16 amount initially
- Updated amount auto-reflects in Form 26AS later
- Can claim correct TDS during ITR filing

---

**COMMON TDS QUESTIONS:**

❓ **What if Form 16 TDS is wrong?**
- Inform employer HR immediately
- Request corrected Form 16
- Some employers send revised copies automatically
- You can file ITR with correct amount

❓ **Form 16 not received yet?**
- Legally, must be given by 31-May
- Contact HR for issue
- Can file ITR estimate initially, update when received
- If employer refuses: RTI application or tax notice complaint

❓ **What if TDS matches neither Form 16 nor 26AS?**
- 3-way mismatch is rare
- Contact income-tax helpline
- Usually resolves within 2-3 months

---

**NEXT STEPS:**

1. Verify Form 16 matches your salary slips
2. Download Form 26AS from income-tax.gov.in
3. Match TDS between both documents
4. File ITR with Form 16 information
5. Monitor Form 26AS for TDS updates

**Questions?** Ask me about:
• Specific salary components in your Form 16
• How to download Form 26AS
• Step-by-step ITR filing process
• TDS credit claiming process"""
            
            elif any(word in query_lower for word in ["benefit", "advantage", "advantage", "help", "useful", "better"]):
                return """💡 **Understanding Tax Benefits & Advantages**

Tax benefits work in different ways:

**Deductions:** Reduce your taxable income
• Example: ₹1.5L investment → ₹1.5L less taxable income
• Benefit depends on your tax slab (10%, 20%, 30%)
• Example: 30% slab × ₹1.5L = ₹45,000 savings

**Exemptions:** Income that's not taxable at all
• HRA for salaried employees
• LTA for eligible travel
• Certain allowances and perks

**Credits:** Direct reduction in tax payable
• More valuable than deductions
• Example: ₹10K credit = ₹10K less tax

**Planning Tips:**
1. Maximize exemptions first (automatic benefits)
2. Then utilize deductions strategically
3. Consider old vs new regime annually
4. Plan early in the financial year

**Which benefit interests you?** Tell me about:
• Your income source (salary/business/investment)
• Current monthly income
• Major expenses
• Any specific goal"""
            
            elif any(word in query_lower for word in ["save", "reduce", "minimize", "optimize", "planning"]):
                return """🎯 **Tax Saving Strategies & Planning**

**Strategic Planning Approach:**

**Quarter 1-2 (Apr-Sep):**
• Review current year income projection
• Assess likely tax slab
• Identify available deductions
• Start ELSS/PPF/insurance investments
• Plan home loan payments

**Quarter 3 (Oct-Nov):**
• Accelerate investments if needed
• File advance tax if required
• Review TDS applicability
• Consider NPS additional contribution

**Quarter 4 (Dec-Jan):**
• Complete pending investments
• Finalize documents
• Prepare for ITR filing
• Plan next year strategy

**Tax-Saving Investment Options (≤ ₹1.5L total):**
1. **PPF** (Public Provident Fund) - Safe, ₹50K minimum
2. **ELSS** (Equity Mutual Funds) - Growth-oriented
3. **LIC/Insurance** - Protection + tax benefit
4. **NSC** (National Savings Certificate) - Government security
5. **Home Loan Principal** - Self-occupied property
6. **Education Fees** - School/college fees
7. **EPF Contribution** - Automatic from salary

**Advanced Options:**
• Section 80CCD(1B): ₹50K extra for NPS
• Section 80D: Health insurance (≤₹25K individual)
• Section 80E: Education loan interest (unlimited)

**Quick Assessment:**
To give you best recommendations, tell me:
1. Your annual income
2. Current tax slab estimate
3. Existing investments
4. Financial goals (retirement, education, home)"""
            
            elif any(word in query_lower for word in ["deadline", "date", "when", "time", "by"]):
                return """📅 **Important Tax Dates & Deadlines**

**FY 2024-25 (Tax year ending 31-Mar-2025):**

**January-March:**
• 31-Jan: Advance tax Q4 installment due
• Throughout: Continue investments, collect proofs

**April-May (Next FY start):**
• 31-May: ITR filing deadline (last date typically)
• Earlier filing gets faster refunds

**June-July:**
• 31-Jul: Extended ITR deadline (if needed)
• After this: 200% penalty applies

**ITR Filing Specifics:**
• **Normal deadline:** 31-Jul following the financial year
• **Extended deadline:** 31-Oct (with late filing fee)
• **E-verification deadline:** Within 30 days of filing

**Quarter Advance Tax Due Dates:**
• Q1 (Apr): 15-Jun
• Q2 (Jul): 15-Sep
• Q3 (Oct): 15-Dec
• Q4 (Jan): 31-Jan

**Other Important Dates:**
• 31-Aug: Monsoon assessment filing deadline
• 15-Jun: Estimated advance tax payment (if applicable)
• Anytime: Respond to tax notices within 30 days

**Pro Tip:** File 2-3 weeks before deadline to avoid last-minute issues

**What timeline question do you have?**"""
            
            else:
                return """📊 **Comprehensive Income Tax Guidance**

I can help you with detailed information on:

**Income Classification:**
• Salary (Form 16, TDS reconciliation)
• Capital gains (equity, real estate, crypto)
• Business/Professional income
• Rental income from properties
• Interest and dividend income

**Deduction Planning:**
• Section 80C (₹1.5L for investments)
• Section 80D (health insurance)
• Section 80E (education loan interest)
• Home loan interest (₹2L for self-occupied)
• Donations, education, NPS, and more

**Tax Regime Comparison:**
• Old regime with deductions and exemptions
• New regime with simpler tax rates
• Which is better for your situation

**Return Filing (ITR):**
• Choosing the right ITR form
• Step-by-step filing procedure
• E-verification options
• Deadline and penalties

**Documentation & Verification:**
• What Form 16 shows
• Understanding Form 26AS
• TDS reconciliation process
• Keeping audit-ready records

**Ask me anything about taxes!** For specific guidance, share:
• Your income type
• Annual income amount
• Current tax concerns
• Specific deductions you're considering"""
        
        # GST related responses
        elif module == TaxModule.GST:
            if any(word in query_lower for word in ["benefit", "advantage", "save", "reduce"]):
                return """💰 **GST Benefits & Tax Optimization**

**ITC (Input Tax Credit) Benefits:**
• Claim tax paid on business purchases
• Reduces your output tax liability
• Properly documented = significant savings

**Registration Benefits:**
• Ability to claim ITC
• Legal business recognition
• B2B credibility
• Separate business entity status

**Composition Scheme:**
• Fixed tax at 1-5% instead of regular rates
• No ITC required (can't claim)
• Simpler compliance
• Better for smaller businesses

**Ask for specific scenarios related to:**
• Your business type
• Annual turnover
• Whether you're B2B or B2C"""
            else:
                return self._generate_fallback_response(module)
        
        # Default comprehensive response
        else:
            return self._generate_fallback_response(module)

    def _get_knowledge_base(self, module: TaxModule) -> Dict:
        """Get appropriate knowledge base for module"""
        if module == TaxModule.GST:
            return self.gst_kb
        elif module == TaxModule.ACCOUNTING:
            return self.accounting_kb
        else:
            return self.income_tax_kb

    def _generate_fallback_response(self, module: TaxModule) -> str:
        """Generate comprehensive fallback response with detailed guidance"""
        if module == TaxModule.GST:
            return """📌 **GST & Indirect Tax Guidance**

I can provide comprehensive help on:

**Registration & Compliance:**
• GST Registration (eligibility by turnover, who needs it)
• Business Classification (goods, services, composition)
• Documents required and timeline for approval
• PAN, Aadhaar, and Business Registration linking

**Returns & Filing:**
• GSTR-1 (supplier return) - monthly or quarterly
• GSTR-2A & GSTR-2 (buyer returns and reconciliation)
• GSTR-3B (monthly/quarterly return)
• GSTR-4 (composition scheme)
• GSTR-9 (annual return)

**Tax Credits & Deductions:**
• Input Tax Credit (ITC) claims and restrictions
• Blocked credits (common scenarios)
• Amendment of previous returns
• Carry-forward of unused credits

**Invoicing & Compliance:**
• E-invoicing requirements and benefits
• E-way bills (when needed, how to generate)
• Invoice format and mandatory fields
• HSN/SAC classification

**Notices & Issues:**
• Responding to GST notices
• Common audit issues and resolutions
• Demand notices and appeals

What specific GST topic would you like to explore?"""
        
        elif module == TaxModule.ACCOUNTING:
            return """📌 **Accounting & Bookkeeping Guidance**

I can help with comprehensive accounting topics:

**Basic Concepts:**
• Double-entry bookkeeping fundamentals
• Debit and credit mechanics
• Account classification (assets, liabilities, equity)
• The accounting equation

**Daily Operations:**
• Journal entries (types and examples)
• Ledger posting and subsidiary ledgers
• Transaction reconciliation
• Month-end closing procedures

**Financial Management:**
• Bank reconciliation (matching book vs bank)
• Inventory accounting (FIFO, LIFO, weighted average)
• Accounts payable and receivable aging
• Depreciation calculations

**Financial Reporting:**
• Profit & Loss Statement (Income Statement)
• Balance Sheet (Statement of Position)
• Cash Flow Statement
• Ratio analysis and financial interpretation

**Compliance & Audit:**
• Audit-ready documentation
• Record retention requirements
• Internal controls and checks
• Trial balance and adjustments

What accounting topic would you like to understand better?"""
        
        else:  # Income Tax
            return """📌 **Income Tax & Tax Planning Guidance**

I can provide detailed guidance on:

**Income Sources & Taxation:**
• Salary income and house property income
• Capital gains (short-term and long-term)
• Dividend and interest income
• Business and professional income
• Rental and other income

**Deductions & Exemptions:**
• Section 80C (₹1.5L investment limit) - ELSS, PPF, LIC, etc.
• Section 80D (health insurance premiums)
• Section 80E (education loan interest)
• Section 80G (charitable donations)
• Section 24B (home loan interest)
• HRA, LTA, standard deduction, and more

**Tax Planning & Optimization:**
• Old vs New tax regime comparison
• Tax-saving investment strategies
• Optimal deduction planning
• Tax year-end planning

**Filing & Compliance:**
• ITR form selection (ITR-1, ITR-2, ITR-3, ITR-4, etc.)
• Step-by-step ITR filing process
• E-filing and e-verification
• Deadline and penalty information

**Documents & Verification:**
• Form 16 (salary certificate) interpretation
• Form 26AS (tax credit summary)
• TDS (Tax Deducted at Source) reconciliation
• AIS and TIS reports

**Notices & Assessments:**
• Understanding tax notices
• Audit and scrutiny assessment
• Responding to demands
• Appeal procedures

**Special Topics:**
• NPS (National Pension Scheme) benefits
• Gratuity and leave encashment taxation
• Foreign income and NRI taxation
• Advance tax and installment obligations

What's your tax-related question? Be as specific as possible for the best answer!"""

    def _get_next_steps(self, module: TaxModule, conversation: ConversationContext) -> List[str]:
        """Generate next steps based on context"""
        if module == TaxModule.GST:
            return ["Explain GST registration", "Show GSTR-1 filing steps", "Calculate ITC benefit"]
        elif module == TaxModule.ACCOUNTING:
            return ["Create a journal entry", "Reconcile bank account", "Generate financial statement"]
        else:  # Income Tax
            return [
                "Calculate my tax", 
                "Show deduction options",
                "Help with ITR filing",
                "Explain capital gains"
            ]
