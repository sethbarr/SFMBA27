# MIT SFMBA 2026-2027 Calendar

ICS calendar files for the MIT Sloan Fellows MBA Class of 2027. Subscribe via URL to keep your calendar up to date when files change.

## Subscribing

Use the raw GitHub URL for each file. Subscriptions update automatically when files are committed.

**URL pattern:**
```
https://raw.githubusercontent.com/<org-or-username>/<repo>/main/ics_files/<filename>.ics
```

### Available calendars

| File | Contents |
|------|----------|
| `MIT_SFMBA_June_Orientation_2026.ics` | June orientation schedule |
| `MIT_SFMBA_Summer_2026_SectionA.ics` | Summer term — Section A only |
| `MIT_SFMBA_Summer_2026_SectionB.ics` | Summer term — Section B only |
| `15809_Marketing_Strategy.ics` | 15.809 Marketing & Strategy |
| `15338_Leadership_Teams_Lab.ics` | 15.338 Leadership Teams lab | 

### Adding to Apple Calendar

File → New Calendar Subscription → paste raw URL → Subscribe

### Adding to Google Calendar

Other calendars (+ icon) → From URL → paste raw URL → Add calendar

> **Note:** Google Calendar can take up to 24 hours to reflect updates. Apple Calendar refreshes roughly every few hours. Neither can be forced to refresh immediately.

---

## Contributing

### Updating an existing ICS file

Commit the updated file to `ics_files/`. Subscribers will get the changes on their calendar's next refresh.

### Adding a new course

1. Add the syllabus PDF to `syllabi/`
2. Generate the ICS file (see below)
3. Commit the ICS to `ics_files/`
4. Update the table above

### What to keep out

- No personal information in event descriptions
- No Zoom links or meeting passwords **Note: I'm open to changing this, but would require the github repo to be private, and everyone who wants to access it would need github accounts**
- No home addresses or phone numbers

One ICS file per course. Keep event summaries generic enough to be useful to the whole cohort.

---

## Generating ICS files from a syllabus PDF

### Option A: Claude Code (recommended)

Requires Claude Code installed (`npm install -g @anthropic-ai/claude-code`) and a Claude Pro/Max subscription.

```bash
cd "/path/to/calendars"
claude "Read syllabi/<filename>.pdf and generate an ICS file. Save to ics_files/<filename>.ics. Match the format of existing files in ics_files/ — ZoneInfo America/New_York, no VTIMEZONE block, same alarm structure and PRODID style."
```

### Option B: Python script

Requires an Anthropic API key.

```bash
pip install anthropic icalendar python-dateutil
export ANTHROPIC_API_KEY=your_key_here

python syllabus_to_ics.py syllabi/<filename>.pdf
# Output goes to ics_files/<filename>.ics automatically

# Or specify the output path:
python syllabus_to_ics.py syllabi/<filename>.pdf --output ics_files/15338_Leadership.ics
```

### After generating

Check the output before committing — open the ICS in a calendar app or text editor and verify dates and times look right. The extraction is good but not perfect, particularly for syllabi with complex table layouts or ambiguous date formats.

### If you find errors

Please change in the `.ics` fill and push changes with appropriate info. That will help us keep it up to date. If you don't know how to do this, reach out :) 
