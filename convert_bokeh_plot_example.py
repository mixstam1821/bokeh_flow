"""
EXAMPLE: Converting Your Existing Bokeh Plots to Backgrounds

This shows how to take your existing Bokeh visualization code
and convert it to work as a background for the flow field.
"""

from bokeh.plotting import output_file, save, figure
from bokeh.layouts import column
from bokeh.models import Div, Slider, Select, CheckboxGroup
from bokeh.models import CustomJS
from flowfield_with_background import FlowFieldWithBackground
from background_utils import create_coastline_background
import math

# ============================================
# YOUR EXISTING BOKEH PLOT CODE
# (This would be your coastline/bathymetry viz)
# ============================================

def create_your_bokeh_plot():
    """
    This represents YOUR existing Bokeh plotting code.
    Could be coastlines, bathymetry, network graphs, etc.
    """
    width, height = 800, 600
    
    p = figure(
        width=width,
        height=height,
        x_range=(0, width),
        y_range=(0, height),
        title="Your Geographic Data",
        tools="pan,wheel_zoom,reset",
        toolbar_location="above"
    )
    
    # Your plotting code here...
    p.background_fill_color = "#1a2332"
    
    # Example: Some coastlines
    coast1_x = [100, 200, 250, 200, 120, 100]
    coast1_y = [150, 130, 180, 230, 200, 150]
    p.patch(coast1_x, coast1_y, fill_color='#3d5a3d', 
            fill_alpha=0.8, line_color='#2d4a2d', line_width=2)
    
    coast2_x = [450, 550, 600, 580, 480, 450]
    coast2_y = [300, 280, 350, 420, 400, 300]
    p.patch(coast2_x, coast2_y, fill_color='#3d5a3d', 
            fill_alpha=0.8, line_color='#2d4a2d', line_width=2]
    
    # Bathymetry contours
    for depth in [50, 100, 150, 200]:
        p.circle(400, 300, size=depth*3, 
                fill_alpha=0, line_alpha=0.1,
                line_color='#4a7c8c', line_width=1.5,
                line_dash='dashed')
    
    return p, width, height

# ============================================
# CONVERT TO BACKGROUND (Two Methods)
# ============================================

# METHOD 1: Manual recreation with PIL (Always works!)
def method1_manual():
    """
    Manually recreate your coastlines as PIL image.
    This always works - no extra dependencies needed.
    """
    width, height = 800, 600
    
    # Define the same shapes
    coast1 = ([100, 200, 250, 200, 120], [150, 130, 180, 230, 200])
    coast2 = ([450, 550, 600, 580, 480], [300, 280, 350, 420, 400])
    
    bg_image = create_coastline_background(
        width=width,
        height=height,
        coastlines=[coast1, coast2],
        bg_color='#1a2332',
        land_color='#3d5a3d'
    )
    
    return bg_image, width, height


# METHOD 2: Export Bokeh plot (Requires pillow + selenium)
def method2_export_bokeh():
    """
    Export your Bokeh plot directly to an image.
    Requires: pip install pillow selenium
    """
    from background_utils import prepare_background
    
    p, width, height = create_your_bokeh_plot()
    
    try:
        bg_image = prepare_background(p)
        print("✅ Successfully exported Bokeh plot to background!")
        return bg_image, width, height
    
    except ImportError as e:
        print(f"⚠️  Bokeh export requires additional packages:")
        print(f"   pip install pillow selenium geckodriver")
        print(f"   Falling back to PIL method...")
        return method1_manual()
    
    except Exception as e:
        print(f"⚠️  Export failed: {e}")
        print(f"   Falling back to PIL method...")
        return method1_manual()


# ============================================
# GENERATE FLOW DATA
# ============================================

def generate_flow_around_obstacles(width, height):
    """Generate flow that goes around the coastlines"""
    grid_size = 35
    
    x_coords = []
    y_coords = []
    dx_values = []
    dy_values = []
    magnitudes = []
    
    # Obstacle centers (matching coastline locations)
    obstacles = [
        (160, 180, 80),   # (x, y, radius)
        (520, 350, 100),
    ]
    
    for i in range(grid_size + 1):
        for j in range(grid_size + 1):
            x = (i / grid_size) * width
            y = (j / grid_size) * height
            
            # Base flow (left to right)
            dx_base = 1.0
            dy_base = 0.1 * math.sin(y / height * math.pi * 2)
            
            # Deflection around obstacles
            dx_deflect = 0
            dy_deflect = 0
            
            for obs_x, obs_y, obs_r in obstacles:
                dx_obs = x - obs_x
                dy_obs = y - obs_y
                dist = math.sqrt(dx_obs**2 + dy_obs**2)
                
                if dist < obs_r * 2:  # Influence zone
                    strength = max(0, 1 - dist / (obs_r * 2))
                    # Push flow around obstacle
                    if dist > 0:
                        dx_deflect += (dx_obs / dist) * strength * 0.5
                        dy_deflect += (dy_obs / dist) * strength * 0.5
            
            dx = dx_base + dx_deflect
            dy = dy_base + dy_deflect
            magnitude = math.sqrt(dx**2 + dy**2)
            
            x_coords.append(x)
            y_coords.append(y)
            dx_values.append(dx)
            dy_values.append(dy)
            magnitudes.append(magnitude)
    
    return x_coords, y_coords, dx_values, dy_values, magnitudes


# ============================================
# CREATE EXAMPLE
# ============================================

output_file("convert_bokeh_plot_example.html")

# Try Method 2 first (export), fall back to Method 1 (manual)
bg_image, width, height = method2_export_bokeh()

# Generate flow data
x, y, dx, dy, mag = generate_flow_around_obstacles(width, height)

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
    particle_count=4000,
    particle_size=2.5,
    particle_life=100,
    flow_strength=3.0,
    particle_trail=True,
    
    # Background
    background_image=bg_image,
    background_alpha=1.0,
    background_color='transparent',
    
    # Visuals
    color_scheme='turbo',
    show_vectors=False,
    animate=True
)

# Controls
strength_slider = Slider(start=0.5, end=8, value=3.0, step=0.5,
                        title="Flow Strength", width=350)
strength_slider.js_on_change('value', CustomJS(
    args=dict(f=flow), code="f.flow_strength = cb_obj.value;"))

particle_slider = Slider(start=1000, end=8000, value=4000, step=500,
                        title="Particle Count", width=350)
particle_slider.js_on_change('value', CustomJS(
    args=dict(f=flow), code="f.particle_count = cb_obj.value;"))

bg_alpha_slider = Slider(start=0, end=1, value=1.0, step=0.1,
                        title="Background Opacity", width=350)
bg_alpha_slider.js_on_change('value', CustomJS(
    args=dict(f=flow), code="f.background_alpha = cb_obj.value;"))

color_select = Select(title="Color Scheme", value='turbo',
                     options=['viridis', 'turbo', 'plasma', 'ocean', 'rainbow'],
                     width=350)
color_select.js_on_change('value', CustomJS(
    args=dict(f=flow), code="f.color_scheme = cb_obj.value;"))

vectors_check = CheckboxGroup(labels=["Show Flow Vectors"], active=[], width=350)
vectors_check.js_on_change('active', CustomJS(
    args=dict(f=flow), code="f.show_vectors = cb_obj.active.includes(0);"))

# Header
header = Div(text="""
<div style="font-family: system-ui; padding: 30px; 
     background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
     color: white; border-radius: 10px; margin-bottom: 30px;">
    <h1 style="margin: 0 0 10px 0; font-size: 32px; font-weight: 700;">
        🔄 Converting Bokeh Plots to Flow Backgrounds
    </h1>
    <p style="margin: 0; font-size: 16px; opacity: 0.95;">
        Two methods to convert your existing Bokeh visualizations
    </p>
</div>

<div style="font-family: system-ui; background: #e7f3ff; padding: 20px; 
     border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #2196F3;">
    <h3 style="margin: 0 0 12px 0; color: #1976D2;">📋 Two Conversion Methods</h3>
    
    <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0;">
        <h4 style="margin: 0 0 8px 0; color: #2196F3;">Method 1: Manual Recreation (Always Works)</h4>
        <p style="margin: 0; color: #555; line-height: 1.7;">
            Extract your coastline/feature coordinates and recreate with PIL.
            <strong>Pros:</strong> No dependencies, always works, fast.
            <strong>Cons:</strong> Need to extract/recreate shapes manually.
        </p>
        <pre style="background: #263238; color: #aed581; padding: 10px; border-radius: 4px; 
             font-size: 12px; margin: 10px 0;">
bg = create_coastline_background(
    coastlines=[(x_coords, y_coords), ...],
    bg_color='#1a2332',
    land_color='#3d5a3d'
)
        </pre>
    </div>
    
    <div style="background: white; padding: 15px; border-radius: 5px; margin: 10px 0;">
        <h4 style="margin: 0 0 8px 0; color: #2196F3;">Method 2: Export Bokeh Plot (Convenient)</h4>
        <p style="margin: 0; color: #555; line-height: 1.7;">
            Export your Bokeh plot directly to base64 image.
            <strong>Pros:</strong> Use existing plot code unchanged.
            <strong>Cons:</strong> Requires pillow + selenium packages.
        </p>
        <pre style="background: #263238; color: #aed581; padding: 10px; border-radius: 4px; 
             font-size: 12px; margin: 10px 0;">
<span style="color: #7fdbca;"># pip install pillow selenium</span>
bg = prepare_background(your_bokeh_plot)
        </pre>
    </div>
</div>
""", width=width)

info = Div(text="""
<div style="font-family: system-ui; background: #f8f9fa; padding: 20px; 
     border-radius: 8px; margin: 20px 0; border-left: 4px solid #6c757d;">
    <h3 style="margin: 0 0 10px 0; color: #495057;">💡 What to Try</h3>
    <ul style="line-height: 2; color: #555; margin: 5px 0;">
        <li><strong>Zoom in</strong> - notice background and flow zoom together!</li>
        <li><strong>Adjust Background Opacity</strong> - make it semi-transparent</li>
        <li><strong>Enable Flow Vectors</strong> - see how flow bends around islands</li>
        <li><strong>Hover</strong> - get flow data at any point on the map</li>
    </ul>
</div>
""", width=width)

# Layout
layout = column(
    header,
    flow,
    Div(text="""
    <div style="font-family: system-ui; padding: 12px; 
         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
         color: white; border-radius: 8px 8px 0 0; margin-top: 20px;">
        <h3 style="margin: 0; font-size: 15px; font-weight: 600;">⚙️ Controls</h3>
    </div>
    """, width=width),
    Div(
        children=[
            Div(text="", width=30),
            column(strength_slider, particle_slider, width=350),
            Div(text="", width=40),
            column(bg_alpha_slider, color_select, vectors_check, width=350),
            Div(text="", width=30),
        ],
        styles={'background': '#f8f9fa', 'padding': '20px', 
                'display': 'flex', 'border-radius': '0 0 8px 8px'}
    ),
    info,
    sizing_mode="fixed"
)

save(layout)

print("\n" + "="*70)
print("✅ Created: convert_bokeh_plot_example.html")
print("="*70)
print("\nThis example shows how to convert your existing Bokeh plots")
print("to backgrounds for the flow field visualization.")
print("\nTwo methods demonstrated:")
print("  1. Manual recreation with PIL (always works)")
print("  2. Direct export with prepare_background() (needs pillow+selenium)")
print("\nThe flow field now renders ON TOP of your geographic data!")
print("="*70)
