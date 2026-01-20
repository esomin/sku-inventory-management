"""
Unit tests for product name normalizer.

These tests verify the normalizer's ability to parse product names from
다나와 and Reddit, extract GPU attributes, and handle edge cases.
"""

import pytest
import sys
import os
from unittest.mock import Mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the db_connection module before importing transformers
sys.modules['etl.db_connection'] = Mock()

from transformers.product_normalizer import ProductNormalizer, NormalizationError
from models import NormalizedProduct


class TestProductNormalizer:
    """Test suite for ProductNormalizer."""
    
    @pytest.fixture
    def normalizer(self):
        """Create a ProductNormalizer instance for testing."""
        return ProductNormalizer()
    
    # Test successful normalization with 다나와 product names
    
    def test_normalize_asus_tuf_4070_super(self, normalizer):
        """Test normalization of ASUS TUF RTX 4070 SUPER product."""
        product_name = "ASUS TUF Gaming 지포스 RTX 4070 SUPER OC D6X 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.brand == "ASUS"
        assert result.chipset == "RTX 4070 Super"
        assert result.vram == "12GB"
        assert result.is_oc is True
        assert "TUF" in result.model_name or "Gaming" in result.model_name
    
    def test_normalize_msi_gaming_x_4070_ti(self, normalizer):
        """Test normalization of MSI Gaming X RTX 4070 Ti product."""
        product_name = "MSI 지포스 RTX 4070 Ti 게이밍 X 트리오 D6X 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.brand == "MSI"
        assert result.chipset == "RTX 4070 Ti"
        assert result.vram == "12GB"
        assert result.is_oc is False
    
    def test_normalize_gigabyte_4070_ti_super(self, normalizer):
        """Test normalization of GIGABYTE RTX 4070 Ti Super product."""
        product_name = "GIGABYTE 지포스 RTX 4070 Ti SUPER GAMING OC 16GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.brand == "GIGABYTE"
        assert result.chipset == "RTX 4070 Ti Super"
        assert result.vram == "16GB"
        assert result.is_oc is True
    
    def test_normalize_zotac_4070_basic(self, normalizer):
        """Test normalization of ZOTAC RTX 4070 basic model."""
        product_name = "ZOTAC GAMING GeForce RTX 4070 Twin Edge 12GB GDDR6X"
        
        result = normalizer.normalize(product_name)
        
        assert result.brand == "ZOTAC"
        assert result.chipset == "RTX 4070"
        assert result.vram == "12GB"
        assert result.is_oc is False
    
    def test_normalize_korean_brand_gigabyte(self, normalizer):
        """Test normalization with Korean brand name (기가바이트)."""
        product_name = "기가바이트 지포스 RTX 4070 SUPER 윈드포스 OC 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.brand == "GIGABYTE"
        assert result.chipset == "RTX 4070 Super"
        assert result.vram == "12GB"
        assert result.is_oc is True
    
    def test_normalize_korean_brand_palit(self, normalizer):
        """Test normalization with Korean brand name (팔릿)."""
        product_name = "팔릿 지포스 RTX 4070 Ti 듀얼 OC 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.brand == "PALIT"
        assert result.chipset == "RTX 4070 Ti"
        assert result.vram == "12GB"
        assert result.is_oc is True
    
    def test_normalize_emtek_korean(self, normalizer):
        """Test normalization with Korean brand name (이엠텍)."""
        product_name = "이엠텍 지포스 RTX 4070 SUPER MIRACLE D6X 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.brand == "EMTEK"
        assert result.chipset == "RTX 4070 Super"
        assert result.vram == "12GB"
    
    # Test Reddit text normalization
    
    def test_normalize_reddit_casual_mention(self, normalizer):
        """Test normalization of casual Reddit mention."""
        reddit_text = "Just got an ASUS Dual RTX 4070 Super 12GB for a great price!"
        
        result = normalizer.normalize(reddit_text)
        
        assert result.brand == "ASUS"
        assert result.chipset == "RTX 4070 Super"
        assert result.vram == "12GB"
        assert result.is_oc is False
    
    def test_normalize_reddit_abbreviated(self, normalizer):
        """Test normalization of abbreviated Reddit text."""
        reddit_text = "MSI 4070 Ti Super 16GB OC is amazing"
        
        result = normalizer.normalize(reddit_text)
        
        assert result.brand == "MSI"
        assert result.chipset == "RTX 4070 Ti Super"
        assert result.vram == "16GB"
        assert result.is_oc is True
    
    def test_normalize_reddit_lowercase(self, normalizer):
        """Test normalization with lowercase text."""
        reddit_text = "thinking about getting a gigabyte rtx 4070 super 12gb"
        
        result = normalizer.normalize(reddit_text)
        
        assert result.brand == "GIGABYTE"
        assert result.chipset == "RTX 4070 Super"
        assert result.vram == "12GB"
    
    # Test OC detection variations
    
    def test_oc_detection_uppercase(self, normalizer):
        """Test OC detection with uppercase 'OC'."""
        product_name = "ASUS RTX 4070 SUPER OC 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.is_oc is True
    
    def test_oc_detection_korean(self, normalizer):
        """Test OC detection with Korean '오버클럭'."""
        product_name = "MSI RTX 4070 Ti 오버클럭 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.is_oc is True
    
    def test_oc_detection_full_word(self, normalizer):
        """Test OC detection with full word 'Overclock'."""
        product_name = "GIGABYTE RTX 4070 Overclock Edition 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.is_oc is True
    
    def test_no_oc_detection(self, normalizer):
        """Test that non-OC products are correctly identified."""
        product_name = "ASUS RTX 4070 SUPER 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.is_oc is False
    
    # Test chipset variant detection
    
    def test_chipset_4070_basic(self, normalizer):
        """Test detection of basic RTX 4070."""
        product_name = "ASUS RTX 4070 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.chipset == "RTX 4070"
    
    def test_chipset_4070_super(self, normalizer):
        """Test detection of RTX 4070 Super."""
        product_name = "ASUS RTX 4070 SUPER 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.chipset == "RTX 4070 Super"
    
    def test_chipset_4070_ti(self, normalizer):
        """Test detection of RTX 4070 Ti."""
        product_name = "ASUS RTX 4070 Ti 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.chipset == "RTX 4070 Ti"
    
    def test_chipset_4070_ti_super(self, normalizer):
        """Test detection of RTX 4070 Ti Super."""
        product_name = "ASUS RTX 4070 Ti SUPER 16GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.chipset == "RTX 4070 Ti Super"
    
    def test_chipset_case_insensitive(self, normalizer):
        """Test that chipset detection is case-insensitive."""
        product_name = "ASUS rtx 4070 super 12gb"
        
        result = normalizer.normalize(product_name)
        
        assert result.chipset == "RTX 4070 Super"
    
    # Test VRAM extraction variations
    
    def test_vram_12gb(self, normalizer):
        """Test extraction of 12GB VRAM."""
        product_name = "ASUS RTX 4070 SUPER 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.vram == "12GB"
    
    def test_vram_16gb(self, normalizer):
        """Test extraction of 16GB VRAM."""
        product_name = "ASUS RTX 4070 Ti SUPER 16GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.vram == "16GB"
    
    def test_vram_with_space(self, normalizer):
        """Test extraction of VRAM with space between number and unit."""
        product_name = "ASUS RTX 4070 SUPER 12 GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.vram == "12GB"
    
    def test_vram_lowercase(self, normalizer):
        """Test extraction of VRAM with lowercase 'gb'."""
        product_name = "ASUS RTX 4070 SUPER 12gb"
        
        result = normalizer.normalize(product_name)
        
        assert result.vram == "12GB"
    
    # Test edge cases
    
    def test_normalize_extra_whitespace(self, normalizer):
        """Test normalization with extra whitespace."""
        product_name = "ASUS   RTX  4070   SUPER    12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.brand == "ASUS"
        assert result.chipset == "RTX 4070 Super"
        assert result.vram == "12GB"
    
    def test_normalize_special_characters(self, normalizer):
        """Test normalization with special characters."""
        product_name = "ASUS [RTX 4070 SUPER] (OC) - 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.brand == "ASUS"
        assert result.chipset == "RTX 4070 Super"
        assert result.vram == "12GB"
        assert result.is_oc is True
    
    def test_normalize_mixed_korean_english(self, normalizer):
        """Test normalization with mixed Korean and English."""
        product_name = "ASUS 지포스 RTX 4070 SUPER 게이밍 OC 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.brand == "ASUS"
        assert result.chipset == "RTX 4070 Super"
        assert result.vram == "12GB"
        assert result.is_oc is True
    
    def test_normalize_without_geforce_prefix(self, normalizer):
        """Test normalization without GeForce prefix."""
        product_name = "MSI RTX 4070 Ti Gaming X 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.brand == "MSI"
        assert result.chipset == "RTX 4070 Ti"
        assert result.vram == "12GB"
    
    # Test error cases
    
    def test_normalize_empty_string(self, normalizer):
        """Test that empty string raises NormalizationError."""
        with pytest.raises(NormalizationError, match="cannot be empty"):
            normalizer.normalize("")
    
    def test_normalize_whitespace_only(self, normalizer):
        """Test that whitespace-only string raises NormalizationError."""
        with pytest.raises(NormalizationError, match="cannot be empty"):
            normalizer.normalize("   ")
    
    def test_normalize_missing_brand(self, normalizer):
        """Test that missing brand raises NormalizationError."""
        product_name = "RTX 4070 SUPER 12GB"
        
        with pytest.raises(NormalizationError, match="Failed to extract brand"):
            normalizer.normalize(product_name)
    
    def test_normalize_missing_chipset(self, normalizer):
        """Test that missing chipset raises NormalizationError."""
        product_name = "ASUS Gaming Graphics Card 12GB"
        
        with pytest.raises(NormalizationError, match="Failed to extract chipset"):
            normalizer.normalize(product_name)
    
    def test_normalize_missing_vram(self, normalizer):
        """Test that missing VRAM raises NormalizationError."""
        product_name = "ASUS RTX 4070 SUPER"
        
        with pytest.raises(NormalizationError, match="Failed to extract VRAM"):
            normalizer.normalize(product_name)
    
    def test_normalize_wrong_gpu_series(self, normalizer):
        """Test that non-RTX 4070 series raises NormalizationError."""
        product_name = "ASUS RTX 3080 12GB"
        
        with pytest.raises(NormalizationError, match="Failed to extract chipset"):
            normalizer.normalize(product_name)
    
    def test_normalize_rtx_4060(self, normalizer):
        """Test that RTX 4060 is rejected."""
        product_name = "ASUS RTX 4060 8GB"
        
        with pytest.raises(NormalizationError, match="Failed to extract chipset"):
            normalizer.normalize(product_name)
    
    def test_normalize_rtx_4080(self, normalizer):
        """Test that RTX 4080 is rejected."""
        product_name = "ASUS RTX 4080 16GB"
        
        with pytest.raises(NormalizationError, match="Failed to extract chipset"):
            normalizer.normalize(product_name)
    
    def test_normalize_rtx_4090(self, normalizer):
        """Test that RTX 4090 is rejected."""
        product_name = "ASUS RTX 4090 24GB"
        
        with pytest.raises(NormalizationError, match="Failed to extract chipset"):
            normalizer.normalize(product_name)
    
    # Test model name extraction
    
    def test_model_name_extraction_tuf(self, normalizer):
        """Test extraction of TUF model lineup."""
        product_name = "ASUS TUF Gaming RTX 4070 SUPER OC 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert "TUF" in result.model_name or "Gaming" in result.model_name
    
    def test_model_name_extraction_dual(self, normalizer):
        """Test extraction of Dual model lineup."""
        product_name = "ASUS Dual GeForce RTX 4070 SUPER OC 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert "Dual" in result.model_name
    
    def test_model_name_extraction_gaming_x(self, normalizer):
        """Test extraction of Gaming X model lineup."""
        product_name = "MSI GeForce RTX 4070 Ti GAMING X TRIO 12GB"
        
        result = normalizer.normalize(product_name)
        
        # Model name should contain Gaming or X or TRIO
        assert any(word in result.model_name for word in ["Gaming", "GAMING", "X", "TRIO", "Trio"])
    
    # Test all supported brands
    
    @pytest.mark.parametrize("brand", [
        "ASUS", "MSI", "GIGABYTE", "ZOTAC", "PALIT", "GALAX",
        "GAINWARD", "EMTEK", "PNY", "INNO3D", "COLORFUL"
    ])
    def test_all_supported_brands(self, normalizer, brand):
        """Test that all supported brands are correctly extracted."""
        product_name = f"{brand} RTX 4070 SUPER 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.brand == brand.upper()
    
    # Test all RTX 4070 variants
    
    @pytest.mark.parametrize("chipset,expected", [
        ("RTX 4070", "RTX 4070"),
        ("RTX 4070 Super", "RTX 4070 Super"),
        ("RTX 4070 Ti", "RTX 4070 Ti"),
        ("RTX 4070 Ti Super", "RTX 4070 Ti Super"),
    ])
    def test_all_rtx_4070_variants(self, normalizer, chipset, expected):
        """Test that all RTX 4070 variants are correctly extracted."""
        product_name = f"ASUS {chipset} 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.chipset == expected
    
    # Test error message specificity
    
    def test_error_message_includes_product_name(self, normalizer):
        """Test that error messages include the problematic product name."""
        product_name = "Unknown Brand RTX 4070 12GB"
        
        with pytest.raises(NormalizationError) as exc_info:
            normalizer.normalize(product_name)
        
        assert product_name in str(exc_info.value)
    
    def test_error_message_specifies_missing_field(self, normalizer):
        """Test that error messages specify which field is missing."""
        product_name = "ASUS RTX 4070 SUPER"  # Missing VRAM
        
        with pytest.raises(NormalizationError) as exc_info:
            normalizer.normalize(product_name)
        
        assert "VRAM" in str(exc_info.value)


class TestProductNormalizerEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def normalizer(self):
        """Create a ProductNormalizer instance for testing."""
        return ProductNormalizer()
    
    def test_normalize_with_typo_in_brand(self, normalizer):
        """Test that typos in brand names cause errors."""
        product_name = "ASUSS RTX 4070 SUPER 12GB"  # Typo: ASUSS
        
        with pytest.raises(NormalizationError, match="Failed to extract brand"):
            normalizer.normalize(product_name)
    
    def test_normalize_abbreviated_chipset(self, normalizer):
        """Test normalization with abbreviated chipset (4070 without RTX)."""
        # This should now work because we support abbreviated forms
        product_name = "ASUS 4070 SUPER 12GB"
        
        result = normalizer.normalize(product_name)
        
        # Should successfully extract and add RTX prefix
        assert result.chipset == "RTX 4070 Super"
        assert result.brand == "ASUS"
        assert result.vram == "12GB"
    
    def test_normalize_multiple_vram_values(self, normalizer):
        """Test that first VRAM value is used when multiple are present."""
        product_name = "ASUS RTX 4070 SUPER 12GB (16GB available)"
        
        result = normalizer.normalize(product_name)
        
        # Should extract the first VRAM value
        assert result.vram == "12GB"
    
    def test_normalize_vram_without_space(self, normalizer):
        """Test VRAM extraction without space."""
        product_name = "ASUS RTX 4070 SUPER 12GB"
        
        result = normalizer.normalize(product_name)
        
        assert result.vram == "12GB"
    
    def test_normalize_complex_model_name(self, normalizer):
        """Test normalization of complex model name with many descriptors."""
        product_name = "ASUS ROG STRIX GeForce RTX 4070 Ti SUPER OC Edition White 16GB GDDR6X"
        
        result = normalizer.normalize(product_name)
        
        assert result.brand == "ASUS"
        assert result.chipset == "RTX 4070 Ti Super"
        assert result.vram == "16GB"
        assert result.is_oc is True
        # Model name should contain some of the descriptors
        assert len(result.model_name) > 0
