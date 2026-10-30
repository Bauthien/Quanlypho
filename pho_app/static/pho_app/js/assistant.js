/* Read-only catalog assistance. Recommendations never create financial actions. */
(() => {
  'use strict';
  const root = document.querySelector('[data-assistant]'); if (!root) return;
  const $ = selector => root.querySelector(selector);
  const dialog = $('#aiAssistant'), messages = $('[data-ai-messages]'), form = $('[data-ai-form]');
  const send = $('.ai-send'), error = $('[data-ai-error]'), opener = $('[data-ai-open]');
  const initial = [...messages.children].map(element => element.cloneNode(true));
  const money = value => Number(value).toLocaleString('vi-VN') + 'đ';
  let controller, serial = 0;
  const node = (tag, className, text) => { const element = document.createElement(tag); element.className = className; if (text != null) element.textContent = text; return element; };
  function close() { dialog.close(); }
  function link(url, label, className) {
    const anchor = node('a', className, label);
    if (typeof url === 'string' && url.startsWith('/') && !url.startsWith('//')) anchor.href = url;
    return anchor;
  }
  function show() { if (!dialog.open) { dialog.showModal(); document.body.classList.add('assistant-open'); $('#aiQuestion').focus(); } }
  opener.addEventListener('click', show); $('[data-ai-close]').addEventListener('click', close);
  dialog.addEventListener('close', () => { document.body.classList.remove('assistant-open'); opener.focus(); });
  dialog.addEventListener('click', event => { if (event.target === dialog) { const box = dialog.getBoundingClientRect(); if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) close(); } });
  async function ask(message) {
    if (!message.trim()) return;
    controller?.abort(); controller = new AbortController(); const current = ++serial;
    error.hidden = true; send.disabled = true; form.setAttribute('aria-busy', 'true');
    messages.append(node('div', 'ai-message user', message));
    const pending = node('div', 'ai-message bot ai-loading', 'Đang kiểm tra dữ liệu Phở Nhà…'); messages.append(pending); messages.scrollTop = messages.scrollHeight;
    try {
      const response = await fetch(root.dataset.replyUrl, {method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json','X-CSRFToken':form.querySelector('[name=csrfmiddlewaretoken]').value,'X-Account-Generation':document.querySelector('meta[name=account-generation]')?.content || ''},body:JSON.stringify({message,people:Number(form.elements.people.value),budget:Number(form.elements.budget.value),use_history:Boolean(form.elements.use_history?.checked)})});
      const data = await response.json(); if (current !== serial) return;
      if (!response.ok || !data.ok) throw new Error(data.error || 'Chưa lấy được gợi ý. Hãy thử lại.');
      pending.remove(); messages.append(node('div', 'ai-message bot', data.text));
      if (data.products?.length) {
        const products = node('div','ai-products');
        data.products.forEach(product => {
          const card = node('article',''), img = node('img',''); img.src = product.image; img.alt = ''; img.loading = 'lazy';
          const copy = node('div',''); copy.append(node('strong','', `${product.quantity} × ${product.name}`),node('small','', `${money(product.price)} / phần · Còn phục vụ tại lúc kiểm tra`),node('p','',product.reason));
          const choose = node('button','ai-product-action','Chọn món'); choose.type = 'button';
          choose.addEventListener('click', () => { close(); if (document.getElementById('menuGrid')) document.dispatchEvent(new CustomEvent('pho:choose-dish',{detail:{id:product.id,quantity:product.quantity}})); else { const url = new URL(product.url,location.origin); if (url.origin === location.origin) location.assign(url); } });
          copy.append(choose); card.append(img,copy); products.append(card);
        });
        messages.append(products);
      }
      const links = node('div','ai-links'); (data.links || []).forEach(item => links.append(link(item.url,item.label,'secondary-btn')));
      if (document.getElementById('menuGrid') && data.products?.length) { const cart = node('button','primary-btn full','Mở giỏ để xem phí giao'); cart.type = 'button'; cart.addEventListener('click',()=>{close();document.dispatchEvent(new CustomEvent('pho:open-cart'));}); links.append(cart); }
      if (links.childElementCount) messages.append(links);
      messages.append(node('p','ai-source',`Dữ liệu ${data.updated_at}${data.history_used ? ' · Có dùng lịch sử đơn của bạn' : ' · Không dùng lịch sử cá nhân'}. ${data.notice}`));
    } catch (err) {
      pending.remove(); if (err.name !== 'AbortError' && current === serial) { error.textContent = err.message || 'Mất kết nối. Hãy thử lại.'; error.hidden = false; }
    } finally { if (current === serial) { send.disabled = false; form.removeAttribute('aria-busy'); messages.scrollTop = messages.scrollHeight; } }
  }
  form.addEventListener('submit', event => { event.preventDefault(); if (!form.reportValidity()) return; const input = $('#aiQuestion'), value = input.value.trim(); input.value = ''; ask(value); });
  $('#aiQuestion').addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); form.requestSubmit(); } });
  root.addEventListener('click', event => { const starter = event.target.closest('[data-ai-ask]'); if (starter) ask(starter.dataset.aiAsk); });
  $('[data-ai-reset]').addEventListener('click', () => { controller?.abort(); ++serial; messages.replaceChildren(...initial.map(element=>element.cloneNode(true))); send.disabled = false; error.hidden = true; form.removeAttribute('aria-busy'); $('#aiQuestion').value = ''; $('#aiQuestion').focus(); });
})();
