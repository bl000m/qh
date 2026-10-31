export class ApiError extends Error {
  constructor(public readonly status: number, public readonly providerError?: string) { super('QH request failed'); }
}
/** Read the classified provider failure kind, never a provider body. */
export async function failedResponse(response: Response): Promise<ApiError> {
  const value = [429, 503].includes(response.status) ? await response.json().catch(() => null) : null;
  const kind = value?.detail?.provider_error;
  return new ApiError(response.status, typeof kind === 'string' && /^[a-z_]{1,32}$/.test(kind) ? kind : undefined);
}
const PROVIDER_MESSAGES: Record<string, string> = {
  request: 'Mistral a refusé cette requête. Aucune nouvelle tentative automatique ; l’IA reste disponible.',
  transport: 'Mistral n’a pas répondu (réseau ou délai dépassé). Réessaie dans un instant.',
  rate_limit: 'Mistral limite temporairement les requêtes. Réessaie dans une minute.',
  provider: 'Mistral a rencontré une erreur temporaire. Réessaie dans un instant.',
  auth: 'La clé ou le compte Mistral est refusé. L’IA est suspendue jusqu’à vérification de la configuration.',
  accounting: 'Anomalie de comptabilité IA : l’IA est suspendue jusqu’à vérification.',
  suspended: 'L’IA est suspendue après une anomalie à vérifier. Tes messages sont conservés.',
  session: 'Ta session IA a expiré (8 h après la connexion). Déconnecte-toi puis reconnecte-toi.',
  session_expired: 'Ta session IA a expiré (8 h après la connexion). Déconnecte-toi puis reconnecte-toi.',
  budget: 'Plafond IA atteint. Aucune nouvelle requête ne sera facturée.',
  not_eligible: 'L’IA n’est pas activée pour ce compte ou ce contexte.',
  unconfigured: 'L’IA n’est pas configurée sur ce serveur (clé ou autorisation absente).',
};
export function providerMessage(kind?: string | null): string | null {
  return kind ? PROVIDER_MESSAGES[kind] ?? null : null;
}
export const isUuid = (v: string) => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v);

/** Save a checked private response without exposing its authenticated endpoint. */
export async function saveDownload(response:Response,name:string):Promise<void>{
 const url=URL.createObjectURL(await response.blob()),anchor=document.createElement('a');
 anchor.href=url;anchor.download=name;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
