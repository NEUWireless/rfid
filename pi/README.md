# Wireless Club RFID Attendance #

RFID attendance tracking system for NEU Wireless Club.

## Install ##

```bash
$ apt install libnfc libfreefare
$ pip3 install --user -e .
```

## Usage ##

Run attendance tracking:

```bash
$ wc-attendance
```

Yellow LED: New card detected, person must enter their name to be added to the system
Green LED: Success, attendance was logged

Data gets stored in `~/attendance.json`

View attendance in TUI:

```bash
$ wc-tui
```

Use up/down or j/k to navigate the user list, ENTER to see a menu of options for a person.
Use the Exit button or Ctrl-C to exit.

## Development Usage ##

For development/testing, run from repo directory:

```bash
$ python3 -m wc_attendance
```
