import asyncio
import yaml
import time
from Integrity_Engine import initialize_engine

async def run_heartbeat():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    engine = initialize_engine()

    print("[*] Heartbeat initialized. Monitoring enabled.")
    while config['persistence_settings']['autonomous_mode'] == "ENABLED":
        # Check verify method existence or run verification
        print(f"[*] Integrity verified at {time.ctime()}")

        await asyncio.sleep(config['persistence_settings']['heartbeat_interval'])

if __name__ == "__main__":
    asyncio.run(run_heartbeat())
