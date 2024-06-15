import requests
import urllib.request
import os
import json
from num2words import num2words
from pprint import pprint

BASE_URL = "https://symposium.vis.ethz.ch/"
URL = f"{BASE_URL}/en/viscon2024/"
SPECIAL = ["\\", "&", "%", "$", "#", "_", "{", "}", "~", "^"]


def escape_latex(text):
    if not text:
        return ""

    for c in SPECIAL:
        text = text.replace(c, "\\" + c)

    return text


def fetch_events(token):
    cookies = {
        "_frab_session": token
    }

    response = requests.get(f"{URL}/events.json", cookies=cookies)

    return (response.status_code, response.json())


def get_events():
    if os.path.exists("events.json"):
        opt = input("events.json already exists. Re-download? [y/N] ")

        if not "y" == opt.lower():
            with open("events.json", "r") as f:
                return json.load(f)

    if not os.path.exists(".token"):
        open(".token", "w").close()

    events = None

    with open(".token", "r+") as f:
        f.seek(0)
        token = f.read().strip()

        if not token:
            token = input("Paste frab token: ")

        while True:
            status, events = fetch_events(token)
            if status == 200:
                break

            print("Invalid token")
            token = input("Paste frab token: ")

        # Save token
        f.seek(0)
        f.write(token)
        f.truncate()

    with open("events.json", "w") as f:
        json.dump(events["events"], f)

    return events["events"]

def gen_latex(event):
    pprint(event)

    dir = os.path.join("events", event["title"].replace(" ", "_"))
    os.makedirs(dir, exist_ok=True)

    with open(f"{dir}/def.tex", "w") as tex:

        # Speakers
        num_speakers = len(event["speakers"])
        tex.write(f"\\def\\numSpeakers{{{num_speakers}}}\n")

        for i, speaker in enumerate(event["speakers"]):
            name = escape_latex(speaker["public_name"])
            bio = escape_latex(speaker["abstract"]) if speaker["abstract"] else ""

            tex.write(f"\\def\\Speaker{num2words(i+1).title()}{{{name}}}\n")
            tex.write(f"\\def\\Speaker{num2words(i+1).title()}Bio{{{bio}}}\n")

            if speaker["image"]:
                image_url = BASE_URL + speaker["image"]
                image_ext = image_url.split(".")[-1].split("?")[0]

                urllib.request.urlretrieve(image_url, f"{dir}/Speaker{num2words(i+1).title()}.{image_ext}")

        # Event
        title = escape_latex(event["title"])
        subtitle = escape_latex(event["subtitle"])
        summary = escape_latex(event["abstract"])
        classifiers = map(escape_latex, event["event_classifiers"].keys())

        tex.write(f"\\def\\TalkTitle{{{title}}}\n")
        tex.write(f"\\def\\TalkSubtitle{{{subtitle}}}\n")
        tex.write(f"\\def\\TalkSummary{{{summary}}}\n")

        tex.write(f"\\def\\Tags{{{' - '.join(classifiers)}}}\n")

        links = event["links"]
        if len(links) > 0:
            tex.write(f"\\def\\Link{{{links[0]['url']}}}\n")
            tex.write(f"\\def\\LinkText{{{links[0]['title']}}}\n")

        if event["logo"]:
            logo_url = BASE_URL + event["logo"]
            logo_ext = logo_url.split(".")[-1].split("?")[0]

            urllib.request.urlretrieve(logo_url, f"{dir}/Logo.{logo_ext}")

def main():
    events = get_events()
    events = list(filter(lambda e: e["state"] in ["unconfirmed", "confirmed"], events))
    for event in events:
        gen_latex(event)


if __name__ == "__main__":
    main()
