"""
Main entry point.

This application generates N SCT (Script Concordance Test) items and saves them.
The number of items is configured via NUM_SCTS_TO_GENERATE environment variable.
Items are distributed across three clinical guidelines: American, British, and European.
"""

import sys
from typing import List

from .config import settings
from .generator import generate_items_per_guideline
from .logging import get_logger, setup_logging
from .schemas import SCTItem

logger = get_logger(__name__)


def generate_scts(
    num_items: int, model: str, domains: List[str], provider: str
) -> List[SCTItem]:
    """
    Generate N SCT items distributed across three clinical guidelines.
    
    Each guideline (American, British, European) will receive num_items items.
    Total generated = num_items * 3 guidelines.

    Args:
        num_items: Number of SCT items to generate PER GUIDELINE.
        model: LLM model to use.
        domains: List of clinical domains to distribute items across.
        provider: LLM provider to use ("openai" or "gemini").

    Returns:
        List of all generated SCTItem objects.
    """
    logger.info(f"Starting generation of {num_items} SCT items PER GUIDELINE")
    logger.info(f"Total items to generate: {num_items * 3} (across 3 guidelines)")
    logger.info(f"Using provider: {provider}")
    logger.info(f"Using model: {model}")
    logger.info(f"Domains: {', '.join(domains)}")
    logger.info("=" * 70)

    # Select a domain for this generation run
    # If you want to distribute across domains, you could modify this
    domain = domains[0] if domains else None

    try:
        # Generate items for all three guidelines
        results = generate_items_per_guideline(
            model=model,
            items_per_guideline=num_items,
            provider=provider,
            domain=domain,
        )

        # Flatten results into a single list
        all_items = []
        for guideline, items in results.items():
            all_items.extend(items)

        # Calculate statistics
        total_generated = len(all_items)
        total_expected = num_items * 3
        failed_count = total_expected - total_generated

        logger.info("=" * 70)
        logger.info("\nGeneration complete!")
        logger.info(f"  Successful: {total_generated}/{total_expected}")
        logger.info(f"  Failed: {failed_count}/{total_expected}")
        logger.info("\n  Breakdown by guideline:")
        for guideline, items in results.items():
            logger.info(f"    {guideline.capitalize()}: {len(items)}/{num_items}")
        logger.info("\n  Output folders:")
        logger.info("    All items: data/generated/")
        logger.info("    Validated: data/validated/")
        logger.info("    Failed validation: data/validation_failed/")

        return all_items

    except Exception as e:
        logger.error(f"Error during generation: {e}")
        raise


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Setup logging
    setup_logging(level=settings.log_level)

    logger.info("=" * 70)
    logger.info("SCT DATA GENERATION APPLICATION")
    logger.info("=" * 70)

    # Validate LLM provider
    provider = settings.llm_provider.lower()
    if provider not in ["openai", "gemini"]:
        logger.error(f"ERROR: Invalid LLM_PROVIDER: {provider}")
        logger.error("Must be 'openai' or 'gemini'")
        return 1

    # Validate API key based on provider
    if provider == "openai":
        if not settings.openai_api_key:
            logger.error("ERROR: OPENAI_API_KEY not configured")
            logger.error("Please set OPENAI_API_KEY in .env file or environment")
            return 1
    elif provider == "gemini":
        if not settings.gemini_api_key:
            logger.error("ERROR: GEMINI_API_KEY not configured")
            logger.error("Please set GEMINI_API_KEY in .env file or environment")
            return 1

    if settings.num_scts_to_generate <= 0:
        logger.error(
            f"ERROR: Invalid NUM_SCTS_TO_GENERATE: {settings.num_scts_to_generate}"
        )
        logger.error("Must be a positive integer")
        return 1

    # Validate domains
    domains = settings.domains
    if not domains:
        logger.error("ERROR: No domains configured")
        logger.error("Please set DOMAIN_DISTRIBUTION in .env file")
        return 1

    # Display configuration
    logger.info("\nConfiguration:")
    logger.info(f"  LLM Provider: {provider.upper()}")
    logger.info(f"  Items per guideline: {settings.num_scts_to_generate}")
    logger.info(f"  Total items: {settings.num_scts_to_generate * 3} (3 guidelines)")
    logger.info(f"  Guidelines: American, British, European")
    logger.info(f"  Model: {settings.model}")
    logger.info(f"  Domains: {', '.join(domains)} ({len(domains)} total)")
    logger.info("  All items: data/generated/")
    logger.info("  Validated: data/validated/")
    logger.info("  Failed: data/validation_failed/")
    logger.info("")

    try:
        # Generate SCTs
        items = generate_scts(
            num_items=settings.num_scts_to_generate,
            model=settings.model,
            domains=domains,
            provider=provider,
        )

        if not items:
            logger.error("\nNo items were generated successfully")
            return 1

        logger.info("\n" + "=" * 70)
        logger.info("APPLICATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        return 0

    except KeyboardInterrupt:
        logger.warning("\n\nGeneration interrupted by user")
        return 1

    except Exception as e:
        logger.error(f"\n\nFATAL ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
