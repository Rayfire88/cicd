from flask import Flask, request, Response, jsonify
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# === Prometheus Metrics ===
home_page_counter = Counter("flask_homepage_hits_total", "Hits to the home page")
click_counter = Counter("flask_button_clicks_total", "Total button clicks on homepage")
push_event_counter = Counter("gitlab_push_events_total", "Total GitLab push events")
visitor_counter = Counter("flask_visitor_hits_total", "Total requests by IP and endpoint", ["ip", "endpoint"])
login_counter = Counter("flask_login_attempts_total", "Login attempts", ["status"])
ua_counter = Counter("flask_user_agent_hits_total", "User-Agent hits", ["user_agent"])

# === Log and Count Visitors ===
@app.before_request
def log_visitor():
    ip = request.remote_addr
    endpoint = request.path
    ua = request.headers.get('User-Agent') or "unknown"
    visitor_counter.labels(ip=ip, endpoint=endpoint).inc()
    ua_counter.labels(user_agent=ua[:100]).inc()
    print(f"🔍 {ip} visited {endpoint} — UA: {ua}")

# === Routes ===
@app.route("/")
def home():
    home_page_counter.inc()
    return """
    <html><body>
        <h1>✅ Homepage</h1>
        <button onclick="fetch('/click', {method: 'POST'}).then(res => alert('Clicked!'))">
            Click Me!
        </button>
        <br><br>
        <form id="loginForm" onsubmit="submitLogin(); return false;">
            <input type="text" id="user" placeholder="Username">
            <input type="password" id="password" placeholder="Password">
            <button type="submit">Login</button>
        </form>
        <script>
            function submitLogin() {
                fetch('/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        user: document.getElementById('user').value,
                        password: document.getElementById('password').value
                    })
                }).then(res => res.text()).then(alert);
            }
        </script>
    </body></html>
    """

@app.route("/click", methods=["POST"])
def click():
    click_counter.inc()
    return "🖱️ Button clicked!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    print("🔔 Webhook received:", data.get("event_name"))
    if data.get("event_name") == "push":
        push_event_counter.inc()
    return "Webhook OK", 200

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = data.get("user")
    password = data.get("password")

    if user == "admin" and password == "123":
        login_counter.labels(status="success").inc()
        return "✅ Login successful"
    else:
        login_counter.labels(status="failed").inc()
        return "❌ Invalid credentials", 401

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route("/health")
def health():
    return "OK", 200

# === Run App ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
