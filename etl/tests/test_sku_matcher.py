"""
Unit tests for SKU matcher.

These tests verify the SKU matcher's ability to find existing SKUs,
suggest new SKU creation, and handle edge cases.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the db_connection module before importing sku_matcher
sys.modules['etl.db_connection'] = Mock()

from transformers.sku_matcher import SKUMatcher, SKUMatchError
from models import NormalizedProduct


class TestSKUMatcher:
    """Test suite for SKUMatcher."""
    
    @pytest.fixture
    def matcher(self):
        """Create a SKUMatcher instance for testing."""
        return SKUMatcher()
    
    @pytest.fixture
    def sample_product(self):
        """Create a sample normalized product."""
        return NormalizedProduct(
            brand="ASUS",
            chipset="RTX 4070 Super",
            model_name="TUF Gaming OC",
            vram="12GB",
            is_oc=True
        )
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create a mock database manager."""
        mock_db = Mock()
        mock_cursor = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = Mock(return_value=mock_cursor)
        mock_context.__exit__ = Mock(return_value=False)
        mock_db.get_cursor.return_value = mock_context
        return mock_db, mock_cursor
    
    # Test find_matching_sku
    
    def test_find_matching_sku_found(self, matcher, sample_product, mock_db_manager):
        """Test finding an exact matching SKU."""
        mock_db, mock_cursor = mock_db_manager
        mock_cursor.fetchone.return_value = (123,)  # SKU ID 123
        
        with patch.object(matcher, 'db', mock_db):
            sku_id = matcher.find_matching_sku(sample_product)
        
        assert sku_id == 123
        mock_cursor.execute.assert_called_once()
        
        # Verify query parameters
        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]
        assert params[0] == "ASUS"
        assert params[1] == "RTX 4070 Super"
        assert params[2] == "TUF Gaming OC"
        assert params[3] == "12GB"
        assert params[4] is True
    
    def test_find_matching_sku_not_found(self, matcher, sample_product, mock_db_manager):
        """Test when no matching SKU is found."""
        mock_db, mock_cursor = mock_db_manager
        mock_cursor.fetchone.return_value = None
        
        with patch.object(matcher, 'db', mock_db):
            sku_id = matcher.find_matching_sku(sample_product)
        
        assert sku_id is None
    
    def test_find_matching_sku_database_error(self, matcher, sample_product, mock_db_manager):
        """Test handling of database errors."""
        mock_db, mock_cursor = mock_db_manager
        mock_cursor.execute.side_effect = Exception("Database connection failed")
        
        with patch.object(matcher, 'db', mock_db):
            with pytest.raises(SKUMatchError, match="Failed to find matching SKU"):
                matcher.find_matching_sku(sample_product)
    
    # Test find_similar_skus
    
    def test_find_similar_skus_same_brand_and_chipset(self, matcher, sample_product, mock_db_manager):
        """Test finding similar SKUs with same brand and chipset."""
        mock_db, mock_cursor = mock_db_manager
        mock_cursor.fetchall.return_value = [
            (101, "ASUS", "RTX 4070 Super", "Dual OC", "12GB", True, 3),
            (102, "ASUS", "RTX 4070 Super", "ROG STRIX", "12GB", False, 3),
        ]
        
        with patch.object(matcher, 'db', mock_db):
            similar_skus = matcher.find_similar_skus(sample_product, limit=5)
        
        assert len(similar_skus) == 2
        assert similar_skus[0]['sku_id'] == 101
        assert similar_skus[0]['brand'] == "ASUS"
        assert similar_skus[0]['chipset'] == "RTX 4070 Super"
        assert similar_skus[0]['similarity_score'] == 3
    
    def test_find_similar_skus_same_chipset_different_brand(self, matcher, sample_product, mock_db_manager):
        """Test finding similar SKUs with same chipset but different brand."""
        mock_db, mock_cursor = mock_db_manager
        mock_cursor.fetchall.return_value = [
            (201, "MSI", "RTX 4070 Super", "Gaming X", "12GB", True, 2),
        ]
        
        with patch.object(matcher, 'db', mock_db):
            similar_skus = matcher.find_similar_skus(sample_product, limit=5)
        
        assert len(similar_skus) == 1
        assert similar_skus[0]['brand'] == "MSI"
        assert similar_skus[0]['similarity_score'] == 2
    
    def test_find_similar_skus_no_results(self, matcher, sample_product, mock_db_manager):
        """Test when no similar SKUs are found."""
        mock_db, mock_cursor = mock_db_manager
        mock_cursor.fetchall.return_value = []
        
        with patch.object(matcher, 'db', mock_db):
            similar_skus = matcher.find_similar_skus(sample_product, limit=5)
        
        assert similar_skus == []
    
    def test_find_similar_skus_respects_limit(self, matcher, sample_product, mock_db_manager):
        """Test that limit parameter is respected."""
        mock_db, mock_cursor = mock_db_manager
        
        with patch.object(matcher, 'db', mock_db):
            matcher.find_similar_skus(sample_product, limit=3)
        
        # Verify limit is passed to query
        call_args = mock_cursor.execute.call_args
        params = call_args[0][1]
        assert params[-1] == 3  # Last parameter should be the limit
    
    def test_find_similar_skus_database_error(self, matcher, sample_product, mock_db_manager):
        """Test handling of database errors when finding similar SKUs."""
        mock_db, mock_cursor = mock_db_manager
        mock_cursor.execute.side_effect = Exception("Query failed")
        
        with patch.object(matcher, 'db', mock_db):
            with pytest.raises(SKUMatchError, match="Failed to find similar SKUs"):
                matcher.find_similar_skus(sample_product)
    
    # Test suggest_new_sku
    
    def test_suggest_new_sku_basic(self, matcher, sample_product):
        """Test basic new SKU suggestion."""
        with patch.object(matcher, 'find_similar_skus', return_value=[]):
            suggestion = matcher.suggest_new_sku(sample_product)
        
        assert suggestion['action'] == 'create_new_sku'
        assert suggestion['reason'] == 'No matching SKU found in database'
        assert suggestion['product_data']['brand'] == "ASUS"
        assert suggestion['product_data']['chipset'] == "RTX 4070 Super"
        assert suggestion['suggested_fields']['category'] == '그래픽카드'
        assert suggestion['suggested_fields']['brand'] == "ASUS"
        assert suggestion['suggested_fields']['is_oc'] is True
    
    def test_suggest_new_sku_with_similar_skus(self, matcher, sample_product):
        """Test new SKU suggestion includes similar SKUs."""
        similar_skus = [
            {'sku_id': 101, 'brand': 'ASUS', 'chipset': 'RTX 4070 Super', 
             'model_name': 'Dual', 'vram': '12GB', 'is_oc': False, 'similarity_score': 3}
        ]
        
        with patch.object(matcher, 'find_similar_skus', return_value=similar_skus):
            suggestion = matcher.suggest_new_sku(sample_product)
        
        assert 'similar_existing_skus' in suggestion
        assert len(suggestion['similar_existing_skus']) == 1
        assert suggestion['similar_existing_skus'][0]['sku_id'] == 101
        assert 'note' in suggestion
        assert 'similar SKUs' in suggestion['note']
    
    def test_suggest_new_sku_handles_similar_skus_error(self, matcher, sample_product):
        """Test that suggestion continues even if finding similar SKUs fails."""
        with patch.object(matcher, 'find_similar_skus', side_effect=SKUMatchError("DB error")):
            suggestion = matcher.suggest_new_sku(sample_product)
        
        # Should still return a valid suggestion
        assert suggestion['action'] == 'create_new_sku'
        assert 'similar_existing_skus' not in suggestion
    
    # Test match_or_suggest
    
    def test_match_or_suggest_existing_sku(self, matcher, sample_product):
        """Test match_or_suggest when existing SKU is found."""
        with patch.object(matcher, 'find_matching_sku', return_value=123):
            result = matcher.match_or_suggest(sample_product)
        
        assert result['action'] == 'use_existing'
        assert result['sku_id'] == 123
        assert result['product_data']['brand'] == "ASUS"
    
    def test_match_or_suggest_new_sku(self, matcher, sample_product):
        """Test match_or_suggest when no existing SKU is found."""
        with patch.object(matcher, 'find_matching_sku', return_value=None):
            with patch.object(matcher, 'find_similar_skus', return_value=[]):
                result = matcher.match_or_suggest(sample_product)
        
        assert result['action'] == 'create_new_sku'
        assert 'suggested_fields' in result
    
    def test_match_or_suggest_database_error(self, matcher, sample_product):
        """Test match_or_suggest handles database errors."""
        with patch.object(matcher, 'find_matching_sku', side_effect=SKUMatchError("DB error")):
            with pytest.raises(SKUMatchError):
                matcher.match_or_suggest(sample_product)
    
    # Test batch_match
    
    def test_batch_match_multiple_products(self, matcher):
        """Test batch matching multiple products."""
        products = [
            NormalizedProduct("ASUS", "RTX 4070 Super", "TUF", "12GB", True),
            NormalizedProduct("MSI", "RTX 4070 Ti", "Gaming X", "12GB", False),
            NormalizedProduct("GIGABYTE", "RTX 4070", "WindForce", "12GB", False),
        ]
        
        # Mock different results for each product
        match_results = [
            {'action': 'use_existing', 'sku_id': 101},
            {'action': 'create_new_sku', 'suggested_fields': {}},
            {'action': 'use_existing', 'sku_id': 102},
        ]
        
        with patch.object(matcher, 'match_or_suggest', side_effect=match_results):
            results = matcher.batch_match(products)
        
        assert len(results) == 3
        assert results[0]['action'] == 'use_existing'
        assert results[0]['sku_id'] == 101
        assert results[1]['action'] == 'create_new_sku'
        assert results[2]['action'] == 'use_existing'
        assert results[2]['sku_id'] == 102
    
    def test_batch_match_handles_errors(self, matcher):
        """Test batch matching continues even if some products fail."""
        products = [
            NormalizedProduct("ASUS", "RTX 4070 Super", "TUF", "12GB", True),
            NormalizedProduct("MSI", "RTX 4070 Ti", "Gaming X", "12GB", False),
        ]
        
        def side_effect(product):
            if product.brand == "ASUS":
                raise SKUMatchError("Database error")
            return {'action': 'use_existing', 'sku_id': 102}
        
        with patch.object(matcher, 'match_or_suggest', side_effect=side_effect):
            results = matcher.batch_match(products)
        
        assert len(results) == 2
        assert results[0]['action'] == 'error'
        assert 'error' in results[0]
        assert results[1]['action'] == 'use_existing'
    
    def test_batch_match_empty_list(self, matcher):
        """Test batch matching with empty product list."""
        results = matcher.batch_match([])
        
        assert results == []
    
    # Test with different product variations
    
    def test_match_different_brands(self, matcher, mock_db_manager):
        """Test matching products from different brands."""
        mock_db, mock_cursor = mock_db_manager
        
        products = [
            NormalizedProduct("ASUS", "RTX 4070 Super", "TUF", "12GB", True),
            NormalizedProduct("MSI", "RTX 4070 Super", "Gaming X", "12GB", True),
            NormalizedProduct("GIGABYTE", "RTX 4070 Super", "WindForce", "12GB", True),
        ]
        
        for product in products:
            mock_cursor.fetchone.return_value = None
            
            with patch.object(matcher, 'db', mock_db):
                sku_id = matcher.find_matching_sku(product)
            
            assert sku_id is None
    
    def test_match_different_chipsets(self, matcher, mock_db_manager):
        """Test matching products with different chipsets."""
        mock_db, mock_cursor = mock_db_manager
        
        chipsets = ["RTX 4070", "RTX 4070 Super", "RTX 4070 Ti", "RTX 4070 Ti Super"]
        
        for chipset in chipsets:
            product = NormalizedProduct("ASUS", chipset, "TUF", "12GB", True)
            mock_cursor.fetchone.return_value = None
            
            with patch.object(matcher, 'db', mock_db):
                sku_id = matcher.find_matching_sku(product)
            
            assert sku_id is None
    
    def test_match_oc_vs_non_oc(self, matcher, mock_db_manager):
        """Test that OC and non-OC versions are treated as different SKUs."""
        mock_db, mock_cursor = mock_db_manager
        
        product_oc = NormalizedProduct("ASUS", "RTX 4070 Super", "TUF", "12GB", True)
        product_non_oc = NormalizedProduct("ASUS", "RTX 4070 Super", "TUF", "12GB", False)
        
        # Mock finding OC version
        mock_cursor.fetchone.return_value = (101,)
        with patch.object(matcher, 'db', mock_db):
            sku_id_oc = matcher.find_matching_sku(product_oc)
        
        # Mock not finding non-OC version
        mock_cursor.fetchone.return_value = None
        with patch.object(matcher, 'db', mock_db):
            sku_id_non_oc = matcher.find_matching_sku(product_non_oc)
        
        assert sku_id_oc == 101
        assert sku_id_non_oc is None
    
    def test_match_different_vram(self, matcher, mock_db_manager):
        """Test that different VRAM sizes are treated as different SKUs."""
        mock_db, mock_cursor = mock_db_manager
        
        product_12gb = NormalizedProduct("ASUS", "RTX 4070 Super", "TUF", "12GB", True)
        product_16gb = NormalizedProduct("ASUS", "RTX 4070 Super", "TUF", "16GB", True)
        
        # Mock finding 12GB version
        mock_cursor.fetchone.return_value = (101,)
        with patch.object(matcher, 'db', mock_db):
            sku_id_12gb = matcher.find_matching_sku(product_12gb)
        
        # Mock not finding 16GB version
        mock_cursor.fetchone.return_value = None
        with patch.object(matcher, 'db', mock_db):
            sku_id_16gb = matcher.find_matching_sku(product_16gb)
        
        assert sku_id_12gb == 101
        assert sku_id_16gb is None
