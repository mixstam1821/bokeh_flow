"""
TRUE OVERLAY EXAMPLE: Flow Field Over Background Images

This example demonstrates TRUE overlay by using background images.
Three approaches shown:
1. Manual coastlines (PIL-generated)
2. Bokeh plot converted to background
3. Custom image file

All support zoom, pan, and hover tooltips!
"""

from bokeh.plotting import output_file, save, figure
from bokeh.layouts import column, row
from bokeh.models import Div, Slider, Select, CheckboxGroup, Button
from bokeh.models import CustomJS
from flowfield_with_background import FlowFieldWithBackground
from background_utils import create_coastline_background, prepare_background
import math

# ============================================
# GENERATE FLOW DATA
# ============================================

def generate_ocean_currents(width=900, height=700):
    """Generate realistic ocean current flow field"""
    grid_size = 45
    
    x_coords = []
    y_coords = []
    dx_values = []
    dy_values = []
    magnitudes = []
    
    for i in range(grid_size + 1):
        for j in range(grid_size + 1):
            x = (i / grid_size) * width
            y = (j / grid_size) * height
            
            # Main gyre (large circular current)
            center_x, center_y = width * 0.6, height * 0.5
            dx_c = x - center_x
            dy_c = y - center_y
            dist = math.sqrt(dx_c**2 + dy_c**2)
            
            if dist > 0:
                # Cyclonic flow
                strength = math.exp(-dist / 180)
                gyre_dx = -dy_c / dist * strength * 1.2
                gyre_dy = dx_c / dist * strength * 1.2
            else:
                gyre_dx, gyre_dy = 0, 0
            
            # Coastal current (along western edge)
            coastal_dist = abs(x - 80)
            if coastal_dist < 100:
                coastal_strength = (1 - coastal_dist / 100) * 0.8
                coastal_dx = 0
                coastal_dy = coastal_strength  # Northward flow
            else:
                coastal_dx, coastal_dy = 0, 0
            
            # Small eddies
            eddy1_x, eddy1_y = width * 0.25, height * 0.7
            dx_e1 = x - eddy1_x
            dy_e1 = y - eddy1_y
            dist_e1 = math.sqrt(dx_e1**2 + dy_e1**2)
            
            if dist_e1 > 0 and dist_e1 < 90:
                eddy_strength = (1 - dist_e1 / 90) * 0.5
                eddy1_dx = dy_e1 / dist_e1 * eddy_strength  # Counter-clockwise
                eddy1_dy = -dx_e1 / dist_e1 * eddy_strength
            else:
                eddy1_dx, eddy1_dy = 0, 0
            
            # Eastward background flow
            background_dx = 0.2
            background_dy = 0.05 * math.sin(y / height * math.pi * 2)
            
            # Combine all components
            dx = gyre_dx + coastal_dx + eddy1_dx + background_dx
            dy = gyre_dy + coastal_dy + eddy1_dy + background_dy
            
            magnitude = math.sqrt(dx**2 + dy**2)
            
            x_coords.append(x)
            y_coords.append(y)
            dx_values.append(dx)
            dy_values.append(dy)
            magnitudes.append(magnitude)
    
    return x_coords, y_coords, dx_values, dy_values, magnitudes

# ============================================
# APPROACH 1: PIL-Generated Coastlines
# ============================================

def example1_manual_coastlines():
    """Create flow over manually-defined coastlines"""
    width, height = 900, 700
    
    # Define island shapes
    island1 = (
        [150, 220, 280, 250, 180, 150],
        [120, 100, 140, 200, 210, 120]
    )
    
    island2 = (
        [550, 650, 720, 700, 620, 550, 520],
        [280, 250, 300, 400, 450, 420, 320]
    )
    
    island3 = (
        [300, 380, 450, 500, 480, 420, 350, 280],
        [480, 460, 480, 520, 580, 600, 580, 520]
    )
    
    # Create background image
    bg_image = create_coastline_background(
        width=width,
        height=height,
        coastlines=[island1, island2, island3],
        bg_color='#0a1929',  # Dark ocean blue
        land_color='#4a7c59'  # Green land
    )
    
    # Generate flow data
    x, y, dx, dy, mag = generate_ocean_currents(width, height)
    
    # Create flow field with background
    flow = FlowFieldWithBackground(
        width=width,
        height=height,
        x_coords=x,
        y_coords=y,
        dx_values=dx,
        dy_values=dy,
        magnitudes=mag,
        
        # Particle settings
        particle_count=1000,
        particle_size=1.5,
        particle_life=120,
        flow_strength=3.5,
        particle_trail=True,
        
        # Background
        background_image=bg_image,
        background_alpha=1.0,
        background_color='transparent',
        
        # Visuals
        color_scheme='yellow',
        show_vectors=False,
        animate=True
    )
    
    return flow, width, height

# ============================================
# APPROACH 2: Bokeh Plot as Background
# ============================================

def example2_bokeh_background():
    """Create Bokeh plot and use it as background"""
    width, height = 900, 700
    
    # Create Bokeh plot with geographic features
    p = figure(
        width=width,
        height=height,
        x_range=(0, width),
        y_range=(0, height),
        toolbar_location=None
    )
    
    p.background_fill_color = "#0a1929"
    p.border_fill_color = "#0a1929"
    p.outline_line_color = None
    p.axis.visible = False
    p.grid.visible = False
    
    # Add islands
    island1_x = [150, 220, 280, 250, 180, 150]
    island1_y = [120, 100, 140, 200, 210, 120]
    p.patch(island1_x, island1_y, fill_color='#4a7c59', 
            fill_alpha=0.9, line_color='#2d5016', line_width=2)
    
    island2_x = [550, 650, 720, 700, 620, 550, 520]
    island2_y = [280, 250, 300, 400, 450, 420, 320]
    p.patch(island2_x, island2_y, fill_color='#4a7c59', 
            fill_alpha=0.9, line_color='#2d5016', line_width=2)
    
    island3_x = [300, 380, 450, 500, 480, 420, 350, 280]
    island3_y = [480, 460, 480, 520, 580, 600, 580, 520]
    p.patch(island3_x, island3_y, fill_color='#4a7c59', 
            fill_alpha=0.9, line_color='#2d5016', line_width=2)
    
    # Add depth contours
    for depth_radius in [100, 200, 300, 400]:
        p.circle(
            width * 0.6, height * 0.5,
            size=depth_radius * 2,
            fill_alpha=0,
            line_alpha=0.08,
            line_color='#5a9e6f',
            line_width=1,
            line_dash='dashed'
        )
    
    # Convert to background image
    try:
        bg_image = prepare_background(p)
    except:
        # Fallback if export_png not available
        print("⚠️  Bokeh export requires: pip install pillow selenium")
        print("   Using PIL-generated background instead")
        bg_image = create_coastline_background(
            width=width, height=height,
            coastlines=[
                (island1_x, island1_y),
                (island2_x, island2_y),
                (island3_x, island3_y)
            ]
        )
    
    # Generate flow data
    x, y, dx, dy, mag = generate_ocean_currents(width, height)
    
    # Create flow field
    flow = FlowFieldWithBackground(
        width=width,
        height=height,
        x_coords=x,
        y_coords=y,
        dx_values=dx,
        dy_values=dy,
        magnitudes=mag,
        particle_count=2000,
        particle_size=1.5,
        flow_strength=3.5,
        background_image=bg_image,
        background_alpha=1.0,
        color_scheme='yellow',
        show_vectors=False
    )
    
    return flow, width, height

# ============================================
# CREATE CONTROLS
# ============================================

def create_controls(flow, width):
    """Create Bokeh widget controls for the flow field"""
    
    # Particle controls
    particle_slider = Slider(
        start=1000, end=12000, value=flow.particle_count, step=1000,
        title="Particle Count", width=260
    )
    particle_slider.js_on_change('value', CustomJS(
        args=dict(f=flow), code="f.particle_count = cb_obj.value;"))
    
    size_slider = Slider(
        start=1, end=6, value=flow.particle_size, step=0.5,
        title="Particle Size", width=260
    )
    size_slider.js_on_change('value', CustomJS(
        args=dict(f=flow), code="f.particle_size = cb_obj.value;"))
    
    # Flow controls
    strength_slider = Slider(
        start=0.5, end=10, value=flow.flow_strength, step=0.5,
        title="Flow Strength", width=260
    )
    strength_slider.js_on_change('value', CustomJS(
        args=dict(f=flow), code="f.flow_strength = cb_obj.value;"))
    
    speed_slider = Slider(
        start=0.1, end=3, value=flow.animation_speed, step=0.1,
        title="Animation Speed", width=260
    )
    speed_slider.js_on_change('value', CustomJS(
        args=dict(f=flow), code="f.animation_speed = cb_obj.value;"))
    
    # Visual controls
    color_select = Select(
        title="Color Scheme", value=flow.color_scheme,
        options=['viridis', 'turbo', 'plasma', 'inferno', 'cividis', 'ocean', 'rainbow'],
        width=260
    )
    color_select.js_on_change('value', CustomJS(
        args=dict(f=flow), code="f.color_scheme = cb_obj.value;"))
    
    bg_alpha_slider = Slider(
        start=0, end=1, value=flow.background_alpha, step=0.1,
        title="Background Opacity", width=260
    )
    bg_alpha_slider.js_on_change('value', CustomJS(
        args=dict(f=flow), code="f.background_alpha = cb_obj.value;"))
    
    # Options
    options_checks = CheckboxGroup(
        labels=["Show Flow Vectors", "Particle Trails"],
        active=[1] if flow.particle_trail else [],
        width=260
    )
    options_checks.js_on_change('active', CustomJS(
        args=dict(f=flow),
        code="""
        f.show_vectors = cb_obj.active.includes(0);
        f.particle_trail = cb_obj.active.includes(1);
        """
    ))
    
    # Play/Pause
    play_button = Button(label="⏸ Pause", button_type="success", width=260)
    play_button.js_on_click(CustomJS(args=dict(f=flow, b=play_button), code="""
        f.animate = !f.animate;
        b.label = f.animate ? '⏸ Pause' : '▶ Play';
        b.button_type = f.animate ? 'success' : 'warning';
    """))
    
    # Layout
    controls_header = Div(text="""
    <div style="font-family: system-ui; padding: 12px; 
         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
         color: white; border-radius: 8px 8px 0 0; margin-top: 20px;">
        <h3 style="margin: 0; font-size: 16px; font-weight: 600;">⚙️ Flow Field Controls</h3>
    </div>
    """, width=width)
    
    controls_panel = row(
        Div(text="", width=30),
        column(particle_slider, size_slider, width=260),
        Div(text="", width=30),
        column(strength_slider, speed_slider, width=260),
        Div(text="", width=30),
        column(color_select, bg_alpha_slider, options_checks, play_button, width=260),
        Div(text="", width=30),
        sizing_mode="fixed",
        styles={'background': '#f8f9fa', 'padding': '20px', 
                'border-radius': '0 0 8px 8px'}
    )
    
    return column(controls_header, controls_panel, sizing_mode="fixed")

# ============================================
# MAIN EXAMPLE
# ============================================

output_file("true_overlay_example.html")

# Use Approach 1 (works without additional dependencies)
flow, width, height = example1_manual_coastlines()

# Create controls
controls = create_controls(flow, width)

# Layout
layout = column(
    flow,
    controls,
    sizing_mode="fixed"
)

save(layout)
