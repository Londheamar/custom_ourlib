frappe.listview_settings['Koha Password Update'] = {
    refresh: function (listview) {
        console.log("Koha Password Update list loaded");

        listview.page.add_inner_button("Update Koha Admin Pass", function () {
            frappe.prompt(
                [
                    {
                        fieldname: 'password',
                        label: 'Enter current koha admin password',
                        fieldtype: 'Data',
                        reqd: 1
                    }
                ],
                function (data) {
                    frappe.call({
                        method: "custom_ourlib.custom_app_for_ourlib.doctype.koha_password_update.koha_password_update.add_in_queue_update_koha_pass",
                        args: { p: data.password },
                        freeze: true,
                        freeze_message: "Queuing password update...",
                        callback: function (r) {
                            if (!r.exc) {
                                frappe.msgprint("Task added to background queue successfully.");
                            }
                        }
                    });
                },
                "Update Koha Admin Password",
                "Submit"
            );
        });
    }
};

