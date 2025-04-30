// ==UserScript==
// @name         批诉表单助手
// @namespace    https://github.com/ecuplxd
// @version      0.0.2
// @description  批诉表单助手
// @author       ecuplxd
// @match        https://www.hshfy.sh.cn/wsla/*
// @icon         http://101.132.222.176:8666/favicon.ico
// @grant        none
// @homepageURL  https://github.com/ecuplxd/layer_helper/

// ==/UserScript==

(function () {
  'use strict';

  const FILED_MAP = {
    xm: '名称',
    fddbr: '法人代表姓名',
    jcjz: '经常居住地',
    shxydm: '社会信用代码',
    // 原告时候有效
    brdl: '该原告由本人代理',
    lxdh1: '联系电话1',
    // 1 上海市 0 非上海市
    zsdgs: '住所地（选择）',
    zsd: '住所地',
    sswssdd: '诉讼文书送达地',
    gj: '国家或地区',
    zjlx: '证件类型',
    zjhm: '证件号码',
  };

  // 自然人
  function zrr() {
    return {
      xm: null,
      gj: 1,
      brdl: null,
      zjlx: 1,
      zjhm: null,
      lxdh1: null,
      jcjz: null,
      zsdgs: null,
      zsd: null,
      sswssdd: null,
    };
  }

  // 法人
  function fr() {
    return {
      xm: null,
      fddbr: null,
      jcjz: null,
      shxydm: null,
      lxdh1: null,
      zsdgs: null,
      zsd: null,
      sswssdd: null,
    };
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // 标的额
  function bde(val) {
    const el = document.getElementById('bde');
    el.value = val;
    changeInput(el);
  }

  // 申请受理法院
  function sqslfy(val) {
    const select = document.getElementById('SQFY');
    const opts = Array.from(document.querySelectorAll('#SQFY option'));

    opts.forEach((opt) => opt.removeAttribute('selected'));

    for (let i = 0; i < opts.length; i++) {
      const opt = opts[i];

      if (opt.innerText === val) {
        opt.setAttribute('selected', 'selected');
        select.value = opt.getAttribute('value');
        changeInput(select);
        break;
      }
    }
  }

  // 诉讼请求
  async function ssqq(qqs = []) {
    const a = document.querySelector('.add-btn');

    qqs.forEach(async (qq, i) => {
      let id = 'ssqqqq_' + (i + 1);
      let input = document.getElementById(id);

      if (!input) {
        a.click();
        await sleep(500);
        input = document.getElementById(id);
      }

      input.value = qq;
      changeInput(input);
    });
  }

  // 当事人信息
  function dsrxx(aaa, kind = 'bg', type = 'zrr', idx = 1) {
    aaa.zsdgs = +(aaa.zsd || '').includes('上海');

    for (const key in aaa) {
      const val = aaa[key];
      const name = kind + '_' + type + '_' + key + '_' + idx;
      const el = document.querySelector(`[name="${name}"]`);

      if (el) {
        if (el.getAttribute('type') === 'radio') {
          el.checked = !!val;
        } else {
          el.value = val;
        }

        changeInput(el);
      }
    }
  }

  // 事实与理由
  function ssyly(val) {
    const el = document.querySelector('textarea');

    el.value = val;
    changeInput(el);
  }

  // 上传起诉材料
  function scqscl() {
    document.querySelector('.upload').click();
  }

  function extractVal(content, key) {
    return content.split(key)[1].split('，')[0].substring(1).replace('。', '').replace('：', '').trim();
  }

  function changeInput(el) {
    // el.dispatchEvent(new Event('input'));
    // el.dispatchEvent(new Event('change'));
    el.dispatchEvent(new Event('keyup'));
  }

  function parseDoc(content) {
    let blocks_ = content.split('\n\n').filter(Boolean);
    let blocks = blocks_.slice(1, 4);

    const dsr = blocks[0].split('\n').splice(2);

    const bg = zrr();
    const bg2 = zrr();
    const bg_fr = fr();

    bg.xm = extractVal(dsr[0], '被告');
    bg.zjhm = extractVal(dsr[0], '身份证号');
    bg.zsd = extractVal(dsr[0], '住址');
    bg.sswssdd = extractVal(dsr[0], '送达地址');
    bg.jcjz = bg.sswssdd;
    bg.lxdh1 = extractVal(dsr[0], '联系电话');

    if (dsr.length === 2) {
      bg2.xm = extractVal(dsr[1], '被告二');
      bg2.zjhm = extractVal(dsr[1], '身份证号');
      bg2.sswssdd = extractVal(dsr[1], '送达地址');
      bg2.jcjz = bg2.sswssdd;
      bg2.lxdh1 = extractVal(dsr[1], '联系电话');
    } else if (dsr.length === 3) {
      bg_fr.xm = extractVal(dsr[1], '被告二');
      bg_fr.shxydm = extractVal(dsr[1], '统一社会信用代码');
      bg_fr.zsd = extractVal(dsr[1], '注册地址');
      bg_fr.sswssdd = extractVal(dsr[1], '送达地址');
      bg_fr.jcjz = bg_fr.sswssdd;
      bg_fr.lxdh1 = extractVal(dsr[1], '联系电话');
      bg_fr.fddbr = extractVal(dsr[2], '法定代表人');
    }

    const ssqq = blocks[1]
      .split('\n')
      .splice(1)
      .map((item) => item.substring(2, item.length - 1));

    ssqq[0] = ssqq[0].split('(')[0];
    ssqq[1] = ssqq[1].split('【')[0];

    const ssyly = blocks[2].split('\n').splice(1).join('\n').replace(/15%/g, '百分之十五');

    return {
      bde: ssqq[2].split('合计为')[1].replace('元', ''),
      SQFY: '嘉定区人民法院',
      bg,
      bg2,
      bg_fr,
      ssqq,
      ssyly,
    };
  }

  function fillValue(content) {
    const meta = parseDoc(content);

    bde(meta.bde);
    sqslfy(meta.SQFY);

    const tables = document.querySelectorAll('#dsrxx table');
    const adds = document.querySelectorAll('#dsr_bg .dsr-btn-small');
    const isCreate = tables.length === 0;

    if (isCreate) {
      adds[0].click();
    }

    dsrxx(meta.bg);

    if (meta.bg2.xm) {
      if (isCreate) {
        adds[0].click();
      }

      dsrxx(meta.bg2, 'bg', 'zrr', 2);
    } else if (meta.bg_fr.xm) {
      if (isCreate) {
        adds[1].click();
      }

      dsrxx(meta.bg_fr, 'bg', 'fr', 2);
    }

    ssqq(meta.ssqq);
    ssyly(meta.ssyly);
  }

  function createUI() {
    const div = document.createElement('div');
    const style = `
    position: fixed;
    right: 10px;
    top: 100px;
    padding: 8px;
    background: #fff;
    border: 1px solid;
    `;

    div.style = style;
    div.innerHTML = `<div>
    <textarea rows="10" id="_word-content" placeholder="粘贴诉状"></textarea>
    </div>
    <div style="display: flex; justify-content: space-between; margin-top: 8px;">
      <div>
        <button style="margin-right: 4px;" id="_reset-btn">重置</button>
        <button id="_fill-btn">填写</button>
      </div>
      <div>
        <button id="_upload-btn">上传材料</button>
      </div>
    </div>`;

    document.body.appendChild(div);
  }

  function initEvent() {
    const inputEl = document.getElementById('_word-content');
    const reset = document.getElementById('_reset-btn');
    const fill = document.getElementById('_fill-btn');
    const upload = document.getElementById('_upload-btn');

    reset.addEventListener('click', () => {
      inputEl.value = '';
    });

    fill.addEventListener('click', () => {
      fillValue(inputEl.value);
      reset.click();
    });
    upload.addEventListener('click', scqscl);
  }

  createUI();
  initEvent();
})();
