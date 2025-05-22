# Intelligent Web Crawler & Analyzer

A smart web crawler capable of analyzing website crawlability, extracting key metadata, and proposing the best approach to access data.

## Project Structure

```
├── src/
│   ├── crawler/
│   │   ├── __init__.py
│   │   ├── robots_analyzer.py      # Crawlability Specialist
│   │   ├── content_extractor.py    # Content Extractor
│   │   ├── js_handler.py          # JS & API Handler
│   │   └── utils.py               # Common utilities
│   ├── dashboard/
│   │   ├── __init__.py
│   │   └── app.py                 # Streamlit dashboard
│   └── main.py                    # Main entry point
├── data/                          # Storage for crawled data
├── tests/                         # Unit tests
├── requirements.txt               # Project dependencies
└── README.md                      # This file
```

## Team Members & Responsibilities

1. **Crawlability Specialist**
   - Robots.txt analysis
   - Crawl permission checking
   - Crawlability rules summary

2. **Content Extractor**
   - Data extraction using BeautifulSoup/Scrapy
   - Content parsing and cleaning
   - Pagination handling

3. **JS & API Handler**
   - JavaScript-heavy site detection
   - Playwright/Selenium implementation
   - API/RSS feed detection

4. **Visual & Report Designer**
   - Streamlit dashboard development
   - Data visualization
   - Crawlability score display

5. **Documentation & Deployment**
   - Project documentation
   - Deployment setup
   - Report generation

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd [repository-name]
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```bash
   playwright install
   ```

5. Run the Streamlit dashboard:
   ```bash
   streamlit run src/dashboard/app.py
   ```

## Features

- Website crawlability analysis
- Content extraction and parsing
- JavaScript rendering support
- API/RSS feed detection
- Interactive dashboard
- Data visualization
- Comprehensive reporting

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 