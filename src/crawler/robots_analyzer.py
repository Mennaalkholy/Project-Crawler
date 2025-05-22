import requests
from urllib.parse import urljoin, urlparse
import time
from typing import Dict, List, Tuple

class RobotsAnalyzer:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.robots_url = urljoin(base_url, '/robots.txt')
        self.rules = {}
        self.sitemaps = []
        self.crawl_delay = 0
        
    def fetch_robots_txt(self) -> bool:
        """Fetch and parse robots.txt file."""
        try:
            response = requests.get(self.robots_url, timeout=10)
            if response.status_code == 200:
                self._parse_robots_txt(response.text)
                return True
            return False
        except requests.RequestException:
            return False
            
    def _parse_robots_txt(self, content: str):
        """Parse robots.txt content and extract rules."""
        current_user_agent = '*'
        
        for line in content.split('\n'):
            line = line.strip().lower()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('user-agent:'):
                current_user_agent = line.split(':', 1)[1].strip()
                if current_user_agent not in self.rules:
                    self.rules[current_user_agent] = {'allow': [], 'disallow': []}
                    
            elif line.startswith('disallow:'):
                path = line.split(':', 1)[1].strip()
                if current_user_agent in self.rules:
                    self.rules[current_user_agent]['disallow'].append(path)
                    
            elif line.startswith('allow:'):
                path = line.split(':', 1)[1].strip()
                if current_user_agent in self.rules:
                    self.rules[current_user_agent]['allow'].append(path)
                    
            elif line.startswith('crawl-delay:'):
                try:
                    self.crawl_delay = float(line.split(':', 1)[1].strip())
                except ValueError:
                    self.crawl_delay = 0
                    
            elif line.startswith('sitemap:'):
                sitemap_url = line.split(':', 1)[1].strip()
                self.sitemaps.append(sitemap_url)
                
    def is_allowed(self, url: str, user_agent: str = '*') -> bool:
        """Check if a URL is allowed to be crawled."""
        if user_agent not in self.rules:
            user_agent = '*'
            
        if user_agent not in self.rules:
            return True
            
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # Check disallow rules first
        for disallow in self.rules[user_agent]['disallow']:
            if path.startswith(disallow):
                return False
                
        # Then check allow rules
        for allow in self.rules[user_agent]['allow']:
            if path.startswith(allow):
                return True
                
        return True
        
    def get_crawlability_summary(self) -> Dict:
        """Generate a summary of crawlability rules."""
        return {
            'base_url': self.base_url,
            'robots_txt_exists': bool(self.rules),
            'crawl_delay': self.crawl_delay,
            'sitemaps': self.sitemaps,
            'user_agents': list(self.rules.keys()),
            'disallow_rules': {ua: rules['disallow'] for ua, rules in self.rules.items()},
            'allow_rules': {ua: rules['allow'] for ua, rules in self.rules.items()}
        }
        
    def get_crawl_delay(self) -> float:
        """Get the crawl delay in seconds."""
        return self.crawl_delay
        
    def get_sitemaps(self) -> List[str]:
        """Get list of sitemap URLs."""
        return self.sitemaps 