#!/usr/bin/env python3
"""
Jednokratna provera artikla (za GitHub Actions).
Sva podešavanja dolaze iz GitHub Secrets, tako da u kodu nema ničeg privatnog.

Izlazni kod: 0 = nije dostupan / greška, 10 = DOSTUPAN (workflow tada gasi sam sebe).
"""

import os
import sys
import requests

URL = os.environ.get("ARTIKAL_URL", "")
TEKST_DOSTUPNO = [t.strip() for t in os.environ.get("TEKST_DOSTUPNO", "").split("|") if t.strip()]
TEKST_NEDOSTUPNO = [t.strip() for t in os.environ.get("TEKST_NEDOSTUPNO", "").split("|") if t.strip()]
NTFY_TEMA = os.environ.get("NTFY_TEMA", "")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TEST = os.environ.get("TEST_NOTIFIKACIJA", "false").lower() == "true"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "sr,en;q=0.8",
}


def posalji_notifikaciju(naslov, poruka):
    if NTFY_TEMA:
        try:
            requests.post(
                f"https://ntfy.sh/{NTFY_TEMA}",
                data=poruka.encode("utf-8"),
                headers={"Title": naslov.encode("utf-8"), "Click": URL, "Priority": "high"},
                timeout=15,
            )
        except requests.RequestException as e:
            print(f"Greška pri slanju ntfy notifikacije: {e}")

    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": f"{naslov}\n{poruka}"},
                timeout=15,
            )
        except requests.RequestException as e:
            print(f"Greška pri slanju Telegram poruke: {e}")


def da_li_je_dostupan():
    try:
        r = requests.get(URL, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Greška pri učitavanju stranice: {e}")
        return None

    tekst = r.text.lower()
    if TEKST_DOSTUPNO:
        return any(t.lower() in tekst for t in TEKST_DOSTUPNO)
    if TEKST_NEDOSTUPNO:
        return not any(t.lower() in tekst for t in TEKST_NEDOSTUPNO)

    print("Nije podešen ni TEKST_DOSTUPNO ni TEKST_NEDOSTUPNO.")
    return None


def main():
    if TEST:
        posalji_notifikaciju("Test", "Notifikacije rade.")
        print("Poslata test notifikacija.")
        return 0

    if not URL:
        print("Nedostaje ARTIKAL_URL secret.")
        return 0

    dostupan = da_li_je_dostupan()
    if dostupan:
        print("ARTIKAL JE DOSTUPAN!")
        posalji_notifikaciju("Artikal je dostupan!", f"Požuri: {URL}")
        return 10

    print("Još nije dostupan." if dostupan is False else "Provera nije uspela.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
