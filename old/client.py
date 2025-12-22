# frontend/client.py
import requests

API_URL = "http://localhost:8000"

class LegalChatClient:
    def __init__(self):
        self.token = None
        self.headers = {}

    def login(self, username, password):
        try:
            r = requests.post(f"{API_URL}/token", data={"username": username, "password": password})
            if r.status_code == 200:
                self.token = r.json()["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                return True, "✅ Login successful! Redirecting..."
            return False, f"❌ Login Failed: {r.json().get('detail', 'Unknown error')}"
        except Exception as e:
            return False, f"❌ Connection Error: {str(e)}"

    def register(self, username, password):
        try:
            r = requests.post(f"{API_URL}/register", json={"username": username, "password": password})
            if r.status_code == 200:
                return True, "✅ Registration successful! Please Sign In."
            return False, f"❌ Registration Failed: {r.json().get('detail')}"
        except Exception as e:
            return False, f"❌ Error: {str(e)}"

    def upload_file(self, file_obj):
        if not self.token:
            return "<span style='color: red;'>❌ Session expired. Login again.</span>"
        if not file_obj:
            return "<span style='color: red;'>⚠️ No file selected.</span>"

        files = {"file": open(file_obj, "rb")}
        try:
            r = requests.post(f"{API_URL}/upload", files=files, headers=self.headers)
            if r.status_code == 200:
                data = r.json()
                return f"<span style='color: white; font-weight: bold;'>✅ {data['filename']} processed & deleted securely.</span>"
            return f"<span style='color: red;'>❌ Upload Error: {r.text}</span>"
        except Exception as e:
            return f"<span style='color: red;'>❌ System Error: {str(e)}</span>"

    def chat_stream(self, message):
        if not self.token:
            yield "⚠️ Please login first."
            return

        try:
            r = requests.post(
                f"{API_URL}/analyze",
                json={"query": message},
                headers=self.headers,
                stream=True,
                timeout=120
            )
            partial_acc = ""
            for chunk in r.iter_content(chunk_size=32, decode_unicode=True):
                if chunk:
                    partial_acc += chunk
                    yield partial_acc
        except Exception as e:
            yield f"❌ Stream Error: {str(e)}"

# Singleton instance to be used by the app
client = LegalChatClient()