"""Throwaway stand-in for the FastAPI backend, used only to screenshot the UI."""

import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

GROUNDED = {
    "answer": (
        "You receive twelve days of paid sick leave per year [1]. Unused days "
        "do not carry over into the next calendar year [2]."
    ),
    "refused": False,
    "refused_by": None,
    "gate_distance": 0.2212,
    "sources": [
        {
            "index": 1,
            "source": "leave_policy.md",
            "chunk_index": 2,
            "text": (
                "Every employee receives twelve days of paid sick leave per calendar "
                "year. Sick leave accrues monthly at a rate of one day per month and "
                "is available from the first day of employment. Employees must notify "
                "their manager before 10:00 on the first day of absence. A doctor's "
                "note is required for any absence longer than three consecutive days."
            ),
            "distance": 0.2212,
            "rerank_score": 8.04,
        },
        {
            "index": 2,
            "source": "leave_policy.md",
            "chunk_index": 3,
            "text": (
                "Unused sick leave does not carry forward into the following calendar "
                "year and is not paid out on termination of employment."
            ),
            "distance": 0.4381,
            "rerank_score": 3.17,
        },
        {
            "index": 3,
            "source": "remote_work_policy.md",
            "chunk_index": 0,
            "text": (
                "Employees working remotely are expected to follow the same leave "
                "reporting procedures as office-based staff."
            ),
            "distance": 0.6122,
            "rerank_score": -1.44,
        },
    ],
    "usage": {"prompt_tokens": 512, "completion_tokens": 24},
    "latency_ms": 840,
}

REFUSED_DISTANCE = {
    "answer": "I don't know based on the provided documents.",
    "refused": True,
    "refused_by": "distance_threshold",
    "gate_distance": 0.7419,
    "sources": [
        {
            "index": 1,
            "source": "remote_work_policy.md",
            "chunk_index": 4,
            "text": (
                "Employees are responsible for maintaining a safe and distraction-free "
                "home working environment, including adequate lighting and seating."
            ),
            "distance": 0.7419,
            "rerank_score": None,
        },
    ],
    "usage": None,
    "latency_ms": 96,
}

REFUSED_LLM = {
    "answer": "I don't know based on the provided documents.",
    "refused": True,
    "refused_by": "llm_grounding",
    "gate_distance": 0.5881,
    "sources": [
        {
            "index": 1,
            "source": "remote_work_policy.md",
            "chunk_index": 4,
            "text": (
                "Employees are responsible for maintaining a safe and distraction-free "
                "home working environment, including adequate lighting and seating."
            ),
            "distance": 0.6766,
            "rerank_score": 2.14,
        },
        {
            "index": 2,
            "source": "security_guidelines.md",
            "chunk_index": 1,
            "text": (
                "Visitors must be signed in at reception and escorted at all times "
                "while inside secure areas of the building."
            ),
            "distance": 0.6752,
            "rerank_score": 1.02,
        },
        {
            "index": 3,
            "source": "leave_policy.md",
            "chunk_index": 0,
            "text": "All employees are entitled to paid annual leave.",
            "distance": 0.7331,
            "rerank_score": -0.88,
        },
    ],
    "usage": {"prompt_tokens": 480, "completion_tokens": 12},
    "latency_ms": 620,
}


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    def _send(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            self._send({"status": "ok", "chunks": 21})
        else:
            self._send({"detail": "not found"}, 404)

    def do_POST(self):
        if self.path != "/api/ask":
            self._send({"detail": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", 0))
        question = json.loads(self.rfile.read(length) or b"{}").get("question", "")
        time.sleep(0.4)
        q = question.lower()
        if "pet" in q:
            payload = REFUSED_LLM
        elif "tax" in q or "income" in q:
            payload = REFUSED_DISTANCE
        else:
            payload = GROUNDED
        self._send(payload)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("mock backend on http://localhost:8000", flush=True)
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
