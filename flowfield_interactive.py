from bokeh.core.properties import Int, Float, String, Bool, List
from bokeh.models import LayoutDOM

class FlowFieldInteractive(LayoutDOM):
    """
    Interactive Flow Field Visualization
    
    This component renders a flow field with particle animation.
    Use Bokeh widgets (Slider, Select, ColorPicker, etc.) with CustomJS
    callbacks to control the visualization parameters.
    
    You provide the flow data:
    - x_coords: X positions of grid points
    - y_coords: Y positions of grid points  
    - dx_values: X component of flow vector at each point
    - dy_values: Y component of flow vector at each point
    - magnitudes: Magnitude of flow at each point
    
    All visualization parameters can be controlled via Bokeh widgets!
    """
    
    __implementation__ = "flowfield_interactive.ts"
    
    # Flow field data - YOU provide this
    x_coords = List(Float, help="X coordinates of flow field grid points")
    y_coords = List(Float, help="Y coordinates of flow field grid points")
    dx_values = List(Float, help="X component of velocity at each grid point")
    dy_values = List(Float, help="Y component of velocity at each grid point")
    magnitudes = List(Float, help="Magnitude of velocity at each grid point")
    
    # Particle settings (control via Bokeh widgets)
    particle_count = Int(3000, help="Number of particles")
    particle_size = Float(2, help="Particle size in pixels")
    particle_life = Int(100, help="Particle lifetime in frames")
    flow_strength = Float(2.5, help="Flow velocity multiplier")
    
    # Animation settings
    animate = Bool(True, help="Enable animation")
    animation_speed = Float(1.0, help="Animation speed multiplier (higher = faster)")
    
    # Visual settings
    show_vectors = Bool(False, help="Show flow vectors")
    background_color = String("#0a0a0a", help="Background color")
    color_scheme = String("viridis", help="Color scheme: viridis, turbo, plasma, inferno, cividis, ocean, rainbow")
