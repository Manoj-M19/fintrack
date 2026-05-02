import pytest


async def get_token(client) -> str:
    await client.post("/api/v1/auth/register", json={
        "email": "expense_user@example.com",
        "full_name": "Expense User",
        "password": "Secret123",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "expense_user@example.com",
        "password": "Secret123",
    })
    return response.json()["tokens"]["access_token"]


@pytest.mark.asyncio
async def test_create_expense(client):
    token = await get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/api/v1/expenses", json={
        "amount": "150.00",
        "description": "Lunch at restaurant",
        "expense_date": "2024-01-15",
        "currency": "INR",
        "payment_method": "upi",
        "tags": ["food"],
    }, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Lunch at restaurant"
    assert data["amount"] == "150.00"


@pytest.mark.asyncio
async def test_list_expenses(client):
    token = await get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/expenses", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_expense_not_found(client):
    token = await get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/expenses/99999", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_expense(client):
    token = await get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post("/api/v1/expenses", json={
        "amount": "50.00",
        "description": "Coffee",
        "expense_date": "2024-01-10",
        "currency": "INR",
        "payment_method": "cash",
    }, headers=headers)

    expense_id = create.json()["id"]
    delete = await client.delete(f"/api/v1/expenses/{expense_id}", headers=headers)
    assert delete.status_code == 204