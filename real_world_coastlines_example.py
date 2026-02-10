"""
REAL WORLD COASTLINES WITH CARTOPY

Uses actual geographic coastline data from Cartopy to create
a realistic ocean current flow field visualization over real continents.

Requirements:
    pip install cartopy pillow bokeh

This example shows:
1. Loading real coastline data from Natural Earth via Cartopy
2. Rendering coastlines to a PNG background image
3. Overlaying realistic ocean currents on the geographic map
4. Interactive zoom/pan with unified coordinate system
"""

from bokeh.plotting import output_file, save, figure
from bokeh.layouts import column, row
from bokeh.models import Div, Slider, Select, CheckboxGroup, Button
from bokeh.models import CustomJS
from flowfield_with_background import FlowFieldWithBackground
from PIL import Image, ImageDraw
import io
import base64
import math

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    CARTOPY_AVAILABLE = True
except ImportError:
    CARTOPY_AVAILABLE = False
    print("⚠️  Cartopy not installed!")
    print("   Install with: pip install cartopy")
    print("   Falling back to simple example...")

# ============================================
# CREATE REAL-WORLD COASTLINE BACKGROUND
# ============================================

def create_cartopy_background(lon_min=-100, lon_max=10, lat_min=20, lat_max=70, 
                               width=1000, height=700, dpi=100):
    """
    Create a background image with real-world coastlines using Cartopy.
    
    Parameters
    ----------
    lon_min, lon_max : float
        Longitude range (degrees)
    lat_min, lat_max : float
        Latitude range (degrees)
    width, height : int
        Image dimensions in pixels
    dpi : int
        Resolution for rendering
        
    Returns
    -------
    str
        Base64-encoded PNG image data URI
    """
    if not CARTOPY_AVAILABLE:
        raise ImportError("Cartopy is required for real-world coastlines")
    
    # Create figure with exact pixel dimensions
    fig_width = width / dpi
    fig_height = height / dpi
    
    fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
    ax = plt.axes([0, 0, 1, 1], projection=ccrs.PlateCarree())
    
    # Set map extent
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
    
    # Ocean background
    ax.add_feature(cfeature.OCEAN, facecolor='#0057b4', zorder=0)
    
    # Add land with natural earth data
    ax.add_feature(cfeature.LAND, facecolor='#dd9001', edgecolor='#997501', 
                   linewidth=1.5, zorder=1)
    
    # Add coastlines with higher resolution
    ax.coastlines(resolution='50m', color='#000000', linewidth=1, zorder=2)
    
    # Optional: Add rivers and lakes
    ax.add_feature(cfeature.RIVERS, edgecolor='#beddff', linewidth=0.5, zorder=1)
    ax.add_feature(cfeature.LAKES, facecolor='#beddff', edgecolor='#beddff', 
                   linewidth=0.5, zorder=1)
    
    # Optional: Add borders (subtle)
    ax.add_feature(cfeature.BORDERS, edgecolor='#3a3a3a', linewidth=0.5, 
                   linestyle=':', alpha=0.3, zorder=2)
    
    # Remove axes
    ax.set_frame_on(False)
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', 
                pad_inches=0, facecolor='#0a1929')
    plt.close(fig)
    
    # Convert to base64 data URI
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    data_uri = f"data:image/png;base64,{img_base64}"
    
    return data_uri

# ============================================
# GENERATE REALISTIC OCEAN CURRENTS
# ============================================

def generate_currents(lon_min=-100, lon_max=10, lat_min=20, lat_max=70,
                                width=1000, height=700):
    """

    Parameters
    ----------
    lon_min, lon_max : float
        Longitude range (degrees)
    lat_min, lat_max : float  
        Latitude range (degrees)
    width, height : int
        Canvas dimensions in pixels
        
    Returns
    -------
    tuple
        (x_coords, y_coords, dx_values, dy_values, magnitudes)
    """
    grid_size = 50  # Grid resolution
    
    x_coords = []
    y_coords = []
    dx_values = []
    dy_values = []
    magnitudes = []
    
    # Convert lat/lon to pixel coordinates
    def latlon_to_pixel(lon, lat):
        x = (lon - lon_min) / (lon_max - lon_min) * width
        y = (lat_max - lat) / (lat_max - lat_min) * height  # Flip Y
        return x, y
    
    # Convert pixel to lat/lon
    def pixel_to_latlon(x, y):
        lon = lon_min + (x / width) * (lon_max - lon_min)
        lat = lat_max - (y / height) * (lat_max - lat_min)  # Flip Y
        return lon, lat
    
    for i in range(grid_size + 1):
        for j in range(grid_size + 1):
            # Pixel coordinates
            x = (i / grid_size) * width
            y = (j / grid_size) * height
            
            # Geographic coordinates
            lon, lat = pixel_to_latlon(x, y)
            
            # Initialize flow components
            dx_total = 0
            dy_total = 0
            
            # ===================================
            # BACKGROUND CIRCULATION
            # Subtle basin-wide patterns
            # ===================================
            bg_dx = 0.15 * math.cos(lat * math.pi / 180 * 2)
            bg_dy = 0.1 * math.sin(lon * math.pi / 180 * 2)
            dx_total += bg_dx
            dy_total += bg_dy
            
            # Calculate magnitude
            magnitude = math.sqrt(dx_total**2 + dy_total**2)
            
            x_coords.append(x)
            y_coords.append(y)
            dx_values.append(dx_total)
            dy_values.append(dy_total)
            magnitudes.append(magnitude)
    
    return x_coords, y_coords, dx_values, dy_values, magnitudes

# ============================================
# CREATE CONTROLS
# ============================================

def create_controls(flow, width):
    """Create Bokeh widget controls for the flow field"""
    
    # Particle controls
    particle_slider = Slider(
        start=1000, end=15000, value=flow.particle_count, step=1000,
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
        options=['yellow', 'red', 'purple', 'blue', 'lightblue', 'lime', 'white', 'pink'],
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
    
    controls_panel = column(
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
    
    return column(controls_panel, sizing_mode="fixed")

# ============================================
# MAIN EXAMPLE
# ============================================

def main():
    """Create the real-world coastline example"""
    
    if not CARTOPY_AVAILABLE:
        print("\n" + "="*70)
        print("ERROR: Cartopy is required for this example")
        print("="*70)
        print("\nInstall with:")
        print("  pip install cartopy")
        print("\nNote: Cartopy installation can be complex. If you have issues:")
        print("  - Try: conda install -c conda-forge cartopy")
        print("  - Or see: https://scitools.org.uk/cartopy/docs/latest/installing.html")
        print("="*70)
        return
    
    output_file("real_world_coastlines.html")
    
    # ============================================
    # CONFIGURATION
    # ============================================
    
    # North Atlantic region
    lon_min, lon_max = -100, 10
    lat_min, lat_max = 20, 70
    width, height = 1000, 700
    
    print("\n" + "="*70)
    print("🌍 Generating Real-World Coastline Map...")
    print("="*70)
    print(f"Region: {lat_min}°N to {lat_max}°N, {lon_min}°E to {lon_max}°E")
    print(f"Resolution: {width}x{height} pixels")
    print("Loading Natural Earth coastline data via Cartopy...")
    
    # Create background with real coastlines
    bg_image = create_cartopy_background(
        lon_min=lon_min, lon_max=lon_max,
        lat_min=lat_min, lat_max=lat_max,
        width=width, height=height,
        dpi=100
    )
    
    print("✓ Coastline background created")
    

    x, y, dx, dy, mag = generate_currents(
        lon_min=lon_min, lon_max=lon_max,
        lat_min=lat_min, lat_max=lat_max,
        width=width, height=height
    )
    
    print("✓ Ocean currents generated")
    
    # Create flow field
    print("Creating interactive flow field...")
    
    flow = FlowFieldWithBackground(
        width=width,
        height=height,
        x_coords=x,
        y_coords=y,
        dx_values=dx,
        dy_values=dy,
        magnitudes=mag,
        
        # Particle settings
        particle_count=2000,
        particle_size=1,
        particle_life=120,
        flow_strength=4.0,
        particle_trail=True,
        
        # Background
        background_image=bg_image,
        background_alpha=1.0,
        background_color='transparent',
        
        # Visuals
        color_scheme='white',
        show_vectors=False,
        animate=True
    )
    
    print("✓ Flow field created")
    
    # Create controls
    controls = create_controls(flow, width)

    # Layout
    layout = column(
        flow,
        controls,
        sizing_mode="fixed"
    )
    
    save(layout)

if __name__ == "__main__":
    main()
