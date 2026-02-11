# app.py - Main application entry point
import asyncio
import signal
import sys
import logging
from datetime import datetime

from bot_manager import AutoResponderBot
from config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Global bot instance
bot = None

async def shutdown(signal, loop):
    """Cleanup tasks tied to the service's shutdown."""
    logger.info(f"Received exit signal {signal.name}...")
    
    global bot
    if bot:
        await bot.safe_disconnect()
    
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    logger.info("Shutdown complete")

async def health_monitor(bot_instance):
    """Periodic health monitoring"""
    while True:
        try:
            await asyncio.sleep(Config.HEALTH_CHECK_INTERVAL)
            
            # Perform health check
            healthy = await bot_instance.health_check()
            
            if not healthy:
                logger.warning("Health check failed, may need restart")
            
            # Log stats periodically
            stats = bot_instance.get_stats()
            logger.info(f"Bot Stats: {stats}")
            
        except Exception as e:
            logger.error(f"Health monitor error: {str(e)}")

async def main():
    """Main application function"""
    global bot
    
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Create bot instance
        bot = AutoResponderBot()
        
        # Setup signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(shutdown(s, loop))
            )
        
        # Start health monitor
        health_task = asyncio.create_task(health_monitor(bot))
        
        # Run the bot
        await bot.run()
        
        # Cancel health monitor
        health_task.cancel()
        try:
            await health_task
        except asyncio.CancelledError:
            pass
        
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if running in Railway
    is_railway = os.getenv("RAILWAY_ENVIRONMENT") is not None
    if is_railway:
        print(f"🚄 Railway Environment Detected - Starting Bot at {datetime.now()}")
    
    # Run the application
    asyncio.run(main())
