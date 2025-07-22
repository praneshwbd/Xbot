'''
Authors: Sen Chen and Lingling Fan
'''

import os
import shutil
import sys
import csv
import subprocess # Import the subprocess module

global paras_path

# Global configurations from command line arguments
emulator = sys.argv[1] # Emulator name
# emulator = 'emulator-5554' # Android Studio emulator (example)

# Derive other paths
accessbility_folder = os.path.join(os.getcwd(), 'main-folder') 

apkPath = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else  os.path.join(accessbility_folder, "apks")# APK folder e.g., main-folder/apks/a2dp.Vol_133.apk

config_folder = os.path.join(accessbility_folder, "config")
results_folder = os.path.join(accessbility_folder, "results")
storydroid_folder = os.path.join(accessbility_folder, "storydroid")
decompilePath = os.path.join(accessbility_folder, "apktool")  # decompiled app path (apktool handled)
repackagedAppPath = os.path.join(results_folder, "repackaged")  # store the repackaged apps
keyPath = os.path.join(config_folder, "coolapk.keystore") # pwd: 123456, private key path
lib_home_path = os.path.join(config_folder, "libs") # configlib path
results_outputs = os.path.join(results_folder, "outputs") # project results
tmp_file = os.path.join(results_folder, emulator) # tmp file for parallel execution

# Java Home Path - **Please verify this path for your system**
# java_home_path = '/Library/Java/JavaVirtualMachines/jdk1.8.0_211.jdk/Contents/Home/' # For Macbook (example)
java_home_path = os.environ.get('JAVA_HOME')

# SDK Platform Path - **Please verify this path for your system**
sdk_platform_path = os.path.join(lib_home_path, 'android-platforms') # For Macbook (example)

# Global variable for activity parameters file path, set later in main
paras_path = ''

# Import other modules (assuming they are in the same directory or Python path)
# Assuming these modules have been refactored to use subprocess.
import repkg_apk
import explore_activity


def createOutputFolder():
    """
    Creates necessary output directories if they don't already exist.
    """
    print("Creating output folders...")
    os.makedirs(results_folder, exist_ok=True)
    os.makedirs(storydroid_folder, exist_ok=True)
    os.makedirs(decompilePath, exist_ok=True)
    os.makedirs(repackagedAppPath, exist_ok=True)
    os.makedirs(results_outputs, exist_ok=True)
    print("Output folders ensured.")


def execute(apk_path, apk_name):
    """
    Executes the repackaging and activity exploration process for a single APK.
    Args:
        apk_path (str): Full path to the original APK.
        apk_name (str): Name of the APK without the '.apk' extension.
    """
    # Repackage app
    repackaged_apk_full_path = os.path.join(repackagedAppPath, apk_name + '.apk')

    if not os.path.exists(repackaged_apk_full_path):
        print(f"Repackaging {apk_name}...")
        r = repkg_apk.startRepkg(apk_path, apk_name, results_folder, config_folder)

        if r in ['no manifest file', 'build error', 'sign error']:
            print(f"APK {apk_name} not successfully recompiled ({r}). Will use the original app to execute if possible.")
            # In case of repackaging failure, if original logic was to use original APK,
            # we should adjust new_apkpath accordingly.
            # However, the current logic relies on `os.path.exists(new_apkpath)` to be the repackaged one.
            # So, if repackaging failed, new_apkpath might not exist as the repackaged version.
            # For simplicity, we'll keep `new_apkpath` pointing to the potential repackaged app.
            # The explore_activity will then proceed if a repackaged app exists or handle its absence.
    else:
        print(f"Repackaged APK {apk_name} already exists. Skipping repackaging.")

    new_apkpath = os.path.join(repackagedAppPath, apk_name + '.apk')

    # If repackaging failed, the `new_apkpath` might not exist.
    # The `explore_activity` module should be robust to handle this by either
    # using the original APK or reporting an error.
    if os.path.exists(new_apkpath):
        print(f"Starting activity exploration for repackaged APK: {new_apkpath}")
        explore_activity.exploreActivity(new_apkpath, apk_name, results_folder, emulator, tmp_file, paras_path)
    else:
        print(f"Repackaged APK {new_apkpath} not found. Cannot proceed with exploration for {apk_name}.")


def run_soot(apk_path, pkg):
    """
    Runs the Soot analysis tool to get bundle data for UI page rendering.
    Args:
        apk_path (str): Full path to the APK.
        pkg (str): Package name of the APK.
    """
    soot_file = 'run_soot.run' # Binary file name
    current_dir = os.getcwd() # Save current directory
    
    print(f"Changing directory to: {config_folder}")
    os.chdir(config_folder) # Change to config directory where run_soot.run is located

    cmd = [
        f'./{soot_file}',
        storydroid_folder,
        apk_path,
        pkg,
        java_home_path,
        sdk_platform_path,
        lib_home_path
    ]
    undefined_values = [val for val in cmd if not val]
    if undefined_values:
        print("❌ Error: Some required command arguments are undefined or empty:")
        for i, val in enumerate(cmd):
            if not val:
                print(f"  - Argument {i + 1} (missing)")

    print(f"Running Soot command: {' '.join(cmd)}")
    try:
        # Use subprocess.run to execute the binary
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Soot analysis completed successfully.")
        if result.stdout:
            print(f"Soot Output:\n{result.stdout}")
        if result.stderr:
            print(f"Soot Errors (if any):\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Error running Soot analysis for {pkg}: {e}")
        print(f"Soot Stderr:\n{e.stderr}")
    except FileNotFoundError:
        print(f"Error: Soot binary '{soot_file}' not found in {config_folder}. Please ensure it exists and is executable.")
    except Exception as e:
        print(f"An unexpected error occurred during Soot analysis: {e}")
    finally:
        # Change back to the original directory
        print(f"Changing directory back to: {current_dir}")
        os.chdir(current_dir)


def get_pkg(apk_path):
    """
    Extracts the package name from an APK using aapt.
    This version tries to get the most "used" package name.
    Args:
        apk_path (str): Full path to the APK file.
    Returns:
        str: The determined package name.
    """
    defined_pkg_name = ''
    try:
        # Command to get the package name defined in the manifest
        cmd_defined_pkg = f"aapt dump badging \"{apk_path}\" | grep 'package' | awk -v FS=\"'\" '/package: name=/{{print$2}}'"
        defined_pkg_name = subprocess.run(cmd_defined_pkg, shell=True, capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting defined package name for {apk_path}: {e.stderr.strip()}")
        return '' # Return empty if aapt fails

    used_pkg_name = defined_pkg_name # Default to defined package name

    try:
        # Command to get the launchable activity
        cmd_launcher = f"aapt dump badging \"{apk_path}\" | grep launchable-activity | awk '{{print $2}}'"
        launcher_output = subprocess.run(cmd_launcher, shell=True, capture_output=True, text=True, check=True).stdout.strip()

        if launcher_output:
            launcher = launcher_output.strip("'") # Remove potential quotes
            if not launcher.startswith(".") and defined_pkg_name not in launcher:
                # Heuristic: If launcher activity is not relative and doesn't contain defined pkg,
                # try to derive pkg from launcher's full class name.
                # This assumes launcher is like com.some.other.package.ActivityName
                parts = launcher.split('.')
                # Assuming the package part is everything before the last element (activity class name)
                if len(parts) > 1:
                    potential_used_pkg = '.'.join(parts[:-1])
                    if potential_used_pkg: # Ensure it's not empty
                        used_pkg_name = potential_used_pkg
    except subprocess.CalledProcessError as e:
        print(f"Error getting launchable activity for {apk_path}: {e.stderr.strip()}")
    except Exception as e:
        print(f"An unexpected error occurred while parsing launcher activity: {e}")

    print(f"Determined package name for {os.path.basename(apk_path)}: {used_pkg_name}")
    return used_pkg_name


def remove_folder(apkname, decompilePath):
    """
    Removes the decompiled APK folder.
    Args:
        apkname (str): The base name of the APK.
        decompilePath (str): Path to the directory containing decompiled APK folders.
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
    except Exception as e:
        print(f"An unexpected error occurred while removing folder {folder}: {e}")


if __name__ == '__main__':
    
    createOutputFolder()  # Create the folders if not exists

    out_csv = os.path.join(results_folder, 'log.csv')
    if not os.path.exists(out_csv):
        # Use 'w' mode to create the file and write header, then 'a' for subsequent runs.
        # Use newline='' for proper CSV writing on all platforms.
        with open(out_csv, 'w', newline='') as f:
            csv.writer(f).writerow(('apk_name', 'pkg_name', 'all_act_num', 'launched_act_num',
                                    'act_not_launched','act_num_with_issue'))

    # Prepare for ADB root command once
    adb_root_cmd = ["adb", "-s", emulator, "root"]
    print(f"Attempting to root emulator: {' '.join(adb_root_cmd)}")
    try:
        root_output = subprocess.run(adb_root_cmd, capture_output=True, text=True, check=False)
        print(f"ADB Root Output:\n{root_output.stdout.strip()}")
        if root_output.stderr:
            print(f"ADB Root Errors:\n{root_output.stderr.strip()}")
        if root_output.returncode != 0 and "adbd cannot run as root" not in root_output.stderr:
            print("Warning: Failed to get root access or encountered an unexpected error.")
    except FileNotFoundError:
        print("Error: adb command not found. Please ensure ADB is installed and in your PATH.")
        sys.exit(1) # Exit if adb is not found

    # Set global paras_path before calling execute
    # This path is where Soot outputs activity parameters
    # The assumption is that `run_soot` would have created this path and file.
    paras_path = os.path.join(storydroid_folder, 'outputs', 'activity_paras.txt') # Adjusted to not include apk_name initially

    for apk_file in os.listdir(apkPath): # Run the apk one by one
        # Ensure we only process actual APK files and not directories or other files
        if apk_file.lower().endswith('.apk') and os.path.isfile(os.path.join(apkPath, apk_file)):

            apk_full_path = os.path.join(apkPath, apk_file) # Get full apk path
            apk_name = os.path.splitext(apk_file)[0] # Get apk name without .apk extension
            pkg = get_pkg(apk_full_path) # Get pkg name for this APK

            print(f"\n======== Starting analysis for {apk_name} (Package: {pkg}) ========")

            '''
            Get Bundle Data (Soot Analysis)
            Trade off by users, open or close
            '''
            # Ensure the output directory for this specific APK's Soot results exists
            current_soot_output_dir = os.path.join(storydroid_folder, 'outputs', apk_name)
            os.makedirs(current_soot_output_dir, exist_ok=True)
            current_paras_path = os.path.join(current_soot_output_dir, 'activity_paras.txt')

            # Update the global paras_path for explore_activity to use the correct file for this APK
            paras_path = current_paras_path

            # Only run Soot if the parameters file doesn't exist or is empty
            if not os.path.exists(current_paras_path) or os.stat(current_paras_path).st_size == 0:
                print(f"Running Soot analysis for {apk_name} to generate parameters in {current_soot_output_dir}...")
                run_soot(apk_full_path, pkg)
            else:
                print(f"Soot parameters file already exists for {apk_name}. Skipping Soot analysis.")

            # Ensure the parameters file exists, even if empty, before passing to explore_activity
            if not os.path.exists(paras_path):
                open(paras_path, 'w').close() # Create an empty file if Soot didn't create it

            '''
            Core Execution (Repackaging and Exploration)
            '''
            execute(apk_full_path, apk_name)

            print(f"Cleaning up files for {apk_name}...")
            # Delete the original apk (if it was copied or moved by repkg_apk)
            if os.path.exists(apk_full_path):
                try:
                    os.remove(apk_full_path)
                    print(f"Removed original APK: {apk_full_path}")
                except OSError as e:
                    print(f"Error removing original APK {apk_full_path}: {e}")

            # Delete the repackaged apk
            repackaged_apk_to_remove = os.path.join(repackagedAppPath, apk_name + '.apk')
            if os.path.exists(repackaged_apk_to_remove):
                try:
                    os.remove(repackaged_apk_to_remove)
                    print(f"Removed repackaged APK: {repackaged_apk_to_remove}")
                except OSError as e:
                    print(f"Error removing repackaged APK {repackaged_apk_to_remove}: {e}")

            # Remove the decompiled and modified resources
            remove_folder(apk_name, decompilePath)

    print("\nAll APKs processed. Script finished.")