from flask import Flask, request, render_template_string
import subprocess

app = Flask(__name__)
wifi_device = "wlan0"  # Change to "wlan0" if using built-in WiFi

@app.route('/', methods=['GET', 'POST'])
def wifi():
    message = ""
    
    # Handle form submission
    if request.method == 'POST':
        ssid = request.form['ssid']
        password = request.form['password']
        connect_cmd = ["nmcli", "device", "wifi", "connect", ssid, "ifname", wifi_device]
        if password:
            connect_cmd += ["password", password]

        result = subprocess.run(connect_cmd, capture_output=True)
        if result.returncode == 0:
            message = f"✅ Connected to {ssid}!"
        else:
            message = f"❌ Failed to connect to {ssid}:<br><pre>{result.stderr.decode()}</pre>"

    # Scan WiFi networks
    scan = subprocess.check_output([
        "nmcli", "--colors", "no", "-m", "multiline", "--get-value", "SSID",
        "dev", "wifi", "list", "ifname", wifi_device
    ])
    ssid_list = [s.strip().removeprefix("SSID:") for s in scan.decode().split('\n') if s.strip()]

    # Simple HTML template inline
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connect to WiFi</title>
    </head>
    <body>
        <h2>📶 Available WiFi Networks</h2>
        <form method="post">
            <label for="ssid">SSID:</label>
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
    app.run(host="0.0.0.0", port=80)
