import streamlit as st
import pandas as pd
import io
import xlsxwriter
import plotly.express as px
import plotly.graph_objects as go
import collections
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
from datetime import datetime
import sys
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler.robots_analyzer import RobotsAnalyzer
from crawler.content_extractor import ContentExtractor
from crawler.js_handler import JSHandler

st.set_page_config(
    page_title="Crawler 3la allah",
    page_icon="🕷️",
    layout="wide"
)

if sys.platform.startswith('win') and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def export_results_to_excel(crawlability, content, js_api, recommendations):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Crawlability summary (main info)
        summary_cols = ['base_url', 'robots_txt_exists', 'crawl_delay']
        summary = {k: crawlability.get(k, '') for k in summary_cols}
        pd.DataFrame([summary]).to_excel(writer, index=False, sheet_name='Crawlability_Summary')

        # Sitemaps (one per row)
        sitemaps = crawlability.get('sitemaps', [])
        if sitemaps:
            pd.DataFrame({'sitemap': sitemaps}).to_excel(writer, index=False, sheet_name='Sitemaps')

        # User agents (one per row)
        user_agents = crawlability.get('user_agents', [])
        if user_agents:
            pd.DataFrame({'user_agent': user_agents}).to_excel(writer, index=False, sheet_name='UserAgents')

        # Disallow rules (user agent, rule per row)
        disallow_rules = crawlability.get('disallow_rules', {})
        disallow_rows = []
        for ua, rules in disallow_rules.items():
            for rule in rules:
                disallow_rows.append({'user_agent': ua, 'disallow': rule})
        if disallow_rows:
            pd.DataFrame(disallow_rows).to_excel(writer, index=False, sheet_name='DisallowRules')

        # Allow rules (user agent, rule per row)
        allow_rules = crawlability.get('allow_rules', {})
        allow_rows = []
        for ua, rules in allow_rules.items():
            for rule in rules:
                allow_rows.append({'user_agent': ua, 'allow': rule})
        if allow_rows:
            pd.DataFrame(allow_rows).to_excel(writer, index=False, sheet_name='AllowRules')

        # Content (flattened)
        pd.DataFrame([content]).to_excel(writer, index=False, sheet_name='Content')

        # JS/API (flattened)
        pd.DataFrame([js_api]).to_excel(writer, index=False, sheet_name='JS_API')

        # Recommendations
        pd.DataFrame(recommendations).to_excel(writer, index=False, sheet_name='Recommendations')

    output.seek(0)
    return output

def main():
    st.title("🕷️ Crawler 3la allah")
    
    # Sidebar for input
    st.sidebar.header("Configuration")
    target_url = st.sidebar.text_input("Target URL", "https://example.com")
    
    if st.sidebar.button("Analyze Website"):
        with st.spinner("Analyzing website..."):
            analyze_website(target_url)
            
def analyze_website(url: str):
    # Initialize components
    robots_analyzer = RobotsAnalyzer(url)
    content_extractor = ContentExtractor(url)
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Crawlability Analysis",
        "Content Analysis",
        "JS & API Analysis",
        "Recommendations"
    ])
    
    with tab1:
        display_crawlability_analysis(robots_analyzer)
        
    with tab2:
        display_content_analysis(content_extractor)
        
    with tab3:
        display_js_api_analysis(url)
        
    with tab4:
        display_recommendations(url)

def display_crawlability_analysis(robots_analyzer: RobotsAnalyzer):
    st.header("Crawlability Analysis")
    
    if robots_analyzer.fetch_robots_txt():
        summary = robots_analyzer.get_crawlability_summary()
        
        # Calculate crawlability score
        score = 0
        if summary['robots_txt_exists']:
            score += 40
        if summary['crawl_delay'] <= 2:
            score += 20
        elif summary['crawl_delay'] <= 5:
            score += 10
        disallowed_count = sum(len(rules) for rules in summary['disallow_rules'].values())
        if disallowed_count <= 2:
            score += 20
        elif disallowed_count <= 5:
            score += 10
        if summary['sitemaps']:
            score += 20
        
        st.metric("Crawlability Score", f"{score}/100")
        
        # Display basic info
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Robots.txt Found", "Yes" if summary['robots_txt_exists'] else "No")
        with col2:
            st.metric("Crawl Delay", f"{summary['crawl_delay']} seconds")
            
        # Display sitemaps
        if summary['sitemaps']:
            st.subheader("Sitemaps")
            for sitemap in summary['sitemaps']:
                st.write(f"- {sitemap}")
                
        # Display rules
        st.subheader("Crawling Rules")
        for user_agent, rules in summary['disallow_rules'].items():
            with st.expander(f"Rules for {user_agent}"):
                if rules:
                    st.write("Disallowed paths:")
                    for rule in rules:
                        st.write(f"- {rule}")
                else:
                    st.write("No disallow rules found")
                    
    else:
        st.error("Could not fetch robots.txt file")
        
def display_content_analysis(content_extractor: ContentExtractor):
    st.header("Content Analysis")
    
    # Extract content from the main page
    content = content_extractor.extract_page_content(content_extractor.base_url)
    
    if content:
        # Display basic content info
        st.subheader("Page Content")
        st.write(f"Title: {content['title']}")
        st.write(f"Description: {content['description']}")
        
        # Display content statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Content Length", len(content['content']))
        with col2:
            st.metric("Number of Links", len(content['links']))
        with col3:
            st.metric("Number of Images", len(content['images']))
            
        # Display link distribution
        if content['links']:
            st.subheader("Link Distribution")
            link_data = pd.DataFrame(content['links'])
            fig = px.histogram(link_data, x='text', title="Link Text Distribution")
            st.plotly_chart(fig)
            
            # Top 5 most common link texts
            link_texts = [l['text'] for l in content['links'] if l['text']]
            top_links = collections.Counter(link_texts).most_common(5)
            st.subheader("Top 5 Link Texts")
            st.table(pd.DataFrame(top_links, columns=["Link Text", "Count"]))
        
        # Word cloud for main content
        if content['content']:
            st.subheader("Main Content Word Cloud")
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate(content['content'])
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
    else:
        st.error("Could not extract content from the page")
        
def display_js_api_analysis(url: str):
    st.header("JavaScript & API Analysis")
    
    with JSHandler(url) as js_handler:
        # Check if page is JS-heavy
        is_js_heavy, js_metrics = js_handler.is_js_heavy(url)
        
        # Display JS metrics
        st.subheader("JavaScript Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("JavaScript Heavy", "Yes" if is_js_heavy else "No")
        with col2:
            if js_metrics:
                st.metric("Content Difference Ratio", f"{js_metrics['content_difference_ratio']:.2%}")
                
        # Display dynamic elements
        if js_metrics and 'dynamic_elements' in js_metrics:
            st.subheader("Dynamic Elements")
            elements = js_metrics['dynamic_elements']
            fig = go.Figure(data=[
                go.Bar(
                    x=list(elements.keys()),
                    y=list(elements.values()),
                    text=list(elements.values()),
                    textposition='auto',
                )
            ])
            st.plotly_chart(fig)
            
        # Display API endpoints
        st.subheader("API Endpoints")
        api_endpoints = js_handler.detect_apis(url)
        if api_endpoints:
            for endpoint in api_endpoints:
                with st.expander(f"{endpoint['method']} {endpoint['url']}"):
                    st.json(endpoint['headers'])
        else:
            st.write("No API endpoints detected")
            
        # Display RSS feeds
        st.subheader("RSS Feeds")
        rss_feeds = js_handler.detect_rss_feeds(url)
        if rss_feeds:
            for feed in rss_feeds:
                st.write(f"- {feed}")
        else:
            st.write("No RSS feeds detected")
            
def display_recommendations(url: str):
    st.header("Crawling Recommendations")
    
    # Initialize components for analysis
    robots_analyzer = RobotsAnalyzer(url)
    content_extractor = ContentExtractor(url)
    
    recommendations = []
    crawlability = {}
    content = {}
    js_api = {}
    
    # Check robots.txt
    if robots_analyzer.fetch_robots_txt():
        summary = robots_analyzer.get_crawlability_summary()
        crawlability = summary
        if summary['crawl_delay'] > 0:
            recommendations.append({
                'category': 'Crawl Rate',
                'recommendation': f"Respect crawl delay of {summary['crawl_delay']} seconds",
                'priority': 'High'
            })
    # Check for sitemaps
    if robots_analyzer.get_sitemaps():
        recommendations.append({
            'category': 'Data Source',
            'recommendation': "Use sitemap for efficient crawling",
            'priority': 'High'
        })
    # Check for JS
    with JSHandler(url) as js_handler:
        is_js_heavy, _ = js_handler.is_js_heavy(url)
        js_api = {'is_js_heavy': is_js_heavy}
        if is_js_heavy:
            recommendations.append({
                'category': 'Technology',
                'recommendation': "Use Playwright/Selenium for JavaScript rendering",
                'priority': 'High'
            })
        # Check for APIs
        api_endpoints = js_handler.detect_apis(url)
        js_api['api_endpoints'] = api_endpoints
        if api_endpoints:
            recommendations.append({
                'category': 'Data Source',
                'recommendation': "Consider using available APIs instead of web scraping",
                'priority': 'Medium'
            })
        # Check for RSS
        rss_feeds = js_handler.detect_rss_feeds(url)
        js_api['rss_feeds'] = rss_feeds
        if rss_feeds:
            recommendations.append({
                'category': 'Data Source',
                'recommendation': "Use RSS feeds for content updates",
                'priority': 'Medium'
            })
    # Content extraction
    content = content_extractor.extract_page_content(url) or {}
    # Display recommendations
    if recommendations:
        df = pd.DataFrame(recommendations)
        st.dataframe(df)
        # Create priority chart
        priority_counts = df['priority'].value_counts()
        fig = px.pie(
            values=priority_counts.values,
            names=priority_counts.index,
            title="Recommendation Priority Distribution"
        )
        st.plotly_chart(fig)
    else:
        st.info("No specific recommendations available")
    # Excel export code
    output = export_results_to_excel(crawlability, content, js_api, recommendations)
    st.download_button(
        label="Download Full Report as Excel",
        data=output,
        file_name="web_crawler_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
        
if __name__ == "__main__":
    main() 