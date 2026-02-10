"""
EXAMPLE 1: Basic Usage with Bokeh Widgets

This example shows how to create different flow patterns and control them
using Bokeh widgets (Sliders, Select, ColorPicker) with CustomJS callbacks.
"""

from bokeh.plotting import output_file, save
from bokeh.layouts import column, row
from bokeh.models import Div, Slider, Select, ColorPicker, CheckboxGroup, Button
from bokeh.models import CustomJS
from flowfield_interactive import FlowFieldInteractive
import math

# ============================================
# HELPER FUNCTION: Generate Flow Patterns
# ============================================

def generate_flow_pattern(pattern_type, width=800, height=600, grid_size=40):
    """
    Generate different flow patterns.
    
    Args:
        pattern_type: 'spiral', 'vortex', 'sink', 'source', 'wave', 'double_gyre'
        width: Canvas width in pixels
        height: Canvas height in pixels
        grid_size: Number of grid divisions
    
    Returns:
        x_coords, y_coords, dx, dy, magnitudes (all lists)
    """
    x_coords = []
    y_coords = []
    dx_values = []
    dy_values = []
    magnitudes = []
    
    center_x = width / 2
    center_y = height / 2
    
    for i in range(grid_size + 1):
        for j in range(grid_size + 1):
            # Grid position in pixels
            x = (i / grid_size) * width
            y = (j / grid_size) * height
            
            # Relative to center
            dx_c = x - center_x
            dy_c = y - center_y
            dist = math.sqrt(dx_c**2 + dy_c**2)
            
            # Calculate flow based on pattern type
            if pattern_type == 'spiral':
                # Spiraling outward
                if dist > 0:
                    angle = math.atan2(dy_c, dx_c)
                    tangent_x = -math.sin(angle)
                    tangent_y = math.cos(angle)
                    radial_x = math.cos(angle)
                    radial_y = math.sin(angle)
                    strength = 1.0 - math.exp(-dist / 100)
                    dx = tangent_x * strength * 0.7 + radial_x * strength * 0.3
                    dy = tangent_y * strength * 0.7 + radial_y * strength * 0.3
                else:
                    dx, dy = 0, 0
                    
            elif pattern_type == 'vortex':
                # Pure rotation
                if dist > 0:
                    dx = -dy_c / dist
                    dy = dx_c / dist
                else:
                    dx, dy = 0, 0
                    
            elif pattern_type == 'sink':
                # Inward flow
                if dist > 0:
                    strength = 1 - math.exp(-dist / 200)
                    dx = -dx_c / dist * strength
                    dy = -dy_c / dist * strength
                else:
                    dx, dy = 0, 0
                    
            elif pattern_type == 'source':
                # Outward flow
                if dist > 0:
                    strength = 1 - math.exp(-dist / 200)
                    dx = dx_c / dist * strength
                    dy = dy_c / dist * strength
                else:
                    dx, dy = 0, 0
                    
            elif pattern_type == 'wave':
                # Wavy horizontal flow
                dx = 0.8
                dy = 0.3 * math.sin(x / width * math.pi * 4)
                
            elif pattern_type == 'double_gyre':
                # Two counter-rotating gyres
                # Normalized coordinates
                nx = x / width
                ny = y / height
                dx = -math.sin(nx * math.pi) * math.cos(ny * math.pi)
                dy = math.cos(nx * math.pi) * math.sin(ny * math.pi)
                
            else:
                dx, dy = 0, 0
            
            magnitude = math.sqrt(dx**2 + dy**2)
            
            x_coords.append(x)
            y_coords.append(y)
            dx_values.append(dx)
            dy_values.append(dy)
            magnitudes.append(magnitude)
    
    return x_coords, y_coords, dx_values, dy_values, magnitudes

# ============================================
# CREATE FLOW VISUALIZATION WITH CONTROLS
# ============================================

def create_flow_with_controls(pattern_type, title, bg_color, color_scheme, width=700, height=500):
    """Create a flow field visualization with Bokeh widget controls"""
    
    # Generate flow data
    x, y, dx, dy, mag = generate_flow_pattern(pattern_type, width=width, height=height)
    
    # Create flow field visualization
    flow = FlowFieldInteractive(
        width=width,
        height=height,
        x_coords=x,
        y_coords=y,
        dx_values=dx,
        dy_values=dy,
        magnitudes=mag,
        
        # Initial settings
        particle_count=3000,
        particle_size=2,
        flow_strength=2.5,
        particle_life=100,
        animation_speed=1.0,
        
        # Visual
        background_color=bg_color,
        color_scheme=color_scheme,
        show_vectors=False,
        animate=True
    )
    
    # ============================================
    # CREATE BOKEH WIDGETS
    # ============================================
    
    # Particle count slider
    particle_slider = Slider(
        start=500, end=8000, value=3000, step=500,
        title="Particle Count",
        width=300
    )
    particle_slider.js_on_change('value', CustomJS(
        args=dict(flow=flow),
        code="flow.particle_count = cb_obj.value;"
    ))
    
    # Particle size slider
    size_slider = Slider(
        start=1, end=8, value=2, step=0.5,
        title="Particle Size",
        width=300
    )
    size_slider.js_on_change('value', CustomJS(
        args=dict(flow=flow),
        code="flow.particle_size = cb_obj.value;"
    ))
    
    # Flow strength slider
    strength_slider = Slider(
        start=0.5, end=10, value=2.5, step=0.5,
        title="Flow Strength",
        width=300
    )
    strength_slider.js_on_change('value', CustomJS(
        args=dict(flow=flow),
        code="flow.flow_strength = cb_obj.value;"
    ))
    
    # Animation speed slider
    speed_slider = Slider(
        start=0.1, end=3, value=1.0, step=0.1,
        title="Animation Speed",
        width=300
    )
    speed_slider.js_on_change('value', CustomJS(
        args=dict(flow=flow),
        code="flow.animation_speed = cb_obj.value;"
    ))
    
    # Particle lifetime slider
    life_slider = Slider(
        start=30, end=200, value=100, step=10,
        title="Particle Lifetime",
        width=300
    )
    life_slider.js_on_change('value', CustomJS(
        args=dict(flow=flow),
        code="flow.particle_life = cb_obj.value;"
    ))
    
    # Color scheme selector
    color_select = Select(
        title="Color Scheme",
        value=color_scheme,
        options=['viridis', 'turbo', 'plasma', 'inferno', 'cividis', 'ocean', 'rainbow'],
        width=300
    )
    color_select.js_on_change('value', CustomJS(
        args=dict(flow=flow),
        code="flow.color_scheme = cb_obj.value;"
    ))
    
    # Background color picker
    bg_picker = ColorPicker(
        title="Background Color",
        color=bg_color,
        width=300
    )
    bg_picker.js_on_change('color', CustomJS(
        args=dict(flow=flow),
        code="flow.background_color = cb_obj.color;"
    ))
    
    # Show vectors checkbox
    vectors_checkbox = CheckboxGroup(
        labels=["Show Flow Vectors"],
        active=[],
        width=300
    )
    vectors_checkbox.js_on_change('active', CustomJS(
        args=dict(flow=flow),
        code="flow.show_vectors = cb_obj.active.includes(0);"
    ))
    
    # Play/Pause button
    play_button = Button(label="⏸ Pause", button_type="success", width=150)
    play_button.js_on_click(CustomJS(
        args=dict(flow=flow, btn=play_button),
        code="""
        flow.animate = !flow.animate;
        btn.label = flow.animate ? '⏸ Pause' : '▶ Play';
        btn.button_type = flow.animate ? 'success' : 'warning';
        """
    ))
    
    # ============================================
    # LAYOUT CONTROLS IN A NICE PANEL
    # ============================================
    
    controls_title = Div(text=f"""
    <div style="font-family: system-ui; padding: 15px; 
         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
         color: white; border-radius: 8px 8px 0 0; margin-top: 20px;">
        <h3 style="margin: 0; font-size: 18px; font-weight: 600;">
            ⚙️ Controls - {title}
        </h3>
    </div>
    """, width=width)
    
    controls_bg = Div(text="", width=width, height=10, 
                      styles={'background': '#f8f9fa', 'border-radius': '0 0 8px 8px'})
    
    # Arrange controls in columns
    controls_col1 = column(particle_slider, size_slider, strength_slider, 
                          sizing_mode="fixed", width=300)
    controls_col2 = column(speed_slider, life_slider, play_button,
                          sizing_mode="fixed", width=300)
    controls_col3 = column(color_select, bg_picker, vectors_checkbox,
                          sizing_mode="fixed", width=300)
    
    controls_row = row(
        Div(text="", width=10),  # Spacer
        controls_col1,
        Div(text="", width=20),  # Spacer
        controls_col2,
        Div(text="", width=20),  # Spacer
        controls_col3,
        sizing_mode="fixed",
        styles={'background': '#f8f9fa', 'padding': '20px', 
                'border-radius': '0 0 8px 8px'}
    )
    
    # Title div
    title_div = Div(text=f"""
    <h2 style="font-family: system-ui; color: #333; margin: 30px 0 10px 0; 
               font-size: 24px; font-weight: 600;">
        {title}
    </h2>
    """, width=width)
    
    return column(title_div, flow, controls_title, controls_row, sizing_mode="fixed")

# ============================================
# CREATE EXAMPLES
# ============================================

output_file("example1_basic_patterns.html")

# Create multiple flow fields with different patterns
patterns = [
    ('spiral', 'Spiraling Outward', '#0a0a0a', 'turbo'),
    ('vortex', 'Pure Vortex', '#1a0033', 'plasma'),
    ('double_gyre', 'Double Gyre', '#001a1a', 'ocean')
]

visualizations = []

for pattern_type, title, bg_color, color_scheme in patterns:
    viz = create_flow_with_controls(pattern_type, title, bg_color, color_scheme)
    visualizations.append(viz)



# Layout
layout = column(*visualizations, sizing_mode="fixed")

save(layout)
