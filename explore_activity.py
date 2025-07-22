'''
Authors: Sen Chen and Lingling Fan
'''

import os
import shutil
import time
import csv
import subprocess # Import the subprocess module

# Global variables, initialized in exploreActivity
adb = ''
tmp_dir = ''
act_paras_file = ''
defined_pkg_name = ''
used_pkg_name = ''

def _run_adb_command(command_args, check_output=False, input_data=None):
    """
    Helper function to run adb commands using subprocess.
    Automatically handles the global 'adb' variable which contains emulator details.
    """
    global adb
    # Split the adb string (e.g., "adb -s emulator_id") into components
    adb_parts = adb.split()
    full_command = adb_parts + command_args

    try:
        if check_output:
            # For commands where output is needed
            result = subprocess.run(full_command, capture_output=True, text=True, check=True, input=input_data)
            return result.stdout.strip()
        else:
            # For commands where only execution is needed
            subprocess.run(full_command, check=True, input=input_data)
            return True
    except subprocess.CalledProcessError as e:
        print(f"Error running ADB command: {' '.join(full_command)}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"Error: ADB command not found. Please ensure '{adb_parts[0]}' is in your PATH.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred with ADB: {e}")
        return False

def _run_shell_command(cmd, check_output=False, capture_stderr=False):
    """
    Helper function to run general shell commands using subprocess.
    Use with caution due to shell=True.
    """
    try:
        if check_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        else:
            result = subprocess.run(cmd, shell=True, capture_output=capture_stderr, text=True, check=True)
            if capture_stderr and result.stderr:
                print(f"Stderr: {result.stderr.strip()}")
            return True
    except subprocess.CalledProcessError as e:
        print(f"Error running shell command: {cmd}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"Error: Command not found for shell execution: {cmd.split()[0]}.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred with shell command: {e}")
        return False

def installAPP(new_apkpath, apk_name, results_folder):
    """
    Installs an APK on the connected device/emulator.
    Args:
        new_apkpath (str): Path to the APK file.
        apk_name (str): Name of the APK (for logging).
        results_folder (str): Folder to save install error logs.
    Returns:
        str: 'Success' or 'Failure'.
    """
    appPath = new_apkpath
    get_pkgname(appPath)

    print(f"Installing {apk_name}...")
    result_output = _run_adb_command(["install", "-r", appPath], check_output=True)

    if result_output is False: # Command execution failed entirely
        print(f"Install command failed for {apk_name}.")
        with open(os.path.join(results_folder, 'installError.csv'), 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow((apk_name, "Command execution error"))
        return 'Failure'

    for o in result_output.split('\n'):
        if 'Failure' in o or 'Error' in o:
            print(f'Install failure: {apk_name}')
            print(result_output)
            with open(os.path.join(results_folder, 'installError.csv'), 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow((apk_name, result_output.replace('\n', ', ')))
            return 'Failure'
    print('Install Success')
    return 'Success'

def uninstallApp(package):
    """
    Uninstalls an application from the device/emulator.
    Args:
        package (str): Package name of the app to uninstall.
    """
    print(f"Uninstalling {package}...")
    _run_adb_command(["uninstall", package])

# def take_screenshot(act, appname):
#     # This function was commented out, so no changes needed for now.
#     pass

def scan_and_return():
    """
    Simulates taps on the device screen for scanning and returning.
    """
    print("Performing scan and return taps...")
    time.sleep(1)
    _run_adb_command(["shell", "input", "tap", "945", "1650"]) # Scan
    time.sleep(5)
    _run_adb_command(["shell", "input", "tap", "910", "128"]) # Share
    time.sleep(1)
    _run_adb_command(["shell", "input", "tap", "654", "1078"]) # Cancel
    time.sleep(1)
    _run_adb_command(["shell", "input", "tap", "540", "1855"]) # Back (Home or Back button depending on context)
    time.sleep(1)

def clean_tmp_folder(folder):
    """
    Cleans up a temporary folder.
    Args:
        folder (str): Path to the folder to clean.
    """
    print(f"Cleaning temporary folder: {folder}...")
    if not os.path.exists(folder):
        print(f"Folder does not exist: {folder}")
        return

    for f in os.listdir(folder):
        file_path = os.path.join(folder, f)
        if os.path.isdir(file_path):
            try:
                shutil.rmtree(file_path)
            except OSError as e:
                print(f"Error removing directory {file_path}: {e}")
        else:
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error removing file {file_path}: {e}")

def unzip(zipfile, activity):
    """
    Unzips a file and renames its contents, then deletes the zip file.
    Args:
        zipfile (str): Path to the zip file.
        activity (str): Activity name to use for renaming.
    """
    print(f"Unzipping {os.path.basename(zipfile)}...")
    issue_folder = zipfile.replace('.zip', '')

    # Unzip command
    _run_shell_command(f'unzip -o "{zipfile}" -d "{issue_folder}"')

    # Remove zip file
    try:
        os.remove(zipfile)
    except OSError as e:
        print(f"Error removing zip file {zipfile}: {e}")

    # Rename txt and png file name
    if os.path.exists(issue_folder) and os.path.isdir(issue_folder):
        for f in os.listdir(issue_folder):
            file_path = os.path.join(issue_folder, f)
            if f.endswith('.png'):
                new_png_path = os.path.join(issue_folder, f"{activity}.png")
                _run_shell_command(f'mv "{file_path}" "{new_png_path}"')
            elif f.endswith('.txt'):
                new_txt_path = os.path.join(issue_folder, f"{activity}.txt")
                _run_shell_command(f'mv "{file_path}" "{new_txt_path}"')
    else:
        print(f"Warning: Issue folder not found after unzip: {issue_folder}")

def collect_results(activity, appname, accessibility_folder, results_outputs):
    """
    Collects scan results (issues and screenshots) from the device.
    Args:
        activity (str): Current activity name.
        appname (str): Application name.
        accessibility_folder (str): Base folder for accessibility results.
        results_outputs (str): Folder to store final results.
    """
    scanner_pkg = 'com.google.android.apps.accessibility.auditor'
    print('Collecting scan results from device...')

    tmp_folder = os.path.join(accessibility_folder, tmp_dir)
    os.makedirs(tmp_folder, exist_ok=True) # Ensure tmp_folder exists

    # Pull issues and rename
    issue_path = os.path.join(results_outputs, appname, 'issues')
    os.makedirs(issue_path, exist_ok=True)

    _run_adb_command(["pull", f"/data/data/{scanner_pkg}/cache/export/", tmp_folder])

    zip_folder = os.path.join(tmp_folder, "export")
    if os.path.exists(zip_folder):
        for zip_file in os.listdir(zip_folder):
            if zip_file.endswith('.zip'):
                src_zip_path = os.path.join(zip_folder, zip_file)
                dest_zip_path = os.path.join(issue_path, f"{activity}.zip")
                _run_shell_command(f'mv "{src_zip_path}" "{dest_zip_path}"')

    clean_tmp_folder(tmp_folder)

    if os.path.exists(os.path.join(issue_path, f"{activity}.zip")):
        unzip(os.path.join(issue_path, f"{activity}.zip"), activity)

    # Pull screenshot and rename
    screenshot_path = os.path.join(results_outputs, appname, 'screenshot')
    os.makedirs(screenshot_path, exist_ok=True)

    _run_adb_command(["pull", f"/data/data/{scanner_pkg}/files/screenshots/", tmp_folder])

    for png_file in os.listdir(tmp_folder):
        if png_file.endswith('.png') and not png_file.endswith('thumbnail.png'):
            src_png_path = os.path.join(tmp_folder, png_file)
            dest_png_path = os.path.join(screenshot_path, f"{activity}.png")
            _run_shell_command(f'mv "{src_png_path}" "{dest_png_path}"')
    clean_tmp_folder(tmp_folder)

    # Clean up device results
    _run_adb_command(["shell", "rm", "-rf", f"/data/data/{scanner_pkg}/cache/export/"])
    _run_adb_command(["shell", "rm", "-rf", f"/data/data/{scanner_pkg}/files/screenshots"])

def check_current_screen():
    """
    Checks the current resumed activity and logcat for errors/exceptions.
    Returns:
        bool: True if screen is normal, False otherwise.
    """
    resumed_activity_output = _run_adb_command(["shell", "dumpsys", "activity", "activities", "|", "grep", "mResumedActivity"], check_output=True)
    error_log_output = _run_adb_command(["logcat", "-t", "100", "|", "grep", "Error"], check_output=True)
    exception_log_output = _run_adb_command(["logcat", "-t", "100", "|", "grep", "Exception"], check_output=True)

    if (error_log_output and 'Error:' in error_log_output) or \
       (exception_log_output and 'Exception:' in exception_log_output) or \
       (resumed_activity_output and 'com.android.launcher3' in resumed_activity_output):
        return False
    return True

def check_current_screen_new(activity, appname, results_outputs):
    """
    Dumps UI XML to check for crash keywords or permission dialogs.
    Args:
        activity (str): Current activity name.
        appname (str): Application name.
        results_outputs (str): Folder to store layout XMLs.
    Returns:
        str: 'normal' if screen is normal, 'abnormal' if crash or permission dialog handled.
    """
    keywords = ['has stopped', 'isn\'t responding', 'keeps stopping']

    layout_path_dir = os.path.join(results_outputs, appname, 'layouts')
    os.makedirs(layout_path_dir, exist_ok=True)
    xml_filename = f"{activity}.xml"
    device_xml_path = f"/sdcard/{xml_filename}"
    local_xml_path = os.path.join(layout_path_dir, xml_filename)

    print(f"Dumping UI automator XML to {local_xml_path}...")
    _run_adb_command(["shell", "uiautomator", "dump", device_xml_path])
    _run_adb_command(["pull", device_xml_path, layout_path_dir])
    _run_adb_command(["shell", "rm", device_xml_path])

    # Check whether it crashes
    if not os.path.exists(local_xml_path):
        print(f"Warning: XML file not found at {local_xml_path}. Assuming abnormal state.")
        return 'abnormal'

    with open(local_xml_path, 'r') as f:
        xml_content = f.read()

    for word in keywords:
        if word in xml_content:
            print(f"Crash keyword '{word}' found in XML. Removing {local_xml_path}.")
            try:
                os.remove(local_xml_path)
            except OSError as e:
                print(f"Error removing XML file {local_xml_path}: {e}")
            return 'abnormal'

    # Check whether it is a permission dialog
    if 'ALLOW' in xml_content.upper() and 'DENY' in xml_content.upper():
        print("Permission dialog detected. Tapping ALLOW.")
        _run_adb_command(["shell", "input", "tap", "780", "1080"]) # Tap ALLOW
        time.sleep(1)
        resumed_activity_output = _run_adb_command(["shell", "dumpsys", "activity", "activities", "|", "grep", "mResumedActivity"], check_output=True)
        focused_activity_output = _run_adb_command(["shell", "dumpsys", "activity", "activities", "|", "grep", "mFocusedActivity"], check_output=True)
        if 'com.android.launcher3' not in resumed_activity_output and 'com.android.launcher3' not in focused_activity_output:
            return 'normal'
        else:
            print("After tapping ALLOW, still on launcher or an abnormal state. Removing {local_xml_path}.")
            try:
                os.remove(local_xml_path)
            except OSError as e:
                print(f"Error removing XML file {local_xml_path}: {e}")
            return 'abnormal'

    resumed_activity_output = _run_adb_command(["shell", "dumpsys", "activity", "activities", "|", "grep", "mResumedActivity"], check_output=True)
    focused_activity_output = _run_adb_command(["shell", "dumpsys", "activity", "activities", "|", "grep", "mFocusedActivity"], check_output=True)
    if 'com.android.launcher3' not in resumed_activity_output and 'com.android.launcher3' not in focused_activity_output:
        return 'normal'
    else:
        print(f"Currently on launcher or an abnormal state. Removing {local_xml_path}.")
        try:
            os.remove(local_xml_path)
        except OSError as e:
            print(f"Error removing XML file {local_xml_path}: {e}")
        return 'abnormal'

def explore(activity, appname, results_folder, results_outputs):
    """
    Explores a given activity, performs scans, and collects results if the screen is normal.
    Args:
        activity (str): Activity to explore.
        appname (str): Application name.
        results_folder (str): Base results folder.
        results_outputs (str): Folder for specific outputs.
    """
    current = check_current_screen_new(activity, appname, results_outputs)
    if current == 'abnormal':
        print(f"Activity {activity} is abnormal. Attempting to recover by tapping home.")
        _run_adb_command(["shell", "input", "tap", "540", "1855"]) # Tap Home/Back
        time.sleep(1)
        return

    if current == 'normal':
        print(f"Activity {activity} is normal. Performing scan and collecting results.")
        scan_and_return()
        collect_results(activity, appname, results_folder, results_outputs)

def clean_logcat():
    """
    Clears the device logcat.
    """
    print("Cleaning logcat...")
    _run_adb_command(["logcat", "-c"])

def init_d(activity, d):
    """
    Initializes a dictionary entry for an activity. (This function is not currently used in the main logic)
    """
    d[activity] = {}
    d[activity]['actions'] = ''
    d[activity]['category'] = ''
    return d

def extract_activity_action(path):
    """
    Extracts activities, actions, and categories from AndroidManifest.xml.
    Args:
        path (str): Path to AndroidManifest.xml.
    Returns:
        dict: A dictionary mapping activity names to a list of [action, category] pairs.
    """
    d = {}
    flag = 0 # 0: outside activity, 1: inside activity, 2: inside intent-filter
    current_activity = None
    action_category_pair = None

    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f: # Use utf-8 and ignore errors for manifest files
            for line in f:
                line = line.strip()
                if line.startswith('<activity'):
                    activity_name = ''
                    if 'android:name="' in line:
                        activity_name = line.split('android:name="')[1].split('"')[0]

                    if activity_name.startswith('.'):
                        activity_name = used_pkg_name + activity_name

                    if activity_name and used_pkg_name in activity_name:
                        current_activity = activity_name
                        if current_activity not in d:
                            d[current_activity] = []
                        flag = 1
                    if line.endswith('/>'):
                        flag = 0
                        current_activity = None # Reset current activity if it's a self-closing tag
                        continue

                elif line.startswith('<intent-filter') and flag == 1:
                    flag = 2
                    action_category_pair = ['', '']
                elif line.startswith('<action') and flag == 2:
                    if 'android:name="' in line:
                        action_category_pair[0] = line.split('android:name="')[1].split('"')[0]
                elif line.startswith('<category') and flag == 2:
                    if 'android:name="' in line:
                        action_category_pair[1] = line.split('android:name="')[1].split('"')[0]
                elif line.startswith('</intent-filter>') and flag == 2:
                    flag = 1
                    if current_activity and (action_category_pair[0] or action_category_pair[1]):
                        d[current_activity].append(action_category_pair)
                    action_category_pair = None # Reset for next intent-filter
                elif line.startswith('</activity>'):
                    flag = 0
                    current_activity = None # Reset current activity
    except FileNotFoundError:
        print(f"AndroidManifest.xml not found at {path}")
    except Exception as e:
        print(f"Error parsing AndroidManifest.xml at {path}: {e}")

    return d

def get_full_activity(component):
    """
    Gets the full activity name from a component string.
    Args:
        component (str): Component string (e.g., "pkg/activity" or "pkg/.activity").
    Returns:
        str: Full activity name.
    """
    act = component.split('/')[1]
    if act.startswith('.'):
        activity = component.split('/')[0] + act
    else:
        activity = act
    return activity

def convert(api, key, extras):
    """
    Converts API and key to ADB extra parameters.
    Args:
        api (str): API type (e.g., 'getString').
        key (str): Key for the extra.
        extras (str): Current extras string.
    Returns:
        str: Updated extras string.
    """
    if api == 'getString' or api == 'getStringArray':
        extras = extras + ' --es ' + key + ' test'
    elif api == 'getInt' or api == 'getIntArray':
        extras = extras + ' --ei ' + key + ' 1'
    elif api == 'getBoolean' or api == 'getBooleanArray':
        extras = extras + ' --ez ' + key + ' False'
    elif api == 'getFloat' or api == 'getFloatArray':
        extras = extras + ' --ef ' + key + ' 0.1'
    elif api == 'getLong' or api == 'getLongArray':
        extras = extras + ' --el ' + key + ' 1'
    return extras

def get_act_extra_paras(activity):
    """
    Gets extra parameters for an activity from a predefined file.
    Args:
        activity (str): Activity name.
    Returns:
        str: Extra parameters string or None if not found/empty.
    """
    if not os.path.exists(act_paras_file):
        print(f"Warning: Activity parameters file not found at {act_paras_file}")
        return None

    try:
        with open(act_paras_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(":", 1)
                if len(parts) == 2 and parts[0] == activity:
                    paras = parts[1].strip()
                    if not paras:
                        return ''
                    extras = ''
                    for each_para in paras.split(';'):
                        if '__' in each_para:
                            api, key = each_para.split('__', 1)
                            extras = convert(api, key, extras)
                    return extras
    except Exception as e:
        print(f"Error reading activity parameters file {act_paras_file}: {e}")
    return None

def startAct(component, action, cate, appname, results_folder, results_outputs):
    """
    Starts an activity on the device/emulator.
    Args:
        component (str): Component name (package/activity).
        action (str): Action to start with.
        cate (str): Category to start with.
        appname (str): Application name.
        results_folder (str): Base results folder.
        results_outputs (str): Folder for specific outputs.
    Returns:
        str: Status from explore function ('normal' or 'abnormal').
    """
    clean_logcat()
    cmd_args = ["shell", "am", "start", "-S", "-n", component]

    if action:
        cmd_args.extend(["-a", action])
    if cate:
        cmd_args.extend(["-c", cate])

    activity = get_full_activity(component)
    extras = get_act_extra_paras(activity)

    if extras is not None and extras: # Check if extras is not None and not empty string
        cmd_args.extend(extras.split()) # Split extras string into individual arguments

    print(f"Starting activity: {' '.join(cmd_args)}")
    _run_adb_command(cmd_args)
    time.sleep(3)

    return explore(activity, appname, results_folder, results_outputs)

def save_activity_to_csv(results_folder, apk_name, all_act_num, launched_act_num, act_not_launched, act_num_with_issue):
    """
    Saves activity exploration statistics to a CSV file.
    Args:
        results_folder (str): Base results folder.
        apk_name (str): APK name.
        all_act_num (int): Total number of activities.
        launched_act_num (int): Number of launched activities.
        act_not_launched (int): Number of activities not launched.
        act_num_with_issue (int): Number of activities with accessibility issues.
    """
    csv_file = os.path.join(results_folder, 'log.csv')
    # Use 'a' for append mode, newline='' to prevent blank rows on Windows
    with open(csv_file, 'a', newline='') as f:
        writer = csv.writer(f)
        # Write header if file is empty
        if os.stat(csv_file).st_size == 0:
            writer.writerow(('apk_name', 'pkg_name', 'all_act_num', 'launched_act_num', 'act_not_launched', 'act_num_with_issue'))
        writer.writerow((apk_name, used_pkg_name, all_act_num, launched_act_num, act_not_launched, act_num_with_issue))
    print(f"Saved activity stats to {csv_file}")

def parseManifest(new_apkpath, apk_name, results_folder, decompilePath, results_outputs):
    """
    Parses AndroidManifest.xml to extract activities and explore them.
    Args:
        new_apkpath (str): Path to the repackaged APK.
        apk_name (str): APK name.
        results_folder (str): Base results folder.
        decompilePath (str): Path to the decompiled app.
        results_outputs (str): Folder for specific outputs.
    """
    print(f"Parsing {apk_name}...")

    if not os.path.exists(new_apkpath):
        print(f"Cannot find the decompiled app: {apk_name}. Skipping manifest parsing.")
        return

    manifestPath = os.path.join(decompilePath, apk_name, "AndroidManifest.xml")

    if not os.path.exists(manifestPath):
        print(f"There is no AndroidManifest file for: {apk_name}. Skipping manifest parsing.")
        return

    pairs = extract_activity_action(manifestPath)
    all_activity_num = len(pairs.keys())
    print(f"Found {all_activity_num} activities in {apk_name}.")

    launched_activities = set() # To track successfully launched unique activities

    for activity, intent_filters in pairs.items():
        component = f"{defined_pkg_name}/{activity}"
        
        # Try launching with specific actions/categories first
        launched_with_intent_filter = False
        if intent_filters:
            for s in intent_filters:
                action = s[0]
                category = s[1]
                status = startAct(component, action, category, apk_name, results_folder, results_outputs)
                if status == 'normal':
                    launched_activities.add(activity)
                    launched_with_intent_filter = True
                    break # Break after first successful launch with intent filter

        # If not launched with specific intent filters, or no intent filters, try without
        if not launched_with_intent_filter:
            status = startAct(component, '', '', apk_name, results_folder, results_outputs)
            if status == 'normal':
                launched_activities.add(activity)

    # Get statistics
    launched_act_num = len(launched_activities)
    act_not_launched = all_activity_num - launched_act_num

    # Count activities with issues by checking issue folder
    issues_folder_for_app = os.path.join(results_outputs, apk_name, 'issues')
    act_num_with_issue = 0
    if os.path.exists(issues_folder_for_app):
        # Count only non-empty folders inside 'issues' which indicates an issue for an activity
        # Assuming each issue dump creates a subfolder or zip file for an activity
        # The unzip function already places files like activity.txt/png directly, so we can count these.
        for item in os.listdir(issues_folder_for_app):
            if item.endswith('.txt') or item.endswith('.png'):
                # This simple check might overcount if both .txt and .png exist for same activity
                # A more robust check would be to get unique base names (e.g., 'activity_name')
                activity_base_name = item.rsplit('.', 1)[0]
                if os.path.exists(os.path.join(issues_folder_for_app, f"{activity_base_name}.txt")) or \
                   os.path.exists(os.path.join(issues_folder_for_app, f"{activity_base_name}.png")):
                    act_num_with_issue += 1
        # To get unique activities with issues:
        unique_issue_activities = set()
        for item in os.listdir(issues_folder_for_app):
            if item.endswith('.txt') or item.endswith('.png') or item.endswith('.zip'):
                 unique_issue_activities.add(item.rsplit('.', 1)[0])
        act_num_with_issue = len(unique_issue_activities)


    save_activity_to_csv(results_folder, apk_name, all_activity_num, launched_act_num, act_not_launched,
                         act_num_with_issue)
    print(f"Parsing of {apk_name} finished!")


def get_pkgname(apk_path):
    """
    Extracts package names (defined and used) from an APK.
    Args:
        apk_path (str): Path to the APK file.
    """
    global defined_pkg_name
    global used_pkg_name

    # Use aapt to get the package name
    defined_pkg_name = _run_shell_command(
        f"aapt dump badging '{apk_path}' | grep 'package' | awk -F\"'\" '/package: name=/{{print $2}}'",
        check_output=True
    )

    # Use aapt to get the launchable activity and derive used_pkg_name
    launcher_output = _run_shell_command(
        f"aapt dump badging \"{apk_path}\" | grep launchable-activity | awk '{{print $2}}'",
        check_output=True
    )

    if launcher_output:
        launcher = launcher_output.strip().strip("'") # Remove potential quotes from awk output
        if launcher.startswith(".") or defined_pkg_name in launcher:
            used_pkg_name = defined_pkg_name
        else:
            # Handle cases like "com.example.app/com.example.app.MainActivity" or just "com.example.app.MainActivity"
            # Extract the package part from the activity name
            parts = launcher.split('.')
            if len(parts) > 1:
                # Find the longest prefix that matches a package structure
                # A common pattern is that the last part is the activity class name
                # So, we try to reconstruct the package name by removing the last part
                potential_pkg = '.'.join(parts[:-1])
                # This is a heuristic, it might need refinement for complex cases
                used_pkg_name = potential_pkg if defined_pkg_name.startswith(potential_pkg) else defined_pkg_name
            else:
                used_pkg_name = defined_pkg_name # Fallback if parsing fails
    else:
        used_pkg_name = defined_pkg_name # If no launchable activity, default to defined package name

    print(f"Defined Package Name: {defined_pkg_name}")
    print(f"Used Package Name: {used_pkg_name}")

def remove_folder(apkname, decompilePath):
    """
    Removes the decompiled app folder.
    Args:
        apkname (str): APK name.
        decompilePath (str): Base decompilation folder.
    """
    folder = os.path.join(decompilePath, apkname)
    if not os.path.exists(folder):
        print(f"Decompiled folder not found: {folder}. Nothing to remove.")
        return
    try:
        shutil.rmtree(folder)
        print(f"Successfully removed decompiled folder: {folder}")
    except OSError as e:
        print(f"Error removing folder {folder}: {e}")

def exploreActivity(new_apkpath, apk_name, results_folder, emulator, tmp_file, storydroid_file):
    """
    Main function to explore activities of a given APK.
    Args:
        new_apkpath (str): Path to the repackaged APK to explore.
        apk_name (str): Name of the APK.
        results_folder (str): Base results folder for the entire process.
        emulator (str): Emulator ID (e.g., "emulator-5554").
        tmp_file (str): Temporary directory name within accessibility_folder.
        storydroid_file (str): Path to the activity parameters file (act_paras_file).
    """
    global adb
    adb = f"adb -s {emulator}" # Set global adb string with emulator ID

    global tmp_dir
    tmp_dir = tmp_file

    global act_paras_file
    act_paras_file = storydroid_file # Set global activity parameters file path

    decompilePath = os.path.join(results_folder, "apktool")  # Decompiled app path (apktool handled)
    results_outputs = os.path.join(results_folder, "outputs") # Where screenshots and issues are stored
    installErrorAppPath = os.path.join(results_folder, "install-error-apks")

    # Ensure all necessary directories exist
    os.makedirs(decompilePath, exist_ok=True)
    os.makedirs(results_outputs, exist_ok=True)
    os.makedirs(installErrorAppPath, exist_ok=True)

    print(f"Starting activity exploration for {apk_name} at {new_apkpath} on {emulator}")

    # Install the app
    result = installAPP(new_apkpath, apk_name, results_folder)

    if result == 'Failure':
        print(f"Installation failed for {apk_name}. Moving APK to install error folder.")
        dest_path = os.path.join(installErrorAppPath, os.path.basename(new_apkpath))
        try:
            shutil.move(new_apkpath, dest_path)
            print(f"Moved {os.path.basename(new_apkpath)} to {installErrorAppPath}")
        except FileNotFoundError:
            print(f"Original APK not found at {new_apkpath} for moving.")
        except shutil.Error as e:
            print(f"Error moving APK to install error folder: {e}")
        return # Exit if installation fails

    # Parse manifest and explore activities
    parseManifest(new_apkpath, apk_name, results_folder, decompilePath, results_outputs)

    # Uninstall the app after exploration
    if defined_pkg_name:
        uninstallApp(defined_pkg_name)
    else:
        print(f"Warning: Could not determine package name for {apk_name}. Skipping uninstall.")

    # Remove the decompiled and modified resources (optional, currently commented out in original)
    # remove_folder(apk_name, decompilePath)

    print(f"Activity exploration for {apk_name} completed.")


# Example usage (uncomment and modify paths/emulator details to test)
# if __name__ == '__main__':
#     # Dummy setup for testing
#     test_results_folder = "test_results"
#     test_emulator = "emulator-5554"  # Replace with your emulator ID
#     test_tmp_file = "temp_scan_data"
#     test_storydroid_file = "dummy_activity_params.txt" # Create this file for testing if needed
#     test_apk_path = "path/to/your/repackaged_test_app.apk" # Path to a real repackaged APK
#     test_apk_name = "repackaged_test_app"
#
#     os.makedirs(test_results_folder, exist_ok=True)
#
#     # Create a dummy activity params file if it doesn't exist for testing
#     if not os.path.exists(test_storydroid_file):
#         with open(test_storydroid_file, 'w') as f:
#             f.write("com.example.app.MainActivity:getString__param1;getInt__param2\n")
#             f.write("com.example.app.AnotherActivity:\n")
#
#     # Call the main exploration function
#     # exploreActivity(test_apk_path, test_apk_name, test_results_folder, test_emulator, test_tmp_file, test_storydroid_file)
#
#     print("Script finished. Check 'test_results' folder for outputs.")