# Copyright (c) 2026, ourlib and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class KSOSupportIssue(Document):
    def before_save(self):
        """
        Triggers automatically right before the document is written to the database.
        """
        # Option A: Always populate if the checklist is completely empty
        if not self.get("verification_steps"):
            self.reload_checklist_data()
            
        # Option B: (Optional) If you want to force-reload whenever they switch modules:
        if self.has_value_changed("module"):
            self.reload_checklist_data()

    def reload_checklist_data(self):
        self.set("verification_steps", [])
        append_checklist(self)


CHECKLISTS = {
    "Universal": [
        "Ticket/Issue ID created",
        "Date and time recorded",
        "Reported by user/client captured",
        "Product and module identified",
        "Exact issue documented",
        "Error screenshot attached if available",
        "Error message copied exactly",
        "Steps provided by user",
        "Impact scope identified",
        "Issue replicated or replication result documented",
        "Evidence/logs checked",
        "Root cause category selected",
        "Resolution steps documented",
        "Testing/validation completed",
        "Client confirmation captured",
    ],
    "Circulation": [
        "Same item tested with same patron",
        "Same item tested with different patron",
        "Item status verified: not withdrawn, lost, damaged, or already issued",
        "Patron active membership verified",
        "Patron category verified",
        "Outstanding fines/restrictions checked",
        "Circulation rules matrix checked",
        "Branch transfer rules checked",
        "Barcode/item record verified",
        "Fine calculation verified",
        "Issue/return/reissue workflow tested",
        "SIP/self-check behavior tested if applicable",
    ],
    "OPAC": [
        "Staff interface record checked",
        "OPAC visibility checked",
        "Suppression/hidden item settings verified",
        "Zebra or Elasticsearch service status checked",
        "Rebuild index requirement assessed",
        "Browser console checked",
        "OPAC template/customization reviewed",
        "Cache cleared and retested",
    ],
    "Search": [
        "VuFind search query replicated",
        "Solr status checked",
        "Record indexed in Solr verified",
        "Facet behavior checked",
        "Koha API/ILS driver connectivity checked",
        "Search cache cleared",
        "Index freshness verified",
        "Authentication impact checked if user-specific",
    ],
    "Reports": [
        "SQL syntax reviewed",
        "GROUP BY logic validated",
        "Date filters tested",
        "Counts manually verified",
        "Sample records validated",
        "Slow query/performance reviewed",
        "Export output tested",
    ],
    "Email": [
        "SMTP settings verified",
        "Authentication checked",
        "Email queue checked",
        "Template verified",
        "Cron job verified",
        "Delivery logs checked",
        "Spam/bounce possibility assessed",
    ],
    "Cron Jobs": [
        "Cron service status checked",
        "Koha cron configuration checked",
        "Scheduler timing verified",
        "Relevant log reviewed",
        "Manual job run tested if safe",
        "Recent OS/package change reviewed",
    ],
    "SIP2": [
        "SIP listener status checked",
        "Port/firewall checked",
        "SIP account credentials verified",
        "Branch mapping checked",
        "Item/patron test transaction performed",
        "Self-check/kiosk tested",
    ],
    "Footfall": [
        "Scanner tested",
        "Auto-enter behavior verified",
        "Counter increment verified",
        "Duplicate prevention checked",
        "Dashboard total manually verified",
    ],
}

def append_checklist(doc):
    module = doc.module or "Universal"
    steps = CHECKLISTS.get("Universal", []) + CHECKLISTS.get(module, [])
    for step in steps:
        doc.append("verification_steps", {
            "verification_step": step,
            "completed": 0
        })

# Keep this function whitelisted ONLY if you still want to allow manual overrides via API/Button
@frappe.whitelist()
def load_checklist(issue_name):
    doc = frappe.get_doc("KSO Support Issue", issue_name)
    doc.reload_checklist_data()
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return True