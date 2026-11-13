import re

import pandas as pd #the data manipulator

from playwright.sync_api import sync_playwright

from bs4 import BeautifulSoup#the HTML parser

print("--- BuyRentKenya Universal Rental Scraper ---")
print("Press Enter on any prompt to search EVERYTHING in that category.")

user_category = input("Enter property category (house, apartment, commercial, bedsitter) [Press Enter for ALL]: ").strip().lower()
user_location = input("Enter location (e.g., nairobi) [Press Enter for ALL]: ").strip().lower()

user_bedrooms = ""
user_sqft = ""

if user_category == "commercial":
    user_sqft = input("Enter minimum square footage (e.g., 1000) [Press Enter to ignore]: ").strip()
elif user_category not in ["bedsitter", "commercial"]:
    user_bedrooms = input("Enter bedrooms (e.g., 2) [Press Enter for ALL]: ").strip()

category_map = {  #the dictionary thats used in da url slug just here below
    "house": "houses-for-rent", 
    "apartment": "flats-apartments-for-rent",
    "commercial": "commercial-property-for-rent",
    "bedsitter": "bedsitters-for-rent"
}  

url_slug = category_map.get(user_category, "property-for-rent")  #.get helps incase the user types nonesense it just defaults to default
BASE_URL = f"https://www.buyrentkenya.com/{url_slug}"

if user_location:
    BASE_URL += f"/{user_location}"
if user_bedrooms:
    BASE_URL += f"?bedrooms={user_bedrooms}"

print(f"\nTarget URL: {BASE_URL}")
print("Starting Playwright browser...")

scraped_data = []

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        channel="msedge", 
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context()
    page = context.new_page()
    
    page_num = 1
    
    while True:
        if page_num == 1:
            url = BASE_URL
        else:
            separator = "&" if "?" in BASE_URL else "?"
            url = f"{BASE_URL}{separator}page={page_num}"
            
        print(f"\nScraping Page {page_num}... ({url})")
        page.goto(url)
        
        try:
            page.wait_for_selector("article", timeout=60000)
            page.wait_for_timeout(2000)
        except:
            print(f"ERROR: No properties appeared after 60 seconds on page {page_num}.")
                
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        cards = soup.find_all("article") 
        
        if len(cards) == 0:
            print(f"Kill switch activated: 0 properties found on page {page_num}. Ending scrape.")
            break
            
        print(f"Found {len(cards)} properties!")

        for card in cards:
            # 1. Price
            price_el = card.find("a", class_="text-heading-sm md:text-heading-md text-primary underline-offset-4 decoration-2 hover:underline")
            price_raw = price_el.text.strip().replace("KSh ", "").replace(",", "") if price_el else ""
            price = int(price_raw) if price_raw.isdigit() else price_raw

            # 2. Title
            all_images = card.find_all("img")
            alt_texts = [img.get("alt", "") for img in all_images if img.get("alt")]
            title = max(alt_texts, key=len) if alt_texts else "No Title"

            if price != "" and title != "No Title":
                # Bedrooms (Fixed Regex)
                bed_match = re.search(r'(\d+)[-\s]*bed', title, re.IGNORECASE)
                if bed_match:
                    bedrooms = int(bed_match.group(1))
                else:
                    bedrooms = int(user_bedrooms) if user_bedrooms and user_bedrooms.isdigit() else "N/A"
                
                # Extract Size and convert to sq ft
                card_text = card.get_text(" ").lower()
                size_sqft = "N/A"
                
                m2_match = re.search(r'([\d,\.]+)\s*(m²|m2|sqm|sq\s*m)', card_text)
                sqft_match = re.search(r'([\d,\.]+)\s*(sq\s*ft|sqft|square\s*feet)', card_text)
                
                if sqft_match:
                    val = float(sqft_match.group(1).replace(',', ''))
                    size_sqft = int(round(val))
                elif m2_match:
                    val = float(m2_match.group(1).replace(',', ''))
                    size_sqft = int(round(val * 10.7639))

                # Drop the property if it's smaller than your requested minimum sqft
                if user_category == "commercial" and user_sqft.isdigit():
                    if size_sqft == "N/A" or size_sqft < int(user_sqft):
                        continue  # Skips to the next property

                # Extract Neighborhood and City
                neighborhood = "Unknown"
                city = "Unknown"
                
                if " in " in title:
                    
                    loc_string = title.split(" in ")[-1].strip() 
                    loc_parts = loc_string.split(",")
                    
                    neighborhood = loc_parts[0].strip()
                    if len(loc_parts) > 1:
                        city = loc_parts[-1].strip()
                    else:
                        city = loc_parts[0].strip()
                
                cat_label = user_category.title() if user_category else "All Rentals"

                # Save with all columns
                scraped_data.append({
                    "Title": title,
                    "Neighborhood": neighborhood,
                    "City": city,
                    "Price (KSh)": price,
                    "Bedrooms": bedrooms,
                    "Size (sq ft)": size_sqft,
                    "Category": cat_label,
                    "Type": "Rent"
                })
        
        page_num += 1

    browser.close()

if len(scraped_data) > 0:
    df = pd.DataFrame(scraped_data)
    df.to_excel("buyrent_rentals_data.xlsx", index=False)
    print("\nTask complete. All data exported cleanly to buyrent_rentals_data.xlsx!")

else:
    print("\nNo data found. Excel file was not created.")