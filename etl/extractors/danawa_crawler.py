"""
다나와 Price Crawler for RTX 4070 Series GPUs.

This module extracts GPU price data from 다나와 (Korean e-commerce site),
including current prices and 3-month historical price trends.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from models import PriceData

logger = logging.getLogger(__name__)


class CrawlError(Exception):
    """Raised when crawling fails."""
    pass


class DanawaCrawler:
    """
    Crawler for extracting GPU price data from 다나와.
    
    This crawler searches for RTX 4070 series products and extracts:
    - Current prices
    - 3-month price history
    - Product names and URLs
    """
    
    BASE_URL = "http://prod.danawa.com/list/"
    SEARCH_PARAMS = {
        "cate": "112758",  # Graphics card category
        "limit": "40",
        "sort": "saveDESC",
    }
    
    RTX_4070_VARIANTS = [
        "RTX 4070",
        "RTX 4070 Super",
        "RTX 4070 Ti",
        "RTX 4070 Ti Super"
    ]
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    def __init__(self, max_retries: int = 3, retry_backoff: int = 5):
        """
        Initialize the 다나와 crawler.
        
        Args:
            max_retries: Maximum number of retry attempts for failed requests
            retry_backoff: Initial backoff time in seconds for retries
        """
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def crawl_danawa(self, chipset: str) -> List[PriceData]:
        """
        Crawl 다나와 for RTX 4070 series prices.
        
        Args:
            chipset: One of ["RTX 4070", "RTX 4070 Super", "RTX 4070 Ti", "RTX 4070 Ti Super"]
        
        Returns:
            List of PriceData objects with current price and 3-month history
        
        Raises:
            CrawlError: If website is unreachable or parsing fails
        """
        if chipset not in self.RTX_4070_VARIANTS:
            raise ValueError(f"Invalid chipset: {chipset}. Must be one of {self.RTX_4070_VARIANTS}")
        
        logger.info(f"Starting 다나와 crawl for chipset: {chipset}")
        
        try:
            # Search for products matching the chipset
            products = self._search_products(chipset)
            
            if not products:
                logger.warning(f"No products found for chipset: {chipset}")
                return []
            
            logger.info(f"Found {len(products)} products for {chipset}")
            
            # Extract price data for each product
            price_data_list = []
            for product in products:
                try:
                    price_data = self._extract_price_data(product, chipset)
                    if price_data:
                        price_data_list.append(price_data)
                except Exception as e:
                    logger.error(f"Failed to extract price data for product {product.get('name', 'unknown')}: {e}")
                    # Continue with remaining products
                    continue
            
            logger.info(f"Successfully extracted {len(price_data_list)} price records for {chipset}")
            return price_data_list
            
        except Exception as e:
            logger.error(f"다나와 crawl failed for {chipset}: {e}")
            raise CrawlError(f"Failed to crawl 다나와 for {chipset}: {e}")
    
    def _search_products(self, chipset: str) -> List[dict]:
        """
        Search for products matching the chipset.
        
        Args:
            chipset: RTX 4070 series variant
        
        Returns:
            List of product dictionaries with name, price, and URL
        """
        # Build search query
        search_query = chipset.replace("RTX ", "RTX")  # Normalize spacing
        params = self.SEARCH_PARAMS.copy()
        params["search"] = search_query
        
        # Construct URL
        url = f"{self.BASE_URL}?{urlencode(params)}"
        
        logger.debug(f"Searching 다나와 with URL: {url}")
        
        # Fetch page with retry logic
        html = self._fetch_with_retry(url)
        
        # Parse HTML
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract product listings
        products = []
        product_items = soup.select('.product_list .product_item')
        
        if not product_items:
            logger.warning(f"No product items found in HTML for {chipset}")
            return []
        
        for item in product_items:
            try:
                product = self._parse_product_item(item)
                if product and self._is_matching_chipset(product['name'], chipset):
                    products.append(product)
            except Exception as e:
                logger.warning(f"Failed to parse product item: {e}")
                continue
        
        return products
    
    def _parse_product_item(self, item) -> Optional[dict]:
        """
        Parse a single product item from the listing page.
        
        Args:
            item: BeautifulSoup element representing a product
        
        Returns:
            Dictionary with product name, price, and URL, or None if parsing fails
        """
        try:
            # Extract product name
            name_elem = item.select_one('.prod_name a')
            if not name_elem:
                return None
            product_name = name_elem.get_text(strip=True)
            
            # Extract product URL
            product_url = name_elem.get('href', '')
            if product_url and not product_url.startswith('http'):
                product_url = f"http://prod.danawa.com{product_url}"
            
            # Extract current price
            price_elem = item.select_one('.price_sect strong')
            if not price_elem:
                return None
            
            price_text = price_elem.get_text(strip=True)
            # Remove commas and "원" suffix
            price_text = price_text.replace(',', '').replace('원', '').strip()
            
            try:
                price = float(price_text)
            except ValueError:
                logger.warning(f"Failed to parse price: {price_text}")
                return None
            
            return {
                'name': product_name,
                'price': price,
                'url': product_url
            }
            
        except Exception as e:
            logger.warning(f"Error parsing product item: {e}")
            return None
    
    def _is_matching_chipset(self, product_name: str, chipset: str) -> bool:
        """
        Check if product name matches the target chipset.
        
        Args:
            product_name: Product name from listing
            chipset: Target chipset (e.g., "RTX 4070 Super")
        
        Returns:
            True if product matches chipset, False otherwise
        """
        product_upper = product_name.upper()
        chipset_upper = chipset.upper()
        
        # Normalize spacing variations
        chipset_normalized = chipset_upper.replace(" ", "")
        product_normalized = product_upper.replace(" ", "")
        
        # Exact match check
        if chipset_normalized in product_normalized:
            # Additional validation for Ti variants to avoid false positives
            if "TI" in chipset_upper:
                # If looking for "RTX 4070 Ti" (not Super), reject "RTX 4070 Ti Super"
                if "SUPER" not in chipset_upper and "TISUPER" in product_normalized:
                    return False
            return True
        
        return False
    
    def _extract_price_data(self, product: dict, chipset: str) -> Optional[PriceData]:
        """
        Extract price data for a single product.
        
        Args:
            product: Product dictionary with name, price, and URL
            chipset: RTX 4070 series variant
        
        Returns:
            PriceData object or None if extraction fails
        """
        try:
            # Create PriceData object with current price
            price_data = PriceData(
                product_name=product['name'],
                price=product['price'],
                source='다나와',
                source_url=product['url'],
                recorded_at=datetime.now(),
                price_change_pct=None  # Will be calculated later by Risk_Calculator
            )
            
            return price_data
            
        except Exception as e:
            logger.error(f"Failed to extract price data: {e}")
            return None
    
    def _fetch_with_retry(self, url: str) -> str:
        """
        Fetch URL with exponential backoff retry logic.
        
        Args:
            url: URL to fetch
        
        Returns:
            HTML content as string
        
        Raises:
            CrawlError: If all retry attempts fail
        """
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                logger.debug(f"Fetching URL (attempt {retries + 1}/{self.max_retries}): {url}")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                logger.debug(f"Successfully fetched URL: {url}")
                return response.text
                
            except requests.exceptions.Timeout as e:
                last_error = e
                retries += 1
                logger.warning(f"Request timeout: {e}")
                
            except requests.exceptions.HTTPError as e:
                last_error = e
                status_code = e.response.status_code if e.response else 'unknown'
                logger.error(f"HTTP error {status_code} for URL {url}: {e}")
                
                # Don't retry on 4xx errors (client errors)
                if e.response and 400 <= e.response.status_code < 500:
                    raise CrawlError(f"HTTP {status_code} error: {e}")
                
                retries += 1
                
            except requests.exceptions.RequestException as e:
                last_error = e
                retries += 1
                logger.warning(f"Request failed: {e}")
            
            # Exponential backoff
            if retries < self.max_retries:
                backoff_time = self.retry_backoff * (2 ** (retries - 1))
                logger.info(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
        
        raise CrawlError(f"Failed to fetch URL after {self.max_retries} attempts: {last_error}")
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
        logger.debug("다나와 crawler session closed")


def crawl_all_rtx_4070_series() -> List[PriceData]:
    """
    Convenience function to crawl all RTX 4070 series variants.
    
    Returns:
        List of PriceData objects for all RTX 4070 series products
    """
    crawler = DanawaCrawler()
    all_price_data = []
    
    try:
        for chipset in DanawaCrawler.RTX_4070_VARIANTS:
            try:
                price_data = crawler.crawl_danawa(chipset)
                all_price_data.extend(price_data)
            except CrawlError as e:
                logger.error(f"Failed to crawl {chipset}: {e}")
                # Continue with remaining chipsets
                continue
    finally:
        crawler.close()
    
    return all_price_data
