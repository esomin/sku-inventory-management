"""
Main ETL Pipeline for GPU Price Monitoring System.

This module orchestrates the complete Extract → Transform → Load pipeline,
integrating all components to collect, process, and store GPU price and
market sentiment data.

Validates: Requirements 3.5, 8.5
"""

import logging
import sys
from datetime import datetime
from typing import List, Dict, Tuple

from config import settings
from db_connection import db_manager
from models import PriceData, MarketSignal, NormalizedProduct

# Extractors
from extractors.danawa_crawler import DanawaCrawler, CrawlError
from extractors.reddit_collector import RedditCollector, RateLimitError

# Transformers
from transformers.product_normalizer import ProductNormalizer, NormalizationError
from transformers.sku_matcher import SKUMatcher, SKUMatchError
from transformers.price_analyzer import PriceAnalyzer, InsufficientDataError
from transformers.sentiment_analyzer import SentimentAnalyzer
from transformers.risk_calculator import RiskCalculator

# Loaders
from loaders.db_loader import (
    upsert_product,
    insert_price_log,
    insert_market_signal,
    insert_risk_alert,
    LoaderError
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('etl_pipeline.log')
    ]
)

logger = logging.getLogger(__name__)


class ETLPipeline:
    """
    Main ETL pipeline orchestrator.
    
    This class coordinates the Extract → Transform → Load workflow,
    handling errors at each stage and ensuring data consistency.
    """
    
    def __init__(self):
        """Initialize the ETL pipeline with all required components."""
        logger.info("Initializing ETL Pipeline")
        
        # Extractors
        self.price_crawler = DanawaCrawler()
        self.reddit_collector = RedditCollector()
        
        # Transformers
        self.product_normalizer = ProductNormalizer()
        self.sku_matcher = SKUMatcher()
        self.price_analyzer = PriceAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.risk_calculator = RiskCalculator()
        
        # Statistics
        self.stats = {
            'prices_extracted': 0,
            'signals_extracted': 0,
            'products_normalized': 0,
            'prices_loaded': 0,
            'signals_loaded': 0,
            'alerts_generated': 0,
            'errors': []
        }
    
    def run_full_pipeline(self) -> Dict:
        """
        Execute the complete ETL pipeline.
        
        This method runs all three phases sequentially:
        1. Extract: Crawl prices and collect Reddit signals
        2. Transform: Normalize products, calculate sentiment and risk
        3. Load: Persist data to database and generate alerts
        
        Returns:
            Dictionary with pipeline execution statistics
        """
        logger.info("=" * 80)
        logger.info("Starting Full ETL Pipeline Execution")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # Phase 1: Extract
            logger.info("\n" + "=" * 80)
            logger.info("PHASE 1: EXTRACT")
            logger.info("=" * 80)
            
            price_data_list = self.extract_prices()
            market_signals = self.extract_market_signals()
            
            # Phase 2: Transform
            logger.info("\n" + "=" * 80)
            logger.info("PHASE 2: TRANSFORM")
            logger.info("=" * 80)
            
            normalized_products, sku_mapping = self.transform_products(price_data_list)
            enriched_signals = self.transform_sentiment(market_signals)
            
            # Phase 3: Load
            logger.info("\n" + "=" * 80)
            logger.info("PHASE 3: LOAD")
            logger.info("=" * 80)
            
            self.load_products(normalized_products)
            self.load_prices(price_data_list, sku_mapping)
            self.load_market_signals(enriched_signals)
            
            # Phase 4: Risk Analysis & Alerts
            logger.info("\n" + "=" * 80)
            logger.info("PHASE 4: RISK ANALYSIS & ALERTS")
            logger.info("=" * 80)
            
            self.generate_risk_alerts()
            
            # Calculate execution time
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Update statistics
            self.stats['execution_time_seconds'] = execution_time
            self.stats['success'] = True
            
            # Log summary
            self._log_pipeline_summary()
            
            return self.stats
            
        except Exception as e:
            logger.error(f"ETL Pipeline failed with error: {e}", exc_info=True)
            self.stats['success'] = False
            self.stats['fatal_error'] = str(e)
            return self.stats
        
        finally:
            # Cleanup resources
            self._cleanup()
    
    def extract_prices(self) -> List[PriceData]:
        """
        Extract price data from 다나와 for all RTX 4070 series variants.
        
        Returns:
            List of PriceData objects
        """
        logger.info("Extracting price data from 다나와...")
        
        all_price_data = []
        
        for chipset in DanawaCrawler.RTX_4070_VARIANTS:
            try:
                logger.info(f"Crawling prices for {chipset}...")
                price_data = self.price_crawler.crawl_danawa(chipset)
                
                all_price_data.extend(price_data)
                self.stats['prices_extracted'] += len(price_data)
                
                logger.info(f"✓ Extracted {len(price_data)} prices for {chipset}")
                
            except CrawlError as e:
                error_msg = f"Failed to crawl {chipset}: {e}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)
                # Continue with remaining chipsets
                continue
            except Exception as e:
                error_msg = f"Unexpected error crawling {chipset}: {e}"
                logger.error(error_msg, exc_info=True)
                self.stats['errors'].append(error_msg)
                continue
        
        logger.info(f"✓ Price extraction complete: {len(all_price_data)} total prices")
        return all_price_data
    
    def extract_market_signals(self) -> List[MarketSignal]:
        """
        Extract market signals from Reddit RSS feeds.
        
        Returns:
            List of MarketSignal objects
        """
        logger.info("Extracting market signals from Reddit...")
        
        try:
            signals = self.reddit_collector.collect_signals()
            self.stats['signals_extracted'] = len(signals)
            
            logger.info(f"✓ Market signal extraction complete: {len(signals)} signals")
            return signals
            
        except RateLimitError as e:
            error_msg = f"Reddit rate limit exceeded: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            return []
        except Exception as e:
            error_msg = f"Failed to collect Reddit signals: {e}"
            logger.error(error_msg, exc_info=True)
            self.stats['errors'].append(error_msg)
            return []
    
    def transform_products(
        self,
        price_data_list: List[PriceData]
    ) -> Tuple[List[NormalizedProduct], Dict[str, int]]:
        """
        Transform raw product names into normalized products and match to SKUs.
        
        Args:
            price_data_list: List of PriceData objects with raw product names
        
        Returns:
            Tuple of (normalized_products, sku_mapping)
            where sku_mapping maps product_name to sku_id
        """
        logger.info("Normalizing product names...")
        
        normalized_products = []
        sku_mapping = {}
        
        for price_data in price_data_list:
            try:
                # Normalize product name
                normalized = self.product_normalizer.normalize(price_data.product_name)
                normalized_products.append(normalized)
                
                # Match to existing SKU or prepare for creation
                match_result = self.sku_matcher.match_or_suggest(normalized)
                
                if match_result['action'] == 'use_existing':
                    sku_id = match_result['sku_id']
                    sku_mapping[price_data.product_name] = sku_id
                    logger.debug(
                        f"Matched '{price_data.product_name}' to SKU {sku_id}"
                    )
                else:
                    # Will be created during load phase
                    sku_mapping[price_data.product_name] = None
                    logger.debug(
                        f"New SKU will be created for '{price_data.product_name}'"
                    )
                
                self.stats['products_normalized'] += 1
                
            except NormalizationError as e:
                error_msg = f"Failed to normalize '{price_data.product_name}': {e}"
                logger.warning(error_msg)
                self.stats['errors'].append(error_msg)
                continue
            except SKUMatchError as e:
                error_msg = f"Failed to match SKU for '{price_data.product_name}': {e}"
                logger.warning(error_msg)
                self.stats['errors'].append(error_msg)
                continue
            except Exception as e:
                error_msg = f"Unexpected error processing '{price_data.product_name}': {e}"
                logger.error(error_msg, exc_info=True)
                self.stats['errors'].append(error_msg)
                continue
        
        logger.info(
            f"✓ Product normalization complete: {len(normalized_products)} products"
        )
        return normalized_products, sku_mapping
    
    def transform_sentiment(self, signals: List[MarketSignal]) -> List[MarketSignal]:
        """
        Transform market signals by calculating sentiment scores.
        
        Args:
            signals: List of MarketSignal objects
        
        Returns:
            List of MarketSignal objects with sentiment scores
        """
        logger.info("Calculating sentiment scores...")
        
        try:
            enriched_signals = self.sentiment_analyzer.enrich_signals_with_sentiment(signals)
            
            logger.info(f"✓ Sentiment analysis complete: {len(enriched_signals)} signals enriched")
            return enriched_signals
            
        except Exception as e:
            error_msg = f"Failed to calculate sentiment scores: {e}"
            logger.error(error_msg, exc_info=True)
            self.stats['errors'].append(error_msg)
            return signals  # Return original signals without sentiment scores
    
    def load_products(self, products: List[NormalizedProduct]) -> None:
        """
        Load normalized products into the database.
        
        Args:
            products: List of NormalizedProduct objects
        """
        logger.info("Loading products into database...")
        
        loaded_count = 0
        
        for product in products:
            try:
                sku_id = upsert_product(product)
                loaded_count += 1
                logger.debug(f"Loaded product: {product.brand} {product.model_name} (SKU {sku_id})")
                
            except LoaderError as e:
                error_msg = f"Failed to load product {product.brand} {product.model_name}: {e}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)
                continue
            except Exception as e:
                error_msg = f"Unexpected error loading product: {e}"
                logger.error(error_msg, exc_info=True)
                self.stats['errors'].append(error_msg)
                continue
        
        logger.info(f"✓ Product loading complete: {loaded_count} products loaded")
    
    def load_prices(
        self,
        price_data_list: List[PriceData],
        sku_mapping: Dict[str, int]
    ) -> None:
        """
        Load price data into the database with price change calculations.
        
        Args:
            price_data_list: List of PriceData objects
            sku_mapping: Mapping of product_name to sku_id
        """
        logger.info("Loading price data into database...")
        
        loaded_count = 0
        
        for price_data in price_data_list:
            try:
                # Get or create SKU ID
                sku_id = sku_mapping.get(price_data.product_name)
                
                if sku_id is None:
                    # Product wasn't matched, need to create it first
                    normalized = self.product_normalizer.normalize(price_data.product_name)
                    sku_id = upsert_product(normalized)
                    sku_mapping[price_data.product_name] = sku_id
                
                # Calculate price change if possible
                try:
                    price_change_pct = self.price_analyzer.calculate_price_change(
                        sku_id,
                        price_data.price
                    )
                    price_data.price_change_pct = price_change_pct
                except InsufficientDataError:
                    # Not enough historical data, skip price change calculation
                    price_data.price_change_pct = None
                    logger.debug(f"Insufficient data for price change calculation (SKU {sku_id})")
                
                # Insert price log
                insert_price_log(sku_id, price_data)
                loaded_count += 1
                self.stats['prices_loaded'] += 1
                
            except LoaderError as e:
                error_msg = f"Failed to load price for '{price_data.product_name}': {e}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)
                continue
            except Exception as e:
                error_msg = f"Unexpected error loading price: {e}"
                logger.error(error_msg, exc_info=True)
                self.stats['errors'].append(error_msg)
                continue
        
        logger.info(f"✓ Price loading complete: {loaded_count} price logs loaded")
    
    def load_market_signals(self, signals: List[MarketSignal]) -> None:
        """
        Load market signals into the database.
        
        Args:
            signals: List of MarketSignal objects with sentiment scores
        """
        logger.info("Loading market signals into database...")
        
        loaded_count = 0
        
        for signal in signals:
            try:
                insert_market_signal(signal)
                loaded_count += 1
                self.stats['signals_loaded'] += 1
                
            except LoaderError as e:
                error_msg = f"Failed to load signal '{signal.keyword}': {e}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)
                continue
            except Exception as e:
                error_msg = f"Unexpected error loading signal: {e}"
                logger.error(error_msg, exc_info=True)
                self.stats['errors'].append(error_msg)
                continue
        
        logger.info(f"✓ Market signal loading complete: {loaded_count} signals loaded")
    
    def generate_risk_alerts(self) -> None:
        """
        Calculate risk indices for all SKUs and generate alerts for high-risk products.
        """
        logger.info("Calculating risk indices and generating alerts...")
        
        try:
            # Calculate risk for all SKUs
            risk_results = self.risk_calculator.calculate_risk_for_all_skus(days=7)
            
            # Generate alerts for high-risk products
            for sku_id, (risk_index, is_high_risk) in risk_results.items():
                if is_high_risk:
                    try:
                        # Get product name for alert
                        query = """
                            SELECT brand, model_name, chipset
                            FROM products
                            WHERE id = %s
                        """
                        
                        with db_manager.get_cursor(commit=False) as cursor:
                            cursor.execute(query, (sku_id,))
                            result = cursor.fetchone()
                            
                            if result:
                                brand, model_name, chipset = result
                                product_name = f"{brand} {chipset} {model_name}"
                                
                                # Get latest price
                                price_query = """
                                    SELECT price
                                    FROM price_logs
                                    WHERE sku_id = %s
                                    ORDER BY recorded_at DESC
                                    LIMIT 1
                                """
                                cursor.execute(price_query, (sku_id,))
                                price_result = cursor.fetchone()
                                current_price = float(price_result[0]) if price_result else 0.0
                                
                                # Get new release mentions
                                new_release_mentions = self.risk_calculator.get_new_release_mentions(days=7)
                                total_mentions = sum(new_release_mentions.values())
                                
                                # Get contributing factors
                                factors = self.risk_calculator.get_contributing_factors(
                                    sku_id,
                                    current_price,
                                    total_mentions
                                )
                                
                                # Add reason to factors
                                if factors.get('price_change_pct', 0) < -5 and total_mentions > 10:
                                    factors['reason'] = "가격 하락 + 신제품 루머 증가"
                                elif factors.get('price_change_pct', 0) < -5:
                                    factors['reason'] = "가격 급락"
                                elif total_mentions > 10:
                                    factors['reason'] = "신제품 루머 급증"
                                else:
                                    factors['reason'] = "재고 위험 감지"
                                
                                # Insert risk alert
                                insert_risk_alert(
                                    sku_id=sku_id,
                                    product_name=product_name,
                                    risk_index=risk_index,
                                    threshold=self.risk_calculator.threshold,
                                    contributing_factors=factors
                                )
                                
                                self.stats['alerts_generated'] += 1
                                
                    except Exception as e:
                        error_msg = f"Failed to generate alert for SKU {sku_id}: {e}"
                        logger.error(error_msg)
                        self.stats['errors'].append(error_msg)
                        continue
            
            logger.info(
                f"✓ Risk analysis complete: {len(risk_results)} SKUs analyzed, "
                f"{self.stats['alerts_generated']} alerts generated"
            )
            
        except Exception as e:
            error_msg = f"Failed to calculate risk indices: {e}"
            logger.error(error_msg, exc_info=True)
            self.stats['errors'].append(error_msg)
    
    def _log_pipeline_summary(self) -> None:
        """Log a summary of the pipeline execution."""
        logger.info("\n" + "=" * 80)
        logger.info("ETL PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Status: {'SUCCESS' if self.stats['success'] else 'FAILED'}")
        logger.info(f"Execution Time: {self.stats.get('execution_time_seconds', 0):.2f} seconds")
        logger.info("")
        logger.info("Extraction:")
        logger.info(f"  - Prices extracted: {self.stats['prices_extracted']}")
        logger.info(f"  - Market signals extracted: {self.stats['signals_extracted']}")
        logger.info("")
        logger.info("Transformation:")
        logger.info(f"  - Products normalized: {self.stats['products_normalized']}")
        logger.info("")
        logger.info("Loading:")
        logger.info(f"  - Prices loaded: {self.stats['prices_loaded']}")
        logger.info(f"  - Market signals loaded: {self.stats['signals_loaded']}")
        logger.info("")
        logger.info("Risk Analysis:")
        logger.info(f"  - Risk alerts generated: {self.stats['alerts_generated']}")
        logger.info("")
        logger.info(f"Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors']:
            logger.info("\nError Details:")
            for i, error in enumerate(self.stats['errors'][:10], 1):  # Show first 10 errors
                logger.info(f"  {i}. {error}")
            if len(self.stats['errors']) > 10:
                logger.info(f"  ... and {len(self.stats['errors']) - 10} more errors")
        
        logger.info("=" * 80)
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up resources...")
        
        try:
            self.price_crawler.close()
            self.reddit_collector.close()
            logger.info("✓ Cleanup complete")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")


def run_price_crawl_only() -> Dict:
    """
    Run only the price crawling portion of the ETL pipeline.
    
    This is useful for scheduled jobs that only need to update prices.
    
    Returns:
        Dictionary with execution statistics
    """
    logger.info("Running price crawl only...")
    
    pipeline = ETLPipeline()
    
    try:
        # Extract prices
        price_data_list = pipeline.extract_prices()
        
        # Transform products
        normalized_products, sku_mapping = pipeline.transform_products(price_data_list)
        
        # Load products and prices
        pipeline.load_products(normalized_products)
        pipeline.load_prices(price_data_list, sku_mapping)
        
        pipeline.stats['success'] = True
        logger.info("✓ Price crawl complete")
        
        return pipeline.stats
        
    except Exception as e:
        logger.error(f"Price crawl failed: {e}", exc_info=True)
        pipeline.stats['success'] = False
        pipeline.stats['fatal_error'] = str(e)
        return pipeline.stats
    
    finally:
        pipeline._cleanup()


def run_reddit_collection_only() -> Dict:
    """
    Run only the Reddit collection portion of the ETL pipeline.
    
    This is useful for scheduled jobs that only need to update market signals.
    
    Returns:
        Dictionary with execution statistics
    """
    logger.info("Running Reddit collection only...")
    
    pipeline = ETLPipeline()
    
    try:
        # Extract market signals
        market_signals = pipeline.extract_market_signals()
        
        # Transform sentiment
        enriched_signals = pipeline.transform_sentiment(market_signals)
        
        # Load market signals
        pipeline.load_market_signals(enriched_signals)
        
        pipeline.stats['success'] = True
        logger.info("✓ Reddit collection complete")
        
        return pipeline.stats
        
    except Exception as e:
        logger.error(f"Reddit collection failed: {e}", exc_info=True)
        pipeline.stats['success'] = False
        pipeline.stats['fatal_error'] = str(e)
        return pipeline.stats
    
    finally:
        pipeline._cleanup()


def main():
    """
    Main entry point for the ETL pipeline.
    
    Supports command-line arguments for running specific tasks:
    - No arguments: Run full pipeline
    - --task=price_crawl: Run price crawl only
    - --task=reddit_collection: Run Reddit collection only
    - --task=start_scheduler: Start the scheduler daemon
    - --task=stop_scheduler: Stop the scheduler daemon (not implemented in CLI)
    
    Validates: Requirement 9.4
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='GPU Price Monitoring ETL Pipeline')
    parser.add_argument(
        '--task',
        choices=['full', 'price_crawl', 'reddit_collection', 'start_scheduler'],
        default='full',
        help='Task to run (default: full)'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting ETL task: {args.task}")
    
    try:
        if args.task == 'price_crawl':
            stats = run_price_crawl_only()
            sys.exit(0 if stats.get('success', False) else 1)
        elif args.task == 'reddit_collection':
            stats = run_reddit_collection_only()
            sys.exit(0 if stats.get('success', False) else 1)
        elif args.task == 'start_scheduler':
            # Import scheduler here to avoid circular dependency
            from scheduler import ETLScheduler
            
            logger.info("Starting scheduler daemon...")
            scheduler = ETLScheduler()
            scheduler.schedule_price_crawl()
            scheduler.schedule_reddit_collection()
            scheduler.start()
            
            # Keep running until interrupted
            import time
            try:
                logger.info("Scheduler is running. Press Ctrl+C to stop.")
                while True:
                    time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                logger.info("Received shutdown signal")
                scheduler.stop()
                logger.info("Scheduler shutdown complete")
                sys.exit(0)
        else:
            pipeline = ETLPipeline()
            stats = pipeline.run_full_pipeline()
            sys.exit(0 if stats.get('success', False) else 1)
        
    except Exception as e:
        logger.critical(f"Fatal error in ETL pipeline: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
