from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_route(method, path):
    print(f"Testing {method} {path}")
    if method == "GET":
        r = client.get(path)
    elif method == "POST":
        r = client.post(path)
    print(f"  STATUS: {r.status_code}")
    print("-" * 20)

test_route("GET", "/api/users/login")
test_route("GET", "/api/users/login/")
test_route("POST", "/api/users/login")
test_route("POST", "/api/users/login/")
