# BuyRentKenya Property Scraper

A Python-based web scraper that extracts real estate pricing data from BuyRentKenya. Built to handle dynamic JavaScript rendering and bypass Cloudflare anti-bot protections using Playwright stealth mechanics.

## Features
* **Anti-Bot Bypass:** Uses an automated, non-headless Chromium context to pass Cloudflare human-verification checks.
* **Dynamic Pagination:** Automatically loops through infinite pages until all search results are exhausted.
* **Smart Timers:** Relies on DOM state (`wait_for_selector`) instead of hardcoded sleep timers to maximize speed while preventing race conditions.
* **CLI Inputs:** Prompts the user for location and bedroom count to dynamically target specific datasets.

## Installation
1. Clone the repository
2. Install the required Python libraries:



License & Ethics

This project is built strictly for academic and portfolio demonstration purposes. Ensure rate limits and terms of service are respected when performing web scraping at scale.