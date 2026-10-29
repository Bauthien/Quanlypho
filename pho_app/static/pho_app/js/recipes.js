/* Recipe drafts are local; Django validates and replaces one complete formula atomically. */
(() => {
  'use strict';
  const root = document.querySelector('[data-recipe-editor]');
  const source = document.getElementById('recipe-editor-data');
  if (!root || !source) return;
  const data = JSON.parse(source.textContent), $ = s => root.querySelector(s), all = s => [...root.querySelectorAll(s)];
  const escape = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const countUnits = new Set(['chai', 'lon', 'hộp', 'gói', 'cái', 'quả', 'viên', 'phần']);
  const units = {g:1, gram:1, gam:1, gr:1, kg:1000, ml:1, l:1000, 'lít':1000, lit:1000, liter:1000};
  const number = value => /^\d+(?:[.,]\d+)?$/.test(String(value).trim()) ? Number(String(value).replace(',', '.')) : NaN;
  const normalized = unit => unit.trim().toLowerCase();
  const inputUnit = unit => normalized(unit) === 'kg' ? 'g' : ['l','lít','lit','liter'].includes(normalized(unit)) ? 'ml' : unit;
  const unitChoices = unit => ['kg','g','gram','gam','gr'].includes(normalized(unit)) ? ['g','kg'] : ['ml','l','lít','lit','liter'].includes(normalized(unit)) ? ['ml','lít'] : [unit];
  const productKey = p => `${p.kind}:${p.id}`;
  const storageKey = `pho-recipe-drafts-v2:${data.user_id}`;
  let kind = 'MENU', scope = 'PHO', selected = {}, drafts = {}, pending = new Set(), clearKey = null;
  try {
    const saved = JSON.parse(sessionStorage.getItem(storageKey) || 'null');
    if (saved && ['MENU','DRINK','TOPPING'].includes(saved.kind) && ['PHO','DRINK'].includes(saved.scope)) {
      kind = saved.kind; scope = saved.scope; selected = saved.selected || {};
      for (const p of data.products) {
        const d = saved.drafts?.[productKey(p)];
        if (d && Array.isArray(d.rows) && d.rows.length <= 200 && d.rows.every(r => r && typeof r.quantity === 'string' && typeof r.input_unit === 'string' && (r.ingredient_id === '' || data.ingredients.some(i => i.id === Number(r.ingredient_id)))) && Array.isArray(d.allowed)) drafts[productKey(p)] = d;
      }
    }
  } catch (_) {}
  const category = () => kind === 'MENU' ? 'PHO' : kind === 'DRINK' ? 'DRINK' : scope;
  const groupName = () => category() === 'PHO' ? 'Món chính' : 'Nước uống';
  const selectionKey = () => `${kind}:${category()}`;
  const products = () => data.products.filter(p => p.kind === (kind === 'TOPPING' ? 'topping' : 'menu') && p.category === category());
  const product = () => products().find(p => p.id === Number(selected[selectionKey()])) || products()[0];
  const blank = () => ({ingredient_id:'',quantity:'',input_unit:''});
  const draft = () => {
    const p = product(); if (!p) return {rows:[],allowed:[],all:false,mode:'BOM'};
    const key = productKey(p);
    if (!drafts[key]) drafts[key] = {revision:p.revision,dirty:false,mode:p.inventory_mode === 'DIRECT' ? 'DIRECT' : 'BOM',all:p.applies_to_all,allowed:[...p.allowed_menu_items],rows:p.rows.map(r => {
      const unit = inputUnit(r.input_unit), factor = (units[normalized(r.input_unit)] || 1) / (units[normalized(unit)] || 1);
      return {...r,quantity:String(Number((Number(r.quantity)*factor).toFixed(6))),input_unit:unit};
    })};
    return drafts[key];
  };
  const direct = () => kind === 'DRINK' && draft().mode === 'DIRECT';
  const ingredients = () => data.ingredients.filter(i => [category(),'SHARED'].includes(i.usage) && (!direct() || countUnits.has(normalized(i.unit))));
  function remember() { try { sessionStorage.setItem(storageKey, JSON.stringify({kind,scope,selected,drafts})); } catch (_) {} }
  function closePicker() { $('#recipeBatchPicker').hidden = true; $('[data-recipe-pick]').setAttribute('aria-expanded','false'); pending.clear(); }
  function closeClear() { $('#recipeClearConfirm').hidden = true; $('[data-recipe-clear]').setAttribute('aria-expanded','false'); clearKey = null; }
  function errors(messages = []) { const box = $('[data-recipe-errors]'); box.hidden = !messages.length; box.innerHTML = messages.map(m => `<p>${escape(m)}</p>`).join(''); }
  function summary() {
    const p = product(), d = draft(), count = d.rows.filter(r => r.ingredient_id).length;
    $('[data-recipe-count]').textContent = p ? `${count} nguyên liệu${d.dirty?' · Chưa lưu':''}` : 'Chưa có sản phẩm trong nhóm';
    $('[data-recipe-save]').textContent = direct() ? 'Lưu liên kết kho' : `Lưu ${count} nguyên liệu`;
    $('[data-recipe-save]').disabled = !p || !count;
    $('[data-recipe-clear]').disabled = !d.rows.length;
    $('[data-recipe-add]').disabled = !p || d.rows.length >= ingredients().length;
    $('[data-recipe-pick]').disabled = !p || ingredients().every(i => d.rows.some(r => Number(r.ingredient_id) === i.id));
    $('[data-recipe-empty]').hidden = d.rows.length > 0;
  }
  function changed() { closeClear(); draft().dirty = true; errors(); $('[data-recipe-status]').textContent = ''; summary(); remember(); }
  function renderRows() {
    const d = draft(), catalog = ingredients();
    $('[data-recipe-rows]').innerHTML = d.rows.map((r,index) => {
      const ingredient = data.ingredients.find(i => i.id === Number(r.ingredient_id));
      const options = [category(), 'SHARED'].map(usage => {
        const items = catalog.filter(i => i.usage === usage);
        if (!items.length) return '';
        const label = usage === 'SHARED' ? 'Dùng chung cho cả hai nhóm' : groupName();
        return `<optgroup label="${label}">${items.map(i => `<option value="${i.id}"${Number(r.ingredient_id)===i.id?' selected':''}${d.rows.some((other,n)=>n!==index&&Number(other.ingredient_id)===i.id)?' disabled':''}>${escape(i.name)}${usage==='SHARED'?' · Dùng chung':''}</option>`).join('')}</optgroup>`;
      }).join('');
      const choices = ingredient ? unitChoices(ingredient.unit) : [''];
      return `<div class="recipe-row" data-index="${index}"><div class="recipe-ingredient-field"><label class="recipe-mobile-label" for="recipeIngredient${index}">Nguyên liệu</label><select class="form-input" id="recipeIngredient${index}" data-ingredient aria-label="Nguyên liệu dòng ${index+1}" aria-describedby="recipeLineError${index}"><option value="">Chọn nguyên liệu</option>${options}</select><p class="recipe-row-error" id="recipeLineError${index}" data-line-error hidden></p></div><div class="recipe-amount-field"><label class="recipe-mobile-label" for="recipeAmount${index}">Số lượng</label><input class="form-input" id="recipeAmount${index}" type="text" inputmode="decimal" data-amount aria-label="Số lượng dòng ${index+1}" value="${escape(r.quantity)}"${direct()?' readonly':''}></div><div class="recipe-unit-field"><label class="recipe-mobile-label" for="recipeUnit${index}">Đơn vị</label><select class="form-input" id="recipeUnit${index}" data-unit aria-label="Đơn vị nhập dòng ${index+1}"${choices.length<2?' disabled':''}>${choices.map(u=>`<option value="${escape(u)}"${u===r.input_unit?' selected':''}>${escape(u)}</option>`).join('')}</select></div>${direct()?'':`<button type="button" class="icon-button recipe-delete" data-delete aria-label="Xóa ${escape(ingredient?.name || 'dòng '+(index+1))}">Xóa</button>`}</div>`;
    }).join(''); summary();
  }
  function renderEligibility() {
    const d = draft(); $('[data-all-menu]').checked = d.all;
    $('[data-menu-choices]').innerHTML = data.products.filter(p => p.kind==='menu' && p.category===scope).map(p => `<label class="check-row"><input type="checkbox" data-allowed value="${p.id}"${d.all||d.allowed.includes(p.id)?' checked':''}${d.all?' disabled':''}>${escape(p.name)}</label>`).join('');
  }
  function render() {
    closePicker(); closeClear(); errors();
    const p = product(); if (p) selected[selectionKey()] = p.id;
    all('[name=recipe_target]').forEach(i => i.checked = i.value === kind);
    all('[name=topping_scope]').forEach(i => i.checked = i.value === scope);
    $('[data-menu-field]').hidden = kind === 'TOPPING'; $('[data-topping-field]').hidden = kind !== 'TOPPING';
    $('#menuItemSelect').disabled = kind === 'TOPPING'; $('#menuItemSelect').required = kind !== 'TOPPING';
    $('#toppingSelect').disabled = kind !== 'TOPPING'; $('#toppingSelect').required = kind === 'TOPPING';
    $('[data-menu-label]').textContent = kind === 'DRINK' ? 'Chọn nước uống' : 'Chọn món chính';
    const select = kind === 'TOPPING' ? $('#toppingSelect') : $('#menuItemSelect');
    select.innerHTML = products().map(p => `<option value="${p.id}">${escape(p.name)}</option>`).join('') || '<option value="">Chưa có sản phẩm trong nhóm</option>';
    if (p) select.value = p.id;
    $('[data-topping-scope]').hidden = kind !== 'TOPPING'; $('[data-topping-eligibility]').hidden = kind !== 'TOPPING';
    $('[data-drink-mode]').hidden = kind !== 'DRINK';
    all('[name=inventory_mode]').forEach(i => i.checked = i.value === draft().mode);
    if (kind === 'TOPPING') renderEligibility();
    $('[data-recipe-portion]').textContent = kind === 'MENU' ? 'Lượng tiêu hao cho 1 tô' : kind === 'TOPPING' ? 'Lượng tiêu hao cho 1 phần gọi thêm' : direct() ? 'Trừ 1 chai / lon khi bán' : 'Lượng tiêu hao cho 1 ly';
    $('[data-recipe-heading]').textContent = direct() ? 'Hàng xuất kho' : 'Danh sách nguyên liệu';
    const sharedCount = ingredients().filter(i => i.usage === 'SHARED').length;
    $('[data-inventory-scope]').textContent = `${direct()?'Hàng xuất kho':'Nguyên liệu'}: ${groupName()}${sharedCount?' + Dùng chung':''}`;
    $('[data-inventory-label]').textContent = `${ingredients().length} lựa chọn phù hợp${sharedCount?` · ${sharedCount} dùng chung`:''}`;
    $('[data-row-actions]').hidden = direct();
    $('[data-recipe-status]').textContent = !p ? 'Thêm sản phẩm trong Thực đơn và chọn đúng nhóm trước khi thiết lập định lượng.' : '';
    renderRows();
  }
  all('[name=recipe_target]').forEach(i => i.addEventListener('change', () => {kind=i.value;render();remember();}));
  all('[name=topping_scope]').forEach(i => i.addEventListener('change', () => {scope=i.value;render();remember();}));
  [$('#menuItemSelect'),$('#toppingSelect')].forEach(select => select.addEventListener('change', () => {selected[selectionKey()]=Number(select.value);render();remember();}));
  all('[name=inventory_mode]').forEach(i => i.addEventListener('change', () => {
    const d=draft(); d.mode=i.value;
    if (direct()) {d.preparedRows=d.rows; const valid=d.rows.length===1 && ingredients().some(i=>i.id===Number(d.rows[0].ingredient_id)); d.rows=valid?[{...d.rows[0],quantity:'1'}]:[{...blank(),quantity:'1'}];}
    else if (d.preparedRows) {d.rows=d.preparedRows;delete d.preparedRows;}
    render();changed();
  }));
  $('[data-all-menu]').addEventListener('change', e => {draft().all=e.target.checked;renderEligibility();changed();});
  $('[data-menu-choices]').addEventListener('change', () => {draft().allowed=all('[data-allowed]:checked').map(i=>Number(i.value));changed();});
  $('[data-recipe-rows]').addEventListener('input', e => {if(!e.target.matches('[data-amount]')||direct())return;draft().rows[Number(e.target.closest('.recipe-row').dataset.index)].quantity=e.target.value;changed();});
  $('[data-recipe-rows]').addEventListener('change', e => {
    const el=e.target.closest('.recipe-row');if(!el)return;const index=Number(el.dataset.index),r=draft().rows[index];
    if(e.target.matches('[data-ingredient]')) {r.ingredient_id=e.target.value;const i=data.ingredients.find(i=>i.id===Number(r.ingredient_id));r.input_unit=i?inputUnit(i.unit):'';r.quantity=direct()?'1':'';renderRows();$(`#recipeAmount${index}`).focus();}
    if(e.target.matches('[data-unit]')) {const before=units[normalized(r.input_unit)]||1,after=units[normalized(e.target.value)]||1,amount=number(r.quantity);r.input_unit=e.target.value;if(Number.isFinite(amount))r.quantity=String(Number((amount*before/after).toFixed(6)));renderRows();}
    closePicker();changed();
  });
  $('[data-recipe-rows]').addEventListener('click', e => {const button=e.target.closest('[data-delete]');if(!button)return;draft().rows.splice(Number(button.closest('.recipe-row').dataset.index),1);renderRows();closePicker();changed();$('[data-recipe-add]').focus();});
  $('[data-recipe-add]').addEventListener('click', () => {draft().rows.push(blank());renderRows();closePicker();changed();$('[data-recipe-rows]').lastElementChild.querySelector('select').focus();});
  $('[data-recipe-pick]').addEventListener('click', () => {
    closeClear();if(!$('#recipeBatchPicker').hidden){closePicker();return;}
    $('[data-picker-options]').innerHTML=[category(),'SHARED'].map(usage=>{
      const items=ingredients().filter(i=>i.usage===usage);if(!items.length)return '';
      return `<section class="recipe-picker-group"><strong>${usage==='SHARED'?'Dùng chung cho cả hai nhóm':groupName()}</strong>${items.map(i=>{const used=draft().rows.some(r=>Number(r.ingredient_id)===i.id);return `<label><input type="checkbox" value="${i.id}"${used?' checked disabled':''}>${escape(i.name)}<small>${used?'Đã thêm':escape(i.unit)}</small></label>`;}).join('')}</section>`;
    }).join('');
    pending.clear();$('[data-picker-apply]').disabled=true;$('[data-picker-apply]').textContent='Thêm đã chọn';$('#recipeBatchPicker').hidden=false;$('[data-recipe-pick]').setAttribute('aria-expanded','true');
  });
  $('[data-picker-options]').addEventListener('change', e => {if(!e.target.matches('input'))return;const id=Number(e.target.value);e.target.checked?pending.add(id):pending.delete(id);$('[data-picker-apply]').disabled=!pending.size;$('[data-picker-apply]').textContent=`Thêm ${pending.size} nguyên liệu`;});
  $('[data-picker-cancel]').addEventListener('click', () => {closePicker();$('[data-recipe-pick]').focus();});
  $('[data-picker-apply]').addEventListener('click', () => {for(const id of pending){const ingredient=data.ingredients.find(i=>i.id===id),r={ingredient_id:id,quantity:'',input_unit:inputUnit(ingredient.unit)},index=draft().rows.findIndex(r=>!r.ingredient_id&&!r.quantity);if(index>=0)draft().rows[index]=r;else draft().rows.push(r);}closePicker();renderRows();changed();});
  $('[data-recipe-clear]').addEventListener('click', () => {closePicker();clearKey=productKey(product());$('#recipeClearTitle').textContent=`Xóa tất cả ${draft().rows.length} dòng nguyên liệu của ${product().name}?`;$('#recipeClearConfirm').hidden=false;$('[data-recipe-clear]').setAttribute('aria-expanded','true');$('[data-clear-cancel]').focus();});
  $('[data-clear-cancel]').addEventListener('click', () => {closeClear();$('[data-recipe-clear]').focus();});
  $('[data-clear-confirm]').addEventListener('click', () => {if(!product()||clearKey!==productKey(product()))return;draft().rows=[];renderRows();changed();$('[data-recipe-status]').textContent='Đã xóa các dòng trong bản nháp. Bạn có thể thêm lại nguyên liệu.';$('[data-recipe-add]').focus();});
  $('[data-recipe-form]').addEventListener('submit', async e => {
    e.preventDefault();closeClear();const p=product(),d=draft();if(!p)return;
    const messages=[],seen=new Set();
    all('.recipe-row').forEach((el,index)=>{
      const r=d.rows[index],ingredient=ingredients().find(i=>i.id===Number(r.ingredient_id)),amount=number(r.quantity);
      let message=!ingredient?'Chọn nguyên liệu phù hợp.':seen.has(ingredient.id)?'Nguyên liệu đã có trong công thức.':!Number.isFinite(amount)||amount<=0?'Nhập số lượng lớn hơn 0.':'';
      if(ingredient)seen.add(ingredient.id);const error=el.querySelector('[data-line-error]');error.textContent=message;error.hidden=!message;el.querySelector('[data-ingredient]').setAttribute('aria-invalid',String(!!message));if(message)messages.push(`Dòng ${index+1}: ${message}`);
    });
    if(!d.rows.length)messages.push('Thêm ít nhất một nguyên liệu trước khi lưu.');
    if(kind==='TOPPING'&&!d.all&&!d.allowed.length)messages.push('Chọn ít nhất một món được gọi kèm topping.');
    if(messages.length){errors(messages);$('[aria-invalid=true]')?.focus();return;}
    const form=e.target,body=new FormData(form),saveKey=productKey(p);
    body.set('rows',JSON.stringify(d.rows));body.set('revision',d.revision);body.set('inventory_mode',d.mode);
    body.delete('allowed_menu_items');d.allowed.forEach(id=>body.append('allowed_menu_items',id));body.set('applies_to_all',d.all?'1':'');
    const controls=[...form.querySelectorAll('button,input,select')].map(el=>({el,disabled:el.disabled}));controls.forEach(({el})=>el.disabled=true);form.setAttribute('aria-busy','true');$('[data-recipe-save]').textContent='Đang lưu…';
    try {
      const response=await fetch(form.action,{method:'POST',body,headers:{Accept:'application/json'}});
      const result=await response.json();
      if(!response.ok||!result.ok){const messages=Object.values(result.errors||{}).flat().map(error=>error.message);throw new Error(messages.join('\n')||result.error||'Không lưu được định lượng. Hãy kiểm tra phiên đăng nhập và thử lại.');}
      delete drafts[saveKey];remember();location.assign(result.redirect);
    } catch(error) {errors([error.message||'Không kết nối được máy chủ. Bản nháp được giữ để thử lại.']);}
    finally {controls.forEach(({el,disabled})=>el.disabled=disabled);form.removeAttribute('aria-busy');summary();}
  });
  const inventory = document.querySelector('[data-inventory-groups]');
  function syncInventoryGroup() {
    if (!inventory) return;
    const group = inventory.querySelector('[data-list-category][aria-pressed="true"]')?.dataset.listCategory || 'PHO';
    const create = document.querySelector('[data-inventory-create]');
    if (create) { const url = new URL(create.href); url.searchParams.set('usage', group); create.href = url.href; }
    inventory.querySelector('[data-inventory-group-name]').textContent = group === 'DRINK' ? 'Nước uống' : 'Món chính';
    inventory.querySelector('[data-inventory-recipe]').dataset.recipeTarget = group === 'DRINK' ? 'DRINK' : 'MENU';
  }
  inventory?.addEventListener('click', event => { if (event.target.closest('[data-list-category]')) syncInventoryGroup(); });
  document.addEventListener('click', event => {
    const opener = event.target.closest('[data-dialog-open="recipeEditor"][data-recipe-target]');
    if (!opener || !['MENU','DRINK','TOPPING'].includes(opener.dataset.recipeTarget)) return;
    kind = opener.dataset.recipeTarget;
    if (kind !== 'TOPPING') scope = kind === 'DRINK' ? 'DRINK' : 'PHO';
    render(); remember();
  }, true);
  syncInventoryGroup();
  render();
})();
