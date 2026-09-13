import { useCallback, useState } from "react";
import { CameraCapture } from "./CameraCapture";
import { StatusPanel } from "./StatusPanel";
import { addSample } from "../api/client";
import { ApiError } from "../types";

interface AddSampleCaptureProps {
  identityId: string;
  displayName: string;
  /** Called after each successfully added sample, so parents can refresh counts. */
  onSampleAdded?: () => void;
}

type Stage = "capture" | "processing" | "added" | "error";

/**
 * Captures an additional face sample for an already-enrolled identity.
 *
 * Multiple samples are how an identity survives changes in pose and lighting:
 * a single enrollment photo generalizes poorly, and without this the only
 * remedy for a mis-recognized person is to delete and re-enroll them.
 */
export function AddSampleCapture({ identityId, displayName, onSampleAdded }: AddSampleCaptureProps) {
  const [stage, setStage] = useState<Stage>("capture");
  const [errorMessage, setErrorMessage] = useState("");

  const handleCapture = useCallback(
    async (image: Blob) => {
      setStage("processing");
      try {
        await addSample(identityId, image);
        setStage("added");
        onSampleAdded?.();
      } catch (err) {
        setErrorMessage(
          err instanceof ApiError ? err.message : "Something went wrong. Please try again."
        );
        setStage("error");
      }
    },
    [identityId, onSampleAdded]
  );

  if (stage === "processing") {
    return <StatusPanel variant="processing" title="Adding photo..." message="Detecting and encoding the face." />;
  }

  if (stage === "added") {
    return (
      <StatusPanel variant="success" title="Photo added" message={`Another photo was added for ${displayName}.`}>
        <div className="action-row">
          <button type="button" className="btn btn-secondary" onClick={() => setStage("capture")}>
            Add Another Photo
          </button>
        </div>
      </StatusPanel>
    );
  }

  return (
    <div className="add-sample">
      {stage === "error" && <StatusPanel variant="error" title="Could not add photo" message={errorMessage} />}
      <CameraCapture onCapture={handleCapture} />
      <p className="hint">
        Vary the angle and lighting between photos — that is what makes recognition robust.
        Exactly one face must be visible.
      </p>
    </div>
  );
}
