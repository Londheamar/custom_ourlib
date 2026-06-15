# tasks/sla.py
# Purpose: Hourly SLA escalation check for KSO Support Issue.
import frappe
from frappe.utils import now_datetime, get_datetime, add_to_date
from datetime import datetime, timedelta, time

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



def get_business_hours_elapsed(start_dt, end_dt):
    """
    Returns full business hours between start_dt and end_dt.
    Excludes Saturdays and Sundays.
    """
    if end_dt <= start_dt:
        return 0

    total_seconds = 0
    current_day = start_dt.date()

    while current_day <= end_dt.date():

        # Skip weekends
        if current_day.weekday() < 5:
            work_start = datetime.combine(current_day, WORK_START)
            work_end = datetime.combine(current_day, WORK_END)

            period_start = max(start_dt, work_start)
            period_end = min(end_dt, work_end)

            if period_end > period_start:
                total_seconds += (period_end - period_start).total_seconds()

        current_day += timedelta(days=1)

    return int(total_seconds // 3600)

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

            business_hours_exceeded = get_business_hours_elapsed(due, current)

            doc.flags.ignore_validate = True
            doc.flags.ignore_mandatory = True

            doc.escalated = 1
            doc.escalation_level = max(1, business_hours_exceeded)
            

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
