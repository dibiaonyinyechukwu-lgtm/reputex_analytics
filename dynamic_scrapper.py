import time
import re
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

REVIEW_URL_TEMPLATE = "https://www.trustpilot.com/review/flutterwave.com?page={page}"

def parse_reviews_from_html(html: str, page: int):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select('[data-testid="service-review-card-v2"]')
    rows = []

    for root in cards:
        name_el = (
            root.select_one('[data-testid="consumer-name-typography"]') or
            root.select_one('[data-consumer-name-typography="true"]') or
            root.select_one('[data-testid*="consumer-name"]')
        )
        name = name_el.get_text(strip=True) if name_el else None

        reviews_count_el = root.select_one('[data-consumer-reviews-count-typography="true"]')
        m = re.search(r'(\d+)', reviews_count_el.get_text(strip=True)) if reviews_count_el else None
        reviews_count = int(m.group(1)) if m else None

        text_el = root.select_one('[data-service-review-text-typography="true"]')
        review_text = text_el.get_text(strip=True) if text_el else None

        star_el = root.select_one('[data-service-review-rating]')
        star_rating = None
        if star_el and star_el.has_attr("data-service-review-rating"):
            m = re.search(r'(\d+)', star_el["data-service-review-rating"])
            star_rating = int(m.group(1)) if m else None

        date_el = root.select_one('[data-service-review-date-time-ago]')
        review_date = date_el.get_text(strip=True) if date_el else None

        rows.append({
            "page": page,
            "reviewer_name": name,
            "reviews_count": reviews_count,
            "review_text": review_text,
            "star_rating": star_rating,
            "review_date": review_date,
        })

    return rows

def main(pages=range(1, 30), headless=False):
    all_rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        # 1) Go to Trustpilot login and let YOU log in manually
        page.goto("https://www.trustpilot.com/users/connect", wait_until="domcontentloaded")

        print("✅ Please log in manually in the opened browser.")
        print("✅ If you see CAPTCHA/2FA, complete it.")
        input("Press ENTER here after you are fully logged in...")

        # 2) Now visit review pages while logged in
        for pg in pages:
            url = REVIEW_URL_TEMPLATE.format(page=pg)
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(1.5)  # small wait for content

            html = page.content()
            rows = parse_reviews_from_html(html, page=pg)

            if not rows:
                print(f"Page {pg}: no rows found (layout change / blocked / empty).")
            else:
                print(f"Page {pg}: scraped {len(rows)} reviews")
                all_rows.extend(rows)

        browser.close()

    df = pd.DataFrame(all_rows)
    print("Total reviews:", len(df))
    df.to_csv("flutterwave_trustpilot_reviews.csv", index=False)
    print("Saved -> flutterwave_trustpilot_reviews.csv")

if __name__ == "__main__":
    main()
