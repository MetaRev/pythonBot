import requests
import json
import time
from PIL import Image
import io
import os
from colorama import init, Fore, Back, Style
import configparser
from cleantext import clean

init()

def debug_response(response, context=""):
    """Debug helper to print detailed response information"""
    print(f"\n{Back.YELLOW}{Fore.BLACK}[Debug]{Back.BLACK}{Fore.WHITE} {context}")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    try:
        print(f"Response: {response.text}")
    except:
        print("Could not get response text")
    print()

def debug_request(method, url, headers=None, data=None, files=None):
    """Debug helper to print request information"""
    print(f"\n{Back.YELLOW}{Fore.BLACK}[Debug]{Back.BLACK}{Fore.WHITE} Making {method} request to {url}")
    if headers:
        print(f"Headers: {headers}")
    if data:
        print(f"Data: {data}")
    if files:
        print(f"Files: {list(files.keys())}")
    print()

class RobloxUploader:
    def __init__(self, cookie, headers=None):
        self.session = requests.Session()
        self.session.cookies[".ROBLOSECURITY"] = cookie

        # Debug cookie
        print(f"\n{Back.YELLOW}{Fore.BLACK}[Debug]{Back.BLACK}{Fore.WHITE} Cookie set:")
        print(f"Cookie length: {len(cookie)}")
        print(f"Session cookies: {dict(self.session.cookies)}\n")

        self.headers = headers or {
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Origin": "https://create.roblox.com",
            "Referer": "https://create.roblox.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.robux_spent = 0
        self._refresh_csrf()

    def _refresh_csrf(self):
        try:
            debug_request("POST", "https://auth.roblox.com/v1/logout", self.headers)

            csrf_request = self.session.post(
                "https://auth.roblox.com/v1/logout",
                headers=self.headers
            )

            debug_response(csrf_request, "CSRF Request")

            csrf_token = csrf_request.headers.get("x-csrf-token")
            if csrf_token:
                self.headers["x-csrf-token"] = csrf_token
                print(f"{Back.GREEN}{Fore.BLACK}[Debug]{Back.BLACK}{Fore.WHITE} Got CSRF token: {csrf_token}")
            else:
                print(f"{Back.RED}{Fore.BLACK}[Debug]{Back.BLACK}{Fore.WHITE} No CSRF token in response")
            return csrf_token
        except Exception as e:
            print(f"{Back.RED}{Fore.BLACK}[Debug]{Back.BLACK}{Fore.WHITE} CSRF Error: {str(e)}")
            raise Exception(f"Failed to fetch CSRF token: {e}")

    def _ensure_csrf(self):
        """Ensure the CSRF token is valid by refreshing it if necessary."""
        try:
            debug_request("GET", "https://auth.roblox.com/v1/authentication-context", self.headers)
            response = self.session.get("https://auth.roblox.com/v1/authentication-context", headers=self.headers)
            debug_response(response, "Ensure CSRF Token")

            if response.status_code == 403:
                print(f"{Back.YELLOW}{Fore.BLACK}[Info]{Back.BLACK}{Fore.WHITE} Refreshing CSRF token...")
                self._refresh_csrf()
        except Exception as e:
            print(f"{Back.RED}{Fore.BLACK}[Debug]{Back.BLACK}{Fore.WHITE} Failed to ensure CSRF token: {str(e)}")

    def get_robux_balance(self):
        try:
            self._ensure_csrf()
            debug_request("GET", "https://economy.roblox.com/v1/user/currency", self.headers)
            response = self.session.get("https://economy.roblox.com/v1/user/currency")
            debug_response(response, "Robux Balance Check")
            return response.json()["robux"]
        except Exception as e:
            print(f"{Back.RED}{Fore.BLACK}[Error]{Back.BLACK}{Fore.WHITE} Failed to get Robux balance: {e}")
            return 0

    def upload_asset(self, image_path, config_data, max_retries=3):
        image_data, message = self._validate_image(image_path)
        if not image_data:
            raise ValueError(message)

        files = {
            'request': ('request.json', json.dumps(config_data), 'application/json; charset=utf-8'),
            'fileContent': ('image.png', image_data, 'image/png')
        }

        for attempt in range(max_retries):
            try:
                self._ensure_csrf()

                debug_request("POST", "https://apis.roblox.com/assets/user-auth/v1/assets", 
                            self.headers, config_data, files)

                response = self.session.post(
                    "https://apis.roblox.com/assets/user-auth/v1/assets",
                    files=files,
                    headers=self.headers
                )

                debug_response(response, "Upload Asset Response")

                if response.status_code == 429:
                    print(f"{Back.YELLOW}{Fore.BLACK}[Wait]{Back.BLACK}{Fore.WHITE} Rate limited, waiting 30s")
                    time.sleep(30)
                    continue

                if response.status_code != 200:
                    print(f"{Back.RED}{Fore.BLACK}[Error]{Back.BLACK}{Fore.WHITE} Upload failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    continue

                operation_id = response.json().get('operationId')
                if not operation_id:
                    print(f"{Back.RED}{Fore.BLACK}[Debug]{Back.BLACK}{Fore.WHITE} No operation ID in response")
                    continue

                status = self._monitor_operation(operation_id)
                if status.get('done') and 'response' in status:
                    self.robux_spent += 10
                    return status['response']

            except requests.exceptions.RequestException as e:
                print(f"{Back.RED}{Fore.BLACK}[Debug]{Back.BLACK}{Fore.WHITE} Request failed: {str(e)}")
                print(f"Attempt {attempt + 1} of {max_retries}")
                if attempt == max_retries - 1:
                    raise

            time.sleep(5)

        raise Exception("Upload failed after maximum retries")

    def _monitor_operation(self, operation_id, timeout=300):
        debug_request("GET", f"https://apis.roblox.com/assets/user-auth/v1/operations/{operation_id}", 
                     self.headers)

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(
                    f"https://apis.roblox.com/assets/user-auth/v1/operations/{operation_id}",
                    headers=self.headers
                )

                debug_response(response, "Operation Status Check")

                status = response.json()
                if status.get('done'):
                    return status

                time.sleep(2)
            except Exception as e:
                print(f"{Back.RED}{Fore.BLACK}[Debug]{Back.BLACK}{Fore.WHITE} Status check failed: {str(e)}")
                time.sleep(5)

        raise TimeoutError("Operation monitoring timed out")

    def _validate_image(self, image_path):
        try:
            with Image.open(image_path) as img:
                if img.size != (585, 559):
                    return None, f"Invalid template size: {img.size}, required: 585x559"

                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG', optimize=False)
                img_byte_arr.seek(0)
                return img_byte_arr.read(), "Success"

        except Exception as e:
            return None, f"Image processing error: {e}"

def move_to_error_folder(file_path):
    """Move failed files to an error folder"""
    error_folder = os.path.join(os.path.dirname(os.path.dirname(file_path)), "FileCausedError")
    os.makedirs(error_folder, exist_ok=True)
    new_path = os.path.join(error_folder, os.path.basename(file_path))
    os.rename(file_path, new_path)
    print(f"{Back.YELLOW}{Fore.BLACK}[Move]{Back.BLACK}{Fore.WHITE} Moved failed file to error folder")

def process_folder(uploader, folder_path, asset_type, group_id, price, description, max_robux):
    while True:
        try:
            if uploader.robux_spent >= max_robux:
                print(f"{Back.RED}{Fore.BLACK}[Limit]{Back.BLACK}{Fore.WHITE} Max Robux spend reached (R${max_robux})")
                return

            files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
            if not files:
                print(f"{Back.MAGENTA}{Fore.BLACK}[Done]{Back.BLACK}{Fore.WHITE} No more files to process in {folder_path}")
                return

            for file_name in files:
                file_path = os.path.join(folder_path, file_name)
                display_name = clean(os.path.splitext(file_name)[0], no_emoji=True)

                config_data = {
                    "displayName": display_name,
                    "description": description,
                    "assetType": asset_type,
                    "creationContext": {
                        "creator": {
                            "groupId": group_id
                        },
                        "expectedPrice": price
                    }
                }

                try:
                    print(f"{Back.CYAN}{Fore.BLACK}[Upload]{Back.BLACK}{Fore.WHITE} Processing: {display_name}")
                    result = uploader.upload_asset(file_path, config_data)
                    print(f"{Back.GREEN}{Fore.BLACK}[Success]{Back.BLACK}{Fore.WHITE} Uploaded: {display_name}")
                    
                    os.remove(file_path)
                    
                    balance = uploader.get_robux_balance()
                    print(f"{Back.CYAN}{Fore.BLACK}[Robux]{Back.BLACK}{Fore.WHITE} Remaining: R${balance}\n")
                    
                    time.sleep(5)

                except Exception as e:
                    print(f"{Back.RED}{Fore.BLACK}[Fail]{Back.BLACK}{Fore.WHITE} Failed to upload {display_name}: {e}")
                    move_to_error_folder(file_path)
                    time.sleep(5)

        except Exception as e:
            print(f"{Back.RED}{Fore.BLACK}[Error]{Back.BLACK}{Fore.WHITE} Folder processing error: {e}")
            time.sleep(5)

def main():
    config = configparser.ConfigParser()
    config.read("Config.ini")

    cookie = config.get("auth", "cookie")
    group = config.get("clothing", "group")
    description = config.get("clothing", "description")
    price = int(config.get("clothing", "price"))
    max_robux = int(config.get("optional", "maxrobuxtospend"))

    uploader = RobloxUploader(cookie)

    try:
        debug_request("GET", "https://users.roblox.com/v1/users/authenticated", uploader.headers)
        response = uploader.session.get("https://users.roblox.com/v1/users/authenticated")
        debug_response(response, "Authentication Check")
        
        user_data = response.json()
        print(f"{Back.CYAN}{Fore.BLACK}[Auth]{Back.BLACK}{Fore.WHITE} Logged in as {user_data['name']}")
        
        balance = uploader.get_robux_balance()
        print(f"{Back.CYAN}{Fore.BLACK}[Robux]{Back.BLACK}{Fore.WHITE} Balance: R${balance}\n")
    except Exception as e:
        print(f"{Back.RED}{Fore.BLACK}[Error]{Back.BLACK}{Fore.WHITE} Authentication failed: {e}")
        return

    while True:
        try:
            print("\n1. Upload Shirts")
            print("2. Upload Pants")
            print("3. Exit")
            choice = input("Select option (1-3): ")

            base_path = os.path.join(os.getcwd(), "Storage", "Clothes")

            if choice == "1":
                print("\nProcessing Shirts...")
                folder_path = os.path.join(base_path, "Shirts")
                process_folder(uploader, folder_path, "Shirt", group, price, description, max_robux)
            elif choice == "2":
                print("\nProcessing Pants...")
                folder_path = os.path.join(base_path, "Pants")
                process_folder(uploader, folder_path, "Pants", group, price, description, max_robux)
            elif choice == "3":
                print("Exiting...")
                break
            else:
                print("Invalid option. Please select 1-3")
                
        except Exception as e:
            print(f"Main loop error: {str(e)}")
            time.sleep(2)

if __name__ == "__main__":
    main()