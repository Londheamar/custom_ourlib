# Copyright (c) 2026, ourlib and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class KSOSupportIssue(Document):
    def before_save(self):
        """
        Triggers automatically right before the document is written to the database.
        """
        # Populate if the checklist table is currently completely empty
        if not self.get("verification_steps"):
            self.reload_checklist_data()

    def reload_checklist_data(self):
        self.set("verification_steps", [])
        append_checklist_from_template(self)


def append_checklist_from_template(doc):
    """
    Fetches matching steps from KSO SOP Template using Product & Module filters,
    falling back to a 'Universal' template if a specific one isn't found.
    Ensures all tracking metadata fields start clean/empty.
    """
    steps_to_add = []

    # 1. Fetch steps from a module-specific template if product and module match
    if doc.product and doc.module:
        specific_template = frappe.db.get_value(
            "KSO SOP Template", 
            {"product": doc.product, "module": doc.module}, 
            "name"
        )
        if specific_template:
            template_doc = frappe.get_cached_doc("KSO SOP Template", specific_template)
            for row in template_doc.verification_steps:
                if row.verification_step:
                    steps_to_add.append(row.verification_step)

    # 2. Always fetch 'Universal' fallback steps if a separate Universal template exists
    universal_template = frappe.db.get_value(
        "KSO SOP Template", 
        {"template_name": "SOP-Universal"}, 
        "name"
    )
    if universal_template:
        u_template_doc = frappe.get_cached_doc("KSO SOP Template", universal_template)
        for row in u_template_doc.verification_steps:
            if row.verification_step and row.verification_step not in steps_to_add:
                steps_to_add.append(row.verification_step)

    # 3. Append gathered steps directly to our Support Issue child table (All metadata empty)
    for step in steps_to_add:
        doc.append("verification_steps", {
            "verification_step": step,
            "completed": 0,
            "notes": None,
            "verified_by": None,
            "verification_time": None
        })


@frappe.whitelist()
def load_checklist(issue_name):
    """
    Whitelisted API fallback engine to force manual overrides/reloads via actions
    """
    doc = frappe.get_doc("KSO Support Issue", issue_name)
    doc.reload_checklist_data()
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return True