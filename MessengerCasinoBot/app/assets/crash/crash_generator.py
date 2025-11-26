from PIL import Image, ImageDraw, ImageFilter
import math
import random

def generate_crash_animation(output_file="crash_animation.webp", size=(400, 400)):
    width, height = size
    crash_target = 100.0
    
    def calculate_multiplier(t):
        return 1 + 0.02 * math.pow(t, 1.8 + 0.015 * t)
    
    def find_time_for_multiplier(target_multiplier, max_time=100, step=0.01):
        t = 0
        while t <= max_time:
            if calculate_multiplier(t) >= target_multiplier:
                return t
            t += step
        return max_time
    
    real_time_to_crash = find_time_for_multiplier(100.0)
    target_animation_duration = 20.0
    time_scale_factor = real_time_to_crash / target_animation_duration
    

    def generate_smooth_frame_times():
        frame_times = []
        
        multiplier = 1.00
        while multiplier <= 3.00:
            t = find_time_for_multiplier(multiplier)
            frame_times.append(t)
            multiplier += 0.01
            multiplier = round(multiplier, 2)
        
        multiplier = 3.00
        while multiplier <= 10.00:
            t = find_time_for_multiplier(multiplier)
            frame_times.append(t)
            multiplier += 0.05
            multiplier = round(multiplier, 2)
        
        multiplier = 10.00
        while multiplier <= 20.00:
            t = find_time_for_multiplier(multiplier)
            frame_times.append(t)
            multiplier += 0.10
            multiplier = round(multiplier, 2)
        
        multiplier = 20.00
        while multiplier <= 100.00:
            t = find_time_for_multiplier(multiplier)
            frame_times.append(t)
            multiplier += 1.00
        
        return frame_times
    
    real_frame_times = generate_smooth_frame_times()
    total_frames = len(real_frame_times)
    
    frame_times = [t / time_scale_factor for t in real_frame_times]
    
    images = []
    display_max_time = 8
    display_max_multiplier = 1.5
    
    class SparkSystem:
        def __init__(self):
            self.sparks = []
            
        def add_sparks(self, x, y, count=5, intensity=1.0):
            for _ in range(count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(0.5, 2.0) * intensity
                life = random.uniform(10, 25) * intensity
                size = random.uniform(2, 4) * intensity
                self.sparks.append({
                    'x': x, 'y': y,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'life': life,
                    'max_life': life,
                    'size': size,
                    'color': random.choice([
                        (255, 255, 200), (255, 200, 100),
                        (255, 100, 50), (100, 255, 200),
                    ])
                })
                
        def update(self):
            for spark in self.sparks[:]:
                spark['x'] += spark['vx']
                spark['y'] += spark['vy']
                spark['vy'] += 0.1
                spark['vx'] *= 0.98
                spark['life'] -= 1
                if spark['life'] <= 0:
                    self.sparks.remove(spark)
                    
        def draw(self, draw):
            for spark in self.sparks:
                alpha = int(255 * (spark['life'] / spark['max_life']))
                size = spark['size'] * (spark['life'] / spark['max_life'])
                color = (*spark['color'], alpha)
                draw.ellipse([
                    spark['x'] - size, spark['y'] - size,
                    spark['x'] + size, spark['y'] + size
                ], fill=color)
    
    spark_system = SparkSystem()
    
    class SpecialEffects:
        def __init__(self):
            self.active_effects = []
            self.integer_effects = {}
            
        def add_effect(self, multiplier, effect_type, x=None, y=None):
            self.active_effects.append({
                'multiplier': multiplier,
                'type': effect_type,
                'x': x,
                'y': y,
                'life': 25,
                'max_life': 25
            })
            
        def add_integer_effect(self, multiplier):
            self.integer_effects[multiplier] = {
                'life': 15,
                'max_life': 15
            }
            
        def update(self):
            for effect in self.active_effects[:]:
                effect['life'] -= 1
                if effect['life'] <= 0:
                    self.active_effects.remove(effect)
            
            for multiplier in list(self.integer_effects.keys()):
                self.integer_effects[multiplier]['life'] -= 1
                if self.integer_effects[multiplier]['life'] <= 0:
                    del self.integer_effects[multiplier]
                    
        def draw(self, draw, current_tip_x, current_tip_y, current_multiplier):
            for effect in self.active_effects:
                progress = effect['life'] / effect['max_life']
                alpha = int(255 * progress)
                
                if effect['type'] == 'milestone_tip':
                    x, y = current_tip_x, current_tip_y
                    
                    if progress > 0.3:
                        text = f"{effect['multiplier']:.1f}x!"
                        text_bbox = draw.textbbox((0, 0), text)
                        text_width = text_bbox[2] - text_bbox[0]
                        text_size = 22
                        
                        for i in range(3):
                            glow_alpha = 100 - i * 30
                            draw.text((x - text_width//2 - i, y - 42 - i), 
                                     text, fill=(255, 255, 255, glow_alpha), font_size=text_size)
                            draw.text((x - text_width//2 + i, y - 42 - i), 
                                     text, fill=(255, 255, 255, glow_alpha), font_size=text_size)
                            draw.text((x - text_width//2 - i, y - 42 + i), 
                                     text, fill=(255, 255, 255, glow_alpha), font_size=text_size)
                            draw.text((x - text_width//2 + i, y - 42 + i), 
                                     text, fill=(255, 255, 255, glow_alpha), font_size=text_size)
                        
                        draw.text((x - text_width//2, y - 42), 
                                 text, fill=(255, 255, 255, alpha), font_size=text_size)
                    
                    radius = 20 * (1 - progress)
                    for i in range(2):
                        wave_radius = radius + i * 8
                        wave_alpha = alpha - i * 100
                        if wave_alpha > 0:
                            draw.ellipse([x - wave_radius, y - wave_radius, 
                                        x + wave_radius, y + wave_radius], 
                                       outline=(255, 255, 255, wave_alpha), width=2)
    
    special_effects = SpecialEffects()
    
    milestone_multipliers = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    triggered_milestones = set()
    last_integer = 0

    frame_report = []

    for frame in range(len(frame_times)):
        elapsed_time = frame_times[frame]
        real_elapsed_time = real_frame_times[frame]
        target_multiplier = calculate_multiplier(real_elapsed_time)
        final_multiplier = min(target_multiplier, crash_target)
        
        frame_report.append({
            'frame': frame,
            'time': elapsed_time,
            'multiplier': final_multiplier
        })
    
    duration = max(50, min(100, int(3000 / total_frames)))
    
    # Main animation loop
    for frame in range(len(frame_times)):
        elapsed_time = frame_times[frame]
        real_elapsed_time = real_frame_times[frame]
        target_multiplier = calculate_multiplier(real_elapsed_time)
        
        img = Image.new("RGB", size, "#0f1419")
        draw = ImageDraw.Draw(img)
        
        # Dynamic axis scaling 
        if elapsed_time > display_max_time * 0.7:
            display_max_time = min(display_max_time * 1.02, 80)
        if target_multiplier > display_max_multiplier * 0.6:
            display_max_multiplier = min(display_max_multiplier * 1.02, 150)
        
        padding = 50
        graph_width = width - 2 * padding
        graph_height = height - 2 * padding
        
        graph_center_x = padding + graph_width // 2
        
        def map_time_to_x(time):
            return padding + (time / display_max_time) * graph_width
        
        def map_multiplier_to_y(multiplier):
            return padding + graph_height - ((multiplier - 1) / (display_max_multiplier - 1)) * graph_height
        
        # Gradient background
        for y in range(height):
            ratio = y / height
            r = int(15 + 5 * ratio)
            g = int(20 + 10 * ratio)
            b = int(25 + 15 * ratio)
            draw.line([0, y, width, y], fill=(r, g, b))
        
        # Grid lines
        for i in range(1, 8):
            y = padding + (i / 8) * graph_height
            draw.line([padding, y, width - padding, y], fill="#1a2430", width=1)
            x = padding + (i / 8) * graph_width
            draw.line([x, padding, x, height - padding], fill="#1a2430", width=1)
        
        # Y-axis labels
        multiplier_levels = [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 25.0, 50.0, 75.0, 100.0]
        for level in multiplier_levels:
            if level <= display_max_multiplier:
                y = map_multiplier_to_y(level)
                if padding <= y <= height - padding:
                    draw.line([padding - 5, y, padding + 2, y], fill="#2a3a4a", width=2)
                    level_text = f"{level:.1f}x"
                    draw.text((padding - 45, y - 6), level_text, fill="#cccccc")
        
        # X-axis labels
        time_interval = max(1, display_max_time // 8)
        time_levels = [i * time_interval for i in range(int(display_max_time / time_interval) + 1)]
        for level in time_levels:
            if level <= display_max_time:
                x = map_time_to_x(level)
                if padding <= x <= width - padding:
                    draw.line([x, height - padding - 2, x, height - padding + 5], fill="#2a3a4a", width=2)
                    if level == int(level):
                        draw.text((x - 8, height - padding + 10), f"{int(level)}s", fill="#cccccc", font_size=9)
        
        # Main axes
        draw.line([padding, height - padding, width - padding, height - padding], fill="#2a3a4a", width=2)
        draw.line([padding, padding, padding, height - padding], fill="#2a3a4a", width=2)
        
        # Generate graph points
        segments = min(300, int(elapsed_time * 10))
        max_t = min(elapsed_time, display_max_time)
        
        points = []
        for i in range(segments + 1):
            t = (max_t / segments) * i if segments > 0 else 0
            real_t = t * time_scale_factor
            m = calculate_multiplier(real_t)
            x = map_time_to_x(t)
            y = map_multiplier_to_y(m)
            if y < padding: y = padding
            elif y > height - padding: y = height - padding
            points.append((x, y))
        
        tip_x, tip_y = 0, 0
        if len(points) > 1:
            # Area fill under graph
            area_points = points + [(points[-1][0], height - padding), (points[0][0], height - padding)]
            area_layer = Image.new("RGBA", size, (0, 0, 0, 0))
            area_draw = ImageDraw.Draw(area_layer)
            area_draw.polygon(area_points, fill=(0, 255, 136, 40))
            img = Image.alpha_composite(img.convert("RGBA"), area_layer).convert("RGB")
            draw = ImageDraw.Draw(img)
            
            # Graph glow effect
            glow_layer = Image.new("RGBA", size, (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_layer)
            for glow_width, alpha in [(8, 40), (5, 60), (3, 80)]:
                glow_draw.line(points, fill=(0, 255, 136, alpha), width=glow_width)
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(4))
            img = Image.alpha_composite(img.convert("RGBA"), glow_layer).convert("RGB")
            draw = ImageDraw.Draw(img)
            
            tip_x, tip_y = points[-1]
            
            # Graph tip glow
            tip_glow = Image.new("RGBA", size, (0, 0, 0, 0))
            tip_draw = ImageDraw.Draw(tip_glow)
            tip_draw.ellipse([tip_x-8, tip_y-8, tip_x+8, tip_y+8], fill=(0, 255, 136, 100))
            tip_glow = tip_glow.filter(ImageFilter.GaussianBlur(4))
            img = Image.alpha_composite(img.convert("RGBA"), tip_glow).convert("RGB")
            draw = ImageDraw.Draw(img)
            
            # Graph tip circle
            draw.ellipse([tip_x-4, tip_y-4, tip_x+4, tip_y+4], 
                       fill="#00ff88", outline="#ffffff", width=2)
            
            # Check for milestone triggers
            for milestone in milestone_multipliers:
                if (target_multiplier >= milestone and 
                    milestone not in triggered_milestones and
                    frame > 10):
                    triggered_milestones.add(milestone)
                    special_effects.add_effect(milestone, 'milestone_tip', tip_x, tip_y)
            
            # Check for integer milestones
            current_integer = int(target_multiplier)
            if (current_integer >= 1 and 
                current_integer > last_integer and
                frame > 10):
                last_integer = current_integer
                special_effects.add_integer_effect(current_integer)
        
        # Draw special effects
        special_effects.update()
        effects_layer = Image.new("RGBA", size, (0, 0, 0, 0))
        effects_draw = ImageDraw.Draw(effects_layer)
        special_effects.draw(effects_draw, tip_x, tip_y, target_multiplier)
        img = Image.alpha_composite(img.convert("RGBA"), effects_layer).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # Add sparks at graph tip
        if len(points) > 1:
            intensity = 1.0 + (real_elapsed_time / real_time_to_crash) * 2.0
            if random.random() < 0.4 or frame < 15:
                spark_system.add_sparks(tip_x, tip_y, random.randint(2, 6), intensity)
        
        # Update and draw sparks
        spark_system.update()
        if spark_system.sparks:
            spark_layer = Image.new("RGBA", size, (0, 0, 0, 0))
            spark_draw = ImageDraw.Draw(spark_layer)
            spark_system.draw(spark_draw)
            img = Image.alpha_composite(img.convert("RGBA"), spark_layer).convert("RGB")
            draw = ImageDraw.Draw(img)
        
        # Main multiplier display
        final_multiplier = min(target_multiplier, crash_target)
        multiplier_text = f"{final_multiplier:.2f}x"
        
        # Position above graph
        text_x = graph_center_x / 1.45
        text_y = padding - 40
        
        # Background for readability
        bg_padding = 10
        text_bbox = draw.textbbox((text_x, text_y), multiplier_text)
        bg_width = text_bbox[2] - text_bbox[0] + bg_padding * 2
        bg_height = text_bbox[3] - text_bbox[1] + bg_padding * 2
        bg_x = text_x - bg_width / 1.45
        bg_y = text_y - bg_padding
        
        # Semi-transparent background
        draw.rectangle([bg_x, bg_y, bg_x + bg_width, bg_y + bg_height], 
                      fill=(15, 20, 25, 180))
        
        # Text with shadow
        shadow_offset = 2
        draw.text((text_x + shadow_offset, text_y + shadow_offset), 
                 multiplier_text, fill=(0, 0, 0, 120), font_size=48)
        
        # Main text
        draw.text((text_x, text_y), 
                 multiplier_text, fill="#fffff0", font_size=48)
        
        images.append(img)
        
        # Crash detection and final frames
        if target_multiplier >= crash_target:
            # Add extra frames after crash
            for _ in range(20):
                spark_system.update()
                special_effects.update()
                final_img = img.copy()
                
                # Final effects
                effects_layer = Image.new("RGBA", size, (0, 0, 0, 0))
                effects_draw = ImageDraw.Draw(effects_layer)
                special_effects.draw(effects_draw, tip_x, tip_y, crash_target)
                final_img = Image.alpha_composite(final_img.convert("RGBA"), effects_layer).convert("RGB")
                
                # Final sparks
                if spark_system.sparks:
                    spark_layer = Image.new("RGBA", size, (0, 0, 0, 0))
                    spark_draw = ImageDraw.Draw(spark_layer)
                    spark_system.draw(spark_draw)
                    final_img = Image.alpha_composite(final_img.convert("RGBA"), spark_layer).convert("RGB")
                
                images.append(final_img)
            break

    # Print frame multiplier report
    print("\nMultipliers per frame:")
    multipliers = [report['multiplier'] for report in frame_report]
    print("multipliers = [")
    for i in range(0, len(multipliers), 10):
        chunk = multipliers[i:i+10]
        print("    " + ", ".join(f"{m:.2f}" for m in chunk) + ",")
    print("]")
    
    # Save animation
    images[0].save(output_file, save_all=True, append_images=images[1:],
                  duration=duration, loop=0, format="WEBP")

if __name__ == "__main__":
    generate_crash_animation()