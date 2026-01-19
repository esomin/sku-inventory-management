"""
Unit tests for 다나와 crawler.

These tests verify the crawler's ability to extract price data from 다나와,
handle errors gracefully, and parse product information correctly.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import requests

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extractors.danawa_crawler import DanawaCrawler, CrawlError
from models import PriceData


class TestDanawaCrawler:
    """Test suite for DanawaCrawler."""
    
    @pytest.fixture
    def crawler(self):
        """Create a DanawaCrawler instance for testing."""
        return DanawaCrawler(max_retries=2, retry_backoff=1)
    
    @pytest.fixture
    def sample_html(self):
        """Sample HTML from 다나와 product listing."""
        return """
        <html>
            <body>
                <div class="product_list">
                    <div class="product_item">
                        <div class="prod_name">
                            <a href="/product/12345">ASUS TUF Gaming 지포스 RTX 4070 SUPER OC D6X 12GB</a>
                        </div>
                        <div class="price_sect">
                            <strong>789,000원</strong>
                        </div>
                    </div>
                    <div class="product_item">
                        <div class="prod_name">
                            <a href="/product/67890">MSI 지포스 RTX 4070 SUPER 게이밍 X 트리오 D6X 12GB</a>
                        </div>
                        <div class="price_sect">
                            <strong>819,000원</strong>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
    
    def test_crawl_danawa_valid_chipset(self, crawler, sample_html):
        """Test crawling with a valid RTX 4070 series chipset."""
        with patch.object(crawler, '_fetch_with_retry', return_value=sample_html):
            results = crawler.crawl_danawa("RTX 4070 Super")
            
            assert len(results) == 2
            assert all(isinstance(r, PriceData) for r in results)
            assert all(r.source == '다나와' for r in results)
            assert results[0].price == 789000.0
            assert results[1].price == 819000.0
    
    def test_crawl_danawa_invalid_chipset(self, crawler):
        """Test that invalid chipset raises ValueError."""
        with pytest.raises(ValueError, match="Invalid chipset"):
            crawler.crawl_danawa("RTX 3080")
    
    def test_crawl_danawa_no_products_found(self, crawler):
        """Test handling when no products are found."""
        empty_html = "<html><body><div class='product_list'></div></body></html>"
        
        with patch.object(crawler, '_fetch_with_retry', return_value=empty_html):
            results = crawler.crawl_danawa("RTX 4070")
            
            assert results == []
    
    def test_parse_product_item_success(self, crawler):
        """Test parsing a valid product item."""
        from bs4 import BeautifulSoup
        
        html = """
        <div class="product_item">
            <div class="prod_name">
                <a href="/product/12345">ASUS RTX 4070 12GB</a>
            </div>
            <div class="price_sect">
                <strong>699,000원</strong>
            </div>
        </div>
        """
        
        soup = BeautifulSoup(html, 'lxml')
        item = soup.select_one('.product_item')
        
        product = crawler._parse_product_item(item)
        
        assert product is not None
        assert product['name'] == "ASUS RTX 4070 12GB"
        assert product['price'] == 699000.0
        assert product['url'] == "http://prod.danawa.com/product/12345"
    
    def test_parse_product_item_missing_name(self, crawler):
        """Test parsing fails gracefully when product name is missing."""
        from bs4 import BeautifulSoup
        
        html = """
        <div class="product_item">
            <div class="price_sect">
                <strong>699,000원</strong>
            </div>
        </div>
        """
        
        soup = BeautifulSoup(html, 'lxml')
        item = soup.select_one('.product_item')
        
        product = crawler._parse_product_item(item)
        
        assert product is None
    
    def test_parse_product_item_invalid_price(self, crawler):
        """Test parsing fails gracefully when price is invalid."""
        from bs4 import BeautifulSoup
        
        html = """
        <div class="product_item">
            <div class="prod_name">
                <a href="/product/12345">ASUS RTX 4070 12GB</a>
            </div>
            <div class="price_sect">
                <strong>가격문의</strong>
            </div>
        </div>
        """
        
        soup = BeautifulSoup(html, 'lxml')
        item = soup.select_one('.product_item')
        
        product = crawler._parse_product_item(item)
        
        assert product is None
    
    def test_is_matching_chipset_exact_match(self, crawler):
        """Test chipset matching with exact match."""
        assert crawler._is_matching_chipset("ASUS RTX 4070 SUPER 12GB", "RTX 4070 Super")
        assert crawler._is_matching_chipset("MSI RTX4070SUPER Gaming", "RTX 4070 Super")
    
    def test_is_matching_chipset_no_match(self, crawler):
        """Test chipset matching with non-matching product."""
        assert not crawler._is_matching_chipset("ASUS RTX 4070 12GB", "RTX 4070 Super")
        assert not crawler._is_matching_chipset("ASUS RTX 4070 Ti SUPER 16GB", "RTX 4070 Super")
    
    def test_is_matching_chipset_ti_variants(self, crawler):
        """Test chipset matching for Ti variants."""
        assert crawler._is_matching_chipset("ASUS RTX 4070 Ti 12GB", "RTX 4070 Ti")
        assert not crawler._is_matching_chipset("ASUS RTX 4070 Ti SUPER 16GB", "RTX 4070 Ti")
    
    def test_fetch_with_retry_success(self, crawler):
        """Test successful fetch on first attempt."""
        mock_response = Mock()
        mock_response.text = "<html>test</html>"
        mock_response.status_code = 200
        
        with patch.object(crawler.session, 'get', return_value=mock_response):
            result = crawler._fetch_with_retry("http://test.com")
            
            assert result == "<html>test</html>"
    
    def test_fetch_with_retry_timeout_then_success(self, crawler):
        """Test retry logic after timeout."""
        mock_response = Mock()
        mock_response.text = "<html>test</html>"
        mock_response.status_code = 200
        
        with patch.object(crawler.session, 'get') as mock_get:
            # First call times out, second succeeds
            mock_get.side_effect = [
                requests.exceptions.Timeout("Timeout"),
                mock_response
            ]
            
            result = crawler._fetch_with_retry("http://test.com")
            
            assert result == "<html>test</html>"
            assert mock_get.call_count == 2
    
    def test_fetch_with_retry_all_attempts_fail(self, crawler):
        """Test that CrawlError is raised after all retries fail."""
        with patch.object(crawler.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Timeout")
            
            with pytest.raises(CrawlError, match="Failed to fetch URL"):
                crawler._fetch_with_retry("http://test.com")
            
            assert mock_get.call_count == crawler.max_retries
    
    def test_fetch_with_retry_http_4xx_no_retry(self, crawler):
        """Test that 4xx errors don't trigger retries."""
        mock_response = Mock()
        mock_response.status_code = 404
        
        with patch.object(crawler.session, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.HTTPError(response=mock_response)
            
            with pytest.raises(CrawlError, match="HTTP 404 error"):
                crawler._fetch_with_retry("http://test.com")
            
            # Should not retry on 4xx errors
            assert mock_get.call_count == 1
    
    def test_crawl_danawa_continues_on_product_error(self, crawler, sample_html):
        """Test that crawler continues with remaining products if one fails."""
        with patch.object(crawler, '_fetch_with_retry', return_value=sample_html):
            with patch.object(crawler, '_extract_price_data') as mock_extract:
                # First product fails, second succeeds
                mock_extract.side_effect = [
                    Exception("Parse error"),
                    PriceData(
                        product_name="MSI RTX 4070 SUPER",
                        price=819000.0,
                        source='다나와',
                        source_url="http://test.com",
                        recorded_at=datetime.now()
                    )
                ]
                
                results = crawler.crawl_danawa("RTX 4070 Super")
                
                # Should get one result despite first product failing
                assert len(results) == 1
                assert results[0].price == 819000.0
    
    def test_extract_price_data_success(self, crawler):
        """Test successful price data extraction."""
        product = {
            'name': 'ASUS RTX 4070 SUPER 12GB',
            'price': 789000.0,
            'url': 'http://prod.danawa.com/product/12345'
        }
        
        price_data = crawler._extract_price_data(product, "RTX 4070 Super")
        
        assert price_data is not None
        assert price_data.product_name == 'ASUS RTX 4070 SUPER 12GB'
        assert price_data.price == 789000.0
        assert price_data.source == '다나와'
        assert price_data.source_url == 'http://prod.danawa.com/product/12345'
        assert price_data.price_change_pct is None
        assert isinstance(price_data.recorded_at, datetime)
    
    def test_close_session(self, crawler):
        """Test that session is properly closed."""
        with patch.object(crawler.session, 'close') as mock_close:
            crawler.close()
            mock_close.assert_called_once()


class TestCrawlAllRTX4070Series:
    """Test the convenience function for crawling all variants."""
    
    def test_crawl_all_rtx_4070_series_success(self):
        """Test crawling all RTX 4070 series variants."""
        from extractors.danawa_crawler import crawl_all_rtx_4070_series, DanawaCrawler
        
        mock_price_data = [
            PriceData(
                product_name="Test Product",
                price=700000.0,
                source='다나와',
                source_url="http://test.com",
                recorded_at=datetime.now()
            )
        ]
        
        with patch.object(DanawaCrawler, 'crawl_danawa', return_value=mock_price_data):
            with patch.object(DanawaCrawler, 'close'):
                results = crawl_all_rtx_4070_series()
                
                # Should get results for all 4 variants
                assert len(results) == 4
    
    def test_crawl_all_rtx_4070_series_continues_on_error(self):
        """Test that function continues with remaining variants if one fails."""
        from extractors.danawa_crawler import crawl_all_rtx_4070_series, DanawaCrawler
        
        mock_price_data = [
            PriceData(
                product_name="Test Product",
                price=700000.0,
                source='다나와',
                source_url="http://test.com",
                recorded_at=datetime.now()
            )
        ]
        
        call_count = [0]
        
        def side_effect_func(chipset):
            call_count[0] += 1
            if call_count[0] == 1:
                raise CrawlError("Failed")
            return mock_price_data
        
        with patch.object(DanawaCrawler, 'crawl_danawa', side_effect=side_effect_func):
            with patch.object(DanawaCrawler, 'close'):
                results = crawl_all_rtx_4070_series()
                
                # Should get 3 results (one failed)
                assert len(results) == 3
