from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = 'shesecure_secret_key_2025'

# In-memory storage (replace with database in production)
alerts = []
devices = []
contacts = []
audio_files = []

# HTML Templates
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SheSecure{% endblock %}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .navbar {
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 1.5rem;
            font-weight: bold;
            color: #764ba2;
        }
        
        .nav-links {
            display: flex;
            gap: 2rem;
        }
        
        .nav-links a {
            text-decoration: none;
            color: #333;
            font-weight: 500;
            transition: color 0.3s;
        }
        
        .nav-links a:hover {
            color: #764ba2;
        }
        
        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        
        .card {
            background: white;
            border-radius: 10px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .card h2 {
            color: #764ba2;
            margin-bottom: 1rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .stat-card h3 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .stat-card p {
            opacity: 0.9;
        }
        
        .alert-item {
            border-left: 4px solid #e74c3c;
            padding: 1rem;
            margin-bottom: 1rem;
            background: #fff5f5;
            border-radius: 5px;
        }
        
        .alert-active {
            border-left-color: #e74c3c;
            background: #ffebee;
        }
        
        .alert-resolved {
            border-left-color: #27ae60;
            background: #f1f8f4;
        }
        
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary {
            background: #764ba2;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5a3780;
        }
        
        .btn-danger {
            background: #e74c3c;
            color: white;
        }
        
        .btn-success {
            background: #27ae60;
            color: white;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1rem;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        table th,
        table td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        table th {
            background: #f8f9fa;
            font-weight: 600;
        }
        
        .badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .badge-danger {
            background: #ffebee;
            color: #c62828;
        }
        
        .badge-success {
            background: #e8f5e9;
            color: #2e7d32;
        }
        
        .badge-warning {
            background: #fff3e0;
            color: #ef6c00;
        }
        
        .emergency-banner {
            background: #c62828;
            color: white;
            padding: 1rem;
            text-align: center;
            font-weight: bold;
            font-size: 1.2rem;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar">
        <div class="logo">🛡️ SheSecure</div>
        <div class="nav-links">
            <a href="/">Dashboard</a>
            <a href="/alerts">Alerts</a>
            <a href="/devices">Devices</a>
            <a href="/contacts">Contacts</a>
            <a href="/audio">Audio Files</a>
        </div>
    </nav>
    
    {% block content %}{% endblock %}
</body>
</html>
"""

DASHBOARD_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
{% block content %}
    {% if active_alerts %}
    <div class="emergency-banner">
        ⚠️ ACTIVE EMERGENCY ALERTS: {{ active_alerts }} - Immediate Action Required
    </div>
    {% endif %}
    
    <div class="container">
        <h1 style="color: white; margin-bottom: 2rem;">Dashboard Overview</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>{{ total_alerts }}</h3>
                <p>Total Alerts</p>
            </div>
            <div class="stat-card">
                <h3>{{ active_alerts }}</h3>
                <p>Active Emergencies</p>
            </div>
            <div class="stat-card">
                <h3>{{ total_devices }}</h3>
                <p>Registered Devices</p>
            </div>
            <div class="stat-card">
                <h3>{{ total_contacts }}</h3>
                <p>Emergency Contacts</p>
            </div>
        </div>
        
        <div class="card">
            <h2>Recent Alerts</h2>
            {% if recent_alerts %}
                {% for alert in recent_alerts %}
                <div class="alert-item {% if alert.status == 'active' %}alert-active{% else %}alert-resolved{% endif %}">
                    <strong>Device ID: {{ alert.device_id }}</strong><br>
                    <span class="badge {% if alert.status == 'active' %}badge-danger{% else %}badge-success{% endif %}">
                        {{ alert.status.upper() }}
                    </span>
                    <p>Time: {{ alert.timestamp }}</p>
                    <p>Location: {{ alert.location }}</p>
                    {% if alert.status == 'active' %}
                    <button class="btn btn-success" onclick="resolveAlert({{ alert.id }})">Mark as Safe</button>
                    {% endif %}
                </div>
                {% endfor %}
            {% else %}
                <p>No alerts recorded yet.</p>
            {% endif %}
        </div>
    </div>
    
    <script>
        function resolveAlert(alertId) {
            fetch('/api/resolve_alert/' + alertId, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if(data.success) {
                        location.reload();
                    }
                });
        }
        
        // Auto-refresh every 10 seconds
        setTimeout(() => location.reload(), 10000);
    </script>
{% endblock %}
""")

ALERTS_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
{% block content %}
    <div class="container">
        <div class="card">
            <h2>Alert Management</h2>
            <button class="btn btn-primary" onclick="document.getElementById('newAlertForm').style.display='block'">
                + Simulate New Alert
            </button>
            
            <div id="newAlertForm" style="display:none; margin-top: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 5px;">
                <form method="POST" action="/alerts">
                    <div class="form-group">
                        <label>Device ID</label>
                        <input type="text" name="device_id" required>
                    </div>
                    <div class="form-group">
                        <label>Location (Lat, Long)</label>
                        <input type="text" name="location" placeholder="17.3850, 78.4867" required>
                    </div>
                    <button type="submit" class="btn btn-danger">Trigger Emergency Alert</button>
                </form>
            </div>
        </div>
        
        <div class="card">
            <h2>All Alerts</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Device</th>
                        <th>Status</th>
                        <th>Location</th>
                        <th>Timestamp</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for alert in alerts %}
                    <tr>
                        <td>{{ alert.id }}</td>
                        <td>{{ alert.device_id }}</td>
                        <td>
                            <span class="badge {% if alert.status == 'active' %}badge-danger{% else %}badge-success{% endif %}">
                                {{ alert.status.upper() }}
                            </span>
                        </td>
                        <td>{{ alert.location }}</td>
                        <td>{{ alert.timestamp }}</td>
                        <td>
                            {% if alert.status == 'active' %}
                            <button class="btn btn-success" onclick="resolveAlert({{ alert.id }})">Resolve</button>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        function resolveAlert(alertId) {
            fetch('/api/resolve_alert/' + alertId, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if(data.success) location.reload();
                });
        }
    </script>
{% endblock %}
""")

DEVICES_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
{% block content %}
    <div class="container">
        <div class="card">
            <h2>Device Management</h2>
            <button class="btn btn-primary" onclick="document.getElementById('newDeviceForm').style.display='block'">
                + Register New Device
            </button>
            
            <div id="newDeviceForm" style="display:none; margin-top: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 5px;">
                <form method="POST" action="/devices">
                    <div class="form-group">
                        <label>Device ID</label>
                        <input type="text" name="device_id" required>
                    </div>
                    <div class="form-group">
                        <label>User Name</label>
                        <input type="text" name="user_name" required>
                    </div>
                    <div class="form-group">
                        <label>Device Type</label>
                        <select name="device_type">
                            <option>Bracelet</option>
                            <option>Ring</option>
                            <option>Pendant</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">Register Device</button>
                </form>
            </div>
        </div>
        
        <div class="card">
            <h2>Registered Devices</h2>
            <table>
                <thead>
                    <tr>
                        <th>Device ID</th>
                        <th>User</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Registered</th>
                    </tr>
                </thead>
                <tbody>
                    {% for device in devices %}
                    <tr>
                        <td>{{ device.device_id }}</td>
                        <td>{{ device.user_name }}</td>
                        <td>{{ device.device_type }}</td>
                        <td><span class="badge badge-success">{{ device.status }}</span></td>
                        <td>{{ device.registered_at }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}
""")

CONTACTS_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
{% block content %}
    <div class="container">
        <div class="card">
            <h2>Emergency Contacts</h2>
            <button class="btn btn-primary" onclick="document.getElementById('newContactForm').style.display='block'">
                + Add Contact
            </button>
            
            <div id="newContactForm" style="display:none; margin-top: 1rem; padding: 1rem; background: #f8f9fa; border-radius: 5px;">
                <form method="POST" action="/contacts">
                    <div class="form-group">
                        <label>Name</label>
                        <input type="text" name="name" required>
                    </div>
                    <div class="form-group">
                        <label>Phone Number</label>
                        <input type="tel" name="phone" required>
                    </div>
                    <div class="form-group">
                        <label>Relationship</label>
                        <input type="text" name="relationship" placeholder="e.g., Family, Friend">
                    </div>
                    <button type="submit" class="btn btn-primary">Add Contact</button>
                </form>
            </div>
        </div>
        
        <div class="card">
            <h2>Contact List</h2>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Phone</th>
                        <th>Relationship</th>
                        <th>Added</th>
                    </tr>
                </thead>
                <tbody>
                    {% for contact in contacts %}
                    <tr>
                        <td>{{ contact.name }}</td>
                        <td>{{ contact.phone }}</td>
                        <td>{{ contact.relationship }}</td>
                        <td>{{ contact.added_at }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}
""")

AUDIO_TEMPLATE = BASE_TEMPLATE.replace("{% block content %}{% endblock %}", """
{% block content %}
    <div class="container">
        <div class="card">
            <h2>Audio Recordings</h2>
            <p>Emergency audio recordings captured by devices during alerts.</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Alert ID</th>
                        <th>Device</th>
                        <th>Duration</th>
                        <th>Recorded At</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for audio in audio_files %}
                    <tr>
                        <td>{{ audio.alert_id }}</td>
                        <td>{{ audio.device_id }}</td>
                        <td>{{ audio.duration }}</td>
                        <td>{{ audio.recorded_at }}</td>
                        <td><span class="badge badge-warning">Stored</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
{% endblock %}
""")

# Routes
@app.route('/')
def dashboard():
    active_alerts_count = len([a for a in alerts if a['status'] == 'active'])
    recent = alerts[-5:] if alerts else []
    
    return render_template_string(DASHBOARD_TEMPLATE,
        total_alerts=len(alerts),
        active_alerts=active_alerts_count,
        total_devices=len(devices),
        total_contacts=len(contacts),
        recent_alerts=reversed(recent))

@app.route('/alerts', methods=['GET', 'POST'])
def alerts_page():
    if request.method == 'POST':
        alert = {
            'id': len(alerts) + 1,
            'device_id': request.form['device_id'],
            'location': request.form['location'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'active'
        }
        alerts.append(alert)
        
        # Simulate audio recording
        audio_files.append({
            'alert_id': alert['id'],
            'device_id': alert['device_id'],
            'duration': '00:45',
            'recorded_at': alert['timestamp']
        })
        
        return redirect(url_for('alerts_page'))
    
    return render_template_string(ALERTS_TEMPLATE, alerts=reversed(alerts))

@app.route('/devices', methods=['GET', 'POST'])
def devices_page():
    if request.method == 'POST':
        device = {
            'device_id': request.form['device_id'],
            'user_name': request.form['user_name'],
            'device_type': request.form['device_type'],
            'status': 'Active',
            'registered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        devices.append(device)
        return redirect(url_for('devices_page'))
    
    return render_template_string(DEVICES_TEMPLATE, devices=devices)

@app.route('/contacts', methods=['GET', 'POST'])
def contacts_page():
    if request.method == 'POST':
        contact = {
            'name': request.form['name'],
            'phone': request.form['phone'],
            'relationship': request.form.get('relationship', 'N/A'),
            'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        contacts.append(contact)
        return redirect(url_for('contacts_page'))
    
    return render_template_string(CONTACTS_TEMPLATE, contacts=contacts)

@app.route('/audio')
def audio_page():
    return render_template_string(AUDIO_TEMPLATE, audio_files=audio_files)

@app.route('/api/resolve_alert/<int:alert_id>', methods=['POST'])
def resolve_alert(alert_id):
    for alert in alerts:
        if alert['id'] == alert_id:
            alert['status'] = 'resolved'
            return jsonify({'success': True})
    return jsonify({'success': False})

# API endpoints for device communication
@app.route('/api/emergency', methods=['POST'])
def emergency_alert():
    data = request.json
    alert = {
        'id': len(alerts) + 1,
        'device_id': data.get('device_id'),
        'location': data.get('location'),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'active'
    }
    alerts.append(alert)
    return jsonify({'success': True, 'alert_id': alert['id']})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)