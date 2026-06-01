# install_all.py
# Purpose: ERPNext/Frappe v14 deployment script for Koha + VuFind Support Operations.
# Usage:
#   bench --site <site-name> execute koha_support_ops.install_all.run_all

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CREATE_DEMO_DATA = False

ROLES = [
    "Support Agent",
    "Support Engineer",
    "Senior Engineer",
    "Infra Administrator",
    "Reporting Specialist",
    "QA Engineer",
    "Support Manager",
    "Client Viewer",
    "Discovery Team",
]

SELECTS = {
    "product": "\nKoha\nVuFind\nKoha + VuFind\nSIP\nSMTP\nSolr\nElasticsearch\nZebra\nApache/Nginx\nDatabase\nServer/Infrastructure",
    "module": "\nCirculation\nCataloguing\nAcquisitions\nSerials\nReports\nOPAC\nPatron Management\nSIP2\nNotices\nCron Jobs\nAuthorities\nMARC Framework\nOffline Circulation\nSearch\nSolr Index\nAuthentication\nFacets\nOPAC Integration\nDiscovery UI\nUser Accounts\nAPI Integration\nFootfall\nEmail\nLogin/Permissions\nData/Items\nOther",
    "environment": "\nProduction\nStaging\nUAT\nDevelopment",
    "severity": "\nSev-1 Critical\nSev-2 High\nSev-3 Medium\nSev-4 Low",
    "priority": "\nUrgent\nHigh\nMedium\nLow",
    "support_status": "\nNew\nTriage\nInvestigation\nPending Client\nPending Vendor\nFix In Progress\nTesting\nMonitoring\nResolved\nClosed\nReopened",
    "impact_scope": "\nSingle User\nMultiple Users\nDepartment\nBranch\nInstitution\nMulti-Tenant\nEntire System",
    "root_cause_category": "\nConfiguration Issue\nPermission Issue\nData Issue\nData Corruption\nSQL/Report Defect\nZebra Index Failure\nElasticsearch Failure\nSolr Failure\nCron Failure\nSMTP Failure\nSIP Connectivity\nCustomization Defect\nUpgrade Regression\nServer Resource Issue\nDatabase Issue\nNetwork Issue\nUnknown/Pending",
    "resolution_type": "\nConfiguration Update\nData Correction\nSQL Fix\nReindex\nRestart Service\nPatch Applied\nPermission Update\nCache Clear\nCustom Code Fix\nRollback\nWorkaround\nMonitoring Only",
    "risk_level": "\nLow\nMedium\nHigh\nCritical",
}

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


def run_all():
    frappe.only_for("System Manager")
    create_roles()
    create_doctypes()
    create_workflow()
    create_client_script()
    create_notifications()
    create_sop_templates()
    if CREATE_DEMO_DATA:
        create_demo_data()
    frappe.db.commit()
    print("Koha + VuFind Support Operations package installed successfully.")


def create_roles():
    for role in ROLES:
        if not frappe.db.exists("Role", role):
            doc = frappe.new_doc("Role")
            doc.role_name = role
            doc.desk_access = 1
            doc.insert(ignore_permissions=True)


def make_field(fieldname, label, fieldtype, **kwargs):
    d = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype}
    d.update(kwargs)
    return d


def ensure_doctype(name, module, fields, istable=0, autoname=None, title_field=None):
    if frappe.db.exists("DocType", name):
        return
    doc = frappe.new_doc("DocType")
    doc.name = name
    doc.module = module
    doc.custom = 0
    doc.istable = istable
    if autoname:
        doc.autoname = autoname
    if title_field:
        doc.title_field = title_field
    for i, f in enumerate(fields, start=1):
        row = doc.append("fields", {})
        row.idx = i
        for k, v in f.items():
            setattr(row, k, v)
    if not istable:
        add_permissions(doc)
    doc.insert(ignore_permissions=True)


def add_permissions(doc):
    perm_map = [
        ("System Manager", 0, 1, 1, 1, 1, 0, 0),
        ("Support Manager", 0, 1, 1, 1, 1, 0, 0),
        ("Senior Engineer", 0, 1, 1, 1, 1, 0, 0),
        ("Support Engineer", 0, 1, 1, 1, 0, 0, 0),
        ("Support Agent", 0, 1, 1, 1, 0, 0, 0),
        ("QA Engineer", 0, 1, 1, 0, 0, 0, 0),
        ("Infra Administrator", 0, 1, 1, 0, 0, 0, 0),
        ("Reporting Specialist", 0, 1, 1, 0, 0, 0, 0),
        ("Client Viewer", 0, 1, 0, 0, 0, 0, 0),
    ]

    for role, level, read, write, create, delete, submit, cancel in perm_map:
        p = doc.append("permissions", {})
        p.role = role
        p.permlevel = level
        p.read = read
        p.write = write
        p.create = create
        p.delete = delete
        p.submit = submit
        p.cancel = cancel


def create_doctypes():
    module = "Koha Support Ops"
    ensure_module(module)

    ensure_doctype("KSO Verification Step", module, [
        make_field("verification_step", "Verification Step", "Data", reqd=1, in_list_view=1),
        make_field("completed", "Completed", "Check", in_list_view=1),
        make_field("notes", "Notes", "Small Text"),
        make_field("verified_by", "Verified By", "Link", options="User"),
        make_field("verification_time", "Verification Time", "Datetime"),
    ], istable=1)

    ensure_doctype("KSO Evidence", module, [
        make_field("evidence_type", "Evidence Type", "Select", options="\nScreenshot\nError Message\nApplication Log\nSQL Error\nBrowser Console\nCron Log\nEmail Log\nService Status\nOther", in_list_view=1),
        make_field("description", "Description", "Small Text", in_list_view=1),
        make_field("attachment", "Attachment", "Attach"),
        make_field("log_snippet", "Log Snippet", "Code"),
        make_field("collected_by", "Collected By", "Link", options="User"),
    ], istable=1)

    ensure_doctype("KSO RCA Entry", module, [
        make_field("rca_type", "RCA Type", "Select", options=SELECTS["root_cause_category"], in_list_view=1),
        make_field("description", "Description", "Small Text", in_list_view=1),
        make_field("confirmed", "Confirmed", "Check", in_list_view=1),
        make_field("identified_by", "Identified By", "Link", options="User"),
    ], istable=1)

    ensure_doctype("KSO Resolution Action", module, [
        make_field("action_type", "Action Type", "Select", options=SELECTS["resolution_type"], in_list_view=1),
        make_field("description", "Description", "Small Text", in_list_view=1),
        make_field("risk_level", "Risk Level", "Select", options=SELECTS["risk_level"], in_list_view=1),
        make_field("backup_taken", "Backup Taken", "Check"),
        make_field("executed_by", "Executed By", "Link", options="User"),
    ], istable=1)

    ensure_doctype("KSO Testing Result", module, [
        make_field("test_scenario", "Test Scenario", "Data", reqd=1, in_list_view=1),
        make_field("result", "Result", "Select", options="\nPass\nFail\nPartial\nNot Applicable", in_list_view=1),
        make_field("notes", "Notes", "Small Text"),
        make_field("tested_by", "Tested By", "Link", options="User"),
    ], istable=1)

    ensure_doctype("KSO SOP Template", module, [
        make_field("template_name", "Template Name", "Data", reqd=1, unique=1, in_list_view=1),
        make_field("product", "Product", "Select", options=SELECTS["product"], in_list_view=1),
        make_field("module", "Module", "Select", options=SELECTS["module"], in_list_view=1),
        make_field("description", "Description", "Small Text"),
        make_field("steps_section", "Checklist Steps", "Section Break"),
        make_field("verification_steps", "Verification Steps", "Table", options="KSO Verification Step"),
    ], autoname="field:template_name", title_field="template_name")

    ensure_doctype("KSO Knowledge Base Article", module, [
        make_field("title", "Title", "Data", reqd=1, in_list_view=1),
        make_field("category", "Category", "Select", options="\nCirculation\nOPAC/Search\nSIP2\nSMTP\nSolr\nZebra\nElasticsearch\nSQL Reports\nPatron Issues\nAuthentication\nFootfall\nInfrastructure", in_list_view=1),
        make_field("symptoms", "Symptoms", "Text"),
        make_field("resolution", "Resolution", "Text Editor"),
        make_field("related_rca", "Related RCA", "Select", options=SELECTS["root_cause_category"]),
        make_field("related_module", "Related Module", "Select", options=SELECTS["module"]),
    ], autoname="field:title", title_field="title")

    ensure_doctype("KSO Support Issue", module, [
        make_field("subject", "Subject", "Data", reqd=1, in_list_view=1),
        make_field("client_section", "Client / Site", "Section Break"),
        make_field("client", "Client", "Link", options="Customer", in_list_view=1),
        make_field("site_name", "Site Name", "Data"),
        make_field("reported_by", "Reported By", "Data"),
        make_field("contact_email", "Contact Email", "Data"),
        make_field("classification_section", "Classification", "Section Break"),
        make_field("product", "Product", "Select", options=SELECTS["product"], reqd=1, in_list_view=1),
        make_field("module", "Module", "Select", options=SELECTS["module"], reqd=1, in_list_view=1),
        make_field("environment", "Environment", "Select", options=SELECTS["environment"], default="Production"),
        make_field("severity", "Severity", "Select", options=SELECTS["severity"], reqd=1, in_list_view=1),
        make_field("priority", "Priority", "Select", options=SELECTS["priority"], default="Medium"),
        make_field("support_status", "Support Status", "Select", options=SELECTS["support_status"], default="New", in_list_view=1),
        make_field("impact_scope", "Impact Scope", "Select", options=SELECTS["impact_scope"]),
        make_field("assignment_section", "Assignment", "Section Break"),
        make_field("assigned_team", "Assigned Team", "Data"),
        make_field("assigned_engineer", "Assigned Engineer", "Link", options="User"),
        make_field("description_section", "Issue Description", "Section Break"),
        make_field("detailed_description", "Detailed Description", "Text Editor"),
        make_field("exact_error_message", "Exact Error Message", "Code"),
        make_field("steps_to_reproduce", "Steps To Reproduce", "Text"),
        make_field("browser_details", "Browser Details", "Data"),
        make_field("version_details", "Version Details", "Data"),
        make_field("verification_section", "Verification", "Section Break"),
        make_field("verification_steps", "Verification Steps", "Table", options="KSO Verification Step"),
        make_field("evidence", "Evidence", "Table", options="KSO Evidence"),
        make_field("rca_section", "Root Cause Analysis", "Section Break"),
        make_field("root_cause_category", "Root Cause Category", "Select", options=SELECTS["root_cause_category"]),
        make_field("rca_entries", "RCA Entries", "Table", options="KSO RCA Entry"),
        make_field("resolution_section", "Resolution", "Section Break"),
        make_field("resolution_type", "Resolution Type", "Select", options=SELECTS["resolution_type"]),
        make_field("resolution_actions", "Resolution Actions", "Table", options="KSO Resolution Action"),
        make_field("permanent_fix_applied", "Permanent Fix Applied", "Check"),
        make_field("preventive_action_required", "Preventive Action Required", "Check"),
        make_field("resolution_summary", "Resolution Summary", "Text Editor"),
        make_field("testing_section", "Testing & Closure", "Section Break"),
        make_field("testing_results", "Testing Results", "Table", options="KSO Testing Result"),
        make_field("client_confirmation", "Client Confirmation", "Check"),
        make_field("escalation_section", "SLA / Escalation", "Section Break"),
        make_field("escalated", "Escalated", "Check"),
        make_field("escalation_level", "Escalation Level", "Int", default="0"),
        make_field("sla_due", "SLA Due", "Datetime"),
        make_field("first_response_time", "First Response Time", "Datetime"),
        make_field("resolved_on", "Resolved On", "Datetime"),
    ], autoname="SUP-.YYYY.-.#####", title_field="subject")


def ensure_module(module):
    if not frappe.db.exists("Module Def", module):
        m = frappe.new_doc("Module Def")
        m.module_name = module
        m.custom = 1
        m.insert(ignore_permissions=True)


def ensure_workflow_state(state_name, style="Primary"):
    if not frappe.db.exists("Workflow State", state_name):
        doc = frappe.get_doc({
            "doctype": "Workflow State",
            "workflow_state_name": state_name,
            "style": style
        })
        doc.insert(ignore_permissions=True)
def ensure_workflow_action(action_name):
    if not frappe.db.exists("Workflow Action Master", action_name):
        doc = frappe.get_doc({
            "doctype": "Workflow Action Master",
            "workflow_action_name": action_name
        })
        doc.insert(ignore_permissions=True)

def create_workflow():
    if frappe.db.exists("Workflow", "WF-SUPPORT-V1"):
        return
    wf = frappe.new_doc("Workflow")
    wf.workflow_name = "WF-SUPPORT-V1"
    wf.document_type = "KSO Support Issue"
    wf.workflow_state_field = "support_status"
    wf.is_active = 1
    wf.send_email_alert = 0

    states = [
        ("New", 0), ("Triage", 0), ("Investigation", 0), ("Pending Client", 0),
        ("Pending Vendor", 0), ("Fix In Progress", 0), ("Testing", 0),
        ("Monitoring", 0), ("Resolved", 1), ("Closed", 1), ("Reopened", 0)
    ]

    transitions = [
        ("New", "Triage", "Start Triage", "Support Agent"),
        ("Triage", "Investigation", "Investigate", "Support Engineer"),
        ("Investigation", "Pending Client", "Request Client Info", "Support Engineer"),
        ("Investigation", "Pending Vendor", "Send to Vendor", "Support Engineer"),
        ("Investigation", "Fix In Progress", "Start Fix", "Support Engineer"),
        ("Pending Client", "Investigation", "Resume Investigation", "Support Engineer"),
        ("Pending Vendor", "Investigation", "Vendor Response Received", "Support Engineer"),
        ("Fix In Progress", "Testing", "Send to Testing", "Senior Engineer"),
        ("Testing", "Fix In Progress", "Testing Failed", "QA Engineer"),
        ("Testing", "Monitoring", "Start Monitoring", "QA Engineer"),
        ("Monitoring", "Resolved", "Resolve", "Support Manager"),
        ("Resolved", "Closed", "Close", "Support Manager"),
        ("Closed", "Reopened", "Reopen", "Support Manager"),
        ("Resolved", "Reopened", "Reopen", "Support Manager"),
        ("Reopened", "Investigation", "Investigate Reopened", "Support Engineer"),
    ]

    for state, _ in states:
        ensure_workflow_state(state)
    
    unique_actions = set([t[2] for t in transitions])

    for action in unique_actions:
        ensure_workflow_action(action)

    for state, doc_status in states:
        row = wf.append("states", {})
        row.state = state
        row.doc_status = doc_status
        row.allow_edit = "Support Manager" if state in ["Resolved", "Closed"] else "Support Engineer"


    for from_state, to_state, action, role in transitions:
        row = wf.append("transitions", {})
        row.state = from_state
        row.action = action
        row.next_state = to_state
        row.allowed = role
    wf.insert(ignore_permissions=True)


def create_client_script():
    name = "KSO Support Issue Client Logic"
    if frappe.db.exists("Client Script", name):
        return
    script = frappe.new_doc("Client Script")
    script.name = name
    script.dt = "KSO Support Issue"
    script.enabled = 1
    script.script = """
frappe.ui.form.on('KSO Support Issue', {
    refresh: function(frm) {
        if (frm.doc.severity === 'Sev-1 Critical') {
            frm.dashboard.set_headline_alert('Critical issue: immediate triage and escalation required.', 'red');
        }
        
        if (!frm.is_new()) {
            frm.add_custom_button(__('Reload Checklist'), function() {
                frappe.call({
                    method: 'custom_ourlib.koha_support_ops.doctype.kso_support_issue.kso_support_issue.load_checklist', // Double check this path matches your app structure
                    args: { issue_name: frm.doc.name },
                    callback: function(r) {
                        if(!r.exc) {
                            frm.reload_doc();
                            frappe.show_alert({message: __('Checklist reloaded successfully'), indicator: 'green'});
                        }
                    }
                });
            });
        }
    },
    severity: function(frm) {
        frm.set_df_property('impact_scope', 'reqd', frm.doc.severity === 'Sev-1 Critical');
        frm.set_df_property('exact_error_message', 'reqd', ['Sev-1 Critical','Sev-2 High'].includes(frm.doc.severity));
    },
    product: function(frm) {
        if (frm.doc.product === 'VuFind') {
            frappe.show_alert('VuFind issue: remember to check Solr, VuFind logs, and Koha ILS driver connectivity.');
        }
        if (frm.doc.product === 'Koha') {
            frappe.show_alert('Koha issue: remember to check Plack, Zebra/ES, cron jobs, and Koha logs.');
        }
    }
});
"""
    script.insert(ignore_permissions=True)


def create_notifications():
    # Minimal placeholder notifications. Teams should adjust recipients and channels.
    if not frappe.db.exists("Notification", "KSO Sev-1 Alert"):
        n = frappe.new_doc("Notification")
        n.name = "KSO Sev-1 Alert"
        n.subject = "Critical Support Issue: {{ doc.name }}"
        n.document_type = "KSO Support Issue"
        n.event = "New"
        n.enabled = 1
        n.condition = "doc.severity == 'Sev-1 Critical'"
        n.message = """<p>Critical support issue created.</p>
<p><b>Ticket:</b> {{ doc.name }}</p>
<p><b>Subject:</b> {{ doc.subject }}</p>
<p><b>Client:</b> {{ doc.client }}</p>
<p><b>Product:</b> {{ doc.product }}</p>
<p><b>Module:</b> {{ doc.module }}</p>"""
        n.insert(ignore_permissions=True)


def create_sop_templates():
    for template, steps in CHECKLISTS.items():
        name = f"SOP-{template}"
        if frappe.db.exists("KSO SOP Template", name):
            continue
        doc = frappe.new_doc("KSO SOP Template")
        doc.template_name = name
        doc.product = "Koha + VuFind" if template == "Universal" else ("VuFind" if template == "Search" else "Koha")
        doc.module = template if template in SELECTS["module"] else "Other"
        doc.description = f"Standard troubleshooting checklist for {template} issues."
        for step in steps:
            doc.append("verification_steps", {"verification_step": step})
        doc.insert(ignore_permissions=True)


def create_demo_data():
    samples = [
        {
            "subject": "Koha circulation issue: item not issuing to active patron",
            "client": None,
            "site_name": "Demo University Library",
            "product": "Koha",
            "module": "Circulation",
            "severity": "Sev-2 High",
            "priority": "High",
            "impact_scope": "Branch",
            "detailed_description": "Staff reports that active patron cannot issue a specific barcode.",
            "exact_error_message": "Issuing rules do not allow this item type for this patron category.",
        },
        {
            "subject": "VuFind search results missing newly catalogued records",
            "site_name": "Central Discovery Portal",
            "product": "VuFind",
            "module": "Search",
            "severity": "Sev-2 High",
            "priority": "High",
            "impact_scope": "Institution",
            "detailed_description": "Records visible in Koha staff interface but not visible in VuFind discovery.",
            "exact_error_message": "No explicit user-facing error. Solr index suspected stale.",
        },
        {
            "subject": "Email notices not being delivered",
            "site_name": "Demo College Library",
            "product": "SMTP",
            "module": "Email",
            "severity": "Sev-3 Medium",
            "priority": "Medium",
            "impact_scope": "Institution",
            "detailed_description": "Overdue and due date notices are not reaching patrons.",
            "exact_error_message": "SMTP authentication failed in mail log.",
        },
    ]
    for sample in samples:
        if frappe.db.exists("KSO Support Issue", {"subject": sample["subject"]}):
            continue
        doc = frappe.new_doc("KSO Support Issue")
        doc.update(sample)
        doc.environment = "Production"
        doc.support_status = "New"
        doc.reported_by = "Demo Reporter"
        doc.contact_email = "demo@example.com"
        append_checklist(doc)
        doc.insert(ignore_permissions=True)


def append_checklist(doc):
    module = doc.module or "Universal"
    steps = CHECKLISTS.get("Universal", []) + CHECKLISTS.get(module, [])
    for step in steps:
        doc.append("verification_steps", {"verification_step": step})


@frappe.whitelist()
def load_checklist(issue_name):
    doc = frappe.get_doc("KSO Support Issue", issue_name)
    doc.set("verification_steps", [])
    append_checklist(doc)
    doc.save(ignore_permissions=True)
    return True
