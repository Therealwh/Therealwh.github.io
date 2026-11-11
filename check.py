#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка доступности tgchat.run:443 и обновление status/history/dates.
Запускается GitHub Actions каждые 5 минут."""
import socket, json, time, re, io, os, datetime, sys

HOST, PORT = "tgchat.run", 443
ROOT = os.path.dirname(os.path.abspath(__file__))
MONTHS = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]

# --- 1. TCP-проверка (доступность хоста = доступность прокси) ---
ok, ms = False, None
t0 = time.time()
try:
    s = socket.create_connection((HOST, PORT), timeout=8)
    ms = int((time.time() - t0) * 1000)
    s.close()
    ok = True
except Exception:
    ok = False

now = datetime.datetime.utcnow() + datetime.timedelta(hours=3)  # МСК
iso = now.strftime("%Y-%m-%dT%H:%M:%S+03:00")
hm = now.strftime("%H:%M")
ru_date = f"{now.day} {MONTHS[now.month-1]} {now.year}"

# --- 2. status.json ---
status_path = os.path.join(ROOT, "status.json")
try:
    status = json.load(io.open(status_path, encoding="utf-8"))
except Exception:
    status = {}
status.update({"online": ok, "last_check": iso, "response_ms": ms, "host": HOST, "port": PORT})
io.open(status_path, "w", encoding="utf-8", newline="\n").write(json.dumps(status, ensure_ascii=False))

# --- 3. history.json (последние 1000 проверок) ---
hist_path = os.path.join(ROOT, "history.json")
try:
    hist = json.load(io.open(hist_path, encoding="utf-8"))
except Exception:
    hist = []
hist.append({"t": iso, "ok": ok, "ms": ms})
hist = hist[-1000:]
io.open(hist_path, "w", encoding="utf-8", newline="\n").write(json.dumps(hist, ensure_ascii=False))

# --- 4. Обновление дат в index.html (SEO: «на 11 ноября 2026», «проверено …») ---
html_path = os.path.join(ROOT, "index.html")
html = io.open(html_path, encoding="utf-8").read()
DATE_RE = re.compile(r"\d{1,2} (?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря) \d{4}")
html_new = DATE_RE.sub(ru_date, html)
if html_new != html:
    io.open(html_path, "w", encoding="utf-8", newline="\n").write(html_new)
    print("dates refreshed:", ru_date)

# --- 5. README: дата последней проверки ---
readme_path = os.path.join(ROOT, "README.md")
try:
    rd = io.open(readme_path, encoding="utf-8").read()
    rd_new = re.sub(r"Последняя проверка: [^\n]*",
                    f"Последняя проверка: {ru_date} в {hm} МСК — {'🟢 доступен' if ok else '🔴 недоступен'}",
                    rd)
    if rd_new != rd:
        io.open(readme_path, "w", encoding="utf-8", newline="\n").write(rd_new)
except FileNotFoundError:
    pass

print(f"check done: host={HOST} online={ok} ms={ms} date={ru_date} {hm} МСК")
