/**
 * AstraTrack AI - Orbital Trajectory & Satellite Sentinel 3D Engine
 * Renders Keplerian orbits, comet comas/tails, asteroid flybys,
 * and satellite sensor tracking telemetry in interactive 3D heliocentric space.
 */

class OrbitalSentinelView {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    // Camera parameters for 3D orbital space
    this.yaw = 0.5;
    this.pitch = 0.75;
    this.zoom = 1.0;
    this.isDragging = false;
    this.lastMouse = { x: 0, y: 0 };

    // Datasets
    this.trajectoriesData = null;
    this.selectedTargetId = 'apophis';
    this.animationPhase = 0;

    this.setupInteraction();
  }

  setupInteraction() {
    this.canvas.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.lastMouse = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('mouseup', () => {
      this.isDragging = false;
    });

    this.canvas.addEventListener('mousemove', (e) => {
      if (this.isDragging) {
        const dx = e.clientX - this.lastMouse.x;
        const dy = e.clientY - this.lastMouse.y;
        this.yaw += dx * 0.006;
        this.pitch = Math.max(0.1, Math.min(1.45, this.pitch + dy * 0.006));
        this.lastMouse = { x: e.clientX, y: e.clientY };
      }
    });

    this.canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      const factor = e.deltaY > 0 ? 0.9 : 1.1;
      this.zoom = Math.max(0.3, Math.min(6.0, this.zoom * factor));
    });
  }

  setData(trajectories) {
    this.trajectoriesData = trajectories;
  }

  selectTarget(targetId) {
    this.selectedTargetId = targetId;
  }

  project3D(x, y, z) {
    // Rotation around Z (yaw)
    const cosY = Math.cos(this.yaw);
    const sinY = Math.sin(this.yaw);
    const x1 = x * cosY - y * sinY;
    const y1 = x * sinY + y * cosY;
    const z1 = z;

    // Tilt via Pitch (around X axis)
    const cosP = Math.cos(this.pitch);
    const sinP = Math.sin(this.pitch);
    const x2 = x1;
    const y2 = y1 * cosP - z1 * sinP;
    const z2 = y1 * sinP + z1 * cosP;

    const cx = this.canvas.width / 2;
    const cy = this.canvas.height / 2;
    const baseScale = Math.min(cx, cy) * 0.55 * this.zoom;

    // Standard perspective depth
    const dist = 6.0;
    const depth = z2 + dist;
    if (depth <= 0.1) return null;

    const screenX = cx + (x2 / depth) * baseScale * 4.0;
    const screenY = cy - (y2 / depth) * baseScale * 4.0;

    return { x: screenX, y: screenY, depth: z2 };
  }

  render() {
    const w = this.canvas.width;
    const h = this.canvas.height;
    const ctx = this.ctx;

    ctx.clearRect(0, 0, w, h);
    this.animationPhase += 0.03;

    if (!this.trajectoriesData) return;

    // 1. Draw Heliocentric grid planes & distance rings (AU circles)
    this.renderDistanceRings();

    // 2. Draw Central Sun
    this.renderSun();

    // 3. Draw Planetary orbits (Mercury, Venus, Earth, Mars)
    this.renderPlanetaryOrbits();

    // 4. Draw Astral Bodies (Asteroids & Comets) with full Keplerian orbits
    this.renderAstralBodies();

    // 5. Draw Tracking Satellites & Active Sensor Cones
    this.renderSatelliteSentinels();
  }

  renderDistanceRings() {
    const ctx = this.ctx;
    const radii = [0.5, 1.0, 1.5, 2.5, 5.0]; // AU
    
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 4]);

    radii.forEach(r => {
      ctx.strokeStyle = r === 1.0 ? 'rgba(0, 243, 255, 0.35)' : 'rgba(255, 255, 255, 0.08)';
      ctx.beginPath();
      let started = false;
      for (let i = 0; i <= 64; i++) {
        const theta = (i / 64) * Math.PI * 2;
        const pt = this.project3D(r * Math.cos(theta), r * Math.sin(theta), 0);
        if (pt) {
          if (!started) { ctx.moveTo(pt.x, pt.y); started = true; }
          else { ctx.lineTo(pt.x, pt.y); }
        }
      }
      ctx.stroke();

      // Label AU radius
      const labelPt = this.project3D(r, 0, 0);
      if (labelPt) {
        ctx.fillStyle = 'rgba(148, 163, 184, 0.5)';
        ctx.font = '10px monospace';
        ctx.fillText(`${r} AU`, labelPt.x + 4, labelPt.y - 4);
      }
    });

    ctx.setLineDash([]);
  }

  renderSun() {
    const ctx = this.ctx;
    const sunPt = this.project3D(0, 0, 0);
    if (!sunPt) return;

    // Solar flare glow
    const pulse = 14 + Math.sin(this.animationPhase * 2) * 2;
    const grad = ctx.createRadialGradient(sunPt.x, sunPt.y, 2, sunPt.x, sunPt.y, pulse * 2.5);
    grad.addColorStop(0, '#ffffff');
    grad.addColorStop(0.3, '#ffd166');
    grad.addColorStop(0.7, 'rgba(255, 159, 67, 0.3)');
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(sunPt.x, sunPt.y, pulse * 2.5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(sunPt.x, sunPt.y, 6, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#ffd166';
    ctx.font = 'bold 11px monospace';
    ctx.fillText('SOL (Sun)', sunPt.x + 12, sunPt.y + 4);
  }

  renderPlanetaryOrbits() {
    const ctx = this.ctx;
    const earthPos = this.trajectoriesData.earth_position || { x: 1, y: 0, z: 0 };
    const earthPt = this.project3D(earthPos.x, earthPos.y, earthPos.z);

    if (earthPt) {
      // Earth glow & indicator
      ctx.fillStyle = '#00d2d3';
      ctx.shadowColor = '#00f3ff';
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.arc(earthPt.x, earthPt.y, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;

      ctx.fillStyle = '#00f3ff';
      ctx.font = 'bold 11px monospace';
      ctx.fillText('EARTH', earthPt.x + 8, earthPt.y + 3);

      // Moon distance boundary (1 LD indicator ring)
      ctx.strokeStyle = 'rgba(0, 243, 255, 0.25)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(earthPt.x, earthPt.y, 14, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  renderAstralBodies() {
    const ctx = this.ctx;
    const bodies = this.trajectoriesData.tracked_bodies || [];

    for (const body of bodies) {
      const isSelected = body.id === this.selectedTargetId;

      // 1. Draw Orbit Trajectory Path
      if (body.orbit_path && body.orbit_path.length > 0) {
        ctx.strokeStyle = isSelected ? body.color : 'rgba(255, 255, 255, 0.15)';
        ctx.lineWidth = isSelected ? 2.0 : 1.0;
        ctx.beginPath();
        let started = false;
        for (const pt3 of body.orbit_path) {
          const pt = this.project3D(pt3.x, pt3.y, pt3.z);
          if (pt) {
            if (!started) { ctx.moveTo(pt.x, pt.y); started = true; }
            else { ctx.lineTo(pt.x, pt.y); }
          }
        }
        ctx.stroke();
      }

      // 2. Draw Body Location
      const pos = body.position;
      const pt = this.project3D(pos.x, pos.y, pos.z);
      if (!pt) continue;

      // Draw Comet Ion Tail if it's a comet
      if (body.type.includes('Comet')) {
        // Ion tail points radially away from the Sun (0, 0, 0)
        const tailVecX = pos.x * 0.35;
        const tailVecY = pos.y * 0.35;
        const tailVecZ = pos.z * 0.35;
        const tailPt = this.project3D(pos.x + tailVecX, pos.y + tailVecY, pos.z + tailVecZ);

        if (tailPt) {
          const tailGrad = ctx.createLinearGradient(pt.x, pt.y, tailPt.x, tailPt.y);
          tailGrad.addColorStop(0, 'rgba(112, 161, 255, 0.8)');
          tailGrad.addColorStop(1, 'rgba(0, 243, 255, 0)');
          ctx.strokeStyle = tailGrad;
          ctx.lineWidth = 3;
          ctx.beginPath();
          ctx.moveTo(pt.x, pt.y);
          ctx.lineTo(tailPt.x, tailPt.y);
          ctx.stroke();
        }
      }

      // Draw body node
      ctx.fillStyle = body.color || '#ff4757';
      ctx.beginPath();
      const radius = isSelected ? 5 : 3.5;
      ctx.arc(pt.x, pt.y, radius, 0, Math.PI * 2);
      ctx.fill();

      // Selected Reticle
      if (isSelected) {
        ctx.strokeStyle = body.color;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 11 + Math.sin(this.animationPhase * 3) * 2, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Label
      ctx.fillStyle = isSelected ? '#ffffff' : 'rgba(226, 232, 240, 0.7)';
      ctx.font = isSelected ? 'bold 11px monospace' : '10px monospace';
      ctx.fillText(body.name, pt.x + 8, pt.y + 3);
    }
  }

  renderSatelliteSentinels() {
    const ctx = this.ctx;
    const earthPos = this.trajectoriesData.earth_position || { x: 1, y: 0, z: 0 };
    const earthPt = this.project3D(earthPos.x, earthPos.y, earthPos.z);
    if (!earthPt) return;

    const satellites = this.trajectoriesData.satellite_fleet || [];
    const bodies = this.trajectoriesData.tracked_bodies || [];
    const selectedBody = bodies.find(b => b.id === this.selectedTargetId) || bodies[0];

    // Find screen coordinate of selected body
    let targetPt = null;
    if (selectedBody) {
      targetPt = this.project3D(selectedBody.position.x, selectedBody.position.y, selectedBody.position.z);
    }

    satellites.forEach((sat, index) => {
      // Offset satellite slightly from Earth for visualization
      const satAngle = this.animationPhase + (index * Math.PI * 2) / satellites.length;
      const satDist = 0.05 + index * 0.02; // Visual scale around Earth
      const satPos = {
        x: earthPos.x + Math.cos(satAngle) * satDist,
        y: earthPos.y + Math.sin(satAngle) * satDist,
        z: 0.01 * (index - 1)
      };

      const satPt = this.project3D(satPos.x, satPos.y, satPos.z);
      if (!satPt) return;

      // Draw Satellite Node
      ctx.fillStyle = sat.color;
      ctx.fillRect(satPt.x - 3, satPt.y - 3, 6, 6);

      // Label
      ctx.fillStyle = sat.color;
      ctx.font = '9px monospace';
      ctx.fillText(`🛰️ ${sat.name.split(' ')[0]}`, satPt.x + 6, satPt.y + 2);

      // Draw Laser Sensor Tracking Beam to Selected Target
      if (targetPt && (sat.id === 'neowise_sat' || sat.id === 'jwst')) {
        ctx.strokeStyle = sat.color;
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(satPt.x, satPt.y);
        ctx.lineTo(targetPt.x, targetPt.y);
        ctx.stroke();
        ctx.setLineDash([]);

        // Animated telemetry pulse packet traveling along beam
        const pulseRatio = (this.animationPhase * 1.5) % 1.0;
        const pulseX = satPt.x + (targetPt.x - satPt.x) * pulseRatio;
        const pulseY = satPt.y + (targetPt.y - satPt.y) * pulseRatio;
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(pulseX, pulseY, 2, 0, Math.PI * 2);
        ctx.fill();
      }
    });
  }
}

window.OrbitalSentinelView = OrbitalSentinelView;
