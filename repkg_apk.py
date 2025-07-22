import os
import shutil
import subprocess # Import the subprocess module

# keyPath = os.path.join(os.path.split(os.path.realpath(__file__))[0], "coolapk.keystore")  # pwd: 123456, private key path
keyPath = ''
def decompile(eachappPath, decompileAPKPath):
    """
    Decompiles an APK file using apktool.
    Args:
        eachappPath (str): Path to the APK file.
        decompileAPKPath (str): Path to the output directory for decompiled files.
    """
    print("Decompiling...")
    cmd = ["apktool", "d", eachappPath, "-f", "-o", decompileAPKPath]
    print(f"Command to run: {' '.join(cmd)}")
    try:
        # Using subprocess.run for simple command execution.
        # check=True will raise CalledProcessError if the command returns a non-zero exit code.
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Successfully decompiled {eachappPath} to {decompileAPKPath}")
    except subprocess.CalledProcessError as e:
        print(f"Error during decompilation: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
    except FileNotFoundError:
        print("Error: apktool command not found. Please ensure apktool is installed and in your PATH.")


def modifyManifestAgain(line_num, decompileAPKPath):
    """
    Modifies the AndroidManifest.xml to fix a specific error related to resource visibility.
    Args:
        line_num (int): The 1-based line number in the Manifest file to modify.
        decompileAPKPath (str): Path to the decompiled APK directory.
    """
    ManifestPath = os.path.join(decompileAPKPath, "AndroidManifest.xml")
    try:
        with open(ManifestPath, 'r') as f:
            lines = f.readlines()

        if 0 < line_num <= len(lines):
            # Adjust to 0-based index for list access
            target_line_index = line_num - 1
            if '@android' in lines[target_line_index]:
                # Replace '@android' with '@*android' to fix resource visibility error
                parts = lines[target_line_index].split('@android', 1)
                lines[target_line_index] = parts[0] + '@*android' + parts[1]
                print(f"Modified line {line_num} in AndroidManifest.xml.")
            else:
                print(f"Line {line_num} does not contain '@android'. No modification needed.")
        else:
            print(f"Line number {line_num} is out of bounds for AndroidManifest.xml.")

        with open(ManifestPath, 'w') as f:
            f.writelines(lines)
    except FileNotFoundError:
        print(f"Error: AndroidManifest.xml not found at {ManifestPath}")
    except Exception as e:
        print(f"An error occurred while modifying AndroidManifest.xml: {e}")


def recompile(decompileAPKPath):
    """
    Recompiles the modified APK using apktool.
    Args:
        decompileAPKPath (str): Path to the decompiled APK directory.
    Returns:
        str: The standard output from the apktool recompile command.
    """
    cmd = ["apktool", "b", decompileAPKPath]
    print("Recompiling...")
    try:
        # Using subprocess.run to capture output.
        # capture_output=True captures stdout and stderr.
        # text=True decodes stdout/stderr as text.
        result = subprocess.run(cmd, capture_output=True, text=True, check=False) # check=False because we handle errors based on output content
        if result.returncode != 0:
            print(f"Recompilation failed with exit code {result.returncode}.")
            print(f"Stderr: {result.stderr}")
        return result.stdout
    except FileNotFoundError:
        print("Error: apktool command not found. Please ensure apktool is installed and in your PATH.")
        return ""
    except Exception as e:
        print(f"An error occurred during recompilation: {e}")
        return ""


def sign_apk(apk_name, decompileAPKPath, repackagedAppPath):
    """
    Signs the repackaged APK using jarsigner.
    Args:
        apk_name (str): The base name of the APK (without .apk extension).
        decompileAPKPath (str): Path to the decompiled APK directory (where the 'dist' folder is).
        repackagedAppPath (str): Path to the directory where the signed APK will be stored.
    Returns:
        str: "success" if signing is successful, "fail" otherwise.
    """
    repackName = apk_name + ".apk"
    resign_appName = apk_name + "_sign" + ".apk"
    repackAppPath = os.path.join(decompileAPKPath, 'dist', repackName) # Corrected path to the built APK
    sign_apk_output_path = os.path.join(repackagedAppPath, resign_appName)

    print(f"Key Path: {keyPath}")
    print(f"Output Signed APK Path: {sign_apk_output_path}")
    print(f"Input Repackaged APK Path: {repackAppPath}")

    # The password '123456' is passed via stdin to jarsigner
    cmd = [
        "jarsigner",
        "-verbose",
        "-keystore", keyPath,
        "-signedjar", sign_apk_output_path,
        repackAppPath,
        "coolapk" # Alias for the key
    ]

    print("Signing...")
    try:
        # Using subprocess.run with input to pass the password
        result = subprocess.run(
            cmd,
            input='123456\n', # Password followed by a newline
            capture_output=True,
            text=True,
            check=False # Do not raise an exception for non-zero exit codes, we check output
        )
        signlog = result.stdout
        if result.returncode != 0:
            print(f"Jarsigner failed with exit code {result.returncode}.")
            print(f"Stderr: {result.stderr}")

        for line in signlog.split("\n"):
            if 'jar signed.' in line:
                print('Sign success...................................................')
                return "success"
        print("Sign failed. 'jar signed.' not found in output.")
        return "fail"
    except FileNotFoundError:
        print("Error: jarsigner command not found. Please ensure Java Development Kit (JDK) is installed and in your PATH.")
        return "fail"
    except Exception as e:
        print(f"An error occurred during signing: {e}")
        return "fail"


def rename(apkname, repackagedAppPath):
    """
    Renames the signed APK to its original name.
    Args:
        apkname (str): The base name of the APK.
        repackagedAppPath (str): Path to the directory where the signed APK is located.
    """
    oldNamePath = os.path.join(repackagedAppPath, apkname + '_sign.apk')
    newNamePath = os.path.join(repackagedAppPath, apkname + '.apk')
    try:
        if os.path.exists(oldNamePath):
            os.rename(oldNamePath, newNamePath)
            print(f"Renamed {os.path.basename(oldNamePath)} to {os.path.basename(newNamePath)}")
        else:
            print(f"Error: File not found for renaming: {oldNamePath}")
    except OSError as e:
        print(f"Error renaming file: {e}")


def remove_folder(apkname, decompilePath):
    """
    Removes the decompiled APK folder.
    Args:
        apkname (str): The base name of the APK.
        decompilePath (str): Path to the directory containing decompiled APK folders.
    """
    folder = os.path.join(decompilePath, apkname)
    if not os.path.exists(folder):
        print(f"Folder not found: {folder}. Nothing to remove.")
        return
    try:
        shutil.rmtree(folder)
        print(f"Successfully removed folder: {folder}")
    except OSError as e:
        print(f"Error removing folder {folder}: {e}")


def addExportedTrue(line):
    """
    Adds or modifies 'exported="true"' attribute to an XML line.
    Args:
        line (str): The XML line to modify.
    Returns:
        str: The modified XML line.
    """
    if 'exported="true"' in line:
        return line
    if 'exported="false"' in line:
        return line.replace('exported="false"', 'exported="true"')
    if not 'exported' in line:
        # Insert exported="true" after <activity tag
        return '<activity exported="true" ' + line.split('<activity ')[1]
    return line # Return original line if no relevant change is needed


def modifyManifest_00(decompileAPKPath):
    """
    Modifies the AndroidManifest.xml to set all activities as exported="true".
    Args:
        decompileAPKPath (str): Path to the decompiled APK directory.
    Returns:
        str: "NoManifest" if Manifest file is not found, None otherwise.
    """
    newlines = []
    ManifestPath = os.path.join(decompileAPKPath, "AndroidManifest.xml")

    if not os.path.exists(ManifestPath):
        print(f"AndroidManifest.xml not found at {ManifestPath}")
        return "NoManifest"
    else:
        try:
            with open(ManifestPath, 'r') as f:
                for line in f:
                    if line.strip().startswith('<activity '):
                        line = addExportedTrue(line)
                    newlines.append(line)

            # Use 'w' mode for writing, 'wb' is for binary mode.
            # Since we are using text=True in subprocess, we should handle files as text.
            with open(ManifestPath, 'w') as f:
                f.writelines(newlines)
            print(f"Successfully modified AndroidManifest.xml at {ManifestPath}")
            return None
        except Exception as e:
            print(f"An error occurred while modifying AndroidManifest.xml: {e}")
            return "Error"


def startRepkg(apk_path, apkname, results_folder, config_folder):
    """
    Starts the repackaging process for an APK.
    Args:
        apk_path (str): Path to the original APK file.
        apkname (str): The base name of the APK (without .apk extension).
        results_folder (str): Base folder for all results (decompiled, repackaged, error apks).
        config_folder (str): Folder containing configuration files like keystore.
    Returns:
        str: Status of the repackaging process (e.g., 'success', 'no manifest file', 'build error', 'sign error').
    """
    global keyPath
    keyPath = os.path.join(config_folder, "coolapk.keystore")
    print(f"Using keystore path: {keyPath}")

    noManifestAppPath = os.path.join(results_folder, "no-manifest-apks")
    buildErrorAppPath = os.path.join(results_folder, "build-error-apks")
    signErrorAppPath = os.path.join(results_folder, "sign-error-apks")
    decompilePath = os.path.join(results_folder, "apktool")  # decompiled app path (apktool handled)
    repackagedAppPath = os.path.join(results_folder, "repackaged")  # store the repackaged apps

    # Create necessary directories
    os.makedirs(noManifestAppPath, exist_ok=True)
    os.makedirs(buildErrorAppPath, exist_ok=True)
    os.makedirs(signErrorAppPath, exist_ok=True)
    os.makedirs(decompilePath, exist_ok=True)
    os.makedirs(repackagedAppPath, exist_ok=True)

    decompileAPKPath = os.path.join(decompilePath, apkname)

    # Decompile original apk
    decompile(apk_path, decompileAPKPath)

    # Modify Manifest
    msg = modifyManifest_00(decompileAPKPath)

    if msg == "NoManifest":
        print("No AndroidManifest.xml found. Moving original APK to error folders.")
        # Using shutil.move for moving files
        try:
            shutil.move(apk_path, os.path.join(repackagedAppPath, os.path.basename(apk_path)))
            shutil.move(os.path.join(repackagedAppPath, os.path.basename(apk_path)), noManifestAppPath)
        except FileNotFoundError:
            print(f"Original APK not found at {apk_path} for moving.")
        except shutil.Error as e:
            print(f"Error moving APK: {e}")
        return 'no manifest file'

    # Recompile modified apk
    recompileInfo = recompile(decompileAPKPath)
    print("Recompiling output received.")

    builtApk = False
    for line in recompileInfo.split('\n'):
        if "Error: Resource is not public." in line:
            print("Resource not public error detected. Attempting to fix and recompile.")
            line_num = int(line.split('AndroidManifest.xml:')[1].split(': error')[0])
            modifyManifestAgain(line_num, decompileAPKPath)
            recompileInfo = recompile(decompileAPKPath) # Re-attempt recompile after modification
            break # Exit loop after first fix attempt
        if "Built apk..." in line:
            builtApk = True
            print("Successfully recompiled an apk!!!")
            break # Exit loop once "Built apk..." is found

    if not builtApk:
        print("Recompilation failed. Moving original APK to build-error-apks.")
        try:
            shutil.move(apk_path, os.path.join(repackagedAppPath, os.path.basename(apk_path)))
            shutil.move(os.path.join(repackagedAppPath, os.path.basename(apk_path)), buildErrorAppPath)
        except FileNotFoundError:
            print(f"Original APK not found at {apk_path} for moving.")
        except shutil.Error as e:
            print(f"Error moving APK: {e}")
        return 'build error'

    print("Signing...")
    # Sign the modified apk
    signlabel = sign_apk(apkname, decompileAPKPath, repackagedAppPath)

    if signlabel == "fail":
        print("Signing failed. Moving original APK to sign-error-apks.")
        try:
            shutil.move(apk_path, os.path.join(repackagedAppPath, os.path.basename(apk_path)))
            shutil.move(os.path.join(repackagedAppPath, os.path.basename(apk_path)), signErrorAppPath)
        except FileNotFoundError:
            print(f"Original APK not found at {apk_path} for moving.")
        except shutil.Error as e:
            print(f"Error moving APK: {e}")
        return 'sign error'

    # Rename the signed apk
    rename(apkname, repackagedAppPath)
    print(f"Repackaging of {apkname} completed successfully.")

    # Remove the decompiled and modified resources
    # Uncomment the line below if you want to remove the decompiled folder after successful repackaging
    # remove_folder(apkname, decompilePath)

    return 'success' # Indicate overall success

# Example usage (uncomment and modify paths to test)
# if __name__ == '__main__':
#     # Define dummy paths for testing
#     # You would replace these with actual paths to your APK, keystore, and desired output folders
#     test_apk_path = "/path/to/your/app.apk"
#     test_apk_name = "app"
#     test_results_folder = "/path/to/your/results"
#     test_config_folder = "/path/to/your/config" # This folder should contain coolapk.keystore
#
#     # Create dummy files/folders for testing if they don't exist
#     os.makedirs(test_config_folder, exist_ok=True)
#     # Create a dummy keystore file if it doesn't exist for testing purposes
#     # In a real scenario, you would have a valid keystore.
#     # with open(os.path.join(test_config_folder, "coolapk.keystore"), 'w') as f:
#     #     f.write("dummy keystore content")
#
#     # Create a dummy APK file for testing purposes
#     # with open(test_apk_path, 'w') as f:
#     #     f.write("dummy apk content")
#
#     # Call the main repackaging function
#     # status = startRepkg(test_apk_path, test_apk_name, test_results_folder, test_config_folder)
#     # print(f"Repackaging status: {status}")