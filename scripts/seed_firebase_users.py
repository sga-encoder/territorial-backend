"""Creates one Firebase Auth e-mail/password account per seeded official and citizen.

Every account uses the demo password below, so any role can log in to the frontend.
Run after scripts/seed_demo.py. Needs the frontend's public Firebase web API key and
the e-mail/password provider enabled in the Firebase console.

Usage:
    FIREBASE_API_KEY=<web api key> python scripts/seed_firebase_users.py

Existing accounts (EMAIL_EXISTS) are reported and skipped; changing their password
requires the Firebase Admin SDK and is out of scope.
"""
import os
import sys
import time
from pathlib import Path

import requests

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app import create_app  # noqa: E402
from app.models.citizen import Citizen  # noqa: E402
from app.models.official import Official  # noqa: E402

DEMO_PASSWORD = "Admin123*"
IDENTITY_TOOLKIT_URL = "https://identitytoolkit.googleapis.com/v1/accounts"
# Firebase limits sign-ups per IP; a short pause keeps ~65 accounts well under it.
PAUSE_SECONDS = 0.3
FATAL_ERRORS = {"OPERATION_NOT_ALLOWED", "TOO_MANY_ATTEMPTS_TRY_LATER", "API_KEY_INVALID"}


def firebase_error(response):
    try:
        return response.json()["error"]["message"]
    except (ValueError, KeyError):
        return f"HTTP {response.status_code}"


def create_account(api_key, email, display_name):
    response = requests.post(f"{IDENTITY_TOOLKIT_URL}:signUp", params={"key": api_key},
                             json={"email": email, "password": DEMO_PASSWORD, "returnSecureToken": True}, timeout=20)
    if not response.ok:
        return firebase_error(response)
    # signUp does not accept a display name; set it so the navbar shows the person.
    requests.post(f"{IDENTITY_TOOLKIT_URL}:update", params={"key": api_key},
                  json={"idToken": response.json()["idToken"], "displayName": display_name,
                        "returnSecureToken": False}, timeout=20)
    return None


def main():
    api_key = os.getenv("FIREBASE_API_KEY")
    if not api_key:
        sys.exit("Define FIREBASE_API_KEY (apiKey de environment.firebase en el frontend).")

    app = create_app()
    with app.app_context():
        people = [(o.email, o.name, f"official:{o.role}") for o in Official.query.order_by(Official.id_official)]
        people += [(c.email, c.name, "citizen") for c in Citizen.query.order_by(Citizen.id_citizen)]

    created, skipped = 0, 0
    for email, name, kind in people:
        error = create_account(api_key, email, name)
        if error is None:
            created += 1
            print(f"  + {email} ({kind})")
        elif error.startswith("EMAIL_EXISTS"):
            skipped += 1
            print(f"  = {email} ya existe, se omite")
        elif error.split(" ")[0] in FATAL_ERRORS:
            sys.exit(f"Firebase rechazó el alta: {error}")
        else:
            skipped += 1
            print(f"  ! {email}: {error}")
        time.sleep(PAUSE_SECONDS)

    print(f"Cuentas creadas: {created}, omitidas: {skipped}. Contraseña: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
