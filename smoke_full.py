import io
import os
import time
import random
import requests


BASE = "http://127.0.0.1:8000/api"


def ensure_server():
    for _ in range(10):
        try:
            requests.get(BASE, timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def register(username: str, email: str, password: str):
    r = requests.post(
        f"{BASE}/accounts/register/",
        data={
            "username": username,
            "email": email,
            "password": password,
            "full_name": "Smoke Full",
        },
        timeout=10,
    )
    return r.status_code, r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text


def login(username: str, password: str):
    r = requests.post(
        f"{BASE}/accounts/login/",
        data={"username": username, "password": password},
        timeout=10,
    )
    return r.status_code, r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def upload(token: str, filename: str, content: bytes):
    files = {"file": (filename, io.BytesIO(content))}
    r = requests.post(f"{BASE}/files/upload/", headers=auth_headers(token), files=files, timeout=20)
    return r.status_code, r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text


def list_files(token: str):
    r = requests.get(f"{BASE}/files/", headers=auth_headers(token), timeout=10)
    return r.status_code, r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text


def download(token: str, file_id: int):
    r = requests.get(f"{BASE}/files/{file_id}/download/", headers=auth_headers(token), timeout=20)
    return r.status_code


def rename(token: str, file_id: int, new_name: str):
    r = requests.post(f"{BASE}/files/{file_id}/rename/", headers=auth_headers(token), data={"name": new_name}, timeout=10)
    return r.status_code


def delete(token: str, file_id: int):
    # REST: DELETE /files/{id}/
    r = requests.delete(f"{BASE}/files/{file_id}/", headers=auth_headers(token), timeout=10)
    return r.status_code


def main() -> int:
    if not ensure_server():
        print("Server is not responding at:", BASE)
        return 99

    pwd = "secret123"
    u1 = f"smoke{random.randint(10000,99999)}"
    u2 = f"smoke{random.randint(10000,99999)}"

    # Register user1 and login
    sc, body = register(u1, f"{u1}@example.com", pwd)
    print("register u1:", sc, body)
    if sc != 201:
        return 1
    sc, body = login(u1, pwd)
    print("login u1:", sc, body)
    if sc != 200 or not isinstance(body, dict) or "access" not in body:
        return 2
    token1 = body["access"]

    # Upload allowed file
    sc, body = upload(token1, "ok.txt", b"hello world")
    print("upload ok.txt:", sc, body)
    if sc != 201:
        return 3
    file_id = body["id"] if isinstance(body, dict) else None
    if not file_id:
        return 4

    # Upload forbidden .exe
    sc, body = upload(token1, "bad.exe", b"MZ\x00\x00fake")
    print("upload bad.exe:", sc, body)
    if sc != 400:
        return 5

    # List files
    sc, body = list_files(token1)
    print("list:", sc, body if isinstance(body, list) else str(body)[:120])
    if sc != 200:
        return 6

    # Download
    sc = download(token1, file_id)
    print("download:", sc)
    if sc != 200:
        return 7

    # Rename
    sc = rename(token1, file_id, "renamed.txt")
    print("rename:", sc)
    if sc != 200:
        return 8

    # Access check: user2 should not access user1 file
    sc, body = register(u2, f"{u2}@example.com", pwd)
    print("register u2:", sc)
    sc, body = login(u2, pwd)
    token2 = body["access"] if sc == 200 and isinstance(body, dict) else None
    sc = download(token2, file_id)
    print("download by other user:", sc)
    if sc != 403:
        return 9

    # Delete by owner
    sc = delete(token1, file_id)
    print("delete:", sc)
    if sc != 204:
        return 10

    print("SMOKE FULL: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


