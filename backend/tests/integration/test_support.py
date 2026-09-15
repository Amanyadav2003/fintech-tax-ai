from uuid import uuid4

from app.routes.auth_routes import pending_registrations
from app.utils.security import SecurityManager


def unique_pan():
    return f"ABCDE{uuid4().int % 10000:04d}F"


def register_user(client, email):
    client.post('/api/auth/send-registration-otp', json={'email': email})
    otp = pending_registrations[email]['otp']
    assert client.post('/api/auth/verify-registration-otp', json={'email': email, 'otp': otp}).status_code == 200
    response = client.post('/api/auth/register', json={
        'email': email,
        'password': 'TestPassword123!',
        'name': 'Support Test User',
        'phone': '9876543210',
        'pan': unique_pan(),
        'age': 35,
        'state': 'Maharashtra',
        'employment_type': 'Salaried',
        'pan_aadhaar_linked': True,
        'financial_year': 'FY 2025-26 (AY 2026-27)',
    })
    assert response.status_code == 200
    return response


def test_user_support_ticket_ownership_and_admin_access(client, monkeypatch):
    owner_email = f'{uuid4().hex[:8]}@example.com'
    other_email = f'{uuid4().hex[:8]}@example.com'
    register_user(client, owner_email)
    ticket_response = client.post('/api/support/tickets', json={
        'subject': 'Need help',
        'category': 'Technical Issue',
        'description': 'The support drawer is not loading.',
    })
    assert ticket_response.status_code == 201
    ticket = ticket_response.json()
    assert ticket['ticket_code'].startswith('TM-')
    assert ticket['status'] == 'Open'

    assert client.post(f"/api/support/tickets/{ticket['id']}/messages", json={'message': 'Additional details'}).status_code == 200
    assert client.get('/api/support/tickets').json()[0]['id'] == ticket['id']

    client.post('/api/auth/logout')
    register_user(client, other_email)
    assert client.get(f"/api/support/tickets/{ticket['id']}").status_code == 404
    assert client.post(f"/api/support/tickets/{ticket['id']}/messages", json={'message': 'Not mine'}).status_code == 404
    assert client.get('/api/support/admin/tickets').status_code == 403


def test_support_admin_can_manage_tickets(client, monkeypatch):
    admin_email = f'{uuid4().hex[:8]}@example.com'
    monkeypatch.setenv('SUPPORT_ADMIN_EMAILS', admin_email)
    register_user(client, admin_email)
    ticket_response = client.post('/api/support/tickets', json={
        'subject': 'Admin test',
        'category': 'Tax Calculation',
        'description': 'Please review this question.',
    })
    ticket_id = ticket_response.json()['id']
    assert client.get('/api/support/admin/tickets').status_code == 200
    assert client.post(f'/api/support/admin/tickets/{ticket_id}/messages', json={'message': 'Support reply'}).status_code == 200
    status_response = client.patch(f'/api/support/admin/tickets/{ticket_id}/status', json={'status': 'Resolved'})
    assert status_response.status_code == 200
    assert status_response.json()['status'] == 'Resolved'
    assert client.get(f'/api/support/admin/tickets/{ticket_id}').json()['messages']
