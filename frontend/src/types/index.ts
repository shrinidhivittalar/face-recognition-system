export interface EnrollResponse {
  identity_id: string;
  display_name: string;
  detection_score: number;
}

export interface SampleAddedResponse {
  identity_id: string;
  sample_id: string;
  detection_score: number;
}

export interface IdentifyResponse {
  outcome: "known" | "unknown";
  identity_id: string | null;
  display_name: string | null;
}

export interface IdentityOut {
  id: string;
  display_name: string;
  created_at: string;
  sample_count: number;
}

export interface ApiErrorBody {
  error: string;
  message: string;
}

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.code = body.error;
    this.status = status;
  }
}
