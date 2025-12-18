// Copyright (c) 2025, ourlib and contributors
// For license information, please see license.txt

frappe.ui.form.on('CSV To MRC', {
    refresh: function(frm) {
        
        frm.add_custom_button(__('Validate CSV file'), function() {
            // Trigger the API when the button is clicked
            frappe.call({
                method: 'custom_ourlib.custom_app_for_ourlib.doctype.csv_to_mrc.csv_to_mrc.validate_csv',  // Path to your Server Script (API) here
                args: {
                    docname: frm.doc.name  // Pass the record name to the API
                },
                freeze: true,
                freeze_message: __("Magically validating CSV... Please wait, our gnomes are working hard."),
                callback: function(response) {
                    if (response.message) {
                        frappe.msgprint(response.message);
                    }
                }
            });
        });

        // Add a custom button for converting CSV to MRC
        frm.add_custom_button(__('Convert CSV to MRC'), function() {
            // Trigger the API when the button is clicked
            frappe.call({
                method: 'custom_ourlib.custom_app_for_ourlib.doctype.csv_to_mrc.csv_to_mrc.convert_csv_to_mrc',  // Path to your Server Script (API) here
                args: {
                    docname: frm.doc.name  // Pass the record name to the API
                },
                freeze: true,
                freeze_message: __("Magically turning CSV into MRC... Please wait, our gnomes are working hard."),
                callback: function(response) {
                    if (response.message) {
                        frappe.msgprint(response.message);
                    }
                }
            });
        });

    }
});

