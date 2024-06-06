import pytest
import json
from statistika import app, get_db_connection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            get_db_connection()
        yield client

def test_index(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'modal' in rv.data

def test_get_columns(client):
    rv = client.get('/get_columns')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert isinstance(data, list)
    assert all("title" in col and "field" in col for col in data)

def test_packet(client):
    response = client.post('/check_packet', json=[101, 102])
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'data' in data

# def test_result(client):
#     response = client.post('/set_result', json={'key': 'value'})
#     assert response.status_code == 200
#     data = json.loads(response.data)
#     assert data['success'] == True
#     assert 'data' in data

def test_get_data_for_main_table(client):
    rv = client.get('/get_data_for_main_table')
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)

def test_get_data_for_table_players(client):
    rv = client.get('/get_data_for_table_players')
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data, list)

# def test_update(client):
#     response = client.post('/update', data={'row_id': 1, 'column_id': 2, 'value': 'new_value'})
#     assert response.status_code == 200
#     data = json.loads(response.data)
#     assert data['success'] == True

# def test_update_table_players(client):
#     response = client.post('/update_table_players', json={'playerFIO': 'John Doe', 'playerName': 123})
#     assert response.status_code == 200
#     data = json.loads(response.data)
#     assert data['success'] == True
