/** Public Context Space V0.2 wire contracts. Imported assertions remain unverified. */
export type ContextDimension='situation_information'|'objectives_intentions'|'decisions_actions'|'constraints_preferences'|'hypotheses_uncertainties'|'open_questions';
export interface ContextOrigin {
 schema_version:'qh.context-space/1';logical_id:string;name:string;version:number;consolidated_at:string;
 understanding:{id:string;text:string;primary_dimension:ContextDimension|null;certainty:'asserted'|'tentative'|null;validation_state:'proposed'|'confirmed'|'rejected';evidence:{source_revision_id:string;quote:string;turn_id:string|null}[]}[];
}
export interface PortableContext extends ContextOrigin {ancestry?:ContextOrigin[]}
export interface AnswerAttribution {
 model:string;support_basis:'dialogue'|'canonical'|'mixed'|'insufficient';insufficient_context:boolean;partial_coverage:boolean;reference_ids:string[];
}
export interface ContextIntake {
 id:string;kind:'message'|'document'|'context';role:'user'|'assistant';text:string|null;name:string|null;context:PortableContext|null;attribution?:AnswerAttribution;
}
export interface ConsolidatedVersion {
 id:string;context_space_id:string;version:number;intake_ids:string[];source_revision_id:string;revision_ids:string[];created_at:string;
}
export interface WorkspaceState {
 context_id:string;state:'empty'|'pending'|'running'|'current'|'failed';pending_count:number;
 current:ConsolidatedVersion|null;intake:ContextIntake[];
}
