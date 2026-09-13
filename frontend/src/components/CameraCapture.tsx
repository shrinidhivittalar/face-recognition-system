import { useCallback, useEffect, useRef, useState } from "react";

interface CameraCaptureProps {
  onCapture: (image: Blob, previewUrl: string) => void;
  disabled?: boolean;
}

export function CameraCapture({ onCapture, disabled }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } },
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        setCameraReady(true);
      } catch {
        setCameraError("Camera unavailable. You can upload a photo instead.");
      }
    }

    startCamera();

    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const handleCapture = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (blob) onCapture(blob, canvas.toDataURL("image/jpeg"));
      },
      "image/jpeg",
      0.92
    );
  }, [onCapture]);

  const handleFileUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const url = URL.createObjectURL(file);
      onCapture(file, url);
      e.target.value = "";
    },
    [onCapture]
  );

  return (
    <div className="camera-capture">
      <div className="camera-frame">
        {cameraError ? (
          <div className="camera-placeholder">{cameraError}</div>
        ) : (
          <>
            <video ref={videoRef} autoPlay playsInline muted className="camera-video" />
            <div className="face-guide" aria-hidden="true" />
          </>
        )}
      </div>
      <div className="camera-actions">
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleCapture}
          disabled={disabled || !cameraReady}
        >
          Capture
        </button>
        <label className="btn btn-secondary">
          Upload Photo
          <input type="file" accept="image/*" hidden onChange={handleFileUpload} disabled={disabled} />
        </label>
      </div>
    </div>
  );
}
