from fixtures import client


def test_job_create(client):
    data = {
        'text': 'some text'
    }

    resp = client.post('/job', data=data)
    json_data = resp.get_json()
    assert resp.status_code == 200
