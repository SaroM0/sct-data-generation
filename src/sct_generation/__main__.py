"""
Main entry point.

This application generates N SCT (Script Concordance Test) items and saves them.
The number of items is configured via NUM_SCTS_TO_GENERATE environment variable.
"""

import sys
from typing import List

from .config import settings
from .generator import generate_sct_item
from .logging import get_logger, setup_logging
from .schemas import SCTItem

logger = get_logger(__name__)


def generate_scts(num_items: int, model: str, domains: List[str]) -> List[SCTItem]:
    """
    Generate N SCT items with balanced domain coverage.

    Args:
        num_items: Number of SCT items to generate.
        model: OpenAI model to use.
        domains: List of clinical domains to distribute items across.

    Returns:
        List of generated SCTItem objects.
    """
    generated_items = []
    failed_count = 0

    logger.info(f"Starting generation of {num_items} SCT items")
    logger.info(f"Using model: {model}")
    logger.info(f"Domains: {', '.join(domains)}")
    logger.info("=" * 70)

    for i in range(num_items):
        # Distribute items across domains for balanced coverage
        domain = domains[i % len(domains)]

        try:
            logger.info(
                f"\n[{i + 1}/{num_items}] Generating SCT item - Domain: {domain}"
            )

            item = generate_sct_item(
                model=model,
                domain=domain,
            )

            generated_items.append(item)
            logger.info(f"✓ Successfully generated and saved item {i + 1}/{num_items}")

        except Exception as e:
            failed_count += 1
            logger.error(f"✗ Failed to generate item {i + 1}/{num_items}: {e}")

    logger.info("=" * 70)
    logger.info("\nGeneration complete!")
    logger.info(f"  Successful: {len(generated_items)}/{num_items}")
    logger.info(f"  Failed: {failed_count}/{num_items}")
    logger.info("  All items saved to: data/generated/")

    return generated_items


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

    # Validate configuration
    if not settings.openai_api_key:
        logger.error("ERROR: OPENAI_API_KEY not configured")
        logger.error("Please set OPENAI_API_KEY in .env file or environment")
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
    logger.info(f"  Number of SCTs: {settings.num_scts_to_generate}")
    logger.info(f"  Model: {settings.model}")
    logger.info(f"  Domains: {', '.join(domains)} ({len(domains)} total)")
    logger.info("  Output directory: data/generated/")
    logger.info("")

    try:
        # Generate SCTs
        items = generate_scts(
            num_items=settings.num_scts_to_generate,
            model=settings.model,
            domains=domains,
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
