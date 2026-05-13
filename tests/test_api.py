"""
test_api.py
Automated tests for the Notes Vault API.
Covers API level and data layer testing.
"""
import pytest
from app import app, db

large_text = """This is the song that never ends. 
Yes, it goes on and on, my friend. Some people started singing it not knowing what it was, 
And they'll continue singing it forever just because... """

@pytest.fixture
def client():
    app.config['TESTING'] = True # Sets flask to test mode for better error output
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        # creating and dropping tables tests data layer will be made dynamically
        db.create_all()
        yield app.test_client()
        db.drop_all() # each test has it's own in memory DB, this deletes them after test runs

# Create Note Test with different examples
@pytest.mark.parametrize("payload,expected_title", [
    ({"content": "My first note"}, None),
    ({"content": "Note with title", "title": "Shopping List"}, "Shopping List"),
    ({"content": "Another note", "title": "Work Tasks"}, "Work Tasks"),
    ])
def test_create_note(client, payload, expected_title):
    response = client.post('/notes',
        json=payload,
        content_type='application/json'
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['content'] == payload['content']
    assert data['title'] == expected_title
    assert data['id'] is not None
    assert data['created_at'] is not None


# Test all three invalid post scenarios, empty json, missing content, content too long
@pytest.mark.parametrize("payload", [
    {},
    {"title" : "Blank Note"},
    {"title" : "lamb chop", "content":  (large_text*66)},
    ])
def test_create_note_invalid(client, payload):
    response = client.post('/notes', 
                           json=payload, 
                           content_type='application/json')

    assert response.status_code == 400
    data = response.get_json()
    assert data.get('error') is not None


# Test get notes
def test_get_notes(client):
    # Didn't parameterize this test becuase I needed a known list of entries to assert against
    payloads = [
    {"title" : "no droids", "content" : "These aren't the droids you're looking for..."},
    {"title" : "88 mph", "content" : "When this baby his 88 miles per hour, you're doing to see some serious $***"},
    {"title" : "love you", "content" : "I love you 3000"}
    ]

    for pl in payloads:
        client.post('/notes', json=pl, content_type = 'application/json')
    
    response = client.get('/notes')
    assert response.status_code == 200
    data = response.get_json()
    titles = [d.get('title') for d in data]
    assert len(data) == 3
    assert "love you" in titles

# Test get note by ID valid and invalid
def test_get_note_by_id(client):
    payloads = [
        {"title" : "Abed", "content" : "Cool. cool, cool, cool"},
        {"title" : "Gilfoyle", "content" : "I'm going to put this as delicately as I know how..."},
        {"title" : "Shawn", "content" : "I don’t lose things. I place things in locations which later elude me."}
        ]
    
    for pl in payloads:
        client.post("/notes", json=pl, content_type = 'application/json')
    
    all_notes = client.get('/notes').get_json()
    second_note_id = all_notes[1]['id']
    valid_response = client.get(f'/notes/{second_note_id}')
    valid_data = valid_response.get_json()
    assert "delicately" in valid_data.get('content')

    invalid_resopnse = client.get('/notes/13')
    assert invalid_resopnse.status_code == 404

def test_delete_note(client):
    payloads = [
        {"title" : "Homer", "content" : "I am so smart. S-M-R-T!"},
        {"title" : "Morty", "content" : "Nobody exists on purpose, nobody belongs anywhere, everybody's gonna die"},
        {"title" : "S.S. SSSSSSS", "content" : "I only had a 'S' stencil....."}
        ]
    
    for pl in payloads:
        client.post("/notes", json=pl, content_type = 'application/json')

    client.delete('/notes/2')
    unsuccessful_delete_response = client.delete('/notes/8675309')
    assert unsuccessful_delete_response.status_code == 404
    all_notes = client.get('/notes').get_json()
    assert len(all_notes) == 2
    assert all_notes[1].get('title') == "S.S. SSSSSSS"


def test_search_notes(client):
    payloads = [
        {"title" : "Master Chief", "content" : "I need a weapon"},
        {"title" : "Master Chef", "content" : "My mum's more Chinese than this dish, and she's from Scotland"},
        {"title" : "Chef", "content" : "Hello There, Children!"}
        ]

    for pl in payloads:
        client.post("/notes", json=pl, content_type = 'application/json')
    
    search_1_results = client.get('/notes/search?title=master')
    search_1_data = search_1_results.get_json()
    assert(len(search_1_data)) == 2

    search_2_results = client.get('/notes/search?title=chief')
    search_2_data = search_2_results.get_json()
    assert(len(search_2_data)) == 1
    assert "weapon" in search_2_data[0].get('content')

def test_update_note(client):
    payload =  {"title" : "Homer", "content" : "Just because I don’t care doesn’t mean I don’t understand."}
    client.post("/notes", json=payload, content_type = 'application/json')

    # Test update
    update_payload = {"title" : "Homer hobbies", "content" : "All hobbies suck, but if you keep at it, you might find at the end that you’ve managed to kill some precious time."}
    update_response = client.patch("/notes/1", json=update_payload, content_type = 'application/json')
    update_data = update_response.get_json()
    assert update_response.status_code == 200
    assert update_data.get('content').endswith("precious time.")
    assert update_data.get('content').startswith("All hobbies suck")

    # Test 404 when trying to update non-existent note
    non_note_response = client.patch("notes/8675309", json = {}, content_type = 'application/json')
    assert non_note_response.status_code == 404