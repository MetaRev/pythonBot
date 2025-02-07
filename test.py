import requests
import configparser
import json
import os
import time
from PIL import Image
import io

def validate_and_convert_image(image_path):
    try:
        with Image.open(image_path) as img:
            if img.size != (585, 559):
                return None, f"Template size is {img.size}, must be 585 x 559 pixels"
            
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG', optimize=False)
            img_byte_arr.seek(0)
            return img_byte_arr.read(), "Image validated and converted successfully"
            
    except Exception as e:
        return None, f"Error processing image: {e}"

config = configparser.ConfigParser()
try:
    config.read_file(open(r"Config.ini"))
    cookie = config.get("auth", "cookie", fallback="")
    if not cookie:
        raise ValueError("[ERROR] No .ROBLOSECURITY cookie found in Config.ini")
except Exception as e:
    print(f"[ERROR] Failed to read config file: {e}")
    exit()

url = "https://apis.roblox.com/assets/user-auth/v1/assets"
session = requests.Session()
session.cookies[".ROBLOSECURITY"] = cookie
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0"
}

try:
    csrf_request = session.post("https://auth.roblox.com/v1/logout", headers=headers)
    csrf_token = csrf_request.headers.get("x-csrf-token")
    if not csrf_token:
        raise Exception("[ERROR] Failed to fetch CSRF token.")
    headers["x-csrf-token"] = csrf_token
except Exception as e:
    print(f"[ERROR] Failed to fetch CSRF token: {e}")
    exit()

png_file_path = r"C:\Users\asus\OneDrive\Desktop\Open source\python\project\Storage\Clothes\Shirts\Christmas.png"

if not os.path.exists(png_file_path):
    print(f"[ERROR] File not found: {png_file_path}")
    exit()

config_data = {
    "displayName": "cute_christmas_croptop",
    "description": "Shirt",
    "assetType": "Shirt",
    "creationContext": {
        "creator": {
            "groupId": 13175463
        },
        "expectedPrice": 10
    }
}

def check_operation_status(operation_id):
    operation_url = f"https://apis.roblox.com/assets/user-auth/v1/operations/{operation_id}"
    try:
        response = session.get(operation_url, headers=headers)
        return response.json()
    except Exception as e:
        print(f"[ERROR] Failed to check operation status: {e}")
        return None

try:
    image_bytes, message = validate_and_convert_image(png_file_path)
    if not image_bytes:
        print(f"[ERROR] {message}")
        exit()
    
    print("Image validation passed - proceeding with upload")
    
    files = {
        "fileContent": ("Christmas.png", image_bytes, "image/png"),
        "request": (None, json.dumps(config_data), "application/json")
    }
    
    headers["Content-Length"] = str(len(image_bytes))
    
    try:

        print("Sending upload request...")
        response = session.post(url, headers=headers, files=files)
        
        print("\nResponse Headers:", dict(response.headers))
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                operation_id = response_data.get('operationId')
                
                if operation_id:
                    print(f"\nOperation ID received: {operation_id}")
                    print("Checking operation status...")
                    
                    max_attempts = 10
                    attempt = 0
                    while attempt < max_attempts:
                        status_response = check_operation_status(operation_id)
                        
                        if status_response:
                            print(f"\nOperation Status (Attempt {attempt + 1}):")
                            print(json.dumps(status_response, indent=2))
                            
                            # Check if operation is complete
                            if status_response.get('done'):
                                print("\nOperation completed!")
                                break
                        
                        attempt += 1
                        if attempt < max_attempts:
                            print("Waiting 5 seconds before next check...")
                            time.sleep(5)
                    
                    if attempt >= max_attempts:
                        print("\n[WARNING] Maximum polling attempts reached")
                else:
                    print("[ERROR] No operation ID in response")
            except json.JSONDecodeError:
                print("[ERROR] Failed to parse response JSON")
        elif response.status_code == 500:
            print("\nTrying to get more error details...")
            try:
                error_json = response.json()
                print("Detailed error:", json.dumps(error_json, indent=2))
            except:
                print("Could not parse error response as JSON")
                
    except Exception as e:
        print(f"[ERROR] Failed to make the POST request: {e}")
        
except Exception as e:
    print(f"[ERROR] Failed to process the file: {e}")