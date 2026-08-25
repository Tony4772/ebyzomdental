import json
import urllib.request
import urllib.parse
import urllib.error

# Login
form = urllib.parse.urlencode(
    {"username": "gerencia@ebyzom.com", "password": "Genvicgar97*72"}
).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/auth/login",
    data=form,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=30) as resp:
    tokens = json.loads(resp.read().decode())

token = tokens["access_token"]
req2 = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/auth/me",
    headers={"Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(req2, timeout=30) as resp:
    me = json.loads(resp.read().decode())["data"]

print("is_platform_operator", me["user"].get("is_platform_operator"))
print("has_platform_perm", "platform.clinics.provision" in me.get("permissions", []))
print("clinic_count", len(me.get("clinics", [])))
print("clinics", [c["name"] for c in me.get("clinics", [])])
