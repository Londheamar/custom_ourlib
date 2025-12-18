# Copyright (c) 2025, ourlib and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MobileApplication(Document):
    

    def before_save(self):
        js_object = f"""const dbDetails = {{
    host: "{self.hostserver}",
    user: "{self.username}",
    password: "Replace databse password here",
    database: "{self.database}",
    client: {{
        isDbAccessWritable: {self.isdbaccesswritable},
        clientConfigId: "{self.name}",
        isRenewalAllowed: {self.isrenewalallowed},
        acceptPaymentOnline: {self.acceptpaymentonline},
        payDetails: {{
            payType: "{self.paytype}",
            rzp_key_id: "{self.paytype}",
            rzp_key_secret: "{self.paytype}",
            ppl_client_id: "{self.paytype}",
            ppl_secret: "{self.paytype}"
        }},
        authType: "{self.authtype}",
        ldapDetails: {{
            server: "",
            port: "",
            tls: ""
        }}
    }}
}};
export default dbDetails;

        """
        
        self.database_configuration = js_object
        #self.save()


@frappe.whitelist(allow_guest=True)
def get_app_details(docname = ""):
    if not docname:
        return {"status":400}
    try:

        doc = frappe.get_doc("Mobile Application", docname)
        full_doc_data = doc.as_dict()
        required_fields = ["poster_links", "company_name","company_logo","library_name","welcome_text","library_slogan","library_icon_logo","library_timing","poster_links","feedback_email_id","contact_email_id","contact_number","library_address","attendance_flag","color_primary","color_primary_dark","color_accent","text_color","web_links"]

        filtered_data = {
            field: full_doc_data.get(field)
            for field in required_fields
            if full_doc_data.get(field) is not None # Optional: Exclude fields that are None
        }

        return {"status": 200, "data": filtered_data}
    except frappe.DoesNotExistError:
        return {"status": 404, "message": f"Mobile Application with name '{docname}' not found."}
    except Exception as e:
        return {"status": 500, "message": f"An unexpected error occurred: {str(e)}"}
    
