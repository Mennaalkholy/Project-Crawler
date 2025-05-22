from playwright.sync_api import sync_playwright
import requests
from typing import Dict, List, Optional, Tuple
import json
import time
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class JSHandler:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    def __enter__(self):
        """Context manager entry."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
            
    def is_js_heavy(self, url: str) -> Tuple[bool, Dict]:
        """Determine if a page is JavaScript-heavy."""
        try:
            # First, get the page without JavaScript
            response = requests.get(url, timeout=10)
            static_content = response.text
            
            # Then get the page with JavaScript
            self.page.goto(url, wait_until='networkidle')
            js_content = self.page.content()
            
            # Compare the content
            static_soup = BeautifulSoup(static_content, 'lxml')
            js_soup = BeautifulSoup(js_content, 'lxml')
            
            # Check for differences
            static_text = static_soup.get_text(strip=True)
            js_text = js_soup.get_text(strip=True)
            
            # Calculate content difference ratio
            content_diff = abs(len(js_text) - len(static_text)) / max(len(js_text), len(static_text))
            
            # Check for dynamic elements
            dynamic_elements = self.page.evaluate('''() => {
                return {
                    'dynamic_scripts': document.querySelectorAll('script[src]').length,
                    'event_listeners': window.getEventListeners ? Object.keys(window.getEventListeners(document)).length : 0,
                    'ajax_calls': performance.getEntriesByType('resource')
                        .filter(r => r.initiatorType === 'xmlhttprequest').length
                }
            }''')
            
            return content_diff > 0.3 or dynamic_elements['dynamic_scripts'] > 5, {
                'content_difference_ratio': content_diff,
                'dynamic_elements': dynamic_elements
            }
            
        except Exception as e:
            logging.error(f"Error checking JS heaviness: {str(e)}")
            return False, {}
            
    def extract_js_content(self, url: str) -> Optional[Dict]:
        """Extract content from a JavaScript-heavy page."""
        try:
            self.page.goto(url, wait_until='networkidle')
            
            # Wait for dynamic content to load
            self.page.wait_for_load_state('networkidle')
            
            # Extract content
            content = self.page.evaluate('''() => {
                return {
                    'title': document.title,
                    'description': document.querySelector('meta[name="description"]')?.content || '',
                    'content': document.body.innerText,
                    'links': Array.from(document.querySelectorAll('a')).map(a => ({
                        'url': a.href,
                        'text': a.innerText
                    })),
                    'images': Array.from(document.querySelectorAll('img')).map(img => ({
                        'src': img.src,
                        'alt': img.alt
                    }))
                }
            }''')
            
            return content
            
        except Exception as e:
            logging.error(f"Error extracting JS content: {str(e)}")
            return None
            
    def detect_apis(self, url: str) -> List[Dict]:
        """Detect potential APIs and endpoints."""
        try:
            self.page.goto(url, wait_until='networkidle')
            
            # Collect all network requests
            api_endpoints = []
            
            def handle_request(request):
                if any(ext in request.url for ext in ['.json', '.xml', '/api/', '/graphql']):
                    api_endpoints.append({
                        'url': request.url,
                        'method': request.method,
                        'headers': request.headers
                    })
                    
            self.page.on('request', handle_request)
            
            # Wait for some time to collect requests
            time.sleep(5)
            
            return api_endpoints
            
        except Exception as e:
            logging.error(f"Error detecting APIs: {str(e)}")
            return []
            
    def detect_rss_feeds(self, url: str) -> List[str]:
        """Detect RSS feeds on the page."""
        try:
            self.page.goto(url, wait_until='networkidle')
            
            # Look for RSS feed links
            rss_links = self.page.evaluate('''() => {
                return Array.from(document.querySelectorAll('link[type="application/rss+xml"], link[type="application/atom+xml"]'))
                    .map(link => link.href)
            }''')
            
            return rss_links
            
        except Exception as e:
            logging.error(f"Error detecting RSS feeds: {str(e)}")
            return [] 