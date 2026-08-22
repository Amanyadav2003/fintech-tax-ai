"""
Unit tests for the tax chatbot agent.
"""

from app.agents.chat_agent import ChatAgent


class TestChatAgent:
    """Test chatbot routing and compliance knowledge coverage."""

    def setup_method(self):
        self.agent = ChatAgent()

    def test_routes_compliance_queries_to_compliance_intent(self):
        result = self.agent.generate_response("Explain tax compliance and ITR deadlines")

        assert result["intent"] == "compliance"
        assert result["requires_context"] is False
        assert "ITR filing and deadlines" in result["response"]
        assert len(result["suggestions"]) > 0

    def test_understands_nps_80ccd_1b_queries(self):
        result = self.agent.generate_response("Tell me about 80CCD(1B) and NPS savings")

        assert result["intent"] == "information"
        assert result["topic"] == "80ccd_1b"
        assert "₹50K" in result["response"]

    def test_understands_e_verification_queries(self):
        result = self.agent.generate_response("How do I e-verify my return?")

        assert result["intent"] == "information"
        assert result["topic"] == "e_verification"
        assert "e-verification" in result["response"].lower()

    def test_general_law_question_returns_tax_overview(self):
        result = self.agent.generate_response("List the major tax laws and compliances")

        assert result["intent"] == "compliance"
        assert "PAN-Aadhaar linking" in result["response"]
        assert "audit risk" in result["response"].lower()
