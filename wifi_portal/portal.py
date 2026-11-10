from flask import Flask, request, render_template_string
import subprocess

app = Flask(__name__)
wifi_device = "wlan0"  # Change this if your WiFi device is different (e.g., wlan1)

@app.route('/', methods=['GET', 'POST'])
def wifi():
    message = ""

    if request.method == 'POST':
        ssid = request.form['ssid']
        password = request.form['password']

        connect_cmd = ["nmcli", "device", "wifi", "connect", ssid, "ifname", wifi_device]
        if password:
            connect_cmd += ["password", password]

        result = subprocess.run(connect_cmd, capture_output=True)
        if result.returncode == 0:
            message = f"✅ Connected to <b>{ssid}</b>. You may now disconnect from the hotspot."
        else:
            message = f"❌ Failed to connect:<br><pre>{result.stderr.decode()}</pre>"

    # WiFi Scan
    try:
        scan = subprocess.check_output([
            "nmcli", "--colors", "no", "-m", "multiline", "--get-value", "SSID",
            "dev", "wifi", "list", "ifname", wifi_device
        ])
        ssid_list = [s.strip().removeprefix("SSID:") for s in scan.decode().split('\n') if s.strip()]
    except subprocess.CalledProcessError as e:
        ssid_list = []
        message = f"<pre>Error scanning WiFi: {e}</pre>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connect to WiFi</title>
    </head>
    <body>
        <h2>📶 Available Networks</h2>
        <form method="post">
            <label>SSID:</label>
            <select name="ssid" required>
                {''.join(f'<option value="{s}">{s}</option>' for s in ssid_list)}
            </select><br><br>
            <label>Password:</label>
            <input type="password" name="password"><br><br>
            <button type="submit">Connect</button>
        </form>
        <hr>
        {message}
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
