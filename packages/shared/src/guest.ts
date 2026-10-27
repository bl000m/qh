/** QH-20: no context or invited email is disclosed before mailbox verification. */
export type GuestRight = 'READ' | 'ASK_AI';

export interface GuestInvitationCreated {
  id: string;
  snapshot_id: string;
  expires_at: string;
  /** Owner-only, returned once. Put in a URL fragment, never a path/query/log. */
  invitation_token: string;
}

export interface GuestCodeRequest {
  invitation_token: string;
  email: string;
}

export interface GuestCodeReceipt {
  challenge_id: string;
  message: string;
}

export interface GuestVerifyRequest {
  invitation_token: string;
  challenge_id: string;
  code: string;
}

export interface GuestSessionView {
  snapshot_id: string;
  rights: GuestRight[];
  expires_at: string;
  verification: 'mailbox_control';
}

export interface SharingPolicy {
  recipient_email:string; purpose:string; rights:GuestRight[]; expires_at:string;
  include_proposed:boolean; include_quotes:boolean; provider:'offline'|'mistral-small-2603'|null;
}
export interface SharedItem {
  reference:string; text:string; validation_state:'proposed'|'confirmed'; origin_kind:string;
  sources:string[]; citations?:{source:string;quote:string;redacted:boolean}[];
  primary_dimension?:{value:string;certainty:string;review_state:string};
}
export interface SharedPayload {format:'qh.disclosure/1';items:SharedItem[];recap?:{title:string;text:string}}
export interface SharingPreview {
  id:string;fingerprint:string;policy:SharingPolicy;payload:SharedPayload;
  report:{status:string;message:string;warning:string;risks:string[];
    exclusions:{revision_id:string;reason:string}[];masks:{reference:string;rules:string[]}[]};
}
export interface GuestProviderStatus {model:'offline'|'mistral-small-2603';enabled:boolean;simulated:boolean;remaining_usd?:string|null;plafond_reached?:boolean;authorized_total_eur?:string;budget_scope?:'development_global'}
export interface GuestAnswer {simulated:boolean;model?:'mistral-small-2603';answer:string;reference_aliases:string[];insufficient_context:boolean;support_basis?:'dialogue'|'canonical'|'mixed'|'insufficient';budget?:GuestProviderStatus;accounting?:{attempt:number;cost_usd:string;usage:{prompt_tokens:number;completion_tokens:number}}}
