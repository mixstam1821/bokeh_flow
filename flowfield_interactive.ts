// flowfield_interactive.ts - Flow Field Visualization with Zoom, Pan, and Tooltip
import * as p from "core/properties"
import {LayoutDOM, LayoutDOMView} from "models/layouts/layout_dom"
import {div} from "core/dom"

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  maxLife: number
}

export class FlowFieldInteractiveView extends LayoutDOMView {
  declare model: FlowFieldInteractive
  private container_el?: HTMLDivElement
  private canvas?: HTMLCanvasElement
  private ctx?: CanvasRenderingContext2D
  private tooltip_el?: HTMLDivElement
  private animation_id?: number
  private particles: Particle[] = []
  
  // Pan and zoom state
  private pan_x: number = 0
  private pan_y: number = 0
  private zoom: number = 1
  private is_panning: boolean = false
  private last_mouse_x: number = 0
  private last_mouse_y: number = 0

  override get child_models(): LayoutDOM[] {
    return []
  }

  override connect_signals(): void {
    super.connect_signals()
    
    // React to property changes from Python/Bokeh widgets
    const {particle_count, particle_life, animate, background_color} = this.model.properties
    
    this.on_change(particle_count, () => this.reset_particles())
    this.on_change(particle_life, () => {
      // Update max life for existing particles
      for (const p of this.particles) {
        p.maxLife = this.model.particle_life
      }
    })
    this.on_change(animate, () => {
      if (this.model.animate) {
        this.start_animation()
      } else {
        this.stop_animation()
        this.render_frame()
      }
    })
    this.on_change(background_color, () => {
      if (this.container_el) {
        this.container_el.style.background = this.model.background_color
      }
    })
  }

  override render(): void {
    super.render()
    const width = this.model.width ?? 800
    const height = this.model.height ?? 600
    
    // Container for canvas + tooltip
    this.container_el = div({style: {
      position: 'relative',
      width: `${width}px`,
      height: `${height}px`,
      overflow: 'hidden',
      borderRadius: '8px',
      background: this.model.background_color,
      cursor: 'grab'
    }})
    
    // Canvas for flow field
    this.canvas = document.createElement('canvas')
    this.canvas.width = width
    this.canvas.height = height
    this.canvas.style.cssText = `
      display: block;
      touch-action: none;
    `
    
    // Tooltip
    this.tooltip_el = div({style: {
      position: 'absolute',
      display: 'none',
      background: 'rgba(0, 0, 0, 0.85)',
      color: 'white',
      padding: '8px 12px',
      borderRadius: '6px',
      fontSize: '12px',
      fontFamily: 'monospace',
      pointerEvents: 'none',
      zIndex: '1000',
      whiteSpace: 'nowrap',
      border: '1px solid rgba(255, 255, 255, 0.2)',
      boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
    }})
    
    this.container_el.appendChild(this.canvas)
    this.container_el.appendChild(this.tooltip_el)
    this.shadow_el.appendChild(this.container_el)
    
    this.ctx = this.canvas.getContext('2d')!
    
    // Add interaction listeners
    this.setup_interactions()
    
    this.reset_particles()
    
    if (this.model.animate) {
      this.start_animation()
    } else {
      this.render_frame()
    }
  }

  private setup_interactions(): void {
    if (!this.canvas || !this.container_el) return
    
    // Mouse wheel zoom
    this.canvas.addEventListener('wheel', (e: WheelEvent) => {
      e.preventDefault()
      const rect = this.canvas!.getBoundingClientRect()
      const mouse_x = e.clientX - rect.left
      const mouse_y = e.clientY - rect.top
      
      const zoom_factor = e.deltaY > 0 ? 0.9 : 1.1
      const new_zoom = Math.max(0.5, Math.min(5, this.zoom * zoom_factor))
      
      // Zoom towards mouse position
      this.pan_x = mouse_x - (mouse_x - this.pan_x) * (new_zoom / this.zoom)
      this.pan_y = mouse_y - (mouse_y - this.pan_y) * (new_zoom / this.zoom)
      this.zoom = new_zoom
      
      this.render_frame()
    })
    
    // Mouse pan
    this.canvas.addEventListener('mousedown', (e: MouseEvent) => {
      this.is_panning = true
      this.last_mouse_x = e.clientX
      this.last_mouse_y = e.clientY
      this.container_el!.style.cursor = 'grabbing'
    })
    
    this.canvas.addEventListener('mousemove', (e: MouseEvent) => {
      if (this.is_panning) {
        const dx = e.clientX - this.last_mouse_x
        const dy = e.clientY - this.last_mouse_y
        this.pan_x += dx
        this.pan_y += dy
        this.last_mouse_x = e.clientX
        this.last_mouse_y = e.clientY
        this.render_frame()
      } else {
        // Show tooltip
        this.show_tooltip(e)
      }
    })
    
    this.canvas.addEventListener('mouseup', () => {
      this.is_panning = false
      this.container_el!.style.cursor = 'grab'
    })
    
    this.canvas.addEventListener('mouseleave', () => {
      this.is_panning = false
      this.container_el!.style.cursor = 'grab'
      if (this.tooltip_el) {
        this.tooltip_el.style.display = 'none'
      }
    })
  }

  private show_tooltip(e: MouseEvent): void {
    if (!this.canvas || !this.tooltip_el) return
    
    const rect = this.canvas.getBoundingClientRect()
    const canvas_x = e.clientX - rect.left
    const canvas_y = e.clientY - rect.top
    
    // Transform to flow field coordinates
    const flow_x = (canvas_x - this.pan_x) / this.zoom
    const flow_y = (canvas_y - this.pan_y) / this.zoom
    
    // Get flow at this position
    const flow = this.get_flow_at(flow_x, flow_y)
    
    // Format tooltip
    const speed = Math.sqrt(flow.dx**2 + flow.dy**2)
    const angle = Math.atan2(flow.dy, flow.dx) * 180 / Math.PI
    
    this.tooltip_el.innerHTML = `
      <div style="margin-bottom: 4px;"><strong>Position:</strong> (${flow_x.toFixed(1)}, ${flow_y.toFixed(1)})</div>
      <div style="margin-bottom: 4px;"><strong>Velocity:</strong> dx=${flow.dx.toFixed(3)}, dy=${flow.dy.toFixed(3)}</div>
      <div style="margin-bottom: 4px;"><strong>Speed:</strong> ${speed.toFixed(3)}</div>
      <div><strong>Direction:</strong> ${angle.toFixed(1)}°</div>
    `
    
    // Position tooltip
    const tooltip_x = Math.min(canvas_x + 15, rect.width - 200)
    const tooltip_y = Math.max(10, canvas_y - 80)
    
    this.tooltip_el.style.left = tooltip_x + 'px'
    this.tooltip_el.style.top = tooltip_y + 'px'
    this.tooltip_el.style.display = 'block'
  }

  private reset_particles(): void {
    if (!this.canvas) return
    
    const width = this.canvas.width
    const height = this.canvas.height
    
    this.particles = []
    for (let i = 0; i < this.model.particle_count; i++) {
      this.particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: 0,
        vy: 0,
        life: Math.random() * this.model.particle_life,
        maxLife: this.model.particle_life
      })
    }
  }

  private get_flow_at(x: number, y: number): {dx: number, dy: number, mag: number} {
    if (!this.canvas) return {dx: 0, dy: 0, mag: 0}
    
    const xs = this.model.x_coords
    const ys = this.model.y_coords
    const dxs = this.model.dx_values
    const dys = this.model.dy_values
    const mags = this.model.magnitudes
    
    if (xs.length === 0 || ys.length === 0) return {dx: 0, dy: 0, mag: 0}
    
    // Find nearest grid point (simple nearest-neighbor interpolation)
    let min_dist = Infinity
    let best_idx = 0
    
    for (let i = 0; i < xs.length; i++) {
      const dist = Math.sqrt((xs[i] - x)**2 + (ys[i] - y)**2)
      if (dist < min_dist) {
        min_dist = dist
        best_idx = i
      }
    }
    
    return {
      dx: dxs[best_idx],
      dy: dys[best_idx],
      mag: mags[best_idx]
    }
  }

  private get_color_palette(): string[] {
    const palettes: {[key: string]: string[]} = {
      viridis: ['#440154', '#482777', '#3f4a8a', '#31678e', '#26838f', '#1f9d8a', 
                '#6cce5a', '#b6de2b', '#fee825'],
      turbo: ['#30123b', '#4454c4', '#4990c9', '#1ac7c2', '#52f667', '#a4fc3b', 
              '#f2d13a', '#fb8022', '#c42503', '#7a0402'],
      plasma: ['#0d0887', '#5302a3', '#8b0aa5', '#b83289', '#db5c68', '#f48849', 
               '#febd2a', '#f0f921'],
      inferno: ['#000004', '#320a5a', '#781c6d', '#bb3654', '#ed6925', '#fbb41a', '#fcffa4'],
      cividis: ['#00204c', '#414487', '#5d6c9c', '#7e94b4', '#a3bdcb', '#cae3e3', '#ffea46'],
      ocean: ['#001f3f', '#0056a7', '#0080ff', '#00a8e8', '#00c9ff', '#7fdfff', '#bfefff'],
      rainbow: ['#9400D3', '#4B0082', '#0000FF', '#00FF00', '#FFFF00', '#FF7F00', '#FF0000']
    }
    
    return palettes[this.model.color_scheme] || palettes.viridis
  }

  private update_particles(): void {
    if (!this.canvas) return
    
    const width = this.canvas.width
    const height = this.canvas.height
    
    for (const p of this.particles) {
      const flow = this.get_flow_at(p.x, p.y)
      
      // Apply flow strength multiplier
      p.vx = flow.dx * this.model.flow_strength
      p.vy = flow.dy * this.model.flow_strength
      
      // Update position
      p.x += p.vx
      p.y += p.vy
      
      // Age the particle
      p.life--
      
      // Respawn if dead or out of bounds
      if (p.life <= 0 || p.x < 0 || p.x > width || p.y < 0 || p.y > height) {
        p.x = Math.random() * width
        p.y = Math.random() * height
        p.vx = 0
        p.vy = 0
        p.life = p.maxLife
      }
    }
  }

  private render_frame(): void {
    if (!this.ctx || !this.canvas) return
    
    const ctx = this.ctx
    const width = this.canvas.width
    const height = this.canvas.height
    
    // Save context state
    ctx.save()
    
    // Clear with fade effect
    const bg = this.model.background_color
    if (bg === 'transparent' || bg.includes('rgba')) {
      ctx.clearRect(0, 0, width, height)
    } else {
      // Semi-transparent fill for trail effect
      ctx.fillStyle = bg + '20'
      ctx.fillRect(0, 0, width, height)
    }
    
    // Apply zoom and pan transform
    ctx.translate(this.pan_x, this.pan_y)
    ctx.scale(this.zoom, this.zoom)
    
    // Draw flow vectors if enabled
    if (this.model.show_vectors) {
      this.draw_vectors()
    }
    
    // Draw particles
    this.draw_particles()
    
    // Restore context state
    ctx.restore()
  }

  private draw_vectors(): void {
    if (!this.ctx) return
    
    const ctx = this.ctx
    const xs = this.model.x_coords
    const ys = this.model.y_coords
    const dxs = this.model.dx_values
    const dys = this.model.dy_values
    
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 1 / this.zoom  // Adjust line width for zoom
    ctx.globalAlpha = 0.3
    
    // Subsample for performance
    for (let i = 0; i < xs.length; i += 3) {
      const x = xs[i]
      const y = ys[i]
      const dx = dxs[i] * 20  // Scale for visibility
      const dy = dys[i] * 20
      
      ctx.beginPath()
      ctx.moveTo(x, y)
      ctx.lineTo(x + dx, y + dy)
      ctx.stroke()
      
      // Arrow head
      const angle = Math.atan2(dy, dx)
      const arrowSize = 5
      ctx.beginPath()
      ctx.moveTo(x + dx, y + dy)
      ctx.lineTo(
        x + dx - arrowSize * Math.cos(angle - Math.PI / 6),
        y + dy - arrowSize * Math.sin(angle - Math.PI / 6)
      )
      ctx.moveTo(x + dx, y + dy)
      ctx.lineTo(
        x + dx - arrowSize * Math.cos(angle + Math.PI / 6),
        y + dy - arrowSize * Math.sin(angle + Math.PI / 6)
      )
      ctx.stroke()
    }
    
    ctx.globalAlpha = 1.0
  }

  private draw_particles(): void {
    if (!this.ctx) return
    
    const ctx = this.ctx
    const palette = this.get_color_palette()
    
    for (const p of this.particles) {
      const flow = this.get_flow_at(p.x, p.y)
      
      // Map magnitude to color
      const normalized_mag = Math.min(flow.mag / 2, 1)
      const color_idx = Math.floor(normalized_mag * (palette.length - 1))
      const color = palette[color_idx]
      
      // Fade based on lifetime
      const life_factor = p.life / p.maxLife
      const size = this.model.particle_size
      const alpha = 0.7 * life_factor
      
      ctx.fillStyle = color
      ctx.globalAlpha = alpha
      
      ctx.beginPath()
      ctx.arc(p.x, p.y, size, 0, Math.PI * 2)
      ctx.fill()
    }
    
    ctx.globalAlpha = 1.0
  }

  private animate_frame = (): void => {
    if (!this.model.animate) return
    
    // Update multiple times per frame based on animation speed
    for (let i = 0; i < this.model.animation_speed; i++) {
      this.update_particles()
    }
    
    this.render_frame()
    this.animation_id = requestAnimationFrame(this.animate_frame)
  }

  private start_animation(): void {
    if (this.animation_id !== undefined) return
    this.animation_id = requestAnimationFrame(this.animate_frame)
  }

  private stop_animation(): void {
    if (this.animation_id !== undefined) {
      cancelAnimationFrame(this.animation_id)
      this.animation_id = undefined
    }
  }

  override remove(): void {
    this.stop_animation()
    super.remove()
  }
}

export namespace FlowFieldInteractive {
  export type Attrs = p.AttrsOf<Props>
  export type Props = LayoutDOM.Props & {
    x_coords: p.Property<number[]>
    y_coords: p.Property<number[]>
    dx_values: p.Property<number[]>
    dy_values: p.Property<number[]>
    magnitudes: p.Property<number[]>
    particle_count: p.Property<number>
    particle_size: p.Property<number>
    particle_life: p.Property<number>
    flow_strength: p.Property<number>
    animate: p.Property<boolean>
    animation_speed: p.Property<number>
    show_vectors: p.Property<boolean>
    background_color: p.Property<string>
    color_scheme: p.Property<string>
  }
}

export interface FlowFieldInteractive extends FlowFieldInteractive.Attrs {}

export class FlowFieldInteractive extends LayoutDOM {
  declare properties: FlowFieldInteractive.Props
  declare __view_type__: FlowFieldInteractiveView

  constructor(attrs?: Partial<FlowFieldInteractive.Attrs>) {
    super(attrs)
  }

  static {
    this.prototype.default_view = FlowFieldInteractiveView
    this.define<FlowFieldInteractive.Props>(({Bool, Float, Int, List, String}) => ({
      x_coords: [ List(Float), [] ],
      y_coords: [ List(Float), [] ],
      dx_values: [ List(Float), [] ],
      dy_values: [ List(Float), [] ],
      magnitudes: [ List(Float), [] ],
      particle_count: [ Int, 3000 ],
      particle_size: [ Float, 2 ],
      particle_life: [ Int, 100 ],
      flow_strength: [ Float, 2.5 ],
      animate: [ Bool, true ],
      animation_speed: [ Float, 1.0 ],
      show_vectors: [ Bool, false ],
      background_color: [ String, '#0a0a0a' ],
      color_scheme: [ String, 'viridis' ],
    }))
  }
}
