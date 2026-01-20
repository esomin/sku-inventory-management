"""
SKU matching logic for normalized products.

This module matches normalized product data against existing SKUs in the database
and suggests new SKU creation when no match is found.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import asdict

from etl.models import NormalizedProduct
from etl.db_connection import db_manager

logger = logging.getLogger(__name__)


class SKUMatchError(Exception):
    """Raised when SKU matching encounters an error."""
    pass


class SKUMatcher:
    """
    Matches normalized products to existing SKUs in the database.
    
    This class queries the database to find existing SKUs that match the
    normalized product attributes. If no match is found, it suggests
    creating a new SKU.
    """
    
    def __init__(self):
        """Initialize the SKU matcher."""
        self.db = db_manager
    
    def find_matching_sku(self, product: NormalizedProduct) -> Optional[int]:
        """
        Find an existing SKU that matches the normalized product.
        
        Matching is based on exact matches of:
        - brand
        - chipset
        - model_name
        - vram
        - is_oc
        
        Args:
            product: Normalized product to match
        
        Returns:
            SKU ID if match found, None otherwise
        
        Raises:
            SKUMatchError: If database query fails
        """
        try:
            query = """
                SELECT id 
                FROM skus 
                WHERE brand = %s 
                  AND chipset = %s 
                  AND model_name = %s 
                  AND vram = %s 
                  AND is_oc = %s
                LIMIT 1
            """
            
            params = (
                product.brand,
                product.chipset,
                product.model_name,
                product.vram,
                product.is_oc
            )
            
            with self.db.get_cursor(commit=False) as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                
                if result:
                    sku_id = result[0]
                    logger.info(
                        f"Found matching SKU {sku_id} for product: "
                        f"{product.brand} {product.chipset} {product.model_name}"
                    )
                    return sku_id
                
                logger.info(
                    f"No matching SKU found for product: "
                    f"{product.brand} {product.chipset} {product.model_name}"
                )
                return None
                
        except Exception as e:
            logger.error(f"Error finding matching SKU: {e}")
            raise SKUMatchError(f"Failed to find matching SKU: {e}")
    
    def find_similar_skus(self, product: NormalizedProduct, limit: int = 5) -> list:
        """
        Find similar SKUs based on partial matches.
        
        This is useful for suggesting existing SKUs that might be related
        when an exact match is not found.
        
        Matching priority:
        1. Same brand and chipset
        2. Same chipset (different brand)
        3. Same brand (different chipset)
        
        Args:
            product: Normalized product to match
            limit: Maximum number of similar SKUs to return
        
        Returns:
            List of tuples (sku_id, brand, chipset, model_name, similarity_score)
        
        Raises:
            SKUMatchError: If database query fails
        """
        try:
            query = """
                SELECT 
                    id,
                    brand,
                    chipset,
                    model_name,
                    vram,
                    is_oc,
                    CASE
                        WHEN brand = %s AND chipset = %s THEN 3
                        WHEN chipset = %s THEN 2
                        WHEN brand = %s THEN 1
                        ELSE 0
                    END as similarity_score
                FROM skus
                WHERE (brand = %s OR chipset = %s)
                ORDER BY similarity_score DESC, id DESC
                LIMIT %s
            """
            
            params = (
                product.brand,  # CASE WHEN brand = %s
                product.chipset,  # AND chipset = %s
                product.chipset,  # WHEN chipset = %s
                product.brand,  # WHEN brand = %s
                product.brand,  # WHERE brand = %s
                product.chipset,  # OR chipset = %s
                limit
            )
            
            with self.db.get_cursor(commit=False) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                similar_skus = [
                    {
                        'sku_id': row[0],
                        'brand': row[1],
                        'chipset': row[2],
                        'model_name': row[3],
                        'vram': row[4],
                        'is_oc': row[5],
                        'similarity_score': row[6]
                    }
                    for row in results
                ]
                
                logger.info(f"Found {len(similar_skus)} similar SKUs")
                return similar_skus
                
        except Exception as e:
            logger.error(f"Error finding similar SKUs: {e}")
            raise SKUMatchError(f"Failed to find similar SKUs: {e}")
    
    def suggest_new_sku(self, product: NormalizedProduct) -> Dict[str, Any]:
        """
        Generate a suggestion for creating a new SKU.
        
        This method returns a dictionary with all the information needed
        to create a new SKU in the database, including the normalized
        product attributes and metadata.
        
        Args:
            product: Normalized product
        
        Returns:
            Dictionary with SKU creation suggestion
        """
        suggestion = {
            'action': 'create_new_sku',
            'reason': 'No matching SKU found in database',
            'product_data': asdict(product),
            'suggested_fields': {
                'category': '그래픽카드',
                'brand': product.brand,
                'chipset': product.chipset,
                'model_name': product.model_name,
                'vram': product.vram,
                'is_oc': product.is_oc
            }
        }
        
        # Find similar SKUs for context
        try:
            similar_skus = self.find_similar_skus(product, limit=3)
            if similar_skus:
                suggestion['similar_existing_skus'] = similar_skus
                suggestion['note'] = (
                    f"Found {len(similar_skus)} similar SKUs. "
                    "Review these before creating a new SKU to avoid duplicates."
                )
        except SKUMatchError:
            # If finding similar SKUs fails, continue without them
            pass
        
        logger.info(
            f"Suggesting new SKU creation for: "
            f"{product.brand} {product.chipset} {product.model_name}"
        )
        
        return suggestion
    
    def match_or_suggest(self, product: NormalizedProduct) -> Dict[str, Any]:
        """
        Find matching SKU or suggest creating a new one.
        
        This is the main entry point for SKU matching. It attempts to find
        an exact match first, and if not found, returns a suggestion for
        creating a new SKU.
        
        Args:
            product: Normalized product
        
        Returns:
            Dictionary with either:
            - {'action': 'use_existing', 'sku_id': int} if match found
            - {'action': 'create_new_sku', ...} if no match found
        
        Raises:
            SKUMatchError: If database operations fail
        """
        # Try to find exact match
        sku_id = self.find_matching_sku(product)
        
        if sku_id is not None:
            return {
                'action': 'use_existing',
                'sku_id': sku_id,
                'product_data': asdict(product)
            }
        
        # No match found, suggest creating new SKU
        return self.suggest_new_sku(product)
    
    def batch_match(self, products: list[NormalizedProduct]) -> list[Dict[str, Any]]:
        """
        Match multiple products in batch.
        
        This method processes multiple products and returns matching results
        for each one. It's more efficient than calling match_or_suggest
        multiple times for large batches.
        
        Args:
            products: List of normalized products
        
        Returns:
            List of match results (one per product)
        """
        results = []
        
        for product in products:
            try:
                result = self.match_or_suggest(product)
                results.append(result)
            except SKUMatchError as e:
                logger.error(f"Failed to match product {product.brand} {product.model_name}: {e}")
                results.append({
                    'action': 'error',
                    'error': str(e),
                    'product_data': asdict(product)
                })
        
        return results
