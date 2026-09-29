import os
import sys
import socket
import webbrowser

# Ensure safe UTF-8 output on Windows terminals
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import uvicorn
from app.database import Base, engine
from app.seed import seed_database


def is_port_in_use(port: int) -> bool:
    """Check if a local TCP port is already open/in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def find_available_port(start_port: int = 8000, max_attempts: int = 20) -> int:
    """Finds the first free port starting from start_port."""
    for p in range(start_port, start_port + max_attempts):
        if not is_port_in_use(p):
            return p
    return start_port


def main():
    print("=" * 65)
    print("   POOLPILOT: Community Peer-to-Peer Ride-Sharing Network")
    print("   Urban Mobility & Commute Crisis Solution (Chennai Demo)")
    print("=" * 65)

    # 1. Initialize DB and auto-seed on initial launch
    try:
        Base.metadata.create_all(bind=engine)
        seed_database(reset=False)
    except Exception as e:
        print(f"[Init] Database initialization note: {e}")

    # 2. Select free port
    port = find_available_port(8000)
    url = f"http://localhost:{port}"

    print(f"\n[+] Server starting on: {url}")
    print(f"[+] Interactive API Docs: {url}/docs")
    print(f"[+] Demo Riders: Rahul (ID 1), Priya (ID 2)")
    print(f"[+] Demo Drivers: Karthik (ID 3), Ananya (ID 4)")
    print(f"[+] Demo Admin: Admin (ID 5)")
    print("-" * 65)
    print("Press CTRL+C to stop the server.\n")

    # 3. Start Uvicorn Server
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="info", reload=False)


if __name__ == "__main__":
    main()
