import csv
import os
import time
import json
import requests
from openai import OpenAI
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----- OpenAI API Key Configuration -----
client: OpenAI = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_all_in_one(
    product_name: str,
    desc_en: str,
    launches_en: str,
    reviews_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate in a single ChatGPT call:
      - More detailed Description in Japanese
      - More detailed Recent Launches in Japanese
      - Reviews (each review translated to Japanese + text with star ratings)
      - Business Context (initial customers, persona, market size)
      - Other (deep insights)
    and return as JSON.

    Returns: Dictionary with the following keys:
      {
        "enhancedDescription": str,
        "enhancedLaunches": str,
        "reviews": str,
        "businessContext": {
            "initialCustomers": str,
            "persona": str,
            "marketSize": str
        },
        "etcInfo": str
      }
    """
    # reviews_data structure: [{"stars": 4, "text_en": "....."}, ...]

    prompt: str = f"""
Please output only in JSON format. Do not include any additional text.
Based on the following information, please construct JSON in the specified format.

[Specified Format]
{{
  "enhancedDescription": "...(detailed Japanese explanation based on desc_en + usage)...",
  "enhancedLaunches": "...(more detailed Japanese explanation based on launches_en)...",
  "reviews": "...(text summarizing stars and Japanese translations based on reviews_data. OK as one string)...",
  "businessContext": {{
    "initialCustomers": "...",
    "persona": "...",
    "marketSize": "..."
  }},
  "etcInfo": "...(deep analysis and additional information about this product in Japanese. Comparison with similar products, areas for improvement, etc.)..."
}}

[Input Data]
- Product Name (English): {product_name}

- desc_en (English):
{desc_en}

- launches_en (English):
{launches_en}

- reviews_data:
{reviews_data}

[Requirements]
1. Convert desc_en into a more detailed Japanese explanation including usage in "enhancedDescription"
2. Write launches_en in more detail in Japanese in "enhancedLaunches"
3. reviews_data contains stars (rating) and text_en (English review text).
   Translate all into Japanese and combine into one string for "reviews"
   Example:
   Review(1): ★4
   (translated text)
   ...
4. Write businessContext in Japanese with initialCustomers, persona, and marketSize
5. In "etcInfo", briefly summarize (1)comparison with similar products, (2)specific use cases, 
   (3)technical advantages, (4)areas for improvement, and other product-related information
6. Output must be only in the specified JSON format without any extra text
    """.strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    content: str = response.choices[0].message.content.strip()

    try:
        data: Dict[str, Any] = json.loads(content)
        return data
    except json.JSONDecodeError:
        return {
            "enhancedDescription": "",
            "enhancedLaunches": "",
            "reviews": "",
            "businessContext": {
                "initialCustomers": "",
                "persona": "",
                "marketSize": ""
            },
            "etcInfo": ""
        }

def scrape_product_hunt(product_hunt_url: str) -> Dict[str, str]:
    """
    Pass a Product Hunt URL to scrape the page and get:
      - product_name_en
      - desc_en
      - launches_en
      - reviews_data -> [{"stars": int, "text_en": str}, ...]
      - product_url, etc.
    Finally use generate_all_in_one(...) to send everything to ChatGPT and return results.
    """
    resp = requests.get(product_hunt_url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Product Name
    product_name_tag = soup.find("h1")
    product_name_en: str = product_name_tag.get_text(strip=True) if product_name_tag else ""

    # Description (English)
    desc_tag = soup.find("div", {"class": "text-18 font-normal text-light-gray"})
    desc_en: str = desc_tag.get_text(strip=True) if desc_tag else ""

    # Recent Launches (English)
    launches_section = soup.find("div", {"data-sentry-component": "RecentLaunches"})
    if launches_section:
        launches_en: str = launches_section.get_text(separator="\n", strip=True)
    else:
        launches_en = ""

    # Reviews (★ count + English text)
    rating_review_list = soup.find_all("div", {"data-sentry-component": "RatingReview"})
    reviews_data: List[Dict[str, Any]] = []
    for i, review_div in enumerate(rating_review_list):
        if i >= 20:
            break
        star_tags = review_div.find_all("svg", {"data-test": lambda x: x and "star-" in x})
        # Count filled stars
        filled_stars: int = sum(1 for st in star_tags if "fill-[#f5a623]" in st.get("class", []))
        review_body_tag = review_div.find("div", {"class": "styles_htmlText__eYPgj"})
        review_body_en: str = review_body_tag.get_text(strip=True) if review_body_tag else ""
        reviews_data.append({
            "stars": filled_stars,
            "text_en": review_body_en
        })

    # ProductHuntURL
    product_hunt_url_field: str = product_hunt_url

    # ProductURL
    visit_button = soup.find("a", {"data-test": "product-header-visit-button"})
    if visit_button and visit_button.has_attr("href"):
        product_url: str = visit_button["href"]
    else:
        product_url = ""

    # ChatGPT call
    gpt_result: Dict[str, Any] = generate_all_in_one(
        product_name=product_name_en,
        desc_en=desc_en,
        launches_en=launches_en,
        reviews_data=reviews_data
    )

    return {
        "Product Name": product_name_en,
        "Description": gpt_result.get("enhancedDescription", ""),
        "Recent Launches": gpt_result.get("enhancedLaunches", ""),
        "Reviews": gpt_result.get("reviews", ""),
        "ProductHuntURL": product_hunt_url_field,
        "ProductURL": product_url,
        "Other": gpt_result.get("etcInfo", ""),
        "Initial Customers": gpt_result.get("businessContext", {}).get("initialCustomers", ""),
        "Persona": gpt_result.get("businessContext", {}).get("persona", ""),
        "Market Size": gpt_result.get("businessContext", {}).get("marketSize", ""),
    }

def write_csv(data: List[Dict[str, str]], csv_filename: str) -> None:
    if not data:
        return
    fieldnames = list(data[0].keys())
    with open(csv_filename, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main() -> None:
    TARGET_URLS: List[str] = [
        "https://www.producthunt.com/products/threadstart",
        "https://www.producthunt.com/products/jimo",
        "https://www.producthunt.com/products/fairmint-equity-of-the-future",
        "https://www.producthunt.com/products/superblocks",
        "https://www.producthunt.com/products/screen-studio",
        "https://www.producthunt.com/products/erxes",
        "https://www.producthunt.com/products/howitzer-for-reddit",
        "https://www.producthunt.com/products/heygen",
        "https://www.producthunt.com/products/summari",
        "https://www.producthunt.com/products/fig",
        "https://www.producthunt.com/products/sigmaos",
        "https://www.producthunt.com/products/sidekick-browser",
        "https://www.producthunt.com/products/guidde-2",
        "https://www.producthunt.com/products/function12",
        "https://www.producthunt.com/products/timeos",
        "https://www.producthunt.com/products/startup-recipes",
        "https://www.producthunt.com/products/rewind-2",
    ]

    all_results: List[Dict[str, str]] = []
    # Parallel processing
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(scrape_product_hunt, url): url for url in TARGET_URLS}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                all_results.append(result)
                print(f"Completed: {url}")
            except Exception as e:
                print(f"Error: {url} -> {e}")

    write_csv(all_results, "producthunt_result.csv")
    print("Written to CSV: producthunt_result.csv")

if __name__ == "__main__":
    main()