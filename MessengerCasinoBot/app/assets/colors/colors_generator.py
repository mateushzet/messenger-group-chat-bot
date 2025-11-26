from PIL import Image, ImageDraw
import random

def generate_wheel_animation(target, shift,color_shift = 0, output_file="fortune_spin_slow_smooth.webp", size=512, frames=100, duration=75, hold_frames=20):
    
    mini_shift = shift # -5 -3 -1
    radius_outer = size // 2 - 3
    ring_thickness = 10
    radius_inner = radius_outer - ring_thickness
    gap_angle = 0.7
    center = size // 2
    bg_color = "#1c1c27"

    color_map = {0: "#444", 1: "#d22", 2: "#3af", 3: "#fc3"}
    colorOrder = [3, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1,
                  0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2,
                  0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2]
    colorOrder2 = [0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 
                   0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 
                   0, 1, 0, 2, 3, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1]
    
    if color_shift != 0:
        colorOrder = colorOrder[color_shift:] + colorOrder[:color_shift]

    segments = len(colorOrder)
    angle_per_segment = 360 / segments

    target_segment = target
    target_angle = -(target_segment * angle_per_segment + angle_per_segment / 2) - mini_shift 

    total_rotations = 2
    total_angle = 360 * total_rotations + target_angle

    angles = []

    ease_in_ratio = 0.1
    for i in range(frames):
        t = i / (frames - 1)
        if t < ease_in_ratio:
            norm_t = t / ease_in_ratio
            angle = total_angle * (norm_t ** 2) * ease_in_ratio
        else:
            norm_t = (t - ease_in_ratio) / (1 - ease_in_ratio)
            angle = total_angle * (ease_in_ratio + (1 - (1 - norm_t) ** 3) * (1 - ease_in_ratio))
        angles.append(angle)

    angles.extend([angles[-1]] * hold_frames)

    images = []
    for angle_offset in angles:
        img = Image.new("RGB", (size, size), bg_color)
        draw = ImageDraw.Draw(img)

        for i, color_id in enumerate(colorOrder):
            start_angle_seg = angle_per_segment * i + angle_offset + gap_angle
            end_angle_seg = angle_per_segment * (i + 1) + angle_offset - gap_angle

            bbox_outer = [center - radius_outer, center - radius_outer,
                          center + radius_outer, center + radius_outer]
            bbox_inner = [center - radius_inner, center - radius_inner,
                          center + radius_inner, center + radius_inner]

            mask = Image.new("L", (size, size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.pieslice(bbox_outer, start=start_angle_seg, end=end_angle_seg, fill=255)
            mask_draw.pieslice(bbox_inner, start=start_angle_seg, end=end_angle_seg, fill=0)

            seg_img = Image.new("RGB", (size, size), color_map[color_id])
            img.paste(seg_img, (0, 0), mask)

        draw.ellipse([center - radius_inner + 2, center - radius_inner + 2,
                      center + radius_inner - 2, center + radius_inner - 2], fill=bg_color)
        if mini_shift == 1:
            mini_shift = 3
        
        current_index = int((360 - (angle_offset % 360) - mini_shift) / angle_per_segment) % len(colorOrder)
        arrow_color = color_map[colorOrder2[current_index]]
        arrow_size = 20
        arrow_height = arrow_size * 1.5
        arrow_width = 40
        arrow_height = 30
        arrow_top_y = size - 60

        arrow_width = 30
        arrow_height = 30
        arrow_top_y = size - 60

        arrow_points = [
            (center, arrow_top_y + arrow_height),
            (center - arrow_width / 2 +3, arrow_top_y + 2),
            (center + arrow_width / 2 - 3, arrow_top_y + 2),
        ]

        draw.polygon(arrow_points, fill=arrow_color)

        arrow_arc_height = 8
        arc_width_factor = 1.0

        draw.pieslice(
            [center - arrow_width * arc_width_factor / 2, arrow_top_y - arrow_arc_height,
            center + arrow_width * arc_width_factor / 2, arrow_top_y + arrow_arc_height],
            start=0, end=180, fill=bg_color
        )


        images.append(img)

    images[0].save(
        output_file,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        format="WEBP",
        optimize=True
    )

    return target_segment, color_map[colorOrder[target_segment]]

if __name__ == "__main__":

    shift_tab = [1, 3, 5]

    colorOrder = [0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 
                   0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 
                   0, 1, 0, 2, 3, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1]

    color_map = {
        0: "black",
        1: "red",
        2: "blue",
        3: "gold"
    }

    for i in range(54):
        for j in range(3):
            filename = f"colors_wheel_{color_map[colorOrder[i]]}_{i}_{j}.webp"
            print(f"{i} - {j} -> {filename}")
            generate_wheel_animation(
                target=i,
                shift=shift_tab[j],
                output_file=filename
            )