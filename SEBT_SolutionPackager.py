import os
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET

# Variables
INPUT_FOLDER = "Input"
OUTPUT_FOLDER = "Packaged Solutions"
TEMP_FOLDER = "Temporary"


# Helper Functions
# ----------------
# Zip Extraction
def extract_zip(zip_file, extract_location):
    print(f"➡️  Extracting {zip_file} to {extract_location}")

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(extract_location)

# Zip Creation
def create_zip(output_location, edited_solution):
    print(f"➡️  Creating zip {output_location}")

    # Check that output location exists
    parent_dir = os.path.dirname(os.path.abspath(output_location))
    if not os.path.exists(parent_dir):
        print(f"  ℹ️  Output Location did not exist. Creating: {parent_dir}")
        os.makedirs(parent_dir, exist_ok=True)

    with zipfile.ZipFile(output_location, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(edited_solution):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, edited_solution)
                zipf.write(full_path, arcname)

# Solution.xml edits that need to be made
def edit_solution_xml(file_path):
    print(f"➡️  Editing solution.xml")

    tree = ET.parse(file_path)
    root = tree.getroot()

    manifest = root.find("SolutionManifest")

    # Rename Solution UniqueName
    unique = manifest.find("UniqueName")
    if unique is not None:
        unique.text = "SecurityRoleManager"

    # Rename LocalizedName
    for ln in manifest.findall(".//LocalizedName[@languagecode='1033']"):
        ln.set("description", "Security Role Manager")

    # Set Managed status to Unmanaged
    managed = manifest.find("Managed")
    if managed is not None:
        managed.text = "0"

    # Set Publisher Information to eWorldSunbucksWorkforce
    publisher = manifest.find("Publisher")
    if publisher is not None:
        # UniqueName
        pub_unique = publisher.find("UniqueName")
        if pub_unique is not None:
            pub_unique.text = "eWorldSunbucksWorkforce"

        # LocalizedName
        for ln in publisher.findall(".//LocalizedName[@languagecode='1033']"):
            ln.set("description", "eWorld Sunbucks Workforce")

        # Description
        for desc in publisher.findall(".//Description[@languagecode='1033']"):
            desc.set("description", "Sunbucks Workforce")

        # Prefixes
        prefix = publisher.find("CustomizationPrefix")
        if prefix is not None:
            prefix.text = "ewwp"

        opt_prefix = publisher.find("CustomizationOptionValuePrefix")
        if opt_prefix is not None:
            opt_prefix.text = "81963"

    # Renaming RootComponents
    for rc in manifest.findall(".//RootComponent"):
        schema = rc.attrib.get("schemaName", "")
        if schema == "cc_Cathal.SecurityRoleManager/bundle.js.map":
            rc.set("schemaName", "ewwp_bundle.js.map")
        elif schema == "cn_Cathal.SecurityRoleManager":
            rc.set("schemaName", "ewwp.SecurityRoleManager")

    tree.write(file_path, encoding="utf-8", xml_declaration=True)

# customizations.xml edits that need to be made
def edit_customizations_xml(file_path):
    print(f"➡️  Editing customizations.xml")

    tree = ET.parse(file_path)
    root = tree.getroot()

    for node in root.findall(".//Name"):
        if node.text == "cn_Cathal.SecurityRoleManager":
            node.text = "ewwp.SecurityRoleManager"
        elif node.text == "cc_Cathal.SecurityRoleManager/bundle.js.map":
            node.text = "ewwp_bundle.js.map"

    for node in root.findall(".//FileName"):
        if node.text == "/Controls/cn_Cathal.SecurityRoleManager/ControlManifest.xml":
            node.text = "/Controls/SecurityRoleManager/ControlManifest.xml"
        elif node.text == "/WebResources/cc_Cathal.SecurityRoleManager/bundle.js.map":
            node.text = "/WebResources/ewwp_bundle.js.map"

    tree.write(file_path, encoding="utf-8", xml_declaration=True)

# ControlManifest.xml edits that need to be made
def edit_control_manifest(file_path):
    print(f"➡️  Editing ControlManifest.xml")

    tree = ET.parse(file_path)
    root = tree.getroot()

    control = root.find(".//control")
    if control is not None:
        control.set("namespace", "ewwp")

    tree.write(file_path, encoding="utf-8", xml_declaration=True)

# Solution Packager
def main():
    # find the input solution and extract version
    input_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith("_managed.zip")]
    if not input_files:
        raise FileNotFoundError("❌ No *_managed.zip file found in Input folder.")

    zip_file = os.path.join(INPUT_FOLDER, input_files[0])
    version_match = re.search(r"SecurityRoleManager_(.*?)_managed\.zip", input_files[0])
    version = version_match.group(1) if version_match else "unknown"

    edited_zip = os.path.join(
        OUTPUT_FOLDER, f"SecurityRoleManager_{version}_unmanaged.zip"
    )

    # cleanup old temp in case it exists
    if os.path.exists(TEMP_FOLDER):
        shutil.rmtree(TEMP_FOLDER)
    os.makedirs(TEMP_FOLDER, exist_ok=True)

    # unpack zip
    extract_zip(zip_file, TEMP_FOLDER)

    # edit solution.xml
    sol_path = os.path.join(TEMP_FOLDER, "solution.xml")
    if os.path.exists(sol_path):
        edit_solution_xml(sol_path)

    # edit customizations.xml
    cust_path = os.path.join(TEMP_FOLDER, "customizations.xml")
    if os.path.exists(cust_path):
        edit_customizations_xml(cust_path)

    # move and rename bundle.js.map
    old_bundle = os.path.join(TEMP_FOLDER, "WebResources", "cc_Cathal.SecurityRoleManager", "bundle.js.map")
    new_bundle = os.path.join(TEMP_FOLDER, "WebResources", "ewwp_bundle.js.map")
    if os.path.exists(old_bundle):
        shutil.move(old_bundle, new_bundle)
        shutil.rmtree(os.path.join(TEMP_FOLDER, "WebResources", "cc_Cathal.SecurityRoleManager"), ignore_errors=True)

    # rename controls folder
    old_controls = os.path.join(TEMP_FOLDER, "Controls", "cn_Cathal.SecurityRoleManager")
    new_controls = os.path.join(TEMP_FOLDER, "Controls", "SecurityRoleManager")
    if os.path.exists(old_controls):
        shutil.move(old_controls, new_controls)
        manifest = os.path.join(new_controls, "ControlManifest.xml")
        if os.path.exists(manifest):
            edit_control_manifest(manifest)

    # repackage into new zip
    create_zip(edited_zip, TEMP_FOLDER)

    # cleanup temp
    shutil.rmtree(TEMP_FOLDER, ignore_errors=True)

    print(f"✅ Created unmanaged solution: {edited_zip}")

# In case the script gets imported elsewhere
if __name__ == "__main__":
    main()
