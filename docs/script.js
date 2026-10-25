/**
 * TURNITOUT — Unified Dual-Mode Engine
 * 1. Scrapbook Manifesto: 3-State Notebook Pattern Disruptor Engine
 * 2. Spatial Academic Desk: Pan & Zoom Infinite Canvas, 64-Ray Radial Dial, Battery Entropy
 * 3. Perspective Switcher: Seamless transition between reading paper & desk workspace
 */

document.addEventListener("DOMContentLoaded", () => {
  // SVG Icons
  const CHECK_SVG = '<svg class="icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>';
  const REFRESH_SVG = '<svg class="icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>';

  // ==========================================================================
  // 1. PERSPECTIVE SWITCHER: Reading Mode vs Look Down at Desk Mode
  // ==========================================================================
  const manifestoView = document.getElementById("manifestoView");
  const spatialDeskView = document.getElementById("spatialDeskView");
  const toggleDeskModeBtn = document.getElementById("toggleDeskModeBtn");
  const lookDownBannerBtn = document.getElementById("lookDownBannerBtn");
  const lookUpBtn = document.getElementById("lookUpBtn");
  const lookUpFloatingBtn = document.getElementById("lookUpFloatingBtn");

  let isDeskMode = false;
  let isTransitioning = false;

  function showDeskMode(instant = false) {
    if (isDeskMode || isTransitioning) return;
    isDeskMode = true;
    if (window.location.hash !== "#desk") {
      history.pushState(null, "", "#desk");
    }

    if (instant) {
      document.body.classList.add("is-desk-mode");
      if (manifestoView) manifestoView.style.display = "none";
      if (spatialDeskView) spatialDeskView.style.display = "flex";
      initSpatialDeskCanvas();
      return;
    }

    isTransitioning = true;
    document.body.classList.add("morphing-to-desk");

    if (spatialDeskView) {
      spatialDeskView.style.display = "flex";
      spatialDeskView.style.opacity = "0";
    }
    initSpatialDeskCanvas();

    setTimeout(() => {
      document.body.classList.add("is-desk-mode");
      document.body.classList.remove("morphing-to-desk");
      if (manifestoView) manifestoView.style.display = "none";
      if (spatialDeskView) spatialDeskView.style.opacity = "";
      isTransitioning = false;
    }, 450);
  }

  function showManifestoMode(instant = false) {
    if (!isDeskMode || isTransitioning) return;
    isDeskMode = false;
    if (window.location.hash === "#desk") {
      history.pushState(null, "", window.location.pathname + window.location.search);
    }

    if (instant) {
      document.body.classList.remove("is-desk-mode");
      if (spatialDeskView) spatialDeskView.style.display = "none";
      if (manifestoView) manifestoView.style.display = "block";
      return;
    }

    isTransitioning = true;
    document.body.classList.add("morphing-to-paper");
    if (manifestoView) {
      manifestoView.style.display = "block";
      manifestoView.style.opacity = "0";
    }

    setTimeout(() => {
      document.body.classList.remove("is-desk-mode");
      document.body.classList.remove("morphing-to-paper");
      if (spatialDeskView) spatialDeskView.style.display = "none";
      if (manifestoView) manifestoView.style.opacity = "";
      isTransitioning = false;
    }, 450);
  }

  if (toggleDeskModeBtn) toggleDeskModeBtn.addEventListener("click", () => showDeskMode(false));
  if (lookDownBannerBtn) lookDownBannerBtn.addEventListener("click", () => showDeskMode(false));
  if (lookUpBtn) lookUpBtn.addEventListener("click", () => showManifestoMode(false));
  if (lookUpFloatingBtn) lookUpFloatingBtn.addEventListener("click", () => showManifestoMode(false));

  window.addEventListener("hashchange", () => {
    if (window.location.hash === "#desk") {
      showDeskMode(false);
    } else {
      showManifestoMode(false);
    }
  });

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && isDeskMode) {
      showManifestoMode(false);
    }
  });

  // Check initial hash on load (instant, no delay on page entrance)
  if (window.location.hash === "#desk") {
    showDeskMode(true);
  }

  // ==========================================================================
  // 2. GLOBAL THEME (DARK / LIGHT MODE - SYNCHRONIZED ACROSS BOTH VIEWS)
  // ==========================================================================
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const hudThemeToggleBtn = document.getElementById("hudThemeToggleBtn");

  function updateThemeUI(isDark) {
    const sunIcon = '<svg class="icon icon-sun" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg><span>Normal Light</span>';
    const moonIcon = '<svg class="icon icon-moon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg><span>3 AM (Dark)</span>';
    
    if (themeToggleBtn) themeToggleBtn.innerHTML = isDark ? sunIcon : moonIcon;
    if (hudThemeToggleBtn) hudThemeToggleBtn.innerHTML = isDark ? sunIcon : moonIcon;
  }

  function toggleGlobalTheme() {
    document.body.classList.toggle("dark-mode");
    const isDark = document.body.classList.contains("dark-mode");
    localStorage.setItem("turnitout_theme", isDark ? "dark" : "light");
    updateThemeUI(isDark);
  }

  const savedTheme = localStorage.getItem("turnitout_theme");
  if (savedTheme === "dark") {
    document.body.classList.add("dark-mode");
    updateThemeUI(true);
  }

  if (themeToggleBtn) themeToggleBtn.addEventListener("click", toggleGlobalTheme);
  if (hudThemeToggleBtn) hudThemeToggleBtn.addEventListener("click", toggleGlobalTheme);

  // ==========================================================================
  // 3. SCRAPBOOK NOTEBOOK SIMULATOR ENGINE (The Student's Revenge)
  // ==========================================================================
  const SAMPLE_ACADEMIC = "In conclusion, it is important to delve into the comprehensive tapestry of modern neural networks. This study plays a pivotal role in illustrating that artificial intelligence stands as a testament to human innovation. Furthermore, the interplay between stochastic optimization and computational scalability provides a robust framework for subsequent empirical inquiries.";

  const SAMPLE_ESSAY = "Moreover, in today's fast-paced digital era, the profound impact of social connectivity cannot be overlooked. This experience serves as a critical milestone in my personal journey. Furthermore, it allows us to delve deep into the multifaceted dimensions of human empathy. Ultimately, this paradigm shift has fundamentally shaped my worldview.";

  const paperSheet = document.getElementById("paperSheet");
  const humanizeBtn = document.getElementById("humanizeBtn");
  const copyBtn = document.getElementById("copyBtn");
  const meterFill = document.getElementById("meterFill");
  const meterScore = document.getElementById("meterScore");
  const sampleAcademicBtn = document.getElementById("sampleAcademicBtn");
  const sampleEssayBtn = document.getElementById("sampleEssayBtn");
  const statusStamp = document.getElementById("statusStamp");
  const tutorNote = document.getElementById("tutorNote");

  let currentSimState = "RAW";
  let cachedRawText = paperSheet ? paperSheet.textContent.trim() : SAMPLE_ACADEMIC;
  let lastCleanedText = "";

  async function resetToRaw(text) {
    cachedRawText = text;
    lastCleanedText = "";
    currentSimState = "RAW";
    if (paperSheet) paperSheet.textContent = text;
    if (statusStamp) statusStamp.style.display = "none";
    if (tutorNote) tutorNote.style.display = "none";
    if (humanizeBtn) humanizeBtn.textContent = "HUMANIZE THIS PAPER →";

    try {
      const detRes = await fetch("/api/detect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      if (detRes.ok) {
        const d = await detRes.json();
        const score = d.ai_risk ?? (d.metrics && d.metrics.ai_risk) ?? 85;
        if (meterFill) {
          meterFill.style.width = `${score}%`;
          meterFill.style.backgroundColor = "var(--red-pen)";
        }
        if (meterScore) {
          meterScore.textContent = `${score}%`;
          meterScore.style.color = "var(--red-pen)";
        }
        return;
      }
    } catch (_) {}
  }

  if (sampleAcademicBtn && paperSheet) {
    sampleAcademicBtn.addEventListener("click", () => resetToRaw(SAMPLE_ACADEMIC));
  }

  if (sampleEssayBtn && paperSheet) {
    sampleEssayBtn.addEventListener("click", () => resetToRaw(SAMPLE_ESSAY));
  }

  if (paperSheet) {
    paperSheet.addEventListener("input", () => {
      if (currentSimState !== "RAW") {
        currentSimState = "RAW";
        if (humanizeBtn) humanizeBtn.textContent = "HUMANIZE THIS PAPER →";
        if (statusStamp) statusStamp.style.display = "none";
        if (tutorNote) tutorNote.style.display = "none";
      }
      cachedRawText = paperSheet.textContent.trim();
    });
  }

  if (humanizeBtn && paperSheet) {
    humanizeBtn.addEventListener("click", async () => {
      if (currentSimState === "RAW") {
        let rawText = cachedRawText || paperSheet.textContent.trim();
        if (!rawText) return;

        humanizeBtn.disabled = true;
        humanizeBtn.textContent = "Humanizing via Engine...";

        try {
          const res = await fetch("/api/humanize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: rawText, intensity: 0.85 })
          });
          if (res.ok) {
            const data = await res.json();
            lastCleanedText = data.cleaned_text || rawText;
            const beforeRisk = data.metrics_before ? data.metrics_before.ai_risk : 85;
            const afterRisk = data.metrics_after ? data.metrics_after.ai_risk : 15;

            let markedHtml = lastCleanedText;
            if (Array.isArray(data.changes) && data.changes.length > 0) {
              data.changes.slice(0, 8).forEach(ch => {
                if (ch.replacement && ch.original && ch.type !== "burstiness_recast") {
                  const escapedRep = ch.replacement.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
                  markedHtml = markedHtml.replace(
                    new RegExp(escapedRep),
                    `<span class="ai-crossed">${ch.original}</span><span class="human-replacement">${ch.replacement}</span>`
                  );
                }
              });
            }
            paperSheet.innerHTML = markedHtml;
            if (meterFill) {
              meterFill.style.width = `${afterRisk}%`;
              meterFill.style.backgroundColor = "#2E7D32";
            }
            if (meterScore) {
              meterScore.textContent = `${afterRisk}%`;
              meterScore.style.color = "#2E7D32";
            }
            if (statusStamp) statusStamp.style.display = "inline-block";
            if (tutorNote) tutorNote.style.display = "block";
            humanizeBtn.disabled = false;
            humanizeBtn.innerHTML = `RESOLVE TO CLEAN TEXT ${CHECK_SVG}`;
            currentSimState = "MARKED";
            return;
          }
        } catch (_) {}

        humanizeBtn.disabled = false;
      } else if (currentSimState === "MARKED") {
        paperSheet.textContent = lastCleanedText || cachedRawText;
        humanizeBtn.innerHTML = `RESET TO RAW AI SAMPLE ${REFRESH_SVG}`;
        currentSimState = "CLEAN";
      } else if (currentSimState === "CLEAN") {
        resetToRaw(cachedRawText);
      }
    });
  }

  // Copy Clean Text to Clipboard
  if (copyBtn && paperSheet) {
    copyBtn.addEventListener("click", () => {
      let textToCopy = lastCleanedText || paperSheet.textContent.trim();

      if (!textToCopy) return;

      navigator.clipboard.writeText(textToCopy).then(() => {
        const originalHtml = copyBtn.innerHTML;
        copyBtn.innerHTML = `Copied Clean Text! ${CHECK_SVG}`;
        setTimeout(() => {
          copyBtn.innerHTML = originalHtml;
        }, 2000);
      });
    });
  }

  // ==========================================================================
  // 4. SPATIAL ACADEMIC DESK CANVAS ENGINE
  // ==========================================================================
  let isCanvasInitialized = false;

  function initSpatialDeskCanvas() {
    if (isCanvasInitialized) return;
    isCanvasInitialized = true;

    const deskViewport = document.getElementById("deskViewport");
    const deskWorld = document.getElementById("deskWorld");
    const zoomInBtn = document.getElementById("zoomInBtn");
    const zoomOutBtn = document.getElementById("zoomOutBtn");
    const resetViewBtn = document.getElementById("resetViewBtn");
    const zoomDisplay = document.getElementById("zoomDisplay");

    // Camera Transform State
    let scale = 0.85;
    let panX = 40;
    let panY = 20;
    let isDragging = false;
    let startX = 0;
    let startY = 0;

    function updateCameraTransform() {
      if (!deskWorld) return;
      deskWorld.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
      if (zoomDisplay) {
        zoomDisplay.textContent = `${Math.round(scale * 100)}%`;
      }
    }

    if (deskViewport) {
      deskViewport.addEventListener("mousedown", (e) => {
        if (e.target.closest("button") || e.target.closest("input") || e.target.closest("[contenteditable='true']") || e.target.closest("a")) {
          return;
        }
        isDragging = true;
        startX = e.clientX - panX;
        startY = e.clientY - panY;
      });

      window.addEventListener("mousemove", (e) => {
        if (!isDragging) return;
        panX = e.clientX - startX;
        panY = e.clientY - startY;
        updateCameraTransform();
      });

      window.addEventListener("mouseup", () => {
        isDragging = false;
      });

      // Mouse Wheel Zoom centered on cursor
      deskViewport.addEventListener("wheel", (e) => {
        e.preventDefault();
        const zoomFactor = 1.1;
        const rect = deskViewport.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        const prevScale = scale;
        if (e.deltaY < 0) {
          scale = Math.min(scale * zoomFactor, 1.75);
        } else {
          scale = Math.max(scale / zoomFactor, 0.45);
        }

        panX = mouseX - (mouseX - panX) * (scale / prevScale);
        panY = mouseY - (mouseY - panY) * (scale / prevScale);
        updateCameraTransform();
      }, { passive: false });
    }

    if (zoomInBtn) {
      zoomInBtn.addEventListener("click", () => {
        scale = Math.min(scale * 1.15, 1.75);
        updateCameraTransform();
      });
    }

    if (zoomOutBtn) {
      zoomOutBtn.addEventListener("click", () => {
        scale = Math.max(scale / 1.15, 0.45);
        updateCameraTransform();
      });
    }

    if (resetViewBtn) {
      resetViewBtn.addEventListener("click", () => {
        scale = 0.85;
        panX = 40;
        panY = 20;
        updateCameraTransform();
      });
    }

    // Spatial Focus Jump Bookmarks
    const focusVitalsBtn = document.getElementById("focusVitalsBtn");
    const focusThesisBtn = document.getElementById("focusThesisBtn");
    const focusArchiveBtn = document.getElementById("focusArchiveBtn");
    const focusDeskBtn = document.getElementById("focusDeskBtn");

    function smoothPanTo(targetX, targetY, targetScale) {
      scale = targetScale;
      panX = targetX;
      panY = targetY;
      deskWorld.style.transition = "transform 0.45s cubic-bezier(0.2, 0.8, 0.2, 1)";
      updateCameraTransform();
      setTimeout(() => {
        if (deskWorld) deskWorld.style.transition = "none";
      }, 450);
    }

    if (focusVitalsBtn) {
      focusVitalsBtn.addEventListener("click", () => {
        smoothPanTo(-150, -100, 1.05);
      });
    }

    if (focusThesisBtn) {
      focusThesisBtn.addEventListener("click", () => {
        smoothPanTo(-550, -100, 1.05);
      });
    }

    if (focusArchiveBtn) {
      focusArchiveBtn.addEventListener("click", () => {
        smoothPanTo(-100, -850, 0.95);
      });
    }

    if (focusDeskBtn) {
      focusDeskBtn.addEventListener("click", () => {
        smoothPanTo(40, 20, 0.85);
      });
    }

    // Generate 64 Rays on Radial Dial SVG
    const radialRayDialSvg = document.getElementById("radialRayDialSvg");
    if (radialRayDialSvg) {
      const cx = 125, cy = 125, r1 = 80, r2 = 112;
      const totalTicks = 64;
      let svgTicksHtml = "";

      for (let i = 0; i < totalTicks; i++) {
        const angle = (i * 360 / totalTicks) * (Math.PI / 180);
        const x1 = cx + r1 * Math.cos(angle);
        const y1 = cy + r1 * Math.sin(angle);
        const x2 = cx + r2 * Math.cos(angle);
        const y2 = cy + r2 * Math.sin(angle);
        const isMajor = (i % 8 === 0);
        const strokeColor = isMajor ? "rgba(20,20,24,0.75)" : "rgba(20,20,24,0.3)";
        const strokeWidth = isMajor ? "2.2" : "1.2";

        svgTicksHtml += `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="${strokeColor}" stroke-width="${strokeWidth}" stroke-linecap="round"/>`;
      }
      radialRayDialSvg.innerHTML = svgTicksHtml;
    }

    // Dial Action Arrow Trigger
    const dialActionArrow = document.getElementById("dialActionArrow");
    const dialScoreNum = document.getElementById("dialScoreNum");
    const dialScoreLabel = document.getElementById("dialScoreLabel");

    if (dialActionArrow) {
      dialActionArrow.addEventListener("click", () => {
        if (radialRayDialSvg) {
          radialRayDialSvg.style.transform = "rotate(720deg)";
          setTimeout(() => {
            radialRayDialSvg.style.transform = "rotate(0deg)";
          }, 800);
        }
        if (dialScoreNum) {
          dialScoreNum.textContent = "0%";
          dialScoreNum.style.color = "var(--ink-green-safe)";
        }
        if (dialScoreLabel) {
          dialScoreLabel.textContent = "AI Neutralized";
          dialScoreLabel.style.color = "var(--ink-green-safe)";
        }
      });
    }

    // Segmented Battery Bar Generation (20 pills)
    const segmentedBatteryBar = document.getElementById("segmentedBatteryBar");
    if (segmentedBatteryBar) {
      let pillsHtml = "";
      for (let i = 0; i < 20; i++) {
        const isFilled = i < 17; // 85% filled
        pillsHtml += `<div class="battery-pill ${isFilled ? 'filled' : ''}"></div>`;
      }
      segmentedBatteryBar.innerHTML = pillsHtml;
    }

    // Desk Interactive Sample Sheet Humanize Button
    const executeHumanizeBtn = document.getElementById("executeHumanizeBtn");
    const deskPaperSheet = document.getElementById("deskPaperSheet");
    if (executeHumanizeBtn && deskPaperSheet) {
      executeHumanizeBtn.addEventListener("click", () => {
        let text = deskPaperSheet.textContent.trim();
        replacements.forEach(item => {
          text = text.replace(item.pattern, item.replace);
        });
        deskPaperSheet.textContent = text;
        executeHumanizeBtn.innerHTML = `<span>DISRUPTED & CLEAN</span> ${CHECK_SVG}`;
        setTimeout(() => {
          executeHumanizeBtn.innerHTML = `<span>DISRUPT AI PATTERNS</span> <svg class="icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>`;
        }, 2200);
      });
    }

    // Task Checklist Interaction
    const taskRows = document.querySelectorAll(".planner-task-row");
    taskRows.forEach(row => {
      row.addEventListener("click", () => {
        row.classList.toggle("is-done");
      });
    });

    updateCameraTransform();
  }

  // ==========================================================================
  // CLUSTER TRAFFIC DISPATCHER: Load-balance across 8 nodes (91% workers, 9% main heart)
  // ==========================================================================
  const CLUSTER_NODES = [
    { url: "https://turnitout1.streamlit.app/", weight: 13 },
    { url: "https://turnitout2.streamlit.app/", weight: 13 },
    { url: "https://turnitout3.streamlit.app/", weight: 13 },
    { url: "https://turnitout4.streamlit.app/", weight: 13 },
    { url: "https://turnitout5.streamlit.app/", weight: 13 },
    { url: "https://turnitout6.streamlit.app/", weight: 13 },
    { url: "https://turnitout7.streamlit.app/", weight: 13 },
    { url: "https://turnitout.streamlit.app/",  weight: 9 }
  ];

  function getRandomClusterNode() {
    const totalWeight = CLUSTER_NODES.reduce((acc, n) => acc + n.weight, 0);
    let rand = Math.random() * totalWeight;
    for (let i = 0; i < CLUSTER_NODES.length; i++) {
      if (rand < CLUSTER_NODES[i].weight) {
        return CLUSTER_NODES[i].url;
      }
      rand -= CLUSTER_NODES[i].weight;
    }
    return CLUSTER_NODES[0].url;
  }

  function isExplicitMirrorLink(link, href) {
    if (link.classList.contains('direct-mirror-link')) return true;
    if (link.dataset && link.dataset.direct === 'true') return true;
    const text = (link.textContent || '').trim().toLowerCase();
    if (text.includes('mirror 1') || text.includes('mirror 2') || text.includes('mirror 3') || text.includes('mirror 4') || text.includes('mirror 5') || text.includes('mirror 6') || text.includes('mirror 7')) {
      return true;
    }
    return false;
  }

  function randomizeAllClusterLinks() {
    try {
      const selectors = [
        '.app-launch-btn',
        '.hud-cta-app-btn',
        '.launch-streamlit-btn',
        'a[href="https://turnitout.streamlit.app/"]'
      ];
      const links = document.querySelectorAll(selectors.join(','));
      links.forEach(link => {
        if (!isExplicitMirrorLink(link, link.getAttribute('href'))) {
          link.href = getRandomClusterNode();
        }
      });
    } catch (e) {}
  }

  randomizeAllClusterLinks();

  document.addEventListener('click', (e) => {
    const link = e.target.closest('a');
    if (!link) return;
    const href = link.getAttribute('href');
    if (isExplicitMirrorLink(link, href)) {
      return; // Respect direct user choice
    }
    const isAppBtn = link.classList.contains('app-launch-btn') ||
                     link.classList.contains('hud-cta-app-btn') ||
                     link.classList.contains('launch-streamlit-btn');
    if (isAppBtn || (href && href === 'https://turnitout.streamlit.app/')) {
      link.href = getRandomClusterNode();
    }
  }, true);
});
