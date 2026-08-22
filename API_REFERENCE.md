# TaxMate AI - API Reference

## Base URL
```
http://localhost:5000/api
```

## Authentication
Currently no authentication required. Future versions should implement JWT tokens.

---

## Endpoints

### 1. User Management

#### Create User
```http
POST /users
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "9876543210",
  "pan": "AAAPA1234A",
  "age": 35,
  "state": "Maharashtra"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "9876543210",
  "pan": "AAAPA1234A",
  "age": 35,
  "state": "Maharashtra",
  "created_at": "2024-01-15T10:30:00"
}
```

#### Get User
```http
GET /users/{user_id}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "9876543210",
  "pan": "AAAPA1234A",
  "age": 35,
  "state": "Maharashtra",
  "created_at": "2024-01-15T10:30:00"
}
```

---

### 2. Tax Filing

#### Create Tax Filing
Initiates a new tax filing record with income and deduction data.

```http
POST /tax-filing
Content-Type: application/json

{
  "user_id": 1,
  "filing_year": 2024,
  "income_data": {
    "salary": 1200000,
    "interest": 50000,
    "dividend": 100000,
    "rental_income": 0,
    "professional_fees": 0
  },
  "deductions_data": {
    "investments": 150000,
    "health_insurance": 25000,
    "education_loan_interest": 0,
    "home_loan_interest": 200000,
    "donations": 50000,
    "medical_expenses": 0
  },
  "tds_paid": 150000,
  "advance_tax_paid": 0
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "filing_year": 2024,
  "status": "draft",
  "total_income": 1350000,
  "total_deductions": 425000,
  "tax_old_regime": 210000,
  "tax_new_regime": 190000,
  "recommended_regime": "new",
  "created_at": "2024-01-15T10:30:00"
}
```

#### Analyze Filing (Main Agent Execution)
Triggers all 3 agents (Tax, Risk, Strategy) to process the filing.

```http
POST /analyze/{filing_id}
```

**Response (200 OK):**
```json
{
  "filing_id": 1,
  "total_income": 1350000,
  "total_deductions": 425000,
  "taxable_income": 925000,
  "tax_old_regime": 210000,
  "tax_new_regime": 190000,
  "recommended_regime": "new",
  "potential_savings": 20000,
  "audit_risk_score": 3.2,
  "audit_risk_level": "GREEN",
  "missed_deductions": [
    {
      "deduction": "80G Donations",
      "potential_savings": 15000,
      "description": "Consider donating to registered charities",
      "action": "Donate ₹50K-100K to registered NGOs"
    }
  ],
  "next_best_actions": [
    {
      "priority": 1,
      "action": "Claim 80EMI Home Loan Interest",
      "details": "You didn't claim home loan interest deduction",
      "deadline": "Before March 31",
      "impact": "Reduce tax liability"
    }
  ]
}
```

#### Get Analysis Results
```http
GET /results/{filing_id}
```

**Response (200 OK):**
```json
{
  "filing_id": 1,
  "status": "analyzed",
  "total_income": 1350000,
  "total_deductions": 425000,
  "tax_old_regime": 210000,
  "tax_new_regime": 190000,
  "recommended_regime": "new",
  "tax_agent_output": {
    "total_income": 1350000,
    "deductions": {
      "matched_deductions": {
        "80c_investments": 150000,
        "80d_health_insurance": 25000,
        "80e_education_loan": 0,
        "80emi_home_loan": 200000,
        "80g_donations": 50000
      },
      "total_deductions": 425000
    },
    "tax_old_regime": {
      "gross_income": 1350000,
      "total_deductions": 425000,
      "standard_deduction": 50000,
      "taxable_income": 875000,
      "tax_before_cess": 185000,
      "health_education_cess": 35000,
      "total_tax": 210000,
      "regime": "old"
    },
    "tax_new_regime": {
      "gross_income": 1350000,
      "standard_deduction": 75000,
      "taxable_income": 925000,
      "tax_before_cess": 169000,
      "health_education_cess": 21000,
      "total_tax": 190000,
      "regime": "new"
    }
  },
  "risk_agent_output": {
    "audit_flags": [],
    "overall_audit_risk_score": 3.2,
    "risk_level": "GREEN",
    "total_flags": 0,
    "estimated_audit_probability": 5
  },
  "strategy_agent_output": {
    "next_actions": [
      {
        "priority": 1,
        "action": "Claim 80EMI Home Loan Interest",
        "details": "Home loan interest not claimed",
        "deadline": "Before March 31",
        "impact": "Reduce tax liability"
      }
    ],
    "missed_deductions": [
      {
        "deduction": "80G Donations",
        "potential_savings": 15000,
        "description": "Donate to registered charities",
        "action": "Donate ₹50K-100K"
      }
    ]
  }
}
```

---

### 3. Dashboard

#### Get User Dashboard
```http
GET /dashboard/{user_id}
```

**Response (200 OK):**
```json
{
  "user_id": 1,
  "total_income": 1350000,
  "total_tax_liability": 190000,
  "effective_tax_rate": 14.1,
  "total_deductions": 425000,
  "recommended_regime": "new",
  "potential_savings": 20000,
  "last_updated": "2024-01-15T10:35:00"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request format"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently no rate limiting. Production deployment should implement:
- 100 requests per minute per IP
- 1000 requests per hour per user

---

## Pagination

For future list endpoints:
```http
GET /endpoint?skip=0&limit=10
```

---

## Example Workflow

### Step 1: Create User
```bash
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "phone": "9876543210",
    "pan": "AAAPA1234A",
    "age": 35,
    "state": "Maharashtra"
  }'
```

### Step 2: Create Tax Filing
```bash
curl -X POST http://localhost:5000/api/tax-filing \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "filing_year": 2024,
    "income_data": {
      "salary": 1200000,
      "interest": 50000,
      "dividend": 100000,
      "rental_income": 0,
      "professional_fees": 0
    },
    "deductions_data": {
      "investments": 150000,
      "health_insurance": 25000,
      "education_loan_interest": 0,
      "home_loan_interest": 200000,
      "donations": 50000,
      "medical_expenses": 0
    },
    "tds_paid": 150000,
    "advance_tax_paid": 0
  }'
```

### Step 3: Analyze Filing (All Agents Run)
```bash
curl -X POST http://localhost:5000/api/analyze/1
```

### Step 4: Get Results
```bash
curl http://localhost:5000/api/results/1
```

### Step 5: Get Dashboard
```bash
curl http://localhost:5000/api/dashboard/1
```

---

## Agent Output Explanation

### Tax Agent Output
- `tax_old_regime`: Tax liability with deductions (~30% of income)
- `tax_new_regime`: Tax without most deductions (~14% of income)
- `recommendation`: Which regime saves more tax
- `potential_savings`: ₹ difference between regimes

### Risk Agent Output
- `audit_flags`: Items flagged as risky
- `overall_audit_risk_score`: 0-10 (0=low, 10=high)
- `risk_level`: GREEN/YELLOW/RED
- `estimated_audit_probability`: Likelihood I-T will audit this filing

### Strategy Agent Output
- `next_best_actions`: Prioritized actions to take
- `missed_deductions`: Deductions user could have claimed
- `tax_saving_recommendations`: Investment suggestions
- `financial_health_score`: Overall financial wellness (0-100)

---

## Data Validation

### Income Data Validation
- Salary: ≥ 0
- Interest: ≥ 0
- Dividend: ≥ 0
- Rental: ≥ 0
- Professional: ≥ 0

### Deduction Data Validation
- Investments (80C): ≤ ₹1.5L
- Health Insurance (80D): ≤ ₹25K (or ₹50K if age > 60)
- Donations (80G): ≤ 50% of income
- Home Loan: No limit (but only interest)

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 400 | Bad Request - Invalid data |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Error - Server error |

---

## Next Development Steps

1. **Authentication**: Implement JWT with refresh tokens
2. **Rate Limiting**: Add request throttling
3. **Caching**: Cache benchmark data for performance
4. **Webhooks**: Notify on filing completion
5. **Export**: Generate PDF/ITR-V file
6. **Multi-language**: Add Hindi UI
7. **Mobile App**: React Native version
8. **CA Integration**: Connect with CA portal

---

## Support

For API issues:
1. Check error message
2. Verify input data format
3. Check server logs: `docker logs taxmate_backend`
4. Create GitHub issue with details
