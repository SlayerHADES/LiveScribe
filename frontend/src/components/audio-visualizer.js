/**
 * AudioVisualizer — Canvas-based audio waveform visualization engine.
 *
 * Renders real-time audio amplitudes from an AnalyserNode or simulated
 * flowing waveforms for idle/demo states.
 *
 * States: IDLE, LISTENING, PAUSED, PROCESSING, COMPLETE
 */

export class AudioVisualizer {
  /**
   * @param {HTMLCanvasElement} canvas
   * @param {Object} [opts]
   */
  constructor(canvas, opts = {}) {
    this.canvas = canvas;
    this.ctx = canvas ? canvas.getContext("2d") : null;
    this.state = opts.state || "IDLE";
    this.analyser = null;
    this.dataArray = null;
    this.animationId = null;
    this.phase = 0;

    if (this.canvas) {
      this._resize();
      window.addEventListener("resize", () => this._resize());
    }
  }

  _resize() {
    if (!this.canvas) return;
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    if (this.ctx) {
      this.ctx.scale(dpr, dpr);
    }
    this.width = rect.width;
    this.height = rect.height;
  }

  /**
   * Attach a Web Audio AnalyserNode for real mic visualization.
   * @param {AnalyserNode} analyser
   */
  setAnalyser(analyser) {
    this.analyser = analyser;
    if (this.analyser) {
      this.analyser.fftSize = 128;
      const bufferLength = this.analyser.frequencyBinCount;
      this.dataArray = new Uint8Array(bufferLength);
    }
  }

  setState(state) {
    this.state = state;
  }

  start() {
    if (this.animationId) return;
    const render = () => {
      this._draw();
      this.animationId = requestAnimationFrame(render);
    };
    render();
  }

  stop() {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  _draw() {
    if (!this.ctx || !this.width || !this.height) return;

    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    const centerY = h / 2;

    ctx.clearRect(0, 0, w, h);
    this.phase += 0.05;

    if (this.state === "IDLE") {
      this._drawIdle(ctx, w, h, centerY);
    } else if (this.state === "LISTENING") {
      this._drawListening(ctx, w, h, centerY);
    } else if (this.state === "PAUSED") {
      this._drawPaused(ctx, w, h, centerY);
    } else if (this.state === "PROCESSING") {
      this._drawProcessing(ctx, w, h, centerY);
    } else if (this.state === "COMPLETE") {
      this._drawComplete(ctx, w, h, centerY);
    }
  }

  _drawIdle(ctx, w, h, centerY) {
    ctx.beginPath();
    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.lineWidth = 1.5;

    for (let x = 0; x < w; x += 4) {
      const y = centerY + Math.sin(x * 0.02 + this.phase) * 2;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  _drawListening(ctx, w, h, centerY) {
    // Get frequency data if analyser present
    let rawAmplitudes = [];
    if (this.analyser && this.dataArray) {
      this.analyser.getByteFrequencyData(this.dataArray);
      for (let i = 0; i < this.dataArray.length; i++) {
        rawAmplitudes.push(this.dataArray[i] / 255);
      }
    }

    const bars = 48;
    const barWidth = 3;
    const gap = (w - bars * barWidth) / (bars + 1);

    // Glowing background aura
    const grad = ctx.createLinearGradient(0, 0, w, 0);
    grad.addColorStop(0, "rgba(56, 189, 248, 0.15)");
    grad.addColorStop(0.5, "rgba(129, 140, 248, 0.25)");
    grad.addColorStop(1, "rgba(168, 85, 247, 0.15)");

    ctx.fillStyle = grad;
    ctx.fillRect(0, centerY - h / 3, w, (h * 2) / 3);

    // Waveform bars
    for (let i = 0; i < bars; i++) {
      const x = gap + i * (barWidth + gap);
      let amp = 0.2;

      if (rawAmplitudes.length > 0) {
        const idx = Math.floor((i / bars) * rawAmplitudes.length);
        amp = rawAmplitudes[idx] || 0.1;
      } else {
        // Simulated amplitude
        amp = 0.15 + Math.sin(i * 0.3 + this.phase * 2) * 0.35 + Math.cos(i * 0.1 + this.phase) * 0.2;
        amp = Math.max(0.08, Math.abs(amp));
      }

      const barHeight = Math.min(h * 0.8, amp * h * 0.75 + 4);

      // Bar color gradient
      const barGrad = ctx.createLinearGradient(0, centerY - barHeight / 2, 0, centerY + barHeight / 2);
      barGrad.addColorStop(0, "#38bdf8");
      barGrad.addColorStop(0.5, "#818cf8");
      barGrad.addColorStop(1, "#a855f7");

      ctx.fillStyle = barGrad;
      ctx.shadowColor = "#38bdf8";
      ctx.shadowBlur = 8;

      ctx.beginPath();
      ctx.roundRect(x, centerY - barHeight / 2, barWidth, barHeight, 2);
      ctx.fill();

      ctx.shadowBlur = 0;
    }
  }

  _drawPaused(ctx, w, h, centerY) {
    ctx.beginPath();
    ctx.strokeStyle = "rgba(245, 158, 11, 0.4)";
    ctx.lineWidth = 2;

    for (let x = 0; x < w; x += 6) {
      const y = centerY + Math.sin(x * 0.05) * 4;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  _drawProcessing(ctx, w, h, centerY) {
    const time = this.phase * 2;
    ctx.save();
    ctx.translate(w / 2, centerY);

    for (let i = 0; i < 3; i++) {
      ctx.beginPath();
      const radius = 12 + i * 14 + Math.sin(time + i) * 4;
      ctx.arc(0, 0, radius, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(129, 140, 248, ${0.6 - i * 0.18})`;
      ctx.lineWidth = 2;
      ctx.stroke();
    }
    ctx.restore();
  }

  _drawComplete(ctx, w, h, centerY) {
    ctx.beginPath();
    ctx.strokeStyle = "rgba(16, 185, 129, 0.4)";
    ctx.lineWidth = 2;

    for (let x = 0; x < w; x += 4) {
      const y = centerY + Math.sin(x * 0.01) * 3;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
}
