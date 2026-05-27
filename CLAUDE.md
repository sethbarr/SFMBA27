# CLAUDE.md — MIT SFMBA Calendars

Handoff context for Claude Code. Read this before doing anything in this repo.

## What this repo is

ICS calendar files for the MIT Sloan Fellows MBA Class of 2027, shared across the cohort via GitHub raw URLs. Classmates subscribe to the raw URL of each file so their calendars update when files are committed.

## Your main job here

Convert syllabus PDFs into ICS calendar files. PDFs live in `syllabi/`. Output goes to `ics_files/`.

## How to generate an ICS from a syllabus PDF

Read the PDF, extract every scheduled item, and write a valid ICS file. Do not use the `syllabus_to_ics.py` script — that exists for automated/API use. You can read PDFs natively.

### What to extract

- Class sessions and lectures (with times)
- Recitations / sections
- Assignment due dates
- Exams and project milestones
- Guest speaker sessions
- No-class days (as all-day events)

### ICS format rules

Match the style of existing files in `ics_files/`. Specifically:

**Calendar header:**
```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MIT SFMBA 2027//Syllabus ICS Generator//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:MIT SFMBA | <course_number>
X-WR-TIMEZONE:America/New_York
X-WR-CALDESC:<course_number> <course_name> - MIT Sloan Fellows MBA 2026-2027
```

**Timezone:** Use `TZID=America/New_York` on DTSTART/DTEND. Do not include a VTIMEZONE block — modern clients handle IANA timezone names without it.

**Event summary format:** `<course_number> | <short description>`
e.g. `15.338 | Leadership POD Meeting #1`

**UIDs:** Generate a unique UUID per event in the format:
`<uuid4>@mit.sfmba.2027`

**Alarms:**
- Timed events (lectures, recitations): two alarms — 1440 minutes (24h) and 10 minutes before
- Assignments: one alarm — 1440 minutes before
- All-day / no-class events: no alarms

**Datetime format:**
- Timed events: `DTSTART;TZID=America/New_York:20260608T083000`
- All-day events: `DTSTART;VALUE=DATE:20260608`

**DTSTAMP / CREATED:** Use current UTC time in format `20260527T120000Z`

### What to keep out of descriptions

- No Zoom links or meeting passwords
- No personal information
- No home addresses or phone numbers

Keep descriptions generic enough to be useful to the whole cohort.

## File naming convention

`ics_files/<course_number_no_dots>_<Short_Title>.ics`

Examples:
- `15338_Leadership_Teams_Lab.ics`
- `15809_Marketing_Strategy.ics`

## After generating

Tell the user:
1. How many events were written
2. The output file path
3. Any dates or times that were ambiguous or missing from the syllabus

## Existing files for format reference

- `ics_files/15809_Marketing_Strategy.ics` — good single-course example
- `ics_files/MIT_SFMBA_Summer_2026.ics` — larger multi-event example

## Do not

- Modify existing ICS files unless asked
- Change the README without being asked
- Run `syllabus_to_ics.py` — it makes API calls
