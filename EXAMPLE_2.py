

from real_world_coastlines_example import *


def example_globe():
    """Globe"""
    return {
        'lon_min': -180, 'lon_max': 180,
        'lat_min': -90, 'lat_max': 90,
        'width': 1200, 'height': 500,
        'title': 'Globe',
        'description': 'Complex circulation with strait connections'
    }


def generate_regional_currents(config, width, height):
    """
    Generate currents based on region type.
    This is a simplified version - you can enhance it with region-specific patterns.
    """
    lon_min = config['lon_min']
    lon_max = config['lon_max']
    lat_min = config['lat_min']
    lat_max = config['lat_max']
    
    # Use the Atlantic current generator as a base
    # In practice, you'd customize this for each region
    return generate_currents(
        lon_min=lon_min, lon_max=lon_max,
        lat_min=lat_min, lat_max=lat_max,
        width=width, height=height
    )

def create_visualization(region_config):
    """Create visualization for a specific region"""
    
    if not CARTOPY_AVAILABLE:
        print("\n⚠️  ERROR: Cartopy is required")
        print("Install with: conda install -c conda-forge cartopy")
        return
    
    config = region_config()
    
    print("\n" + "="*70)
    print(f"🌍 Creating: {config['title']}")
    print("="*70)
    print(f"Region: {config['lat_min']}°N to {config['lat_max']}°N")
    print(f"        {config['lon_min']}°E to {config['lon_max']}°E")
    print(f"Features: {config['description']}")
    print("="*70)
    
    # Create background
    print("Loading coastline data...")
    bg_image = create_cartopy_background(
        lon_min=config['lon_min'],
        lon_max=config['lon_max'],
        lat_min=config['lat_min'],
        lat_max=config['lat_max'],
        width=config['width'],
        height=config['height'],
        dpi=100
    )
    print("✓ Coastlines loaded")
    
    # Generate currents
    print("Generating ocean currents...")
    x, y, dx, dy, mag = generate_regional_currents(
        config, config['width'], config['height']
    )
    print("✓ Currents generated")
    
    # Create flow field
    flow = FlowFieldWithBackground(
        width=config['width'],
        height=config['height'],
        x_coords=x, y_coords=y,
        dx_values=dx, dy_values=dy,
        magnitudes=mag,
        particle_count=2000,
        particle_size=1.5,
        particle_life=120,
        flow_strength=5.0,
        particle_trail=True,
        background_image=bg_image,
        background_alpha=1.0,
        color_scheme='lime',
        show_vectors=False,
        animate=True
    )
    # Create controls
    controls = create_controls(flow, config['width'])
    
    # Layout
    layout = row(flow, controls, sizing_mode="fixed")
    
    # Generate filename from title
    filename = config['title'].lower()
    filename = ''.join(c if c.isalnum() else '_' for c in filename)
    filename = f"{filename}.html"
    
    output_file(filename)
    save(layout)
    
    print(f"\n✅ Created: {filename}")
    print("="*70)
    
    return filename


result = create_visualization(example_globe)
