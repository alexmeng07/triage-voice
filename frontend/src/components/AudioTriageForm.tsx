"use client";

import { useState, useRef } from "react";
import { createTriageVisitFromAudio, ApiError } from "@/lib/api";
import type { TriageVisitResponse } from "@/lib/types";
import { Mic, MicOff, Upload, AlertTriangle } from "lucide-react";

interface Props {
  patientId: number;
  onSubmit: (result: TriageVisitResponse) => void;
  loading: boolean;
}

/** Determine if the browser supports MediaRecorder for live recording. */
function supportsMediaRecorder(): boolean {
  return typeof window !== "undefined" && typeof MediaRecorder !== "undefined";
}

/** Get a sensible filename for a recorded blob (extension from mime type). */
function extensionForMime(mime: string): string {
  if (mime.includes("webm")) return "webm";
  if (mime.includes("mp4") || mime.includes("m4a")) return "m4a";
  if (mime.includes("ogg")) return "ogg";
  return "webm";
}

/** Pick best supported MediaRecorder mime type (Chrome: webm, Safari: mp4). */
function pickSupportedMimeType(): string | undefined {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4", // Safari
    "audio/ogg;codecs=opus",
    "audio/ogg",
  ];
  for (const m of candidates) {
    if (MediaRecorder.isTypeSupported(m)) return m;
  }
  return undefined;
}

/** Map microphone/getUserMedia errors to user-friendly messages. */
function formatMicrophoneError(err: unknown): string {
  if (err instanceof DOMException) {
    switch (err.name) {
      case "NotAllowedError":
        return "Microphone access denied. Check browser permissions and allow this site to use your mic.";
      case "NotFoundError":
        return "No microphone found. Connect a microphone or check device settings.";
      case "NotReadableError":
        return "Microphone is in use by another app, or the device may not be working.";
      case "OverconstrainedError":
        return "Microphone doesn't support required settings. Try using Upload File instead.";
      case "SecurityError":
        return "Microphone access requires HTTPS or localhost.";
      default:
        return err.message || "Could not access microphone.";
    }
  }
  return err instanceof Error ? err.message : "Could not access microphone.";
}

export default function AudioTriageForm({
  patientId,
  onSubmit,
  loading,
}: Props) {
  const [recording, setRecording] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isBusy = loading || submitting;

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || isBusy) return;

    setError(null);
    setSubmitting(true);
    try {
      const result = await createTriageVisitFromAudio(patientId, file);
      onSubmit(result);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail : "Audio triage failed",
      );
    } finally {
      setSubmitting(false);
    }
  };

  const startRecording = async () => {
    if (recording || isBusy) return;
    setError(null);
    try {
      // Try permissive constraints first — some built-in mics fail with strict defaults
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (gumErr) {
        // Fallback: request any audio input (helps some laptops / Windows)
        stream = await navigator.mediaDevices.getUserMedia({ audio: {} });
      }
      const mime = pickSupportedMimeType();
      const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (ev) => {
        if (ev.data.size > 0) chunksRef.current.push(ev.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const actualMime = recorder.mimeType || mime || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: actualMime });
        const ext = extensionForMime(actualMime);
        const file = new File([blob], `recording.${ext}`, { type: blob.type });
        setSubmitting(true);
        try {
          const result = await createTriageVisitFromAudio(patientId, file);
          onSubmit(result);
        } catch (err) {
          setError(
            err instanceof ApiError ? err.detail : "Audio triage failed",
          );
        } finally {
          setSubmitting(false);
        }
      };

      // Use timeslice to request data periodically — improves compatibility with some built-in mics
      recorder.start(1000);
      setRecording(true);
    } catch (err) {
      setError(formatMicrophoneError(err));
    }
  };

  const stopRecording = () => {
    if (!recording) return;
    const rec = mediaRecorderRef.current;
    if (rec && rec.state !== "inactive") {
      rec.stop();
    }
    setRecording(false);
  };

  const canRecord = supportsMediaRecorder();

  return (
    <div className="space-y-5">
      <p className="text-sm text-navy/60">
        Record the patient&apos;s complaint or upload an audio file. Supported:
        WAV, MP3, OGG, WebM, FLAC.
      </p>

      {error && (
        <div className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
          <AlertTriangle size={18} className="shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        {canRecord && (
          <>
            {!recording ? (
              <button
                type="button"
                onClick={startRecording}
                disabled={isBusy}
                className="inline-flex items-center gap-2 rounded-xl border border-navy/15 bg-white px-5 py-3 text-sm font-medium text-navy transition-colors hover:bg-navy/5 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Mic size={18} />
                Start Recording
              </button>
            ) : (
              <button
                type="button"
                onClick={stopRecording}
                className="inline-flex items-center gap-2 rounded-xl border-2 border-red-300 bg-red-50 px-5 py-3 text-sm font-medium text-red-700 transition-colors hover:bg-red-100 cursor-pointer animate-pulse"
              >
                <MicOff size={18} />
                Stop Recording
              </button>
            )}
          </>
        )}

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isBusy || recording}
          className="inline-flex items-center gap-2 rounded-xl border border-navy/15 bg-white px-5 py-3 text-sm font-medium text-navy transition-colors hover:bg-navy/5 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Upload size={18} />
          Upload File
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/wav,audio/x-wav,audio/mpeg,audio/mp3,audio/ogg,audio/webm,audio/flac"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {recording && (
        <p className="text-xs text-navy/50 italic">
          Recording in progress… Speak clearly, then click Stop when finished.
        </p>
      )}

      {isBusy && (
        <div className="flex items-center gap-2 text-sm text-navy/60">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-navy/20 border-t-navy" />
          Transcribing and running triage…
        </div>
      )}
    </div>
  );
}
