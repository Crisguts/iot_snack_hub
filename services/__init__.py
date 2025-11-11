import os

# Mock mode active if no GPIO hardware or forced
MOCK_MODE = os.getenv("MOCK_MODE", "True").lower() == "true"
