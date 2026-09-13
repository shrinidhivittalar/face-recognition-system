import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { AddSampleCapture } from "../components/AddSampleCapture";
import { CameraCapture } from "../components/CameraCapture";
import { StatusPanel } from "../components/StatusPanel";
import { enroll } from "../api/client";
import { ApiError, type EnrollResponse } from "../types";

type Stage = "capture" | "processing" | "success" | "error";

/** Photos per identity below which we still nudge for more. */
const RECOMMENDED_SAMPLES = 3;

export function Enroll() {
  const [displayName, setDisplayName] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [capturedImage, setCapturedImage] = useState<Blob | null>(null);
  const [stage, setStage] = useState<Stage>("capture");
  const [errorMessage, setErrorMessage] = useState("");
  const [result, setResult] = useState<EnrollResponse | null>(null);
  const [sampleCount, setSampleCount] = useState(0);

  const handleCapture = useCallback((image: Blob, preview: string) => {
    setCapturedImage(image);
    setPreviewUrl(preview);
  }, []);

  const handleReset = useCallback(() => {
    setStage("capture");
    setCapturedImage(null);
    setPreviewUrl(null);
    setDisplayName("");
    setErrorMessage("");
    setResult(null);
    setSampleCount(0);
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!capturedImage || !displayName.trim()) return;

    setStage("processing");
    try {
      const response = await enroll(displayName.trim(), capturedImage);
      setResult(response);
      setSampleCount(1);
      setStage("success");
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Something went wrong. Please try again.");
      }
      setStage("error");
    }
  }, [capturedImage, displayName]);

  const canSubmit = Boolean(capturedImage) && displayName.trim().length > 0;

  return (
    <div className="page page-enroll">
      <h1>Enroll Person</h1>

      {stage === "success" && result ? (
        <div className="enroll-success">
          <StatusPanel
            variant="success"
            title="Enrollment Successful"
            message={`${result.display_name} has been enrolled — ${sampleCount} ${
              sampleCount === 1 ? "photo" : "photos"
            } on file.`}
          >
            <div className="action-row">
              <button className="btn btn-primary" onClick={handleReset}>
                Enroll Another Person
              </button>
              <Link className="btn btn-secondary" to="/identify">
                Go to Identify
              </Link>
            </div>
          </StatusPanel>

          <section className="add-sample-section">
            <h2>Add more photos</h2>
            {sampleCount < RECOMMENDED_SAMPLES ? (
              <p className="hint">
                A single photo captures one pose and one lighting condition. Adding a
                few more — turned slightly left and right, or under different lighting —
                makes {result.display_name} much less likely to be missed later.
              </p>
            ) : (
              <p className="hint">
                {result.display_name} has {sampleCount} photos on file. You can keep
                adding more, or finish here.
              </p>
            )}
            <AddSampleCapture
              identityId={result.identity_id}
              displayName={result.display_name}
              onSampleAdded={() => setSampleCount((n) => n + 1)}
            />
          </section>
        </div>
      ) : (
        <div className="enroll-form">
          <label className="field">
            <span>Identity Name</span>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g. Jane Doe"
              disabled={stage === "processing"}
              maxLength={255}
            />
          </label>

          {previewUrl ? (
            <div className="preview-frame">
              <img src={previewUrl} alt="Captured preview" />
              <button
                type="button"
                className="btn btn-text"
                onClick={() => {
                  setCapturedImage(null);
                  setPreviewUrl(null);
                }}
                disabled={stage === "processing"}
              >
                Retake
              </button>
            </div>
          ) : (
            <CameraCapture onCapture={handleCapture} disabled={stage === "processing"} />
          )}

          {stage === "error" && <StatusPanel variant="error" title="Enrollment Failed" message={errorMessage} />}

          <button
            type="button"
            className="btn btn-primary btn-block"
            onClick={handleSubmit}
            disabled={!canSubmit || stage === "processing"}
          >
            {stage === "processing" ? "Processing..." : "Enroll"}
          </button>

          <p className="hint">Make sure exactly one face is clearly visible in the photo.</p>
        </div>
      )}
    </div>
  );
}
