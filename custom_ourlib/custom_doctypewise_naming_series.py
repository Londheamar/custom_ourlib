import frappe

SUPPORTED_DOCTYPES = [
    "Quotation", "Sales Order", "Sales Invoice",
    "Purchase Order", "Purchase Receipt",
    "Subcontracting Order", "Subcontracting Receipt",
    "Work Order", "Job Card",
    "Payment Entry", "Delivery Note", "Packing Slip",
]


# Adds 'abbr' field to all doctypes where Company field exists
def create_abbr_fields():
    doctypes_with_company = frappe.get_all(
        "DocField",
        filters={
            "fieldname":  "company",
            "parenttype": "DocType",
            "fieldtype":  "Link",
            "options":    "Company",
        },
        fields=["parent"],
        pluck="parent",
    )

    for dt in doctypes_with_company:
        if frappe.get_value("DocType", dt, "istable"):
            continue
        if frappe.get_value("DocType", dt, "issingle"):
            continue
        
        existing_cf = frappe.db.exists("Custom Field", {"dt": dt, "fieldname": "abbr"})
        try:
            if existing_cf:
                cf = frappe.get_doc("Custom Field", existing_cf)
                cf.label = "Abbr"
                cf.fieldtype = "Read Only"
                cf.insert_after = "company"
                cf.fetch_from = "company.abbr"
                cf.hidden = 1
                cf.save(ignore_permissions=True)
            else:
                frappe.get_doc({
                    "doctype":      "Custom Field",
                    "dt":           dt,
                    "label":        "Abbr",
                    "fieldname":    "abbr",
                    "fieldtype":    "Read Only",
                    "insert_after": "company",
                    "fetch_from":   "company.abbr",
                    "hidden":       1,
                }).insert(ignore_permissions=True)
        except Exception as e:
            print(e);
        frappe.clear_cache(doctype=dt)

    frappe.db.commit()
    print("✅ Abbr fields created")

DOCTYPE_COMPANY_FIELDNAME = {
    dt: f"custom_{dt.lower().replace(' ', '_')}_series"
    for dt in SUPPORTED_DOCTYPES
}

# Adds custom fields in Company to define default naming series per doctype
def add_series_fields_to_company():

    last_field = frappe.db.get_value(
        "DocField",
        {"parent": "Company"},
        "fieldname",
        order_by="idx desc"
    )

    # Section break
    if not frappe.db.exists("Custom Field", {
        "dt":        "Company",
        "fieldname": "custom_naming_series_section",
    }):
        frappe.get_doc({
            "doctype":      "Custom Field",
            "dt":           "Company",
            "fieldname":    "custom_naming_series_section",
            "label":        "Default Naming Series",
            "fieldtype":    "Section Break",
            "insert_after": last_field,
            "collapsible":  1,
        }).insert(ignore_permissions=True)

    prev_field = "custom_naming_series_section"
    total      = len(SUPPORTED_DOCTYPES)

    # Split into 3 equal columns
    col1_end = total // 3           # end of first column
    col2_end = (total * 2) // 3     # end of second column

    col_break_1_done = frappe.db.exists("Custom Field", {
        "dt":        "Company",
        "fieldname": "custom_naming_series_col_break_1",
    })
    col_break_2_done = frappe.db.exists("Custom Field", {
        "dt":        "Company",
        "fieldname": "custom_naming_series_col_break_2",
    })

    for idx, dt in enumerate(SUPPORTED_DOCTYPES):
        fieldname = DOCTYPE_COMPANY_FIELDNAME[dt]

        # Insert first column break
        if idx == col1_end and not col_break_1_done:
            frappe.get_doc({
                "doctype":      "Custom Field",
                "dt":           "Company",
                "fieldname":    "custom_naming_series_col_break_1",
                "label":        "",
                "fieldtype":    "Column Break",
                "insert_after": prev_field,
            }).insert(ignore_permissions=True)
            prev_field       = "custom_naming_series_col_break_1"
            col_break_1_done = True

        # Insert second column break
        if idx == col2_end and not col_break_2_done:
            frappe.get_doc({
                "doctype":      "Custom Field",
                "dt":           "Company",
                "fieldname":    "custom_naming_series_col_break_2",
                "label":        "",
                "fieldtype":    "Column Break",
                "insert_after": prev_field,
            }).insert(ignore_permissions=True)
            prev_field       = "custom_naming_series_col_break_2"
            col_break_2_done = True

        if frappe.db.exists("Custom Field", {
            "dt":        "Company",
            "fieldname": fieldname,
        }):
            # Update existing — clear description
            frappe.db.set_value(
                "Custom Field",
                {"dt": "Company", "fieldname": fieldname},
                "description", ""
            )
        else:
            frappe.get_doc({
                "doctype":      "Custom Field",
                "dt":           "Company",
                "fieldname":    fieldname,
                "label":        f"{dt} Series",
                "fieldtype":    "Data",
                "insert_after": prev_field,
                "default":      "",
                "description":  "",
            }).insert(ignore_permissions=True)

        prev_field = fieldname

    frappe.db.commit()
    frappe.clear_cache(doctype="Company")
    print("✅ Company series fields done")

SCRIPT_BODY = """
frappe.ui.form.on("{{DOCTYPE}}", {
    onload(frm) {
        apply_company_naming_series(frm);
    },
    refresh(frm) {
        if (frm.is_new()) {
            apply_company_naming_series_ui(frm);
        }
    },
    company(frm) {
        apply_company_naming_series_ui(frm);
    }
});

function apply_company_naming_series_ui(frm) {
    if (!frm.doc.company || !frm.fields_dict.naming_series) return;

    let fieldname = `custom_${frm.doc.doctype.toLowerCase().replace(/ /g, "_")}_series`;
    if (!frm.fields_dict.naming_series.df.default_options) {
        frm.fields_dict.naming_series.df.default_options =
            frm.fields_dict.naming_series.df.options;
    }

    frappe.db.get_value('Company', frm.doc.company, fieldname)
    .then(r => {
        let value = r.message?.[fieldname];

        let original_options = frm.fields_dict.naming_series.df.default_options;
        let options_list = original_options.split("\\n").filter(opt => opt);

        if (value && value.trim() !== "") {

            if (!options_list.includes(value)) {
                options_list.unshift(value);
            }

            frm.set_df_property('naming_series', 'options', options_list.join("\\n"));
            frm.set_value('naming_series', value);

        } else {
            frm.set_df_property('naming_series', 'options', options_list.join("\\n"));
            frm.set_value('naming_series', options_list[0] || "");
        }
    });
}

"""

# Creates client scripts for supported doctypes to apply company-wise naming series in UI
def create_client_scripts():
    for dt in SUPPORTED_DOCTYPES:
        script_name = f"{dt} - Custom Naming Series Script"

        if frappe.db.exists("Client Script", script_name):
            doc = frappe.get_doc("Client Script", script_name)
            doc.script = SCRIPT_BODY.replace("{{DOCTYPE}}", dt)
            doc.enabled = 1
            doc.save()
        else:
            doc = frappe.get_doc({
                "doctype": "Client Script",
                "name": script_name,
                "dt": dt,
                "script": SCRIPT_BODY.replace("{{DOCTYPE}}", dt),
                "enabled": 1
            })
            doc.insert()

    frappe.db.commit()
    print("✅ Client script added for all doctypes")

# Setup method to initialize all customizations (fields + scripts)
def setup():
    print("Creating abbr fields in all doctypes")
    create_abbr_fields()
    print("Creating custom naming series fields in company doctype")
    add_series_fields_to_company()
    print("Add client script in every doctype to show default naming series in form")
    create_client_scripts()
    

# Applies company default naming series before insert; falls back to ERPNext default if not set
def apply_naming_series(doc, method):
    if not getattr(doc, "company", None):
        return

    fieldname = f"custom_{doc.doctype.lower().replace(' ', '_')}_series"
    company = frappe.get_doc("Company", doc.company)

    if not company.meta.get_field(fieldname):
        return

    series = company.get(fieldname)
    if series:
        doc.naming_series = series


'''
doc_events = {
    "*": {
        "before_insert": "custom_ourlib.custom_doctypewise_naming_series.apply_naming_series",
    }
}



'''
