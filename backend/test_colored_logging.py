"""
Test script to verify colored logging works correctly.
Run this to see colored output in console.
"""
import logging
from src.colored_logging import setup_colored_logging

# Setup colored logging
setup_colored_logging(
    log_level=logging.DEBUG,
    log_file="logs/test.log",
)

# Get logger using standard logging module
logger = logging.getLogger(__name__)

# Test all log levels
logger.debug("This is a DEBUG message 🐛")
logger.info("This is an INFO message 🤓")
logger.success("This is a SUCCESS message 🥹")  # Custom level
logger.warning("This is a WARNING message 😳")
logger.error("This is an ERROR message 😱")
logger.critical("This is a CRITICAL message 💀")

# Test with component tags (like in your app)
logger.info("[SESSION QUERY] ========== NEW QUERY REQUEST ==========")
logger.debug("[SESSION] Query length: 42 chars")
logger.info("[TOOL] get_drug_info: drug_name='Aspirin'")
logger.debug("[DRUG SERVICE] Fetching drug records from database")
logger.info("[SESSION] Agent invocation completed in 1234.56ms")
logger.warning("[TOOL] Drug not found: XYZ123")
logger.error("[DRUG SERVICE] Database connection failed")

# Test exception logging
try:
    raise ValueError("This is a test exception")
except Exception as e:
    logger.error("An error occurred", exc_info=True)

print("\n✅ Colored logging test complete!")
print("📄 Check logs/test.log to see plain text output (no colors)")
print("🖥️  Console output above should be colored")
