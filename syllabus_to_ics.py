"""
syllabus_to_ics.py

Converts an MIT Sloan syllabus PDF to an ICS calendar file
using the Anthropic API for extraction and icalendar for generation.

Usage:
    python syllabus_to_ics.py <path_to_syllabus.pdf> [--output <path_to_output.ics>]

Dependencies:
    pip install anthropic icalendar python-dateutil
"""

import argparse
import base64
import json
import re
import sys
import uuid
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import anthropic
from icalendar import Calendar, Event, Alarm


TIMEZONE = "America/New_York"
TZ = ZoneInfo(TIMEZONE)
PRODID = "-//MIT SFMBA 2027//Syllabus ICS Generator//EN"
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 16000

EXTRACTION_PROMPT = """You are extracting calendar events from an MIT Sloan course syllabus PDF.

Extract every scheduled item including:
- Class sessions / lectures
- Recitations / sections
- Assignment due dates
- Exams
- Project milestones
- Guest speaker sessions
- No-class days (include these too, as all-day events)

For each event return a JSON object with these fields:
- "summary": short title e.g. "15.338 | Leadership and Teams Lab"
- "date": in YYYY-MM-DD format
- "start_time": in HH:MM 24h format, or null if all-day
- "end_time": in HH:MM 24h format, or null if all-day
- "location": room or "Zoom" or null
- "description": any additional detail (assignment name, topic, guest speaker, etc.)
- "type": one of "lecture", "recitation", "assignment", "exam", "project", "no_class", "other"

If a time range appears in the syllabus header (e.g. "Tuesdays 10-11:30AM") apply it to
all sessions of that type unless a specific time is given for that row.

Return ONLY a JSON object in this exact structure, no preamble, no markdown fences:
{
  "course_number": "15.XXX",
  "course_name": "Full course name",
  "events": [
    {
      "summary": "...",
      "date": "YYYY-MM-DD",
      "start_time": "HH:MM",
      "end_time": "HH:MM",
      "location": "...",
      "description": "...",
      "type": "lecture"
    }
  ]
}
"""


def read_pdf_as_base64(pdf_path: Path) -> str:
    """Read a PDF file and return its base64-encoded contents.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Base64-encoded string of the PDF contents.
    """
    with open(pdf_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def extract_events_from_pdf(pdf_path: Path, client: anthropic.Anthropic) -> dict:
    """Send the PDF to the Anthropic API and extract structured event data.

    Args:
        pdf_path: Path to the syllabus PDF.
        client: Authenticated Anthropic client.

    Returns:
        Parsed dict containing course info and list of events.

    Raises:
        ValueError: If the API response cannot be parsed as JSON.
    """
    pdf_data = read_pdf_as_base64(pdf_path)

    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": EXTRACTION_PROMPT,
                    },
                ],
            }
        ],
    )

    if message.stop_reason == "max_tokens":
        print("Warning: response was truncated — try a shorter syllabus or increase MAX_TOKENS", file=sys.stderr)

    raw = message.content[0].text.strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"API response was not valid JSON: {e}\n\nRaw response:\n{raw}") from e


def build_alarm(minutes_before: int, description: str = "Reminder") -> Alarm:
    """Build a VALARM component.

    Args:
        minutes_before: How many minutes before the event to trigger.
        description: Alarm display text.

    Returns:
        An Alarm icalendar component.
    """
    alarm = Alarm()
    alarm.add("ACTION", "DISPLAY")
    alarm.add("DESCRIPTION", description)
    alarm.add("TRIGGER", timedelta(minutes=-minutes_before))
    return alarm


def parse_event_datetime(event_date: str, event_time: str | None) -> datetime | date:
    """Parse date and optional time strings into a datetime or date object.

    Args:
        event_date: Date string in YYYY-MM-DD format.
        event_time: Time string in HH:MM format, or None for all-day.

    Returns:
        A timezone-aware datetime (America/New_York) if time given, else a date object.
    """
    parsed_date = date.fromisoformat(event_date)

    if event_time is None:
        return parsed_date

    hour, minute = map(int, event_time.split(":"))
    return datetime(parsed_date.year, parsed_date.month, parsed_date.day, hour, minute, tzinfo=TZ)


def build_calendar(extracted: dict) -> Calendar:
    """Build a full Calendar object from extracted event data.

    Args:
        extracted: Dict returned by extract_events_from_pdf.

    Returns:
        A populated Calendar object ready to serialise.
    """
    course_number = extracted.get("course_number", "UNKNOWN")
    course_name = extracted.get("course_name", "Unknown Course")
    events = extracted.get("events", [])

    cal = Calendar()
    cal.add("VERSION", "2.0")
    cal.add("PRODID", PRODID)
    cal.add("CALSCALE", "GREGORIAN")
    cal.add("METHOD", "PUBLISH")
    cal.add("X-WR-CALNAME", f"MIT SFMBA | {course_number}")
    cal.add("X-WR-TIMEZONE", TIMEZONE)
    cal.add("X-WR-CALDESC", f"{course_number} {course_name} - MIT Sloan Fellows MBA 2026-2027")

    now_utc = datetime.now(tz=timezone.utc)

    for raw_event in events:
        event_date = raw_event.get("date")
        start_time = raw_event.get("start_time")
        end_time = raw_event.get("end_time")

        if not event_date:
            continue

        vevent = Event()
        vevent.add("UID", f"{uuid.uuid4()}@mit.sfmba.2027")
        vevent.add("DTSTAMP", now_utc)
        vevent.add("CREATED", now_utc)

        dtstart = parse_event_datetime(event_date, start_time)
        vevent.add("DTSTART", dtstart)

        if end_time and start_time:
            dtend = parse_event_datetime(event_date, end_time)
        elif start_time is None:
            dtend = date.fromisoformat(event_date) + timedelta(days=1)
        else:
            dtend = dtstart

        vevent.add("DTEND", dtend)
        vevent.add("SUMMARY", raw_event.get("summary", f"{course_number} | Class"))

        location = raw_event.get("location")
        if location:
            vevent.add("LOCATION", location)

        event_type = raw_event.get("type", "other")
        description_parts = [f"Type: {event_type}"]

        raw_desc = raw_event.get("description")
        if raw_desc:
            description_parts.append(raw_desc)

        description_parts.append(f"MIT SFMBA 2026-2027 | {course_number} {course_name}")
        vevent.add("DESCRIPTION", "\n".join(description_parts))

        if start_time and event_type != "assignment":
            vevent.add_component(build_alarm(1440))
            vevent.add_component(build_alarm(10))

        if event_type == "assignment":
            vevent.add_component(build_alarm(1440))

        cal.add_component(vevent)

    return cal


def write_ics(cal: Calendar, output_path: Path) -> None:
    """Serialise the Calendar and write it to disk.

    Args:
        cal: Populated Calendar object.
        output_path: Destination file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(cal.to_ical())


def derive_output_path(pdf_path: Path) -> Path:
    """Derive a default ICS output path from the PDF path.

    Args:
        pdf_path: Path to the source PDF.

    Returns:
        Sibling ics_files/<stem>.ics path.
    """
    ics_dir = pdf_path.parent.parent / "ics_files"
    return ics_dir / f"{pdf_path.stem}.ics"


def confirm_output_path(output_path: Path) -> Path:
    """Prompt the user to confirm or change the output path.

    Args:
        output_path: Derived default output path.

    Returns:
        Confirmed or user-supplied output path.
    """
    print(f"Output file: {output_path}")
    response = input("Press Enter to confirm, or type a new path: ").strip()
    if response:
        return Path(response).expanduser().resolve()
    return output_path


def main() -> None:
    """Entry point: parse args, run extraction, write ICS."""
    arg_parser = argparse.ArgumentParser(
        description="Convert an MIT Sloan syllabus PDF to an ICS calendar file."
    )
    arg_parser.add_argument("pdf", type=Path, help="Path to the syllabus PDF")
    arg_parser.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Output ICS file path (default: ics_files/<pdf_stem>.ics, prompted for confirmation)"
    )
    args = arg_parser.parse_args()

    pdf_path: Path = args.pdf.resolve()
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    derived = args.output.resolve() if args.output else derive_output_path(pdf_path)
    output_path = confirm_output_path(derived)

    print(f"Reading: {pdf_path.name}")
    client = anthropic.Anthropic()

    print("Extracting events via Anthropic API...")
    try:
        extracted = extract_events_from_pdf(pdf_path, client)
    except ValueError as e:
        print(f"Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)

    course = f"{extracted.get('course_number', '?')} {extracted.get('course_name', '')}"
    event_count = len(extracted.get("events", []))
    print(f"Found {event_count} events for {course}")

    cal = build_calendar(extracted)
    write_ics(cal, output_path)
    print(f"Written: {output_path}")


if __name__ == "__main__":
    main()
