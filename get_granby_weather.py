import urllib.request
import json
import datetime


def get_weather():
    url = "https://wttr.in/Granby,QC?format=j1"
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode())

    current = data['current_condition'][0]
    temp_C = current['temp_C']
    desc = current['weatherDesc'][0]['value']
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    message = f"{ts} - Granby, QC: {temp_C}°C, {desc}"
    print(message)

    with open("granby_weather.txt", "w", encoding="utf-8") as f:
        f.write(message + "\n")


if __name__ == "__main__":
    get_weather()
