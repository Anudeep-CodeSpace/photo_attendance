import asyncio

# ---------------------------------------------------------
# Global lock for registration
# Ensures:
#  - /register_students cannot run in parallel
#  - /upload_photo waits politely during registration
# ---------------------------------------------------------
registration_lock = asyncio.Lock()