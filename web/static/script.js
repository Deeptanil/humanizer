document.addEventListener("DOMContentLoaded", () => {
  // Theme Toggle
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  themeToggleBtn.addEventListener("click", () => {
    document.body.classList.toggle("theme-light");
    document.body.classList.toggle("theme-dark");
  });

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

  // Progress HUD
  const progressContainer = document.getElementById("progressContainer");
  const progressStatusText = document.getElementById("progressStatusText");
  const progressChunkBadge = document.getElementById("progressChunkBadge");
  const progressBarFill = document.getElementById("progressBarFill");

  // Metrics
  const metricsBar = document.getElementById("metricsBar");
  const metricAiBefore = document.getElementById("metricAiBefore");
  const metricAiAfter = document.getElementById("metricAiAfter");
  const metricBurstiness = document.getElementById("metricBurstiness");
  const metricCliches = document.getElementById("metricCliches");
  const metricChanges = document.getElementById("metricChanges");

  // SVGs for dynamic buttons (Strict Zero-Emoji Policy)
  const LIGHTNING_SVG = '<svg class="svg-icon" viewBox="0 0 24 24" width="16" height="16" fill="currentColor" stroke="currentColor" stroke-width="1.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>';
  const PULSE_SVG = '<svg class="svg-icon" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>';
  const CHECK_SVG = '<svg class="svg-icon" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';

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
    inputWordCount.textContent = `${countWords(inputText.value)} words`;
  });

  clearBtn.addEventListener("click", () => {
    inputText.value = "";
    outputText.value = "";
    inputWordCount.textContent = "0 words";
    outputWordCount.textContent = "0 words";
    metricsBar.style.display = "none";
    progressContainer.style.display = "none";
  });

  // Multi-Chunk 10,000+ Word Streaming Humanizer
  humanizeBtn.addEventListener("click", async () => {
    const text = inputText.value.trim();
    if (!text) {
      alert("Please paste your thesis text to humanize.");
      return;
    }

    humanizeBtn.disabled = true;
    humanizeBtn.innerHTML = `${LIGHTNING_SVG} HUMANIZING THESIS...`;
    outputText.value = "";
    outputWordCount.textContent = "0 words";

    progressContainer.style.display = "flex";
    progressBarFill.style.width = "5%";
    progressStatusText.textContent = "ANALYZING & SPLITTING DOCUMENT INTO PARAGRAPH CHUNKS...";
    progressChunkBadge.textContent = "PREPARING";

    try {
      const intensity = parseInt(intensitySlider.value, 10) / 100.0;

      // Step 1: Split document into safe ~260-word chunks + get baseline AI risk
      const chunkRes = await fetch("/api/chunk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, max_words_per_chunk: 260 })
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
      let lastModelUsed = "deterministic-3layer";

      // Step 2: Process each chunk sequentially and stream into output pane
      for (let i = 0; i < totalChunks; i++) {
        const chunkNum = i + 1;
        const pct = Math.round(((i + 0.2) / totalChunks) * 100);
        progressBarFill.style.width = `${Math.max(8, pct)}%`;
        progressChunkBadge.textContent = `CHUNK ${chunkNum} / ${totalChunks}`;
        progressStatusText.textContent = `REWRITING CHUNK ${chunkNum} OF ${totalChunks} VIA PRIORITY WATERFALL...`;

        const chunkPayloadText = typeof chunks[i] === "string" ? chunks[i] : chunks[i].text;
        const res = await fetch("/api/humanize", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: chunkPayloadText, intensity })
        });

        if (!res.ok) {
          throw new Error(`Humanize error on chunk ${chunkNum} (HTTP ${res.status})`);
        }

        const data = await res.json();
        completedChunks.push(data.cleaned_text);
        totalShifts += (data.changes_count || 0);
        if (data.model_used) {
          lastModelUsed = data.model_used;
        }

        // Stream live result into textarea
        const currentFullOutput = completedChunks.join("\n\n");
        outputText.value = currentFullOutput;
        const outWords = countWords(currentFullOutput);
        outputWordCount.textContent = `${outWords} words`;

        // Update active model badge
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
      outputWordCount.textContent = `${outWords} words (${retentionPct}%)`;

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

      metricChanges.textContent = `${totalShifts} shifts`;
      progressStatusText.textContent = `COMPLETE // ${totalChunks} CHUNK(S) PROCESSED // ${outWords} WORDS`;
      progressChunkBadge.textContent = "100% DONE";
    } catch (err) {
      alert("Error processing text: " + err.message);
      progressContainer.style.display = "none";
    } finally {
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
});
