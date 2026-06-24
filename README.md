# Bidi Popup

ابزاری سبک برای **لینوکس (X11)** که متن انتخاب‌شده را در یک **پنجره راست‌چین** نشان می‌دهد — مخصوص خواندن متن مخلوط **فارسی/انگلیسی** (یا عربی/عبری) داخل برنامه‌هایی که راست‌چین را درست نشان نمی‌دهند (IDE، مرورگر، چت AI و …).

با **`Ctrl+Alt+Space`** یک پنجره شبیه macOS کنار موس باز می‌شود و متن را درست و راست‌چین می‌بینی.

[![Platform](https://img.shields.io/badge/پلتفرم-Linux%20(X11)-blue)](https://github.com/ha3san/bidi-popup)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## چرا؟

خیلی از برنامه‌ها متن دوزبانه RTL/LTR را به‌هم‌ریخته نشان می‌دهند. به‌جای جنگیدن با UI، متن را انتخاب کن و با یک کلید میانبر در پنجرهٔ مخصوص RTL بخوان.

## امکانات

- میانبر سراسری: `Ctrl+Alt+Space` (Ctrl و Alt چپ یا راست)
- خواندن **متن انتخاب‌شده** (highlight) یا **کلیپ‌بورد** (`Ctrl+C`)
- ظاهر شبیه macOS: دکمه‌های قرمز/زرد/سبز، drag، resize، سایه
- تعویض RTL/LTR، اندازه فونت، تم روشن/تاریک (هماهنگ با GNOME)
- رندر Markdown اگر متن شبیه markdown باشد
- آیکون کنار ساعت (system tray) و اجرای خودکار بعد از لاگین

---

## پیش‌نیازها

- اوبونتو یا توزیع مشابه با **X11** (فعلاً Wayland پشتیبانی نمی‌شود)
- Python **۳.۱۰+**

### بسته‌های سیستمی

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip xclip
```

### فونت فارسی (پیشنهادی)

```bash
sudo apt install -y fonts-vazirmatn
```

---

## نصب

```bash
git clone https://github.com/ha3san/bidi-popup.git
cd bidi-popup

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

chmod +x start.sh install-autostart.sh
```

---

## استفاده

### روزمره

1. متن را در هر برنامه **انتخاب** کن (highlight) — یا با `Ctrl+C` کپی کن
2. **`Ctrl+Alt+Space`** را بزن
3. متن را **راست‌چین** در پنجره بخوان
4. با **`Esc`** یا دکمهٔ قرمز (×) ببند

### میانبرهای داخل پنجره

| کلید | کار |
|------|-----|
| `Esc` | بستن پنجره |
| `Ctrl+C` | کپی متن |
| `Ctrl+F` | جستجو در متن |
| `Ctrl+=` / `Ctrl+-` | بزرگ‌تر / کوچک‌تر کردن فونت |

دکمه‌های نوار بالا: **RTL/LTR** · **A− / A+** · **Copy** · **تم (◐)**

### اجرا

```bash
./start.sh
```

فقط **یک نمونه** در پس‌زمینه اجرا می‌شود (با `flock`).

### اجرای خودکار بعد از لاگین (اوبونتو / GNOME)

```bash
./install-autostart.sh
```

این دستور فایل `~/.config/autostart/bidi-popup.desktop` را با مسیر درست نصب می‌کند.

---

## ساختار پروژه

| فایل | کار |
|------|-----|
| `listener.py` | گوش دادن به hotkey + آیکون کنار ساعت |
| `popup.py` | رابط پنجره |
| `theme.py` | تم روشن/تاریک |
| `start.sh` | اجرای برنامه |
| `install-autostart.sh` | نصب autostart |

## محدودیت‌ها

- فقط **X11** — Wayland هنوز پشتیبانی نمی‌شود
- برای خواندن selection به `xclip` نیاز است
- در بعضی سیستم‌ها hotkey سراسری ممکن است به مجوز خاص نیاز داشته باشد

## لایسنس

[MIT](LICENSE)

---
---

# English

A lightweight **Linux (X11)** tool that shows selected text in a **right-to-left popup** — ideal for mixed Persian/English, Arabic, or Hebrew text in LTR apps.

Press **`Ctrl+Alt+Space`** to open a macOS-style RTL popup near your cursor.

## Features

- Global hotkey: `Ctrl+Alt+Space`
- Primary selection or clipboard (`Ctrl+C`)
- macOS-style UI, RTL/LTR toggle, font size, light/dark theme
- Markdown rendering, search, system tray, autostart

## Requirements

```bash
sudo apt install python3-venv python3-pip xclip
sudo apt install fonts-vazirmatn   # optional Persian font
```

## Install

```bash
git clone https://github.com/ha3san/bidi-popup.git
cd bidi-popup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x start.sh install-autostart.sh
```

## Usage

1. Highlight text (or `Ctrl+C`)
2. Press `Ctrl+Alt+Space`
3. Read RTL-aligned text
4. Press `Esc` or the red button to close

```bash
./start.sh                  # run
./install-autostart.sh      # autostart on login
```

## License

[MIT](LICENSE)
