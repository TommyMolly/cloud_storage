import os
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000/api"
TEST_USER = {
    "username": "user_test",
    "email": "user_test@test.com",
    "password": "Qwe123!",
    "full_name": "Test User",
}

TEST_FILES = {
    "txt": "test_upload.txt",
    "pdf": "test_doc.pdf",
    "png": "test_image.png",
}

# --- Утилиты ---
def safe_json(r):
    try:
        return r.json()
    except Exception:
        print("Response content:", r.text[:500])
        return None

def register(user):
    r = requests.post(f"{BASE_URL}/accounts/register/", data=user)
    return safe_json(r), r.status_code

def login(username, password):
    r = requests.post(f"{BASE_URL}/accounts/login/", data={
        "username": username,
        "password": password
    })
    return safe_json(r), r.status_code

def upload_file(access_token, filepath):
    with open(filepath, "rb") as f:
        files = {"file": f}
        headers = {"Authorization": f"Bearer {access_token}"}
        r = requests.post(f"{BASE_URL}/files/upload/", files=files, headers=headers)
    return safe_json(r), r.status_code

def list_files(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{BASE_URL}/files/", headers=headers)
    return safe_json(r), r.status_code

def download_file(access_token, file_id, save_path):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(f"{BASE_URL}/files/{file_id}/download/", headers=headers, stream=True)
    if r.status_code == 200:
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
    return r.status_code

def get_share_link(access_token, file_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.post(f"{BASE_URL}/files/shared/{file_id}/", headers=headers)
    return safe_json(r), r.status_code

def download_shared(url, save_path):
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
    return r.status_code

def delete_user(admin_token, user_id):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = requests.delete(f"{BASE_URL}/accounts/{user_id}/delete/", headers=headers)
    return safe_json(r), r.status_code

# --- Генерация тестовых файлов ---
def create_test_files():
    # TXT
    with open(TEST_FILES["txt"], "w") as f:
        f.write("Hello, Cloud Storage!")
    # PDF (пустой файл для теста)
    with open(TEST_FILES["pdf"], "wb") as f:
        f.write(b"%PDF-1.4\n%EOF")
    # PNG (простейший 1x1 прозрачный PNG)
    png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01' \
                b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89' \
                b'\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01' \
                b'\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82'
    with open(TEST_FILES["png"], "wb") as f:
        f.write(png_bytes)

def cleanup_test_files():
    for f in TEST_FILES.values():
        if Path(f).exists():
            os.remove(f)
    # скачанные файлы
    for f in ["downloaded_" + fn for fn in TEST_FILES.values()]:
        if Path(f).exists():
            os.remove(f)
    for f in ["shared_" + fn for fn in TEST_FILES.values()]:
        if Path(f).exists():
            os.remove(f)

# --- Тесты ---
if __name__ == "__main__":
    cleanup_test_files()
    create_test_files()

    # 1. Регистрация
    reg, status = register(TEST_USER)
    print("Register:", status, reg)
    user_id = reg["id"] if status == 201 else 9  # если уже существует, укажи id

    # 2. Логин пользователя
    login_res, status = login(TEST_USER["username"], TEST_USER["password"])
    print("Login:", status, login_res)
    access_token = login_res["access"]

    # 3. Загрузка файлов
    uploaded_files = {}
    for ext, path in TEST_FILES.items():
        res, status = upload_file(access_token, path)
        print(f"Upload {ext}:", status, res)
        if status == 201:
            uploaded_files[ext] = res

    # 4. Список файлов
    files, status = list_files(access_token)
    print("File list:", status, files)

    # 5. Скачивание и проверка содержимого
    for ext, file_info in uploaded_files.items():
        save_path = "downloaded_" + TEST_FILES[ext]
        download_status = download_file(access_token, file_info["id"], save_path)
        print(f"Download {ext}:", download_status)
        if ext == "txt":
            with open(save_path) as f:
                content = f.read()
            print("TXT content preview:", content)

    # 6. Share ссылки и скачивание через них
    for ext, file_info in uploaded_files.items():
        share_res, status = get_share_link(access_token, file_info["id"])
        print(f"Share link {ext}:", status, share_res)
        if status == 200:
            share_url = share_res["share_url"]
            save_path = "shared_" + TEST_FILES[ext]
            shared_download_status = download_shared(share_url, save_path)
            print(f"Shared download {ext}:", shared_download_status)

    # 7. Админ для удаления тестового пользователя
    admin_login_res, status = login("admin", "admin")
    if status == 200:
        admin_token = admin_login_res["access"]
        cleanup_res, status = delete_user(admin_token, user_id)
        print("Cleanup:", status, cleanup_res)
    else:
        print("Admin login failed, cannot cleanup test user")

    cleanup_test_files()
