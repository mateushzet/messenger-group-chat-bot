import os
from PIL import Image
from collections import OrderedDict
import threading
from logger import logger

class ResourceCache:
    
    def __init__(self, max_size_mb=100):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache = OrderedDict()
        self.current_size = 0
        self.lock = threading.RLock()
        self.stats = {'hits': 0, 'misses': 0, 'evictions': 0}
        
    def _get_image_size(self, image):
        if image.mode == 'RGBA':
            bytes_per_pixel = 4
        elif image.mode == 'RGB':
            bytes_per_pixel = 3
        else:
            bytes_per_pixel = 1
        
        return image.width * image.height * bytes_per_pixel
    
    def get_image(self, path, resize=None, convert_mode="RGBA"):
        with self.lock:
            file_stat = os.stat(path) if os.path.exists(path) else None
            if not file_stat:
                return None
            
            key = f"{path}_{resize}_{convert_mode}_{file_stat.st_mtime}"
            
            if key in self.cache:
                self.cache.move_to_end(key)
                self.stats['hits'] += 1
                return self.cache[key].copy()
            
            try:
                img = Image.open(path)
                if convert_mode:
                    img = img.convert(convert_mode)
                if resize:
                    img = img.resize(resize)
                
                img_size = self._get_image_size(img)
                
                if img_size > self.max_size_bytes * 0.1:
                    self.stats['misses'] += 1
                    return img
                
                while self.current_size + img_size > self.max_size_bytes and self.cache:
                    self._evict_oldest()
                
                self.cache[key] = img
                self.current_size += img_size
                self.stats['misses'] += 1
                
                return img.copy()
                
            except Exception as e:
                logger.error(f"[ResourceCache] Error loading image {path}: {e}")
                return None
    
    def _evict_oldest(self):
        if self.cache:
            key, img = self.cache.popitem(last=False)
            img_size = self._get_image_size(img)
            self.current_size -= img_size
            self.stats['evictions'] += 1
    
    def get_icon(self, path, size=(25, 25)):
        return self.get_image(path, resize=size, convert_mode="RGBA")
    
    def clear(self):
        with self.lock:
            self.cache.clear()
            self.current_size = 0
    
    def get_stats(self):
        with self.lock:
            return {
                'size_mb': self.current_size / (1024 * 1024),
                'items': len(self.cache),
                'hit_rate': self.stats['hits'] / max(1, self.stats['hits'] + self.stats['misses']),
                **self.stats
            }