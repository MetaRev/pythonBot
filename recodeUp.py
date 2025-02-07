try:
    import time
    import colorama
    import requests
    import time
    import re
    import configparser
    config = configparser.ConfigParser()
    config.read_file(open(r"Config.ini"))
    import os
    import shutil
    from colorama import init, Fore, Back, Style
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

session = requests.session()
session.cookies[".ROBLOSECURITY"] = cookie

headers = {
    "Content-Type": "application/json;charset=UTF-8"
}

csrf_token = ""

try:
    initial_request = session.post(
        url="https://auth.roblox.com/v1/logout", 
        headers=headers
    )
    if "X-CSRF-Token" in initial_request.headers:
        csrf_token = initial_request.headers["X-CSRF-Token"]
        headers["X-CSRF-Token"] = csrf_token
    else:
        raise Exception("Failed to retrieve CSRF token.")
except Exception as e:
    print(f"Error fetching CSRF token: {e}")
    input()
    
try:
    getuser = session.get("https://users.roblox.com/v1/users/authenticated", headers=headers)
    getuser.raise_for_status()  
    user_data = getuser.json()
    user_id = user_data['id']
    user_name = user_data['name']
    print(f"Logged in as {user_name}\n")
except Exception as e:
    print(f"Your cookie is invalid or authentication failed: {e}")
    input()
    
robux = session.get("https://economy.roblox.com/v1/user/currency")
robux = robux.json()
robux = robux["robux"]

print(f"Remaining: R$ {robux}\n")

Shirt = False
holder = input("type [Y] for Shirt, [N] for Pants: ")

if(holder.lower() == "y"):
    Shirt = True
elif(holder.lower() == "n"):
    Shirt = False
else:
    print("Invalid input, exiting")
    exit()

assetid = "1"
robuxspent = 0

def upload():
    global group,description,priceconfig, name,creator,creatortype, pants,assetid, robuxspent, maxrobux
    
    try:
        if(Shirt):
            newPath = f"{path}\\Storage\\Clothes\\Shirts"
            link = "https://itemconfiguration.roblox.com/v1/avatar-assets/11/upload"
        else:
            newPath = f"{path}\\Storage\\Clothes\\Pants"
            link = "https://itemconfiguration.roblox.com/v1/avatar-assets/12/upload"
            
        name = os.listdir(newPath)[0]
        name = name.split(".")
        name = name[0]
        
        source_file = fr"{newPath}\\{os.listdir(newPath)[0]}"
        error_folder = fr"{path}\\Storage\\FileCausedError"
        
        creator = group
        creatortype = "Group"
        
    except:
        print("All clothes have been uploaded")
        return
    
    json = open("Storage\Json\config.json","w")
    json.write(f"""{{"name":"{name}","description":"{description}","creatorTargetId":"{creator}","creatorType":"{creatortype}"}}""")
    json.close()
    
    files = {
        'media': open(fr"{newPath}\\{os.listdir(newPath)[0]}", 'rb'),
        'config': open('Storage\Json\config.json', 'rb')
        }
    
    s = session.post(link,files=files)
    
    if debugmode == True:
        print(f"Status: {s.status_code}\nResponse: {s.text}")
        
    files["media"].close()
    sd = s.json()
    
    try:
        assetid = sd['assetId']
    except:
        code = sd['errors'][0]['code']
        if code == 16:
            print(f"{Back.RED}{Fore.BLACK}[Fail]{Back.BLACK}{Fore.WHITE} Clothing name not allowed or invalid description, removing from list: {name}")
            files["media"].close()
            shutil.move(source_file, error_folder)
            upload()
            return
        elif code == 11:
            print(f"{Back.RED}{Fore.BLACK}[Fail]{Back.BLACK}{Fore.WHITE} Clothing name not allowed or invalid description, removing from list: {name}")
            files["media"].close()
            shutil.move(source_file, error_folder)
            upload()
            return
        elif code == 8:
            print(f"{Back.RED}{Fore.BLACK}[Fail]{Back.BLACK}{Fore.WHITE} Invalid file type extension, removing from list: {name}")
            files["media"].close()
            shutil.move(source_file, error_folder)
            upload()
            return
        elif code == 0:
            print(f"{Back.RED}{Fore.BLACK}[Fail]{Back.BLACK}{Fore.WHITE} Ratelimited, failed to upload (waiting {ratelimz}s): {name}\n")
            time.sleep(ratelimz)
            upload()
            return
        elif code == 6:
            print(f"{Back.RED}{Fore.BLACK}[Robux]{Back.BLACK}{Fore.WHITE} You don't have 10 robux to upload: {name}")
            input()
        elif code == 7:
            print(f"{Back.RED}{Fore.BLACK}[Fail]{Back.BLACK}{Fore.WHITE} Invalid template, removing from list: {name}")
            files["media"].close()
            shutil.move(source_file, error_folder)
            upload()
            return
        elif code == 9:
            print(f"{Back.RED}{Fore.BLACK}[Fail]{Back.BLACK}{Fore.WHITE} You do not have permission to upload to the group")
            upload()
            return
        
    pricefiles = {"price":priceconfig,"priceConfiguration":{"priceInRobux":priceconfig},"saleStatus":"OnSale"}
    priceupdate = f"https://itemconfiguration.roblox.com/v1/assets/{assetid}/release"
    price = session.post(priceupdate,json=pricefiles)
    
    if pants == False:
        if s.status_code == 200:
            print(f"{Back.GREEN}{Fore.BLACK}[Upload]{Back.BLACK}{Fore.WHITE} Successfully uploaded a shirt: {name}")
            robuxspent+=10
            os.remove(fr"{newPath}\\{os.listdir(newPath)[0]}")
        else:
            print(f"{Back.RED}{Fore.BLACK}[Fail]{Back.BLACK}{Fore.WHITE} Failed to upload a shirt: {name}")
    else:
        if s.status_code == 200:
            print(f"{Back.GREEN}{Fore.BLACK}[Upload]{Back.BLACK}{Fore.WHITE} Successfully uploaded pants: {name}")
            robuxspent+=10
            os.remove(fr"{newPath}\\{os.listdir(newPath)[0]}")
        else:
            print(f"{Back.RED}{Fore.BLACK}[Fail]{Back.BLACK}{Fore.WHITE} Failed to upload pants: {name}")
            
    if price.status_code == 200:
        print(f"{Back.GREEN}{Fore.BLACK}[Upload]{Back.BLACK}{Fore.WHITE} Successfully set price to R$ {priceconfig}")
    else:
        print(f"{Back.RED}{Fore.BLACK}[Fail]{Back.BLACK}{Fore.WHITE} Failed to set a price: {name}")
        
    robux = session.get("https://economy.roblox.com/v1/user/currency")
    robux = robux.json()
    robux = robux["robux"]

    print(f"Remaining: R$ {robux}\n")
    
upload()