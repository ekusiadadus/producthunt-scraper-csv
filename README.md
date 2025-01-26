# Product Hunt Scraper Documentation

## Overview

This application scrapes product information from Product Hunt pages and uses OpenAI's GPT model to generate enhanced descriptions and analysis. It processes multiple products in parallel and outputs the results to a CSV file.

## Prerequisites

- Python 3.7+
- OpenAI API key set in environment variables
- Required packages:
  - openai
  - beautifulsoup4
  - requests
  - typing

## Core Components

### 1. OpenAI Integration (`generate_all_in_one`)

Processes product information through GPT to generate enhanced content.

**Input Parameters:**

- `product_name`: Product name (string)
- `desc_en`: Product description in English
- `launches_en`: Launch information in English
- `reviews_data`: List of review dictionaries with structure:
  ```python
  [
    {
      "stars": int,  # Star rating (1-5)
      "text_en": str # Review text in English
    }
  ]
  ```

**Output Format:**

```json
{
  "enhancedDescription": "Detailed product description",
  "enhancedLaunches": "Launch information",
  "reviews": "Aggregated reviews",
  "businessContext": {
    "initialCustomers": "Target initial customers",
    "persona": "User persona",
    "marketSize": "Market size analysis"
  },
  "etcInfo": "Additional insights"
}
```

### 2. Web Scraper (`scrape_product_hunt`)

Extracts information from Product Hunt pages.

**Input:** Product Hunt URL
**Output:** Dictionary containing:

- Product Name
- Description
- Recent Launches
- Reviews
- Product URLs
- Business Context
- Other Information

**Scraped Elements:**

- Product title (h1 tag)
- Description (div with class "text-18 font-normal text-light-gray")
- Recent launches (div with data-sentry-component="RecentLaunches")
- Reviews (div with data-sentry-component="RatingReview")
- Product URL (a with data-test="product-header-visit-button")

### 3. CSV Writer (`write_csv`)

Writes scraped data to CSV format.

**Parameters:**

- `data`: List of dictionaries containing product information
- `csv_filename`: Output file name

### 4. Main Process

- Processes multiple Product Hunt URLs in parallel using ThreadPoolExecutor
- Default maximum of 10 concurrent workers
- Handles errors gracefully with try-except blocks
- Outputs progress to console

## Usage

1. Set environment variable:

```bash
export OPENAI_API_KEY='your-api-key'
```

2. Prepare list of Product Hunt URLs in `TARGET_URLS`

3. Run the script:

```bash
python main.py
```

## Output

Generates a CSV file named "producthunt_result.csv" with columns:

- Product Name
- Description
- Recent Launches
- Reviews
- ProductHuntURL
- ProductURL
- Other
- Initial Customers
- Persona
- Market Size

## Error Handling

- Failed URL scrapes are logged but don't halt execution
- JSON parsing errors return empty dictionary with default structure
- Network errors are caught and logged
- Malformed HTML handling via BeautifulSoup's safe parsing

## Performance Considerations

- Parallel processing of URLs improves throughput
- Review collection limited to first 20 reviews per product
- Uses UTF-8-SIG encoding for proper CSV handling

## Limitations

- Dependent on Product Hunt's HTML structure
- Rate limiting may be necessary for large numbers of requests
- OpenAI API costs scale with usage
- Maximum of 20 reviews per product processed
