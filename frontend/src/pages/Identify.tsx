import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { CameraCapture } from "../components/CameraCapture";
import { StatusPanel } from "../components/StatusPanel";
import { identify } from "../api/client";
import { ApiError, type IdentifyResponse } from "../types";

type Stage = "capture" | "processing" | "result" | "error";

export function Identify() {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [capturedImage, setCapturedImage] = useState<Blob | null>(null);
  const [stage, setStage] = useState<Stage>("capture");
  const [errorMessage, setErrorMessage] = useState("");
  const [result, setResult] = useState<IdentifyResponse | null>(null);

  const handleCapture = useCallback(async (image: Blob, preview: string) => {
    setCapturedImage(image);
    setPreviewUrl(preview);
    setStage("processing");
    try {
      const response = await identify(image);
      setResult(response);
      setStage("result");
    } catch (err) {
      setErrorMessage(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      setStage("error");
    }
  }, []);

  const handleReset = useCallback(() => {
    setStage("capture");
    setCapturedImage(null);
    setPreviewUrl(null);
    setErrorMessage("");
    setResult(null);
  }, []);

  return (
    <div className="page page-identify">
      <h1>Identify Face</h1>

      {stage === "capture" && <CameraCapture onCapture={handleCapture} />}

      {stage === "processing" && (
        <div className="preview-frame">
          {previewUrl && <img src={previewUrl} alt="Captured preview" />}
          <StatusPanel variant="processing" title="Analyzing..." message="Detecting and matching the face." />
        </div>
      )}

      {stage === "result" && result && (
        <div className="preview-frame">
          {previewUrl && <img src={previewUrl} alt="Captured preview" />}
          {result.outcome === "known" ? (
            <StatusPanel variant="success" title="KNOWN" message={`Matched: ${result.display_name}`}>
              <p className="hint">Match accepted.</p>
            </StatusPanel>
          ) : (
            <StatusPanel variant="warning" title="UNKNOWN" message="No enrolled identity matched this face.">
              <div className="action-row">
                <Link className="btn btn-secondary" to="/enroll">
                  Enroll Person
                </Link>
              </div>
            </StatusPanel>
          )}
          <button type="button" className="btn btn-primary btn-block" onClick={handleReset}>
            Identify Again
          </button>
        </div>
      )}

      {stage === "error" && (
        <div className="preview-frame">
          <StatusPanel variant="error" title="Identification Failed" message={errorMessage} />
          <button type="button" className="btn btn-primary btn-block" onClick={handleReset}>
            Try Again
          </button>
        </div>
      )}

      {capturedImage === null && stage === "capture" && (
        <p className="hint">Make sure exactly one face is clearly visible in the photo.</p>
      )}
    </div>
  );
}
