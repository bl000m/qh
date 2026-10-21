import {test,expect} from '@playwright/test';
import {includeProposals} from './navigation.browser';
test('chat reflow at 320 pixels and 200 percent preserves composer and sources',async({page})=>{
 await page.setViewportSize({width:320,height:812});await page.goto('/tests/fixtures/chat-layout.html',{waitUntil:'domcontentloaded'});
 await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
 await page.evaluate(()=>{document.documentElement.style.fontSize='200%';});
 await includeProposals(page);
 await page.getByLabel('Votre question sur ce contexte').fill('Question de contrôle');await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();
 await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toBeVisible();
 const overflow=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,offenders:[...document.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>({tag:e.tagName,class:e.className,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width})).slice(0,20)}));
 expect(overflow.scroll,JSON.stringify(overflow)).toBeLessThanOrEqual(overflow.width);
 await page.getByRole('button',{name:'Sources de la réponse 1',exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('QH-53 tab keys preserve the draft and empty conversation offers no fake memory action',async({page})=>{
 await page.goto('/tests/fixtures/chat-layout.html');
 await page.getByLabel('Votre question sur ce contexte').fill('Une décision à clarifier.');
 const tabs=page.getByRole('tab');await expect(tabs).toHaveText(['Discussion','Éléments','Modèles','Conseils','Paramètres']);
 await tabs.first().focus();await page.keyboard.press('ArrowRight');await expect(tabs.nth(1)).toBeFocused();await expect(tabs.nth(1)).toHaveAttribute('aria-selected','true');
 await page.keyboard.press('End');await expect(tabs.last()).toBeFocused();await page.keyboard.press('Home');await expect(tabs.first()).toBeFocused();
 await expect(page.getByLabel('Votre question sur ce contexte')).toHaveValue('Une décision à clarifier.');
 await expect(page.getByRole('button',{name:'Mémoriser cette conversation',exact:false})).toHaveCount(0);
 await includeProposals(page);await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Mémoriser cette conversation',exact:false})).toBeVisible();
});
