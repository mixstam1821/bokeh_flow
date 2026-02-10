from bokeh.core.properties import Int, Float, String, Bool, List
from bokeh.models import LayoutDOM

class FlowFieldWithBackground(LayoutDOM):
    """
    Flow Field Visualization with Background Image Overlay
    
    This component supports displaying a background image (e.g., from a Bokeh plot)
    with the flow field particles and vectors rendered on top.
    
    Features:
    - Zoom and pan with mouse wheel and drag
    - Hover tooltip showing flow data
    - Background image support (base64 or URL)
    - Customizable vector display
    - Particle trail effects
    
    Flow data (required):
    - x_coords: X positions of grid points
    - y_coords: Y positions of grid points  
    - dx_values: X component of flow vector at each point
    - dy_values: Y component of flow vector at each point
    - magnitudes: Magnitude of flow at each point
    
    Background image:
    - background_image: Base64 data URI or image URL
    - background_alpha: Opacity of background (0-1)
    
    All parameters can be controlled via Bokeh widgets with CustomJS.
    """
    
    __implementation__ = "flowfield_with_background.ts"
    
    # Flow field data
    x_coords = List(Float, help="X coordinates of flow field grid points")
    y_coords = List(Float, help="Y coordinates of flow field grid points")
    dx_values = List(Float, help="X component of velocity at each grid point")
    dy_values = List(Float, help="Y component of velocity at each grid point")
    magnitudes = List(Float, help="Magnitude of velocity at each grid point")
    
    # Particle settings
    particle_count = Int(3000, help="Number of particles")
    particle_size = Float(2, help="Particle size in pixels")
    particle_life = Int(100, help="Particle lifetime in frames")
    particle_trail = Bool(True, help="Enable particle trail effect")
    flow_strength = Float(2.5, help="Flow velocity multiplier")
    
    # Animation settings
    animate = Bool(True, help="Enable animation")
    animation_speed = Float(1.0, help="Animation speed multiplier")
    
    # Vector settings
    show_vectors = Bool(False, help="Show flow vectors")
    vector_color = String("#ffffff", help="Vector arrow color")
    vector_width = Float(1.0, help="Vector line width")
    vector_alpha = Float(0.3, help="Vector transparency (0-1)")
    vector_scale = Float(20.0, help="Vector length multiplier")
    
    # Background settings
    background_color = String("transparent", help="Background color")
    background_image = String("", help="Background image (base64 data URI or URL)")
    background_alpha = Float(1.0, help="Background image opacity (0-1)")
    
    # Visual settings
    color_scheme = String("viridis", help="Color scheme: viridis, turbo, plasma, inferno, cividis, ocean, rainbow")
