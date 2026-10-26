// Helper to encode high-res custom SVG screenshots as instant data URIs
const svgToDataUri = (svgString) => `data:image/svg+xml;utf8,${encodeURIComponent(svgString.trim())}`;

// 1. CUSTOM SCREENSHOT: Admin Dashboard & Intelligent Event Command Center
const adminDashboardScreenshot = svgToDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 460" width="100%" height="100%">
  <defs>
    <linearGradient id="bg1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#090D16"/>
      <stop offset="100%" stop-color="#140B14"/>
    </linearGradient>
    <linearGradient id="accent1" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#FF2A00"/>
      <stop offset="100%" stop-color="#FF6B00"/>
    </linearGradient>
  </defs>
  <rect width="900" height="460" fill="url(#bg1)"/>
  <!-- Sidebar -->
  <rect x="0" y="0" width="190" height="460" fill="#0D121F" stroke="#1E293B" stroke-width="1"/>
  <circle cx="28" cy="30" r="6" fill="#FF3B00"/>
  <text x="44" y="34" fill="#FFFFFF" font-family="monospace" font-weight="bold" font-size="13">COMMAND.OS v3</text>
  <rect x="16" y="64" width="158" height="34" rx="8" fill="url(#accent1)"/>
  <text x="30" y="85" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="12">● Live Telemetry</text>
  <text x="30" y="125" fill="#94A3B8" font-family="sans-serif" font-size="12">Guided Event Setup</text>
  <text x="30" y="160" fill="#94A3B8" font-family="sans-serif" font-size="12">Bottleneck Engine</text>
  <text x="30" y="195" fill="#94A3B8" font-family="sans-serif" font-size="12">Gemini NLP Console</text>
  <text x="30" y="230" fill="#94A3B8" font-family="sans-serif" font-size="12">Volunteer Nodes (42)</text>

  <!-- Top Telemetry Header -->
  <rect x="214" y="20" width="662" height="52" rx="10" fill="#111827" stroke="#1F2937"/>
  <text x="234" y="50" fill="#E2E8F0" font-family="monospace" font-size="13">✨ Gemini NLP Query: "Detect crowd bottlenecks near Auditorium Gate B"</text>
  <rect x="755" y="32" width="105" height="28" rx="6" fill="#065F46"/>
  <text x="770" y="50" fill="#6EE7B7" font-family="monospace" font-size="11">FASTAPI: 32ms</text>

  <!-- KPI Cards -->
  <rect x="214" y="90" width="208" height="95" rx="12" fill="#111827" stroke="#374151"/>
  <text x="232" y="118" fill="#94A3B8" font-family="monospace" font-size="11">ACTIVE CROWD TELEMETRY</text>
  <text x="232" y="152" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="26">1,480 Nodes</text>
  <text x="232" y="172" fill="#34D399" font-family="monospace" font-size="11">▲ 99.4% Sync Accuracy</text>

  <rect x="440" y="90" width="208" height="95" rx="12" fill="#1F1215" stroke="#FF3B00"/>
  <text x="458" y="118" fill="#FCA5A5" font-family="monospace" font-size="11">BOTTLENECK RISK ALERT</text>
  <text x="458" y="152" fill="#FF6B00" font-family="sans-serif" font-weight="bold" font-size="24">Zone B Queue</text>
  <text x="458" y="172" fill="#F87171" font-family="monospace" font-size="11">Auto-dispatched 4 leads</text>

  <rect x="668" y="90" width="208" height="95" rx="12" fill="#111827" stroke="#374151"/>
  <text x="686" y="118" fill="#94A3B8" font-family="monospace" font-size="11">AUTO-GENERATED TASKS</text>
  <text x="686" y="152" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="26">64 / 68 Done</text>
  <text x="686" y="172" fill="#60A5FA" font-family="monospace" font-size="11">Ralph Loop Autonomous</text>

  <!-- Live Telemetry Heatmap & Graph Panel -->
  <rect x="214" y="204" width="434" height="232" rx="12" fill="#111827" stroke="#1F2937"/>
  <text x="234" y="234" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="14">Real-Time Event Load & Crowd Density Wave</text>
  <polyline fill="none" stroke="#FF4500" stroke-width="3.5" points="234,380 280,355 330,365 380,300 430,315 480,260 530,285 580,245 625,255"/>
  <polyline fill="none" stroke="#10B981" stroke-width="2.5" stroke-dasharray="5,5" points="234,400 280,390 330,385 380,360 430,350 480,335 530,340 580,310 625,305"/>
  <circle cx="480" cy="260" r="6" fill="#FF2A00"/>
  <rect x="435" y="225" width="110" height="24" rx="5" fill="#FF2A00"/>
  <text x="444" y="241" fill="#FFFFFF" font-family="monospace" font-size="10">PEAK LOAD DETECTED</text>

  <!-- Right Live Node Status List -->
  <rect x="668" y="204" width="208" height="232" rx="12" fill="#111827" stroke="#1F2937"/>
  <text x="686" y="234" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="14">Live Sector Status</text>
  <rect x="686" y="252" width="172" height="42" rx="8" fill="#1E293B"/>
  <text x="698" y="270" fill="#E2E8F0" font-family="sans-serif" font-size="12">Main Hack Arena</text>
  <text x="698" y="286" fill="#34D399" font-family="monospace" font-size="10">● OPTIMAL (82% Cap)</text>
  <rect x="686" y="306" width="172" height="42" rx="8" fill="#1E293B"/>
  <text x="698" y="324" fill="#E2E8F0" font-family="sans-serif" font-size="12">Check-In Desk B</text>
  <text x="698" y="340" fill="#FBBF24" font-family="monospace" font-size="10">▲ REROUTING TRAFFIC</text>
  <rect x="686" y="360" width="172" height="42" rx="8" fill="#1E293B"/>
  <text x="698" y="378" fill="#E2E8F0" font-family="sans-serif" font-size="12">MongoDB Atlas Cluster</text>
  <text x="698" y="394" fill="#34D399" font-family="monospace" font-size="10">● HEALTHY (0ms lag)</text>
</svg>
`);

// 2. CUSTOM SCREENSHOT: Car Dealership 2.0 & Catalog Admin
const carDealershipScreenshot = svgToDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 460" width="100%" height="100%">
  <rect width="900" height="460" fill="#0B0D11"/>
  <!-- Top Bar -->
  <rect x="0" y="0" width="900" height="58" fill="#12161F"/>
  <text x="30" y="35" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="16">CAR DEALERSHIP 2.0 // ADMIN CATALOG</text>
  <rect x="720" y="16" width="150" height="28" rx="14" fill="#F59E0B"/>
  <text x="742" y="34" fill="#000000" font-family="monospace" font-weight="bold" font-size="11">+ ADD NEW VEHICLE</text>

  <!-- Left Analytics Card -->
  <rect x="28" y="80" width="380" height="350" rx="14" fill="#141821" stroke="#262D3D"/>
  <text x="50" y="114" fill="#F59E0B" font-family="monospace" font-size="11">INVENTORY VALUATION & ANALYTICS</text>
  <text x="50" y="146" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="24">128 Active Vehicles</text>
  <!-- Bar chart -->
  <rect x="60" y="250" width="38" height="130" rx="6" fill="#F59E0B"/>
  <rect x="120" y="210" width="38" height="170" rx="6" fill="#FF4500"/>
  <rect x="180" y="280" width="38" height="100" rx="6" fill="#3B82F6"/>
  <rect x="240" y="190" width="38" height="190" rx="6" fill="#10B981"/>
  <rect x="300" y="235" width="38" height="145" rx="6" fill="#8B5CF6"/>
  <text x="64" y="402" fill="#94A3B8" font-family="monospace" font-size="10">SUVs</text>
  <text x="120" y="402" fill="#94A3B8" font-family="monospace" font-size="10">Sedan</text>
  <text x="180" y="402" fill="#94A3B8" font-family="monospace" font-size="10">EVs</text>
  <text x="238" y="402" fill="#94A3B8" font-family="monospace" font-size="10">Sports</text>
  <text x="300" y="402" fill="#94A3B8" font-family="monospace" font-size="10">Luxury</text>

  <!-- Right Catalog CRUD Table -->
  <rect x="430" y="80" width="442" height="350" rx="14" fill="#141821" stroke="#262D3D"/>
  <text x="454" y="115" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="16">Live Vehicle Catalog (FastAPI + SQL)</text>
  
  <rect x="454" y="140" width="394" height="58" rx="10" fill="#1C2230"/>
  <text x="472" y="166" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="14">Porsche 911 GT3 RS (2026 Spec)</text>
  <text x="472" y="185" fill="#34D399" font-family="monospace" font-size="11">IN STOCK • ID #CD-204 • TypeScript UI</text>
  <rect x="765" y="155" width="66" height="26" rx="6" fill="#2563EB"/>
  <text x="782" y="172" fill="#FFFFFF" font-family="monospace" font-size="11">EDIT</text>

  <rect x="454" y="212" width="394" height="58" rx="10" fill="#1C2230"/>
  <text x="472" y="238" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="14">BMW M4 Competition xDrive</text>
  <text x="472" y="257" fill="#FBBF24" font-family="monospace" font-size="11">RESERVED • ID #CD-198 • Full CRUD</text>
  <rect x="765" y="227" width="66" height="26" rx="6" fill="#2563EB"/>
  <text x="782" y="244" fill="#FFFFFF" font-family="monospace" font-size="11">EDIT</text>

  <rect x="454" y="284" width="394" height="58" rx="10" fill="#1C2230"/>
  <text x="472" y="310" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="14">Audi e-tron GT Quattro</text>
  <text x="472" y="329" fill="#34D399" font-family="monospace" font-size="11">IN STOCK • ID #CD-219 • CSV/SQL Sync</text>
  <rect x="765" y="299" width="66" height="26" rx="6" fill="#2563EB"/>
  <text x="782" y="316" fill="#FFFFFF" font-family="monospace" font-size="11">EDIT</text>
</svg>
`);

// 3. CUSTOM SCREENSHOT: Spotify AI Song Recommender
const spotifyMlScreenshot = svgToDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 460" width="100%" height="100%">
  <rect width="900" height="460" fill="#07120D"/>
  <rect x="24" y="24" width="852" height="412" rx="16" fill="#0D1F17" stroke="#10B981" stroke-opacity="0.35"/>
  <circle cx="60" cy="64" r="14" fill="#10B981"/>
  <text x="86" y="70" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="18">Spotify AI Cosine Similarity Recommender</text>
  <text x="660" y="68" fill="#6EE7B7" font-family="monospace" font-size="12">Scikit-Learn • Streamlit</text>

  <!-- Seed Track Vector Box -->
  <rect x="52" y="105" width="360" height="300" rx="14" fill="#122B20" stroke="#10B981" stroke-opacity="0.3"/>
  <text x="74" y="138" fill="#6EE7B7" font-family="monospace" font-size="11">INPUT AUDIO FEATURE VECTOR</text>
  <text x="74" y="168" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="20">Seed Track: Desi Hip-Hop Mix</text>
  <text x="74" y="208" fill="#A7F3D0" font-family="monospace" font-size="12">Tempo / BPM (128)</text>
  <rect x="74" y="218" width="290" height="10" rx="5" fill="#064E3B"/>
  <rect x="74" y="218" width="245" height="10" rx="5" fill="#10B981"/>

  <text x="74" y="260" fill="#A7F3D0" font-family="monospace" font-size="12">Energy & Bass Weight (0.89)</text>
  <rect x="74" y="270" width="290" height="10" rx="5" fill="#064E3B"/>
  <rect x="74" y="270" width="265" height="10" rx="5" fill="#34D399"/>

  <text x="74" y="312" fill="#A7F3D0" font-family="monospace" font-size="12">Valence / Mood Index (0.76)</text>
  <rect x="74" y="322" width="290" height="10" rx="5" fill="#064E3B"/>
  <rect x="74" y="322" width="215" height="10" rx="5" fill="#10B981"/>

  <!-- Top Cosine Matches -->
  <rect x="440" y="105" width="408" height="300" rx="14" fill="#122B20"/>
  <text x="466" y="138" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="15">Top Vector Similarity Recommendations</text>

  <rect x="466" y="158" width="356" height="64" rx="10" fill="#18382B"/>
  <text x="486" y="185" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="14">1. KR$NA & Seedhe Maut — Hola Amigo</text>
  <text x="486" y="206" fill="#34D399" font-family="monospace" font-size="11">Cosine Similarity: 0.984 • Match: 98.4%</text>

  <rect x="466" y="236" width="356" height="64" rx="10" fill="#18382B"/>
  <text x="486" y="263" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="14">2. Cheema Y — Jackpot</text>
  <text x="486" y="284" fill="#34D399" font-family="monospace" font-size="11">Cosine Similarity: 0.968 • Match: 96.8%</text>

  <rect x="466" y="314" width="356" height="64" rx="10" fill="#18382B"/>
  <text x="486" y="341" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="14">3. DIVINE & Raftaar — Top Class</text>
  <text x="486" y="362" fill="#34D399" font-family="monospace" font-size="11">Cosine Similarity: 0.952 • Match: 95.2%</text>
</svg>
`);

// 4. CUSTOM SCREENSHOT: IMDB Movie Sentiment Analyzer
const imdbNlpScreenshot = svgToDataUri(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 460" width="100%" height="100%">
  <rect width="900" height="460" fill="#12091A"/>
  <rect x="28" y="28" width="844" height="404" rx="16" fill="#1B0F26" stroke="#A855F7" stroke-opacity="0.35"/>
  <text x="58" y="72" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="19">IMDB NLP Movie Review Sentiment Classifier</text>
  <rect x="670" y="48" width="170" height="30" rx="8" fill="#3B0764"/>
  <text x="690" y="67" fill="#E9D5FF" font-family="monospace" font-size="11">TF-IDF • 50K Reviews</text>

  <rect x="58" y="100" width="460" height="145" rx="12" fill="#261636" stroke="#7E22CE"/>
  <text x="78" y="128" fill="#C084FC" font-family="monospace" font-size="11">LIVE TOKENIZED REVIEW INPUT</text>
  <text x="78" y="158" fill="#FFFFFF" font-family="sans-serif" font-size="14">"Stunning cinematography and a powerhouse</text>
  <text x="78" y="182" fill="#FFFFFF" font-family="sans-serif" font-size="14">screenplay that keeps you hooked until the</text>
  <text x="78" y="206" fill="#34D399" font-family="monospace" font-size="13">[+masterpiece] [+brilliant] [+gripping]</text>

  <rect x="58" y="265" width="460" height="135" rx="12" fill="#261636"/>
  <text x="78" y="295" fill="#E9D5FF" font-family="sans-serif" font-weight="bold" font-size="14">N-Gram Polarity Weight Distribution</text>
  <rect x="78" y="315" width="380" height="18" rx="9" fill="#3B0764"/>
  <rect x="78" y="315" width="358" height="18" rx="9" fill="#10B981"/>
  <text x="78" y="362" fill="#34D399" font-family="monospace" font-size="12">Positive Confidence: 94.8%  |  Negative: 5.2%</text>

  <!-- Right Confidence Gauge -->
  <rect x="546" y="100" width="296" height="300" rx="12" fill="#261636"/>
  <circle cx="694" cy="225" r="74" fill="none" stroke="#3B0764" stroke-width="16"/>
  <circle cx="694" cy="225" r="74" fill="none" stroke="#A855F7" stroke-width="16" stroke-dasharray="430 465"/>
  <text x="652" y="234" fill="#FFFFFF" font-family="sans-serif" font-weight="bold" font-size="28">94.8%</text>
  <text x="625" y="338" fill="#34D399" font-family="monospace" font-weight="bold" font-size="14">● POSITIVE SENTIMENT</text>
</svg>
`);

// Portfolio Data Export
const PORTFOLIO_DATA = {
    projects: [
        {
            id: 0,
            tabTitle: "Event Command Center",
            tabSubtitle: "Admin Dashboard • FastAPI, Tailwind & Gemini NLP",
            badge: "ADMIN DASHBOARD FLAGSHIP",
            title: "Intelligent Event Command Center",
            description: "Refactored from a live campus-wide Traitor game admin monitoring panel into a native HTML/Tailwind & FastAPI command center. Features dual-phase planning vs. live telemetry, automated bottleneck detection, and Gemini NLP command execution.",
            stack: "FastAPI • Tailwind CSS • MongoDB Atlas • Gemini API",
            screenshot: "assets/screenshots/admin-dashboard.png",
            fallbackSvg: adminDashboardScreenshot,
            repoUrl: "https://github.com/DevSaty-py"
        },
        {
            id: 1,
            tabTitle: "Car Dealership 2.0",
            tabSubtitle: "Full-Stack Catalog & Admin • TypeScript & FastAPI",
            badge: "FULL-STACK AUTOMOTIVE PLATFORM",
            title: "Car Dealership 2.0 & Catalog Admin",
            description: "End-to-end automotive dealership management system featuring a customer showroom and an administrative catalog dashboard for full CRUD inventory control, tabular/graphical analytics, and SQL persistence.",
            stack: "Python • TypeScript • FastAPI • PostgreSQL • Pandas",
            screenshot: "assets/screenshots/car-dealership.png",
            fallbackSvg: carDealershipScreenshot,
            repoUrl: "https://github.com/DevSaty-py"
        },
        {
            id: 2,
            tabTitle: "Spotify AI Recommender",
            tabSubtitle: "Machine Learning Engine • Scikit-Learn & Streamlit",
            badge: "MACHINE LEARNING DISCOVERY",
            title: "Spotify AI Song Recommender",
            description: "Content-based filtering engine that computes high-dimensional cosine similarity vectors across tempo, energy, and valence features to deliver real-time music recommendations.",
            stack: "Python • Scikit-Learn • Pandas • NumPy • Streamlit",
            screenshot: "assets/screenshots/spotify-ml.png",
            fallbackSvg: spotifyMlScreenshot,
            repoUrl: "https://github.com/DevSaty-py"
        },
        {
            id: 3,
            tabTitle: "IMDB Sentiment Engine",
            tabSubtitle: "NLP Polarity Pipeline • Python & Interactive UI",
            badge: "NATURAL LANGUAGE PROCESSING",
            title: "IMDB Movie Sentiment Analyzer",
            description: "Real-time NLP classification pipeline trained on 50,000+ film reviews with automated TF-IDF vectorization, token weight highlighting, and interactive polarity confidence gauges.",
            stack: "Python • Scikit-Learn • NLP • Matplotlib • Streamlit",
            screenshot: "assets/screenshots/imdb-nlp.png",
            fallbackSvg: imdbNlpScreenshot,
            repoUrl: "https://github.com/DevSaty-py"
        }
    ],

    experiences: [
        {
            title: "Campus Ambassador Intern — Techkriti, IIT Kanpur",
            subtitle: "OCT 2025 – MAR 2026 — INTERNSHIP & LEADERSHIP EXPERIENCE",
            badge: "INTERNSHIP EXPERIENCE",
            cardTitle: "Techkriti, IIT Kanpur — Campus Ambassador",
            desc: "Led campus-wide technical outreach, promotional campaigns, and student developer coordination for IIT Kanpur's annual technical festival.",
            role: "Campus Ambassador Intern",
            timeline: "Oct 2025 – Mar 2026",
            previewImg: adminDashboardScreenshot
        },
        {
            title: "CodeX 3.0 Hack Arena — Intelligent Event Command Center",
            subtitle: "OCT 2026 — HACKATHON EXPERIENCE (HACKINGLY.IN)",
            badge: "HACKATHON FINALIST BUILD",
            cardTitle: "CodeX 3.0 Hack Arena — Event Command Center",
            desc: "Architected and pitched an AI-powered Event Command Center using FastAPI, MongoDB Atlas, Gemini API NLP querying, and Ralph Loop autonomous workflows.",
            role: "Full-Stack & AI Architect",
            timeline: "October 2026",
            previewImg: adminDashboardScreenshot
        },
        {
            title: "1st Place Winner — Pictorial Showdown",
            subtitle: "SEP 2025 — AI PROMPT ENGINEERING COMPETITION",
            badge: "1ST PLACE WINNER",
            cardTitle: "Pictorial Showdown — Prompt Engineering",
            desc: "Secured 1st place for precision generative AI synthesis and multi-constraint visual prompt engineering under competitive time limits.",
            role: "1st Place Winner",
            timeline: "September 2025",
            previewImg: imdbNlpScreenshot
        },
        {
            title: "B.Tech CSE (AI & ML) @ KU & AWS Community Credential",
            subtitle: "2025 – 2029 — KURUKSHETRA UNIVERSITY (KU) & AWS COMMUNITY DAY",
            badge: "ACADEMIC & CLOUD CREDENTIAL",
            cardTitle: "Kurukshetra University (KU) & AWS Credential",
            desc: "Pursuing B.Tech in Computer Science & Engineering (AI & ML) at Kurukshetra University alongside earned credentials at AWS Student Community Day 2026.",
            role: "B.Tech CSE (AI & ML)",
            timeline: "2025 – 2029 @ KU",
            previewImg: carDealershipScreenshot
        }
    ],

    spotlights: [
        {
            tag: "SYSTEM ARCHITECTURE DEEP-DIVE 01 / 03",
            heading: "From Streamlit Prototype to FastAPI Command Center",
            sub: "Admin Dashboard & Real-Time Event Telemetry Refactor",
            quote: "\"Originally built as a Streamlit monitoring panel for a campus-wide Traitor game, I re-architected the stack into a native HTML/Tailwind & FastAPI platform to eliminate state re-render lag—adding a real-time bottleneck detection engine and Gemini NLP command execution.\""
        },
        {
            tag: "SYSTEM ARCHITECTURE DEEP-DIVE 02 / 03",
            heading: "Autonomous Hackathon Execution at CodeX 3.0",
            sub: "FastAPI + MongoDB Atlas + Gemini API Integration",
            quote: "\"During CodeX 3.0 Hack Arena, our focus was building a true decision-support command center. By combining guided event setup with automated task generation and live crowd telemetry, organizers can query live status in natural language.\""
        },
        {
            tag: "SYSTEM ARCHITECTURE DEEP-DIVE 03 / 03",
            heading: "End-to-End Automotive & ML Pipelines",
            sub: "Car Dealership 2.0 & Scikit-Learn Recommendation Engines",
            quote: "\"Whether structuring relational schemas for Car Dealership 2.0 or vectorizing audio and text features for Spotify and IMDB machine learning apps, every project pairs clean Python backend code with an intuitive visual layer.\""
        }
    ],

    faqs: [
        {
            q: "Who is Satyam Gupta and what kind of engineering projects do you build?",
            a: "I am a Computer Science & Engineering undergraduate specializing in Artificial Intelligence and Machine Learning at Kurukshetra University (KU). I build high-performance full-stack web apps, real-time administrative command dashboards, and machine learning pipelines."
        },
        {
            q: "What makes your Admin Dashboard / Event Command Center unique?",
            a: "It combines dual-phase event management (guided setup with automated task generation + live telemetry monitoring) with an AI-assisted bottleneck detection engine and natural language querying powered by the Gemini API over FastAPI and MongoDB Atlas."
        },
        {
            q: "Are you available for AI/ML, Backend, or Full-Stack Internships?",
            a: "Yes! I am actively open to software engineering, backend architecture, and AI/ML internship opportunities, as well as collaborative hackathon builds."
        }
    ]
};