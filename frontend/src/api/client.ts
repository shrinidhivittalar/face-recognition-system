import type {
  ApiErrorBody,
  EnrollResponse,
  IdentifyResponse,
  IdentityOut,
  SampleAddedResponse,
} from "../types";
import { ApiError } from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let body: ApiErrorBody;
    try {
      body = await response.json();
    } catch {
      body = { error: "unknown_error", message: "Something went wrong. Please try again." };
    }
    throw new ApiError(response.status, body);
  }
  return response.json() as Promise<T>;
}

export async function enroll(displayName: string, image: Blob): Promise<EnrollResponse> {
  const form = new FormData();
  form.append("display_name", displayName);
  form.append("image", image, "capture.jpg");

  const response = await fetch(`${BASE_URL}/api/v1/enroll`, { method: "POST", body: form });
  return handleResponse<EnrollResponse>(response);
}

export async function addSample(identityId: string, image: Blob): Promise<SampleAddedResponse> {
  const form = new FormData();
  form.append("image", image, "capture.jpg");

  const response = await fetch(`${BASE_URL}/api/v1/identities/${identityId}/samples`, {
    method: "POST",
    body: form,
  });
  return handleResponse<SampleAddedResponse>(response);
}

export async function identify(image: Blob): Promise<IdentifyResponse> {
  const form = new FormData();
  form.append("image", image, "capture.jpg");

  const response = await fetch(`${BASE_URL}/api/v1/identify`, { method: "POST", body: form });
  return handleResponse<IdentifyResponse>(response);
}

export async function listIdentities(): Promise<IdentityOut[]> {
  const response = await fetch(`${BASE_URL}/api/v1/identities`);
  return handleResponse<IdentityOut[]>(response);
}

export async function deleteIdentity(identityId: string): Promise<void> {
  const response = await fetch(`${BASE_URL}/api/v1/identities/${identityId}`, { method: "DELETE" });
  if (!response.ok && response.status !== 204) {
    const body = await response.json();
    throw new ApiError(response.status, body);
  }
}

export async function checkHealth(): Promise<{ status: string; database: string; model: string }> {
  const response = await fetch(`${BASE_URL}/health`);
  return handleResponse(response);
}
