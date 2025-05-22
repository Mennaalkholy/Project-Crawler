import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple
import time
from urllib.parse import urljoin, urlparse
import logging

class ContentExtractor:
    def __init__(self, base_url: str, crawl_delay: float = 1.0):
        self.base_url = base_url
        self.crawl_delay = crawl_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.visited_urls = set()
        
    def extract_page_content(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """Extract content from a single page."""
        if url in self.visited_urls:
            return None
            
        self.visited_urls.add(url)
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    return self._parse_content(response.text, url)
                time.sleep(self.crawl_delay)
            except requests.RequestException as e:
                logging.error(f"Error fetching {url}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(self.crawl_delay * (attempt + 1))
                continue
        return None
        
    def _parse_content(self, html_content: str, url: str) -> Dict:
        """Parse HTML content and extract relevant information."""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Extract basic metadata
        title = soup.title.string if soup.title else ''
        meta_description = soup.find('meta', {'name': 'description'})
        description = meta_description['content'] if meta_description else ''
        
        # Extract main content (this is a basic implementation - customize based on target website)
        main_content = soup.find('main') or soup.find('article') or soup.find('div', {'class': 'content'})
        content_text = main_content.get_text(strip=True) if main_content else ''
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            if self._is_valid_url(absolute_url):
                links.append({
                    'url': absolute_url,
                    'text': link.get_text(strip=True)
                })
                
        # Extract images
        images = []
        for img in soup.find_all('img', src=True):
            src = img['src']
            absolute_src = urljoin(url, src)
            images.append({
                'src': absolute_src,
                'alt': img.get('alt', '')
            })
            
        return {
            'url': url,
            'title': title,
            'description': description,
            'content': content_text,
            'links': links,
            'images': images,
            'timestamp': time.time()
        }
        
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and belongs to the same domain."""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(self.base_url)
            return parsed_url.netloc == parsed_base.netloc
        except:
            return False
            
    def extract_paginated_content(self, start_url: str, max_pages: int = 10) -> List[Dict]:
        """Extract content from paginated pages."""
        results = []
        current_url = start_url
        page_count = 0
        
        while current_url and page_count < max_pages:
            content = self.extract_page_content(current_url)
            if not content:
                break
                
            results.append(content)
            page_count += 1
            
            # Find next page link (customize based on target website's pagination structure)
            next_page = self._find_next_page(content['links'])
            if not next_page:
                break
                
            current_url = next_page
            time.sleep(self.crawl_delay)
            
        return results
        
    def _find_next_page(self, links: List[Dict]) -> Optional[str]:
        """Find the next page URL from the list of links."""
        # This is a basic implementation - customize based on target website's pagination
        for link in links:
            text = link['text'].lower()
            if any(keyword in text for keyword in ['next', 'next page', '»', '>']):
                return link['url']
        return None 