# Bidi Popup

ابزاری سبک برای **لینوکس** و **ویندوز** که متن انتخاب‌شده را در یک **پنجره راست‌چین** نشان می‌دهد — مخصوص خواندن متن مخلوط **فارسی/انگلیسی** (یا عربی/عبری) داخل برنامه‌هایی که راست‌چین را درست نشان نمی‌دهند (IDE، مرورگر، چت AI و …).

با **`Ctrl+Alt+Space`** یک پنجره شبیه macOS کنار موس باز می‌شود و متن را درست و راست‌چین می‌بینی.

![Bidi Popup — پیش‌نمایش](docs/demo-poster.png)

[![Platform](https://img.shields.io/badge/X11-tested-green)](https://github.com/ha3san/bidi-popup)
[![Wayland](https://img.shields.io/badge/Wayland-experimental-orange)](https://github.com/ha3san/bidi-popup)
[![Windows](https://img.shields.io/badge/Windows-Setup.exe-blue)](https://github.com/ha3san/bidi-popup/releases)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## چرا؟

خیلی از برنامه‌ها متن دوزبانه RTL/LTR را به‌هم‌ریخته نشان می‌دهند. به‌جای جنگیدن با UI، متن را انتخاب کن و با یک کلید میانبر در پنجرهٔ مخصوص RTL بخوان.

## امکانات

- میانبر: `Ctrl+Alt+Space`
- **لینوکس:** X11 (تست‌شده) و Wayland (آزمایشی)
- **ویندوز:** نصب با `Setup.exe` — بدون نیاز به پایتون
- خواندن **متن انتخاب‌شده** (highlight)
- ظاهر شبیه macOS: دکمه‌های قرمز/زرد/سبز، drag، resize، سایه
- تعویض RTL/LTR، اندازه فونت، تم روشن/تاریک
- رندر Markdown اگر متن شبیه markdown باشد
- آیکون کنار ساعت (system tray) و اجرای خودکار بعد از لاگین

---

## ویندوز (بدون دانش فنی)

نیازی به نصب پایتون نیست.

1. از صفحهٔ [Releases](https://github.com/ha3san/bidi-popup/releases) فایل **`BidiPopup-Setup.exe`** را دانلود کن
2. نصب را با دابل‌کلیک انجام بده (می‌توانی «Start with Windows» را فعال کنی)
3. برنامه کنار ساعت می‌ماند — متن را انتخاب کن و **`Ctrl+Alt+Space`** بزن

اگر ویندوز SmartScreen هشدار داد (چون فایل هنوز code-sign نشده): **More info** → **Run anyway**.

ساخت نصب‌کننده از Actions هم ممکن است: workflow با نام **Windows release build** را دستی اجرا کن، یا یک تگ مثل `v1.2.0` بزن.

---

## لینوکس — پیش‌نیازها

- اوبونتو یا توزیع مشابه لینوکس
- Python **۳.۱۰+**
- محیط گرافیکی **X11** یا **Wayland**

### بسته‌های سیستمی

**X11:**
```bash
sudo apt install -y python3-venv python3-pip xclip
```

**Wayland:**
```bash
sudo apt install -y python3-venv python3-pip wl-clipboard
```

**هر دو (پیشنهادی):**
```bash
sudo apt install -y python3-venv python3-pip xclip wl-clipboard
```

### فونت فارسی (پیشنهادی)

```bash
sudo apt install -y fonts-vazirmatn
```

### نوع session تو

```bash
echo $XDG_SESSION_TYPE
```

- `x11` → hotkey خودکار کار می‌کند
- `wayland` → بعد از نصب، یک‌بار `install-shortcut.sh` لازم است

---

## لینوکس — نصب

**سریع (یک اسکریپت):**
```bash
git clone https://github.com/ha3san/bidi-popup.git
cd bidi-popup
chmod +x install.sh
./install.sh
```

**دستی:**
```bash
git clone https://github.com/ha3san/bidi-popup.git
cd bidi-popup

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

chmod +x start.sh install-autostart.sh install-shortcut.sh
```

---

## استفاده

### روزمره

1. برنامه را اجرا کن: `./start.sh`
2. متن را در هر برنامه **انتخاب** کن (highlight)
3. **`Ctrl+Alt+Space`** را بزن
4. متن را **راست‌چین** در پنجره بخوان
5. با **`Esc`** یا دکمهٔ قرمز (×) ببند

### X11 vs Wayland

| محیط | hotkey چطور کار می‌کند |
|------|------------------------|
| **X11** | خودکار — نیازی به تنظیم اضافه نیست |
| **Wayland (GNOME)** | یک‌بار `./install-shortcut.sh` بزن |

روی Wayland، shortcut از طریق GNOME به `./start.sh trigger` وصل می‌شود.

### میانبرهای داخل پنجره

| کلید | کار |
|------|-----|
| `Esc` | بستن پنجره |
| `Ctrl+C` | کپی متن از پنجره |
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

### تنظیم shortcut روی Wayland (GNOME)

```bash
./install-shortcut.sh
```

این دستور `Ctrl+Alt+Space` را در تنظیمات کیبورد GNOME ثبت می‌کند.

---

## ساختار پروژه

| فایل / پوشه | کار |
|-------------|-----|
| `listener.py` | سرویس پس‌زمینه + tray |
| `popup.py` | رابط پنجره |
| `theme.py` | تم روشن/تاریک |
| `bidi_platform/` | تشخیص X11/Wayland/Windows، selection، trigger |
| `start.sh` | اجرا / `trigger` (لینوکس) |
| `start.bat` | اجرا از سورس (ویندوز / توسعه‌دهنده) |
| `packaging/` | PyInstaller + Inno Setup برای Setup.exe |
| `install-autostart.sh` | autostart |
| `install-shortcut.sh` | shortcut GNOME (Wayland) |
| `install.sh` | نصب خودکار venv + وابستگی‌ها |
| `assets/icon.svg` | آیکون اپلیکیشن |

## محدودیت‌ها

- hotkey خودکار روی Wayland فقط با shortcut دسکتاپ (GNOME: `install-shortcut.sh`)
- KDE و compositorهای دیگر: shortcut را دستی به `./start.sh trigger` وصل کن
- روی Wayland باید `./start.sh` قبل از shortcut در حال اجرا باشد
- روی ویندوز، خواندن انتخاب متن با کپی موقت به کلیپ‌بورد انجام می‌شود (سپس بازگردانی)

## تست و پشتیبانی

| محیط | وضعیت |
|------|--------|
| **X11** (اوبونتو) | ✅ توسط نگهدارنده تست شده |
| **Wayland (GNOME)** | ⚠️ کد پشتیبانی دارد؛ روی محیط نگهدارنده تست نشده |
| **KDE / سایر compositorها** | ⚠️ تست نشده — shortcut را دستی تنظیم کنید |
| **Windows** | ⚠️ Setup.exe از CI؛ تست توسط کاربران |

اگر روی محیطی غیر از موارد بالا نصب کردید یا به مشکل خوردید، لطفاً [Issue باز کنید](https://github.com/ha3san/bidi-popup/issues/new/choose) و این‌ها را بنویسید:

- توزیع لینوکس و نسخه
- خروجی `echo $XDG_SESSION_TYPE`
- دسکتاپ (GNOME، KDE، …)
- مراحل بازتولید مشکل

بازخورد و گزارش باگ کمک می‌کند تا پشتیبانی واقعی گسترش پیدا کند.

## لایسنس

[MIT](LICENSE)

---
---

# English

A lightweight **Linux and Windows** tool that shows selected text in a **right-to-left popup**.

Press **`Ctrl+Alt+Space`** to open a macOS-style RTL popup near your cursor.

## Windows (no Python required)

1. Download **`BidiPopup-Setup.exe`** from [Releases](https://github.com/ha3san/bidi-popup/releases)
2. Install (optional: start with Windows)
3. Select text → **`Ctrl+Alt+Space`**

If SmartScreen warns you: **More info** → **Run anyway**.

## Platform notes

| Session | Hotkey |
|---------|--------|
| X11 | Built-in (`pynput`) — tested by maintainer |
| Wayland (GNOME) | Run `./install-shortcut.sh` once — experimental |
| Windows | Built-in (`pynput`); selection via temporary Ctrl+C |

## Testing & support

| Environment | Status |
|-------------|--------|
| **X11** (Ubuntu) | ✅ Tested by maintainer |
| **Wayland (GNOME)** | ⚠️ Code path exists; not tested by maintainer |
| **KDE / other compositors** | ⚠️ Untested — configure shortcut to `./start.sh trigger` manually |
| **Windows** | ⚠️ Built via CI; community-tested |

If something breaks on your setup, please [open an issue](https://github.com/ha3san/bidi-popup/issues/new/choose) with your distro, `echo $XDG_SESSION_TYPE`, desktop environment, and steps to reproduce.

## Linux requirements

```bash
sudo apt install python3-venv python3-pip xclip wl-clipboard
sudo apt install fonts-vazirmatn   # optional
```

## Linux install & run

```bash
git clone https://github.com/ha3san/bidi-popup.git
cd bidi-popup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
chmod +x start.sh install-autostart.sh install-shortcut.sh

./start.sh
./install-autostart.sh    # autostart on login
./install-shortcut.sh     # Wayland / GNOME shortcut
```

## License

[MIT](LICENSE)
