from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_route(method, path, data=None):
    print(f"Testing {method} {path}")
    if method == "GET":
        r = client.get(path)
    elif method == "POST":
        r = client.post(path, data=data)
    print(f"  STATUS: {r.status_code}")
    if r.status_code >= 400:
        print(f"  RESPONSE: {r.text}")
    print("-" * 20)

test_route("GET", "/api/users/login")
test_route("POST", "/api/users/login")
test_route("GET", "/api/users/logout")
test_route("GET", "/")
