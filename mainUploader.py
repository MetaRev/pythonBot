try:
    import sys
    import time
    import logging
    import os
    import re
    import json
    import io
    import shutil
    import configparser
    from colorama import init, Fore, Back, Style
    import requests
    from cleantext import clean
    from PIL import Image
except ImportError as e:
    print("[ERROR] Failed to import modules. Please install all requirements.")
    print(str(e))
    sys.exit(1)

# Initialize colorama
init(autoreset=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Read configuration
config = configparser.ConfigParser()
try:
    with open("Config.ini", "r") as conf_file:
        config.read_file(conf_file)
except Exception as e:
    logging.error("Failed to read Config.ini: %s", e)
    sys.exit(1)

# Get config values with error checking
try:
    cookie = config.get("auth", "cookie")
    group = config.get("clothing", "group")
    description = config.get("clothing", "description")
    priceconfig = config.getint("clothing", "price")
    ratelimz = config.getint("optional", "ratelimitwaitseconds")
    maxrobux = config.getint("optional", "maxrobuxtospend")
    debugmode = config.getboolean("optional", "debugmode")
except Exception as e:
    logging.error("Error reading configuration values: %s", e)
    sys.exit(1)

# Get current working directory and build folder paths
path = os.getcwd()
shirt_png = os.path.join(path, "Storage", "Clothes", "Shirts")
pant_png = os.path.join(path, "Storage", "Clothes", "Pants")
error_File = os.path.join(path, "Storage", "Clothes", "FileCausedError")

# Ensure directories exist (create them if needed)
for dir_path in [shirt_png, pant_png, error_File]:
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            logging.info("Created missing directory: %s", dir_path)
        except Exception as e:
            logging.error("Failed to create directory %s: %s", dir_path, e)
            sys.exit(1)

# Set up headers and session
headers = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Origin": "https://create.roblox.com",
    "Referer": "https://create.roblox.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}
url = "https://apis.roblox.com/assets/user-auth/v1/assets"
session = requests.Session()
session.cookies[".ROBLOSECURITY"] = cookie

# Get CSRF token
try:
    csrf_request = session.post("https://auth.roblox.com/v1/logout", headers=headers)
    csrf_token = csrf_request.headers.get("x-csrf-token")
    if not csrf_token:
        raise Exception("No CSRF token returned")
    headers["x-csrf-token"] = csrf_token
except Exception as e:
    logging.error("Failed to fetch CSRF token: %s", e)
    sys.exit(1)

# Authenticate the user
try:
    auth_response = session.get("https://users.roblox.com/v1/users/authenticated", headers=headers)
    auth_response.raise_for_status()
    user_data = auth_response.json()
    user_name = user_data.get('name', 'Unknown')
    logging.info(f"{Back.CYAN}{Fore.BLACK}[Authentication]{Back.BLACK}{Fore.WHITE} Logged in as {user_name}")
except Exception as e:
    logging.error("Authentication failed: %s", e)
    print(f"{Back.RED}{Fore.BLACK}[Error]{Back.BLACK}{Fore.WHITE} Your cookie is invalid.")
    input("Press Enter to exit...")
    sys.exit(1)

# Fetch currency (Robux)
try:
    currency_response = session.get("https://economy.roblox.com/v1/user/currency", headers=headers)
    currency_response.raise_for_status()
    currency_data = currency_response.json()
    brokie = currency_data.get("robux", 0)
    logging.info(f"{Back.CYAN}{Fore.BLACK}[Robux]{Back.BLACK}{Fore.WHITE} Remaining: R$ {brokie}\n")
except Exception as e:
    logging.error("Failed to fetch currency: %s", e)
    sys.exit(1)

# Ask the user for clothing type selection
try:
    choice = int(input("""
=========================
CLOTHING SELECTION
=========================
[1] Shirts 👕
[2] Pants 👖
-------------------------
Enter your choice: """))
    if choice not in [1, 2]:
        raise ValueError("Invalid choice. Please select either 1 or 2.")
except Exception as e:
    logging.error("Invalid input: %s", e)
    print("Wrong Input, exiting...")
    sys.exit(1)

shirt = True if choice == 1 else False

# Function to check operation status (for future use)
def operation_status(operation_id):
    operation_url = f"https://apis.roblox.com/assets/user-auth/v1/operations/{operation_id}"
    try:
        response = session.get(operation_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error("Failed to check operation status for %s: %s", operation_id, e)
        return None

# Validate an image file
def validate_image(image_path):
    try:
        with Image.open(image_path) as img:
            if img.size != (585, 559):
                return None, f"Template size is {img.size}, must be 585 x 559 pixels."
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG', optimize=False)
            img_byte_arr.seek(0)
            return img_byte_arr.read(), "Image validated and converted successfully."
    except Exception as e:
        return None, f"Error processing image: {e}"

# Remove emojis from a given text
def remove_emojis(text):
    try:
        emoji_pattern = re.compile("[\U00010000-\U0010FFFF]", flags=re.UNICODE)
        return emoji_pattern.sub("", text)
    except Exception as e:
        logging.error("Error removing emojis from text '%s': %s", text, e)
        return text  # Return original text if error occurs

# Main loop for processing and uploading files
robuxspent = 0
while True:
    if robuxspent > maxrobux:
        logging.info("Total money limit reached. Exiting...")
        break

    # Base configuration data for the upload request
    config_data = {
        "displayName": "",
        "description": description,
        "assetType": "Shirt" if shirt else "Pants",
        "creationContext": {
            "creator": {
                "groupId": group
            },
            "expectedPrice": priceconfig
        }
    }

    try:
        folderpath = shirt_png if shirt else pant_png
        files_found = [f for f in os.listdir(folderpath) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not files_found:
            logging.info("No image files found in folder: %s", folderpath)
            break  # Exit if no files to process
        
        for file in files_found:
            tempPath = os.path.join(folderpath, file)
            data, message = validate_image(tempPath)
            if data is None:
                logging.error("Image validation failed for %s: %s", file, message)
                try:
                    target_error_path = os.path.join(error_File, file)
                    shutil.move(tempPath, target_error_path)
                    logging.info("Moved %s to error folder: %s", file, target_error_path)
                except Exception as move_err:
                    logging.error("Failed to move file %s to error folder: %s", file, move_err)
                continue  # Skip to next file
            
            # Process file name: Remove extension, replace underscores with spaces, and remove emojis
            display_name = os.path.splitext(file)[0]   # Removes .png, .jpg, etc.
            display_name = display_name.replace("_", " ")  # Replace underscores with spaces
            display_name = remove_emojis(display_name)  # Remove any emojis
            config_data["displayName"] = display_name
            
            files_payload = {
                "fileContent": (display_name, data, "image/png"),
                "request": (None, json.dumps(config_data), "application/json")
            }
            
            logging.info("Sending upload request for file: %s", file)
            try:
                response = session.post(url, headers=headers, files=files_payload)
                logging.info("Response Headers: %s", response.headers)
                logging.info("Status Code: %s", response.status_code)
                logging.info("Response: %s", response.text)
            except Exception as req_err:
                logging.error("Request failed for file %s: %s", file, req_err)
                continue  # Skip this file
            
            robuxspent += priceconfig
            
            if response.status_code != 200:
                logging.error("Upload failed for file %s. Moving to error folder.", file)
                try:
                    target_error_path = os.path.join(error_File, file)
                    shutil.move(tempPath, target_error_path)
                    logging.info("Moved %s to error folder: %s", file, target_error_path)
                except Exception as move_err:
                    logging.error("Failed to move file %s to error folder: %s", file, move_err)
            else:
                try:
                    os.remove(tempPath)
                    logging.info("File %s uploaded and removed successfully.", file)
                except Exception as remove_err:
                    logging.error("Failed to remove file %s: %s", file, remove_err)
            
            time.sleep(ratelimz)
    except Exception as e:
        logging.error("An unexpected error occurred in the main loop: %s", e)
        break

logging.info("Exiting program.")
