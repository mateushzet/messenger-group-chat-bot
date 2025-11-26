from PIL import Image, ImageDraw
import os
import math
import random

class PlinkoAnimator:
    def __init__(self, width=400, height=500):
        self.width = width
        self.height = height
        self.levels = 14
        self.peg_radius = 3
        self.ball_radius = 5
        
        self.bg_color = (0, 0, 0, 0)
        self.peg_color = (255, 255, 255, 255)
        self.peg_glow = (255, 255, 255, 255)
        self.ball_color = (255, 215, 0, 255)
        self.ball_glow = (255, 235, 100, 255)
        self.ball_highlight = (255, 255, 200, 255)
        
        self.star_colors = [
            (255, 255, 255, 255),
            (255, 255, 200, 255),
            (255, 235, 150, 255),
            (255, 215, 100, 255),
        ]
        
        self.firework_colors = [
            (255, 50, 50, 255),
            (50, 255, 50, 255),
            (50, 50, 255, 255),
            (255, 255, 50, 255),
            (255, 50, 255, 255),
            (50, 255, 255, 255),
            (255, 150, 50, 255),
        ]
        
        self.gravity = 0.8
        self.bounce_factor = 0.6
        self.friction = 0.96
        
        self.calculate_geometry()
        self.pyramid_top = self.find_pyramid_top()
        self.landing_positions = self.calculate_landing_positions()
    
    def calculate_geometry(self):
        self.peg_positions = []
        
        top_margin = 60
        bottom_margin = 80
        play_area_height = self.height - top_margin - bottom_margin
        
        level_spacing = play_area_height / (self.levels + 1)
        
        for level in range(self.levels):
            level_y = top_margin + (level + 1) * level_spacing
            pegs_in_level = level + 1
            level_pegs = []
            
            base_spacing = 28
            total_width = (pegs_in_level - 1) * base_spacing
            start_x = (self.width - total_width) / 2
            
            for peg in range(pegs_in_level):
                x = start_x + peg * base_spacing
                level_pegs.append((x, level_y))
            
            self.peg_positions.append(level_pegs)
    
    def calculate_landing_positions(self):
        landing_positions = []
        
        if not self.peg_positions or len(self.peg_positions) < self.levels:
            return landing_positions
        
        last_level_pegs = self.peg_positions[-1]
        last_level_y = last_level_pegs[0][1] if last_level_pegs else self.height - 80
        
        for i in range(len(last_level_pegs) + 1):
            if i == 0:
                x = last_level_pegs[0][0] - 14
            elif i == len(last_level_pegs):
                x = last_level_pegs[-1][0] + 14
            else:
                x = (last_level_pegs[i-1][0] + last_level_pegs[i][0]) / 2
            
            y = last_level_y + 20
            landing_positions.append((x, y))
        
        return landing_positions
    
    def find_pyramid_top(self):
        if not self.peg_positions or len(self.peg_positions) == 0:
            return self.width / 2, 30
        
        if len(self.peg_positions[0]) > 0:
            top_peg = self.peg_positions[0][0]
            return top_peg[0], top_peg[1] - 30
        else:
            return self.width / 2, 30
    
    def find_nearest_landing_position(self, x):
        if not self.landing_positions:
            last_level_y = self.peg_positions[-1][0][1] if self.peg_positions else self.height - 60
            return x, last_level_y + 20
        
        nearest_pos = None
        min_distance = float('inf')
        
        for pos_x, pos_y in self.landing_positions:
            distance = abs(x - pos_x)
            if distance < min_distance:
                min_distance = distance
                nearest_pos = (pos_x, pos_y)
        
        return nearest_pos
    
    def get_bucket_from_position(self, x):
        if not self.landing_positions:
            return 7
        
        nearest_pos = None
        min_distance = float('inf')
        bucket_index = -1
        
        for i, (pos_x, pos_y) in enumerate(self.landing_positions):
            distance = abs(x - pos_x)
            if distance < min_distance:
                min_distance = distance
                nearest_pos = (pos_x, pos_y)
                bucket_index = i
        
        return bucket_index
    
    def simulate_with_target_bucket(self, target_bucket, max_attempts=1000):
        for attempt in range(max_attempts):
            randomness = random.uniform(0.2, 0.4)
            
            positions, velocities = self.simulate_physics(randomness)
            
            if positions:
                final_x = positions[-1][0]
                actual_bucket = self.get_bucket_from_position(final_x)
                
                if actual_bucket == target_bucket:
                    return positions, velocities, randomness
        
        randomness = random.uniform(0.2, 0.4)
        positions, velocities = self.simulate_physics(randomness)
        return positions, velocities, randomness
    
    def draw_firework_particle(self, draw, x, y, size, color, life):
        alpha = int(255 * (1 - life))
        if alpha < 10:
            return
            
        color_with_alpha = (color[0], color[1], color[2], alpha)
        draw.ellipse([x-size, y-size, x+size, y+size], fill=color_with_alpha)
        
        if life < 0.3:
            highlight_size = size * 0.6
            highlight_alpha = int(200 * (1 - life))
            draw.ellipse([x-highlight_size, y-highlight_size, x+highlight_size, y+highlight_size], 
                        fill=(255, 255, 255, highlight_alpha))
    
    def draw_firework_explosion(self, draw, center_x, center_y, frame, max_frames):
        particles_count = 40
        explosion_radius = 30
        
        for i in range(particles_count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(0.5, 2.0)
            distance = explosion_radius * speed * (frame / max_frames)
            
            particle_x = center_x + math.cos(angle) * distance
            particle_y = center_y + math.sin(angle) * distance
            
            size = random.uniform(0.8, 1.8) * (1 - frame / max_frames)
            color = random.choice(self.firework_colors)
            life = frame / max_frames
            
            self.draw_firework_particle(draw, particle_x, particle_y, size, color, life)
    
    def draw_star(self, draw, x, y, size, color, rotation=0):
        points = []
        for i in range(10):
            angle = math.pi / 5 * i + rotation
            radius = size if i % 2 == 0 else size * 0.4
            px = x + math.cos(angle) * radius
            py = y + math.sin(angle) * radius
            points.append((px, py))
        
        if len(points) >= 3:
            draw.polygon(points, fill=color)
    
    def draw_sparkle(self, draw, x, y, size, color):
        draw.line([x-size, y, x+size, y], fill=color, width=2)
        draw.line([x, y-size, x, y+size], fill=color, width=2)
        draw.line([x-size*0.7, y-size*0.7, x+size*0.7, y+size*0.7], fill=color, width=1)
        draw.line([x+size*0.7, y-size*0.7, x-size*0.7, y+size*0.7], fill=color, width=1)
    
    def draw_stars_trail(self, draw, trajectory_points, current_frame, total_frames):
        if len(trajectory_points) < 3:
            return
        
        trail_length = min(40, int(total_frames * 0.3))
        start_index = max(0, current_frame - trail_length)
        recent_points = trajectory_points[start_index:current_frame + 1]
        
        if len(recent_points) < 2:
            return
        
        step = max(2, len(recent_points) // 15)
        
        for i in range(0, len(recent_points) - 1, step):
            if i >= len(recent_points):
                break
                
            x, y = recent_points[i]
            position_in_trail = i / len(recent_points)
            
            if position_in_trail < 0.3:
                alpha = int(255 * (position_in_trail / 0.3))
            else:
                alpha = 255
                
            if alpha < 10:
                continue
                
            if random.random() < 0.8:
                size = random.uniform(1.3, 2.5)
                base_color = random.choice(self.star_colors)
                color = (base_color[0], base_color[1], base_color[2], alpha)
                offset_x = random.uniform(-2, 2)
                offset_y = random.uniform(-2, 2)
                
                if random.random() < 0.7:
                    rotation = random.uniform(0, math.pi)
                    self.draw_star(draw, x + offset_x, y + offset_y, size, color, rotation)
                else:
                    self.draw_sparkle(draw, x + offset_x, y + offset_y, size * 1.3, color)
    
    def draw_peg(self, draw, x, y, frame_counter=0):
        glow_radius = self.peg_radius + 1
        draw.ellipse([x-glow_radius, y-glow_radius, x+glow_radius, y+glow_radius], 
                    fill=(255, 255, 255, 255))
        
        draw.ellipse([x-self.peg_radius, y-self.peg_radius, 
                     x+self.peg_radius, y+self.peg_radius], 
                    fill=self.peg_color)
        
        highlight_radius = self.peg_radius * 0.6
        hl_x = x - self.peg_radius * 0.2
        hl_y = y - self.peg_radius * 0.2
        draw.ellipse([hl_x-highlight_radius, hl_y-highlight_radius, 
                     hl_x+highlight_radius, hl_y+highlight_radius], 
                    fill=(200, 220, 255, 255))
    
    def draw_ball(self, draw, x, y, velocity_x=0, velocity_y=0, frame_counter=0):
        speed = math.sqrt(velocity_x**2 + velocity_y**2)
        
        for i in range(2):
            glow_radius = self.ball_radius + 3 - i * 1
            gold_r = 255
            gold_g = 215 + i * 10
            gold_b = max(0, 50 - i * 8)
            draw.ellipse([x-glow_radius, y-glow_radius, 
                         x+glow_radius, y+glow_radius], 
                        fill=(gold_r, gold_g, gold_b, 255))
        
        draw.ellipse([x-self.ball_radius, y-self.ball_radius, 
                     x+self.ball_radius, y+self.ball_radius], 
                    fill=self.ball_color)
        
        move_factor = 0.3
        hl_offset_x = -velocity_x * move_factor
        hl_offset_y = -velocity_y * move_factor
        
        hl_x = x - self.ball_radius * 0.2 + hl_offset_x
        hl_y = y - self.ball_radius * 0.2 + hl_offset_y
        hl_r = self.ball_radius * 0.5
        
        draw.ellipse([hl_x-hl_r, hl_y-hl_r, hl_x+hl_r, hl_y+hl_r], 
                    fill=self.ball_highlight)
        
        small_hl_r = hl_r * 0.6
        small_hl_x = hl_x + hl_r * 0.3
        small_hl_y = hl_y + hl_r * 0.3
        draw.ellipse([small_hl_x-small_hl_r, small_hl_y-small_hl_r, 
                     small_hl_x+small_hl_r, small_hl_y+small_hl_r], 
                    fill=(255, 255, 255, 255))
    
    def draw_frame(self, ball_pos=None, ball_velocity=(0, 0), frame_counter=0, 
                  show_trajectory=False, trajectory_points=None, total_frames=0,
                  show_fireworks=False, firework_frame=0, max_firework_frames=0):
        img = Image.new('RGBA', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        if show_trajectory and trajectory_points and len(trajectory_points) > 2:
            self.draw_stars_trail(draw, trajectory_points, len(trajectory_points) - 1, total_frames)
        
        for level_pegs in self.peg_positions:
            for x, y in level_pegs:
                self.draw_peg(draw, x, y, frame_counter)
        
        if ball_pos:
            x, y = ball_pos
            vx, vy = ball_velocity
            self.draw_ball(draw, x, y, vx, vy, frame_counter)
            
            if show_fireworks and ball_pos and max_firework_frames > 0:
                self.draw_firework_explosion(draw, x, y, firework_frame, max_firework_frames)
        
        return img
    
    def simulate_physics(self, randomness=0.3):
        positions = []
        velocities = []
        
        start_x, start_y = self.pyramid_top
        x, y = start_x, start_y
        vx, vy = 0, 1.0
        
        frame = 0
        max_frames = 350
        
        positions.append((x, y))
        velocities.append((vx, vy))
        
        last_level_y = self.peg_positions[-1][0][1] if self.peg_positions else self.height - 100
        landing_boundary = last_level_y + 25
        
        passed_last_level = False
        final_x_position = None
        
        while frame < max_frames:
            frame += 1
            
            if not passed_last_level and y > last_level_y + 10:
                passed_last_level = True
                final_x_position = x
                vx = 0
            
            if passed_last_level:
                vy += self.gravity
                vy *= self.friction
                new_x = final_x_position
                new_y = y + vy
            else:
                vy += self.gravity
                vx *= self.friction
                vy *= self.friction
                new_x = x + vx
                new_y = y + vy
                
                collision_occurred = False
                current_level = min(int((y - 60) / ((self.height - 100) / (self.levels + 1))), self.levels - 1)
                current_level = max(0, current_level)
                
                for level_offset in [-1, 0, 1]:
                    check_level = current_level + level_offset
                    if 0 <= check_level < len(self.peg_positions):
                        for peg_x, peg_y in self.peg_positions[check_level]:
                            dx = new_x - peg_x
                            dy = new_y - peg_y
                            distance_sq = dx*dx + dy*dy
                            min_distance = self.ball_radius + self.peg_radius
                            
                            if distance_sq < min_distance * min_distance:
                                collision_occurred = True
                                distance = math.sqrt(distance_sq)
                                nx = dx / distance
                                ny = dy / distance
                                dot_product = vx * nx + vy * ny
                                vx = vx - 2 * dot_product * nx
                                vy = vy - 2 * dot_product * ny
                                vx = vx * self.bounce_factor + random.uniform(-randomness, randomness)
                                vy = vy * self.bounce_factor + random.uniform(-randomness, randomness)
                                overlap = min_distance - distance
                                new_x += nx * overlap * 1.1
                                new_y += ny * overlap * 1.1
                                break
                        if collision_occurred:
                            break
                
                if new_x < self.ball_radius:
                    new_x = self.ball_radius
                    vx = abs(vx) * self.bounce_factor
                elif new_x > self.width - self.ball_radius:
                    new_x = self.width - self.ball_radius
                    vx = -abs(vx) * self.bounce_factor
            
            if new_y > landing_boundary:
                new_y = landing_boundary
                vy = 0
                
                if final_x_position is not None:
                    target_x, target_y = self.find_nearest_landing_position(final_x_position)
                else:
                    target_x, target_y = self.find_nearest_landing_position(new_x)
                
                if abs(new_x - target_x) > 1:
                    new_x = target_x
                
                x, y = new_x, new_y
                positions.append((x, y))
                velocities.append((0, 0))
                break
            
            x, y = new_x, new_y
            positions.append((x, y))
            velocities.append((vx, vy))
            
            if frame > 300 and abs(vy) < 0.1:
                if final_x_position is not None:
                    target_x, target_y = self.find_nearest_landing_position(final_x_position)
                else:
                    target_x, target_y = self.find_nearest_landing_position(x)
                
                steps = 8
                for i in range(steps):
                    progress = (i + 1) / steps
                    current_x = x + (target_x - x) * progress
                    current_y = y + (target_y - y) * progress
                    positions.append((current_x, current_y))
                    velocities.append((0, 0))
                break
        
        return positions, velocities
    
    def create_animation_for_bucket(self, bucket, output_path, show_trajectory=True):
        positions, velocities, randomness = self.simulate_with_target_bucket(bucket)
        
        if not positions:
            return False
        
        total_frames = len(positions)
        
        frames = []
        
        for frame_idx, (pos, vel) in enumerate(zip(positions, velocities)):
            frame = self.draw_frame(
                ball_pos=pos,
                ball_velocity=vel,
                frame_counter=frame_idx,
                show_trajectory=show_trajectory,
                trajectory_points=positions[:frame_idx+1],
                total_frames=total_frames
            )
            frames.append(frame)
        
        final_pos = positions[-1]
        firework_frames = 30
        
        for i in range(firework_frames):
            pulse = math.sin(i * 0.2) * 0.5
            
            frame = self.draw_frame(
                ball_pos=(final_pos[0], final_pos[1] + pulse),
                ball_velocity=(0, 0),
                frame_counter=total_frames + i,
                total_frames=total_frames,
                show_fireworks=True,
                firework_frame=i,
                max_firework_frames=firework_frames
            )
            
            frames.append(frame)
        
        try:
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=50,
                loop=0,
                format="WEBP",
                quality=85,
                optimize=True,
                method=5
            )
            
            return True
            
        except Exception:
            return False

def generate_all_animations():
    bucket_distribution = {
        0: 1,
        1: 2,
        2: 11,
        3: 44,
        4: 122,
        5: 244,
        6: 367,
        7: 419,
        8: 367,
        9: 244,
        10: 122,
        11: 44,
        12: 11,
        13: 2,
        14: 1
    }
    
    total_animations = sum(bucket_distribution.values())
    
    output_dir = "plinko_animations"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    animator = PlinkoAnimator()
    successful_animations = 0
    
    for bucket, count in bucket_distribution.items():
        for i in range(count):
            output_path = os.path.join(output_dir, f"plinko_bucket_{bucket}_{i+1:03d}.webp")
            
            if animator.create_animation_for_bucket(bucket, output_path, show_trajectory=True):
                successful_animations += 1
    
    return successful_animations

def create_single_animation(bucket=7, output_path="test_plinko.webp"):
    animator = PlinkoAnimator()
    return animator.create_animation_for_bucket(bucket, output_path)

if __name__ == "__main__":
    print("1. Generate all animations")
    print("2. Test - single animation")
    
    choice = input("Select (1 or 2): ").strip()
    
    if choice == "1":
        generate_all_animations()
    elif choice == "2":
        bucket = int(input("Bucket number (0-14): "))
        output_path = f"plinko_test_bucket_{bucket}.webp"
        create_single_animation(bucket, output_path)