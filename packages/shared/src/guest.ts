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
