# Copyright (c) 2025, ourlib and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
import os
import shutil
import json
import datetime
from datetime import datetime as dt
import subprocess
from frappe.utils import get_bench_path, get_site_path
import csv
import re
import time

class CSVToMRC(Document):
	pass


def validate_date_format(date_str, date_format):
    """
    Validate if the given date string matches the specified date format.
    """
    try:
        # Replace "yyyy" with "%Y" (for year), "mm" with "%m" (for month), "dd" with "%d" (for day)
        date_format = date_format.replace("yyyy", "%Y").replace("mm", "%m").replace("dd", "%d")
        dt.strptime(date_str, date_format)  # Try to parse the date string
    except ValueError:
        raise ValueError(f"Date '{date_str}' does not match the expected format '{date_format}'")


@frappe.whitelist()
def validate_csv(docname):
    start_time = time.time()
    base_path = get_bench_path()
    site_name = frappe.local.site

    doc = frappe.get_doc('CSV To MRC', docname)

    csv_file_path = f"{base_path}/sites/{site_name}" + doc.file  # Path to CSV file
    #basefile_name = os.path.splitext(os.path.basename(doc.file))[0]

    validation_rules = json.loads(doc.validation_rules) if isinstance(doc.validation_rules, str) else doc.validation_rules

    # validate csv file as per validation rules

    date_format = validation_rules.get("date_format", "yyyy-mm-dd")
    date_fields = validation_rules.get("date_fields", [])
    required_columns = validation_rules.get("required_columns", [])
    delimiter = validation_rules.get("delimeter", '\t')
    junk_chars = validation_rules.get("junk_chars", "")

    validation_errors = []  # Initialize an array to store errors
    max_errors = 20

    # Open and read the CSV file
    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=delimiter)
            header = next(reader)  # First row is the header
            rows = list(reader)  # Remaining rows are the data rows
            

            # Check if required columns are in the header
            missing_columns = [col for col in required_columns if col not in header]
            if missing_columns:
                validation_errors.append(f"Missing required columns: {', '.join(missing_columns)}")

            # Validate the date fields
            for date_field in date_fields:
                field_index = header.index(date_field) if date_field in header else None
                if field_index is None:
                    validation_errors.append(f"Date field '{date_field}' not found in the header.")
                
                for row in rows:
                    try:
                        if len(validation_errors) >= max_errors:
                            break

                        value = row[field_index]
                        # Validate date format
                        validate_date_format(value, date_format)
                    except Exception as e:
                        validation_errors.append(f"Invalid date format in field '{date_field}' at row {rows.index(row) + 2}: {e}")
                
                if len(validation_errors) >= max_errors:
                    break

            # Validate junk characters
            if len(validation_errors) < max_errors and junk_chars == "new_line":
                for row in rows:
                    for col in row:
                        if "\n" in col:
                            validation_errors.append(f"New line character found in data at row {rows.index(row) + 2}")
                            if len(validation_errors) >= max_errors:
                                break

            # Strip spaces from data rows (leading and trailing) and check for extra spaces
            if len(validation_errors) < max_errors:
                for i, row in enumerate(rows):
                    for j, col in enumerate(row):
                        stripped_col = col.strip()
                        if len(validation_errors) >= max_errors:
                            break
                        # Check for extra internal spaces (multiple spaces within the column)
                        if re.search(r"\s{2,}", stripped_col):
                            validation_errors.append(f"Extra spaces found in row {i+2}, column '{header[j]}': '{col}'")
                        
                    if len(validation_errors) >= max_errors:
                        break

            # Check that data rows match header length
            if len(validation_errors) < max_errors:
                for row in rows:
                    if len(row) != len(header):
                        validation_errors.append(f"Data row {rows.index(row) + 2} has mismatched column count with the header.")
                        if len(validation_errors) >= max_errors:
                            break

            # Set validation errors in the document if there are any
            if validation_errors:
                doc.validation_error = "\n".join(validation_errors)
                doc.validation_status = "Failed"
                end_time = time.time()
                doc.total_time_taken = end_time - start_time
                doc.save()
                doc.reload()
                return {"message":"CSV file validation failed, these are just 20 errors. Please resolve errors and upload file again.", "error": True}
            else:
                doc.validation_status = "Success"
                end_time = time.time()
                doc.total_time_taken = end_time - start_time
                doc.save()
                doc.reload()
                return {"message":"CSV file validated successfully.", "error": False}


    except Exception as e:
        validation_errors.append(f"Error while reading CSV file: {str(e)}")
        doc.validation_error = "\n".join(validation_errors)
        doc.validation_status = "Failed"
        doc.save()
        doc.reload()
        return {"message":"An error occurred while reading the CSV file.", "error": True}


@frappe.whitelist()
def convert_csv_to_mrc(docname):
    """
    This method is whitelisted to convert a CSV file to MRC format
    and move it to ERPNext's private files folder.
    """
    # Get the record from ERPNext (CSV To MRC Doctype)
    base_path = get_bench_path()
    site_name = frappe.local.site

    doc = frappe.get_doc('CSV To MRC', docname)
    
    if not doc.validation_status or doc.validation_status == "Failed":
        return {"message": "The CSV file is either not validated or contains errors. Please check the validation errors or validate the file first.","error": True}
    
    #csv_file_path = "/frappe-lib/frappe-bench/sites/erpNext.ourlib" + doc.file
    csv_file_path = f"{base_path}/sites/{site_name}" + doc.file  # Path to CSV file
    basefile_name = os.path.splitext(os.path.basename(doc.file))[0]
    
    # Define paths for intermediate and final files
    mrk_file_path = f"{base_path}/sites/{site_name}/private/tmp/{basefile_name}.mrk"
    mrk_mi_file_path = f"{base_path}/sites/{site_name}/private/tmp/{basefile_name}.mrk.mi"
    mrk_mb_file_path = f"{base_path}/sites/{site_name}/private/tmp/{basefile_name}.mrk.mb"
    mrc_file_path = f"{base_path}/sites/{site_name}/private/tmp/{basefile_name}.mrc"

    # Function to run shell commands using subprocess
    def run_shell_command(command):
        """ Helper function to execute shell commands and handle errors """
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
        except subprocess.CalledProcessError as e:
            return None, f"Error: {e}"

    stdout, stderr = run_shell_command(f"dos2unix '{csv_file_path}'")

    # Run Command 1: Convert CSV to .mrk
    stdout, stderr = run_shell_command(f"perl {base_path}/apps/custom_ourlib/custom_ourlib/shell-script/tsv2mrk '{csv_file_path}' > {mrk_file_path}")
    if stderr:
        return {"message": f"Error in Command 1: {stderr}", "error": True}

    # Run Command 2: Convert .mrk to .mrk.mi
    stdout, stderr = run_shell_command(f"perl {base_path}/apps/custom_ourlib/custom_ourlib/shell-script/merge_item_fields '{mrk_file_path}' > {mrk_mi_file_path}")
    if stderr:
        return {"message": f"Error in Command 2: {stderr}", "error": True}

    # Run Command 3: Convert .mrk.mi to .mrk.mb
    stdout, stderr = run_shell_command(f"perl {base_path}/apps/custom_ourlib/custom_ourlib/shell-script/merge_items '{mrk_mi_file_path}' > {mrk_mb_file_path}")
    if stderr:
        return {"message": f"Error in Command 3: {stderr}", "error": True}

    # Run Command 4: Convert .mrk.mb to .mrc
    stdout, stderr = run_shell_command(f"perl {base_path}/apps/custom_ourlib/custom_ourlib/shell-script/mrk2mrc '{mrk_mb_file_path}' > {mrc_file_path}")
    if stderr:
        return {"message": f"Error in Command 4: {stderr}", "error": True}

    # Move the final .mrc file to ERPNext private folder
    private_folder = f"{base_path}/sites/{site_name}/private/files/"  # Path for ERPNext's private file storage
    mrc_file_name = os.path.basename(mrc_file_path)  # Get the filename from the path
    final_mrc_path = os.path.join(private_folder, mrc_file_name)  # Destination path in ERPNext's private folder

    # Ensure the private folder exists (it should, but let's make sure)
    if not os.path.exists(private_folder):
        os.makedirs(private_folder)

    # Move the .mrc file to ERPNext's private folder
    try:
        shutil.move(mrc_file_path, final_mrc_path)  # Move file to private folder
    except Exception as e:
        return {"message": f"Error moving file to private folder: {str(e)}", "error": True}

    # Create a File record to link the file to the document (CSV To MRC)
    try:
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": mrc_file_name,
            "file_url": "/private/files/" + mrc_file_name,
            "file_size": os.path.getsize(final_mrc_path),
            "attached_to_doctype": "CSV To MRC",
            "attached_to_name": docname,
            "folder": "Home/Attachments",  # Private folder where files are stored
            "is_private": 1,  # Mark the file as private
        })

        file_doc.save()  # Save the file record in ERPNext
        doc.final_mrc_file_path = "/private/files/" + file_doc.file_name  # Link to the 'final_mrc_file' field in the document
        doc.mrc_status = "Success"
        doc.save()  # Save the document with the linked file
    except Exception as e:
        return {"message": f"Error saving file to ERPNext: {str(e)}", "error": True}

    # Return success message with the path to the final .mrc file
    return {
        "message": "CSV to MRC conversion completed successfully."
    }


