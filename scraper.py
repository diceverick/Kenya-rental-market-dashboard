import csv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

print("--- BuyRentKenya Scraper Setup ---")
user_location = input("Enter the location (e.g., nairobi, mombasa, kilimani): ").strip().lower()
user_bedrooms = input("Enter the number of bedrooms (e.g., 1, 2, 5): ").strip()

BASE_URL = f"https://www.buyrentkenya.com/property-for-sale/{user_location}?bedrooms={user_bedrooms}"

print(f"\nTarget URL: {BASE_URL}")
print("Starting Playwright browser...")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context()
    page = context.new_page()

    with open("buyrent_data.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Title", "Price (KSh)"]) 
        
        page_num = 1
        
        while True:
            if page_num == 1:
                url = BASE_URL
            else:
                url = f"{BASE_URL}&page={page_num}"
                
            print(f"\nScraping Page {page_num}... ({url})")
            page.goto(url)
            
            print("Waiting for apartments to load on the screen...")
            try:
                # The 60-second smart timer. Once articles appear, it moves on instantly.
                page.wait_for_selector("article", timeout=60000)
                page.wait_for_timeout(2000) 
            except:
                print(f"ERROR: No apartments appeared after 60 seconds on page {page_num}.")
                    
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Relaxed the search so it doesn't break on CSS class changes
            cards = soup.find_all("article") 
            
            if len(cards) == 0:
                print(f"Kill switch activated: 0 apartments found on page {page_num}. Ending scrape.")
                break
                
            print(f"Found {len(cards)} apartments!")

            for card in cards:
                price_el = card.find("a", class_="text-heading-sm md:text-heading-md text-primary underline-offset-4 decoration-2 hover:underline")
                price = price_el.text.strip().replace("KSh ", "").replace(",", "") if price_el else "No Price"

                all_images = card.find_all("img")
                alt_texts = [img.get("alt", "") for img in all_images if img.get("alt")]
                title = max(alt_texts, key=len) if alt_texts else "No Title"

                # Only write to the CSV if it's an actual property listing
                if price != "No Price" and title != "No Title":
                    writer.writerow([title, price])
            
            page_num += 1

    browser.close()

print("\nTask complete. All pages exported to buyrent_data.csv!")