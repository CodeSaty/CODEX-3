(function initHero3DScene() {
    const canvas = document.getElementById('hero-3d-canvas');
    const preloader = document.getElementById('hero-preloader');

    function dismissPreloader() {
        if (canvas) {
            canvas.classList.add('scene-ready');
        }
        if (preloader) {
            preloader.classList.add('loaded');
        }
    }

    if (!canvas || typeof THREE === 'undefined') {
        dismissPreloader();
        return;
    }

    let renderer;
    try {
        renderer = new THREE.WebGLRenderer({
            canvas,
            alpha: true,
            antialias: true,
            powerPreference: 'high-performance'
        });
    } catch (_err) {
        dismissPreloader();
        return;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 7.2;

    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    // Procedural radial glow texture for neural halos & firing synaptic pulses
    function createGlowTexture() {
        const size = 64;
        const glowCanvas = document.createElement('canvas');
        glowCanvas.width = size;
        glowCanvas.height = size;
        const ctx = glowCanvas.getContext('2d');
        const gradient = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
        gradient.addColorStop(0, 'rgba(255, 245, 220, 1)');
        gradient.addColorStop(0.28, 'rgba(255, 130, 20, 0.85)');
        gradient.addColorStop(0.65, 'rgba(255, 42, 0, 0.25)');
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, size, size);
        return new THREE.CanvasTexture(glowCanvas);
    }

    const glowTexture = createGlowTexture();

    // Root 3D Neural Network Group
    const neuralGroup = new THREE.Group();
    scene.add(neuralGroup);

    // 1. GENERATE NEURON NODES (SOMAS) IN A CORTICAL 3D CONSTELLATION
    const NODE_COUNT = 54;
    const CONNECT_DISTANCE = 2.15;
    const nodes = [];

    const coreSomaGeo = new THREE.SphereGeometry(0.11, 20, 20);
    const hubSomaGeo = new THREE.SphereGeometry(0.16, 24, 24);

    const spriteMaterialBase = new THREE.SpriteMaterial({
        map: glowTexture,
        color: 0xff6b00,
        transparent: true,
        opacity: 0.55,
        blending: THREE.AdditiveBlending,
        depthWrite: false
    });

    for (let i = 0; i < NODE_COUNT; i++) {
        const isHub = i < 10;
        // Distribute across a bilobed / organic neural volume
        const u = Math.random();
        const v = Math.random();
        const theta = u * 2.0 * Math.PI;
        const phi = Math.acos(2.0 * v - 1.0);
        const radius = isHub
            ? 0.8 + Math.random() * 1.4
            : 1.3 + Math.cbrt(Math.random()) * 2.1;

        const basePos = new THREE.Vector3(
            radius * Math.sin(phi) * Math.cos(theta) * 1.25,
            radius * Math.sin(phi) * Math.sin(theta) * 0.92,
            radius * Math.cos(phi) * 0.85
        );

        const material = new THREE.MeshStandardMaterial({
            color: isHub ? 0xff8800 : 0x3a0900,
            emissive: isHub ? 0xff5500 : 0xff2a00,
            emissiveIntensity: isHub ? 0.85 : 0.42,
            roughness: 0.22,
            metalness: 0.75
        });

        const mesh = new THREE.Mesh(isHub ? hubSomaGeo : coreSomaGeo, material);
        mesh.position.copy(basePos);

        // Add bioluminescent soma halo sprite
        const halo = new THREE.Sprite(spriteMaterialBase.clone());
        const baseHaloScale = isHub ? 0.85 : 0.52;
        halo.scale.set(baseHaloScale, baseHaloScale, 1);
        mesh.add(halo);

        neuralGroup.add(mesh);

        nodes.push({
            index: i,
            isHub,
            mesh,
            halo,
            baseHaloScale,
            basePos,
            phase: Math.random() * Math.PI * 2,
            speed: 0.6 + Math.random() * 0.9,
            excitation: isHub ? 0.35 : 0,
            neighbors: []
        });
    }

    // 2. BUILD AXON SYNAPTIC CONNECTIONS (LINESEGMENTS WITH DYNAMIC VERTEX COLORS)
    const connections = [];
    for (let i = 0; i < NODE_COUNT; i++) {
        for (let j = i + 1; j < NODE_COUNT; j++) {
            const dist = nodes[i].basePos.distanceTo(nodes[j].basePos);
            if (dist < CONNECT_DISTANCE) {
                connections.push({ a: i, b: j, dist });
                nodes[i].neighbors.push(j);
                nodes[j].neighbors.push(i);
            }
        }
    }

    const linePositions = new Float32Array(connections.length * 6);
    const lineColors = new Float32Array(connections.length * 6);
    const axonGeometry = new THREE.BufferGeometry();
    axonGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    axonGeometry.setAttribute('color', new THREE.BufferAttribute(lineColors, 3));

    const axonMaterial = new THREE.LineBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 0.68,
        blending: THREE.AdditiveBlending,
        depthWrite: false
    });

    const axonLines = new THREE.LineSegments(axonGeometry, axonMaterial);
    neuralGroup.add(axonLines);

    // 3. FIRING SYNAPTIC PULSES (ACTION POTENTIALS TRAVELING ALONG AXONS)
    const PULSE_COUNT = 42;
    const pulses = [];
    const pulsePositions = new Float32Array(PULSE_COUNT * 3);
    const pulseColors = new Float32Array(PULSE_COUNT * 3);

    function spawnPulse(pulseObj, forcedSourceIdx) {
        let startIdx = typeof forcedSourceIdx === 'number'
            ? forcedSourceIdx
            : Math.floor(Math.random() * NODE_COUNT);

        if (nodes[startIdx].neighbors.length === 0) {
            startIdx = 0;
        }
        const neighbors = nodes[startIdx].neighbors;
        const endIdx = neighbors[Math.floor(Math.random() * neighbors.length)] || 0;

        pulseObj.from = startIdx;
        pulseObj.to = endIdx;
        pulseObj.t = 0;
        pulseObj.speed = 0.012 + Math.random() * 0.018;
    }

    for (let i = 0; i < PULSE_COUNT; i++) {
        const pulse = { from: 0, to: 1, t: Math.random(), speed: 0.015 };
        spawnPulse(pulse);
        pulse.t = Math.random();
        pulses.push(pulse);
    }

    const pulseGeometry = new THREE.BufferGeometry();
    pulseGeometry.setAttribute('position', new THREE.BufferAttribute(pulsePositions, 3));
    pulseGeometry.setAttribute('color', new THREE.BufferAttribute(pulseColors, 3));

    const pulseMaterial = new THREE.PointsMaterial({
        size: 0.34,
        map: glowTexture,
        vertexColors: true,
        transparent: true,
        opacity: 0.95,
        blending: THREE.AdditiveBlending,
        depthWrite: false
    });

    const pulsePoints = new THREE.Points(pulseGeometry, pulseMaterial);
    neuralGroup.add(pulsePoints);

    // 4. LIGHTING RIG
    const ambientLight = new THREE.AmbientLight(0x2a0800, 1.4);
    scene.add(ambientLight);

    const light1 = new THREE.PointLight(0xff2a00, 4.5, 22);
    light1.position.set(3.5, 2.5, 4.5);
    scene.add(light1);

    const light2 = new THREE.PointLight(0xff8800, 3.6, 22);
    light2.position.set(-3.5, -2.0, 3.5);
    scene.add(light2);

    // 5. POINTER & SCROLL STATE FOR PROXIMITY HIGHLIGHTING
    let pointerNDC = new THREE.Vector2(99, 99);
    let targetMouseX = 0;
    let targetMouseY = 0;
    let smoothMouseX = 0;
    let smoothMouseY = 0;
    let scrollProgress = 0;
    let pointerActive = false;

    const projectedVec = new THREE.Vector3();
    const tempVec = new THREE.Vector3();
    const baseColor = new THREE.Color(0x8c1d00);
    const activeColor = new THREE.Color(0xffb703);

    window.addEventListener('mousemove', (e) => {
        pointerActive = true;
        targetMouseX = (e.clientX / window.innerWidth - 0.5) * 2;
        targetMouseY = (e.clientY / window.innerHeight - 0.5) * 2;
        pointerNDC.set(
            (e.clientX / window.innerWidth) * 2 - 1,
            -(e.clientY / window.innerHeight) * 2 + 1
        );
    }, { passive: true });

    window.addEventListener('scroll', () => {
        scrollProgress = window.scrollY / window.innerHeight;
    }, { passive: true });

    // Pre-allocated temp color for line updates
    const cA = new THREE.Color();
    const cB = new THREE.Color();

    let firstFrameRendered = false;
    const clock = new THREE.Clock();

    function animate() {
        requestAnimationFrame(animate);

        const elapsed = clock.getElapsedTime();

        // Smoothly damp cursor coordinates
        smoothMouseX += (targetMouseX - smoothMouseX) * 0.06;
        smoothMouseY += (targetMouseY - smoothMouseY) * 0.06;

        // Rotate and position the neural constellation
        neuralGroup.rotation.y = elapsed * 0.14 + smoothMouseX * 0.38 - scrollProgress * 0.9;
        neuralGroup.rotation.x = Math.sin(elapsed * 0.25) * 0.08 + smoothMouseY * 0.26;
        neuralGroup.position.y = scrollProgress * -1.35;
        neuralGroup.scale.setScalar(Math.max(0.55, 1 - scrollProgress * 0.32));

        neuralGroup.updateMatrixWorld();

        // Update each neuron soma position, cursor proximity excitation & glow
        for (let i = 0; i < NODE_COUNT; i++) {
            const node = nodes[i];
            const wave = Math.sin(elapsed * node.speed + node.phase) * 0.065;
            node.mesh.position.set(
                node.basePos.x + wave,
                node.basePos.y + Math.cos(elapsed * node.speed + node.phase) * 0.065,
                node.basePos.z + wave * 0.5
            );

            // Check cursor proximity in screen-space NDC
            if (pointerActive) {
                projectedVec.copy(node.mesh.position).applyMatrix4(neuralGroup.matrixWorld).project(camera);
                const dx = projectedVec.x - pointerNDC.x;
                const dy = projectedVec.y - pointerNDC.y;
                const dist2D = Math.sqrt(dx * dx + dy * dy);

                if (dist2D < 0.34) {
                    const boost = (1 - dist2D / 0.34) * 0.95;
                    if (boost > node.excitation) {
                        node.excitation = boost;
                        // Occasionally fire a new synaptic signal from cursor-excited neurons
                        if (Math.random() < 0.08) {
                            const randomPulse = pulses[Math.floor(Math.random() * PULSE_COUNT)];
                            spawnPulse(randomPulse, i);
                            randomPulse.speed = 0.028;
                        }
                    }
                }
            }

            // Natural decay of excitation
            node.excitation = Math.max(node.isHub ? 0.25 : 0.04, node.excitation * 0.95);

            // Apply scale and emissive intensity based on excitation
            const scaleBoost = 1 + node.excitation * 0.65;
            node.mesh.scale.setScalar(scaleBoost);
            node.mesh.material.emissiveIntensity = (node.isHub ? 0.65 : 0.35) + node.excitation * 1.4;

            const haloScale = node.baseHaloScale * (1 + node.excitation * 0.9);
            node.halo.scale.set(haloScale, haloScale, 1);
            node.halo.material.opacity = 0.35 + node.excitation * 0.55;
        }

        // Update axon line segment positions & vertex colors
        const posAttr = axonGeometry.attributes.position;
        const colAttr = axonGeometry.attributes.color;

        for (let i = 0; i < connections.length; i++) {
            const conn = connections[i];
            const nA = nodes[conn.a];
            const nB = nodes[conn.b];

            const idx6 = i * 6;
            linePositions[idx6] = nA.mesh.position.x;
            linePositions[idx6 + 1] = nA.mesh.position.y;
            linePositions[idx6 + 2] = nA.mesh.position.z;

            linePositions[idx6 + 3] = nB.mesh.position.x;
            linePositions[idx6 + 4] = nB.mesh.position.y;
            linePositions[idx6 + 5] = nB.mesh.position.z;

            cA.copy(baseColor).lerp(activeColor, Math.min(1, nA.excitation));
            cB.copy(baseColor).lerp(activeColor, Math.min(1, nB.excitation));

            lineColors[idx6] = cA.r;
            lineColors[idx6 + 1] = cA.g;
            lineColors[idx6 + 2] = cA.b;

            lineColors[idx6 + 3] = cB.r;
            lineColors[idx6 + 4] = cB.g;
            lineColors[idx6 + 5] = cB.b;
        }
        posAttr.needsUpdate = true;
        colAttr.needsUpdate = true;

        // Update firing action-potential pulses along axons
        const pulsePosAttr = pulseGeometry.attributes.position;
        const pulseColAttr = pulseGeometry.attributes.color;

        for (let i = 0; i < PULSE_COUNT; i++) {
            const p = pulses[i];
            p.t += p.speed;
            if (p.t >= 1) {
                // Excite target neuron upon synaptic arrival and cascade to next neuron
                const targetNode = nodes[p.to];
                if (targetNode) {
                    targetNode.excitation = Math.min(1, targetNode.excitation + 0.55);
                }
                spawnPulse(p, p.to);
            }

            const fromNode = nodes[p.from];
            const toNode = nodes[p.to];
            tempVec.lerpVectors(fromNode.mesh.position, toNode.mesh.position, p.t);

            const idx3 = i * 3;
            pulsePositions[idx3] = tempVec.x;
            pulsePositions[idx3 + 1] = tempVec.y;
            pulsePositions[idx3 + 2] = tempVec.z;

            // Bright gold-orange spike at mid-axon
            const intensity = Math.sin(p.t * Math.PI);
            pulseColors[idx3] = 1.0;
            pulseColors[idx3 + 1] = 0.45 + intensity * 0.45;
            pulseColors[idx3 + 2] = 0.1 + intensity * 0.35;
        }
        pulsePosAttr.needsUpdate = true;
        pulseColAttr.needsUpdate = true;

        renderer.render(scene, camera);

        if (!firstFrameRendered) {
            firstFrameRendered = true;
            requestAnimationFrame(() => {
                setTimeout(dismissPreloader, 180);
            });
        }
    }

    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
})();