try:
    import requests
    import requests, re, time, os
    from colorama import init
    import emoji
    from PIL import Image
    import configparser
    config = configparser.ConfigParser()
    config.read_file(open(r"Config.ini"))
    import FunctionToGetIds as idGetter
    init()
except:
    print("Run Requirements.bat to install all required modules.")
    input()
    
path = os.getcwd()

os.makedirs("Storage/Clothes/Shirts", exist_ok=True)
os.makedirs("Storage/Clothes/Pants", exist_ok=True)

config = configparser.ConfigParser()
config.read_file(open(r"Config.ini"))
cookie = str(config.get("auth", "cookie"))

r = requests.session()
r.cookies[".ROBLOSECURITY"] = cookie

headers = {
    "Content-Type": "application/json;charset=UTF-8"
}

csrf_token = ""
try:
    initial_request = r.post(
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
    getuser = r.get("https://users.roblox.com/v1/users/authenticated", headers=headers)
    getuser.raise_for_status()  
    user_data = getuser.json()
    user_id = user_data['id']
    user_name = user_data['name']
    print(f"Logged in as {user_name}\n")
except Exception as e:
    print(f"Your cookie is invalid or authentication failed: {e}")
    input()

try:
    listId, cltype = idGetter.getIds(requests, r)
except Exception as e:
    print(f"Error fetching item IDs: {e}")
    listId = []

def remove_emoji_and_symbols(string):
    string = emoji.replace_emoji(string, replace='')
    
    symbol_pattern = re.compile(r"[^\w\s.,!?']+")  
    return symbol_pattern.sub('', string)

amount = 0
for i in listId:
    try:
        rx = requests.get(
            re.findall(
                r'<url>(.+?)(?=</url>)',
                requests.get(f'https://assetdelivery.roblox.com/v1/asset?id={i}')
                .text.replace('http://www.roblox.com/asset/?id=', 'https://assetdelivery.roblox.com/v1/asset?id='),
            )[0]
        ).content

        url = "https://catalog.roblox.com/v1/catalog/items/details"
        data = {"items": [{"id": i, "itemType": "asset"}]}
        response = r.post(url, json=data, headers=headers)
        response.raise_for_status()
        item_data = response.json()

        if 'data' in item_data and len(item_data['data']) > 0:
            item_name = remove_emoji_and_symbols(item_data['data'][0]['name'])
            print(f"Item ID: {i} -> Name: {item_name}")
        else:
            print(f"Item ID: {i} -> No data found.")
            continue 

        b = item_name.replace(' ', '_')
        if len(rx) >= 7500:
            print(f'Downloaded: {amount}')

            sanitized_name = re.sub(r'[^\w]', ' ', item_name) 
            file_path = f'Storage/Clothes/Shirts/{sanitized_name}.png'

            if cltype == "Shirts":
                with open(file_path, 'wb') as f:
                    f.write(rx)
                
                try:
                    img1 = Image.open(file_path)
                    img2 = Image.open("Storage/Json/shirt.png")
                    img1.paste(img2, (0, 0), mask=img2)
                    img1.save(file_path)
                except Exception as e:
                    print(f"Error processing image for {file_path}: {e}")

            elif cltype == "Pants":
                file_path = f'Storage/Clothes/Pants/{sanitized_name}.png'
                with open(file_path, 'wb') as f:
                    f.write(rx)
                
                try:
                    img1 = Image.open(file_path)
                    img2 = Image.open("Storage/Json/pants.png")
                    img1.paste(img2, (0, 0), mask=img2)
                    img1.save(file_path)
                except Exception as e:
                    print(f"Error processing image for {file_path}: {e}")

            amount += 1
            time.sleep(10)


    except Exception as e:
        print(f"Error processing item ID {i}: {e}")

else:
    print(f"Completed, downloaded {amount} clothes.")
