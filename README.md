# Bidi Popup

A lightweight **Linux (X11)** tool that shows selected text in a **right-to-left popup** — ideal for reading mixed Persian/English, Arabic, or Hebrew text inside LTR apps (IDEs, browsers, chat UIs).

Press **`Ctrl+Alt+Space`** and a macOS-style window opens near your cursor with properly aligned RTL text.

## Features

- Global hotkey: `Ctrl+Alt+Space` (left or right Ctrl/Alt)
- Reads **primary selection** (highlighted text) or **clipboard** (`Ctrl+C`)
- macOS-style UI: traffic-light buttons, drag, resize, drop shadow
- RTL / LTR toggle, font size controls, light / dark theme (follows GNOME)
- Markdown rendering when detected
- In-popup shortcuts: `Esc` close · `Ctrl+C` copy · `Ctrl+F` search
- System tray icon and optional autostart on login

## Requirements

- Linux with **X11** (Ubuntu and similar distros)
- Python **3.10+**
- System packages:

```bash
sudo apt install python3-venv xclip
```

Recommended Persian font:

```bash
sudo apt install fonts-vazirmatn
```

## Installation

```bash
git clone https://github.com/ha3san/bidi-popup.git
cd bidi-popup

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x start.sh install-autostart.sh
```

## Usage

1. **Highlight** text in any application (or copy with `Ctrl+C`)
2. Press **`Ctrl+Alt+Space`**
3. Read the RTL-aligned text in the popup
4. Press **`Esc`** or the red button to close

### Popup shortcuts

| Key | Action |
|-----|--------|
| `Esc` | Close window |
| `Ctrl+C` | Copy text |
| `Ctrl+F` | Search in text |
| `Ctrl+=` / `Ctrl+-` | Increase / decrease font size |

Toolbar buttons: **RTL/LTR** · **A− / A+** · **Copy** · **theme toggle (◐)**

## Run

```bash
./start.sh
```

Only one background instance runs at a time (enforced with `flock`).

## Autostart on login (Ubuntu / GNOME)

```bash
./install-autostart.sh
```

This writes `~/.config/autostart/bidi-popup.desktop` with the correct install path.

## How it works

```
pynput hotkey listener  →  xclip (selection / clipboard)  →  PyQt6 RTL popup
```

## Limitations

- **X11 only** — Wayland is not supported yet
- Requires `xclip` to read selected text
- Global hotkeys may need appropriate permissions on some systems

---

## استفاده (فارسی)

۱. متن را در هر برنامه **انتخاب** کن (یا `Ctrl+C` بزن)  
۲. **`Ctrl+Alt+Space`** را فشار بده  
۳. پنجره با متن **راست‌چین** باز می‌شود  
۴. با **`Esc`** یا دکمه قرمز ببند  

برای اجرای خودکار بعد از لاگین:

```bash
./install-autostart.sh
```

## Project structure

| File | Purpose |
|------|---------|
| `listener.py` | Background hotkey service + system tray |
| `popup.py` | Popup window UI |
| `theme.py` | Light / dark themes (GNOME-aware) |
| `start.sh` | Launcher script |
| `install-autostart.sh` | GNOME autostart installer |

## License

[MIT](LICENSE) © Hassan Mousavi
