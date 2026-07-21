"""Animated 3D hero visual — rotating Earth with orbiting data rings."""

from theme import COLORS

_HERO_TEMPLATE = """
<div id="hero3d-wrap" style="position:relative;width:100%;height:{height}px;border-radius:24px;overflow:hidden;
     background:radial-gradient(ellipse 90% 70% at 50% 30%, rgba(30,60,120,0.25), rgba(5,7,13,0) 75%);">
  <canvas id="hero3d-canvas" style="display:block;width:100%;height:100%;"></canvas>
  <div style="position:absolute;bottom:16px;left:50%;transform:translateX(-50%);
       font-family:'Manrope','Inter',sans-serif;font-size:0.7rem;font-weight:700;
       color:rgba(255,255,255,0.22);letter-spacing:2.5px;pointer-events:none;">
    GLOBAL MARKET INTELLIGENCE
  </div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
(function() {{
  const wrap = document.getElementById('hero3d-wrap');
  const canvas = document.getElementById('hero3d-canvas');
  if (!window.THREE || !wrap || !canvas) return;

  const COLOR_ACCENT_1 = {accent_1};
  const COLOR_ACCENT_3 = {accent_3};
  const COLOR_UP = {up};

  let width = wrap.clientWidth || 800;
  let height = wrap.clientHeight || {height};

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
  camera.position.set(0, 0.2, 8.5);

  const renderer = new THREE.WebGLRenderer({{ canvas: canvas, alpha: true, antialias: true }});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(width, height, false);

  // ── EARTH ──
  const earthGroup = new THREE.Group();
  scene.add(earthGroup);

  // Earth texture from NASA Blue Marble (free, no API key)
  const textureLoader = new THREE.TextureLoader();
  const earthGeo = new THREE.SphereGeometry(2.2, 64, 64);
  const earthMat = new THREE.MeshPhongMaterial({{
    map: textureLoader.load('https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg'),
    specular: new THREE.Color('grey'),
    shininess: 5,
  }});
  const earth = new THREE.Mesh(earthGeo, earthMat);
  earthGroup.add(earth);

  // Atmosphere glow
  const atmosGeo = new THREE.SphereGeometry(2.28, 64, 64);
  const atmosMat = new THREE.MeshBasicMaterial({{
    color: 0x4fc3f7,
    transparent: true,
    opacity: 0.08,
    side: THREE.FrontSide,
  }});
  const atmosphere = new THREE.Mesh(atmosGeo, atmosMat);
  earthGroup.add(atmosphere);

  // Outer glow ring
  const glowRingGeo = new THREE.TorusGeometry(2.35, 0.015, 16, 100);
  const glowRingMat = new THREE.MeshBasicMaterial({{ color: COLOR_ACCENT_3, transparent: true, opacity: 0.35 }});
  const glowRing = new THREE.Mesh(glowRingGeo, glowRingMat);
  glowRing.rotation.x = Math.PI / 2;
  earthGroup.add(glowRing);

  // ── LIGHTING ──
  const ambientLight = new THREE.AmbientLight(0x333366, 0.6);
  scene.add(ambientLight);
  const sunLight = new THREE.DirectionalLight(0xffffff, 1.2);
  sunLight.position.set(5, 3, 7);
  scene.add(sunLight);
  const fillLight = new THREE.DirectionalLight(0x4466aa, 0.4);
  fillLight.position.set(-3, -1, -2);
  scene.add(fillLight);

  // ── ORBITING DATA RINGS ──
  const ringData = [
    {{ radius: 3.0, color: COLOR_ACCENT_3, opacity: 0.4, tilt: 0.3, speed: 0.6 }},
    {{ radius: 3.5, color: 0x6d5ef8, opacity: 0.3, tilt: -0.5, speed: -0.4 }},
    {{ radius: 4.0, color: COLOR_UP, opacity: 0.25, tilt: 0.7, speed: 0.3 }},
  ];
  const rings = [];
  ringData.forEach(function(d) {{
    const ringGeo = new THREE.TorusGeometry(d.radius, 0.004, 8, 140);
    const ringMat = new THREE.MeshBasicMaterial({{ color: d.color, transparent: true, opacity: d.opacity }});
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2 + d.tilt;
    scene.add(ring);
    rings.push({{ mesh: ring, speed: d.speed, tilt: d.tilt }});
  }});

  // ── SATELLITE DOTS ──
  const satellites = [];
  for (let i = 0; i < 8; i++) {{
    const dotGeo = new THREE.SphereGeometry(0.04, 6, 6);
    const dotMat = new THREE.MeshBasicMaterial({{ color: i < 4 ? COLOR_ACCENT_3 : COLOR_UP, transparent: true, opacity: 0.85 }});
    const dot = new THREE.Mesh(dotGeo, dotMat);
    dot.userData = {{
      radius: 2.5 + Math.random() * 2.2,
      speed: 0.4 + Math.random() * 0.9,
      offset: Math.random() * Math.PI * 2,
      tilt: (Math.random() - 0.5) * 1.2,
      yOffset: (Math.random() - 0.5) * 1.5,
    }};
    scene.add(dot);
    satellites.push(dot);
  }}

  // ── STARFIELD ──
  const STAR_COUNT = 300;
  const starPositions = new Float32Array(STAR_COUNT * 3);
  for (let i = 0; i < STAR_COUNT; i++) {{
    starPositions[i * 3] = (Math.random() - 0.5) * 18;
    starPositions[i * 3 + 1] = (Math.random() - 0.5) * 12;
    starPositions[i * 3 + 2] = (Math.random() - 0.5) * 10 - 3;
  }}
  const starGeo = new THREE.BufferGeometry();
  starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
  const starMat = new THREE.PointsMaterial({{
    color: 0xffffff, size: 0.03, transparent: true, opacity: 0.6,
    blending: THREE.AdditiveBlending, depthWrite: false,
  }});
  const stars = new THREE.Points(starGeo, starMat);
  scene.add(stars);

  // ── MOUSE / TOUCH CONTROL ──
  let targetRotX = 0, targetRotY = 0;
  let currentRotX = 0, currentRotY = 0;
  let isDragging = false;

  wrap.addEventListener('mousemove', function(e) {{
    const rect = wrap.getBoundingClientRect();
    const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const ny = ((e.clientY - rect.top) / rect.height) * 2 - 1;
    targetRotY = nx * 1.2;
    targetRotX = ny * 0.7;
  }});

  wrap.addEventListener('touchmove', function(e) {{
    const rect = wrap.getBoundingClientRect();
    const nx = ((e.touches[0].clientX - rect.left) / rect.width) * 2 - 1;
    const ny = ((e.touches[0].clientY - rect.top) / rect.height) * 2 - 1;
    targetRotY = nx * 1.2;
    targetRotX = ny * 0.7;
  }}, {{ passive: true }});

  // ── ANIMATION LOOP ──
  let raf = null, running = true;
  const clock = new THREE.Clock();

  function animate() {{
    if (!running) return;
    raf = requestAnimationFrame(animate);
    const t = clock.getElapsedTime();

    // Smooth mouse follow
    currentRotX += (targetRotX - currentRotX) * 0.025;
    currentRotY += (targetRotY - currentRotY) * 0.025;

    // Earth auto-rotation + mouse influence
    earthGroup.rotation.y += 0.003;
    earthGroup.rotation.x = currentRotX * 0.4;
    earthGroup.rotation.z = currentRotY * 0.25;

    // Atmosphere pulse
    atmosMat.opacity = 0.06 + Math.sin(t * 0.5) * 0.03;

    // Rings
    rings.forEach(function(r) {{
      r.mesh.rotation.z += 0.001 * r.speed;
    }});

    // Satellites orbit
    satellites.forEach(function(s) {{
      const angle = t * s.userData.speed + s.userData.offset;
      const r = s.userData.radius;
      s.position.x = Math.cos(angle) * r;
      s.position.z = Math.sin(angle) * r;
      s.position.y = Math.sin(angle * 0.7) * s.userData.yOffset;
    }});

    // Stars slow drift
    stars.rotation.y += 0.0002;
    stars.rotation.x += 0.0001;

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
    return _HERO_TEMPLATE.format(
        height=height,
        accent_1=repr(COLORS["accent_1"]),
        accent_2=repr(COLORS["accent_2"]),
        accent_3=repr(COLORS["accent_3"]),
        up=repr(COLORS["up"]),
    )