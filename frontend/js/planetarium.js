/**
 * AstraTrack AI - Celestial Dome & Millennial Planetarium Engine
 * Renders the 3D celestial sphere, stars with proper motion drift, constellation lines,
 * and the 25,772-year North Celestial Pole precession ring.
 * NEON VOID EDITION: Enhanced sparkling starfield, neon constellation filaments, deep void background.
 */

class PlanetariumView {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    
    // Viewport camera parameters
    this.yaw = 0.0;     // Azimuth rotation
    this.pitch = 0.6;   // Altitude angle (radians)
    this.zoom = 1.0;
    this.isDragging = false;
    this.lastMouse = { x: 0, y: 0 };
    
    // Astronomical dataset
    this.stars = [];
    this.constellations = [];
    this.poleTelemetry = null;
    this.precessionCircle = [];
    this.currentYear = 2026.0;
    this.showProperMotionVectors = true;
    this.showConstellationLines = true;
    this.distanceMapMode = false;
    this.hoveredStar = null;
    this.selectedStar = null;
    this.dragMoved = false;

    // Neon void: background star particles for depth
    this.bgStarParticles = this._generateBgStars(320);
    // Per-star twinkle phase offsets
    this._twinklePhases = [];
    this._constellationPulse = 0;
    
    this.setupInteraction();
  }

  /** Generate a random set of tiny background star particles */
  _generateBgStars(count) {
    const stars = [];
    for (let i = 0; i < count; i++) {
      stars.push({
        x: Math.random(),
        y: Math.random(),
        r: Math.random() * 1.2 + 0.2,
        opacity: Math.random() * 0.7 + 0.15,
        twinkleSpeed: Math.random() * 0.8 + 0.2,
        twinkleOffset: Math.random() * Math.PI * 2,
        color: Math.random() < 0.15
          ? (Math.random() < 0.5 ? '#a0c8ff' : '#ffe8c0')
          : '#ffffff',
      });
    }
    return stars;
  }

  setupInteraction() {
    this.canvas.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.dragMoved = false;
      this.lastMouse = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('mouseup', () => {
      this.isDragging = false;
    });

    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      if (this.isDragging) {
        const dx = e.clientX - this.lastMouse.x;
        const dy = e.clientY - this.lastMouse.y;
        if (Math.abs(dx) + Math.abs(dy) > 3) this.dragMoved = true;
        this.yaw += dx * 0.005;
        this.pitch = Math.max(-1.4, Math.min(1.4, this.pitch + dy * 0.005));
        this.lastMouse = { x: e.clientX, y: e.clientY };
      }

      this.checkStarHover(mouseX, mouseY);
    });

    this.canvas.addEventListener('click', (e) => {
      if (this.dragMoved) return;
      const rect = this.canvas.getBoundingClientRect();
      this.checkStarHover(e.clientX - rect.left, e.clientY - rect.top);
      if (!this.hoveredStar) return;
      this.selectedStar = this.hoveredStar.star;
      this.canvas.dispatchEvent(new CustomEvent('astratrack:starselected', { detail: this.selectedStar }));
    });

    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
      this.zoom = Math.max(0.5, Math.min(3.5, this.zoom * zoomFactor));
    });
  }

  setData(skyData) {
    this.stars = skyData.stars || [];
    this.constellations = skyData.constellations || [];
    this.poleTelemetry = skyData.pole_telemetry;
    this.precessionCircle = skyData.precession_circle || [];
    this.currentYear = skyData.year || 2026.0;
    // Reset twinkle phases when star data updates
    this._twinklePhases = this.stars.map(() => Math.random() * Math.PI * 2);
  }

  // 3D Cartesian spherical coordinate projection to screen 2D
  project3D(cartesian, radius) {
    let { x, y, z } = cartesian;

    // Apply Yaw (rotation around Z axis)
    const cosY = Math.cos(this.yaw);
    const sinY = Math.sin(this.yaw);
    const x1 = x * cosY - y * sinY;
    const y1 = x * sinY + y * cosY;
    const z1 = z;

    // Apply Pitch (rotation around X axis)
    const cosP = Math.cos(this.pitch);
    const sinP = Math.sin(this.pitch);
    const x2 = x1;
    const y2 = y1 * cosP - z1 * sinP;
    const z2 = y1 * sinP + z1 * cosP;

    // Stereographic / Perspective Projection
    const cx = this.canvas.width / 2;
    const cy = this.canvas.height / 2;
    const scale = (Math.min(cx, cy) * 0.85) * this.zoom;

    // Distance factor for perspective
    const fov = 2.2;
    const pz = z2 + fov;
    if (pz <= 0.1) return null; // Behind camera clipping

    const screenX = cx + (x2 / pz) * scale * 2.0;
    const screenY = cy - (y2 / pz) * scale * 2.0;

    return { x: screenX, y: screenY, depth: z2, isVisible: z2 > -0.8 };
  }

  checkStarHover(mouseX, mouseY) {
    const baseRadius = Math.min(this.canvas.width, this.canvas.height) / 2;
    let found = null;

    for (const star of this.stars) {
      const pt = this.project3D(this.renderPosition(star), baseRadius);
      if (pt && pt.isVisible) {
        const dist = Math.hypot(mouseX - pt.x, mouseY - pt.y);
        const hitRadius = Math.max(12, 18 - star.mag * 3);
        if (dist < hitRadius) {
          found = { star, screenX: pt.x, screenY: pt.y };
          break;
        }
      }
    }
    this.hoveredStar = found;
  }

  renderPosition(star) {
    if (!this.distanceMapMode || !star.distance_au) return star.cartesian;
    const radius = 0.65 + Math.max(0, Math.log10(star.distance_au) - 5) * 0.12;
    return { x: star.cartesian.x * radius, y: star.cartesian.y * radius, z: star.cartesian.z * radius };
  }

  render() {
    const w = this.canvas.width;
    const h = this.canvas.height;
    const ctx = this.ctx;

    this._constellationPulse = (Date.now() * 0.001);

    ctx.clearRect(0, 0, w, h);

    // 0. Draw deep void black background with radial nebula depth effect
    this.renderVoidBackground();

    // 1. Draw background star particles (deep space static field)
    this.renderBgStarParticles();

    // 2. Draw Celestial Horizon / Dome background grid
    if (this.distanceMapMode) this.renderDistanceShells();
    else this.renderDomeGrid();

    // 3. Draw 25,772-year Precession Circle of the North Celestial Pole
    if (!this.distanceMapMode) this.renderPrecessionCircle();

    // 4. Draw Constellation lines (neon filaments)
    if (this.showConstellationLines) {
      this.renderConstellations();
    }

    // 5. Draw Stars and Proper Motion Drift (with sparkling twinkling)
    this.renderStars();

    if (this.selectedStar) this.renderSelectedStar();

    // 6. Draw Active Pole Star Marker
    if (!this.distanceMapMode) this.renderCurrentPoleMarker();

    // 7. Draw Star Hover Tooltip
    if (this.hoveredStar) {
      this.renderTooltip(this.hoveredStar);
    }
  }

  renderSelectedStar() {
    const star = this.stars.find(item => item.id === this.selectedStar.id);
    if (!star) return;
    const point = this.project3D(this.renderPosition(star), 1);
    if (!point || !point.isVisible) return;
    const ctx = this.ctx;
    ctx.save();
    ctx.strokeStyle = 'rgba(219, 198, 153, .84)';
    ctx.lineWidth = 1.25;
    ctx.beginPath();
    ctx.arc(point.x, point.y, 10, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = '#e5d8b8';
    ctx.font = '11px sans-serif';
    ctx.fillText(star.name.split(' (')[0], point.x + 14, point.y - 8);
    ctx.restore();
  }

  /** Pure void black background with subtle nebula depth gradients */
  renderVoidBackground() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    // Absolute void black
    ctx.fillStyle = '#000002';
    ctx.fillRect(0, 0, w, h);

    // Very subtle nebula color pockets for depth
    const nebulae = [
      { x: 0.25, y: 0.3,  r: 0.35, color: 'rgba(64, 77, 102, 0.16)'  },
      { x: 0.75, y: 0.65, r: 0.28, color: 'rgba(89, 73, 86, 0.10)'   },
      { x: 0.55, y: 0.15, r: 0.22, color: 'rgba(70, 88, 103, 0.09)'   },
      { x: 0.4,  y: 0.8,  r: 0.2,  color: 'rgba(81, 77, 100, 0.07)'   },
    ];

    for (const n of nebulae) {
      const gx = n.x * w;
      const gy = n.y * h;
      const gr = n.r * Math.max(w, h);
      const grad = ctx.createRadialGradient(gx, gy, 0, gx, gy, gr);
      grad.addColorStop(0, n.color);
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);
    }
  }

  /** Render tiny twinkling background star particles for cosmic depth */
  renderBgStarParticles() {
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    const t = Date.now() * 0.001;

    for (const s of this.bgStarParticles) {
      const twinkle = 0.5 + 0.5 * Math.sin(t * s.twinkleSpeed + s.twinkleOffset);
      const opacity = s.opacity * (0.4 + 0.6 * twinkle);
      const radius = s.r * (0.7 + 0.3 * twinkle);
      const px = s.x * w;
      const py = s.y * h;

      ctx.globalAlpha = opacity;
      ctx.fillStyle = s.color;
      ctx.beginPath();
      ctx.arc(px, py, radius, 0, Math.PI * 2);
      ctx.fill();

      // Add a faint glow for brighter background stars
      if (twinkle > 0.75 && s.r > 0.7) {
        const glow = ctx.createRadialGradient(px, py, 0, px, py, radius * 4);
        glow.addColorStop(0, `rgba(180, 220, 255, ${opacity * 0.3})`);
        glow.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(px, py, radius * 4, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    ctx.globalAlpha = 1;
  }

  renderDistanceShells() {
    const ctx = this.ctx;
    ctx.save();
    ctx.strokeStyle = 'rgba(184,197,217,.22)';
    ctx.fillStyle = 'rgba(184,197,217,.58)';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 6]);
    [1e6, 1e7, 1e8].forEach((au) => {
      const radius = 0.65 + (Math.log10(au) - 5) * 0.12;
      ctx.beginPath();
      let started = false;
      for (let i = 0; i <= 80; i++) {
        const a = i / 80 * Math.PI * 2;
        const p = this.project3D({ x: Math.cos(a) * radius, y: Math.sin(a) * radius, z: 0 }, 1);
        if (!p) continue;
        if (!started) { ctx.moveTo(p.x, p.y); started = true; }
        else ctx.lineTo(p.x, p.y);
      }
      ctx.stroke();
      const label = this.project3D({ x: radius, y: 0, z: 0 }, 1);
      if (label) ctx.fillText(`${au.toExponential(0)} AU`, label.x + 5, label.y - 5);
    });
    const earth = this.project3D({ x: 0, y: 0, z: 0 }, 1);
    if (earth) {
      ctx.setLineDash([]);
      ctx.fillStyle = '#d9c49a';
      ctx.beginPath(); ctx.arc(earth.x, earth.y, 4, 0, Math.PI * 2); ctx.fill();
      ctx.fillText('EARTH', earth.x + 8, earth.y - 5);
    }
    ctx.restore();
  }

  renderDomeGrid() {
    const ctx = this.ctx;

    // Draw Celestial Equator ring (Z = 0) — very faint neon blue
    ctx.strokeStyle = 'rgba(0, 100, 200, 0.15)';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 6]);

    ctx.beginPath();
    let first = true;
    for (let i = 0; i <= 64; i++) {
      const angle = (i / 64) * Math.PI * 2;
      const cart = { x: Math.cos(angle), y: Math.sin(angle), z: 0 };
      const pt = this.project3D(cart, 1);
      if (pt && pt.isVisible) {
        if (first) { ctx.moveTo(pt.x, pt.y); first = false; }
        else { ctx.lineTo(pt.x, pt.y); }
      }
    }
    ctx.stroke();
    ctx.setLineDash([]);
  }

  renderPrecessionCircle() {
    if (!this.precessionCircle || this.precessionCircle.length === 0) return;
    const ctx = this.ctx;
    const pulse = 0.3 + 0.15 * Math.sin(this._constellationPulse * 0.7);

    // Precession Circle Track — neon cyan dashed ring
    ctx.strokeStyle = `rgba(0, 243, 255, ${pulse})`;
    ctx.lineWidth = 1.5;
    ctx.shadowColor = 'rgba(0, 243, 255, 0.6)';
    ctx.shadowBlur = 6;
    ctx.setLineDash([3, 5]);
    ctx.beginPath();

    let started = false;
    for (const pt of this.precessionCircle) {
      const screenPt = this.project3D(pt.cartesian, 1);
      if (screenPt && screenPt.isVisible) {
        if (!started) { ctx.moveTo(screenPt.x, screenPt.y); started = true; }
        else { ctx.lineTo(screenPt.x, screenPt.y); }
      }
    }
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.shadowBlur = 0;

    // Draw historic Pole Star waypoints on the ring
    const waypoints = [
      { name: "Polaris (2026 CE)", year: 2026,   color: "#bdc8d1" },
      { name: "Errai (4000 CE)",   year: 4000,   color: "#d5bd8c" },
      { name: "Alderamin (7500 CE)", year: 7500,  color: "#93a3b7" },
      { name: "Vega (13,700 CE)",  year: 13700,  color: "#f0ece2" },
      { name: "Thuban (2800 BCE)", year: -2800,  color: "#a6b6aa" }
    ];

    ctx.font = '10px monospace';
    for (const wp of waypoints) {
      const closest = this.precessionCircle.reduce((prev, curr) =>
        Math.abs(curr.year - wp.year) < Math.abs(prev.year - wp.year) ? curr : prev
      );
      if (closest) {
        const p = this.project3D(closest.cartesian, 1);
        if (p && p.isVisible) {
          // Glowing waypoint dot
          ctx.shadowColor = wp.color;
          ctx.shadowBlur = 10;
          ctx.fillStyle = wp.color;
          ctx.beginPath();
          ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
          ctx.fillStyle = wp.color;
          ctx.fillText(wp.name, p.x + 7, p.y + 3);
        }
      }
    }
  }

  renderConstellations() {
    const ctx = this.ctx;
    const t = this._constellationPulse;

    // Animate the constellation line opacity with a slow pulse
    const basePulse = 0.45 + 0.2 * Math.sin(t * 0.4);
    const glowPulse = 0.5 + 0.5 * Math.sin(t * 0.6);

    for (const constellation of this.constellations) {
      for (const seg of constellation.segments) {
        const from = this.distanceMapMode ? this.stars.find(s => s.id === seg.from_id) : null;
        const to = this.distanceMapMode ? this.stars.find(s => s.id === seg.to_id) : null;
        const pt1 = this.project3D(from ? this.renderPosition(from) : seg.from_cartesian, 1);
        const pt2 = this.project3D(to ? this.renderPosition(to) : seg.to_cartesian, 1);

        if (pt1 && pt2 && pt1.isVisible && pt2.isVisible) {
          // Multi-pass glow effect for neon filament look
          // Pass 1: wide outer glow
          ctx.strokeStyle = this.distanceMapMode ? `rgba(189, 173, 139, ${basePulse * 0.1})` : `rgba(173, 186, 200, ${basePulse * 0.08})`;
          ctx.lineWidth = this.distanceMapMode ? 3 : 4;
          ctx.shadowColor = 'rgba(0, 243, 255, 0)';
          ctx.shadowBlur = 0;
          ctx.beginPath();
          ctx.moveTo(pt1.x, pt1.y);
          ctx.lineTo(pt2.x, pt2.y);
          ctx.stroke();

          // Pass 2: mid glow
          ctx.strokeStyle = this.distanceMapMode ? `rgba(189, 173, 139, ${basePulse * 0.32})` : `rgba(173, 186, 200, ${basePulse * 0.24})`;
          ctx.lineWidth = this.distanceMapMode ? 1.5 : 2;
          ctx.shadowColor = this.distanceMapMode ? `rgba(189, 173, 139, ${glowPulse * 0.2})` : `rgba(173, 186, 200, ${glowPulse * 0.25})`;
          ctx.shadowBlur = this.distanceMapMode ? 3 : 5;
          ctx.beginPath();
          ctx.moveTo(pt1.x, pt1.y);
          ctx.lineTo(pt2.x, pt2.y);
          ctx.stroke();

          // Pass 3: bright neon core line
          ctx.strokeStyle = this.distanceMapMode ? `rgba(222, 211, 187, ${basePulse + 0.15})` : `rgba(199, 208, 215, ${basePulse + 0.15})`;
          ctx.lineWidth = 1.0;
          ctx.shadowColor = this.distanceMapMode ? `rgba(222, 211, 187, ${glowPulse * 0.28})` : `rgba(199, 208, 215, ${glowPulse * 0.28})`;
          ctx.shadowBlur = 4;
          ctx.beginPath();
          ctx.moveTo(pt1.x, pt1.y);
          ctx.lineTo(pt2.x, pt2.y);
          ctx.stroke();

          ctx.shadowBlur = 0;
        }
      }
    }
  }

  renderStars() {
    const ctx = this.ctx;
    const t = Date.now() * 0.001;

    for (let idx = 0; idx < this.stars.length; idx++) {
      const star = this.stars[idx];
      const pt = this.project3D(this.renderPosition(star), 1);
      if (!pt || !pt.isVisible) continue;

      // Per-star twinkle factor
      const phase = (this._twinklePhases[idx] || 0);
      const twinkleFreq = 0.5 + (idx % 7) * 0.18;
      const twinkle = 0.5 + 0.5 * Math.sin(t * twinkleFreq + phase);

      const baseSize = Math.max(1.5, (4.5 - star.mag * 0.7));
      const size = baseSize * (0.8 + 0.35 * twinkle);
      const color = star.color || '#ffffff';

      // 1. Draw Proper Motion Drift Vector Trail
      if (this.showProperMotionVectors && star.drift_arcsec > 50) {
        const trailLength = Math.min(45, (star.drift_arcsec / 150.0));
        ctx.strokeStyle = `rgba(255, 209, 102, ${0.3 + 0.2 * twinkle})`;
        ctx.lineWidth = 1;
        ctx.setLineDash([2, 3]);
        ctx.beginPath();
        ctx.moveTo(pt.x, pt.y);
        ctx.lineTo(pt.x + trailLength * 0.8, pt.y - trailLength * 0.5);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // 2. Bright star — large outer glow halo
      if (star.mag < 2.5) {
        const haloSize = baseSize * (4 + 2 * twinkle);
        const gradient = ctx.createRadialGradient(pt.x, pt.y, 0, pt.x, pt.y, haloSize);
        gradient.addColorStop(0, `${color}`);
        gradient.addColorStop(0.2, 'rgba(190, 202, 213, 0.13)');
        gradient.addColorStop(0.6, 'rgba(140, 158, 180, 0.045)');
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, haloSize, 0, Math.PI * 2);
        ctx.fill();
      }

      // 3. Medium glow ring for all visible stars
      if (star.mag < 4.5) {
        const midGlow = baseSize * (2 + twinkle);
        const glowOpacity = Math.max(0.05, (1 - star.mag / 6) * 0.35 * twinkle);
        ctx.shadowColor = color;
        ctx.shadowBlur = 3 + 2 * twinkle;
        const midGrad = ctx.createRadialGradient(pt.x, pt.y, 0, pt.x, pt.y, midGlow);
        midGrad.addColorStop(0, color);
        midGrad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.globalAlpha = glowOpacity;
        ctx.fillStyle = midGrad;
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, midGlow, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.shadowBlur = 0;
      }

      // 4. Core star disc with neon glow shadow
      ctx.shadowColor = color;
      ctx.shadowBlur = 2 + 3 * twinkle;
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, size, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;

      // 5. Sparkle cross-spike for bright stars (diffraction spike effect)
      if (star.mag < 1.8 && twinkle > 0.6) {
        const spikeLen = size * (3 + 4 * twinkle);
        const spikeOpacity = (twinkle - 0.6) * 2;
        ctx.strokeStyle = `rgba(224, 215, 194, ${spikeOpacity * 0.45})`;
        ctx.lineWidth = 0.7;
        ctx.shadowColor = color;
        ctx.shadowBlur = 2;
        ctx.beginPath();
        // Horizontal spike
        ctx.moveTo(pt.x - spikeLen, pt.y);
        ctx.lineTo(pt.x + spikeLen, pt.y);
        // Vertical spike
        ctx.moveTo(pt.x, pt.y - spikeLen);
        ctx.lineTo(pt.x, pt.y + spikeLen);
        // Diagonal spikes
        ctx.moveTo(pt.x - spikeLen * 0.5, pt.y - spikeLen * 0.5);
        ctx.lineTo(pt.x + spikeLen * 0.5, pt.y + spikeLen * 0.5);
        ctx.moveTo(pt.x + spikeLen * 0.5, pt.y - spikeLen * 0.5);
        ctx.lineTo(pt.x - spikeLen * 0.5, pt.y + spikeLen * 0.5);
        ctx.stroke();
        ctx.shadowBlur = 0;
      }

      // 6. Star Name label (for major stars)
      if (star.mag < 2.2) {
        ctx.fillStyle = 'rgba(221, 224, 226, 0.82)';
        ctx.font = '11px sans-serif';
        ctx.shadowColor = 'rgba(203, 195, 176, 0.25)';
        ctx.shadowBlur = 2;
        ctx.fillText(star.name.split(' (')[0], pt.x + size + 5, pt.y + 4);
        ctx.shadowBlur = 0;
      }
    }
  }

  renderCurrentPoleMarker() {
    if (!this.poleTelemetry) return;
    const ctx = this.ctx;
    const pt = this.project3D(this.poleTelemetry.cartesian_pole, 1);
    if (!pt || !pt.isVisible) return;

    // Glowing neon reticle around the true North Celestial Pole
    const time = Date.now() * 0.003;
    const radius = 10 + Math.sin(time) * 2.5;
    const glowPulse = 0.6 + 0.4 * Math.sin(time * 1.3);

    // Outer glow ring
    ctx.strokeStyle = `rgba(193, 152, 144, ${glowPulse * 0.25})`;
    ctx.lineWidth = 4;
    ctx.shadowColor = '#c19a92';
    ctx.shadowBlur = 7;
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, radius + 4, 0, Math.PI * 2);
    ctx.stroke();

    // Inner neon ring
    ctx.strokeStyle = `rgba(207, 171, 158, ${glowPulse * 0.78})`;
    ctx.lineWidth = 1.5;
    ctx.shadowBlur = 12;
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, radius, 0, Math.PI * 2);
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Crosshairs
    ctx.strokeStyle = `rgba(207, 171, 158, ${glowPulse * 0.64})`;
    ctx.lineWidth = 1;
    ctx.shadowColor = '#ff4757';
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.moveTo(pt.x - radius - 6, pt.y);
    ctx.lineTo(pt.x + radius + 6, pt.y);
    ctx.moveTo(pt.x, pt.y - radius - 6);
    ctx.lineTo(pt.x, pt.y + radius + 6);
    ctx.stroke();
    ctx.shadowBlur = 0;

    ctx.fillStyle = '#cda99a';
    ctx.shadowColor = '#cda99a';
    ctx.shadowBlur = 3;
    ctx.font = 'bold 11px monospace';
    ctx.fillText(`NCP (${Math.round(this.currentYear)} CE)`, pt.x + radius + 10, pt.y + 4);
    ctx.shadowBlur = 0;
  }

  renderTooltip(hover) {
    const ctx = this.ctx;
    const star = hover.star;
    const x = hover.screenX + 12;
    const y = hover.screenY - 12;

    const lines = [
      `★ ${star.name}`,
      `Constellation: ${star.constellation}`,
      `Visual Mag: ${star.mag} | Type: ${star.spect}`,
      `Distance: ${star.dist_ly} light years`,
      `Distance: ${Number(star.distance_au || 0).toLocaleString()} AU`,
      `Proper Motion Drift: ${star.drift_arcsec.toFixed(1)}" (arcsec)`
    ];

    ctx.font = '11px monospace';
    const width = 240;
    const height = lines.length * 16 + 16;

    // Void terminal tooltip background
    ctx.fillStyle = 'rgba(0, 0, 4, 0.95)';
    ctx.strokeStyle = 'rgba(203, 190, 161, 0.5)';
    ctx.lineWidth = 1;
    ctx.shadowColor = 'rgba(203, 190, 161, 0.2)';
    ctx.shadowBlur = 5;
    ctx.beginPath();
    ctx.roundRect(x, y - height, width, height, 8);
    ctx.fill();
    ctx.stroke();
    ctx.shadowBlur = 0;

    lines.forEach((line, i) => {
      if (i === 0) {
        ctx.fillStyle = '#d5bd8c';
        ctx.shadowColor = 'rgba(213, 189, 140, 0.25)';
        ctx.shadowBlur = 2;
      } else {
        ctx.fillStyle = '#d4d8df';
        ctx.shadowBlur = 0;
      }
      ctx.fillText(line, x + 10, y - height + 20 + i * 16);
    });
    ctx.shadowBlur = 0;
  }
}

window.PlanetariumView = PlanetariumView;
