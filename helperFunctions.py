def getIds(requests, session):
    r = session
    print("Choose what type of clothing you would like to download\n")
    print("Clothing\n- Shirts (s)\n- Pants (p)")
    b = input("Enter type (s/p): ")
    cltype = ""
    if b.lower() == "shirts" or b.lower() == "shirt" or b.lower() == "s":
        cltype = "Shirts"
    elif b.lower() == "pants" or  b.lower() == "pant" or b.lower() == "p":
        cltype = "Pants"
    else:
        print("Invalid input, restart program.")
        input()
    print(f"Selected: {cltype}")

    print("\n")
    print("Keywords example\n- emo goth y2k\n- slender black dark")
    ab = input("Enter keywords: ")
    ab = ab.strip()
    ab = ab.replace(" ","+")
    ab = ab.lower()

    print("\n")
    friendslist = []
    nextpagecursor = ""
    relevance = f"https://catalog.roblox.com/v1/search/items?category=Clothing&keyword={ab}&limit=120&maxPrice=5&minPrice=5&salesTypeFilter=1&subcategory=Classic{cltype}"

    favouritedalltime = f"https://catalog.roblox.com/v1/search/items?category=Clothing&keyword={ab}&limit=120&maxPrice=5&minPrice=5&salesTypeFilter=1&sortAggregation=5&sortType=1&subcategory=Classic{cltype}"
    favouritedallweek = f"https://catalog.roblox.com/v1/search/items?category=Clothing&keyword={ab}&limit=120&maxPrice=5&minPrice=5&salesTypeFilter=1&sortAggregation=3&sortType=1&subcategory=Classic{cltype}"
    favouritedallday = f"https://catalog.roblox.com/v1/search/items?category=Clothing&keyword={ab}&limit=120&maxPrice=5&minPrice=5&salesTypeFilter=1&sortAggregation=5&sortType=1&subcategory=Classic{cltype}"

    bestsellingalltime = f"https://catalog.roblox.com/v1/search/items?category=Clothing&keyword={ab}&limit=120&maxPrice=5&minPrice=5&salesTypeFilter=1&sortAggregation=5&sortType=2&subcategory=Classic{cltype}"
    bestsellingweek= f"https://catalog.roblox.com/v1/search/items?category=Clothing&keyword={ab}&limit=120&maxPrice=5&minPrice=5&salesTypeFilter=1&sortAggregation=3&sortType=2&subcategory=Classic{cltype}"
    bestsellingday = f"https://catalog.roblox.com/v1/search/items?category=Clothing&keyword={ab}&limit=120&maxPrice=5&minPrice=5&salesTypeFilter=1&sortAggregation=1&sortType=1&subcategory=Classic{cltype}"

    recentlyupdated = f"https://catalog.roblox.com/v1/search/items?category=Clothing&keyword={ab}&limit=120&maxPrice=5&minPrice=5&salesTypeFilter=1&sortType=3&subcategory=Classic{cltype}"



    print("Catalog Sorts\n-[1] Relevance\n\n-[2] Most Favourited (all time)\n-[3] Most Favourited (past week)\n-[4] Most Favourited (past day)\n\n-[5] Bestselling (all time)\n-[6] Bestselling (weekly)\n-[7] Bestselling (past day)\n\n-[8] Recently Updated")
    sortby = input("Sort by: ")
    if sortby == "1":
        a = relevance
        
    elif sortby == "2":
        a = favouritedalltime
    elif sortby == "3":
        a = favouritedallweek
    elif sortby == "4":
        a = favouritedallday
        
    elif sortby == "5":
        a = bestsellingalltime
    elif sortby == "6":
        a = bestsellingweek
    elif sortby == "7":
        a = bestsellingday
    elif sortby == "8":
        a = recentlyupdated
    else:
        print("Invalid input, restart program")
        input()
        
    abx = a.split("&limit=120")

    new1 = abx[1]
    print("\nGathering clothes")
    
    pagecurrent = 0
    a = requests.get(a)
    nextpagecursor = a.json()


    try:
        nextpagecursor = nextpagecursor["nextPageCursor"]
    except:
        print("Issue getting next page, try different key words/different sort - restart program")
        input()
        
    
    abx = f"https://catalog.roblox.com/v1/search/items?category=Clothing&cursor={nextpagecursor}&keyword={ab}&limit=120{new1}"
    ids_and_item_types = a.json()["data"]
    if len(ids_and_item_types) == 0:
        print("No items found (bad keywords)")
        input()
        
    friendslist = [datum["id"] for datum in ids_and_item_types]
    pagecurrent+=1
    
    
    while True:
        pagecurrent+=1
        abx = f"https://catalog.roblox.com/v1/search/items?category=Clothing&cursor={nextpagecursor}&keyword={ab}&limit=120{new1}"
        thelinks = abx

        a = requests.get(thelinks)
        nextpagecursor = a.json()
        
        try:
            nextpagecursor = nextpagecursor["nextPageCursor"]
        except:
            print(f"Max page limit of {pagecurrent} has been reached")
            break
        
        ids_and_item_types = a.json()["data"]
        haha = [datum["id"] for datum in ids_and_item_types]
        friendslist.extend(haha)

        return friendslist, cltype