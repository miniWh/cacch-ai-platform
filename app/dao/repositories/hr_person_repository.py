"""HR persondetail read-only lookup."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class PersonDetailRow:
    staff_no: str
    mobile: str
    name: str
    email: str | None
    staff_status: str


class PersonDetailRepository:
    """Read-only access to shared HR table `persondetail`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_mobile(self, mobile: str) -> PersonDetailRow | None:
        sql = text(
            """
            SELECT "staffNo" AS staff_no,
                   "mobileNo" AS mobile,
                   "staffName" AS name,
                   "workEmail" AS email,
                   "staffStatus" AS staff_status
            FROM persondetail
            WHERE "mobileNo" = :mobile
            LIMIT 2
            """
        )
        rows = self._session.execute(sql, {"mobile": mobile}).mappings().all()
        if not rows:
            return None
        if len(rows) > 1:
            # Prefer IN_SERVICE if multiple
            for row in rows:
                if str(row["staff_status"] or "") == "IN_SERVICE":
                    return PersonDetailRow(
                        staff_no=str(row["staff_no"]),
                        mobile=str(row["mobile"]),
                        name=str(row["name"]),
                        email=str(row["email"]) if row["email"] else None,
                        staff_status=str(row["staff_status"]),
                    )
        row = rows[0]
        return PersonDetailRow(
            staff_no=str(row["staff_no"]),
            mobile=str(row["mobile"]),
            name=str(row["name"]),
            email=str(row["email"]) if row["email"] else None,
            staff_status=str(row["staff_status"]),
        )

    def get_staff_status(self, staff_no: str) -> str | None:
        sql = text(
            """
            SELECT "staffStatus" AS staff_status
            FROM persondetail
            WHERE "staffNo" = :staff_no
            LIMIT 1
            """
        )
        row = self._session.execute(sql, {"staff_no": staff_no}).mappings().first()
        if row is None:
            return None
        return str(row["staff_status"]) if row["staff_status"] is not None else None
