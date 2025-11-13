"""Simple connectivity check against an Elasticsearch endpoint."""

from __future__ import annotations

import argparse
import base64
import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()

def _build_request(url: str, username: str | None, password: str | None) -> urllib.request.Request:
  req = urllib.request.Request(url)
  if username and password:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
  req.add_header("Accept", "application/json")
  return req


def _call(url: str, username: str | None, password: str | None, timeout: float) -> tuple[int, dict | str]:
  req = _build_request(url, username, password)
  try:
    with urllib.request.urlopen(req, timeout=timeout) as resp:
      body = resp.read().decode()
      try:
        data = json.loads(body)
      except json.JSONDecodeError:
        data = body
      return resp.status, data
  except urllib.error.HTTPError as exc:
    err_body = exc.read().decode()
    try:
      payload = json.loads(err_body)
    except json.JSONDecodeError:
      payload = err_body
    return exc.code, payload


def main() -> int:
  parser = argparse.ArgumentParser(description="Test Elasticsearch connectivity")
  parser.add_argument("--url", default=None, help="Elasticsearch base URL, e.g. https://host:9200/")
  parser.add_argument("--username", default=None, help="Basic auth username")
  parser.add_argument("--password", default=None, help="Basic auth password")
  parser.add_argument("--timeout", type=float, default=10, help="Request timeout in seconds")
  args = parser.parse_args()

  url = args.url or os.getenv("ES_ENDPOINT")
  username = args.username or os.getenv("ES_USERNAME")
  password = args.password or os.getenv("ES_PASSWORD")

  if not url:
    raise SystemExit("Missing Elasticsearch URL. Pass --url or set ES_ENDPOINT.")

  print(f"Checking root endpoint: {url}")
  status, body = _call(url, username, password, args.timeout)
  print(f"Status: {status}\nResponse: {body}\n")

  health_url = url.rstrip("/") + "/_cluster/health"
  print(f"Checking cluster health: {health_url}")
  status, body = _call(health_url, username, password, args.timeout)
  print(f"Status: {status}\nResponse: {body}")

  return 0


if __name__ == "__main__":
  raise SystemExit(main())
