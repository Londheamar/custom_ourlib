# uninstall.py
# Purpose: ERPNext/Frappe v14 teardown script for Koha + VuFind Support Operations.
# Usage:
#    bench --site <site-name> execute koha_support_ops.uninstall.run_all

import frappe

DOCTYPES = [
    "KSO Support Issue",
    "KSO Knowledge Base Article",
    "KSO SOP Template",
    "KSO Testing Result",
    "KSO Resolution Action",
    "KSO RCA Entry",
    "KSO Evidence",
    "KSO Verification Step",
]


def run_all():
    frappe.only_for("System Manager")

    print("Starting teardown of Koha + VuFind Support Operations...")

    # 1. Remove Generated/Demo Data first (Prevents foreign key issues or dangling links)
    delete_demo_and_generated_data()

    # 2. Delete Workflows & Metadata configurations
    delete_workflow()
    delete_client_script()
    delete_notifications()

    # 3. Drop Custom DocTypes completely
    delete_doctypes()

    frappe.db.commit()
    print("Koha + VuFind Support Operations package uninstalled successfully.")


def delete_demo_and_generated_data():
    print("--> Deleting issue records, articles, and templates...")
    # Clean up parent documents (Child tables drop automatically with parents or doctype deletion)
    frappe.db.delete("KSO Support Issue")
    frappe.db.delete("KSO Knowledge Base Article")
    frappe.db.delete("KSO SOP Template")


def delete_workflow():
    workflow_name = "WF-SUPPORT-V1"
    if frappe.db.exists("Workflow", workflow_name):
        print(f"--> Removing Workflow: {workflow_name}")
        frappe.delete_doc("Workflow", workflow_name, ignore_permissions=True)

    # Note: Global Workflow States/Actions are intentionally left alone as they might 
    # be shared across other app workflows, but you can target custom transitions safely.


def delete_client_script():
    script_name = "KSO Support Issue Client Logic"
    if frappe.db.exists("Client Script", script_name):
        print(f"--> Removing Client Script: {script_name}")
        frappe.delete_doc("Client Script", script_name, ignore_permissions=True)


def delete_notifications():
    notification_name = "KSO Sev-1 Alert"
    if frappe.db.exists("Notification", notification_name):
        print(f"--> Removing Notification: {notification_name}")
        frappe.delete_doc(
            "Notification", notification_name, ignore_permissions=True
        )


def delete_doctypes():
    print("--> Dropping Custom DocTypes and clearing database tables...")
    for dt in DOCTYPES:
        if frappe.db.exists("DocType", dt):
            # Using delete_doc drops the physical SQL table and clears standard metadata link elements
            frappe.delete_doc("DocType", dt, ignore_permissions=True)


def delete_module(module_name):
    if frappe.db.exists("Module Def", module_name):
        print(f"--> Removing Module Definition: {module_name}")
        frappe.delete_doc("Module Def", module_name, ignore_permissions=True)