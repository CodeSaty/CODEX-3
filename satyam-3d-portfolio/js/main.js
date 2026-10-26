gsap.registerPlugin(ScrollTrigger);

let currentSpotlightIndex = 0;
let lenis;
let workScrollTrigger;

// 1. INITIALIZE LENIS SMOOTH INERTIA SCROLL
function initSmoothScroll() {
    if (typeof Lenis !== 'undefined') {
        lenis = new Lenis({
            duration: 1.15,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
            smoothWheel: true
        });

        lenis.on('scroll', ScrollTrigger.update);
        gsap.ticker.add((time) => {
            lenis.raf(time * 1000);
        });
        gsap.ticker.lagSmoothing(0);
    }
}

// 2. RENDER DOM ELEMENTS FROM PORTFOLIO_DATA
function renderPortfolio() {
    const tabsContainer = document.getElementById('project-tabs-container');
    const stageContainer = document.getElementById('project-cards-stage');

    // Render Project Tabs
    tabsContainer.innerHTML = PORTFOLIO_DATA.projects.map((p, i) => `
    <button onclick="scrollToProjectCard(${i})" class="project-tab w-full text-left p-5 rounded-2xl transition-all duration-300 ${i === 0 ? 'bg-white/15 backdrop-blur-md border border-white/30 shadow-lg' : 'hover:bg-white/10 border border-transparent'}">
      <div class="flex items-center gap-2.5">
        <span class="tab-dot w-2 h-2 rounded-full ${i === 0 ? 'bg-white' : 'bg-white/40'}"></span>
        <h3 class="text-lg font-medium text-white">${p.tabTitle}</h3>
      </div>
      <p class="text-xs text-white/75 pl-4 mt-1">${p.tabSubtitle}</p>
    </button>
  `).join('');

    // Render 3D Stacked Browser Cards (Cards 1..3 start below the stage and slide up on scroll)
    stageContainer.innerHTML = PORTFOLIO_DATA.projects.map((p, i) => `
    <div id="project-card-${i}" style="z-index: ${10 + i};" class="project-card-3d absolute inset-0 rounded-2xl bg-[#0b0f17] border border-white/20 overflow-hidden flex flex-col justify-between">
      <div class="flex items-center justify-between px-5 py-3.5 bg-[#111622] border-b border-white/10">
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full bg-red-500/80"></span>
          <span class="w-3 h-3 rounded-full bg-amber-400/80"></span>
          <span class="w-3 h-3 rounded-full bg-emerald-500/80"></span>
          <span class="font-mono text-xs text-white/60 ml-2">${p.tabTitle.toLowerCase().replace(/\s+/g, '-')}.app</span>
        </div>
        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-mono bg-orange-500/20 text-orange-300 border border-orange-500/30">${p.badge}</span>
      </div>

      <div class="relative h-60 sm:h-68 w-full bg-black overflow-hidden border-b border-white/10 group">
        <img 
          src="${p.screenshot}" 
          onerror="this.onerror=null; this.src='${p.fallbackSvg}';" 
          alt="${p.title} Screenshot" 
          class="w-full h-full object-cover object-top transition-transform duration-700 group-hover:scale-[1.03]"
        />
      </div>

      <div class="p-6 bg-[#0b0f17] space-y-2.5">
        <div class="flex items-center justify-between">
          <h3 class="text-xl md:text-2xl font-semibold">${p.title}</h3>
          <a href="${p.repoUrl}" target="_blank" class="text-xs font-mono text-orange-400 hover:underline shrink-0">View Source ↗</a>
        </div>
        <p class="text-xs sm:text-sm text-white/75 leading-relaxed">${p.description}</p>
        <p class="text-[11px] font-mono text-white/50 pt-1">Stack: ${p.stack}</p>
      </div>
    </div>
  `).join('');

    // Render Experience & Hackathon Rows
    const expContainer = document.getElementById('experience-list-container');
    expContainer.innerHTML = PORTFOLIO_DATA.experiences.map((exp, i) => `
    <div id="exp-row-${i}" onmouseenter="showExpPreview(${i})" class="exp-row py-8 group cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-2 transition-all duration-300">
      <div>
        <h3 class="text-xl md:text-2xl font-medium transition-all duration-300">${exp.title}</h3>
        <p class="text-xs font-mono uppercase tracking-wider text-white/55 mt-1.5">${exp.subtitle}</p>
      </div>
      <span class="text-white/40 group-hover:text-orange-400 group-hover:translate-x-1 transition text-xl">→</span>
    </div>
  `).join('');
    showExpPreview(0);

    // Render Spotlight & FAQs
    cycleSpotlight(0);
    const faqContainer = document.getElementById('faq-container');
    faqContainer.innerHTML = PORTFOLIO_DATA.faqs.map((f, i) => `
    <div class="py-6">
      <button onclick="toggleFaq(${i})" class="w-full flex items-center justify-between text-left gap-4">
        <span class="text-lg md:text-xl font-medium">${f.q}</span>
        <span id="faq-icon-${i}" class="w-8 h-8 rounded-full ${i === 0 ? 'bg-orange-600' : 'bg-white/10'} text-white flex items-center justify-center font-bold shrink-0">${i === 0 ? '−' : '+'}</span>
      </button>
      <div id="faq-body-${i}" class="${i === 0 ? '' : 'hidden'} mt-4 text-sm md:text-base text-white/70 leading-relaxed">${f.a}</div>
    </div>
  `).join('');
}

// 3. FLUID SCROLL CHOREOGRAPHY (MATCHING REFERENCE VIDEO)
function initScrollChoreography() {
    // A. Hero Scale-Back & Rising Orange Dome Flatten (00:00 - 00:03)
    gsap.to('#hero-content', {
        scale: 0.88,
        opacity: 0.15,
        y: -90,
        ease: 'none',
        scrollTrigger: {
            trigger: '#hero-section',
            start: 'top top',
            end: 'bottom top',
            scrub: true
        }
    });

    gsap.to(':root', {
        '--dome-curve': '0px',
        ease: 'none',
        scrollTrigger: {
            trigger: '#work',
            start: 'top 85%',
            end: 'top 10%',
            scrub: true
        }
    });

    // B. Pinned 3D Project Stacking Sequence (00:03 - 00:09)
    const totalProjects = PORTFOLIO_DATA.projects.length;
    for (let i = 1; i < totalProjects; i++) {
        gsap.set(`#project-card-${i}`, { yPercent: 112, rotateX: 8, scale: 0.96 });
    }

    const workTl = gsap.timeline({
        scrollTrigger: {
            trigger: '#work',
            start: 'top top',
            end: `+=${totalProjects * 85}%`,
            pin: true,
            scrub: 0.85,
            onUpdate: (self) => {
                const activeIdx = Math.min(
                    totalProjects - 1,
                    Math.floor(self.progress * totalProjects)
                );
                highlightActiveTab(activeIdx);
            }
        }
    });
    workScrollTrigger = workTl.scrollTrigger;

    for (let i = 1; i < totalProjects; i++) {
        // Previous card scales back into depth while new card slides up over it
        workTl.to(`#project-card-${i - 1}`, {
            scale: 0.92,
            yPercent: -4,
            opacity: 0.45,
            duration: 1,
            ease: 'power2.inOut'
        }, i - 1);

        workTl.to(`#project-card-${i}`, {
            yPercent: 0,
            rotateX: 0,
            scale: 1,
            duration: 1,
            ease: 'power2.inOut'
        }, i - 1);
    }

    // C. "Why Work With Me?" Stagger & Scroll-Scrubbed Progress Bars (00:10 - 00:14)
    gsap.from('.why-card', {
        y: 60,
        opacity: 0,
        stagger: 0.15,
        duration: 0.8,
        scrollTrigger: {
            trigger: '#why-section',
            start: 'top 75%',
            end: 'top 35%',
            scrub: 1
        }
    });

    gsap.to('.why-progress-bar', {
        width: '100%',
        stagger: 0.15,
        ease: 'none',
        scrollTrigger: {
            trigger: '#why-section',
            start: 'top 65%',
            end: 'bottom 55%',
            scrub: 0.8
        }
    });

    // D. Pinned Horizontal Capabilities Carousel (00:15 - 00:22)
    const track = document.getElementById('capabilities-track');
    const cards = gsap.utils.toArray('#capabilities-track .service-card');

    gsap.to(track, {
        x: () => -(track.scrollWidth - window.innerWidth + 96),
        ease: 'none',
        scrollTrigger: {
            trigger: '#capabilities',
            start: 'top top',
            end: () => `+=${track.scrollWidth}`,
            pin: true,
            scrub: 1,
            invalidateOnRefresh: true,
            onUpdate: (self) => {
                const activeCardIdx = Math.min(
                    cards.length - 1,
                    Math.floor(self.progress * cards.length)
                );
                cards.forEach((c, idx) => c.classList.toggle('active-card', idx === activeCardIdx));
            }
        }
    });

    // E. Scroll-Driven Experience & Hackathon Row Switching (00:23 - 00:30)
    PORTFOLIO_DATA.experiences.forEach((_, idx) => {
        ScrollTrigger.create({
            trigger: `#exp-row-${idx}`,
            start: 'top 60%',
            end: 'bottom 60%',
            onEnter: () => showExpPreview(idx),
            onEnterBack: () => showExpPreview(idx)
        });
    });

    // F. 3D Floating Tech Cloud Multi-Depth Parallax (00:31 - 00:36)
    gsap.utils.toArray('.parallax-badge').forEach((badge) => {
        const speed = parseFloat(badge.getAttribute('data-speed')) || -100;
        gsap.fromTo(badge,
            { y: -speed * 0.6 },
            {
                y: speed,
                ease: 'none',
                scrollTrigger: {
                    trigger: '#cloud-section',
                    start: 'top bottom',
                    end: 'bottom top',
                    scrub: true
                }
            }
        );
    });

    gsap.from('#spotlight-card', {
        y: 80,
        scale: 0.94,
        opacity: 0.2,
        scrollTrigger: {
            trigger: '#spotlight-card',
            start: 'top 90%',
            end: 'top 45%',
            scrub: 1
        }
    });
}

function highlightActiveTab(activeIndex) {
    const tabs = document.querySelectorAll('.project-tab');
    tabs.forEach((tab, idx) => {
        const dot = tab.querySelector('.tab-dot');
        if (idx === activeIndex) {
            tab.className = "project-tab w-full text-left p-5 rounded-2xl transition-all duration-300 bg-white/15 backdrop-blur-md border border-white/30 shadow-lg";
            dot.className = "tab-dot w-2 h-2 rounded-full bg-white";
        } else {
            tab.className = "project-tab w-full text-left p-5 rounded-2xl transition-all duration-300 hover:bg-white/10 border border-transparent";
            dot.className = "tab-dot w-2 h-2 rounded-full bg-white/40";
        }
    });
}

// Click a tab to smoothly scroll to that card's exact position in the pinned timeline
function scrollToProjectCard(index) {
    if (!workScrollTrigger) return;
    const total = PORTFOLIO_DATA.projects.length;
    const targetScroll = workScrollTrigger.start + (workScrollTrigger.end - workScrollTrigger.start) * (index / (total - 0.5));
    if (lenis) {
        lenis.scrollTo(targetScroll);
    } else {
        window.scrollTo({ top: targetScroll, behavior: 'smooth' });
    }
}

function showExpPreview(idx) {
    const item = PORTFOLIO_DATA.experiences[idx];
    document.querySelectorAll('.exp-row').forEach((r, i) => r.classList.toggle('active-exp', i === idx));

    const card = document.getElementById('exp-preview-card');
    gsap.fromTo(card, { rotateY: -6, scale: 0.98 }, { rotateY: 0, scale: 1, duration: 0.4, ease: 'power2.out' });

    document.getElementById('exp-screenshot').src = item.previewImg;
    document.getElementById('exp-badge').textContent = item.badge;
    document.getElementById('exp-title').textContent = item.cardTitle;
    document.getElementById('exp-desc').textContent = item.desc;
    document.getElementById('exp-metrics').innerHTML = `
    <div>
      <span class="text-white/40 block">ROLE / CREDENTIAL</span>
      <span class="text-white font-medium">${item.role}</span>
    </div>
    <div>
      <span class="text-white/40 block">TIMELINE</span>
      <span class="text-orange-300 font-medium">${item.timeline}</span>
    </div>
  `;
}

function cycleSpotlight(dir) {
    const list = PORTFOLIO_DATA.spotlights;
    currentSpotlightIndex = (currentSpotlightIndex + dir + list.length) % list.length;
    const s = list[currentSpotlightIndex];
    document.getElementById('spotlight-tag').textContent = s.tag;
    document.getElementById('spotlight-heading').textContent = s.heading;
    document.getElementById('spotlight-sub').textContent = s.sub;
    document.getElementById('spotlight-quote').textContent = s.quote;
}

function toggleFaq(index) {
    const body = document.getElementById(`faq-body-${index}`);
    const icon = document.getElementById(`faq-icon-${index}`);
    const isHidden = body.classList.contains('hidden');
    body.classList.toggle('hidden', !isHidden);
    icon.textContent = isHidden ? '−' : '+';
    icon.className = `w-8 h-8 rounded-full ${isHidden ? 'bg-orange-600' : 'bg-white/10'} text-white flex items-center justify-center font-bold shrink-0`;
}

function toggleContactModal() {
    const modal = document.getElementById('contact-modal');
    modal.classList.toggle('hidden');
    modal.classList.toggle('flex');
}

document.addEventListener('DOMContentLoaded', () => {
    renderPortfolio();
    initSmoothScroll();
    initScrollChoreography();
});