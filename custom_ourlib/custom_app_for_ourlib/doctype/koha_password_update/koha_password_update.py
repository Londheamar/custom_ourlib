# Copyright (c) 2026, ourlib and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe.integrations.utils import make_get_request
from frappe.integrations.utils import make_post_request


class KohaPasswordUpdate(Document):
	pass


@frappe.whitelist(allow_guest=True)
def update_pass(password):
    #password = frappe.form_dict.get("password")
    password = password
    if not password:
        frappe.throw("Missing parameter: password")

    rows = frappe.db.get_all(
        "Customer",
        filters={
            "custom_type_of_installation": "Ourlib Cloud",
            "disabled": 0
        },
        fields=["name", "custom_staff_url", "email_id"]
    )

    username = "admin"

    errors = []
    success = []

    prefix = "Admin@"
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    h = frappe.utils.generate_hash()

    password_to_update = prefix + h[:4]

    unique = {}
    for r in rows:
        url = r.custom_staff_url

        if not url:
            errors.append({
                "customer": r.name,
                "url": url,
                "error": "URL not found!"
            })
            continue

        # normalize URL
        if url.endswith("/"):
            url = url[:-1]

        # keep only unique URLs
        if url not in unique:
            unique[url] = r

    unique_list = list(unique.values())

    docs = frappe.get_all("Koha Password Update Log", fields=["name"])
    for d in docs:
        frappe.delete_doc("Koha Password Update Log", d.name, force=True)

    frappe.db.commit()
    frappe.get_doc({"doctype": "Koha Password Update Log","customer": "Total Count","url":len(unique_list)}).insert(ignore_permissions=True)


    for c in unique_list:
        patron_id = None

        if not c.custom_staff_url:
            continue

        base_url = c.custom_staff_url
        if base_url and base_url.endswith("/"):
            base_url = base_url[:-1]

        lskd = frappe.get_doc({"doctype": "Koha Password Update Log","customer": c.name,"url": base_url, "status": "In Process", "error": "","password": password_to_update,}).insert(ignore_permissions=True)
        frappe.db.commit()
        try:
            getP_ID = make_get_request(base_url + "/api/v1/patrons?cardnumber=ourlib", auth=(username, password))

            # If response is a list: [ { patron_id: 123 } ]
            if isinstance(getP_ID, list) and len(getP_ID) > 0:
                patron_id = getP_ID[0].get("patron_id")
            # If response is an object: { patron_id: 123 }
            elif isinstance(getP_ID, dict):
                patron_id = getP_ID.get("patron_id")

            if patron_id:

                postR = make_post_request(f"{base_url}/api/v1/patrons/{patron_id}/password", json={"password": password_to_update, "password_2":password_to_update}, auth=(username, password))

                success.append({ "url" : base_url, "password": password_to_update })
                lskd.status = "Success"
                lskd.save(ignore_permissions=True)
                frappe.db.commit()

        except Exception as e:
            msg = {"error": str(e)}
            if hasattr(e, "response") and e.response:

                # check if it's an HTTPError (requests)
                msg["status_code"] = e.response.status_code
                msg["reason"] = e.response.reason
                msg["response_text"] = e.response.text  # RAW ERROR MESSAGE FROM KOHA

            errors.append({
                "customer": c.name,
                "url": base_url,
                "error": msg,
                "pass": password_to_update
            })

            lskd.status = "Failed"
            lskd.error = e
            lskd.save(ignore_permissions=True)
            frappe.db.commit()

    msg = "<h4>Dear All,</h4>"
    msg = msg + "<p>We have updated our admin password for all Koha instances.</p>"
    msg = msg + f"<p><b>Updated password:</b> {password_to_update}</p><br>"
    if errors:
        msg = msg + "<h4>However, some Koha instances could NOT be updated:</h4>"
        msg = msg +  """
        <table border="1" cellpadding="6" cellspacing="0">
            <tr>
                <th>Customer</th>
                <th>URL</th>
                <th>Error</th>
            </tr>
        """

        for item in errors:
            msg = msg + f"""
            <tr>
                <td>{item['customer']}</td>
                <td>{item['url']}</td>
                <td>{item['error']}</td>
            </tr>
            """

        msg = msg + "</table>"

    frappe.sendmail(
        recipients=["amar@ourlib.in", "ashish@ourlib.in"],
        subject="[UPDATE] - Admin password updated for all koha`s",
        reference_name= "KOHA_PASS_UPDATE",
        message=msg
    )
    frappe.db.commit()

@frappe.whitelist()
def add_in_queue_update_koha_pass(p):
# Run long task in background
    frappe.enqueue(
        "custom_ourlib.custom_app_for_ourlib.doctype.koha_password_update.koha_password_update.update_pass",
        queue="long",
        job_name="change_koha_admin_passwords_cron",
        password= p,
        timeout=3600
    )
    return "Queued"
