// Copyright (c) 2026, ourlib and contributors
// For license information, please see license.txt

frappe.ui.form.on('Koha Password Update', {
	refresh: function (frm) {
		console.log("Hello")

	}
});


frappe.listview_settings['Koha Password Update'] = {
	refresh: function (listview) {
		console.log("Hello")
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
						method: "custom_app.update_koha_password.add_in_queue_update_koha_pass",
						args: {
							p: data.password
						},
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




frappe.listview_settings['Koha Password Update'] = {

	onload: function (listview) {
		
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
						method: "custom_app.update_koha_password.add_in_queue_update_koha_pass",
						args: {
							p: data.password
						},
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
