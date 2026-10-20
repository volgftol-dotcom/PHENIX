import os, json, time, base64
from flask import Flask, request, Response

app = Flask(__name__)
LOGS = []  # آخر الطلبات (في الذاكرة)
MAX = 300


def record():
    body = request.get_data() or b""
    try:
        body_txt = body.decode("utf-8")
    except Exception:
        body_txt = "BASE64:" + base64.b64encode(body).decode()
    entry = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "method": request.method,
        "path": request.full_path.rstrip("?"),
        "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "headers": {k: v for k, v in request.headers.items()
                    if k.lower() not in ("host", "x-forwarded-proto", "x-forwarded-port",
                                         "x-railway-request-id", "x-real-ip", "x-request-start")},
        "form": request.form.to_dict(),
        "files": {k: f"{v.filename} ({len(v.read())} bytes)" for k, v in request.files.items()},
        "body": body_txt[:3000],
    }
    LOGS.append(entry)
    del LOGS[:-MAX]
    print("REQ", json.dumps(entry, ensure_ascii=False), flush=True)


@app.route("/__logs")
def logs():
    return Response(json.dumps(LOGS[::-1], ensure_ascii=False, indent=1),
                    mimetype="text/plain; charset=utf-8")


@app.route("/__clear")
def clear():
    LOGS.clear()
    return "cleared"


@app.route("/", defaults={"p": ""}, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
@app.route("/<path:p>", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
def catch_all(p):
    record()
    return Response(json.dumps({"status": "ok"}), mimetype="application/json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
