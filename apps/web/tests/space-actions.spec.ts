import {test,expect} from '@playwright/test';
import {exactSpaceName} from '../src/presentation';
test('destructive intent requires the literal full canonical name, without normalization or shortcuts',()=>{
 const name='Santé d’Alice 👩🏽‍🔬';expect(exactSpaceName(name,name)).toBe(true);
 for(const input of ['',name.toLowerCase(),name+' ',' '+name,'Santé',name.replace('é','e\u0301')])expect(exactSpaceName(input,name)).toBe(false);
});
