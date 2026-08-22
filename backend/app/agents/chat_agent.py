"""
CHAT AGENT - AI Assistant for Tax Questions
Handles natural language queries about tax, deductions, and compliance
"""

import re
from typing import Dict, List, Optional
from .tax_agent import TaxAgent
from .risk_agent import RiskAgent
from .strategy_agent import StrategyAgent


class ChatAgent:
    """AI Chat Agent for tax-related questions"""

    def __init__(self):
        self.tax_agent = TaxAgent()
        self.risk_agent = RiskAgent()
        self.strategy_agent = StrategyAgent()
        
        # Tax knowledge base
        self.tax_knowledge = {
            "80c": {
                "questionPatterns": ["80c", "80 c", "section 80c", "investment", "elss", "ppf", "lic", "tax saving"],
                "response": "Section 80C allows deductions up to ₹1.5 Lakhs for ELSS mutual funds, PPF, LIC premium, NSC, EPF employee contribution, tuition fee, and home loan principal."
            },
            "80d": {
                "questionPatterns": ["80d", "80 d", "section 80d", "health insurance", "medical insurance", "health"],
                "response": "Section 80D provides deductions for health insurance premiums: up to ₹25K for self/spouse/children, ₹50K if a senior citizen, plus separate limits for parents."
            },
            "80e": {
                "questionPatterns": ["80e", "80 e", "section 80e", "education loan", "student loan"],
                "response": "Section 80E allows full deduction of education loan interest for self, spouse, or dependent. There is no monetary cap, only the interest component qualifies."
            },
            "80emi": {
                "questionPatterns": ["80emi", "80 emi", "home loan", "housing loan", "mortgage interest", "24b", "section 24"],
                "response": "Home loan interest on self-occupied property is generally deductible under Section 24(b) up to ₹2 Lakhs. Let-out property interest is treated differently and may be set off against house property income rules."
            },
            "80g": {
                "questionPatterns": ["80g", "80 g", "section 80g", "donation", "charity", "donate"],
                "response": "Section 80G provides deduction for eligible donations. The deduction rate may be 50% or 100% depending on the institution, and some donations are subject to income-based limits."
            },
            "80ccd_1b": {
                "questionPatterns": ["80ccd", "80ccd(1b)", "80ccd 1b", "nps", "national pension", "pension"],
                "response": "Section 80CCD(1B) provides an additional ₹50K deduction for NPS contributions, over and above the Section 80C limit."
            },
            "80gg": {
                "questionPatterns": ["80gg", "rent paid", "house rent", "hra not received", "rental deduction"],
                "response": "Section 80GG can help eligible taxpayers claim deduction for rent paid when HRA is not received, subject to income and rent conditions."
            },
            "80ttb": {
                "questionPatterns": ["80ttb", "senior citizen interest", "savings interest", "fixed deposit interest"],
                "response": "Section 80TTB allows senior citizens to claim deduction on interest income from savings, fixed deposits, and recurring deposits up to the applicable limit."
            },
            "80u": {
                "questionPatterns": ["80u", "disability deduction", "person with disability"],
                "response": "Section 80U provides a deduction for resident individuals with a certified disability, subject to prescribed conditions and disability levels."
            },
            "standard_deduction": {
                "questionPatterns": ["standard deduction", "standard", "salary deduction"],
                "response": "Standard deduction is automatically applied for eligible salaried taxpayers and pensioners. It reduces taxable salary income without needing proof of expenses."
            },
            "new_regime": {
                "questionPatterns": ["new regime", "new tax regime", "which regime", "better regime", "old regime", "tax regime"],
                "response": "The old regime allows many deductions and exemptions. The new regime usually has simpler slab rates with fewer deductions. The right choice depends on your income, investments, and exemptions."
            },
            "itr_filing": {
                "questionPatterns": ["itr", "how to file", "e-filing", "income tax return", "file itr"],
                "response": "ITR filing is an annual compliance requirement. Salary earners often use ITR-1, while freelancers and business taxpayers may need ITR-3 or ITR-4 depending on income type."
            },
            "tds": {
                "questionPatterns": ["tds", "tax deducted", "form 16", "form 26as", "certificate", "ais", "tis"],
                "response": "TDS is tax deducted at source. Form 16 shows salary TDS, while Form 26AS, AIS, and TIS help verify taxes already reported and credited while filing ITR."
            },
            "advance_tax": {
                "questionPatterns": ["advance tax", "quarterly tax", "due dates", "self assessment tax", "234b", "234c"],
                "response": "Advance tax applies when your estimated tax liability crosses the statutory threshold. Installment timelines and interest consequences vary by the type of shortfall."
            },
            "audit": {
                "questionPatterns": ["audit", "scrutiny", "income tax raid", "notice", "assessment", "intimation", "enquiry"],
                "response": "Audit or scrutiny risk usually increases when income, deductions, and tax credits do not align. Keep supporting documents, AIS/26AS, and proof of claims for several years."
            },
            "nps": {
                "questionPatterns": ["nps", "pension", "national pension", "80ccc", "80ccd"],
                "response": "NPS can provide deductions under multiple sections depending on contribution type, including an additional benefit under Section 80CCD(1B)."
            },
            "hra": {
                "questionPatterns": ["hra", "house rent allowance", "salary exemption"],
                "response": "HRA exemption is available under the old regime for salaried taxpayers who receive HRA and pay rent, subject to prescribed calculation rules and documentation."
            },
            "lta": {
                "questionPatterns": ["lta", "leave travel allowance", "travel exemption"],
                "response": "LTA exemption may be available for eligible travel expenses under the salary rules in the old regime, subject to employer policy and tax conditions."
            },
            "gratuity": {
                "questionPatterns": ["gratuity", "retirement benefit", "superannuation"],
                "response": "Gratuity may be partially or fully exempt depending on employment type and limits prescribed under tax law. The taxable portion depends on the structure of payment."
            },
            "leave_encashment": {
                "questionPatterns": ["leave encashment", "unused leave", "cash out leave"],
                "response": "Leave encashment has different tax treatment depending on whether it is received during service or on retirement, and on the employee category."
            },
            "capital_gains": {
                "questionPatterns": ["capital gains", "equity gains", "stock sale", "mutual fund sale", "property sale", "capital gain"],
                "response": "Capital gains taxation depends on the asset type and holding period. Equity, mutual funds, and property can each follow different short-term and long-term rules."
            },
            "house_property": {
                "questionPatterns": ["house property", "rental income", "self occupied", "let out property"],
                "response": "House property income is taxed separately from salary. Rent received, municipal taxes, and home-loan interest can affect the final taxable amount."
            },
            "business_income": {
                "questionPatterns": ["business income", "freelance income", "professional income", "consulting income", "presumptive"],
                "response": "Business or professional income may require ITR-3 or ITR-4, depending on the nature of income and whether presumptive taxation is available."
            },
            "pan_aadhaar": {
                "questionPatterns": ["pan aadhaar", "pan aadhar", "link aadhaar", "aadhaar linking"],
                "response": "PAN-Aadhaar linking is an important compliance step for many taxpayers. Failure to keep the linkage active can affect filing and transaction validity."
            },
            "e_verification": {
                "questionPatterns": ["e verify", "e-verification", "verify return", "itr verification", "e verify my return", "verify my return"],
                "response": "ITR e-verification is required after filing. If a return is not verified within the allowed timeline, it may be treated as invalid."
            },
            "refunds": {
                "questionPatterns": ["refund", "tax refund", "refund status", "reconciliation"],
                "response": "Refunds are generally issued after return processing if the taxes paid exceed the liability. Always reconcile Form 26AS/AIS with your return before filing."
            },
            "rebate_87a": {
                "questionPatterns": ["87a", "rebate", "tax rebate"],
                "response": "Section 87A can reduce the tax burden for eligible resident individuals, but availability depends on income level and the chosen tax regime."
            },
            "surcharge_cess": {
                "questionPatterns": ["surcharge", "cess", "health and education cess"],
                "response": "Surcharge and health/education cess are added on top of base tax for many taxpayers based on total income and applicable law."
            },
            "capital_gain_exemption": {
                "questionPatterns": ["54", "54f", "54ec", "capital gain exemption", "property reinvestment"],
                "response": "Capital gains exemptions under sections like 54, 54F, and 54EC can apply when sale proceeds are reinvested under the prescribed conditions."
            },
            "itr_deadlines": {
                "questionPatterns": ["deadline", "due date", "itr deadline", "filing date", "last date"],
                "response": "ITR deadlines change with CBDT notifications, but salaried taxpayers usually file by the notified due date for the relevant assessment year. Always verify the latest official deadline."
            }
        }

    def _normalize_text(self, text: str) -> str:
        """Normalize text for resilient keyword matching."""

        return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

    def _pattern_matches(self, query: str, patterns: List[str]) -> bool:
        """Return True when any pattern matches the query."""

        normalized_query = self._normalize_text(query)
        normalized_query_tokens = normalized_query.split()
        query_lower = query.lower()

        for pattern in patterns:
            normalized_pattern = self._normalize_text(pattern)

            if " " in normalized_pattern:
                if normalized_pattern and normalized_pattern in normalized_query:
                    return True
            elif normalized_pattern in normalized_query_tokens:
                return True

            exact_pattern = re.escape(pattern.lower())
            if re.search(rf"(?<![a-z0-9]){exact_pattern}(?![a-z0-9])", query_lower):
                return True

        return False

    def _compliance_overview(self) -> str:
        """Return a short overview of supported tax-law topics."""

        return (
            "I can help with Indian tax laws and compliance topics including: \n"
            "• ITR filing and deadlines\n"
            "• Salary, house property, capital gains, and business income\n"
            "• Deductions and exemptions (80C, 80D, 80E, 80G, 80CCD, 80GG, 80TTB, 80U)\n"
            "• TDS, Form 16, AIS/26AS/TIS, advance tax, and self-assessment tax\n"
            "• PAN-Aadhaar linking, e-verification, refunds, notices, and audit risk\n"
            "Ask me a section number, a compliance task, or a specific tax law topic."
        )

    def classify_intent(self, query: str) -> Dict:
        """Classify user query intent"""
        query_lower = query.lower()
        
        # Check for greetings
        if any(word in query_lower for word in ["hello", "hi", "hey", "start", "help"]):
            return {"intent": "greeting", "topic": None}
        
        # Check for thanks
        if any(word in query_lower for word in ["thanks", "thank", "great", "awesome"]):
            return {"intent": "thanks", "topic": None}

        # Explicit compliance and law questions should be handled before broad topic matching
        if any(word in query_lower for word in ["law", "laws", "compliance", "rules", "rule", "exemption", "notice", "deadline", "due date", "tax act"]):
            return {"intent": "compliance", "topic": None}
        
        # Match topics
        for topic, data in self.tax_knowledge.items():
            if self._pattern_matches(query, data["questionPatterns"]):
                return {"intent": "information", "topic": topic}

        # Broader compliance questions that are still not specific enough for a topic
        if any(word in query_lower for word in ["section", "deduction", "itr", "filing", "return", "tax"]):
            return {"intent": "compliance", "topic": None}
        
        # Check for analysis request
        if any(word in query_lower for word in ["calculate", "compute", "analyze", "my tax", "filing"]):
            return {"intent": "analysis", "topic": None}
        
        # Check for recommendations
        if any(word in query_lower for word in ["recommend", "suggest", "what should", "advice"]):
            return {"intent": "recommendation", "topic": None}
        
        return {"intent": "general", "topic": None}

    def generate_response(self, query: str, user_context: Optional[Dict] = None) -> Dict:
        """Generate response to user query"""
        intent_data = self.classify_intent(query)
        intent = intent_data["intent"]
        topic = intent_data["topic"]
        
        response_text = ""
        suggestions = []
        
        if intent == "greeting":
            response_text = "Namaste! I'm TaxBot, your AI tax assistant. Ask me about:\n• Tax deductions (80C, 80D, etc.)\n• ITR filing process\n• Audit risk\n• Tax-saving tips\n• Any tax question!"
            suggestions = ["Tell me about 80C", "How do I file ITR?", "What's my audit risk?"]
        
        elif intent == "thanks":
            response_text = "Welcome! Happy to help. Ask me anything more about taxes!"
            suggestions = ["What deductions can I claim?", "Calculate my tax", "Help with filing"]
        
        elif intent == "information" and topic:
            response_text = self.tax_knowledge[topic]["response"]
            # Generate relevant suggestions
            if topic == "80c":
                suggestions = ["Calculate my 80C savings", "Best 80C investments", "Max out 80C"]
            elif topic == "80d":
                suggestions = ["Health insurance tax benefit", "Calculate my tax", "Family coverage"]
            elif topic == "new_regime":
                suggestions = ["Compare both regimes", "Which is better for me?", "Calculate tax"]
            elif topic in ["itr_filing", "itr_deadlines", "e_verification"]:
                suggestions = ["Show filing steps", "What documents do I need?", "Check deadline"]
            elif topic in ["tds", "advance_tax", "refunds"]:
                suggestions = ["How do I reconcile taxes?", "What forms should I check?", "Explain compliance"]
            elif topic in ["capital_gains", "house_property", "business_income"]:
                suggestions = ["Which ITR form applies?", "How is it taxed?", "Show examples"]
            elif topic in ["80ccd_1b", "80gg", "80ttb", "80u", "pan_aadhaar"]:
                suggestions = ["Explain eligibility", "Show documents needed", "Compare with other deductions"]
            else:
                suggestions = ["Calculate my tax", "Other deductions", "File my ITR"]

        elif intent == "compliance":
            response_text = self._compliance_overview()
            suggestions = ["What is the ITR deadline?", "Explain Form 16 and 26AS", "Tell me about deductions"]
        
        elif intent == "analysis" or intent == "recommendation":
            # Generate tax analysis based on context
            if user_context and user_context.get("income_data"):
                income = user_context.get("income_data", {})
                income_data = {
                    "salary": income.get("salary", 0),
                    "interest": income.get("interest", 0),
                    "dividend": income.get("dividend", 0),
                    "rental_income": income.get("rental_income", 0),
                    "professional_fees": income.get("professional_fees", 0),
                }
                total_income = sum(income_data.values())
                
                if total_income > 0:
                    # Run tax agent
                    deductions_data = user_context.get("deductions_data", {})
                    tax_result = self.tax_agent.process_filing(income_data, deductions_data)
                    
                    recommended = tax_result["recommendation"]["recommended_regime"]
                    savings = tax_result["recommendation"]["potential_savings"]
                    
                    response_text = f"Based on your income of ₹{total_income:,}:\n• Recommended regime: {recommended.upper()}\n• Potential savings: ₹{savings:,.0f}\n\n"
                    
                    if savings > 10000:
                        response_text += f"🎯 You could save ₹{savings:,.0f} by choosing {recommended} regime!\n\n"
                    
                    # Add next best action
                    strategy_result = self.strategy_agent.get_next_best_actions(
                        user_context.get("user_profile", {}),
                        {"total_income": total_income, "tax_liability": tax_result["recommendation"][f"tax_{recommended}_regime"]},
                        {"risk_level": "GREEN", "audit_flags": []}
                    )
                    
                    if strategy_result:
                        response_text += f"💡 Next action: {strategy_result[0].get('action', 'N/A')}"
                    
                    suggestions = ["Show details", "Download report", "File ITR"]
                else:
                    response_text = "I'd be happy to analyze your taxes! Please share:\n• Your total income\n• Deductions (if any)\nThen I can calculate and provide recommendations."
                    suggestions = ["Upload income details", "How to add income?", "What deductions apply?"]
            else:
                response_text = "To provide tax analysis, please share:\n1. Your income (salary, interest, etc.)\n2. Deductions claimed (80C, 80D, etc.)\n\nOr I can explain general tax concepts!"
                suggestions = ["Tell me about deductions", "File ITR guide", "Tax tips"]
        
        else:
            # General query
            response_text = self._compliance_overview()
            suggestions = ["Tax calculations", "Deduction guide", "Filing process"]
        
        return {
            "response": response_text,
            "intent": intent,
            "topic": topic,
            "suggestions": suggestions,
            "requires_context": intent in ["analysis", "recommendation"]
        }

    def generate_follow_up(self, user_history: List[Dict]) -> Optional[str]:
        """Generate follow-up based on conversation history"""
        if not user_history:
            return None
        
        last_user_msg = None
        last_bot_msg = None
        
        for msg in reversed(user_history):
            if msg.get("role") == "user" and not last_user_msg:
                last_user_msg = msg.get("content", "")
            elif msg.get("role") == "assistant" and not last_bot_msg:
                last_bot_msg = msg.get("content", "")
            
            if last_user_msg and last_bot_msg:
                break
        
        if last_bot_msg and "80C" in last_bot_msg:
            return "How much have you invested in 80C this year?"
        elif last_bot_msg and "regime" in last_bot_msg.lower():
            return "Would you like me to calculate your exact tax under both regimes?"
        elif last_bot_msg and "deduction" in last_bot_msg.lower():
            return "Would you like personalized recommendations?"
        
        return None
