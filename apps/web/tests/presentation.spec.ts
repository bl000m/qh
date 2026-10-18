import {test,expect} from '@playwright/test';
import {spaceTitle} from '../src/presentation';

test('Space captions retain ten user-perceived characters without splitting Unicode names',()=>{
 for(const name of ['', 'Bien-être', '1234567890'])expect(spaceTitle(name)).toBe(name);
 expect(spaceTitle('Organisation personnelle')).toBe('Organisati…');
 expect(spaceTitle('123456789👩🏽‍🔬suite')).toBe('123456789👩🏽‍🔬…');
 expect(spaceTitle('123456789e\u0301suite')).toBe('123456789e\u0301…');
});
