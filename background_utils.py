"""
Utilities for converting Bokeh plots to base64 images for use as backgrounds
"""

import base64
import io
from typing import Optional
from PIL import Image

def bokeh_to_base64(plot, width: int = None, height: int = None) -> str:
    """
    Convert a Bokeh plot to a base64 data URI.
    
    Args:
        plot: Bokeh Figure or Layout object
        width: Optional width override (uses plot width if not specified)
        height: Optional height override (uses plot height if not specified)
    
    Returns:
        Base64 data URI string (data:image/png;base64,...)
    
    Example:
        from bokeh.plotting import figure
        
        p = figure(width=800, height=600)
        p.circle([1, 2, 3], [4, 5, 6])
        
        img_data = bokeh_to_base64(p)
        
        flow = FlowFieldWithBackground(
            background_image=img_data,
            ...
        )
    """
    try:
        from bokeh.io import export_png
        from bokeh.models import Plot
        
        # Create temporary file-like object
        buffer = io.BytesIO()
        
        # Export to PNG
        export_png(plot, filename=buffer)
        
        # Resize if needed
        if width or height:
            buffer.seek(0)
            img = Image.open(buffer)
            if width and height:
                img = img.resize((width, height), Image.LANCZOS)
            elif width:
                aspect = img.height / img.width
                img = img.resize((width, int(width * aspect)), Image.LANCZOS)
            elif height:
                aspect = img.width / img.height
                img = img.resize((int(height * aspect), height), Image.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
        
        # Encode as base64
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
    
    except ImportError:
        raise ImportError(
            "bokeh_to_base64 requires additional dependencies. Install with:\n"
            "  pip install pillow selenium\n"
            "  or\n"
            "  conda install pillow selenium geckodriver firefox -c conda-forge"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to convert Bokeh plot to base64: {e}")


def image_file_to_base64(filepath: str) -> str:
    """
    Convert an image file to a base64 data URI.
    
    Args:
        filepath: Path to image file (PNG, JPEG, etc.)
    
    Returns:
        Base64 data URI string
    
    Example:
        img_data = image_file_to_base64('coastline_map.png')
        
        flow = FlowFieldWithBackground(
            background_image=img_data,
            ...
        )
    """
    with open(filepath, 'rb') as f:
        img_bytes = f.read()
    
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    # Detect image type from extension
    ext = filepath.lower().split('.')[-1]
    mime_types = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }
    mime_type = mime_types.get(ext, 'image/png')
    
    return f"data:{mime_type};base64,{img_base64}"


def numpy_array_to_base64(array, cmap: str = 'viridis') -> str:
    """
    Convert a numpy array to a base64 data URI using matplotlib.
    
    Args:
        array: 2D numpy array
        cmap: Matplotlib colormap name
    
    Returns:
        Base64 data URI string
    
    Example:
        import numpy as np
        
        # Bathymetry data
        depth = np.random.rand(100, 100)
        img_data = numpy_array_to_base64(depth, cmap='ocean')
        
        flow = FlowFieldWithBackground(
            background_image=img_data,
            ...
        )
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.imshow(array, cmap=cmap, origin='lower')
        ax.axis('off')
        plt.tight_layout(pad=0)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
    
    except ImportError:
        raise ImportError(
            "numpy_array_to_base64 requires matplotlib. Install with:\n"
            "  pip install matplotlib\n"
            "  or\n"
            "  conda install matplotlib"
        )


def create_coastline_background(width: int = 800, height: int = 600, 
                                coastlines: list = None,
                                bg_color: str = '#0a1929',
                                land_color: str = '#4a7c59') -> str:
    """
    Create a simple coastline background image.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        coastlines: List of (x_coords, y_coords) tuples for each coastline polygon
        bg_color: Ocean/background color
        land_color: Land/coastline color
    
    Returns:
        Base64 data URI string
    
    Example:
        # Define some simple islands
        island1 = ([100, 150, 200, 150], [100, 80, 100, 120])
        island2 = ([400, 500, 450], [300, 300, 400])
        
        img_data = create_coastline_background(
            coastlines=[island1, island2]
        )
        
        flow = FlowFieldWithBackground(
            background_image=img_data,
            ...
        )
    """
    try:
        from PIL import Image, ImageDraw
        
        # Create image
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Draw coastlines
        if coastlines:
            for x_coords, y_coords in coastlines:
                polygon = list(zip(x_coords, y_coords))
                draw.polygon(polygon, fill=land_color, outline='#2d5016')
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"
    
    except ImportError:
        raise ImportError(
            "create_coastline_background requires Pillow. Install with:\n"
            "  pip install pillow"
        )


# Convenience function combining everything
def prepare_background(source, **kwargs) -> str:
    """
    Prepare a background image from various sources.
    
    Args:
        source: Can be:
            - Bokeh plot/figure
            - File path (str ending in .png, .jpg, etc.)
            - Numpy array
            - List of coastline polygons
        **kwargs: Additional arguments passed to specific converters
    
    Returns:
        Base64 data URI string
    
    Example:
        # From Bokeh plot
        p = figure(...)
        bg = prepare_background(p)
        
        # From file
        bg = prepare_background('map.png')
        
        # From numpy array
        bg = prepare_background(depth_array, cmap='ocean')
        
        # From coastlines
        bg = prepare_background([island1, island2])
    """
    import numpy as np
    from bokeh.models import Plot, LayoutDOM
    
    # Bokeh plot
    if isinstance(source, (Plot, LayoutDOM)):
        return bokeh_to_base64(source, **kwargs)
    
    # File path
    elif isinstance(source, str) and '.' in source:
        return image_file_to_base64(source)
    
    # Numpy array
    elif isinstance(source, np.ndarray):
        return numpy_array_to_base64(source, **kwargs)
    
    # Coastline polygons
    elif isinstance(source, list):
        return create_coastline_background(coastlines=source, **kwargs)
    
    else:
        raise ValueError(
            f"Unsupported source type: {type(source)}. "
            "Expected Bokeh plot, file path, numpy array, or coastline list."
        )
