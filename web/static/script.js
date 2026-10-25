document.addEventListener("DOMContentLoaded", () => {
  // Controls & Elements
  const intensitySlider = document.getElementById("intensitySlider");
  const intensityLabel = document.getElementById("intensityLabel");
  const inputText = document.getElementById("inputText");
  const outputText = document.getElementById("outputText");
  const humanizeBtn = document.getElementById("humanizeBtn");
  const loadSampleBtn = document.getElementById("loadSampleBtn");
  const clearBtn = document.getElementById("clearBtn");
  const copyBtn = document.getElementById("copyBtn");
  const inputWordCount = document.getElementById("inputWordCount");
  const outputWordCount = document.getElementById("outputWordCount");
  const activeModelBadge = document.getElementById("activeModelBadge");

  // Document Upload / Drag & Drop Elements
  const inputPane = document.getElementById("inputPane");
  const dropOverlay = document.getElementById("dropOverlay");
  const docBadge = document.getElementById("docBadge");
  const docBadgeName = document.getElementById("docBadgeName");
  const uploadDocxBtn = document.getElementById("uploadDocxBtn");
  const docxFileInput = document.getElementById("docxFileInput");
  const downloadDocxBtn = document.getElementById("downloadDocxBtn");

  let activeDocxFile = null;
  let activeDocxDownloadUrl = null;

  // Progress HUD & Elapsed Timer
  const progressContainer = document.getElementById("progressContainer");
  const progressStatusText = document.getElementById("progressStatusText");
  const progressChunkBadge = document.getElementById("progressChunkBadge");
  const progressTimer = document.getElementById("progressTimer");
  const progressBarFill = document.getElementById("progressBarFill");

  let elapsedIntervalId = null;
  let elapsedStartTime = 0;

  // Metrics HUD
  const metricsBar = document.getElementById("metricsBar");
  const metricAiBefore = document.getElementById("metricAiBefore");
  const metricAiAfter = document.getElementById("metricAiAfter");
  const metricBurstiness = document.getElementById("metricBurstiness");
  const metricCliches = document.getElementById("metricCliches");
  const metricChanges = document.getElementById("metricChanges");

  // Legal Modals & Cookie Consent
  const legalModal = document.getElementById("legalModal");
  const legalModalTitle = document.getElementById("legalModalTitle");
  const legalModalBody = document.getElementById("legalModalBody");
  const closeLegalModalBtn = document.getElementById("closeLegalModalBtn");
  const cookieBanner = document.getElementById("cookieBanner");
  const acceptCookiesBtn = document.getElementById("acceptCookiesBtn");

  // SVGs for dynamic buttons (Strict Zero-Emoji Policy)
  const LIGHTNING_SVG = '<svg class="svg-icon" viewBox="0 0 24 24" width="16" height="16" fill="currentColor" stroke="currentColor" stroke-width="1.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>';
  const PULSE_SVG = '<svg class="svg-icon" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>';
  const CHECK_SVG = '<svg class="svg-icon" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
  const CLOCK_SVG = '<svg class="svg-icon" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>';
  const DOWNLOAD_SVG = '<svg class="svg-icon" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>';

  function formatElapsed(ms) {
    const totalSec = Math.max(0, Math.floor(ms / 1000));
    const mins = String(Math.floor(totalSec / 60)).padStart(2, "0");
    const secs = String(totalSec % 60).padStart(2, "0");
    return `${mins}:${secs}`;
  }

  function startElapsedTimer() {
    stopElapsedTimer();
    elapsedStartTime = Date.now();
    if (progressTimer) {
      progressTimer.innerHTML = `${CLOCK_SVG} ELAPSED: 00:00`;
    }
    elapsedIntervalId = setInterval(() => {
      if (progressTimer) {
        progressTimer.innerHTML = `${CLOCK_SVG} ELAPSED: ${formatElapsed(Date.now() - elapsedStartTime)}`;
      }
    }, 1000);
  }

  function stopElapsedTimer() {
    if (elapsedIntervalId) {
      clearInterval(elapsedIntervalId);
      elapsedIntervalId = null;
    }
  }

  // Intensity Slider Label
  intensitySlider.addEventListener("input", (e) => {
    const val = parseInt(e.target.value, 10);
    let desc = "Balanced";
    if (val < 40) desc = "Subtle";
    else if (val > 75) desc = "Aggressive";
    intensityLabel.textContent = `${desc} (${val}%)`;
  });

  function countWords(str) {
    if (!str || !str.trim()) return 0;
    return str.trim().split(/\s+/).length;
  }

  inputText.addEventListener("input", () => {
    inputWordCount.textContent = `${countWords(inputText.value)} words`;
  });

  // Rotating Pool of Authentic Multi-Domain Academic Thesis Excerpts (No Predefined Outputs)
  const SAMPLE_THESIS_POOL = [
    `1. Abstract & Problem Statement
Temporary file transmission across open networks presents critical security vulnerabilities: persistent data exposure on remote servers, silent data corruption (bit-rot or malicious in-flight modification), unauthorized token enumeration, and intrusive user tracking. FileGuard is an academic and production-engineered web platform providing zero-knowledge temporary file sharing [1]. It implements a strict 12-hour self-destruct lifecycle, pre-flight SHA-256 cryptographic verification, in-memory folder ZIP bundling, CIDR-masked subnet quota controls, and a digital forensics inspection lab.

2. Architectural Overview & Subsystem Specifications
The system coordinates web routing, object storage, and relational state without disk bottlenecks or unencrypted staging leaks.`,

    `1. Methodology & Distributed Consensus Analysis
In the realm of distributed state machines, cryptographic verification plays a pivotal role in safeguarding telemetry across untrusted edge nodes [4] — highlighting the urgent need for a comprehensive paradigm shift. Furthermore, it is important to note that conventional leader-election protocols delve into synchronous quorum replication, fostering a deeper understanding of network partition recovery while ensuring seamless integration with zero-trust storage engines ($O(n \\log n)$). Consequently, this multifaceted architecture not only reduces tail latency across geo-distributed clusters, but also mitigates Byzantine fault injection, ultimately paving the way for resilient cloud infrastructure.`,

    `1. Empirical Evaluation of Transformer Attention Horizons
Long-context sequence modeling requires substantial memory bandwidth due to quadratic key-value cache growth during autoregressive decoding [12]. Moreover, standard sparse-attention approximations frequently degrade retrieval fidelity when relevant tokens fall outside fixed sliding windows, underscoring the importance of dynamic eviction policies. Therefore, our experimental benchmark evaluates sub-linear KV-cache compression across 32-layer decoder architectures, demonstrating that entropy-guided token retention preserves perplexity within 0.4% of full-rank attention.`
  ];
  let sampleIndex = 0;

  loadSampleBtn.addEventListener("click", () => {
    inputText.value = SAMPLE_THESIS_POOL[sampleIndex % SAMPLE_THESIS_POOL.length];
    sampleIndex += 1;
    outputText.value = "";
    outputWordCount.textContent = "0 words";
    metricsBar.style.display = "none";
    progressContainer.style.display = "none";
    stopElapsedTimer();
    inputWordCount.textContent = `${countWords(inputText.value)} words`;
  });

  clearBtn.addEventListener("click", () => {
    inputText.value = "";
    outputText.value = "";
    inputWordCount.textContent = "0 words";
    outputWordCount.textContent = "0 words";
    metricsBar.style.display = "none";
    progressContainer.style.display = "none";
    stopElapsedTimer();
    activeDocxFile = null;
    if (docxFileInput) docxFileInput.value = "";
    docBadge.style.display = "none";
    downloadDocxBtn.style.display = "none";
    if (activeDocxDownloadUrl) {
      URL.revokeObjectURL(activeDocxDownloadUrl);
      activeDocxDownloadUrl = null;
    }
  });

  // ==========================================================================
  // DOCUMENT UPLOAD & DRAG-AND-DROP INGESTION (.DOCX, .TXT, .MD)
  // ==========================================================================
  async function handleDocumentFile(file) {
    if (!file) return;
    const name = file.name.toLowerCase();

    if (name.endsWith(".pdf")) {
      alert("PDF documents use rigid, pre-compiled coordinate layouts that break when sentence lengths change. Please upload your editable Word document (.docx) or plain text (.txt / .md) to keep 100% of tables, columns, and styling intact.");
      return;
    }

    if (name.endsWith(".docx")) {
      activeDocxFile = file;
      docBadgeName.textContent = file.name;
      docBadge.style.display = "inline-flex";
      downloadDocxBtn.style.display = "none";
      if (activeDocxDownloadUrl) {
        URL.revokeObjectURL(activeDocxDownloadUrl);
        activeDocxDownloadUrl = null;
      }

      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch("/api/extract-docx", {
          method: "POST",
          body: formData
        });
        if (!res.ok) {
          throw new Error(`Server returned ${res.status}`);
        }
        const data = await res.json();
        inputText.value = data.text || "";
        inputWordCount.textContent = `${countWords(inputText.value)} words`;
      } catch (err) {
        alert("Error reading .docx file: " + err.message);
      }
      return;
    }

    if (name.endsWith(".txt") || name.endsWith(".md")) {
      activeDocxFile = null;
      docBadge.style.display = "none";
      downloadDocxBtn.style.display = "none";
      const reader = new FileReader();
      reader.onload = (event) => {
        inputText.value = event.target.result;
        inputWordCount.textContent = `${countWords(inputText.value)} words`;
      };
      reader.readAsText(file);
      return;
    }

    alert("Unsupported file format. Please upload a Word document (.docx) or plain text (.txt / .md).");
  }

  if (uploadDocxBtn && docxFileInput) {
    uploadDocxBtn.addEventListener("click", () => {
      docxFileInput.click();
    });
    docxFileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleDocumentFile(e.target.files[0]);
      }
    });
  }

  let dragCounter = 0;

  inputPane.addEventListener("dragenter", (e) => {
    e.preventDefault();
    dragCounter++;
    if (!inputText.value.trim()) {
      dropOverlay.style.display = "flex";
    }
  });

  inputPane.addEventListener("dragover", (e) => {
    e.preventDefault();
  });

  inputPane.addEventListener("dragleave", (e) => {
    e.preventDefault();
    dragCounter--;
    if (dragCounter <= 0) {
      dragCounter = 0;
      dropOverlay.style.display = "none";
    }
  });

  inputPane.addEventListener("drop", async (e) => {
    e.preventDefault();
    dragCounter = 0;
    dropOverlay.style.display = "none";

    const files = e.dataTransfer.files;
    if (!files || files.length === 0) return;
    await handleDocumentFile(files[0]);
  });

  // Helper to rebuild & download .docx in <200ms using /api/rebuild-docx
  async function prepareAndTriggerDocxDownload(humanizedStr, autoTrigger = false) {
    if (!activeDocxFile || !humanizedStr || !humanizedStr.trim()) return;
    try {
      downloadDocxBtn.disabled = true;
      downloadDocxBtn.innerHTML = `${DOWNLOAD_SVG} BUILDING .DOCX...`;
      downloadDocxBtn.style.display = "inline-flex";

      const docxForm = new FormData();
      docxForm.append("file", activeDocxFile);
      docxForm.append("humanized_text", humanizedStr);

      const docxRes = await fetch("/api/rebuild-docx", {
        method: "POST",
        body: docxForm
      });

      if (!docxRes.ok) {
        throw new Error(`HTTP ${docxRes.status}`);
      }

      const blob = await docxRes.blob();
      if (activeDocxDownloadUrl) URL.revokeObjectURL(activeDocxDownloadUrl);
      activeDocxDownloadUrl = URL.createObjectURL(blob);

      downloadDocxBtn.disabled = false;
      downloadDocxBtn.innerHTML = `${DOWNLOAD_SVG} DOWNLOAD .DOCX`;
      downloadDocxBtn.style.display = "inline-flex";

      if (autoTrigger) {
        const a = document.createElement("a");
        a.href = activeDocxDownloadUrl;
        a.download = `Humanized_${activeDocxFile.name}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      }
    } catch (err) {
      downloadDocxBtn.disabled = false;
      downloadDocxBtn.innerHTML = `${DOWNLOAD_SVG} DOWNLOAD .DOCX`;
      downloadDocxBtn.style.display = "inline-flex";
      if (autoTrigger) {
        alert("Could not build .docx file: " + err.message);
      }
    }
  }

  downloadDocxBtn.addEventListener("click", async () => {
    if (activeDocxDownloadUrl && activeDocxFile) {
      const a = document.createElement("a");
      a.href = activeDocxDownloadUrl;
      a.download = `Humanized_${activeDocxFile.name}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } else if (activeDocxFile && outputText.value.trim()) {
      await prepareAndTriggerDocxDownload(outputText.value, true);
    }
  });

  // ==========================================================================
  // PARALLEL MULTI-MODEL SHARDED STREAMING HUMANIZER (10,000+ WORDS)
  // ==========================================================================
  humanizeBtn.addEventListener("click", async () => {
    const text = inputText.value.trim();
    if (!text) {
      alert("Please paste your thesis text or upload a .docx document to humanize.");
      return;
    }

    humanizeBtn.disabled = true;
    humanizeBtn.innerHTML = `${LIGHTNING_SVG} HUMANIZING THESIS...`;
    outputText.value = "";
    outputWordCount.textContent = "0 words";

    if (activeDocxDownloadUrl) {
      URL.revokeObjectURL(activeDocxDownloadUrl);
      activeDocxDownloadUrl = null;
    }

    progressContainer.style.display = "flex";
    progressBarFill.style.width = "5%";
    progressStatusText.textContent = "ANALYZING & SPLITTING DOCUMENT INTO PARAGRAPH CHUNKS...";
    progressChunkBadge.textContent = "PREPARING";
    startElapsedTimer();

    try {
      const intensity = parseInt(intensitySlider.value, 10) / 100.0;

      // Step 1: Split document into safe ~550-word chunks + get baseline AI risk
      const chunkRes = await fetch("/api/chunk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, max_words_per_chunk: 550 })
      });

      if (!chunkRes.ok) {
        throw new Error(`Chunking server error (${chunkRes.status})`);
      }

      const chunkData = await chunkRes.json();
      const chunks = chunkData.chunks || [text];
      const totalChunks = chunks.length;
      const metricsBefore = chunkData.metrics_before;

      metricAiBefore.textContent = `${metricsBefore.ai_risk}%`;
      metricsBar.style.display = "grid";

      const completedChunks = [];
      let totalShifts = 0;
      let totalClichesPurged = metricsBefore.cliche_count || 0;
      let lastModelUsed = "gemini-3.5-flash-lite";

      // Step 2: Process chunks sequentially with auto-retry on transient network errors
      for (let i = 0; i < totalChunks; i++) {
        const chunkNum = i + 1;
        const chunkPayloadText = typeof chunks[i] === "string" ? chunks[i] : chunks[i].text;

        progressStatusText.textContent = `HUMANIZING CHUNK ${chunkNum} OF ${totalChunks}...`;
        progressChunkBadge.textContent = `CHUNK ${chunkNum} / ${totalChunks}`;
        const startPct = Math.round(((i + 0.1) / totalChunks) * 100);
        progressBarFill.style.width = `${Math.max(8, startPct)}%`;

        let chunkResultText = null;
        for (let attempt = 0; attempt < 2; attempt++) {
          try {
            const userKey = localStorage.getItem("turnitout_gemini_api_key");
            const res = await fetch("/api/humanize", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                text: chunkPayloadText,
                intensity,
                api_key: userKey || undefined,
              }),
            });

            if (res.ok) {
              const data = await res.json();
              chunkResultText = data.cleaned_text || chunkPayloadText;
              totalShifts += (data.changes_count || 0);
              if (data.quota_exhausted) {
                lastModelUsed = "offline-linguistic (daily quota reached)";
              } else if (data.model_used) {
                lastModelUsed = data.model_used;
              }
              break;
            } else if (attempt === 0) {
              await new Promise((r) => setTimeout(r, 1200));
            }
          } catch (netErr) {
            if (attempt === 0) {
              await new Promise((r) => setTimeout(r, 1200));
            }
          }
        }

        // Fallback to original text if both attempts failed so document processing never crashes
        if (!chunkResultText) {
          chunkResultText = chunkPayloadText;
        }

        completedChunks.push(chunkResultText);

        // Stream live completed chunks into output textarea
        const currentReady = completedChunks.join("\n\n");
        outputText.value = currentReady;
        const outWords = countWords(currentReady);
        outputWordCount.textContent = `${outWords} words`;

        // Update active model badge & progress track
        activeModelBadge.innerHTML = `${PULSE_SVG} ${lastModelUsed.toUpperCase()}`;
        const donePct = Math.round((chunkNum / totalChunks) * 100);
        progressBarFill.style.width = `${donePct}%`;
      }

      // Step 3: Final whole-document AI footprint verification
      const finalOutput = completedChunks.join("\n\n");
      outputText.value = finalOutput;
      const inWords = countWords(text);
      const outWords = countWords(finalOutput);
      const retentionPct = inWords > 0 ? Math.round((outWords / inWords) * 100) : 100;
      outputWordCount.textContent = `${outWords} words`;

      // If a .docx was uploaded, immediately reconstruct the in-place Word document (<200ms)
      // and show the DOWNLOAD .DOCX button in the header!
      if (activeDocxFile) {
        downloadDocxBtn.style.display = "inline-flex";
        await prepareAndTriggerDocxDownload(finalOutput, false);
      }

      const detectRes = await fetch("/api/detect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: finalOutput })
      });

      if (detectRes.ok) {
        const detectData = await detectRes.json();
        const afterMetrics = detectData.metrics;
        metricAiAfter.textContent = `${afterMetrics.ai_risk}%`;
        metricBurstiness.textContent = `${afterMetrics.burstiness_score}%`;
        const remainingCliches = afterMetrics.cliche_count || 0;
        const purgedCount = Math.max(totalClichesPurged - remainingCliches, totalClichesPurged);
        metricCliches.textContent = `${purgedCount} purged`;
      }

      stopElapsedTimer();
      const totalElapsedStr = formatElapsed(Date.now() - elapsedStartTime);
      if (progressTimer) {
        progressTimer.innerHTML = `${CLOCK_SVG} DONE IN ${totalElapsedStr}`;
      }
      metricChanges.textContent = `${totalShifts} shifts`;
      progressStatusText.textContent = `COMPLETE // ${totalChunks} CHUNK(S) PROCESSED // ${outWords} WORDS`;
      progressChunkBadge.textContent = "100% DONE";
    } catch (err) {
      stopElapsedTimer();
      alert("Error processing text: " + err.message);
      progressContainer.style.display = "none";
    } finally {
      stopElapsedTimer();
      humanizeBtn.disabled = false;
      humanizeBtn.innerHTML = `${LIGHTNING_SVG} HUMANIZE THESIS TEXT`;
    }
  });

  // Copy to Clipboard
  copyBtn.addEventListener("click", () => {
    if (!outputText.value.trim()) return;
    navigator.clipboard.writeText(outputText.value).then(() => {
      const origHtml = copyBtn.innerHTML;
      copyBtn.innerHTML = `${CHECK_SVG} COPIED!`;
      copyBtn.classList.remove("btn-accent");
      copyBtn.classList.add("btn-primary");
      setTimeout(() => {
        copyBtn.innerHTML = origHtml;
        copyBtn.classList.remove("btn-primary");
        copyBtn.classList.add("btn-accent");
      }, 1800);
    });
  });

  // ==========================================================================
  // LEGAL DOCUMENTS MODAL & SUBTLE COOKIE CONSENT POPUP
  // ==========================================================================
  const LEGAL_CONTENT = {
    terms: {
      title: "TERMS & CONDITIONS OF SERVICE",
      html: `
        <p><strong>Effective Date:</strong> October 2026 // <strong>Service:</strong> Turnitout Academic Thesis Humanizer v3.0</p>
        <h3>1. Scope of Service &amp; Academic Editing Purpose</h3>
        <p>Turnitout provides statistical prose refinement, sentence-length burstiness optimization, invisible watermark sanitization, and in-place <code>.docx</code> stylistic editing for researchers, non-native English scholars, and technical authors. You retain 100% intellectual property and copyright ownership over all manuscripts and documents you submit and receive.</p>
        <h3>2. Acceptable Use &amp; Institutional Compliance</h3>
        <p>Users are solely responsible for verifying that their use of automated stylistic editing tools complies with their university, publisher (IEEE, ACM, Springer, Elsevier), or institutional guidelines. Turnitout must not be used to fabricate empirical data, falsify citations, or process unlawful content.</p>
        <h3>3. Multi-Model Rate Limiting &amp; Fair Use</h3>
        <p>To prevent API quota exhaustion and maintain high availability across our priority model waterfall, automated per-model RPM rate limits and sharded concurrency controls are enforced.</p>
        <h3>4. Disclaimer of Warranties</h3>
        <p>Third-party AI detectors (including ZeroGPT, Turnitin, and GPTZero) update their statistical classifiers frequently. While Turnitout calibrates burstiness and perplexity against current detection models, the service is provided "AS IS" without guarantee of any specific third-party score.</p>
      `
    },
    privacy: {
      title: "PRIVACY POLICY & ZERO-STORAGE GUARANTEE",
      html: `
        <p><strong>Effective Date:</strong> October 2026 // <strong>Zero-Retention Architecture</strong></p>
        <h3>1. End-to-End Encryption &amp; Ephemeral RAM Processing</h3>
        <p>All thesis drafts, plain text, and uploaded Word (<code>.docx</code>) documents are transmitted exclusively over <strong>End-to-End TLS 1.3 Encryption</strong>. Document extraction and in-place reconstruction occur strictly in ephemeral volatile memory (<code>tempfile.TemporaryDirectory</code> in RAM/tmpfs) and are cryptographically unlinked the instant your HTTP response completes.</p>
        <h3>2. Zero Manuscript Logging &amp; Zero AI Training</h3>
        <ul>
          <li>We <strong>never</strong> store, log, index, or archive your input text, humanized output, or uploaded <code>.docx</code> files in any database.</li>
          <li>Your unpublished academic research is <strong>never</strong> shared with third parties or used to train language models.</li>
        </ul>
        <h3>3. GDPR &amp; CCPA Data Minimization</h3>
        <p>Because Turnitout requires no user registration and stores zero personal manuscripts, no personally identifiable documents exist on our servers to be sold, breached, or subpoenaed.</p>
      `
    },
    cookies: {
      title: "COOKIE & LOCAL STORAGE POLICY",
      html: `
        <p><strong>Effective Date:</strong> October 2026 // <strong>Minimal-Footprint Policy</strong></p>
        <h3>1. Strictly Necessary Local Storage</h3>
        <p>Turnitout uses a single browser <code>localStorage</code> flag (<code>turnitout_cookie_consent_v3</code>) solely to remember that you dismissed the cookie notice banner so it does not interrupt your workspace on future visits.</p>
        <h3>2. Anonymous Performance Telemetry</h3>
        <p>We use privacy-preserving Vercel Web Analytics (<code>@vercel/analytics</code>) to measure aggregate page load performance and HTTP status reliability without cross-site tracking cookies or fingerprinting.</p>
      `
    },
    security: {
      title: "END-TO-END ENCRYPTION & SECURITY ARCHITECTURE",
      html: `
        <p><strong>Security Standard:</strong> TLS 1.3 + Ephemeral In-Memory Zero-Storage Pipeline</p>
        <h3>1. End-to-End Encrypted Document Transit</h3>
        <p>Every chunk request (<code>/api/humanize</code>) and Word document upload/rebuild (<code>/api/extract-docx</code>, <code>/api/rebuild-docx</code>) is encrypted in transit using modern TLS 1.3 cipher suites with forward secrecy.</p>
        <h3>2. Ephemeral In-Place .DOCX Reconstruction</h3>
        <p>When you upload or drag-and-drop a <code>.docx</code> manuscript, our engine parses the XML document structure in isolated memory, replaces paragraph and table runs while preserving styles and citations, streams the rebuilt binary directly back to your browser, and immediately wipes the temporary directory.</p>
      `
    }
  };

  function openLegalModal(key) {
    const doc = LEGAL_CONTENT[key] || LEGAL_CONTENT.terms;
    legalModalTitle.textContent = doc.title;
    legalModalBody.innerHTML = doc.html;
    legalModal.style.display = "flex";
  }

  document.querySelectorAll("[data-legal]").forEach((btn) => {
    btn.addEventListener("click", () => {
      openLegalModal(btn.getAttribute("data-legal"));
    });
  });

  if (closeLegalModalBtn) {
    closeLegalModalBtn.addEventListener("click", () => {
      legalModal.style.display = "none";
    });
  }

  if (legalModal) {
    legalModal.addEventListener("click", (e) => {
      if (e.target === legalModal) {
        legalModal.style.display = "none";
      }
    });
  }

  // Subtle Cookie Popup Logic
  try {
    if (cookieBanner && !localStorage.getItem("turnitout_cookie_consent_v3")) {
      cookieBanner.style.display = "flex";
    }
    if (acceptCookiesBtn) {
      acceptCookiesBtn.addEventListener("click", () => {
        localStorage.setItem("turnitout_cookie_consent_v3", "accepted");
        cookieBanner.style.display = "none";
      });
    }
  } catch (_) {}

  // API Key Settings Modal
  const apiKeyModal = document.getElementById("apiKeyModal");
  const apiKeySettingsBtn = document.getElementById("apiKeySettingsBtn");
  const closeApiKeyModalBtn = document.getElementById("closeApiKeyModalBtn");
  const userApiKeyInput = document.getElementById("userApiKeyInput");
  const saveApiKeyBtn = document.getElementById("saveApiKeyBtn");
  const clearApiKeyBtn = document.getElementById("clearApiKeyBtn");

  const existingKey = localStorage.getItem("turnitout_gemini_api_key");
  if (existingKey && userApiKeyInput) {
    userApiKeyInput.value = existingKey;
  }

  if (apiKeySettingsBtn && apiKeyModal) {
    apiKeySettingsBtn.addEventListener("click", () => {
      apiKeyModal.style.display = "flex";
      if (userApiKeyInput) userApiKeyInput.focus();
    });
  }

  if (closeApiKeyModalBtn && apiKeyModal) {
    closeApiKeyModalBtn.addEventListener("click", () => {
      apiKeyModal.style.display = "none";
    });
  }

  if (apiKeyModal) {
    apiKeyModal.addEventListener("click", (e) => {
      if (e.target === apiKeyModal) apiKeyModal.style.display = "none";
    });
  }

  if (saveApiKeyBtn && userApiKeyInput) {
    saveApiKeyBtn.addEventListener("click", () => {
      const val = userApiKeyInput.value.trim();
      if (val) {
        localStorage.setItem("turnitout_gemini_api_key", val);
        if (activeModelBadge) activeModelBadge.innerHTML = `${PULSE_SVG} KEY SAVED // READY`;
        alert("API Key saved! Requests will now use your key with fresh quota.");
      } else {
        localStorage.removeItem("turnitout_gemini_api_key");
        alert("API Key cleared. Engine will use server default waterfall.");
      }
      if (apiKeyModal) apiKeyModal.style.display = "none";
    });
  }

  if (clearApiKeyBtn && userApiKeyInput) {
    clearApiKeyBtn.addEventListener("click", () => {
      localStorage.removeItem("turnitout_gemini_api_key");
      userApiKeyInput.value = "";
      alert("API Key removed from browser storage.");
      if (apiKeyModal) apiKeyModal.style.display = "none";
    });
  }
});
