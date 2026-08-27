"""
Enhanced helper script to generate FYERS API v3 Access Token using OAuth 2.0 flow.

Supports:
1. Copy-pasting the full redirected URL (e.g. https://trade.fyers.in/api-other/login.html?auth_code=...)
2. Copy-pasting the raw auth_code
3. Automatic .env file updating

Usage:
    python3 app/broker/generate_fyers_token.py
"""

import sys
import json
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.utils.config import Config

def extract_auth_code(user_input: str) -> str:
    """Extract auth_code whether user pasted full URL, JSON, or raw auth_code."""
    user_input = user_input.strip()

    # Case 1: Full URL (e.g. https://.../login.html?auth_code=XYZ&...)
    if user_input.startswith("http://") or user_input.startswith("https://"):
        parsed = urllib.parse.urlparse(user_input)
        params = urllib.parse.parse_qs(parsed.query)
        if "auth_code" in params:
            return params["auth_code"][0]

    # Case 2: JSON output on screen
    if user_input.startswith("{") and "auth_code" in user_input:
        try:
            data = json.loads(user_input)
            if "auth_code" in data:
                return data["auth_code"]
        except Exception:
            pass

    # Case 3: URL snippet containing auth_code=
    if "auth_code=" in user_input:
        parts = user_input.split("auth_code=")
        code = parts[1].split("&")[0].split(" ")[0].strip()
        return code

    # Case 4: Raw string
    return user_input

def update_env_token(access_token: str):
    """Updates FYERS_ACCESS_TOKEN in the project .env file."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        print(f"No .env file found at {env_path}")
        return

    lines = env_path.read_text().splitlines()
    new_lines = []
    found = False

    for line in lines:
        if line.startswith("FYERS_ACCESS_TOKEN="):
            new_lines.append(f'FYERS_ACCESS_TOKEN="{access_token}"')
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f'FYERS_ACCESS_TOKEN="{access_token}"')

    env_path.write_text("\n".join(new_lines) + "\n")
    print(f"Updated FYERS_ACCESS_TOKEN in {env_path}")

def generate_token():
    client_id = Config.FYERS_CLIENT_ID or input("Enter FYERS Client ID (App ID, e.g., XX12345-100): ").strip()
    secret_key = Config.FYERS_SECRET_KEY or input("Enter FYERS Secret Key: ").strip()
    redirect_uri = input("Enter Redirect URI (default: https://trade.fyers.in/api-other/login.html): ").strip() or "https://trade.fyers.in/api-other/login.html"

    try:
        from fyers_apiv3 import fyersModel

        session = fyersModel.SessionModel(
            client_id=client_id,
            secret_key=secret_key,
            redirect_uri=redirect_uri,
            response_type="code",
            grant_type="authorization_code"
        )

        login_url = session.generate_authcode()
        print("\n" + "="*70)
        print("STEP 1: Open this URL in your web browser:")
        print("="*70)
        print(login_url)
        print("="*70 + "\n")

        print("INSTRUCTIONS FOR STEP 2:")
        print("1. Log in with your FYERS User ID, PIN, and OTP.")
        print("2. Once logged in, your browser will redirect to a new URL.")
        print("3. Copy the ENTIRE URL from your browser address bar and paste it below.")
        print("   (Or copy the text on screen if a JSON response appears).\n")

        raw_input_data = input("Paste the FULL redirected URL or auth_code here: ")

        auth_code = extract_auth_code(raw_input_data)

        if not auth_code:
            print("Error: Could not extract auth_code from input.")
            return

        session.set_token(auth_code)
        response = session.generate_token()

        if isinstance(response, dict) and response.get("s") == "ok":
            access_token = response.get("access_token")
            print("\n" + "="*70)
            print("SUCCESS! Your new FYERS Access Token is:")
            print("="*70)
            print(access_token)
            print("="*70 + "\n")

            update_env_token(access_token)
            print("You can now run: python3 app/main.py")
        else:
            print(f"\nFailed to generate token. FYERS Response: {response}")

    except ImportError:
        print("Error: `fyers_apiv3` package is not installed. Install with `pip install fyers-apiv3`.")
    except Exception as e:
        print(f"Exception occurred during token generation: {e}")

if __name__ == "__main__":
    generate_token()
    # Generate the login URL
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=REDIRECT_URI,
        response_type="code",
        grant_type="authorization_code"
    )
    login_url = session.generate_authcode()

    # Start local callback server in a background thread
    server = HTTPServer(("127.0.0.1", REDIRECT_PORT), OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    print(f"\n[INFO] Local callback server started on {REDIRECT_URI}")

    # Open browser automatically
    print(f"[INFO] Opening FYERS login page in your browser...")
    webbrowser.open(login_url)

    print("\nWaiting for you to log in (FYERS User ID + PIN + OTP)...")
    print("(Your browser should open automatically. If not, copy this URL:)")
    print(f"  {login_url}\n")

    # Block until auth_code is captured (or timeout after 3 minutes)
    captured = _server_done.wait(timeout=180)
    server.shutdown()

    if not captured or not _captured["auth_code"]:
        print("\nTimeout or no auth_code captured. Please try again.")
        return

    auth_code = _captured["auth_code"]
    print(f"\n[SUCCESS] Auth code captured!")

    # Exchange auth_code for access_token
    session.set_token(auth_code)
    response = session.generate_token()

    if isinstance(response, dict) and response.get("s") == "ok":
        access_token = response.get("access_token")
        print("\n" + "="*70)
        print("ACCESS TOKEN GENERATED SUCCESSFULLY!")
        print("="*70)
        print(f"Token: {access_token[:40]}...  (truncated for display)")
        print("="*70)

        update_env_token(access_token)
        print("\nYou can now run: python3 app/main.py")
    else:
        print(f"\nFailed to generate token. FYERS Response: {response}")


if __name__ == "__main__":
    generate_token()
