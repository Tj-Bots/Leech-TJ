#!/usr/bin/env python3
"""Keeps a Heroku web dyno awake: it sleeps after 30 minutes without web
traffic, so the bot pings its own BASE_URL every 10 minutes (only on Heroku,
where PORT is set)."""
from logging import error as log_error
from os import environ
from time import sleep

from requests import get

BASE_URL = environ.get("BASE_URL", "").strip().rstrip("/")
INTERVAL = int(environ.get("ALIVE_INTERVAL", "600") or 600)

if environ.get("PORT") and BASE_URL:
    while True:
        try:
            get(BASE_URL, timeout=30)
            sleep(INTERVAL)
        except Exception as e:
            log_error(f"alive.py: {e}")
            sleep(5)
