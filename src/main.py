import os
import sys
import logging
from typing import Dict, List
import json
from datetime import datetime

from crawler.robots_analyzer import RobotsAnalyzer
from crawler.content_extractor import ContentExtractor
from crawler.js_handler import JSHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class WebCrawlerAnalyzer:
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.robots_analyzer = RobotsAnalyzer(target_url)
        self.content_extractor = ContentExtractor(target_url)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'target_url': target_url,
            'crawlability': {},
            'content': {},
            'js_analysis': {},
            'recommendations': []
        }
        
    def analyze(self) -> Dict:
        """Run the complete analysis."""
        logger.info(f"Starting analysis of {self.target_url}")
        
        # Analyze robots.txt
        self._analyze_crawlability()
        
        # Analyze content
        self._analyze_content()
        
        # Analyze JavaScript and APIs
        self._analyze_js_and_apis()
        
        # Generate recommendations
        self._generate_recommendations()
        
        # Save results
        self._save_results()
        
        logger.info("Analysis completed successfully")
        return self.results
        
    def _analyze_crawlability(self):
        """Analyze website crawlability."""
        logger.info("Analyzing crawlability...")
        
        if self.robots_analyzer.fetch_robots_txt():
            self.results['crawlability'] = self.robots_analyzer.get_crawlability_summary()
        else:
            logger.warning("Could not fetch robots.txt")
            self.results['crawlability'] = {'error': 'Could not fetch robots.txt'}
            
    def _analyze_content(self):
        """Analyze website content."""
        logger.info("Analyzing content...")
        
        content = self.content_extractor.extract_page_content(self.target_url)
        if content:
            self.results['content'] = {
                'title': content['title'],
                'description': content['description'],
                'content_length': len(content['content']),
                'links_count': len(content['links']),
                'images_count': len(content['images'])
            }
        else:
            logger.warning("Could not extract content")
            self.results['content'] = {'error': 'Could not extract content'}
            
    def _analyze_js_and_apis(self):
        """Analyze JavaScript usage and APIs."""
        logger.info("Analyzing JavaScript and APIs...")
        
        with JSHandler(self.target_url) as js_handler:
            # Check if page is JS-heavy
            is_js_heavy, js_metrics = js_handler.is_js_heavy(self.target_url)
            self.results['js_analysis'] = {
                'is_js_heavy': is_js_heavy,
                'metrics': js_metrics
            }
            
            # Detect APIs
            api_endpoints = js_handler.detect_apis(self.target_url)
            self.results['js_analysis']['api_endpoints'] = api_endpoints
            
            # Detect RSS feeds
            rss_feeds = js_handler.detect_rss_feeds(self.target_url)
            self.results['js_analysis']['rss_feeds'] = rss_feeds
            
    def _generate_recommendations(self):
        """Generate crawling recommendations."""
        logger.info("Generating recommendations...")
        
        recommendations = []
        
        # Check robots.txt recommendations
        if self.results['crawlability'].get('crawl_delay', 0) > 0:
            recommendations.append({
                'category': 'Crawl Rate',
                'recommendation': f"Respect crawl delay of {self.results['crawlability']['crawl_delay']} seconds",
                'priority': 'High'
            })
            
        # Check sitemap recommendations
        if self.results['crawlability'].get('sitemaps'):
            recommendations.append({
                'category': 'Data Source',
                'recommendation': "Use sitemap for efficient crawling",
                'priority': 'High'
            })
            
        # Check JS recommendations
        if self.results['js_analysis'].get('is_js_heavy'):
            recommendations.append({
                'category': 'Technology',
                'recommendation': "Use Playwright/Selenium for JavaScript rendering",
                'priority': 'High'
            })
            
        # Check API recommendations
        if self.results['js_analysis'].get('api_endpoints'):
            recommendations.append({
                'category': 'Data Source',
                'recommendation': "Consider using available APIs instead of web scraping",
                'priority': 'Medium'
            })
            
        # Check RSS recommendations
        if self.results['js_analysis'].get('rss_feeds'):
            recommendations.append({
                'category': 'Data Source',
                'recommendation': "Use RSS feeds for content updates",
                'priority': 'Medium'
            })
            
        self.results['recommendations'] = recommendations
        
    def _save_results(self):
        """Save analysis results to a JSON file."""
        os.makedirs('data', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        logger.info(f"Results saved to {filename}")
        
def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python main.py <target_url>")
        sys.exit(1)
        
    target_url = sys.argv[1]
    analyzer = WebCrawlerAnalyzer(target_url)
    results = analyzer.analyze()
    
    # Print summary
    print("\nAnalysis Summary:")
    print(f"Target URL: {results['target_url']}")
    print(f"Timestamp: {results['timestamp']}")
    print("\nCrawlability:")
    print(f"- Robots.txt found: {bool(results['crawlability'].get('robots_txt_exists'))}")
    print(f"- Crawl delay: {results['crawlability'].get('crawl_delay', 0)} seconds")
    print("\nContent Analysis:")
    print(f"- Title: {results['content'].get('title', 'N/A')}")
    print(f"- Content length: {results['content'].get('content_length', 0)} characters")
    print("\nJavaScript Analysis:")
    print(f"- JavaScript heavy: {results['js_analysis'].get('is_js_heavy', False)}")
    print(f"- API endpoints found: {len(results['js_analysis'].get('api_endpoints', []))}")
    print(f"- RSS feeds found: {len(results['js_analysis'].get('rss_feeds', []))}")
    print("\nRecommendations:")
    for rec in results['recommendations']:
        print(f"- [{rec['priority']}] {rec['recommendation']}")
        
if __name__ == "__main__":
    main() 