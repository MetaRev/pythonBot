try:
    import time
    import colorama
    import requests
    import time
    import re
    import configparser
    from cleantext import clean
    config = configparser.ConfigParser()
    config.read_file(open(r"Config.ini"))
    import os
    from colorama import init, Fore, Back, Style
    import json
    import os
    from PIL import Image
    import io
    init()
except ImportError:
    print("[ERROR] Failed to import some modules, make sure to run requirements.bat, delete all other python versions and install python 3.10.0 installed with add to path option checked during installation")
    input()
    
cookie = str(config.get("auth","cookie"))
group = str(config.get("clothing","group"))
description = str(config.get("clothing","description"))
priceconfig = int(config.get("clothing","price"))
ratelimz = int(config.get("optional","ratelimitwaitseconds"))
maxrobux = int(config.get("optional","maxrobuxtospend"))
debugmode = config.getboolean('optional', 'debugmode') 

path = os.getcwd()

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
    
try:
    getuser = session.get("https://users.roblox.com/v1/users/authenticated")
    getuser2 = getuser.json()
    getuser3 = getuser2['id']
    getuser4 = getuser2['name']
    print(f"{Back.CYAN}{Fore.BLACK}[Authentication]{Back.BLACK}{Fore.WHITE} Logged in as {getuser4}")
except:
    print(f"{Back.RED}{Fore.BLACK}[Error]{Back.BLACK}{Fore.WHITE} Your cookie is invalid")
    print(f"{Back.YELLOW}{Fore.BLACK}[Info]{Back.BLACK}{Fore.WHITE} Please restart the program, with a valid cookie")
    input()

brokie = session.get("https://economy.roblox.com/v1/user/currency")
brokie = brokie.json()
brokie=brokie["robux"]
print(f"{Back.CYAN}{Fore.BLACK}[Robux]{Back.BLACK}{Fore.WHITE} Remaining: R$ {brokie}")
print("\n")
robuxspent = 0

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


def check_operation_status(operation_id):
    operation_url = f"https://apis.roblox.com/assets/user-auth/v1/operations/{operation_id}"
    try:
        response = session.get(operation_url, headers=headers)
        return response.json()
    except Exception as e:
        print(f"[ERROR] Failed to check operation status: {e}")
        return None
    
def Upload_clothng(folderpath, assetType):
    operation_url2 = f"https://apis.roblox.com/assets/user-auth/v1/assets"
    
    config_data = {
        "displayName": "cute_christmas_croptop",
        "description": description,
        "assetType": assetType,
        "creationContext": {
            "creator": {
                "groupId": group
            },
            "expectedPrice": priceconfig
        }
    }
    
    brokie = session.get("https://economy.roblox.com/v1/user/currency")
    brokie = brokie.json()
    brokie=brokie["robux"]
    print(f"{Back.CYAN}{Fore.BLACK}[Robux]{Back.BLACK}{Fore.WHITE} Remaining: R$ {brokie}")

    try:
        if robuxspent <= maxrobux:
            for file in os.listdir(folderpath):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):  
                    tempPath = folderpath + "\\" + file
                    data = validate_and_convert_image(tempPath)
                    print(data[1])
                    config_data["displayName"] = file
                    print(config_data["displayName"])
        else:
            print("Total Money Reached")
            exit()
        
    except:
        pass

def main(): 
    shirt_png = f"{path}\\Storage\\Clothes\\Shirts"
    pant_png = f"{path}\\Storage\\Clothes\\Pants"
    
    if not os.path.exists(shirt_png) or not os.path.exists(pant_png):
        print(f"[ERROR] File not found")
        exit()
    
    while True:
        try:
            print("\n1. Upload Shirts")
            print("2. Upload Pants")
            print("3. Exit")
            choice = input("Select option (1-3): ")

            base_path = os.path.join(os.getcwd(), "Storage", "Clothes")

            if choice == "1":
                print("\nProcessing Shirts...")
                Upload_clothng(shirt_png, "Shirt")
                #process_folder(uploader, folder_path, "Shirt", group, price, description, max_robux)
            elif choice == "2":
                print("\nProcessing Pants...")
                #process_folder(uploader, folder_path, "Pants", group, price, description, max_robux)
            elif choice == "3":
                print("Exiting...")
                break
            else:
                print("Invalid option. Please select 1-3")
                
        except Exception as e:
            print(f"Main loop error: {str(e)}")
            time.sleep(2)

main()