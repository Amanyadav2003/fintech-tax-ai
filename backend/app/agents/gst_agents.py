"""
GST AGENTS - Virtual Tax Professional GST Module
Handles GST Registration, Return Filing, ITC Validation, E-invoicing, and Notices
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class GSTRegistrationAgent:
    """Guides businesses through GST registration process"""
    
    def __init__(self):
        self.eligibility_thresholds = {
            "goods": 2000000,  # ₹20 Lakhs
            "services": 1000000,  # ₹10 Lakhs
            "all_persons": 500000  # ₹5 Lakhs for certain categories
        }
        
        self.required_documents = {
            "proprietorship": [
                "Aadhaar of proprietor",
                "PAN of proprietor",
                "Business address proof (utility bill, rent agreement)",
                "Bank account statement (last 3 months)",
                "Proof of business authorization",
                "Identity and address proof of authorized signatory"
            ],
            "partnership": [
                "Aadhaar of all partners",
                "PAN of all partners",
                "Partnership deed",
                "Identity and address proof of authorized signatory",
                "Business address proof",
                "Bank account statement"
            ],
            "company": [
                "Certificate of Incorporation",
                "PAN of company",
                "Aadhaar of director",
                "Board resolution",
                "Business address proof",
                "Bank account statement"
            ]
        }
    
    def check_registration_eligibility(self, business_data: Dict) -> Dict:
        """Check if business qualifies for GST registration"""
        turnover = business_data.get("annual_turnover", 0)
        business_type = business_data.get("type", "")  # goods, services, mixed
        category = business_data.get("category", "")  # interstate, import/export, etc.
        
        eligible = False
        reason = ""
        
        # Check eligibility rules
        if business_type == "goods" and turnover > self.eligibility_thresholds["goods"]:
            eligible = True
        elif business_type == "services" and turnover > self.eligibility_thresholds["services"]:
            eligible = True
        elif business_type == "mixed":
            if turnover > self.eligibility_thresholds["goods"]:
                eligible = True
        
        # Special cases
        if "interstate" in category or "import" in category or "export" in category:
            if turnover > 0:  # Compulsory registration even below threshold
                eligible = True
        
        return {
            "eligible": eligible,
            "reason": reason,
            "next_steps": self._get_registration_steps() if eligible else []
        }
    
    def get_registration_checklist(self, entity_type: str) -> Dict:
        """Get documents and checklist for registration"""
        return {
            "documents_required": self.required_documents.get(entity_type.lower(), []),
            "steps": [
                {
                    "step": 1,
                    "title": "Create Account on GST Portal",
                    "description": "Go to www.gst.gov.in, click 'Register Now'",
                    "documents": ["Email ID", "Mobile Number"]
                },
                {
                    "step": 2,
                    "title": "Fill Form GST REG-01",
                    "description": "Provide business and personal details",
                    "documents": ["PAN", "Business details", "Address proof"]
                },
                {
                    "step": 3,
                    "title": "Upload Supporting Documents",
                    "description": "Upload all required documents",
                    "documents": self.required_documents.get(entity_type.lower(), [])
                },
                {
                    "step": 4,
                    "title": "Submit Application",
                    "description": "Review and submit application",
                    "documents": []
                },
                {
                    "step": 5,
                    "title": "Verification (if required)",
                    "description": "GST officer may seek clarifications",
                    "documents": ["Documents as requested"]
                },
                {
                    "step": 6,
                    "title": "Receive GSTIN",
                    "description": "GSTIN issued (usually 8-15 days)",
                    "documents": ["Certificate of registration"]
                }
            ],
            "timeline": "8-15 business days",
            "fees": "No registration fee"
        }
    
    def _get_registration_steps(self) -> List[str]:
        """Get registration process steps"""
        return [
            "Create account on GST portal",
            "Fill Form GST REG-01 with accurate details",
            "Upload all required documents",
            "Submit and wait for verification",
            "Respond to any GST officer queries",
            "Receive GSTIN and certificate"
        ]


class GSTRFilingAgent:
    """Handles GSTR filing (GSTR-1, GSTR-3B, GSTR-9, GSTR-9C)"""
    
    def __init__(self):
        self.return_types = {
            "gstr_1": {
                "name": "GSTR-1 (Outward Supply Return)",
                "filed_by": "Registered businesses",
                "frequency": "Monthly or Quarterly",
                "due_date_month": "11th day of next month",
                "due_date_quarter": "14th of next month",
                "purpose": "Report outward supplies (sales)"
            },
            "gstr_3b": {
                "name": "GSTR-3B (Self-Assessment Return)",
                "filed_by": "All registered businesses",
                "frequency": "Monthly",
                "due_date_month": "20th of next month",
                "purpose": "Report inward + outward supplies and calculate liability"
            },
            "gstr_9": {
                "name": "GSTR-9 (Annual Return)",
                "filed_by": "All registered businesses",
                "frequency": "Annually",
                "due_date": "31 December (next FY)",
                "purpose": "Annual consolidated return with reconciliation"
            },
            "gstr_9c": {
                "name": "GSTR-9C (Reconciliation Statement)",
                "filed_by": "Businesses with annual turnover > ₹2 Cr",
                "frequency": "Annually",
                "due_date": "31 January (next FY)",
                "purpose": "Reconcile books with filed returns"
            }
        }
    
    def get_filing_checklist(self, return_type: str, period: str) -> Dict:
        """Get filing checklist for specific return type"""
        return_info = self.return_types.get(return_type.lower(), {})
        
        if return_type.lower() == "gstr_1":
            checklist = [
                "Compile all sales invoices for the period",
                "Separate invoices by HSN/SAC",
                "Classify by tax rate (0%, 5%, 12%, 18%, 28%)",
                "List B2B invoices with GSTIN",
                "List B2C invoices (total)",
                "List exports (if any)",
                "Verify amendment or credit notes",
                "Review debit notes issued",
                "Check for exempted supplies",
                "Prepare summary schedule",
                "Validate against GSTR-2A (received)",
                "Check for discrepancies",
                "File before due date"
            ]
        elif return_type.lower() == "gstr_3b":
            checklist = [
                "Prepare GSTR-1 (summary of sales)",
                "Prepare GSTR-2A (summary of purchases)",
                "Calculate input tax credit (ITC) claimed",
                "List ITC blocked (if any)",
                "Calculate total tax payable",
                "Check advance tax already paid",
                "Calculate net liability/refund",
                "File GSTR-3B before due date",
                "Pay liability if any",
                "Obtain acknowledgment"
            ]
        elif return_type.lower() == "gstr_9":
            checklist = [
                "Gather all monthly GSTR-1 data",
                "Gather all GSTR-3B data",
                "Compile annual turnover",
                "List amendments made during year",
                "Prepare summary by HSN/SAC",
                "Calculate annual ITC claimed",
                "List any debit/credit notes issued",
                "Prepare advance tax reconciliation",
                "Check amendment history",
                "File GSTR-9 before deadline"
            ]
        else:  # GSTR-9C
            checklist = [
                "Get books of accounts audited (if required)",
                "Gather auditor report",
                "Reconcile GSTR-9 with profit & loss statement",
                "Reconcile ITC claimed vs. actual consumption",
                "List any discrepancies and reasons",
                "Prepare auditor statement",
                "File GSTR-9C before deadline"
            ]
        
        return {
            "return_type": return_info.get("name", "Unknown"),
            "filing_frequency": return_info.get("frequency", ""),
            "due_date": return_info.get("due_date_month") or return_info.get("due_date", ""),
            "purpose": return_info.get("purpose", ""),
            "checklist": checklist
        }


class ITCAgent:
    """Handles Input Tax Credit (ITC) validation and optimization"""
    
    def __init__(self):
        self.blocked_credit_reasons = {
            "personal_expenses": {
                "description": "Personal or non-business expenses",
                "examples": ["Meals, entertainment (personal)", "Car repairs (personal vehicle)"],
                "solution": "ITC cannot be claimed on purely personal items"
            },
            "capital_goods": {
                "description": "Capital goods (with exceptions)",
                "examples": ["Building (most cases)", "Furniture"],
                "solution": "Some capital goods allow depreciation; check applicability"
            },
            "services": {
                "description": "Certain ineligible services",
                "examples": ["Financial services", "Insurance", "Education"],
                "solution": "ITC on specified ineligible services is blocked"
            },
            "supplies": {
                "description": "Supplies not used for business",
                "examples": ["Goods for personal use", "Gifts to employees"],
                "solution": "ITC only for business-related purchases"
            }
        }
    
    def validate_itc_claim(self, invoice_data: Dict) -> Dict:
        """Validate ITC claim on an invoice"""
        gstin = invoice_data.get("supplier_gstin", "")
        invoice_date = invoice_data.get("invoice_date", "")
        amount = invoice_data.get("amount", 0)
        category = invoice_data.get("category", "")  # goods, services, mixed
        
        validation_result = {
            "itc_allowed": True,
            "reasons_blocked": [],
            "itc_amount": invoice_data.get("tax_amount", 0),
            "suggestions": []
        }
        
        # Validation checks
        if not gstin or len(gstin) != 15:
            validation_result["itc_allowed"] = False
            validation_result["reasons_blocked"].append("Invalid GSTIN format")
        
        # Check if supplier is active
        # (In real implementation, check against GST registry)
        
        # Check invoice within 30 days
        try:
            inv_date = datetime.strptime(invoice_date, "%Y-%m-%d")
            if (datetime.now() - inv_date).days > 30:
                validation_result["reasons_blocked"].append("Invoice > 30 days old")
                validation_result["suggestions"].append("Claim GSTR-2A adjustment instead")
        except:
            pass
        
        return validation_result
    
    def reconcile_with_gstr_2a(self, business_gstr_1: List[Dict], gstr_2a: List[Dict]) -> Dict:
        """Reconcile filed GSTR-1 with received GSTR-2A"""
        reconciliation = {
            "total_invoices_filed": len(business_gstr_1),
            "total_invoices_received": len(gstr_2a),
            "matches": [],
            "discrepancies": [],
            "recommendations": []
        }
        
        # Find matches and discrepancies
        for filed_inv in business_gstr_1:
            matched = False
            for received_inv in gstr_2a:
                if (filed_inv.get("invoice_no") == received_inv.get("invoice_no") and
                    filed_inv.get("amount") == received_inv.get("amount")):
                    reconciliation["matches"].append(filed_inv)
                    matched = True
                    break
            
            if not matched:
                reconciliation["discrepancies"].append({
                    "invoice": filed_inv,
                    "issue": "Not found in GSTR-2A",
                    "action": "Check if invoice was received, contact supplier"
                })
        
        # Find invoices in GSTR-2A but not filed
        for received_inv in gstr_2a:
            if received_inv not in [m for m in reconciliation["matches"]]:
                reconciliation["discrepancies"].append({
                    "invoice": received_inv,
                    "issue": "Received but not in GSTR-1",
                    "action": "File amendment or adjust in next return"
                })
        
        return reconciliation


class EInvoicingAgent:
    """Handles e-invoicing and e-way bill workflows"""
    
    def generate_e_invoice_checklist(self) -> List[Dict]:
        """Generate e-invoicing workflow checklist"""
        return [
            {
                "step": 1,
                "title": "Check if E-invoicing Applicable",
                "actions": [
                    "Business turnover > ₹20 Crores (mandatory from 01 Apr 2023)",
                    "B2B invoices must be e-invoiced",
                    "Interstate transactions mandatory"
                ]
            },
            {
                "step": 2,
                "title": "Register with Invoice Registration Portal (IRP)",
                "actions": [
                    "Create account on https://einvoice1.gst.gov.in",
                    "Integrate with accounting software"
                ]
            },
            {
                "step": 3,
                "title": "Generate Invoice with Required Data",
                "actions": [
                    "Invoice number and date",
                    "Buyer and seller GSTIN",
                    "Item details with HSN/SAC",
                    "Tax rates and amounts",
                    "Shipping details"
                ]
            },
            {
                "step": 4,
                "title": "Generate IRN (Invoice Reference Number)",
                "actions": [
                    "Submit invoice to IRP",
                    "IRP generates unique 64-character IRN",
                    "Receive JSON web token (JWT) response"
                ]
            },
            {
                "step": 5,
                "title": "Display QR Code on Invoice",
                "actions": [
                    "Print QR code on invoice copy",
                    "QR contains IRN and digital signature",
                    "Buyer can verify authenticity"
                ]
            },
            {
                "step": 6,
                "title": "File GSTR-1 with IRN",
                "actions": [
                    "GSTR-1 summary includes IRN",
                    "Provides audit trail",
                    "Matches with buyer's GSTR-2A"
                ]
            }
        ]
    
    def generate_e_way_bill_checklist(self, shipment: Dict) -> Dict:
        """Generate e-way bill checklist for shipment"""
        return {
            "description": "E-way bill required for goods movement > ₹50,000",
            "checklist": [
                "Prepare shipment details",
                "Get transporter ID (TID) from transporter",
                "Prepare consignment information",
                "Login to e-way bill portal (ewaybillgst.gov.in)",
                "Enter invoice/delivery challan details",
                "Enter supplier and consignee information",
                "Specify items and HSN codes",
                "Select transportation mode",
                "Generate e-way bill",
                "Share with transporter and receiver",
                "Print and carry during transit"
            ],
            "validity": "100 km: 1 day, >100 km: 10 days",
            "penalties_for_non_compliance": [
                "No e-way bill: ₹50,000 or 100% of applicable tax",
                "Excess quantity: Equivalent penalty",
                "Wrong details: Warnings and penalties"
            ]
        }


class GSTNoticeAgent:
    """Handles GST notices and professional replies"""
    
    def analyze_notice(self, notice_data: Dict) -> Dict:
        """Analyze GST notice and recommend action"""
        notice_type = notice_data.get("type", "")  # LTI, SCN, Show Cause
        deficiency = notice_data.get("deficiency", "")
        
        analysis = {
            "notice_type": notice_type,
            "severity": "low",
            "timeline": "",
            "recommended_actions": [],
            "documents_to_gather": []
        }
        
        if notice_type == "LTI":  # Letter to Initiate
            analysis["timeline"] = "15 days to respond"
            analysis["recommended_actions"] = [
                "Review the deficiency carefully",
                "Gather supporting documents",
                "Prepare detailed reply",
                "Submit before deadline"
            ]
            analysis["documents_to_gather"] = [
                "Relevant invoices",
                "Bank statements",
                "Purchase orders",
                "Delivery documents",
                "Correspondence with customer"
            ]
        
        elif notice_type == "SCN":  # Show Cause Notice
            analysis["severity"] = "high"
            analysis["timeline"] = "30 days to respond"
            analysis["recommended_actions"] = [
                "Consult GST consultant/CA",
                "Prepare detailed reply with evidence",
                "Consider options: Agree, Disagree, Partial Agree",
                "File reply before deadline",
                "Keep copy of submission"
            ]
        
        return analysis
    
    def draft_reply_template(self, notice_type: str, issue: str) -> str:
        """Generate professional notice reply template"""
        template = f"""
PROFESSIONAL REPLY TO GST NOTICE ({notice_type})

{issue}

Reference: Notice No. _____ dated _____
Response to: Deficiency item _____

Respectfully submitted,

1. FACTS OF THE CASE:
   [Describe the transaction/issue]

2. LEGAL POSITION:
   [Cite relevant sections of GST Act]

3. SUPPORTING DOCUMENTS:
   [List attached documents - invoices, bank statements, etc.]

4. EXPLANATION/CLARIFICATION:
   [Provide detailed explanation]

5. CONCLUSION:
   [Summary and request for resolution]

Attachments:
- [Document 1]
- [Document 2]
- [Document 3]

Submitted by: [Name, GSTIN, Signature]
Date: [Date]
        """
        return template
