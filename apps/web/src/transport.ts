export class ApiError extends Error {
  constructor(public readonly status: number) { super('QH request failed'); }
}
export const isUuid = (v: string) => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v);

/** Save a checked private response without exposing its authenticated endpoint. */
export async function saveDownload(response:Response,name:string):Promise<void>{
 const url=URL.createObjectURL(await response.blob()),anchor=document.createElement('a');
 anchor.href=url;anchor.download=name;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
