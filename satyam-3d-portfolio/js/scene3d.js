(function initHero3DScene() {
    const canvas = document.getElementById('hero-3d-canvas');
    if (!canvas || typeof THREE === 'undefined') return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 6.5;

    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Core Metallic Torus Knot
    const geometry = new THREE.TorusKnotGeometry(1.35, 0.38, 180, 28, 2, 3);
    const material = new THREE.MeshStandardMaterial({
        color: 0x1a0500,
        emissive: 0xff2a00,
        emissiveIntensity: 0.32,
        roughness: 0.2,
        metalness: 0.88
    });
    const torusKnot = new THREE.Mesh(geometry, material);
    scene.add(torusKnot);

    // Outer Wireframe Geodesic Cage
    const wireGeo = new THREE.IcosahedronGeometry(2.4, 2);
    const wireMat = new THREE.MeshBasicMaterial({
        color: 0xff6b00,
        wireframe: true,
        transparent: true,
        opacity: 0.15
    });
    const wireShell = new THREE.Mesh(wireGeo, wireMat);
    scene.add(wireShell);

    const light1 = new THREE.PointLight(0xff2a00, 4.8, 20);
    light1.position.set(3, 2, 4);
    scene.add(light1);

    const light2 = new THREE.PointLight(0xff8800, 3.4, 20);
    light2.position.set(-3, -2, 3);
    scene.add(light2);

    let mouseX = 0, mouseY = 0;
    let scrollProgress = 0;

    window.addEventListener('mousemove', (e) => {
        mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
        mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    });

    window.addEventListener('scroll', () => {
        scrollProgress = window.scrollY / window.innerHeight;
    }, { passive: true });

    function animate() {
        requestAnimationFrame(animate);

        // Combine idle rotation + mouse tilt + fluid scroll spin
        torusKnot.rotation.y += 0.004 + mouseX * 0.01;
        torusKnot.rotation.x += 0.002 + mouseY * 0.01;
        torusKnot.position.y = scrollProgress * -1.4;
        torusKnot.scale.setScalar(Math.max(0.5, 1 - scrollProgress * 0.35));

        wireShell.rotation.y = -scrollProgress * 1.8 - performance.now() * 0.0002;
        wireShell.rotation.z = scrollProgress * 1.2;

        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
})();