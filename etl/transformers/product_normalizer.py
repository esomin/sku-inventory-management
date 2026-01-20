"""
Product name normalizer for GPU products.

This module parses raw product names from e-commerce sites and Reddit posts
into structured NormalizedProduct objects with extracted fields like brand,
chipset, VRAM, and OC status.
"""

import re
from typing import Optional
from etl.models import NormalizedProduct


class NormalizationError(Exception):
    """Raised when product name normalization fails."""
    pass


class ProductNormalizer:
    """
    Normalizes GPU product names into structured data.
    
    Extracts brand, chipset, VRAM, OC status, and model lineup from
    raw product names. Only supports RTX 4070 series GPUs.
    """
    
    # RTX 4070 series variants (order matters - check longer strings first)
    RTX_4070_VARIANTS = [
        "RTX 4070 Ti Super",
        "RTX 4070 Super",
        "RTX 4070 Ti",
        "RTX 4070",
    ]
    
    # Common GPU brands (Korean and English names)
    BRANDS = [
        "ASUS", "MSI", "GIGABYTE", "기가바이트", "ZOTAC", "PALIT", "팔릿",
        "GALAX", "GAINWARD", "이엠텍", "EMTEK", "PNY", "INNO3D",
        "COLORFUL", "MANLI", "KFA2", "EVGA", "LEADTEK"
    ]
    
    def __init__(self):
        """Initialize the normalizer with compiled regex patterns."""
        # Compile patterns for better performance
        self._brand_pattern = self._compile_brand_pattern()
        self._chipset_pattern = self._compile_chipset_pattern()
        self._vram_pattern = re.compile(r'(\d+)\s*GB', re.IGNORECASE)
        self._oc_pattern = re.compile(r'\b(OC|오버클럭|Overclock)\b', re.IGNORECASE)
    
    def _compile_brand_pattern(self) -> re.Pattern:
        """Compile regex pattern for brand extraction."""
        # Create pattern that matches any brand name (case-insensitive)
        brands_escaped = [re.escape(brand) for brand in self.BRANDS]
        pattern = r'\b(' + '|'.join(brands_escaped) + r')\b'
        return re.compile(pattern, re.IGNORECASE)
    
    def _compile_chipset_pattern(self) -> re.Pattern:
        """Compile regex pattern for chipset extraction."""
        # Create pattern that matches RTX 4070 variants
        # Allow flexible whitespace between words
        # Order matters - check longer strings first
        patterns = [
            r'RTX\s+4070\s+Ti\s+Super',
            r'RTX\s+4070\s+Super',
            r'RTX\s+4070\s+Ti',
            r'RTX\s+4070',
            # Also match abbreviated forms without RTX prefix
            r'4070\s+Ti\s+Super',
            r'4070\s+Super',
            r'4070\s+Ti',
        ]
        pattern = r'\b(' + '|'.join(patterns) + r')\b'
        return re.compile(pattern, re.IGNORECASE)
    
    def normalize(self, product_name: str) -> NormalizedProduct:
        """
        Parse product name into structured fields.
        
        Args:
            product_name: Raw product name from e-commerce site or Reddit
        
        Returns:
            NormalizedProduct with brand, chipset, vram, is_oc, model_name
        
        Raises:
            NormalizationError: If parsing fails or chipset not in RTX 4070 series
        """
        if not product_name or not product_name.strip():
            raise NormalizationError("Product name cannot be empty")
        
        # Extract each field
        brand = self._extract_brand(product_name)
        chipset = self._extract_chipset(product_name)
        vram = self._extract_vram(product_name)
        is_oc = self._detect_oc(product_name)
        model_name = self._extract_model_name(product_name, brand, chipset)
        
        return NormalizedProduct(
            brand=brand,
            chipset=chipset,
            model_name=model_name,
            vram=vram,
            is_oc=is_oc
        )
    
    def _extract_brand(self, name: str) -> str:
        """
        Extract brand from product name.
        
        Args:
            name: Product name
        
        Returns:
            Brand name in uppercase
        
        Raises:
            NormalizationError: If brand cannot be extracted
        """
        match = self._brand_pattern.search(name)
        if not match:
            raise NormalizationError(f"Failed to extract brand from: {name}")
        
        brand = match.group(1).upper()
        
        # Normalize Korean brand names to English
        brand_mapping = {
            "기가바이트": "GIGABYTE",
            "팔릿": "PALIT",
            "이엠텍": "EMTEK"
        }
        
        return brand_mapping.get(brand, brand)
    
    def _extract_chipset(self, name: str) -> str:
        """
        Extract chipset from product name.
        
        Args:
            name: Product name
        
        Returns:
            Chipset name (e.g., "RTX 4070 Super")
        
        Raises:
            NormalizationError: If chipset cannot be extracted or not RTX 4070 series
        """
        match = self._chipset_pattern.search(name)
        if not match:
            raise NormalizationError(f"Failed to extract chipset from: {name}")
        
        chipset = match.group(1)
        
        # Normalize whitespace
        chipset = ' '.join(chipset.split())
        
        # Add RTX prefix if missing
        if not chipset.upper().startswith('RTX'):
            chipset = 'RTX ' + chipset
        
        # Normalize to standard format (title case)
        chipset_normalized = ' '.join(word.capitalize() if word.lower() not in ['rtx'] else word.upper() 
                                       for word in chipset.split())
        
        # Verify it's in the RTX 4070 series
        if chipset_normalized not in self.RTX_4070_VARIANTS:
            raise NormalizationError(
                f"Chipset {chipset_normalized} not in RTX 4070 series"
            )
        
        return chipset_normalized
    
    def _extract_vram(self, name: str) -> str:
        """
        Extract VRAM capacity from product name.
        
        Args:
            name: Product name
        
        Returns:
            VRAM capacity with unit (e.g., "12GB")
        
        Raises:
            NormalizationError: If VRAM cannot be extracted
        """
        match = self._vram_pattern.search(name)
        if not match:
            raise NormalizationError(f"Failed to extract VRAM from: {name}")
        
        vram_size = match.group(1)
        return f"{vram_size}GB"
    
    def _detect_oc(self, name: str) -> bool:
        """
        Detect if product is overclocked.
        
        Args:
            name: Product name
        
        Returns:
            True if OC indicators found, False otherwise
        """
        return bool(self._oc_pattern.search(name))
    
    def _extract_model_name(self, name: str, brand: str, chipset: str) -> str:
        """
        Extract model lineup name from product name.
        
        This extracts the specific product line (e.g., "TUF", "Gaming X", "Dual")
        by removing brand and chipset information.
        
        Args:
            name: Product name
            brand: Extracted brand
            chipset: Extracted chipset
        
        Returns:
            Model lineup name, or full product name if extraction fails
        """
        # Remove brand and chipset from name to get model lineup
        cleaned = name
        
        # Remove brand (case-insensitive)
        cleaned = re.sub(re.escape(brand), '', cleaned, flags=re.IGNORECASE)
        
        # Remove chipset (case-insensitive)
        cleaned = re.sub(re.escape(chipset), '', cleaned, flags=re.IGNORECASE)
        
        # Remove common words and patterns
        cleaned = re.sub(r'\d+\s*GB', '', cleaned, flags=re.IGNORECASE)  # VRAM
        cleaned = re.sub(r'\b(OC|오버클럭|Overclock)\b', '', cleaned, flags=re.IGNORECASE)  # OC
        cleaned = re.sub(r'\b(D6X?|GDDR6X?)\b', '', cleaned, flags=re.IGNORECASE)  # Memory type
        cleaned = re.sub(r'\b(지포스|GeForce)\b', '', cleaned, flags=re.IGNORECASE)  # GPU family
        
        # Clean up whitespace and special characters
        cleaned = re.sub(r'[^\w\s가-힣-]', ' ', cleaned)  # Keep alphanumeric, Korean, hyphen
        cleaned = ' '.join(cleaned.split())  # Normalize whitespace
        cleaned = cleaned.strip()
        
        # If we extracted something meaningful, return it; otherwise return original name
        if cleaned and len(cleaned) > 2:
            return cleaned
        
        return name
