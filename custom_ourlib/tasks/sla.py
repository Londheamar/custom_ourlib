# tasks/sla.py
# Purpose: Hourly SLA escalation check for KSO Support Issue.
import frappe
from frappe.utils import now_datetime, get_datetime, add_to_date
from datetime import time

SLA_HOURS = {
    "Sev-1 Critical": 1,
    "Sev-2 High": 4,
    "Sev-3 Medium": 24,
    "Sev-4 Low": 72,
}

WORK_START = time(9, 30)
WORK_END = time(18, 30)


def is_working_time():
    now = now_datetime()

    # Monday=0 ... Sunday=6
    if now.weekday() >= 5:  # Saturday/Sunday
        return False

    current_time = now.time()

    return WORK_START <= current_time <= WORK_END


def check_sla():
    # Skip entire job outside business hours
    if not is_working_time():
        return

    issues = frappe.get_all(
        "KSO Support Issue",
        filters={"support_status": ["not in", ["Resolved", "Closed"]]},
        fields=["name", "creation", "severity", "escalated", "escalation_level"],
        limit_page_length=500,
    )

    current = now_datetime()

    for issue in issues:
        hours = SLA_HOURS.get(issue.severity, 24)
        due = add_to_date(get_datetime(issue.creation), hours=hours)

        if current > due:
            doc = frappe.get_doc("KSO Support Issue", issue.name)

            doc.flags.ignore_validate = True
            doc.flags.ignore_mandatory = True

            doc.escalated = 1
            doc.escalation_level = (doc.escalation_level or 0) + 1

            doc.add_comment(
                "Comment",
                f"SLA breached. Escalated automatically. SLA target: {hours} hours."
            )

            doc.save(ignore_permissions=True)

    frappe.db.commit()



def check_sla_():
    issues = frappe.get_all(
        "KSO Support Issue",
        filters={"support_status": ["not in", ["Resolved", "Closed"]]},
        fields=["name", "creation", "severity", "escalated", "escalation_level"],
        limit_page_length=500,
    )
    current = now_datetime()
    for issue in issues:
        hours = SLA_HOURS.get(issue.severity, 24)
        due = add_to_date(get_datetime(issue.creation), hours=hours)
        if current > due:
            doc = frappe.get_doc("KSO Support Issue", issue.name)

            doc.flags.ignore_validate = True
            doc.flags.ignore_mandatory = True

            doc.escalated = 1
            doc.escalation_level = (doc.escalation_level or 0) + 1
            doc.add_comment("Comment", f"SLA breached. Escalated automatically. SLA target: {hours} hours.")
            doc.save(ignore_permissions=True)
    frappe.db.commit()
