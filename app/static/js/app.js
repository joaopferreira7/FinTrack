/* ── STATE ── */
let chartLinha = null;
let chartPizza = null;
let categorias = [];
let chatHistorico = [];
const now = new Date();

/* ── INIT ── */
document.addEventListener('DOMContentLoaded', () => {
  initMonthPicker();
  loadCategorias().then(() => {
    loadDashboard();
    loadGastos();
    loadAlertas();
    loadCatsList();
  });
  document.getElementById('f-data').value = now.toISOString().slice(0, 10);

  // Enviar chat com Enter
  const chatInput = document.getElementById('chat-input');
  if (chatInput) {
    chatInput.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); enviarChat(); }
    });
  }
});

/* ── NAVIGATION ── */
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  event.currentTarget.classList.add('active');
  if (name === 'gastos') loadGastos();
  if (name === 'alertas') loadAlertas();
  if (name === 'categorias') loadCatsList();
  if (name === 'dashboard') loadDashboard();
}

/* ── TOAST ── */
function toast(msg, error = false) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'show' + (error ? ' error' : '');
  setTimeout(() => t.className = '', 3000);
}

/* ── MONTH PICKER ── */
function initMonthPicker() {
  const selMes = document.getElementById('sel-mes');
  const selAno = document.getElementById('sel-ano');
  selMes.value = now.getMonth() + 1;
  for (let y = now.getFullYear(); y >= now.getFullYear() - 3; y--) {
    const o = document.createElement('option');
    o.value = y; o.textContent = y;
    selAno.appendChild(o);
  }
}

function getMes() { return +document.getElementById('sel-mes').value; }
function getAno() { return +document.getElementById('sel-ano').value; }

/* ── CATEGORIAS ── */
async function loadCategorias() {
  const r = await fetch('/api/categorias/');
  categorias = await r.json();
  populateCatSelects();
}

function populateCatSelects() {
  ['f-cat', 'filtro-cat', 'edit-cat'].forEach(id => {
    const sel = document.getElementById(id);
    if (!sel) return;
    const isFilter = id === 'filtro-cat';
    sel.innerHTML = isFilter ? '<option value="">Todas categorias</option>' : '';
    categorias.forEach(c => {
      const o = document.createElement('option');
      o.value = c.id;
      o.textContent = `${c.icone} ${c.nome}`;
      sel.appendChild(o);
    });
  });
}

async function loadCatsList() {
  await loadCategorias();
  const list = document.getElementById('cats-list');
  if (!categorias.length) {
    list.innerHTML = '<div class="empty"><div class="empty-icon">🏷️</div><div class="empty-text">Nenhuma categoria</div></div>';
    return;
  }
  list.innerHTML = categorias.map(c => `
    <div class="gasto-item">
      <span class="gasto-icone">${c.icone}</span>
      <div class="gasto-info">
        <div class="gasto-desc">${c.nome}</div>
        <div class="gasto-meta" style="color:${c.cor}">limite: R$ ${fmtNum(c.limite_mensal)}</div>
      </div>
      <div class="gasto-actions">
        <button class="btn btn-danger" onclick="deletarCategoria(${c.id})">🗑</button>
      </div>
    </div>
  `).join('');
}

function openModalCat() {
  document.getElementById('modal-cat').classList.add('open');
}
function closeModalCat() {
  document.getElementById('modal-cat').classList.remove('open');
}

async function salvarCategoria() {
  const payload = {
    nome: document.getElementById('mc-nome').value,
    icone: document.getElementById('mc-icone').value || '📦',
    cor: document.getElementById('mc-cor').value,
    limite_mensal: parseFloat(document.getElementById('mc-limite').value) || 0,
  };
  if (!payload.nome) { toast('Informe o nome da categoria', true); return; }
  const r = await fetch('/api/categorias/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (r.ok) {
    toast('✔ Categoria criada!');
    closeModalCat();
    await loadCategorias();
    loadCatsList();
  } else {
    const e = await r.json();
    toast(e.erro || 'Erro ao criar categoria', true);
  }
}

async function deletarCategoria(id) {
  if (!confirm('Remover esta categoria e todos seus gastos?')) return;
  const r = await fetch(`/api/categorias/${id}`, { method: 'DELETE' });
  if (r.ok) { toast('Categoria removida'); await loadCategorias(); loadCatsList(); }
  else toast('Erro ao remover categoria', true);
}

/* ── DASHBOARD ── */
async function loadDashboard() {
  const mes = getMes(), ano = getAno();
  const r = await fetch(`/api/dashboard/?mes=${mes}&ano=${ano}`);
  const d = await r.json();

  document.getElementById('d-total').textContent = 'R$ ' + fmtNum(d.total_mes);
  document.getElementById('d-qtd').textContent = `${d.quantidade_gastos} transações`;
  document.getElementById('d-alertas').textContent = d.alertas_pendentes;

  // badge
  const badge = document.getElementById('badge-alertas');
  badge.textContent = d.alertas_pendentes;
  badge.style.display = d.alertas_pendentes > 0 ? 'inline-block' : 'none';

  // ── FIX: sempre limpa antes de preencher ──
  document.getElementById('d-maior-cat').textContent = '—';
  document.getElementById('d-maior-val').textContent = '—';

  if (d.por_categoria.length) {
    const maior = d.por_categoria.reduce((a, b) => a.total > b.total ? a : b);
    document.getElementById('d-maior-cat').textContent = `${maior.categoria.icone} ${maior.categoria.nome}`;
    document.getElementById('d-maior-val').textContent = `R$ ${fmtNum(maior.total)} (${maior.percentual}%)`;
  }

  // limites estourados
  const estourados = d.por_categoria.filter(c => c.uso_limite_pct >= 100).length;
  document.getElementById('d-estourados').textContent = estourados;

  renderChartLinha(d.por_dia);
  renderChartPizza(d.por_categoria);
  renderCatLimits(d.por_categoria);
}

function renderChartLinha(dados) {
  const ctx = document.getElementById('chart-linha').getContext('2d');
  if (chartLinha) chartLinha.destroy();
  chartLinha = new Chart(ctx, {
    type: 'line',
    data: {
      labels: dados.map(d => d.data.slice(8)),
      datasets: [{
        label: 'Gastos (R$)',
        data: dados.map(d => d.total),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16,185,129,.12)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#10b981',
        pointRadius: 4,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: '#1e2d47' }, ticks: { color: '#64748b', font: { family: 'DM Mono' } } },
        y: { grid: { color: '#1e2d47' }, ticks: { color: '#64748b', font: { family: 'DM Mono' }, callback: v => 'R$' + v } },
      }
    }
  });
}

function renderChartPizza(dados) {
  const ctx = document.getElementById('chart-pizza').getContext('2d');
  if (chartPizza) chartPizza.destroy();
  if (!dados.length) return;
  chartPizza = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: dados.map(d => d.categoria.nome),
      datasets: [{
        data: dados.map(d => d.total),
        backgroundColor: dados.map(d => d.categoria.cor),
        borderWidth: 0,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { color: '#e2e8f0', font: { family: 'DM Mono', size: 12 }, padding: 16 } }
      },
      cutout: '65%',
    }
  });
}

function renderCatLimits(dados) {
  const body = document.getElementById('cat-limits-body');
  if (!dados.length) { body.innerHTML = '<tr><td colspan="4" style="color:var(--muted);text-align:center;padding:20px">Sem dados</td></tr>'; return; }
  body.innerHTML = dados.map(c => {
    const pct = Math.min(c.uso_limite_pct, 100);
    const cor = pct >= 100 ? 'var(--red)' : pct >= 80 ? 'var(--yellow)' : 'var(--green)';
    return `<tr class="cat-row">
      <td>${c.categoria.icone} ${c.categoria.nome}</td>
      <td style="font-family:var(--mono)">R$ ${fmtNum(c.total)}</td>
      <td style="font-family:var(--mono);color:var(--muted)">${c.limite_mensal > 0 ? 'R$ ' + fmtNum(c.limite_mensal) : '—'}</td>
      <td style="min-width:120px">
        ${c.limite_mensal > 0 ? `
          <span style="font-family:var(--mono);font-size:12px;color:${cor}">${c.uso_limite_pct}%</span>
          <div class="progress-bar"><div class="progress-fill" style="width:${pct}%;background:${cor}"></div></div>
        ` : '<span style="color:var(--muted);font-size:12px">sem limite</span>'}
      </td>
    </tr>`;
  }).join('');
}

/* ── GASTOS ── */
async function loadGastos() {
  const catId = document.getElementById('filtro-cat').value;
  const mes = getMes(), ano = getAno();
  let url = `/api/gastos/?mes=${mes}&ano=${ano}`;
  if (catId) url += `&categoria_id=${catId}`;
  const r = await fetch(url);
  const gastos = await r.json();
  const list = document.getElementById('gastos-list');

  if (!gastos.length) {
    list.innerHTML = '<div class="empty"><div class="empty-icon">📭</div><div class="empty-text">Nenhum gasto registrado neste período</div></div>';
    return;
  }

  list.innerHTML = gastos.map(g => `
    <div class="gasto-item">
      <span class="gasto-icone">${g.categoria?.icone || '📦'}</span>
      <div class="gasto-info">
        <div class="gasto-desc">${g.descricao}</div>
        <div class="gasto-meta">${g.categoria?.nome || '—'} · ${fmtDate(g.data)}</div>
      </div>
      <div class="gasto-valor">- R$ ${fmtNum(g.valor)}</div>
      <div class="gasto-actions">
        <button class="btn btn-ghost" style="padding:6px 12px;font-size:12px" onclick="abrirEdicao(${g.id},'${g.descricao}',${g.valor},'${g.data}',${g.categoria_id})">✏</button>
        <button class="btn btn-danger" onclick="deletarGasto(${g.id})">🗑</button>
      </div>
    </div>
  `).join('');
}

async function registrarGasto() {
  const payload = {
    descricao:    document.getElementById('f-desc').value,
    valor:        parseFloat(document.getElementById('f-valor').value),
    data:         document.getElementById('f-data').value,
    categoria_id: parseInt(document.getElementById('f-cat').value),
  };
  if (!payload.descricao || !payload.valor || !payload.categoria_id) {
    toast('Preencha todos os campos', true);
    return;
  }
  const r = await fetch('/api/gastos/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (r.ok) {
    toast('✔ Gasto registrado!');
    document.getElementById('f-desc').value = '';
    document.getElementById('f-valor').value = '';
    // ── FIX: atualiza lista de gastos também ──
    loadGastos();
    loadDashboard();
    loadAlertas();
  } else {
    const e = await r.json();
    toast(e.erro || 'Erro ao salvar', true);
  }
}

function abrirEdicao(id, desc, valor, data, catId) {
  document.getElementById('edit-id').value = id;
  document.getElementById('edit-desc').value = desc;
  document.getElementById('edit-valor').value = valor;
  document.getElementById('edit-data').value = data;
  document.getElementById('edit-cat').value = catId;
  document.getElementById('modal-edit').classList.add('open');
}

async function salvarEdicao() {
  const id = document.getElementById('edit-id').value;
  const payload = {
    descricao:    document.getElementById('edit-desc').value,
    valor:        parseFloat(document.getElementById('edit-valor').value),
    data:         document.getElementById('edit-data').value,
    categoria_id: parseInt(document.getElementById('edit-cat').value),
  };
  const r = await fetch(`/api/gastos/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (r.ok) {
    toast('✔ Gasto atualizado!');
    document.getElementById('modal-edit').classList.remove('open');
    loadGastos();
    loadDashboard();
  } else toast('Erro ao atualizar', true);
}

async function deletarGasto(id) {
  if (!confirm('Remover este gasto?')) return;
  const r = await fetch(`/api/gastos/${id}`, { method: 'DELETE' });
  if (r.ok) { toast('Gasto removido'); loadGastos(); loadDashboard(); }
  else toast('Erro ao remover', true);
}

/* ── ALERTAS ── */
async function loadAlertas() {
  const r = await fetch('/api/dashboard/alertas');
  const alertas = await r.json();
  const list = document.getElementById('alertas-list');

  const badge = document.getElementById('badge-alertas');
  const naoLidos = alertas.filter(a => !a.lido).length;
  badge.textContent = naoLidos;
  badge.style.display = naoLidos > 0 ? 'inline-block' : 'none';

  if (!alertas.length) {
    list.innerHTML = '<div class="empty"><div class="empty-icon">✅</div><div class="empty-text">Nenhum alerta</div></div>';
    return;
  }

  list.innerHTML = alertas.map(a => `
    <div class="alerta-item ${a.tipo} ${a.lido ? 'lido' : ''}">
      <div style="flex:1">
        <div class="alerta-msg">${a.mensagem}</div>
        <div class="alerta-time">${fmtDatetime(a.criado_em)}</div>
      </div>
      ${!a.lido ? `<button class="btn btn-ghost" style="padding:5px 10px;font-size:12px" onclick="marcarLido(${a.id})">✓ Lido</button>` : ''}
    </div>
  `).join('');
}

async function marcarLido(id) {
  await fetch(`/api/dashboard/alertas/${id}/lido`, { method: 'PATCH' });
  loadAlertas();
}

async function limparAlertas() {
  await fetch('/api/dashboard/alertas/limpar', { method: 'DELETE' });
  loadAlertas();
  toast('Alertas lidos removidos');
}

/* ── IA ── */
async function analisarIA() {
  const box = document.getElementById('ia-response');
  box.style.display = 'block';
  box.innerHTML = '<span class="spinner"></span> Analisando seus gastos com IA...';
  const r = await fetch('/api/ia/analisar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mes: getMes(), ano: getAno() }),
  });
  const d = await r.json();
  box.textContent = d.analise;
}

async function dicaIA() {
  const box = document.getElementById('ia-response');
  box.style.display = 'block';
  box.innerHTML = '<span class="spinner"></span> Buscando dica do dia...';
  const r = await fetch('/api/ia/dica');
  const d = await r.json();
  box.textContent = '💡 ' + d.dica;
}

/* ── CHAT IA ── */
function appendChatMsg(role, text) {
  const msgs = document.getElementById('chat-msgs');
  const div = document.createElement('div');
  div.className = 'chat-msg chat-' + role;
  div.textContent = text;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

async function enviarChat() {
  const input = document.getElementById('chat-input');
  const mensagem = input.value.trim();
  if (!mensagem) return;
  input.value = '';
  input.disabled = true;

  appendChatMsg('user', mensagem);

  // placeholder
  const msgs = document.getElementById('chat-msgs');
  const placeholder = document.createElement('div');
  placeholder.className = 'chat-msg chat-assistant chat-loading';
  placeholder.innerHTML = '<span class="spinner"></span>';
  msgs.appendChild(placeholder);
  msgs.scrollTop = msgs.scrollHeight;

  try {
    const r = await fetch('/api/ia/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mes: getMes(),
        ano: getAno(),
        historico: chatHistorico,
        mensagem,
      }),
    });
    const d = await r.json();
    placeholder.remove();

    const resposta = d.resposta || d.erro || 'Erro desconhecido.';
    appendChatMsg('assistant', resposta);

    chatHistorico.push({ role: 'user', content: mensagem });
    chatHistorico.push({ role: 'assistant', content: resposta });
    // manter só últimos 10 turnos
    if (chatHistorico.length > 20) chatHistorico = chatHistorico.slice(-20);
  } catch (e) {
    placeholder.remove();
    appendChatMsg('assistant', '❌ Erro ao conectar com a IA.');
  } finally {
    input.disabled = false;
    input.focus();
  }
}

function limparChat() {
  chatHistorico = [];
  const msgs = document.getElementById('chat-msgs');
  msgs.innerHTML = '<div class="chat-msg chat-assistant">👋 Olá! Sou o FinBot, seu assistente financeiro. Posso analisar seus gastos, responder dúvidas e dar dicas personalizadas. Como posso ajudar?</div>';
}

/* ── UTILS ── */
function fmtNum(n) {
  return (n || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fmtDate(iso) {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}
function fmtDatetime(iso) {
  const dt = new Date(iso);
  return dt.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
