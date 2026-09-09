"""Keep continuity unit tests isolated from optional application integrations."""

import os

# Unit/contract tests must never require production Supabase credentials.
# The application connection layer validates presence of these settings at
# import time, so provide inert test-only values before test modules import it.
os.environ.setdefault("SUPABASE_URL", "https://unit-test.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-only-anon-key")
