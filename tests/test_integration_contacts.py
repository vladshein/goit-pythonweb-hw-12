def test_create_contact(client, get_token):
    response = client.post(
        "/api/contacts",
        json={
            "first_name": "test_first_name",
            "last_name": "test_last_name",
            "email": "test_email@example.com",
            "phone_number": "380991234567",
            "birthday": "2000-01-01",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["first_name"] == "test_first_name"
    assert "id" in data


def test_get_contact(client, get_token):

    response = client.get(
        "/api/contacts/1", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == "test_first_name"
    assert "id" in data


def test_get_contact_not_found(client, get_token):
    response = client.get(
        "/api/contacts/2", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"


def test_get_contacts(client, get_token):
    response = client.get(
        "/api/contacts", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["first_name"] == "test_first_name"
    assert "id" in data[0]


def test_update_contact(client, get_token):
    response = client.patch(
        "/api/contacts/1",
        json={
            "first_name": "test_second_name",
            "last_name": "test_last_name",
            "email": "test_email@example.com",
            "phone_number": "380991234567",
            "birthday": "2000-01-01",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == "test_second_name"
    assert "id" in data


def test_update_contact_not_found(client, get_token):
    response = client.patch(
        "/api/contacts/3",
        json={
            "first_name": "test_new_name",
            "last_name": "test_last_name",
            "email": "test_email@example.com",
            "phone_number": "380991234567",
            "birthday": "2000-01-01",
        },
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Contact not found"


def test_delete_contact(client, get_token):
    response = client.delete(
        "/api/contacts/1", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == "test_second_name"
    assert "id" in data


def test_repeat_delete_contact(client, get_token):
    response = client.delete(
        "/api/contacts/1", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Requested contact not found"


#####
def test_get_contacts_with_bds(client, get_token):
    response = client.get(
        "/api/contacts/upcoming_birthdays/",
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    if data:
        assert "first_name" in data[0]
    else:
        print("No contacts with birthdays in the given range.")
