"""Animated 3D hero visual for the top of the main page.

Pure decoration, rendered client-side via Three.js (loaded from a CDN
directly in the user's browser through the iframe that
st.components.v1.html creates) — no data, fabricated or otherwise, is
shown here, and this never touches core/analyzer.py or the fetch path.
"""

from theme import COLORS

_HERO_TEMPLATE = """
<div id="hero3d-wrap" style="position:relative;width:100%;height:{height}px;border-radius:24px;overflow:hidden;
     background:radial-gradient(ellipse 90% 70% at 50% 20%, rgba(109,94,248,0.14), rgba(5,7,13,0) 70%);">
  <canvas id="hero3d-canvas" style="display:block;width:100%;height:100%;"></canvas>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function() {{
  const wrap = document.getElementById('hero3d-wrap');
  const canvas = document.getElementById('hero3d-canvas');
  if (!window.THREE || !wrap || !canvas) return;

  const COLOR_ACCENT_1 = {accent_1};
  const COLOR_ACCENT_2 = {accent_2};
  const COLOR_ACCENT_3 = {accent_3};
  const COLOR_UP = {up};

  let width = wrap.clientWidth || 800;
  let height = wrap.clientHeight || {height};

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(52, width / height, 0.1, 100);
  camera.position.set(0, 0.4, 9);

  const renderer = new THREE.WebGLRenderer({{ canvas: canvas, alpha: true, antialias: true }});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(width, height, false);

  const group = new THREE.Group();
  scene.add(group);

  // Core glowing wireframe icosahedron — the "data crystal"
  const coreGeo = new THREE.IcosahedronGeometry(2.35, 1);
  const coreWire = new THREE.LineSegments(
    new THREE.EdgesGeometry(coreGeo),
    new THREE.LineBasicMaterial({{ color: COLOR_ACCENT_1, transparent: true, opacity: 0.85 }})
  );
  group.add(coreWire);

  const coreFill = new THREE.Mesh(
    coreGeo,
    new THREE.MeshBasicMaterial({{ color: COLOR_ACCENT_1, transparent: true, opacity: 0.05, side: THREE.DoubleSide }})
  );
  group.add(coreFill);

  const innerGeo = new THREE.IcosahedronGeometry(1.15, 0);
  const innerWire = new THREE.LineSegments(
    new THREE.EdgesGeometry(innerGeo),
    new THREE.LineBasicMaterial({{ color: COLOR_ACCENT_3, transparent: true, opacity: 0.55 }})
  );
  group.add(innerWire);

  // Orbiting rings — "capital flow"
  const ringColors = [COLOR_ACCENT_3, COLOR_ACCENT_2, COLOR_UP];
  const rings = [];
  for (let i = 0; i < 3; i++) {{
    const ringGeo = new THREE.TorusGeometry(3.1 + i * 0.42, 0.006, 8, 96);
    const ringMat = new THREE.MeshBasicMaterial({{ color: ringColors[i], transparent: true, opacity: 0.4 - i * 0.08 }});
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2.4 + i * 0.35;
    ring.rotation.y = i * 0.6;
    scene.add(ring);
    rings.push(ring);
  }}

  // Particle field — "market data points"
  const PARTICLE_COUNT = 260;
  const positions = new Float32Array(PARTICLE_COUNT * 3);
  const seeds = new Float32Array(PARTICLE_COUNT);
  for (let i = 0; i < PARTICLE_COUNT; i++) {{
    const r = 3.6 + Math.random() * 2.6;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos((Math.random() * 2) - 1);
    positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta) * 0.6;
    positions[i * 3 + 2] = r * Math.cos(phi);
    seeds[i] = Math.random() * Math.PI * 2;
  }}
  const particleGeo = new THREE.BufferGeometry();
  particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const particleMat = new THREE.PointsMaterial({{
    color: COLOR_ACCENT_3, size: 0.045, transparent: true, opacity: 0.75,
    blending: THREE.AdditiveBlending, depthWrite: false,
  }});
  const particles = new THREE.Points(particleGeo, particleMat);
  scene.add(particles);

  // Gentle mouse parallax
  let targetRotX = 0, targetRotY = 0;
  wrap.addEventListener('mousemove', function(e) {{
    const rect = wrap.getBoundingClientRect();
    const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const ny = ((e.clientY - rect.top) / rect.height) * 2 - 1;
    targetRotY = nx * 0.35;
    targetRotX = ny * 0.2;
  }});

  let raf = null;
  let running = true;
  const clock = new THREE.Clock();

  function animate() {{
    if (!running) return;
    raf = requestAnimationFrame(animate);
    const t = clock.getElapsedTime();

    group.rotation.y += 0.0032;
    group.rotation.x += (targetRotX - group.rotation.x) * 0.02 + 0.0006;
    group.rotation.y += (targetRotY * 0.15);

    rings.forEach(function(ring, i) {{
      ring.rotation.z += 0.0016 * (i % 2 === 0 ? 1 : -1);
    }});

    particles.rotation.y -= 0.0011;
    particleMat.opacity = 0.55 + Math.sin(t * 0.6) * 0.2;

    const pulse = 1 + Math.sin(t * 1.1) * 0.02;
    coreWire.scale.set(pulse, pulse, pulse);

    renderer.render(scene, camera);
  }}
  animate();

  function handleResize() {{
    width = wrap.clientWidth || width;
    height = wrap.clientHeight || height;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
  }}
  window.addEventListener('resize', handleResize);
  if (window.ResizeObserver) {{
    new ResizeObserver(handleResize).observe(wrap);
  }}

  window.addEventListener('beforeunload', function() {{
    running = false;
    if (raf) cancelAnimationFrame(raf);
    renderer.dispose();
  }});
}})();
</script>
"""


def get_hero_html(height: int = 300) -> str:
    """Returns a self-contained HTML/JS snippet (Three.js) for use with
    st.components.v1.html(get_hero_html(), height=..., scrolling=False)."""
    return _HERO_TEMPLATE.format(
        height=height,
        accent_1=repr(COLORS["accent_1"]),
        accent_2=repr(COLORS["accent_2"]),
        accent_3=repr(COLORS["accent_3"]),
        up=repr(COLORS["up"]),
    )