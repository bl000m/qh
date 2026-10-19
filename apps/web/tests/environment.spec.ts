import {test,expect} from '@playwright/test';
import {organization} from '../src/environment';
const id='00000000-0000-0000-0000-000000000001';
test('organization wire contract accepts multiple memberships but rejects aliasing and invalid domains',()=>{
 const doc={version:1,domains:[{id,name:'Travail & projets'}],memberships:{[id]:[id]}};
 expect(organization(doc)).toEqual(doc);
 for(const changed of [{version:-1},{domains:[...doc.domains,...doc.domains]},{memberships:{[id]:['unknown']}},{memberships:{foreign:[id]}},{memberships:{[id]:[id,id]}}])expect(()=>organization({...doc,...changed})).toThrow();
});
