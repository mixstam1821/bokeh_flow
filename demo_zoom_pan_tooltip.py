"""
DEMO: Zoom, Pan, and Hover Tooltip Features

This example demonstrates the new interactive features:
- Mouse wheel to zoom in/out
- Click and drag to pan
- Hover to see flow data at any point
"""

from bokeh.plotting import output_file, save
from bokeh.layouts import column, row
from bokeh.models import Div, Slider, Select, CheckboxGroup, Button
from bokeh.models import CustomJS
from flowfield_interactive import FlowFieldInteractive
import math

# ============================================
# GENERATE INTERESTING FLOW PATTERN
# ============================================

def create_complex_flow(width=900, height=700):
    """Create a complex flow with multiple features"""
    grid_size = 50
    
    x_coords = []
    y_coords = []
    dx_values = []
    dy_values = []
    magnitudes = []
    
    for i in range(grid_size + 1):
        for j in range(grid_size + 1):
            x = (i / grid_size) * width
            y = (j / grid_size) * height
            
            # Create multiple vortices
            vortex_centers = [
                (width * 0.3, height * 0.3, 150, 1.0),   # (x, y, radius, strength)
                (width * 0.7, height * 0.3, 120, -0.8),
                (width * 0.5, height * 0.7, 180, 0.6),
            ]
            
            dx_total = 0
            dy_total = 0
            
            for cx, cy, radius, strength in vortex_centers:
                dx_c = x - cx
                dy_c = y - cy
                dist = math.sqrt(dx_c**2 + dy_c**2)
                
                if dist > 0:
                    # Vortex flow
                    decay = math.exp(-dist / radius)
                    dx_total += -dy_c / dist * decay * strength
                    dy_total += dx_c / dist * decay * strength
            
            # Add a background flow
            dx_total += 0.3
            dy_total += 0.1 * math.sin(x / width * math.pi * 2)
            
            magnitude = math.sqrt(dx_total**2 + dy_total**2)
            
            x_coords.append(x)
            y_coords.append(y)
            dx_values.append(dx_total)
            dy_values.append(dy_total)
            magnitudes.append(magnitude)
    
    return x_coords, y_coords, dx_values, dy_values, magnitudes

# ============================================
# CREATE VISUALIZATION
# ============================================

output_file("demo_zoom_pan_tooltip.html")

width, height = 900, 700

# Generate flow data
x, y, dx, dy, mag = create_complex_flow(width, height)

# Create flow field
flow = FlowFieldInteractive(
    width=width,
    height=height,
    x_coords=x,
    y_coords=y,
    dx_values=dx,
    dy_values=dy,
    magnitudes=mag,
    particle_count=5000,
    particle_size=2.5,
    flow_strength=3.0,
    background_color='#0a0a0a',
    color_scheme='turbo',
    show_vectors=False,
    animate=True
)

# ============================================
# CREATE CONTROLS
# ============================================

particle_slider = Slider(start=1000, end=10000, value=5000, step=500,
                        title="Particle Count", width=280)
particle_slider.js_on_change('value', CustomJS(
    args=dict(flow=flow), code="flow.particle_count = cb_obj.value;"))

strength_slider = Slider(start=0.5, end=10, value=3.0, step=0.5,
                        title="Flow Strength", width=280)
strength_slider.js_on_change('value', CustomJS(
    args=dict(flow=flow), code="flow.flow_strength = cb_obj.value;"))

speed_slider = Slider(start=0.1, end=3, value=1.0, step=0.1,
                     title="Animation Speed", width=280)
speed_slider.js_on_change('value', CustomJS(
    args=dict(flow=flow), code="flow.animation_speed = cb_obj.value;"))

size_slider = Slider(start=1, end=8, value=2.5, step=0.5,
                    title="Particle Size", width=280)
size_slider.js_on_change('value', CustomJS(
    args=dict(flow=flow), code="flow.particle_size = cb_obj.value;"))

color_select = Select(title="Color Scheme", value='turbo',
                     options=['viridis', 'turbo', 'plasma', 'inferno', 
                             'cividis', 'ocean', 'rainbow'], width=280)
color_select.js_on_change('value', CustomJS(
    args=dict(flow=flow), code="flow.color_scheme = cb_obj.value;"))

vectors_check = CheckboxGroup(labels=["Show Flow Vectors"], active=[], width=280)
vectors_check.js_on_change('active', CustomJS(
    args=dict(flow=flow), code="flow.show_vectors = cb_obj.active.includes(0);"))

play_button = Button(label="⏸ Pause", button_type="success", width=280)
play_button.js_on_click(CustomJS(args=dict(flow=flow, btn=play_button), code="""
    flow.animate = !flow.animate;
    btn.label = flow.animate ? '⏸ Pause' : '▶ Play';
    btn.button_type = flow.animate ? 'success' : 'warning';
"""))

controls_panel = row(
    Div(text="", width=30),
    column(particle_slider, strength_slider, width=280),
    Div(text="", width=30),
    column(speed_slider, size_slider, width=280),
    Div(text="", width=30),
    column(color_select, vectors_check, play_button, width=280),
    Div(text="", width=30),
    sizing_mode="fixed",
    styles={'background': '#f8f9fa', 'padding': '20px', 
            'border-radius': '0 0 8px 8px'}
)

# Layout
layout = column(
    flow,
    controls_panel,
    sizing_mode="fixed"
)

save(layout)
