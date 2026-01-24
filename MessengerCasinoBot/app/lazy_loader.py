import os
from PIL import Image

class LazyAnimationLoader:

    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or "/tmp/anim_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.frame_cache = {}
        self.last_frame_cache = {}
        
    def get_last_frame(self, anim_path, use_cache=True):
        if not os.path.exists(anim_path):
            return None
        
        file_stat = os.stat(anim_path)
        cache_key = f"{os.path.basename(anim_path)}_{file_stat.st_size}_{file_stat.st_mtime}"
        cache_path = os.path.join(self.cache_dir, f"{cache_key}_last.webp")
        
        if use_cache and cache_key in self.last_frame_cache:
            if self.last_frame_cache[cache_key]['mtime'] == file_stat.st_mtime:
                return self.last_frame_cache[cache_key]['frame'].copy()
        
        if use_cache and os.path.exists(cache_path):
            if os.path.getmtime(cache_path) >= file_stat.st_mtime:
                try:
                    frame = Image.open(cache_path).convert("RGBA")
                    self.last_frame_cache[cache_key] = {
                        'frame': frame.copy(),
                        'mtime': file_stat.st_mtime
                    }
                    return frame
                except:
                    pass
        
        frame = self._extract_last_frame_fast(anim_path)
        
        if frame:
            self.last_frame_cache[cache_key] = {
                'frame': frame.copy(),
                'mtime': file_stat.st_mtime
            }
            
            if use_cache:
                frame.save(cache_path, "WEBP", quality=85)
            
            if len(self.last_frame_cache) > 50:
                oldest_key = next(iter(self.last_frame_cache))
                del self.last_frame_cache[oldest_key]
        
        return frame
    
    def _extract_last_frame_fast(self, anim_path):
        try:
            with Image.open(anim_path) as img:
                if not getattr(img, "is_animated", False):
                    return img.convert("RGBA")
                
                try:
                    img.seek(img.n_frames - 1)
                    return img.convert("RGBA")
                except:
                    pass
                
                last_frame = None
                frame_count = img.n_frames
                
                if frame_count > 50:
                    step = frame_count // 50
                    for i in range(0, frame_count, step):
                        img.seek(min(i, frame_count - 1))
                        last_frame = img.copy()
                else:
                    for i in range(frame_count):
                        img.seek(i)
                        last_frame = img.copy()
                
                return last_frame.convert("RGBA") if last_frame else None
                
        except Exception as e:
            print(f"Error extracting last frame: {e}")
            return None
    
    def get_frame_at_index(self, anim_path, frame_index):
        key = f"{anim_path}_{frame_index}"
        
        if key in self.frame_cache:
            return self.frame_cache[key].copy()
        
        try:
            with Image.open(anim_path) as img:
                if frame_index < img.n_frames:
                    img.seek(frame_index)
                    frame = img.convert("RGBA")
                    self.frame_cache[key] = frame.copy()
                    
                    if len(self.frame_cache) > 100:
                        self.frame_cache.pop(next(iter(self.frame_cache)))
                    
                    return frame
        except:
            return None
    
    def get_frame_count(self, anim_path):
        try:
            with Image.open(anim_path) as img:
                return getattr(img, "n_frames", 1)
        except:
            return 1
    
    def preload_animation_frames(self, anim_path, frame_indices):
        frames = []
        for idx in frame_indices:
            frame = self.get_frame_at_index(anim_path, idx)
            if frame:
                frames.append(frame)
        return frames