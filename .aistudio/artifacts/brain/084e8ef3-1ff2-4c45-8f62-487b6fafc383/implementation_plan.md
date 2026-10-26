# Interactive 3D Neural Network Hero & Scene Preloader

This plan replaces the existing chain-like torus knot in the hero section with a 3D neural network featuring glowing soma nodes, interconnected axon pathways, and firing synaptic signals, paired with a subtle minimalist neural pulse preloader that smoothly fades out once the WebGL scene renders its first frame.

## User Review & Critical Decisions

> [!IMPORTANT]
> All visual and interaction choices have been confirmed from your answers and integrated into the plan below.

- **Confirmed Decision 1 (3D Hero Graphic)**: Replace the torus knot and wireframe cage with a 3D neural network composed of glowing neuron nodes (somas) and interconnected synaptic pathways (axons) with traveling action-potential pulses.
- **Confirmed Decision 2 (Interactive Behavior)**: Support cursor proximity highlighting—brightening nearby neurons and accelerating synaptic firing along connected axons—alongside smooth cursor tilt and scroll-depth scaling.
- **Confirmed Decision 3 (Hero Preloader)**: Add a minimalist neural pulse indicator with status text in the hero section that smoothly fades out and unmounts from interaction once the Three.js WebGL scene finishes initializing and renders its initial frame.

## 1. Overview & Core Concept

- **What It Does**: Elevates the AI/ML & Full-Stack identity of Satyam Gupta's portfolio by turning the hero backdrop into a living 3D neural architecture. While the Three.js geometry, shaders/materials, and lighting initialize, a sleek neural pulse indicator anchors the hero canvas area, then dissolves seamlessly into the rendered 3D neural network.
- **Target Audience / Persona**: Technical recruiters, AI/ML engineering leads, and hackathon judges exploring the portfolio.
- **Key Value**: Aligns the primary 3D focal point directly with Satyam's AI/ML and deep-learning specialization while eliminating any unstyled canvas pop-in during initial WebGL setup.

## 2. User Experience & Visual Design

- **Key User Flows**:
  1. **Initial Load & Neural Preloader**: On page arrival, the hero canvas starts at `opacity: 0` while a minimalist neural pulse indicator (`Initializing Neural Graph...`) is displayed in the hero stage with a subtle SVG/CSS synaptic ring animation.
  2. **Smooth Scene Reveal**: As soon as the Three.js neural network finishes building its neuron nodes, axon connections, and firing signal particles—and completes its first `renderer.render(scene, camera)` pass—the canvas transitions to full opacity while the preloader smoothly fades out (`opacity: 0`, `pointer-events: none`).
  3. **Cursor Proximity & Synaptic Firing**: Moving the cursor across the hero section projects a 3D interaction locus into the neural graph. Neurons within proximity glow brighter in warm amber-orange and trigger rapid action-potential signal pulses traveling along connected axon lines toward neighboring nodes.
  4. **Scroll Choreography**: Scrolling down smoothly tilts, rotates, and scales the 3D neural cluster in depth while the rising lava dome transitions into the project showcase.
- **Visual Identity & Theme**:
  - *Aesthetic Direction*: Volcanic obsidian AI command center with luminous crimson-amber bioluminescent neural pathways.
  - *Color Palette & Mood*: Obsidian background (`#060606`), deep crimson-ember resting nodes (`#ff2a00`), bright amber-gold excited somas and firing spikes (`#ff6b00` to `#ffd166`), and translucent synaptic filaments.
  - *Typography & Hierarchy*: Existing display headline paired with `JetBrains Mono` (`font-mono`) for the subtle preloader status readouts.
  - *Component Styling & Layout*: Unobstructed full-viewport WebGL canvas (`w-full h-full`) layered behind semantic hero DOM copy (`z-20`) with a non-intrusive preloader badge centered in the visual focal area.
- **Interactive Feedback & Motion**: Frame-rate independent damping on cursor rotation and node excitation, continuous action-potential packets gliding along axon segments, and a 600ms cubic-bezier crossfade between the preloader and live 3D canvas.

## 3. Key Product Decisions & Trade-Offs

- **Decision 1: Procedural Multi-Part 3D Neural Graph (`THREE.Group`)**
  - *Chosen Approach*: Construct the neural network as a structured `THREE.Group` combining spherical soma meshes (core and dendritic hub nodes), a `THREE.LineSegments` buffer for axon connections with dynamic vertex colors, and a `THREE.Points` / instanced signal layer for traveling synaptic pulses.
  - *Why*: Delivers authentic neural topology and high-FPS performance in WebGL without requiring external `.glb` model downloads that could fail or delay page load.
  - *Alternatives Considered*: Static wireframe primitives were rejected because they lack organic neural connectivity and directional signal flow.
- **Decision 2: First-Frame Synchronized Preloader Handshake**
  - *Chosen Approach*: Trigger the preloader fade-out callback immediately after `renderer.render(scene, camera)` completes the first rendered frame (with a graceful fallback timeout if WebGL is unavailable).
  - *Why*: Guarantees zero black-frame flicker between preloader dismissal and 3D scene visibility, and prevents any UI freeze if a browser blocks WebGL.

## 4. Technical Architecture & Data Strategy *(Technical Reference)*

- **Architecture & Component Diagram**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Hero Section Viewport                           │
├───────────────────────────────────┬─────────────────────────────────────┤
│   Minimalist Neural Preloader     │      Three.js WebGL Neural Scene    │
│  • Synaptic SVG Ring Animation    │  • Soma Nodes (Core & Hub Spheres)  │
│  • Monospace Initialization Text  │  • Axon Graph (LineSegments Buffer) │
│  • Auto-Fade on `sceneReady`      │  • Action Potentials (Signal Pulses)│
└─────────────────┬─────────────────┴──────────────────┬──────────────────┘
                  │                                    │
                  │ First Frame Rendered (`onReady`)   │
                  ◄────────────────────────────────────┘
                                                       │
                  ┌────────────────────────────────────┴──────────────────┐
                  │             Real-Time Interaction Loop                │
                  │  • Pointer NDC Projection -> 3D Proximity Excitation  │
                  │  • Active Node Scale & Emissive Boost                 │
                  │  • Synaptic Packet Propagation Along Connected Axons  │
                  │  • Scroll Progress Depth & Rotation Interpolation     │
                  └───────────────────────────────────────────────────────┘
```

- **Data Model & State**:
  - **Neuron Node State**: Each node stores its 3D base position (`Vector3`), organic oscillation phase, connected neighbor indices, and current excitation level (`0.0` to `1.0`) driven by cursor proximity and incoming synaptic pulses.
  - **Synaptic Signal State**: Pool of active action-potential pulses, each tracking its source node, target node, progress (`0.0` → `1.0`), and speed, updating a dedicated `BufferGeometry` position/color attribute each frame.
- **Interactive Component & State Mapping**:
  - *Preloader Lifecycle*: Starts visible in the hero section; when the 3D scene completes setup and renders frame 1, adds the loaded state class that transitions the canvas to `opacity-100` and fades out the preloader overlay.
  - *Cursor Proximity Ray/Projection*: `mousemove` normalizes pointer coordinates and computes distance to each neuron node's projected position, smoothly boosting nearby node scale, emissive intensity, and spawning extra synaptic pulses along attached axons.
  - *Resize & Context Safety*: Window `resize` updates camera aspect and renderer dimensions; `webglcontextlost` and fallback guards ensure the preloader still dismisses cleanly even on non-WebGL devices.
