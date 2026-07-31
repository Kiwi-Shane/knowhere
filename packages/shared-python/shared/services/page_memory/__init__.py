"""Bounded page-memory navigation assist; never a source-sufficiency decision."""

from shared.services.page_memory.contracts import (
    PAGE_MEMORY_CONTRACT_VERSION,
    PAGE_RETRIEVAL_CONTRACT_VERSION,
    PRECOMPUTED_VISUAL_BACKEND_ID,
    PageMemoryContractError,
)
from shared.services.page_memory.deletion import delete_pages
from shared.services.page_memory.index import ingest_page_memory
from shared.services.page_memory.models import (
    PageMemoryPage,
    PageMemorySnapshot,
    PageRetrievalRequest,
    PageRetrievalResult,
)
from shared.services.page_memory.query import (
    classify_retrieval_disposition,
    retrieve_pages,
)
from shared.services.page_memory.storage import PageMemoryStore

__all__ = [
    "PAGE_MEMORY_CONTRACT_VERSION",
    "PAGE_RETRIEVAL_CONTRACT_VERSION",
    "PRECOMPUTED_VISUAL_BACKEND_ID",
    "PageMemoryContractError",
    "PageMemoryPage",
    "PageMemorySnapshot",
    "PageMemoryStore",
    "PageRetrievalRequest",
    "PageRetrievalResult",
    "classify_retrieval_disposition",
    "delete_pages",
    "ingest_page_memory",
    "retrieve_pages",
]
