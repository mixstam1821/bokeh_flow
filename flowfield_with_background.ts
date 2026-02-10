// flowfield_with_background.ts - FINAL FIX with proper fade control
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
  trail_x: number[]
  trail_y: number[]
}

export class FlowFieldWithBackgroundView extends LayoutDOMView {
  declare model: FlowFieldWithBackground
  private container_el?: HTMLDivElement
  private canvas?: HTMLCanvasElement
  private ctx?: CanvasRenderingContext2D
  private trail_canvas?: HTMLCanvasElement
  private trail_ctx?: CanvasRenderingContext2D
  private tooltip_el?: HTMLDivElement
  private background_img?: HTMLImageElement
  private animation_id?: number
  private particles: Particle[] = []
  private frame_count: number = 0  // Track frames for periodic refresh
  
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
    
    const {particle_count, particle_life, animate, background_color, background_image, particle_trail} = this.model.properties
    
    this.on_change(particle_count, () => this.reset_particles())
    this.on_change(particle_life, () => {
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
    this.on_change(background_image, () => {
      this.load_background_image()
    })
    this.on_change(particle_trail, () => {
      if (this.trail_ctx && this.trail_canvas) {
        this.trail_ctx.clearRect(0, 0, this.trail_canvas.width, this.trail_canvas.height)
      }
      this.render_frame()
    })
  }

  override render(): void {
    super.render()
    const width = this.model.width ?? 800
    const height = this.model.height ?? 600
    
    // Container
    this.container_el = div({style: {
      position: 'relative',
      width: `${width}px`,
      height: `${height}px`,
      overflow: 'hidden',
      borderRadius: '8px',
      background: this.model.background_color,
      cursor: 'grab'
    }})
    
    // Main canvas (background + vectors)
    this.canvas = document.createElement('canvas')
    this.canvas.width = width
    this.canvas.height = height
    this.canvas.style.cssText = `
      position: absolute;
      top: 0;
      left: 0;
      display: block;
    `
    
    // Trail canvas (particles - on top, receives events)
    this.trail_canvas = document.createElement('canvas')
    this.trail_canvas.width = width
    this.trail_canvas.height = height
    this.trail_canvas.style.cssText = `
      position: absolute;
      top: 0;
      left: 0;
      display: block;
      touch-action: none;
    `
    
    // Tooltip
    this.tooltip_el = div({style: {
      position: 'absolute',
      display: 'none',
      background: 'rgba(0, 0, 0, 0.9)',
      color: 'white',
      padding: '8px 12px',
      borderRadius: '6px',
      fontSize: '12px',
      fontFamily: 'monospace',
      pointerEvents: 'none',
      zIndex: '1000',
      whiteSpace: 'nowrap',
      border: '1px solid rgba(255, 255, 255, 0.3)',
      boxShadow: '0 2px 8px rgba(0,0,0,0.4)'
    }})
    
    this.container_el.appendChild(this.canvas)
    this.container_el.appendChild(this.trail_canvas)
    this.container_el.appendChild(this.tooltip_el)
    this.shadow_el.appendChild(this.container_el)
    
    this.ctx = this.canvas.getContext('2d')!
    this.trail_ctx = this.trail_canvas.getContext('2d')!
    
    this.load_background_image()
    this.setup_interactions()
    this.reset_particles()
    
    if (this.model.animate) {
      this.start_animation()
    } else {
      this.render_frame()
    }
  }

  private load_background_image(): void {
    if (!this.model.background_image) {
      this.background_img = undefined
      this.render_frame()
      return
    }

    this.background_img = new Image()
    this.background_img.onload = () => {
      this.render_frame()
    }
    this.background_img.onerror = () => {
      console.error('Failed to load background image')
      this.background_img = undefined
      this.render_frame()
    }
    this.background_img.src = this.model.background_image
  }

  private setup_interactions(): void {
    if (!this.trail_canvas || !this.container_el) return
    
    const canvas = this.trail_canvas
    
    // Mouse wheel zoom
    canvas.addEventListener('wheel', (e: WheelEvent) => {
      e.preventDefault()
      const rect = canvas.getBoundingClientRect()
      const mouse_x = e.clientX - rect.left
      const mouse_y = e.clientY - rect.top
      
      const zoom_factor = e.deltaY > 0 ? 0.9 : 1.1
      const new_zoom = Math.max(0.5, Math.min(5, this.zoom * zoom_factor))
      
      this.pan_x = mouse_x - (mouse_x - this.pan_x) * (new_zoom / this.zoom)
      this.pan_y = mouse_y - (mouse_y - this.pan_y) * (new_zoom / this.zoom)
      this.zoom = new_zoom
      
      // Clear trail canvas on zoom
      if (this.trail_ctx && this.trail_canvas) {
        this.trail_ctx.clearRect(0, 0, this.trail_canvas.width, this.trail_canvas.height)
      }
      
      this.render_frame()
    })
    
    // Mouse pan
    canvas.addEventListener('mousedown', (e: MouseEvent) => {
      this.is_panning = true
      this.last_mouse_x = e.clientX
      this.last_mouse_y = e.clientY
      this.container_el!.style.cursor = 'grabbing'
    })
    
    canvas.addEventListener('mousemove', (e: MouseEvent) => {
      if (this.is_panning) {
        const dx = e.clientX - this.last_mouse_x
        const dy = e.clientY - this.last_mouse_y
        this.pan_x += dx
        this.pan_y += dy
        this.last_mouse_x = e.clientX
        this.last_mouse_y = e.clientY
        
        // Clear trail on pan
        if (this.trail_ctx && this.trail_canvas) {
          this.trail_ctx.clearRect(0, 0, this.trail_canvas.width, this.trail_canvas.height)
        }
        
        this.render_frame()
      } else {
        this.show_tooltip(e)
      }
    })
    
    canvas.addEventListener('mouseup', () => {
      this.is_panning = false
      this.container_el!.style.cursor = 'grab'
    })
    
    canvas.addEventListener('mouseleave', () => {
      this.is_panning = false
      this.container_el!.style.cursor = 'grab'
      if (this.tooltip_el) {
        this.tooltip_el.style.display = 'none'
      }
    })
    
    // Touch support
    canvas.addEventListener('touchstart', (e: TouchEvent) => {
      if (e.touches.length === 1) {
        e.preventDefault()
        this.is_panning = true
        this.last_mouse_x = e.touches[0].clientX
        this.last_mouse_y = e.touches[0].clientY
      }
    })
    
    canvas.addEventListener('touchmove', (e: TouchEvent) => {
      if (e.touches.length === 1 && this.is_panning) {
        e.preventDefault()
        const dx = e.touches[0].clientX - this.last_mouse_x
        const dy = e.touches[0].clientY - this.last_mouse_y
        this.pan_x += dx
        this.pan_y += dy
        this.last_mouse_x = e.touches[0].clientX
        this.last_mouse_y = e.touches[0].clientY
        
        if (this.trail_ctx && this.trail_canvas) {
          this.trail_ctx.clearRect(0, 0, this.trail_canvas.width, this.trail_canvas.height)
        }
        
        this.render_frame()
      }
    })
    
    canvas.addEventListener('touchend', () => {
      this.is_panning = false
    })
  }

  private show_tooltip(e: MouseEvent): void {
    if (!this.trail_canvas || !this.tooltip_el) return
    
    const rect = this.trail_canvas.getBoundingClientRect()
    const canvas_x = e.clientX - rect.left
    const canvas_y = e.clientY - rect.top
    
    const flow_x = (canvas_x - this.pan_x) / this.zoom
    const flow_y = (canvas_y - this.pan_y) / this.zoom
    
    const flow = this.get_flow_at(flow_x, flow_y)
    const speed = Math.sqrt(flow.dx**2 + flow.dy**2)
    const angle = Math.atan2(flow.dy, flow.dx) * 180 / Math.PI
    
    this.tooltip_el.innerHTML = `
      <div style="margin-bottom: 4px;"><strong>Position:</strong> (${flow_x.toFixed(1)}, ${flow_y.toFixed(1)})</div>
      <div style="margin-bottom: 4px;"><strong>Velocity:</strong> dx=${flow.dx.toFixed(3)}, dy=${flow.dy.toFixed(3)}</div>
      <div style="margin-bottom: 4px;"><strong>Speed:</strong> ${speed.toFixed(3)}</div>
      <div><strong>Direction:</strong> ${angle.toFixed(1)}°</div>
    `
    
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
        maxLife: this.model.particle_life,
        trail_x: [],
        trail_y: []
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
    const palettes: { [key: string]: string[] } = {
      yellow: [
        '#ffe600',
      ],
    
      red: [
        '#fd0400',
      ],
    
      purple: [
        '#8b0aa5',
      ],
    
      blue: [
        '#0000FF',
      ],
    
      lightblue: [
        '#43d6ff',
      ],
    
      lime: [
        '#00FF00',
      ],
    
      white: [
        '#ffffff',
      ],
      pink: [
        '#ff4dc4',
      ],
    };
    
    
    return palettes[this.model.color_scheme] || palettes.viridis
  }

  private update_particles(): void {
    if (!this.canvas) return
    
    const width = this.canvas.width
    const height = this.canvas.height
    const trail_length = 8
    
    for (const p of this.particles) {
      const flow = this.get_flow_at(p.x, p.y)
      
      p.vx = flow.dx * this.model.flow_strength
      p.vy = flow.dy * this.model.flow_strength
      
      if (this.model.particle_trail) {
        p.trail_x.push(p.x)
        p.trail_y.push(p.y)
        
        if (p.trail_x.length > trail_length) {
          p.trail_x.shift()
          p.trail_y.shift()
        }
      } else {
        p.trail_x = []
        p.trail_y = []
      }
      
      p.x += p.vx
      p.y += p.vy
      p.life--
      
      if (p.life <= 0 || p.x < 0 || p.x > width || p.y < 0 || p.y > height) {
        p.x = Math.random() * width
        p.y = Math.random() * height
        p.vx = 0
        p.vy = 0
        p.life = p.maxLife
        p.trail_x = []
        p.trail_y = []
      }
    }
  }

  private render_frame(): void {
    if (!this.ctx || !this.canvas || !this.trail_ctx || !this.trail_canvas) return
    
    const ctx = this.ctx
    const trail_ctx = this.trail_ctx
    const width = this.canvas.width
    const height = this.canvas.height
    
    this.frame_count++
    
    // =====================================
    // MAIN CANVAS: Background + Vectors
    // (Always clear and redraw fresh!)
    // =====================================
    ctx.save()
    ctx.clearRect(0, 0, width, height)
    
    const bg = this.model.background_color
    if (bg !== 'transparent' && !bg.includes('rgba(0,0,0,0)')) {
      ctx.fillStyle = bg
      ctx.fillRect(0, 0, width, height)
    }
    
    ctx.translate(this.pan_x, this.pan_y)
    ctx.scale(this.zoom, this.zoom)
    
    // Draw background image (always fresh)
    if (this.background_img && this.background_img.complete) {
      ctx.globalAlpha = this.model.background_alpha
      ctx.drawImage(this.background_img, 0, 0, width, height)
      ctx.globalAlpha = 1.0
    }
    
    // Draw vectors
    if (this.model.show_vectors) {
      this.draw_vectors(ctx)
    }
    
    ctx.restore()
    
    // =====================================
    // TRAIL CANVAS: Particles with Trails
    // =====================================
    trail_ctx.save()
    
    if (this.model.particle_trail) {
      // IMPORTANT: Refresh every N frames to prevent over-darkening!
      const refresh_interval = 300  // Clear completely every 300 frames (~5 seconds at 60fps)
      
      if (this.frame_count % refresh_interval === 0) {
        // Complete refresh
        trail_ctx.clearRect(0, 0, width, height)
      } else {
        // Normal fade - VERY subtle to prevent darkening
        trail_ctx.globalCompositeOperation = 'destination-out'
        trail_ctx.fillStyle = 'rgba(0, 0, 0, 0.02)'  // Only 2% fade per frame
        trail_ctx.fillRect(0, 0, width, height)
        trail_ctx.globalCompositeOperation = 'source-over'
      }
    } else {
      // No trails - clear completely
      trail_ctx.clearRect(0, 0, width, height)
    }
    
    // Apply same transforms
    trail_ctx.translate(this.pan_x, this.pan_y)
    trail_ctx.scale(this.zoom, this.zoom)
    
    // Draw particles
    this.draw_particles(trail_ctx)
    
    trail_ctx.restore()
  }

  private draw_vectors(ctx: CanvasRenderingContext2D): void {
    const xs = this.model.x_coords
    const ys = this.model.y_coords
    const dxs = this.model.dx_values
    const dys = this.model.dy_values
    
    ctx.strokeStyle = this.model.vector_color
    ctx.lineWidth = this.model.vector_width / this.zoom
    ctx.globalAlpha = this.model.vector_alpha
    
    const subsample = Math.max(1, Math.floor(5 / this.zoom))
    
    for (let i = 0; i < xs.length; i += subsample) {
      const x = xs[i]
      const y = ys[i]
      const dx = dxs[i] * this.model.vector_scale
      const dy = dys[i] * this.model.vector_scale
      
      ctx.beginPath()
      ctx.moveTo(x, y)
      ctx.lineTo(x + dx, y + dy)
      ctx.stroke()
      
      const angle = Math.atan2(dy, dx)
      const arrowSize = 5 / this.zoom
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

  private draw_particles(ctx: CanvasRenderingContext2D): void {
    const palette = this.get_color_palette()
    
    for (const p of this.particles) {
      const flow = this.get_flow_at(p.x, p.y)
      
      const normalized_mag = Math.min(flow.mag / 2, 1)
      const color_idx = Math.floor(normalized_mag * (palette.length - 1))
      const color = palette[color_idx]
      
      const life_factor = p.life / p.maxLife
      const size = this.model.particle_size / this.zoom
      
      // Draw trail line
      if (this.model.particle_trail && p.trail_x.length > 1) {
        ctx.strokeStyle = color
        ctx.lineWidth = size * 0.5
        ctx.globalAlpha = 0.4 * life_factor
        
        ctx.beginPath()
        ctx.moveTo(p.trail_x[0], p.trail_y[0])
        for (let i = 1; i < p.trail_x.length; i++) {
          ctx.lineTo(p.trail_x[i], p.trail_y[i])
        }
        ctx.stroke()
      }
      
      // Draw particle dot
      const alpha = 0.9 * life_factor  // Brighter particles
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

export namespace FlowFieldWithBackground {
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
    particle_trail: p.Property<boolean>
    flow_strength: p.Property<number>
    animate: p.Property<boolean>
    animation_speed: p.Property<number>
    show_vectors: p.Property<boolean>
    vector_color: p.Property<string>
    vector_width: p.Property<number>
    vector_alpha: p.Property<number>
    vector_scale: p.Property<number>
    background_color: p.Property<string>
    background_image: p.Property<string>
    background_alpha: p.Property<number>
    color_scheme: p.Property<string>
  }
}

export interface FlowFieldWithBackground extends FlowFieldWithBackground.Attrs {}

export class FlowFieldWithBackground extends LayoutDOM {
  declare properties: FlowFieldWithBackground.Props
  declare __view_type__: FlowFieldWithBackgroundView

  constructor(attrs?: Partial<FlowFieldWithBackground.Attrs>) {
    super(attrs)
  }

  static {
    this.prototype.default_view = FlowFieldWithBackgroundView
    this.define<FlowFieldWithBackground.Props>(({Bool, Float, Int, List, String}) => ({
      x_coords: [ List(Float), [] ],
      y_coords: [ List(Float), [] ],
      dx_values: [ List(Float), [] ],
      dy_values: [ List(Float), [] ],
      magnitudes: [ List(Float), [] ],
      particle_count: [ Int, 3000 ],
      particle_size: [ Float, 2 ],
      particle_life: [ Int, 100 ],
      particle_trail: [ Bool, true ],
      flow_strength: [ Float, 2.5 ],
      animate: [ Bool, true ],
      animation_speed: [ Float, 1.0 ],
      show_vectors: [ Bool, false ],
      vector_color: [ String, '#ffffff' ],
      vector_width: [ Float, 1.0 ],
      vector_alpha: [ Float, 0.3 ],
      vector_scale: [ Float, 20.0 ],
      background_color: [ String, 'transparent' ],
      background_image: [ String, '' ],
      background_alpha: [ Float, 1.0 ],
      color_scheme: [ String, 'viridis' ],
    }))
  }
}