"""
Main entry point for Enterprise AI Support Agent.
"""

import asyncio
import sys

from src.utils.config import Config
from src.utils.logging import setup_logging, get_logger
from src.agents.registry import registry


async def main():
    """Main application entry point."""
    
    # Setup logging
    logger = setup_logging()
    
    try:
        # Validate configuration
        Config.validate()
        
        # Log startup
        logger.info("Enterprise AI Support Agent starting...")
        logger.info(f"Registered agents: {registry.get_agent_count()}")
        
        # List active agents
        active_agents = registry.get_active_agents()
        logger.info(f"Active agents: {[agent.name for agent in active_agents]}")
        
        # Demo: List all agents by capability
        from src.agents.registry import AgentCapability
        
        for capability in AgentCapability:
            agent = registry.get_agent_by_capability(capability)
            if agent:
                logger.info(f"{capability.value}: {agent.name}")
        
        logger.info("Enterprise AI Support Agent started successfully")
        logger.info("Ready to process incidents...")
        
        # Keep application running
        # In future versions, this will handle API requests and agent orchestration
        await asyncio.sleep(float('inf'))
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)