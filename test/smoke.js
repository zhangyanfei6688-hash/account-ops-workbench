// 最小 DOM 桩：验证工作台 JS 渲染链路 + 日期选择器联动
const fs = require('fs');
const path = require('path');
const vm = require('vm');

function E(tag) {
  this.tagName = String(tag).toUpperCase();
  this.children = [];
  this.className = '';
  this.style = {};
  this.attrs = {};
  this._text = '';
  this._html = '';
  this.lastChild = null;
  this.parentNode = null;
  this.value = '';
  this.type = '';
  this.selected = false;
  this.min = '';
  this.max = '';
  this.onclick = null;
  this.onchange = null;
  this._ls = {};
}
Object.defineProperty(E.prototype, 'textContent', {
  get() { return this._text; },
  set(v) { this._text = String(v); this.children = []; this.lastChild = null; }
});
Object.defineProperty(E.prototype, 'innerHTML', {
  get() { return this._html; },
  set(v) { this._html = String(v); this.children = []; this.lastChild = null; }
});
E.prototype.appendChild = function (c) {
  this.children.push(c); c.parentNode = this; this.lastChild = c; return c;
};
E.prototype.replaceChild = function (n, o) {
  const i = this.children.indexOf(o);
  if (i >= 0) this.children[i] = n; else this.children.push(n);
  n.parentNode = this; this.lastChild = n;
  return o;
};
E.prototype.setAttribute = function (k, v) { this.attrs[k] = String(v); };
E.prototype.getAttribute = function (k) { return this.attrs[k] === undefined ? null : this.attrs[k]; };
E.prototype.addEventListener = function (t, f) {
  this._ls[t] = (this._ls[t] || []).concat(f);
};
E.prototype.getElementsByTagName = function (t) {
  const out = [];
  (function walk(n) {
    n.children.forEach(function (c) {
      if (c.tagName === t.toUpperCase()) out.push(c);
      walk(c);
    });
  })(this);
  return out;
};
E.prototype.getBoundingClientRect = function () { return { left: 0, top: 0, width: 10, height: 10, right: 10, bottom: 10 }; };
function fire(el, t, ev) {
  ev = ev || {}; ev.target = ev.target || el;
  (el._ls[t] || []).forEach(f => f.call(el, ev));
  if (t === 'click' && typeof el.onclick === 'function') el.onclick.call(el, ev);
}

const html = fs.readFileSync(path.join(__dirname, '..', 'account-workbench.html'), 'utf8');
const ids = [...html.matchAll(/id="([A-Za-z0-9_]+)"/g)].map(m => m[1]);

const store = {};
const document_ = {
  readyState: 'complete',
  createElement: (t) => new E(t),
  getElementById: (id) => store[id] || null,
  addEventListener: () => {}
};
ids.forEach(id => { store[id] = new E('div'); store[id].attrs.id = id; });
// 关键父子关系
['day', 'month', 'year'].forEach(g => {
  const b = new E('button'); b.setAttribute('data-grain', g); store['grainTabs'].appendChild(b);
});
['day', 'month', 'year'].forEach(g => {
  const b = new E('button'); b.setAttribute('data-g', g); store['pGrain'].appendChild(b);
});
['single', 'range'].forEach(m => {
  const b = new E('button'); b.setAttribute('data-m', m); store['pMode'].appendChild(b);
});
['acct', 'prod', 'promo'].forEach(t => {
  const b = new E('button'); b.setAttribute('data-t', t); store['cmpTabSeg'].appendChild(b);
});
[['periodBtn', 'periodBtnTxt'], ['cmpTag', 'cmpTagTxt'], ['trendTag', 'trendTagTxt'], ['funnelTag', 'funnelTagTxt']]
  .forEach(p => store[p[0]].appendChild(store[p[1]]));
store['pAWrap'].appendChild(store['pStart']);
store['pBWrap'].appendChild(store['pEnd']);

const sandbox = {
  window: {},
  document: document_,
  localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} },
  console: console,
  setTimeout: setTimeout, clearTimeout: clearTimeout,
  Blob: function () {}, URL: { createObjectURL: () => 'blob:x', revokeObjectURL: () => {} }
};
sandbox.globalThis = sandbox;

const code = html.match(/<script>([\s\S]*?)<\/script>/)[1];
function dump(id) {
  const e = store[id];
  if (!e) return id + ': MISSING';
  return id + ': children=' + e.children.length + ' text=' + JSON.stringify(e._text).slice(0, 40) +
    ' html=' + JSON.stringify((e._html || '').slice(0, 46));
}
try {
  vm.createContext(sandbox);
  vm.runInContext(code, sandbox, { timeout: 8000 });
  setTimeout(() => {
    console.log('--- 初始渲染（日 · 单日）---');
    ['hdSub', 'alertList', 'kpiGrid', 'acctTable', 'trendBox', 'funnelSteps', 'healthRank', 'adviceList']
      .forEach(id => console.log(dump(id)));
    console.log('periodBtnTxt:', store['periodBtnTxt']._text);
    console.log('cmpTagTxt:', store['cmpTagTxt']._text);

    console.log('--- 打开选择器，切区间 09-14 ~ 09-16，应用 ---');
    fire(store['periodBtn'], 'click');
    console.log('pickerMask:', store['pickerMask'].className);
    store['pStart'].value = '2026-09-14';
    store['pEnd'].value = '2026-09-16';
    fire(store['pMode'], 'click', { target: store['pMode'].getElementsByTagName('button')[1] });
    fire(store['pApply'], 'click');
    console.log('pickerMask after:', store['pickerMask'].className);
    console.log('periodBtnTxt:', store['periodBtnTxt']._text);
    console.log('trendTagTxt:', store['trendTagTxt']._text);
    console.log('funnelTagTxt:', store['funnelTagTxt']._text);
    console.log(dump('kpiGrid'));
    console.log(dump('trendBox'));

    console.log('--- 切月视图（联动） ---');
    fire(store['grainTabs'], 'click', { target: store['grainTabs'].getElementsByTagName('button')[1] });
    console.log('periodBtnTxt:', store['periodBtnTxt']._text);
    console.log('cmpTagTxt:', store['cmpTagTxt']._text);

    console.log('--- 切年视图 ---');
    fire(store['grainTabs'], 'click', { target: store['grainTabs'].getElementsByTagName('button')[2] });
    console.log('periodBtnTxt:', store['periodBtnTxt']._text);
    console.log(dump('trendBox'));

    console.log('--- 商品维度 Tab ---');
    fire(store['cmpTabSeg'], 'click', { target: store['cmpTabSeg'].getElementsByTagName('button')[1] });
    console.log('acctWrap display:', store['acctTableWrap'].style.display, '| prodWrap:', store['prodWrap'].style.display);
    ['prodKpis', 'prodTable', 'prodRank', 'prodAcctRank'].forEach(id => console.log(dump(id)));
    console.log('prodRankMetric:', store['prodRankMetric']._text);
    fire(store['prodMetricSwitch'].getElementsByTagName('button')[1] || store['prodMetricSwitch'], 'click',
      { target: store['prodMetricSwitch'].getElementsByTagName('button')[1] || store['prodMetricSwitch'] });
    console.log('after metric switch prodRank:', dump('prodRank'));

    console.log('--- 推广维度 Tab ---');
    fire(store['cmpTabSeg'], 'click', { target: store['cmpTabSeg'].getElementsByTagName('button')[2] });
    console.log('acct:', store['acctTableWrap'].style.display, 'prod:', store['prodWrap'].style.display, 'promo:', store['promoWrap'].style.display);
    ['promoKpis', 'promoTable', 'promoRank', 'promoFunnel'].forEach(id => console.log(dump(id)));
    var sw2 = store['promoCostSwitch'].getElementsByTagName('button');
    if (sw2.length) {
      fire(store['promoCostSwitch'], 'click', { target: sw2[1] });
      console.log('after cost switch promoRank:', dump('promoRank'));
    }
    console.log('--- 推广趋势指标 ---');
    var tsw = store['metricSwitch'].getElementsByTagName('button');
    console.log('metric chips:', tsw.length);
    if (tsw.length > 8) fire(store['metricSwitch'], 'click', { target: tsw[8] });
    console.log('trendBox:', dump('trendBox'));

    console.log('--- 悬浮提示 ---');
    fire(store['grainTabs'], 'click', { target: store['grainTabs'].getElementsByTagName('button')[0] });
    fire(store['grainTabs'], 'click', { target: store['grainTabs'].getElementsByTagName('button')[1] });
    fire(store['grainTabs'], 'click', { target: store['grainTabs'].getElementsByTagName('button')[0] });
    const fakeTarget = {
      getAttribute: (k) => (k === 'data-i' ? '0' : null),
      getBoundingClientRect: () => ({ left: 100, top: 120, width: 8, height: 8, bottom: 128, right: 108 })
    };
    fire(store['trendBox'], 'mousemove', { target: fakeTarget });
    console.log('chartTip opacity:', store['chartTip'].style.opacity);
    console.log('chartTip html:', JSON.stringify(store['chartTip']._html).slice(0, 160));
    console.log('SMOKE_OK');
  }, 60);
} catch (e) {
  console.log('SMOKE_FAIL', e && e.stack ? e.stack : e);
}
