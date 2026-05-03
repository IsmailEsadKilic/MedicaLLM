"""
Asynchronous PDF downloader for PubMed articles.

Downloads PDFs in the background without blocking LLM responses.
Uses a thread pool to handle downloads concurrently.
Implements LRU cache with 1GB size limit on disk.
"""
import asyncio
import hashlib
import urllib.request
import urllib.error
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, List, Tuple
from logging import getLogger
from datetime import datetime

from ..config import settings

logger = getLogger(__name__)

# Thread pool for background downloads
_download_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="pdf_download")

# PDF storage directory
PDF_STORAGE_DIR = Path(settings.pdf_dir) / "pubmed_downloads"
PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Cache configuration
MAX_CACHE_SIZE_GB = 1.0  # Maximum cache size
TARGET_SIZE_GB = 0.9     # Evict down to this size when limit reached

# Metadata cache: {filename: {"pmid": str, "doi": str, "size": int, "mtime": float}}
_metadata_cache: Dict[str, dict] = {}
_cache_lock = asyncio.Lock()


def _generate_pdf_filename(pmid: str, doi: str = "") -> str:
    """Generate a unique filename for a PDF based on PMID and DOI."""
    # Use PMID as primary identifier, hash DOI as secondary
    if doi:
        doi_hash = hashlib.md5(doi.encode()).hexdigest()[:8]
        return f"pubmed_{pmid}_{doi_hash}.pdf"
    return f"pubmed_{pmid}.pdf"


def _get_directory_size_gb() -> float:
    """Calculate total size of PDF directory in GB."""
    total_size = 0
    try:
        for entry in PDF_STORAGE_DIR.iterdir():
            if entry.is_file() and entry.suffix == '.pdf':
                total_size += entry.stat().st_size
    except Exception as e:
        logger.error(f"[PDF CACHE] Error calculating directory size: {e}")
    
    return total_size / (1024 ** 3)  # Convert bytes to GB


def _scan_directory() -> None:
    """
    Scan PDF directory and build metadata cache.
    Called on startup to initialize cache state.
    """
    global _metadata_cache
    _metadata_cache.clear()
    
    try:
        for entry in PDF_STORAGE_DIR.iterdir():
            if entry.is_file() and entry.suffix == '.pdf':
                stat = entry.stat()
                
                # Extract PMID from filename (format: pubmed_{pmid}_{hash}.pdf or pubmed_{pmid}.pdf)
                filename = entry.name
                parts = filename.replace('.pdf', '').split('_')
                pmid = parts[1] if len(parts) >= 2 else "unknown"
                
                _metadata_cache[filename] = {
                    "pmid": pmid,
                    "doi": "",  # Not stored in filename, will be provided on access
                    "size": stat.st_size,
                    "mtime": stat.st_mtime
                }
        
        size_gb = _get_directory_size_gb()
        logger.info(f"[PDF CACHE] Scanned directory: {len(_metadata_cache)} PDFs, {size_gb:.2f} GB")
    except Exception as e:
        logger.error(f"[PDF CACHE] Error scanning directory: {e}")


def _update_access_time(pdf_path: Path) -> None:
    """Update file modification time to track LRU."""
    try:
        # Touch the file to update mtime
        pdf_path.touch(exist_ok=True)
        
        # Update metadata cache
        filename = pdf_path.name
        if filename in _metadata_cache:
            _metadata_cache[filename]["mtime"] = pdf_path.stat().st_mtime
    except Exception as e:
        logger.warning(f"[PDF CACHE] Error updating access time: {e}")


def _evict_lru_pdfs(target_size_gb: float) -> None:
    """
    Evict least recently used PDFs until directory size is below target.
    
    Args:
        target_size_gb: Target size in GB to evict down to
    """
    current_size_gb = _get_directory_size_gb()
    
    if current_size_gb <= target_size_gb:
        return
    
    logger.info(f"[PDF CACHE] Evicting PDFs: current={current_size_gb:.2f}GB, target={target_size_gb:.2f}GB")
    
    # Get all PDFs sorted by modification time (oldest first)
    pdf_files: List[Tuple[Path, float, int]] = []
    
    try:
        for entry in PDF_STORAGE_DIR.iterdir():
            if entry.is_file() and entry.suffix == '.pdf':
                stat = entry.stat()
                pdf_files.append((entry, stat.st_mtime, stat.st_size))
    except Exception as e:
        logger.error(f"[PDF CACHE] Error listing PDFs for eviction: {e}")
        return
    
    # Sort by mtime (oldest first)
    pdf_files.sort(key=lambda x: x[1])
    
    # Evict oldest PDFs until we reach target size
    evicted_count = 0
    freed_bytes = 0
    
    for pdf_path, mtime, size in pdf_files:
        if current_size_gb <= target_size_gb:
            break
        
        try:
            filename = pdf_path.name
            pdf_path.unlink()
            
            # Remove from metadata cache
            if filename in _metadata_cache:
                del _metadata_cache[filename]
            
            freed_bytes += size
            current_size_gb = _get_directory_size_gb()
            evicted_count += 1
            
            logger.info(f"[PDF CACHE] Evicted: {filename} ({size / (1024**2):.2f} MB)")
        except Exception as e:
            logger.error(f"[PDF CACHE] Error evicting {pdf_path.name}: {e}")
    
    logger.info(f"[PDF CACHE] Eviction complete: {evicted_count} PDFs, {freed_bytes / (1024**2):.2f} MB freed")


def _ensure_cache_size_limit(new_file_size_bytes: int = 0) -> None:
    """
    Ensure cache size is below limit before adding new file.
    
    Args:
        new_file_size_bytes: Size of file about to be added (for proactive eviction)
    """
    current_size_gb = _get_directory_size_gb()
    new_file_size_gb = new_file_size_bytes / (1024 ** 3)
    
    # Check if we need to evict
    if current_size_gb + new_file_size_gb > MAX_CACHE_SIZE_GB:
        logger.info(f"[PDF CACHE] Cache limit reached: {current_size_gb:.2f}GB + {new_file_size_gb:.2f}GB > {MAX_CACHE_SIZE_GB}GB")
        _evict_lru_pdfs(TARGET_SIZE_GB)


def _download_pdf_sync(pmid: str, doi: str = "", url: str = "", pmc_id: str = "") -> Optional[Path]:
    """
    Synchronous PDF download function (runs in thread pool).
    
    Attempts to download PDF from:
    1. Direct URL if provided
    2. PubMed Central with PMC ID (if available - most reliable)
    3. PubMed Central with PMID (converts PMID to PMC automatically)
    4. Europe PMC API
    5. DOI resolver (may hit paywall)
    
    Returns path to downloaded PDF or None if download failed.
    """
    filename = _generate_pdf_filename(pmid, doi)
    pdf_path = PDF_STORAGE_DIR / filename
    
    # Check if already downloaded
    if pdf_path.exists():
        logger.info(f"[PDF DOWNLOAD] PDF already exists: {filename}")
        _update_access_time(pdf_path)
        return pdf_path
    
    # Try download sources in order
    download_urls = []
    
    # 1. Try direct URL if provided
    if url:
        download_urls.append(url)
    
    # 2. Try PubMed Central with PMC ID (most reliable if available)
    if pmc_id:
        # PMC ID format: "PMC7234567" or just "7234567"
        pmc_num = pmc_id.replace("PMC", "")
        # Use the correct PMC PDF URL format
        download_urls.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_num}/pdf/main.pdf")
        download_urls.append(f"https://europepmc.org/articles/PMC{pmc_num}?pdf=render")
    
    # 3. Try Europe PMC API with PMID (often works even without PMC ID)
    download_urls.append(f"https://europepmc.org/articles/MED/{pmid}?pdf=render")
    
    # 4. Try DOI resolver (may hit paywall but worth trying)
    if doi:
        download_urls.append(f"https://doi.org/{doi}")
    
    pdf_data = None
    
    for attempt_url in download_urls:
        try:
            logger.info(f"[PDF DOWNLOAD] Attempting download from: {attempt_url}")
            
            req = urllib.request.Request(
                attempt_url,
                headers={
                    "User-Agent": f"{settings.pubmed_tool_name}/1.0 ({settings.pubmed_email})"
                }
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                content_type = response.headers.get("Content-Type", "")
                
                # Check if response is actually a PDF
                if "application/pdf" not in content_type.lower():
                    logger.warning(f"[PDF DOWNLOAD] Not a PDF: {content_type}")
                    continue
                
                # Download PDF
                pdf_data = response.read()
                
                # Verify it's a valid PDF (starts with %PDF)
                if not pdf_data.startswith(b"%PDF"):
                    logger.warning(f"[PDF DOWNLOAD] Invalid PDF data")
                    pdf_data = None
                    continue
                
                logger.info(f"[PDF DOWNLOAD] Successfully downloaded: {filename} ({len(pdf_data)} bytes)")
                break
        
        except urllib.error.HTTPError as e:
            logger.warning(f"[PDF DOWNLOAD] HTTP error {e.code} for {attempt_url}")
            continue
        except Exception as e:
            logger.warning(f"[PDF DOWNLOAD] Download failed for {attempt_url}: {e}")
            continue
    
    if not pdf_data:
        logger.error(f"[PDF DOWNLOAD] All download attempts failed for PMID {pmid}")
        return None
    
    # Ensure cache size limit before saving
    _ensure_cache_size_limit(len(pdf_data))
    
    # Save to disk
    try:
        with open(pdf_path, "wb") as f:
            f.write(pdf_data)
        
        # Add to metadata cache
        stat = pdf_path.stat()
        _metadata_cache[filename] = {
            "pmid": pmid,
            "doi": doi,
            "size": stat.st_size,
            "mtime": stat.st_mtime
        }
        
        logger.info(f"[PDF DOWNLOAD] Saved to disk: {filename}")
        return pdf_path
    except Exception as e:
        logger.error(f"[PDF DOWNLOAD] Error saving PDF: {e}")
        return None


async def download_pdf_async(pmid: str, doi: str = "", url: str = "", pmc_id: str = "") -> Optional[Path]:
    """
    Asynchronously download a PDF without blocking.
    
    Args:
        pmid: PubMed ID
        doi: Digital Object Identifier (optional)
        url: Direct PDF URL (optional)
        pmc_id: PubMed Central ID (optional, e.g., "PMC7234567")
    
    Returns:
        Path to downloaded PDF or None if download failed
    """
    loop = asyncio.get_event_loop()
    
    try:
        pdf_path = await loop.run_in_executor(
            _download_executor,
            _download_pdf_sync,
            pmid,
            doi,
            url,
            pmc_id
        )
        return pdf_path
    except Exception as e:
        logger.error(f"[PDF DOWNLOAD] Async download failed for PMID {pmid}: {e}")
        return None


def get_pdf_path(pmid: str, doi: str = "") -> Optional[Path]:
    """
    Check if a PDF has already been downloaded.
    Updates access time if found (for LRU tracking).
    
    Returns path if exists, None otherwise.
    """
    filename = _generate_pdf_filename(pmid, doi)
    pdf_path = PDF_STORAGE_DIR / filename
    
    if pdf_path.exists():
        _update_access_time(pdf_path)
        return pdf_path
    return None


def initialize_cache() -> None:
    """
    Initialize PDF cache on startup.
    Scans directory and builds metadata cache.
    """
    logger.info("[PDF CACHE] Initializing PDF cache...")
    _scan_directory()
    
    # Check if we need initial eviction
    current_size_gb = _get_directory_size_gb()
    if current_size_gb > MAX_CACHE_SIZE_GB:
        logger.warning(f"[PDF CACHE] Cache size exceeds limit: {current_size_gb:.2f}GB > {MAX_CACHE_SIZE_GB}GB")
        _evict_lru_pdfs(TARGET_SIZE_GB)
    
    logger.info("[PDF CACHE] Cache initialization complete")


def schedule_pdf_download(pmid: str, doi: str = "", url: str = "") -> None:
    """
    Schedule a PDF download in the background (fire-and-forget).
    
    This doesn't block or return anything - just starts the download.
    """
    asyncio.create_task(download_pdf_async(pmid, doi, url))
    logger.info(f"[PDF DOWNLOAD] Scheduled background download for PMID {pmid}")
