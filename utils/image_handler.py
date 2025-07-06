"""
Image Handler for TG-Trade Suite
Handles image download, validation, processing, and cleanup
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import uuid
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


class ImageHandler:
    """Handles image operations for chart analysis."""

    def __init__(self) -> None:
        # Where downloaded chart images are stored
        self.upload_folder = Path(os.getenv("UPLOAD_FOLDER", "/app/uploads"))

        # 5 MB default size cap (can override via env)
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE", "5242880"))

        # seconds before image auto-deletion
        self.cleanup_delay = int(os.getenv("IMAGE_RETENTION_SECONDS", "60"))

        self.allowed_extensions = {".png", ".jpg", ".jpeg"}

        # Ensure upload dir exists
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        logger.info("📁 Image handler initialized – Upload folder: %s", self.upload_folder)

    # ------------------------------------------------------------------ #
    # Telegram download / validation                                     #
    # ------------------------------------------------------------------ #

    async def download_telegram_image(
        self,
        telegram_file,
        file_extension: str = "jpg",
    ) -> Optional[str]:
        """
        Download image from Telegram and save it locally.

        Args:
            telegram_file: Telegram ``File`` object.
            file_extension: file suffix, e.g. ``jpg`` or ``png``.

        Returns:
            Absolute path to the stored file, or *None* on failure.
        """
        try:
            file_id = uuid.uuid4().hex
            filename = f"chart_{file_id}.{file_extension.lower()}"
            file_path = self.upload_folder / filename

            logger.info("📥 Downloading image: %s", filename)
            await telegram_file.download_to_drive(str(file_path))

            # Verify something was actually written
            if not file_path.exists() or file_path.stat().st_size == 0:
                logger.error("❌ Download failed: %s", filename)
                return None

            logger.info(
                "✅ Downloaded successfully: %s (%d bytes)",
                filename,
                file_path.stat().st_size,
            )

            # Schedule automatic removal
            asyncio.create_task(self._schedule_cleanup(file_path))
            return str(file_path)

        except Exception as exc:  # noqa: BLE001
            logger.error("❌ Error downloading image: %s", exc)
            return None

    async def validate_and_process_image(self, file_path: str) -> Tuple[bool, str]:
        """
        Full validation pipeline used by the *bot* before passing the chart
        to OpenAI. Performs size checks, basic dimension checks, and rescales
        ultra-large pictures down to ≤ 2048 px.

        Returns:
            ``(is_valid, reason_or_info)``
        """
        try:
            p = Path(file_path)

            if not p.exists():
                return False, "Image file not found"

            size_bytes = p.stat().st_size
            if size_bytes > self.max_file_size:
                return (
                    False,
                    f"Image too large: {size_bytes/1_048_576:.1f} MB "
                    f"(max {self.max_file_size/1_048_576:.1f} MB)",
                )
            if size_bytes < 1024:  # < 1 KB
                return False, "Image file too small"

            if p.suffix.lower() not in self.allowed_extensions:
                return False, f"Unsupported format: {p.suffix}"

            # Basic PIL verification + optional down-scale
            try:
                with Image.open(p) as im:
                    w, h = im.size
                    if w < 100 or h < 100:
                        return False, "Image too small (minimum 100×100 px)"

                    if w > 4096 or h > 4096:
                        logger.info("🔧 Resizing large image: %dx%d", w, h)
                        im.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
                        im.save(p, optimize=True, quality=85)
                        logger.info("✅ Image resized and optimized")

                    logger.info("✅ Image validated: %dx%d, %d bytes", w, h, size_bytes)
                    return True, f"Valid image: {w}×{h}px"

            except Exception as pil_error:  # noqa: BLE001
                return False, f"Invalid image file: {pil_error}"

        except Exception as exc:  # noqa: BLE001
            logger.error("❌ Error validating image: %s", exc)
            return False, f"Validation error: {exc}"

    # ------------------------------------------------------------------ #
    # Cleanup helpers                                                    #
    # ------------------------------------------------------------------ #

    async def _schedule_cleanup(self, file_path: Path) -> None:
        """Remove *file_path* after ``self.cleanup_delay`` seconds."""
        try:
            logger.info("⏰ Scheduled cleanup for %s in %ds", file_path.name, self.cleanup_delay)
            await asyncio.sleep(self.cleanup_delay)
            await self._cleanup_file(file_path)
        except Exception as exc:  # noqa: BLE001
            logger.error("❌ Error in cleanup scheduler: %s", exc)

    async def _cleanup_file(self, file_path: Path) -> None:
        """Delete a single file if it still exists."""
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info("🗑️ Removed: %s", file_path.name)
        except Exception as exc:  # noqa: BLE001
            logger.error("❌ Error deleting %s: %s", file_path, exc)

    async def cleanup_old_files(self) -> None:
        """Remove all chart_* files in ``self.upload_folder``."""
        try:
            removed = 0
            for fp in self.upload_folder.glob("chart_*"):
                if fp.is_file():
                    await self._cleanup_file(fp)
                    removed += 1
            if removed:
                logger.info("🗑️ Cleaned up %d old files", removed)
        except Exception as exc:  # noqa: BLE001
            logger.error("❌ Error in periodic cleanup: %s", exc)


# ----------------------------------------------------------------------
#  Extra synchronous helpers required by utils.ai_analyzer
# ----------------------------------------------------------------------


def img_to_base64(path: os.PathLike | str) -> str:
    """
    Return *just* the base-64 representation of an image file
    (**without** the ``data:image/...;base64,`` prefix).
    """
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


def validate_image(path: os.PathLike | str, min_px: int = 100) -> None:
    """
    Lightweight validation used by the analyser.

    Raises
    ------
    ValueError
        If the image is smaller than *min_px* in either dimension or
        cannot be opened.
    """
    try:
        with Image.open(path) as im:
            w, h = im.size
            if w < min_px or h < min_px:
                raise ValueError(f"image too small: {w}×{h}px")
    except Exception as exc:  # noqa: BLE001
        # Re-raise as ValueError so callers only catch one type
        raise ValueError(str(exc)) from exc


# Singleton instance used across the bot
image_handler = ImageHandler()

