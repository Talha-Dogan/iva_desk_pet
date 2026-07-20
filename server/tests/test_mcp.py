"""Konteynerden Iva araclarina (HTTP MCP) erisim testi."""
import json

import requests

URL = "http://host.docker.internal:8090/mcp"
HEAD = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def rpc(session, payload, sid=None):
    h = dict(HEAD)
    if sid:
        h["mcp-session-id"] = sid
    return session.post(URL, headers=h, json=payload, timeout=15)


def main():
    s = requests.Session()
    r = rpc(s, {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "test", "version": "1"}},
    })
    print("initialize HTTP", r.status_code)
    sid = r.headers.get("mcp-session-id")
    if r.status_code != 200:
        print(r.text[:300])
        return

    rpc(s, {"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    r = rpc(s, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, sid)
    names = []
    for line in r.text.splitlines():
        if line.startswith("data: "):
            try:
                data = json.loads(line[6:])
                for t in data.get("result", {}).get("tools", []):
                    names.append(t["name"])
            except Exception:
                pass
    print("araclar:", ", ".join(names) if names else "(bulunamadi)")
    print("toplam:", len(names))


if __name__ == "__main__":
    main()
