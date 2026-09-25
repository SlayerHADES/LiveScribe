/**
 * AudioRecorder — Mic capture, resampling to 16kHz, and WebSocket streaming.
 *
 * Usage:
 *   const recorder = new AudioRecorder({
 *     onTranscript: (data) => console.log(data),
 *     onStatus: (msg) => console.log(msg),
 *     onError: (err) => console.error(err),
 *     chunkDurationSec: 5,
 *   });
 *   await recorder.start();
 *   recorder.stop();
 */

const TARGET_SAMPLE_RATE = 16000;
const DEFAULT_CHUNK_DURATION = 5; // seconds

export class AudioRecorder {
  /**
   * @param {Object} opts
   * @param {function} opts.onTranscript - Called with transcript_chunk / silence JSON
   * @param {function} opts.onStatus     - Called with status messages
   * @param {function} opts.onError      - Called with error messages
   * @param {number}   [opts.chunkDurationSec=5]
   */
  constructor({ onTranscript, onStatus, onError, chunkDurationSec }) {
    this.onTranscript = onTranscript || (() => {});
    this.onStatus = onStatus || (() => {});
    this.onError = onError || (() => {});
    this.chunkDurationSec = chunkDurationSec || DEFAULT_CHUNK_DURATION;

    this.audioContext = null;
    this.stream = null;
    this.sourceNode = null;
    this.processorNode = null;
    this.ws = null;

    this.buffer = [];
    this.bufferSampleCount = 0;
    this.isRecording = false;
    this._nativeSampleRate = 0;
  }

  /**
   * Request mic access, connect to the transcription WebSocket, and start
   * capturing audio in rolling chunks.
   */
  async start() {
    if (this.isRecording) return;

    // 1. Get mic access
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: { ideal: TARGET_SAMPLE_RATE },
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
    } catch (err) {
      this.onError(`Microphone access denied: ${err.message}`);
      return;
    }

    // 2. Set up AudioContext
    this.audioContext = new AudioContext();
    this._nativeSampleRate = this.audioContext.sampleRate;
    this.sourceNode = this.audioContext.createMediaStreamSource(this.stream);

    // ScriptProcessorNode captures raw PCM samples
    // Buffer size 4096 gives ~93ms chunks at 44.1kHz — frequent enough for smooth capture
    this.processorNode = this.audioContext.createScriptProcessor(4096, 1, 1);
    this.processorNode.onaudioprocess = (event) => {
      if (!this.isRecording) return;

      const samples = event.inputBuffer.getChannelData(0);
      // Copy the samples (the buffer is reused by the AudioContext)
      this.buffer.push(new Float32Array(samples));
      this.bufferSampleCount += samples.length;

      // When we've accumulated enough for one chunk, send it
      const chunkSamples = this._nativeSampleRate * this.chunkDurationSec;
      if (this.bufferSampleCount >= chunkSamples) {
        this._flushBuffer();
      }
    };

    this.sourceNode.connect(this.processorNode);
    this.processorNode.connect(this.audioContext.destination);

    // 3. Connect WebSocket
    this._connectWebSocket();

    this.isRecording = true;
    this.onStatus("Recording started");
  }

  /**
   * Stop recording and clean up resources.
   */
  stop() {
    if (!this.isRecording) return;
    this.isRecording = false;

    // Send any remaining audio
    if (this.bufferSampleCount > 0) {
      this._flushBuffer();
    }

    // Clean up audio
    this.processorNode?.disconnect();
    this.sourceNode?.disconnect();
    this.stream?.getTracks().forEach((track) => track.stop());
    this.audioContext?.close();

    // Clean up WebSocket (allow last messages to flush)
    setTimeout(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.close();
      }
    }, 1000);

    this.audioContext = null;
    this.stream = null;
    this.sourceNode = null;
    this.processorNode = null;
    this.buffer = [];
    this.bufferSampleCount = 0;

    this.onStatus("Recording stopped");
  }

  // ─── Private ──────────────────────────────────────────────────────────

  _connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/transcribe`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.onStatus("Connected to transcription service");
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "status") {
          this.onStatus(data.message);
        } else if (data.type === "error") {
          this.onError(data.message);
        } else if (data.type === "transcript_chunk" || data.type === "silence") {
          this.onTranscript(data);
        }
      } catch (err) {
        console.warn("[AudioRecorder] Failed to parse message:", err);
      }
    };

    this.ws.onerror = (err) => {
      this.onError("WebSocket connection error");
      console.error("[AudioRecorder] WebSocket error:", err);
    };

    this.ws.onclose = () => {
      this.onStatus("Disconnected from transcription service");
    };
  }

  /**
   * Concatenate the buffered PCM samples, resample to 16kHz, and send
   * as a binary WebSocket message.
   */
  async _flushBuffer() {
    if (this.buffer.length === 0) return;

    // Concatenate all buffered Float32Arrays
    const fullBuffer = new Float32Array(this.bufferSampleCount);
    let offset = 0;
    for (const chunk of this.buffer) {
      fullBuffer.set(chunk, offset);
      offset += chunk.length;
    }
    this.buffer = [];
    this.bufferSampleCount = 0;

    // Resample to 16kHz
    let resampled;
    try {
      resampled = await this._resample(
        fullBuffer,
        this._nativeSampleRate,
        TARGET_SAMPLE_RATE
      );
    } catch (err) {
      console.warn("[AudioRecorder] Resampling failed:", err);
      return;
    }

    // Send as binary if WebSocket is open
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(resampled.buffer);
    }
  }

  /**
   * Resample audio data using OfflineAudioContext.
   *
   * @param {Float32Array} audioData - Input samples
   * @param {number} fromRate - Input sample rate
   * @param {number} toRate - Output sample rate
   * @returns {Promise<Float32Array>} Resampled audio
   */
  async _resample(audioData, fromRate, toRate) {
    if (fromRate === toRate) return audioData;

    const ratio = toRate / fromRate;
    const newLength = Math.round(audioData.length * ratio);

    const offlineCtx = new OfflineAudioContext(1, newLength, toRate);
    const buffer = offlineCtx.createBuffer(1, audioData.length, fromRate);
    buffer.getChannelData(0).set(audioData);

    const source = offlineCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(offlineCtx.destination);
    source.start(0);

    const rendered = await offlineCtx.startRendering();
    return rendered.getChannelData(0);
  }
}
