from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.dashboard_service import parse_dashboard_metrics, render_html_dashboard


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/metrics":
            data = parse_dashboard_metrics()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
        else:
            data = parse_dashboard_metrics()
            html = render_html_dashboard(data)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))


def main():
    data = parse_dashboard_metrics()
    html = render_html_dashboard(data)
    os.makedirs("docs", exist_ok=True)
    with open("docs/dashboard.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Đã tạo file dashboard tĩnh tại docs/dashboard.html")

    port = 8080
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])

    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"Khởi chạy Dashboard server tại: http://127.0.0.1:{port}")
    print("Nhấn Ctrl+C để dừng server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng server.")


if __name__ == "__main__":
    if "--snapshot" in sys.argv:
        data = parse_dashboard_metrics()
        html = render_html_dashboard(data)
        os.makedirs("docs", exist_ok=True)
        with open("docs/dashboard.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Đã xuất snapshot docs/dashboard.html")
    else:
        main()
