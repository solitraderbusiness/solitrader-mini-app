"""
Image Handler for TG-Trade Suite
Handles image download, processing, and cleanup
"""
import os
import uuid
import logging
import asyncio
from pathlib import Path
from typing import Optional, Tuple
import aiofiles
from PIL import Image

logger = logging.getLogger(__name__)

class ImageHandler:
    """Handles image operations for chart analysis"""
    
    def __init__(self):
        self.upload_folder = Path(os.getenv('UPLOAD_FOLDER', '/app/uploads'))
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE', '5242880'))  # 5MB
        self.cleanup_delay = int(os.getenv('IMAGE_RETENTION_SECONDS', '60'))
        self.allowed_extensions = {'.png', '.jpg', '.jpeg'}
        
        # Ensure upload folder exists
        self.upload_folder.mkdir(exist_ok=True)
        logger.info(f"📁 Image handler initialized - Upload folder: {self.upload_folder}")
    
    async def download_telegram_image(self, telegram_file, file_extension: str = 'jpg') -> Optional[str]:
        """
        Download image from Telegram and save locally
        
        Args:
            telegram_file: Telegram file object
            file_extension: File extension (jpg, png, etc.)
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            filename = f"chart_{file_id}.{file_extension}"
            file_path = self.upload_folder / filename
            
            logger.info(f"📥 Downloading image: {filename}")
            
            # Download file from Telegram
            await telegram_file.download_to_drive(str(file_path))
            
            # Verify file was created and has content
            if not file_path.exists() or file_path.stat().st_size == 0:
                logger.error(f"❌ Download failed: {filename}")
                return None
            
            file_size = file_path.stat().st_size
            logger.info(f"✅ Downloaded successfully: {filename} ({file_size} bytes)")
            
            # Schedule cleanup
            asyncio.create_task(self._schedule_cleanup(str(file_path)))
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"❌ Error downloading image: {e}")
            return None
    
    async def validate_and_process_image(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate and process image for analysis
        
        Args:
            file_path: Path to image file
            
        Returns:
            (is_valid, message)
        """
        try:
            file_path_obj = Path(file_path)
            
            # Check if file exists
            if not file_path_obj.exists():
                return False, "Image file not found"
            
            # Check file size
            file_size = file_path_obj.stat().st_size
            if file_size > self.max_file_size:
                return False, f"Image too large: {file_size/1024/1024:.1f}MB (max: {self.max_file_size/1024/1024:.1f}MB)"
            
            if file_size < 1024:  # Less than 1KB
                return False, "Image file too small"
            
            # Check file extension
            if file_path_obj.suffix.lower() not in self.allowed_extensions:
                return False, f"Unsupported format: {file_path_obj.suffix}"
            
            # Try to open and validate image
            try:
                with Image.open(file_path) as img:
                    # Check image dimensions
                    width, height = img.size
                    if width < 100 or height < 100:
                        return False, "Image too small (minimum 100x100 pixels)"
                    
                    if width > 4096 or height > 4096:
                        # Resize large images
                        logger.info(f"🔧 Resizing large image: {width}x{height}")
                        img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
                        img.save(file_path, optimize=True, quality=85)
                        logger.info(f"✅ Image resized and optimized")
                    
                    logger.info(f"✅ Image validated: {width}x{height}, {file_size} bytes")
                    return True, f"Valid image: {width}x{height}"
                    
            except Exception as img_error:
                return False, f"Invalid image file: {str(img_error)}"
            
        except Exception as e:
            logger.error(f"❌ Error validating image: {e}")
            return False, f"Validation error: {str(e)}"
    
    async def _schedule_cleanup(self, file_path: str):
        """Schedule file cleanup after delay"""
        try:
            logger.info(f"⏰ Scheduled cleanup for {Path(file_path).name} in {self.cleanup_delay}s")
            await asyncio.sleep(self.cleanup_delay)
            await self._cleanup_file(file_path)
        except Exception as e:
            logger.error(f"❌ Error in cleanup scheduler: {e}")
    
    async def _cleanup_file(self, file_path: str):
        """Clean up a single file"""
        try:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                file_path_obj.unlink()
                logger.info(f"🗑️ Cleaned up: {file_path_obj.name}")
            else:
                logger.info(f"📁 File already removed: {file_path_obj.name}")
        except Exception as e:
            logger.error(f"❌ Error cleaning up {file_path}: {e}")
    
    async def cleanup_old_files(self):
        """Clean up old files (called periodically)"""
        try:
            count = 0
            for file_path in self.upload_folder.glob("chart_*"):
                if file_path.is_file():
                    await self._cleanup_file(str(file_path))
                    count += 1
            
            if count > 0:
                logger.info(f"🗑️ Cleaned up {count} old files")
                
        except Exception as e:
            logger.error(f"❌ Error in periodic cleanup: {e}")

# Create singleton instance
image_handler = ImageHandler()
