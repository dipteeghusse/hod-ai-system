"""
Automated Email Recognition Service

Polls the HoD's inbox via IMAP at a configured interval.
For each unread email:
  1. Fetches subject + body
  2. Passes to EmailIntelligenceAgent → extracts tasks, priority, deadline, assignee
  3. Saves extracted tasks to the Task table
  4. Marks the email as read (adds \\Seen flag)
  5. Logs the raw email + extraction result to AgentLog

Runs as a background asyncio task started from main.py lifespan.
Skips silently if IMAP_USER is not configured.
"""

import asyncio
import imaplib
import email
import email.header
import logging
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

from config import settings
from agents.email_intelligence_agent import EmailIntelligenceAgent
from database.db import AsyncSessionLocal, Task, AgentLog, User
from sqlalchemy import select

logger = logging.getLogger("email_poller")

_agent = EmailIntelligenceAgent()


def _decode_header(raw) -> str:
    parts = email.header.decode_header(raw or "")
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def _fetch_unread_emails() -> list[dict]:
    """Connect via IMAP, fetch unread emails, mark them as seen. Returns list of dicts."""
    if not settings.IMAP_USER or not settings.IMAP_PASSWORD:
        return []

    results = []
    try:
        conn = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        conn.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
        conn.select(settings.IMAP_FOLDER)

        _, msg_ids = conn.search(None, "UNSEEN")
        ids = msg_ids[0].split()
        # Limit to last N
        ids = ids[-settings.IMAP_MAX_EMAILS:]

        for msg_id in ids:
            _, data = conn.fetch(msg_id, "(RFC822)")
            raw = data[0][1]
            msg = email.message_from_bytes(raw)

            subject = _decode_header(msg.get("Subject", "(no subject)"))
            sender  = _decode_header(msg.get("From", ""))
            date_str = msg.get("Date", "")
            try:
                received_at = parsedate_to_datetime(date_str).isoformat()
            except Exception:
                received_at = datetime.utcnow().isoformat()

            # Extract plain-text body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        charset = part.get_content_charset() or "utf-8"
                        body = part.get_payload(decode=True).decode(charset, errors="replace")
                        break
            else:
                charset = msg.get_content_charset() or "utf-8"
                body = msg.get_payload(decode=True).decode(charset, errors="replace")

            # Mark as read
            conn.store(msg_id, "+FLAGS", "\\Seen")

            results.append({
                "subject":     subject,
                "sender":      sender,
                "received_at": received_at,
                "body":        body[:3000],   # cap to avoid token overrun
            })

        conn.logout()
    except Exception as exc:
        logger.error(f"IMAP fetch failed: {exc}")

    return results


async def _get_hod_id() -> int:
    """Return the HoD user's DB id (used as task creator)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.role == "hod").limit(1))
        user = result.scalar_one_or_none()
        return user.id if user else 1


async def _process_email(email_dict: dict, hod_id: int):
    """Run the agent on one email and persist extracted tasks."""
    subject  = email_dict["subject"]
    sender   = email_dict["sender"]
    body     = email_dict["body"]
    full_text = f"From: {sender}\nSubject: {subject}\n\n{body}"

    # Agent call — returns structured dict with tasks, summary, draft_reply
    try:
        result = _agent.process_email(full_text)
    except Exception as exc:
        logger.error(f"Agent failed for email '{subject}': {exc}")
        return

    tasks_to_create = result.get("extracted_tasks", [])
    summary         = result.get("summary", "")

    async with AsyncSessionLocal() as db:
        for t in tasks_to_create:
            # Parse deadline — default 7 days from now if missing
            raw_due = t.get("deadline") or t.get("due_date")
            try:
                due = datetime.fromisoformat(str(raw_due))
            except Exception:
                due = datetime.utcnow() + timedelta(days=7)

            task = Task(
                title=t.get("title", subject[:200]),
                description=t.get("description", body[:500]),
                status="pending",
                priority=t.get("priority", "medium"),
                category=t.get("category", "administrative"),
                due_date=due,
                progress_percentage=0,
                notes=f"Auto-extracted from email: {subject}",
                created_by_id=hod_id,
            )
            db.add(task)

        # Log the raw email + extraction
        log = AgentLog(
            agent_type="email_intelligence",
            query=f"[AUTO] {subject}",
            response=summary,
            actions_taken=[f"Extracted {len(tasks_to_create)} task(s)"],
            user_id=hod_id,
        )
        db.add(log)
        await db.commit()

    logger.info(f"Email '{subject}' → {len(tasks_to_create)} task(s) created")


async def run_email_poller():
    """
    Infinite loop: fetch unread emails → process → sleep.
    Started by main.py lifespan. Exits cleanly on CancelledError.
    """
    if not settings.IMAP_USER:
        logger.info("IMAP_USER not set — email poller disabled")
        return

    logger.info(
        f"Email poller started — inbox: {settings.IMAP_USER}, "
        f"interval: {settings.IMAP_POLL_INTERVAL}s"
    )
    hod_id = await _get_hod_id()

    while True:
        try:
            emails = await asyncio.to_thread(_fetch_unread_emails)
            if emails:
                logger.info(f"Found {len(emails)} unread email(s)")
                for em in emails:
                    await _process_email(em, hod_id)
            await asyncio.sleep(settings.IMAP_POLL_INTERVAL)
        except asyncio.CancelledError:
            logger.info("Email poller stopped")
            return
        except Exception as exc:
            logger.error(f"Poller loop error: {exc}")
            await asyncio.sleep(60)   # back off on unexpected errors
