"""GuardSaaS client and data processing helpers."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import re
from typing import Any

from bs4 import BeautifulSoup
from requests import Session

from .const import (
    EXPORT_URL,
    LOGIN_CHECK_URL,
    LOGIN_URL,
    LOGOUT_URL,
    TIMEOUT_GET,
    TIMEOUT_POST,
    USER_AGENT,
)


def now_iso() -> str:
    """Return current UTC datetime in Home Assistant timestamp format."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def clean_text(text: Any) -> str:
    """Normalize string whitespace."""
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text).strip()


def clean_nested_strings(data: Any) -> Any:
    """Recursively normalize all strings inside data."""
    if isinstance(data, dict):
        return {k: clean_nested_strings(v) for k, v in data.items()}
    if isinstance(data, list):
        return [clean_nested_strings(v) for v in data]
    if isinstance(data, str):
        return clean_text(data)
    return data


def extract_plates(comment: Any) -> list[str]:
    """Extract Russian license plates from a comment text."""
    if not isinstance(comment, str):
        return []
    pattern = r"[АВЕКМНОРСТУХABEKMHOPCTYX]\d{3}[АВЕКМНОРСТУХABEKMHOPCTYX]{2}\d{2,3}"
    return re.findall(pattern, comment, re.IGNORECASE)


def ensure_file_exists(filepath: str) -> None:
    """Create cache file with base structure if it does not exist."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "plates": {},
                    "count": 0,
                    "timestamp": now_iso(),
                    "status": "initialized",
                },
                file,
                ensure_ascii=False,
                indent=2,
            )


def load_cached_data(filepath: str) -> dict[str, Any]:
    """Load cached plate data."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            raise ValueError("cache is not dict")
        return data
    except Exception:
        return {
            "plates": {},
            "count": 0,
            "status": "cache_error",
            "timestamp": now_iso(),
        }


@dataclass
class GuardSaaSResult:
    """Normalized GuardSaaS result."""

    content: str
    count: int
    state: str
    plates_data: dict[str, Any]
    timestamp: str
    status: str
    authenticated: bool
    from_cache: bool
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return result as dict."""
        return {
            "content": self.content,
            "count": self.count,
            "state": self.state,
            "plates_data": self.plates_data,
            "timestamp": self.timestamp,
            "status": self.status,
            "authenticated": self.authenticated,
            "from_cache": self.from_cache,
            "error": self.error,
        }


class GuardSaaSClient:
    """Synchronous client for GuardSaaS."""

    def __init__(
        self,
        username: str,
        password: str,
        cache_file: str,
        mandatory_plates: list[str] | None = None,
    ) -> None:
        self.username = username
        self.password = password
        self.cache_file = cache_file
        self.mandatory_plates = mandatory_plates or []

    @contextmanager
    def guarded_session(self):
        """Create requests session and logout on exit."""
        session = Session()
        session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                "Accept-Language": "ru-RU,ru;q=0.9",
            }
        )
        try:
            yield session
        finally:
            try:
                session.get(LOGOUT_URL, timeout=5)
            except Exception:
                pass
            finally:
                try:
                    session.close()
                except Exception:
                    pass

    def authenticate(self, session: Session) -> bool:
        """Authenticate in GuardSaaS."""
        try:
            response = session.get(LOGIN_URL, timeout=TIMEOUT_GET)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            csrf = soup.find("input", attrs={"name": "_csrf_token"})
            if not csrf or not csrf.get("value"):
                return False

            payload = {
                "_username": self.username,
                "_password": self.password,
                "_remember_me": "on",
                "_csrf_token": csrf["value"],
            }
            response = session.post(LOGIN_CHECK_URL, data=payload, timeout=TIMEOUT_POST)
            return response.status_code in (200, 302)
        except Exception:
            return False

    def fetch_license_data(self, session: Session) -> dict[str, Any] | None:
        """Fetch employee export data."""
        try:
            response = session.get(EXPORT_URL, timeout=TIMEOUT_GET)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                return None
            return data
        except Exception:
            return None

    def process_plates_data(self, data: dict[str, Any] | None) -> dict[str, Any]:
        """Process raw export into plate dictionary."""
        if not data:
            return {
                "plates": {},
                "count": 0,
                "status": "error",
                "timestamp": now_iso(),
                "error": "No data received",
            }

        items = data.get("items", []) or []
        plates_dict: dict[str, dict[str, str]] = {}

        for employee in items:
            if not isinstance(employee, dict):
                continue

            comment = clean_text(employee.get("comment", ""))
            employee_data = {
                "user": clean_text(employee.get("number", "")),
                "description": clean_text(employee.get("name", "")),
                "telephone": clean_text(employee.get("position", "")),
                "department": clean_text(employee.get("department", "")),
                "comment": comment,
            }

            for plate in extract_plates(comment):
                plates_dict.setdefault(plate.upper(), employee_data)

        for plate in self.mandatory_plates:
            plate_u = str(plate).upper().strip()
            if not plate_u or plate_u in plates_dict:
                continue

            found = False
            for employee in items:
                if not isinstance(employee, dict):
                    continue

                comment = clean_text(employee.get("comment", ""))
                if comment and plate_u in comment.upper():
                    plates_dict[plate_u] = {
                        "user": clean_text(employee.get("number", "")),
                        "description": clean_text(employee.get("name", "")),
                        "telephone": clean_text(employee.get("position", "")),
                        "department": clean_text(employee.get("department", "")),
                        "comment": comment,
                    }
                    found = True
                    break

            if not found:
                plates_dict[plate_u] = {
                    "user": "",
                    "description": "",
                    "telephone": "",
                    "department": "",
                    "comment": f"Mandatory plate: {plate_u}",
                }

        return {
            "plates": plates_dict,
            "count": len(plates_dict),
            "status": "success",
            "timestamp": now_iso(),
        }

    def update(self) -> dict[str, Any]:
        """Update plate data. Returns normalized dict for coordinator."""
        ensure_file_exists(self.cache_file)

        error: str | None = None
        authenticated = False
        from_cache = False

        try:
            with self.guarded_session() as session:
                authenticated = self.authenticate(session)
                if not authenticated:
                    plates_data = load_cached_data(self.cache_file)
                    error = "Authentication failed; cached data used"
                    from_cache = True
                else:
                    remote = self.fetch_license_data(session)
                    if remote:
                        plates_data = self.process_plates_data(remote)
                        plates_data = clean_nested_strings(plates_data)
                        with open(self.cache_file, "w", encoding="utf-8") as file:
                            json.dump(plates_data, file, ensure_ascii=False, indent=2)
                    else:
                        plates_data = load_cached_data(self.cache_file)
                        error = "Remote fetch failed; cached data used"
                        from_cache = True
        except Exception as exc:
            plates_data = load_cached_data(self.cache_file)
            error = clean_text(str(exc)) or "Unknown error"
            from_cache = True

        plates_data = clean_nested_strings(plates_data)
        plates_dict = plates_data.get("plates", {}) or {}
        count = int(plates_data.get("count", 0) or 0)
        status = clean_text(plates_data.get("status", "unknown"))
        timestamp = clean_text(plates_data.get("timestamp", now_iso()))
        state = "No allowed plates" if count == 0 else "Plates successfully loaded"
        if error and not plates_dict:
            state = "Error occurred"

        result = GuardSaaSResult(
            content=clean_text(" ".join([f"- {plate}" for plate in plates_dict.keys()])),
            count=count,
            state=state,
            plates_data=plates_dict,
            timestamp=timestamp,
            status=status,
            authenticated=authenticated,
            from_cache=from_cache,
            error=error,
        )
        return result.as_dict()
