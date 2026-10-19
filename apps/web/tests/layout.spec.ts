import {test,expect} from '@playwright/test';
test('chat reflow at 320 pixels and 200 percent preserves composer and sources',async({page})=>{
 await page.setViewportSize({width:320,height:812});await page.goto('/tests/fixtures/chat-layout.html',{waitUntil:'domcontentloaded'});
 await expect(page.getByLabel('Votre question sur ce contexte')).toBeEnabled();
 await page.evaluate(()=>{document.documentElement.style.fontSize='200%';});
 await page.getByLabel('Inclure explicitement les propositions non confirmées').check();
 await page.getByLabel('Votre question sur ce contexte').fill('Question de contrôle');await page.getByRole('button',{name:'Envoyer la question',exact:true}).click();
 await expect(page.getByRole('article',{name:'Échange 1',exact:true})).toBeVisible();
 const overflow=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,offenders:[...document.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>({tag:e.tagName,class:e.className,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width})).slice(0,20)}));
 expect(overflow.scroll,JSON.stringify(overflow)).toBeLessThanOrEqual(overflow.width);
 await page.getByRole('button',{name:'Voir les sources de la réponse 1',exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
});
