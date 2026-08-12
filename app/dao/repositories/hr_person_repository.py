"""HR 人员信息只读仓储。

从共享 HR 表 ``persondetail`` 查询员工基本信息，供账号开通校验使用。
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class PersonDetailRow:
    """HR 人员明细行（只读数据传输对象）。"""

    staff_no: str  # 工号
    mobile: str  # 手机号
    name: str  # 姓名
    email: str | None  # 工作邮箱
    staff_status: str  # 在职状态，如 IN_SERVICE


class PersonDetailRepository:
    """HR ``persondetail`` 表只读访问仓储。

    不映射 ORM 模型，直接通过原生 SQL 查询共享 HR 库。
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_by_mobile(self, mobile: str) -> PersonDetailRow | None:
        """按手机号查询员工信息。

        若存在多条记录，优先返回 ``IN_SERVICE`` 状态的员工。
        """
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
        """按工号查询员工在职状态。"""
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
