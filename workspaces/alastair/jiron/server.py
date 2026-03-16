"""Jiron skill server — lightweight HTTP server for Zeroclaw agent skills."""

import json
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # Python < 3.11 fallback

SKILLS_DIR = Path("/workspace/skills")
AGENT_NAME = "unknown"

# Try to extract agent name from SOUL.md
soul_path = Path("/workspace/SOUL.md")
if soul_path.exists():
    for line in soul_path.read_text().splitlines():
        if line.startswith("# "):
            AGENT_NAME = line[2:].strip()
            break


def load_skills():
    """Load all .toml skill definitions from the skills directory."""
    skills = {}
    if not SKILLS_DIR.exists():
        return skills
    for toml_file in sorted(SKILLS_DIR.glob("*.toml")):
        with open(toml_file, "rb") as f:
            skill = tomllib.load(f)
        skills[skill["name"]] = skill
    return skills


class JironHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[jiron] {args[0]}", file=sys.stderr)

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        skills = load_skills()
        path = self.path.rstrip("/")

        if path == "" or path == "/":
            # Root: return agent info and skill catalog
            catalog = [
                {
                    "name": s["name"],
                    "title": s.get("title", s["name"]),
                    "description": s.get("description", ""),
                    "fields": s.get("fields", []),
                }
                for s in skills.values()
            ]
            self.send_json({"agent": AGENT_NAME, "skills": catalog})
            return

        if path.startswith("/skills/"):
            skill_name = path[len("/skills/"):]
            if skill_name in skills:
                self.send_json(skills[skill_name])
                return
            self.send_json({"error": f"skill '{skill_name}' not found"}, 404)
            return

        self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        skills = load_skills()
        path = self.path.rstrip("/")

        if not path.startswith("/skills/"):
            self.send_json({"error": "not found"}, 404)
            return

        skill_name = path[len("/skills/"):]
        if skill_name not in skills:
            self.send_json({"error": f"skill '{skill_name}' not found"}, 404)
            return

        # Read input body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            input_data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"error": "invalid JSON body"}, 400)
            return

        skill = skills[skill_name]
        handler = skill.get("handler", "exec")

        try:
            if handler == "exec":
                command = skill["command"].format(**input_data)
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True, timeout=60
                )
                self.send_json({
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None,
                })
            elif handler == "agent":
                prompt = skill["prompt"].format(**input_data)
                result = subprocess.run(
                    ["zeroclaw", "agent", "-m", prompt],
                    capture_output=True, text=True, timeout=300
                )
                self.send_json({
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "error": result.stderr if result.returncode != 0 else None,
                })
            else:
                self.send_json({"error": f"unknown handler: {handler}"}, 400)
        except subprocess.TimeoutExpired:
            self.send_json({"error": "skill execution timed out"}, 504)
        except KeyError as e:
            self.send_json({"error": f"missing required field: {e}"}, 400)


def main():
    port = int(os.environ.get("JIRON_PORT", "3100"))
    server = HTTPServer(("0.0.0.0", port), JironHandler)
    print(f"[jiron] {AGENT_NAME} skill server listening on :{port}", file=sys.stderr)
    server.serve_forever()


if __name__ == "__main__":
    main()
