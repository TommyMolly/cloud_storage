import random
import requests


BASE = "http://127.0.0.1:8000/api"


def login(username: str, password: str):
  r = requests.post(f"{BASE}/accounts/login/", json={"username": username, "password": password}, timeout=10)
  return r.status_code, (r.json() if r.headers.get('content-type','').startswith('application/json') else r.text)


def register(username: str, email: str, password: str):
  r = requests.post(f"{BASE}/accounts/register/", json={"username": username, "email": email, "password": password, "full_name": "REST Test"}, timeout=10)
  return r.status_code, (r.json() if r.headers.get('content-type','').startswith('application/json') else r.text)


def auth_headers(token: str):
  return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def toggle_admin(token: str, user_id: int, is_admin: bool):
  r = requests.patch(f"{BASE}/accounts/users/{user_id}/", headers=auth_headers(token), json={"is_admin": is_admin}, timeout=10)
  return r.status_code, r.json() if r.headers.get('content-type','').startswith('application/json') else r.text


def delete_user(token: str, user_id: int):
  r = requests.delete(f"{BASE}/accounts/users/{user_id}/", headers={"Authorization": f"Bearer {token}"}, timeout=10)
  return r.status_code


def main() -> int:
  # login as admin (adjust if needed)
  sc, data = login("admin", "admin")
  print("admin login:", sc, str(data)[:200])
  if sc != 200:
    return 1
  token = data["access"]

  # create user
  uname = f"restu{random.randint(10000,99999)}"
  sc, data = register(uname, f"{uname}@ex.com", "secret123")
  print("register:", sc, str(data)[:200])
  if sc != 201:
    return 2
  user_id = data["id"]

  # toggle admin true
  sc, data = toggle_admin(token, user_id, True)
  print("patch is_admin true:", sc, data)
  if sc != 200 or not data.get("is_admin"):
    return 3

  # toggle admin false
  sc, data = toggle_admin(token, user_id, False)
  print("patch is_admin false:", sc, data)
  if sc != 200 or data.get("is_admin"):
    return 4

  # delete
  sc = delete_user(token, user_id)
  print("delete:", sc)
  if sc != 204:
    return 5

  print("USERS REST: OK")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())


