from __future__ import annotations

# Import all SQLAlchemy models so Base.metadata sees every mapped table.

import backend.context.analytics.adapters.outbound.models  # noqa: F401
import backend.context.course.adapters.outbound.models  # noqa: F401
import backend.context.runtime.adapters.outbound.models  # noqa: F401
import backend.context.schedule.adapters.outbound.models  # noqa: F401
import backend.context.user.adapters.outbound.models  # noqa: F401