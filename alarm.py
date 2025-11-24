from gpiozero import MotionSensor, Buzzer, LED
from flask import Flask, render_template_string, redirect, url_for, request
import threading
import time as time_module
import requests
from datetime import datetime, time as dtime

# GPIO-Pins
PIR_PIN = 17
BUZZER_PIN = 18
LED_PIN = 27

PIN_CODE = "1811"

# Telegram-Konfiguration
TELEGRAM_BOT_TOKEN = "8295131851:AAEGTotKaTzIvAxqxcNYk90zNOFx12vVNfk"
TELEGRAM_CHAT_ID = "8428261562"  

# Raspberry-PI Anschlusssensoren
pir = MotionSensor(PIR_PIN)
buzzer = Buzzer(BUZZER_PIN)
led = LED(LED_PIN)

app = Flask(__name__)


manual_armed = False       # manuell scharf/unscharf
night_override_off = False # Nachtmodus für diese Nacht deaktiviert
last_event = None
event_log = []


 
def send_telegram_message(text: str):
    # Schickt eine Nachricht über das Telegram-Bot-API.
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram nicht konfiguriert, überspringe Nachricht.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
        })
        if not response.ok:
            print("Telegram-Fehler:", response.text)
    except Exception as e:
        print("Fehler beim Senden an Telegram:", e)


def log_event(text: str):
    # Speichert Ereignis mit Zeitstempel und gibt es aus.
    global last_event, event_log
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] {text}"
    last_event = entry
    event_log.insert(0, entry)
    event_log = event_log[:20]
    print(entry)


def alarm_on():
    buzzer.on()
    led.on()


def alarm_off():
    buzzer.off()
    led.off()

 # Zeitfenster geht über Mitternacht: [22:30, 24:00) U [00:00, 06:00)
def is_night_window():
    now = datetime.now().time()
    start = dtime(22, 30)
    end = dtime(6, 0)
    return now >= start or now < end


def is_system_armed():
    # Effektiver Scharf-Status:
    # - Wenn Nachtfenster aktiv und nicht übersteuert → scharf
    # - Sonst nach manuellem Status
    if is_night_window() and not night_override_off:
        return True
    return manual_armed


def monitor_motion():
    # Läuft in einem Hintergrundthread und überwacht den PIR.
    global night_override_off
    while True:
        try:
            # Nacht-Override zurücksetzen, wenn man nicht mehr im Nachtfenster ist
            if not is_night_window() and night_override_off:
                night_override_off = False
                log_event("Nacht-Override zurückgesetzt (neuer Tag).")

            if pir.motion_detected:
                if is_system_armed():
                    log_event("Bewegung erkannt! Alarm ausgelöst.")
                    alarm_on()
                    send_telegram_message("Bewegung erkannt! Alarm auf deinem Raspberry Pi!")
                    time_module.sleep(5)   # Alarmdauer
                    alarm_off()
                else:
                    log_event("Bewegung erkannt, aber System ist UNSCHARF.")
                    time_module.sleep(2)
            time_module.sleep(0.1)
        except Exception as e:
            print("Fehler in monitor_motion:", e)
            time_module.sleep(1)


# Weboberfläche (Flask) 
HTML_TEMPLATE = """
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Raspberry Pi Alarmanlage</title>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 20px auto; }
    .status { padding: 10px; border-radius: 5px; margin-bottom: 10px; }
    .armed { background: #ffdddd; }
    .disarmed { background: #ddffdd; }
    .buttons form {
      display: inline-block;
      margin-right: 10px;
      margin-top: 5px;
    }
    button {
      padding: 8px 12px;
      border-radius: 4px;
      border: 1px solid #333;
      background: #f5f5f5;
      cursor: pointer;
    }
    input[type=password] {
      padding: 6px;
      margin-right: 5px;
    }
    .log { margin-top: 20px; }
    li { margin-bottom: 4px; }
    .small { font-size: 0.9em; color: #555; }
  </style>
</head>
<body>
  <h1>Raspberry Pi Alarmanlage</h1>

  <div class="status {{ 'armed' if armed else 'disarmed' }}">
    <strong>Status:</strong>
    {% if armed %}
      SCHARF
      {% if auto_night and not manual_armed and not night_override_off %}
        (Nachtmodus)
      {% elif manual_armed %}
        (manuell)
      {% endif %}
    {% else %}
      UNSCHARF
      {% if auto_night and night_override_off %}
        (Nachtmodus übersteuert)
      {% endif %}
    {% endif %}
    <br>
    <span class="small">
      Nachtmodus aktiv von 22:30 bis 06:00 Uhr.
      {% if auto_night %}
        (Gerade im Nachtzeitfenster)
      {% else %}
        (Aktuell außerhalb des Nachtzeitfensters)
      {% endif %}
    </span><br>
    {% if last_event %}
      <strong>Letztes Ereignis:</strong> {{ last_event }}
    {% else %}
      <strong>Letztes Ereignis:</strong> Noch keins
    {% endif %}
  </div>

  <h2>Steuerung</h2>
  <p class="small">Für alle Aktionen wird der PIN benötigt.</p>

  <div class="buttons">
    {% if not armed %}
      <form method="post" action="{{ url_for('arm') }}">
        <input type="password" name="pin" placeholder="PIN" required>
        <button type="submit">Scharf schalten</button>
      </form>
    {% else %}
      <form method="post" action="{{ url_for('disarm') }}">
        <input type="password" name="pin" placeholder="PIN" required>
        <button type="submit">Entschärfen</button>
      </form>
    {% endif %}

    <form method="post" action="{{ url_for('test_alarm') }}">
      <input type="password" name="pin" placeholder="PIN" required>
      <button type="submit">Test-Alarm</button>
    </form>
  </div>

  <div class="log">
    <h2>Ereignis-Log</h2>
    <ul>
      {% for e in event_log %}
        <li>{{ e }}</li>
      {% endfor %}
    </ul>
  </div>
</body>
</html>
"""


@app.route("/")
def index():
    armed = is_system_armed()
    auto_night = is_night_window()
    return render_template_string(
        HTML_TEMPLATE,
        armed=armed,
        auto_night=auto_night,
        manual_armed=manual_armed,
        night_override_off=night_override_off,
        last_event=last_event,
        event_log=event_log
    )


@app.route("/arm", methods=["POST"])
def arm():
    global manual_armed, night_override_off
    pin = request.form.get("pin", "")
    if pin != PIN_CODE:
        log_event("Falscher PIN beim Scharf schalten (Web).")
        return redirect(url_for('index'))

    manual_armed = True
    night_override_off = False  # wenn manuell scharf, Nacht-Override zurücksetzen
    log_event("System manuell scharf geschaltet (Web).")
    return redirect(url_for('index'))


@app.route("/disarm", methods=["POST"])
def disarm():
    global manual_armed, night_override_off
    pin = request.form.get("pin", "")
    if pin != PIN_CODE:
        log_event("Falscher PIN beim Entschärfen (Web).")
        return redirect(url_for('index'))

    manual_armed = False
    alarm_off()
    if is_night_window():
        night_override_off = True  # Nacht Nachtmodus aus
        log_event("System entschärft, Nachtmodus für diese Nacht übersteuert (Web).")
    else:
        log_event("System entschärft (Web).")
    return redirect(url_for('index'))


@app.route("/test", methods=["POST"])
def test_alarm():
    pin = request.form.get("pin", "")
    if pin != PIN_CODE:
        log_event("Falscher PIN beim Test-Alarm (Web).")
        return redirect(url_for('index'))

    log_event("Test-Alarm ausgelöst (Web).")
    alarm_on()
    send_telegram_message("Test-Alarm vom Raspberry Pi.")
    time_module.sleep(3)
    alarm_off()
    return redirect(url_for('index'))


def main():
    # Hintergrundthread für Bewegungsüberwachung starten
    t = threading.Thread(target=monitor_motion, daemon=True)
    t.start()

    # Flask-Webserver starten
    app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()



