import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

clients_urls = {
    'flutterwave': 'https://www.trustpilot.com/review/flutterwave.com',
    'jumia': 'https://www.trustpilot.com/review/jumia.com.ng',
    'paystack': 'https://www.trustpilot.com/review/paystack.com',
    'dhl': 'https://www.trustpilot.com/review/dhl.com'
}

def fetch_reviews(url, pages):
    results = []
    base_url = url

    for page in pages:
        page_url = f'{base_url}?page={page}'
        response = requests.get(page_url)
        soup = BeautifulSoup(response.content, 'lxml')

        review_cards = soup.select('[data-testid="service-review-card-v2"]')

        for root in review_cards:
            data = {}

            name_el = root.select_one('[data-consumer-name-typography="true"]')
            name = name_el.get_text(strip=True) if name_el else None
            data['name'] = name

            reviews_count_el = root.select_one('[data-consumer-reviews-count-typography="true"]')
            m = re.search(r'(\d+)', reviews_count_el.get_text(strip=True)) if reviews_count_el else None
            reviews_count = int(m.group(1)) if m else None
            data['reviews_count'] = reviews_count

            text_el = root.select_one('[data-service-review-text-typography="true"]')
            review_text = text_el.get_text(strip=True) if text_el else None
            data['review_text'] = review_text

            star_given = root.select_one('[data-service-review-rating]')
            star_rating = None
            if star_given and star_given.has_attr('data-service-review-rating'):
                rating_attr = star_given['data-service-review-rating']
                m = re.search(r'(\d+)', rating_attr) if rating_attr else None
                if m:
                    star_rating = int(m.group(1))
            data['star_rating'] = star_rating

            date = root.select_one('[data-service-review-date-time-ago]')
            if date:
                date_text = date.get_text(strip=True)
                data['date'] = date_text

            data['Client_URL'] = page_url

            results.append(data)
    return results

daily_reviews = []
        

if __name__ == "__main__":
    pages = range(1, 6)

    for client, url in clients_urls.items():
        reviews = fetch_reviews(url, pages)
        daily_reviews.extend(reviews)

    df = pd.DataFrame(daily_reviews)
    df.to_csv('trustpilot_daily_reviews.csv', index=False)
    print("Reviews have been saved to trustpilot_daily_reviews.csv")



## Load the fetched data into PostgreSQL database
## Implement Idempotency to avoid duplicate entries