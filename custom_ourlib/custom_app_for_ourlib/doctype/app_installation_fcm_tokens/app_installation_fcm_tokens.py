# Copyright (c) 2025, ourlib and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.data import now_datetime
from frappe.exceptions import DoesNotExistError, ValidationError
import json

class AppInstallationFcmTokens(Document):
	pass


@frappe.whitelist(allow_guest=True)
def is_uuid_exist(uuid=""):
    # 1. Input Validation
    if not uuid:
        return {"status": 400, "message": "Missing required argument: uuid"}

    try:
        doc = frappe.get_list(
            "App Installation Fcm Tokens",
            filters={"uid": uuid},
            fields=["name", "uid"]
        )

        if doc:
            return {
                "status": 200,
                "isExists": True,
                "data": doc[0],
                "message": "UUID found."
            }
        else:
            return {
                "status": 404,
                "isExists": False,
                "message": f"App installation not found for UUID: {uuid}."
            }

    except Exception as e:
        frappe.log_error(title="API Error in is_uuid_exist", message=str(e))
        return {"status": 500, "message": f"An unexpected error occurred: {str(e)}"}




#@frappe.whitelist(allow_guest=True)
#def insert_new_id(uid, customer, fcmtoken, useripaddress, androidversion, cardnumber_username, isuserloggedin, action="create"):
@frappe.whitelist(allow_guest=True)
def insert_new_id(**kwargs):
    """
    Handles creation (create) or update (update) of AppInstallationFcmTokens records.

    :param uid: Unique ID for the installation. (Required for both)
    :param customer: Related mobile application customer. (Required for create)
    :param fcmtoken: Firebase Cloud Messaging Token. (Required for both)
    :param useripaddress: IP address of the device.
    :param androidversion: Android OS version of the device.
    :param action: "create" to insert a new record, "update" to update an existing one.
    """
    doctype_name = "App Installation Fcm Tokens"
    data_dict = json.loads(kwargs.get('data'))
    uid = data_dict.get("uid")
    customer = data_dict.get("customer", "")
    fcmtoken = data_dict.get("fcmtoken")
    useripaddress = data_dict.get("useripaddress", "")
    androidversion = data_dict.get("androidversion", "")
    cardnumber_username = data_dict.get("cardnumber_username", "")
    isuserloggedin = data_dict.get("isuserloggedin", False)
    action = data_dict.get("action", "create")

    # --- 1. Basic Validation ---
    if not uid:
        return {"status": 400, "message": "Missing required argument: uid (Unique ID)"}

    # --- 2. Action: Create New Record ---
    if action == "create":
        if not customer:
            return {"status": 400, "message": "Missing required argument: customer for 'create' action."}

        # Check if uid already exists to prevent duplicates
        if frappe.db.exists(doctype_name, {"uid": uid}):
             return {"status": 409, "message": f"Record with UID '{uid}' already exists. Use 'update' action instead."}

        try:
            new_doc = frappe.get_doc({
                "doctype": doctype_name,
                "uid": uid,
                "mobile_application": customer,
                "fcmtoken": fcmtoken,
                "useripaddress": useripaddress,
                "androidversion": androidversion,
                "last_updated_at": now_datetime()
            })

            new_doc.insert(ignore_permissions=False) # Respect permissions
            # Calling .save() after .insert() is redundant for a new doc
            frappe.db.commit() # Commit changes to the database

            return {"status": 200, "message": "Record created successfully", "name": new_doc.name}

        except Exception as e:
            frappe.log_error(title=f"API Create Error in {doctype_name}", message=str(e))
            # Return a user-friendly error message, e.g., permission failure
            return {"status": 500, "message": f"Failed to create record. Possible permission issue or invalid data: {str(e)}"}

    # --- 3. Action: Update Existing Record ---
    elif action == "update":
        try:
            # Fetch the document name (primary key) using the unique 'uid'
            doc_name = frappe.db.get_value(doctype_name, {"uid": uid}, "name")

            if not doc_name:
                raise DoesNotExistError(f"No record found with UID: {uid}")

            # Get the document object and update fields
            doc = frappe.get_doc(doctype_name, doc_name)
            if fcmtoken:
                doc.fcmtoken = fcmtoken
            if useripaddress:
                doc.useripaddress = useripaddress
            if androidversion:
                doc.androidversion = androidversion
            if cardnumber_username:
                doc.cardnumber_username = cardnumber_username
            if isuserloggedin:
                doc.isuserloggedin = isuserloggedin
            doc.last_updated_at = now_datetime()

            doc.save(ignore_permissions=False) # Respect permissions
            frappe.db.commit()

            return {"status": 200, "message": "Record updated successfully", "name": doc.name}

        except DoesNotExistError as e:
            return {"status": 404, "message": str(e)}

        except Exception as e:
            frappe.log_error(title=f"API Update Error in {doctype_name}", message=str(e))
            return {"status": 500, "message": f"Failed to update record: {str(e)}"}

    # --- 4. Invalid Action ---
    else:
        return {"status": 400, "message": f"Invalid action: '{action}'. Must be 'create' or 'update'"}
    

