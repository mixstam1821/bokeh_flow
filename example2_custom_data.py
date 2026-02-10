"""
EXAMPLE 2: Using Your Own Flow Data with Bokeh Controls

This example demonstrates how to use your own flow field data
from various sources: calculations, APIs, or data files.
Controls are implemented with Bokeh widgets and CustomJS.
"""

from bokeh.plotting import output_file, save
from bokeh.layouts import column, row
from bokeh.models import Div, Slider, Select, CheckboxGroup, Button
from bokeh.models import CustomJS
from flowfield_interactive import FlowFieldInteractive
import math

# ============================================
# EXAMPLE 1: Mathematical Flow Field
# ============================================

def create_mathematical_flow():
    """Create a flow field from a mathematical function"""
    width = 800
    height = 600
    grid_size = 40
    
    x_coords = []
    y_coords = []
    dx_values = []
    dy_values = []
    magnitudes = []
    
    for i in range(grid_size + 1):
        for j in range(grid_size + 1):
            x = (i / grid_size) * width
            y = (j / grid_size) * height
            
            # YOUR CUSTOM FLOW FUNCTION HERE
            # Example: velocity field from a potential function
            # φ(x,y) = cos(2πx/width) * sin(2πy/height)
            # u = -∂φ/∂y,  v = ∂φ/∂x
            
            nx = x / width * 2 * math.pi
            ny = y / height * 2 * math.pi
            
            dx = -math.cos(nx) * math.cos(ny)  # -∂φ/∂y
            dy = -math.sin(nx) * math.sin(ny)  # ∂φ/∂x
            
            magnitude = math.sqrt(dx**2 + dy**2)
            
            x_coords.append(x)
            y_coords.append(y)
            dx_values.append(dx)
            dy_values.append(dy)
            magnitudes.append(magnitude)
    
    return x_coords, y_coords, dx_values, dy_values, magnitudes

# ============================================
# EXAMPLE 2: Simulated Wind Data
# ============================================

def create_wind_field():
    """Simulate a wind field (could come from API or model)"""
    width = 800
    height = 600
    grid_size = 30
    
    x_coords = []
    y_coords = []
    dx_values = []
    dy_values = []
    magnitudes = []
    
    for i in range(grid_size + 1):
        for j in range(grid_size + 1):
            x = (i / grid_size) * width
            y = (j / grid_size) * height
            
            # Latitude factor (0 = south, 1 = north)
            lat_factor = y / height
            
            # Base westerly wind (stronger in middle latitudes)
            base_u = 1.5 * math.sin(lat_factor * math.pi)
            base_v = 0.3 * math.cos(lat_factor * math.pi * 2)
            
            # Add some "turbulence"
            turb_u = 0.2 * math.sin(x / 50 + y / 30)
            turb_v = 0.2 * math.cos(x / 30 + y / 50)
            
            dx = base_u + turb_u
            dy = base_v + turb_v
            magnitude = math.sqrt(dx**2 + dy**2)
            
            x_coords.append(x)
            y_coords.append(y)
            dx_values.append(dx)
            dy_values.append(dy)
            magnitudes.append(magnitude)
    
    return x_coords, y_coords, dx_values, dy_values, magnitudes

# ============================================
# EXAMPLE 3: Ocean Current Simulation
# ============================================

def create_ocean_current_field():
    """Simulate an ocean current field"""
    width = 800
    height = 600
    grid_size = 35
    
    x_coords = []
    y_coords = []
    dx_values = []
    dy_values = []
    magnitudes = []
    
    center_x = width * 0.6
    center_y = height * 0.5
    
    for i in range(grid_size + 1):
        for j in range(grid_size + 1):
            x = (i / grid_size) * width
            y = (j / grid_size) * height
            
            # Main gyre
            dx_c = x - center_x
            dy_c = y - center_y
            dist = math.sqrt(dx_c**2 + dy_c**2)
            
            if dist > 0:
                strength = math.exp(-dist / 150)
                gyre_u = -dy_c / dist * strength
                gyre_v = dx_c / dist * strength
            else:
                gyre_u, gyre_v = 0, 0
            
            # Coastal current
            coastal_dist = abs(x - 50)
            if coastal_dist < 80:
                coastal_strength = (1 - coastal_dist / 80) * 0.8
                coastal_u = 0
                coastal_v = coastal_strength
            else:
                coastal_u, coastal_v = 0, 0
            
            # Small eddy
            eddy_x, eddy_y = width * 0.3, height * 0.7
            dx_e, dy_e = x - eddy_x, y - eddy_y
            dist_e = math.sqrt(dx_e**2 + dy_e**2)
            
            if dist_e > 0 and dist_e < 80:
                eddy_strength = (1 - dist_e / 80) * 0.4
                eddy_u = dy_e / dist_e * eddy_strength
                eddy_v = -dx_e / dist_e * eddy_strength
            else:
                eddy_u, eddy_v = 0, 0
            
            # Combine
            dx = gyre_u + coastal_u + eddy_u
            dy = gyre_v + coastal_v + eddy_v
            magnitude = math.sqrt(dx**2 + dy**2)
            
            x_coords.append(x)
            y_coords.append(y)
            dx_values.append(dx)
            dy_values.append(dy)
            magnitudes.append(magnitude)
    
    return x_coords, y_coords, dx_values, dy_values, magnitudes

# ============================================
# HELPER: CREATE COMPACT CONTROLS
# ============================================

def create_compact_controls(flow, title):
    """Create a compact control panel for a flow visualization"""
    
    # Sliders
    particle_slider = Slider(start=500, end=6000, value=flow.particle_count, 
                            step=500, title="Particles", width=220)
    particle_slider.js_on_change('value', CustomJS(
        args=dict(f=flow), code="f.particle_count = cb_obj.value;"))
    
    strength_slider = Slider(start=0.5, end=8, value=flow.flow_strength, 
                            step=0.5, title="Strength", width=220)
    strength_slider.js_on_change('value', CustomJS(
        args=dict(f=flow), code="f.flow_strength = cb_obj.value;"))
    
    speed_slider = Slider(start=0.1, end=2.5, value=flow.animation_speed, 
                         step=0.1, title="Speed", width=220)
    speed_slider.js_on_change('value', CustomJS(
        args=dict(f=flow), code="f.animation_speed = cb_obj.value;"))
    
    # Color scheme
    color_select = Select(title="Colors", value=flow.color_scheme,
                         options=['viridis', 'turbo', 'plasma', 'inferno', 
                                 'cividis', 'ocean', 'rainbow'], width=220)
    color_select.js_on_change('value', CustomJS(
        args=dict(f=flow), code="f.color_scheme = cb_obj.value;"))
    
    # Checkboxes
    options_checks = CheckboxGroup(labels=["Show Vectors"], active=[], width=220)
    options_checks.js_on_change('active', CustomJS(
        args=dict(f=flow), code="f.show_vectors = cb_obj.active.includes(0);"))
    
    # Play/pause
    play_btn = Button(label="⏸ Pause", button_type="success", width=220)
    play_btn.js_on_click(CustomJS(args=dict(f=flow, b=play_btn), code="""
        f.animate = !f.animate;
        b.label = f.animate ? '⏸ Pause' : '▶ Play';
        b.button_type = f.animate ? 'success' : 'warning';
    """))
    
    # Layout
    controls_header = Div(text=f"""
    <div style="font-family: system-ui; padding: 12px; 
         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
         color: white; border-radius: 8px 8px 0 0; margin-top: 15px;">
        <h4 style="margin: 0; font-size: 15px; font-weight: 600;">⚙️ {title} Controls</h4>
    </div>
    """, width=800)
    
    controls_panel = row(
        Div(text="", width=20),
        column(particle_slider, strength_slider, width=220),
        Div(text="", width=20),
        column(speed_slider, color_select, width=220),
        Div(text="", width=20),
        column(options_checks, play_btn, width=220),
        sizing_mode="fixed",
        styles={'background': '#f8f9fa', 'padding': '15px', 
                'border-radius': '0 0 8px 8px'}
    )
    
    return column(controls_header, controls_panel, sizing_mode="fixed")

# ============================================
# CREATE VISUALIZATIONS
# ============================================

output_file("example2_custom_data.html")


# Example 1: Mathematical
x1, y1, dx1, dy1, mag1 = create_mathematical_flow()
flow1 = FlowFieldInteractive(
    width=800, height=600,
    x_coords=x1, y_coords=y1,
    dx_values=dx1, dy_values=dy1, magnitudes=mag1,
    particle_count=4000, particle_size=2, flow_strength=3.0,
    background_color='#0a0a0a', color_scheme='viridis'
)

title1 = Div(text="""
<div style="font-family: system-ui; margin: 30px 0 15px 0; padding: 15px; 
     background: white; border-radius: 8px; border-left: 5px solid #667eea;">
    <h2 style="margin: 0 0 8px 0; color: #333; font-size: 22px; font-weight: 600;">
        1️⃣ Mathematical Flow Field
    </h2>
    <p style="margin: 0; color: #666; font-size: 14px; line-height: 1.6;">
        Created from: φ(x,y) = cos(2πx) × sin(2πy) → <strong>u = -∂φ/∂y</strong>, <strong>v = ∂φ/∂x</strong>
    </p>
</div>
""", width=800)

controls1 = create_compact_controls(flow1, "Mathematical Flow")

# Example 2: Wind
x2, y2, dx2, dy2, mag2 = create_wind_field()
flow2 = FlowFieldInteractive(
    width=800, height=600,
    x_coords=x2, y_coords=y2,
    dx_values=dx2, dy_values=dy2, magnitudes=mag2,
    particle_count=3500, particle_size=2.5, flow_strength=2.5,
    background_color='#001a33', color_scheme='turbo'
)

title2 = Div(text="""
<div style="font-family: system-ui; margin: 30px 0 15px 0; padding: 15px; 
     background: white; border-radius: 8px; border-left: 5px solid #667eea;">
    <h2 style="margin: 0 0 8px 0; color: #333; font-size: 22px; font-weight: 600;">
        2️⃣ Simulated Wind Field
    </h2>
    <p style="margin: 0; color: #666; font-size: 14px; line-height: 1.6;">
        Atmospheric pattern with westerly jet + turbulence (like OpenWeatherMap data)
    </p>
</div>
""", width=800)

controls2 = create_compact_controls(flow2, "Wind Field")

# Example 3: Ocean
x3, y3, dx3, dy3, mag3 = create_ocean_current_field()
flow3 = FlowFieldInteractive(
    width=800, height=600,
    x_coords=x3, y_coords=y3,
    dx_values=dx3, dy_values=dy3, magnitudes=mag3,
    particle_count=4500, particle_size=2, flow_strength=3.5,
    background_color='#001a1a', color_scheme='ocean'
)

title3 = Div(text="""
<div style="font-family: system-ui; margin: 30px 0 15px 0; padding: 15px; 
     background: white; border-radius: 8px; border-left: 5px solid #667eea;">
    <h2 style="margin: 0 0 8px 0; color: #333; font-size: 22px; font-weight: 600;">
        3️⃣ Ocean Current Simulation
    </h2>
    <p style="margin: 0; color: #666; font-size: 14px; line-height: 1.6;">
        Complex circulation: main gyre + coastal current + mesoscale eddy
    </p>
</div>
""", width=800)

controls3 = create_compact_controls(flow3, "Ocean Currents")


# Layout
layout = column(
    title1, flow1, controls1,
    title2, flow2, controls2,
    title3, flow3, controls3,
    sizing_mode="fixed"
)

save(layout)

