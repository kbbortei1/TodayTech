/**
 * TodayTech Dashboard Logic
 * Clean Vanilla JS with SVG icons, interactive filtering, and modal controls.
 */

// SVG Icon Helpers
const ICONS = {
  award: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="7"></circle><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline></svg>`,
  mapPin: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>`,
  calendar: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>`,
  bookmarkOutline: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>`,
  bookmarkFilled: `<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>`,
  check: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
  alert: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`,
  externalLink: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>`,
  copy: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`
};

let currentFilter = 'all';
let currentStatus = 'radar';
let currentClosingOnly = false;
let currentSearch = '';
let activeOpportunity = null;

document.addEventListener('DOMContentLoaded', () => {
  loadStats();
  loadOpportunities();
  setupEventListeners();
});

function setupEventListeners() {
  // Search input
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      currentSearch = e.target.value.trim();
      loadOpportunities();
    });
  }

  // Filter pills
  document.querySelectorAll('.pill-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.pill-btn').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.type || 'all';
      loadOpportunities();
    });
  });

  // Interactive Stats Chips
  document.querySelectorAll('.stat-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.stat-chip').forEach((c) => c.classList.remove('active'));
      chip.classList.add('active');
      
      currentStatus = chip.dataset.status || 'radar';
      currentClosingOnly = chip.dataset.closing === 'true';
      loadOpportunities();
    });
  });

  // Drawer close events
  const drawerClose = document.getElementById('drawerClose');
  const drawerBackdrop = document.getElementById('drawerBackdrop');
  if (drawerClose) drawerClose.addEventListener('click', closeDrawer);
  if (drawerBackdrop) drawerBackdrop.addEventListener('click', closeDrawer);

  // Scan button
  const scanBtn = document.getElementById('scanBtn');
  if (scanBtn) {
    scanBtn.addEventListener('click', triggerScan);
  }

  // Settings Modal events
  const settingsBtn = document.getElementById('settingsBtn');
  const settingsModalClose = document.getElementById('settingsModalClose');
  const settingsCancelBtn = document.getElementById('settingsCancelBtn');
  const settingsSaveBtn = document.getElementById('settingsSaveBtn');
  const settingsModalBackdrop = document.getElementById('settingsModalBackdrop');

  if (settingsBtn) settingsBtn.addEventListener('click', openSettingsModal);
  if (settingsModalClose) settingsModalClose.addEventListener('click', closeSettingsModal);
  if (settingsCancelBtn) settingsCancelBtn.addEventListener('click', closeSettingsModal);
  if (settingsSaveBtn) settingsSaveBtn.addEventListener('click', saveSettings);
  if (settingsModalBackdrop) {
    settingsModalBackdrop.addEventListener('click', (e) => {
      if (e.target === settingsModalBackdrop) closeSettingsModal();
    });
  }
}

async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const data = await res.json();
    
    document.getElementById('statTotal').textContent = data.total_opportunities || '0';
    document.getElementById('statClosing').textContent = data.closing_soon_count || '0';
    document.getElementById('statSaved').textContent = data.saved_count || '0';
    document.getElementById('statDrafting').textContent = data.drafting_count || '0';
  } catch (err) {
    console.error('Failed to load stats', err);
  }
}

async function loadOpportunities() {
  const container = document.getElementById('cardsGrid');
  if (!container) return;

  try {
    let url = `/api/opportunities?status=${currentStatus}`;
    if (currentClosingOnly) {
      url += `&closing_soon=true`;
    }
    if (currentFilter !== 'all') {
      url += `&type=${encodeURIComponent(currentFilter)}`;
    }
    if (currentSearch) {
      url += `&query=${encodeURIComponent(currentSearch)}`;
    }

    const res = await fetch(url);
    if (!res.ok) throw new Error('API error');
    const items = await res.json();

    if (items.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 48px 24px; text-align: center; background: #fff; border-radius: 12px; border: 1px solid var(--border-subtle);">
          <h3 style="font-family: var(--font-serif); font-size: 22px; margin-bottom: 8px;">No opportunities found</h3>
          <p style="color: var(--text-muted); font-size: 14px;">Try loosening your filters or search terms.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = items.map((opp) => renderCard(opp)).join('');
    updatePipeline(items);
  } catch (err) {
    console.error('Failed to load opportunities', err);
    container.innerHTML = `<p style="color: var(--text-muted); padding: 24px;">Failed to load opportunities.</p>`;
  }
}

function renderCard(opp) {
  const typeClass = `type-${opp.type.toLowerCase()}`;
  
  let deadlineBadge = `<span class="tag-comfortable">${ICONS.calendar} ${opp.deadline || 'Open enrollment'}</span>`;
  if (opp.days_left !== null && opp.days_left !== undefined) {
    if (opp.days_left <= 3) {
      deadlineBadge = `<span class="tag-urgent">${ICONS.calendar} ${opp.days_left}d left (${opp.deadline})</span>`;
    } else if (opp.days_left <= 7) {
      deadlineBadge = `<span class="tag-urgent" style="background:#FDF7ED; color:#C88A32; border-color:#F7E8CE;">${ICONS.calendar} ${opp.days_left}d left</span>`;
    } else {
      deadlineBadge = `<span class="tag-comfortable">${ICONS.calendar} ${opp.days_left}d left</span>`;
    }
  }

  const isSaved = opp.status === 'saved';
  const saveIcon = isSaved ? ICONS.bookmarkFilled : ICONS.bookmarkOutline;
  const saveLabel = isSaved ? 'Saved' : 'Save';

  return `
    <article class="card">
      <div class="card-top" onclick="openAssistant('${opp.id}')" style="cursor: pointer;">
        <span class="type-tag ${typeClass}">${opp.type}</span>
        <span class="badge-score">
          ${ICONS.check}
          ${opp.fit_score}% Match
        </span>
      </div>

      <h2 class="card-title" onclick="openAssistant('${opp.id}')" title="Click to view requirements and prepare drafts">
        ${escapeHtml(opp.title)}
      </h2>
      <p class="card-org">${escapeHtml(opp.organizer)}</p>

      <div class="card-metadata" onclick="openAssistant('${opp.id}')" style="cursor: pointer;">
        <div class="meta-row">
          <span class="meta-icon">${ICONS.award}</span>
          <span class="meta-highlight">${escapeHtml(opp.reward || 'Recognition & Experience')}</span>
        </div>
        <div class="meta-row">
          <span class="meta-icon">${ICONS.mapPin}</span>
          <span>${escapeHtml(opp.mode)} • ${escapeHtml(opp.location)}</span>
        </div>
        <div class="meta-row">
          <span class="meta-icon" style="color: inherit;"></span>
          ${deadlineBadge}
        </div>
      </div>

      <p class="card-reason">${escapeHtml(opp.fit_reason || 'Strong match for your profile')}</p>

      <div class="card-actions">
        <button class="btn btn-primary btn-sm" onclick="openAssistant('${opp.id}')">
          Prepare Application
        </button>
        <button class="btn-link" onclick="toggleSave('${opp.id}', '${opp.status}')" style="display: inline-flex; align-items: center; gap: 5px;">
          ${saveIcon}
          <span>${saveLabel}</span>
        </button>
      </div>
    </article>
  `;
}

function updatePipeline(items) {
  const pipelineContainer = document.getElementById('pipelineList');
  if (!pipelineContainer) return;

  const activeItems = items.filter(i => i.status === 'saved' || i.status === 'in_progress' || i.status === 'applied');
  
  if (activeItems.length === 0) {
    pipelineContainer.innerHTML = `
      <p style="color: var(--text-muted); font-size: 13px; font-style: italic;">
        No targets saved yet. Click "Save" on any opportunity card to track it here.
      </p>
    `;
    return;
  }

  pipelineContainer.innerHTML = activeItems.map(item => `
    <div class="pipeline-item" onclick="openAssistant('${item.id}')" title="Click to prepare materials">
      <div class="pipeline-item-top">
        <span class="pipeline-item-title">${escapeHtml(item.title.substring(0, 30))}...</span>
        <span class="status-badge status-${item.status}">${item.status.replace('_', ' ')}</span>
      </div>
      <div style="font-size: 12px; color: var(--text-muted); display: flex; align-items: center; gap: 5px; margin-top: 4px;">
        ${ICONS.calendar} ${item.deadline ? 'Due: ' + item.deadline : 'Open'}
      </div>
    </div>
  `).join('');
}

async function toggleSave(id, currentStatus) {
  const nextStatus = currentStatus === 'saved' ? 'radar' : 'saved';
  try {
    await fetch(`/api/opportunity/${id}/state`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: nextStatus })
    });
    showToast(nextStatus === 'saved' ? 'Saved to your active pipeline' : 'Removed from active pipeline');
    loadStats();
    loadOpportunities();
  } catch (err) {
    console.error('Failed to toggle save state', err);
  }
}

async function openAssistant(id) {
  const drawer = document.getElementById('drawer');
  const backdrop = document.getElementById('drawerBackdrop');
  const content = document.getElementById('drawerContent');

  drawer.classList.add('active');
  backdrop.classList.add('active');
  content.innerHTML = `<div style="padding: 40px; text-align: center; color: var(--text-muted);">Loading opportunity details...</div>`;

  try {
    const res = await fetch(`/api/opportunity/${id}`);
    const data = await res.json();
    activeOpportunity = data;

    document.getElementById('drawerTitle').textContent = data.title;

    content.innerHTML = `
      <div class="studio-section">
        <div style="display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap;">
          <span class="type-tag type-${data.type.toLowerCase()}">${data.type}</span>
          <span class="badge-score">${ICONS.check} ${data.fit_score}% Match</span>
          <span class="tag-comfortable">Organized by ${escapeHtml(data.organizer)}</span>
        </div>
        <p style="font-size: 14px; color: var(--text-muted); margin-bottom: 16px;">
          ${escapeHtml(data.fit_reason)}
        </p>
      </div>

      <div class="studio-section">
        <h3 class="studio-section-title">Eligibility Criteria Breakdown</h3>
        <div class="checklist-box">
          <div class="checklist-item">
            <span style="color: var(--accent-sage-text);">${ICONS.check}</span>
            <span><strong>Verdict:</strong> ${data.eligibility_verdict} — ${escapeHtml(data.eligibility_reason)}</span>
          </div>
          <div class="checklist-item">
            <span style="color: var(--text-muted);">${ICONS.mapPin}</span>
            <span><strong>Mode & Location:</strong> ${escapeHtml(data.mode)} (${escapeHtml(data.location)})</span>
          </div>
          <div class="checklist-item">
            <span style="color: var(--text-muted);">${ICONS.award}</span>
            <span><strong>Fee:</strong> ${data.cost > 0 ? '$' + data.cost : 'No application fee'}</span>
          </div>
          <div class="checklist-item">
            <span style="color: var(--text-muted);">${ICONS.calendar}</span>
            <span><strong>Deadline:</strong> ${data.deadline ? data.deadline + ' (' + (data.days_left !== null ? data.days_left + 'd left' : '') + ')' : 'Open enrollment'}</span>
          </div>
        </div>
      </div>

      <div class="studio-section">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
          <h3 class="studio-section-title" style="margin: 0;">Tailored Application Studio</h3>
          <button class="btn btn-primary btn-sm" id="generateDraftBtn" onclick="generateDrafts('${data.id}')">
            Generate Tailored Draft
          </button>
        </div>
        <div id="draftContainer">
          <p style="font-size: 13.5px; color: var(--text-muted); line-height: 1.6;">
            Click <strong>Generate Tailored Draft</strong> to run TodayTech's application assistant. It analyzes the opportunity requirements and synthesizes your profile into a focused personal statement or project pitch.
          </p>
        </div>
      </div>
    `;

    document.getElementById('applyExternalLink').href = data.application_url || '#';
  } catch (err) {
    console.error('Failed to open assistant', err);
    content.innerHTML = `<p style="color: var(--accent-terracotta-text); padding: 24px;">Failed to load opportunity details.</p>`;
  }
}

async function generateDrafts(id) {
  const draftContainer = document.getElementById('draftContainer');
  const generateBtn = document.getElementById('generateDraftBtn');
  
  generateBtn.disabled = true;
  generateBtn.textContent = 'Generating draft...';
  draftContainer.innerHTML = `
    <div style="padding: 24px; text-align: center; color: var(--text-muted); background: var(--bg-surface-subtle); border-radius: 8px;">
      <p style="font-weight: 500; margin-bottom: 6px;">Synthesizing requirements and profile experience...</p>
      <p style="font-size: 12.5px;">This drafts materials into data/drafts/ as Markdown and Word DOCX.</p>
    </div>
  `;

  try {
    const res = await fetch(`/api/opportunity/${id}/apply`, { method: 'POST' });
    const result = await res.json();

    draftContainer.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
        <span style="font-size: 12.5px; font-weight: 600; color: var(--accent-sage-text);">Materials Drafted Successfully</span>
        <button class="btn-link" onclick="copyDraftText()" style="display: inline-flex; align-items: center; gap: 5px;">
          ${ICONS.copy}
          <span>Copy Text</span>
        </button>
      </div>
      <div class="draft-box" id="draftTextBox">${escapeHtml(result.summary)}</div>
    `;
    showToast('Application drafts created in data/drafts/');
    loadStats();
    loadOpportunities();
  } catch (err) {
    draftContainer.innerHTML = `<p style="color: var(--accent-terracotta-text);">Draft generation failed. Make sure your LLM provider key is set in .env.</p>`;
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = 'Regenerate Draft';
  }
}

function copyDraftText() {
  const box = document.getElementById('draftTextBox');
  if (!box) return;
  navigator.clipboard.writeText(box.textContent).then(() => {
    showToast('Copied draft materials to clipboard!');
  });
}

function closeDrawer() {
  document.getElementById('drawer').classList.remove('active');
  document.getElementById('drawerBackdrop').classList.remove('active');
}

// ──────────────────────────────────────────────────────────────────────────
// Settings / Profile Modal
// ──────────────────────────────────────────────────────────────────────────

async function openSettingsModal() {
  const modalBackdrop = document.getElementById('settingsModalBackdrop');
  modalBackdrop.classList.add('active');

  try {
    const res = await fetch('/api/profile');
    if (!res.ok) return;
    const profile = await res.json();

    document.getElementById('profName').value = profile.name || '';
    document.getElementById('profCountry').value = profile.country || '';
    document.getElementById('profUniversity').value = profile.university || '';
    document.getElementById('profLevel').value = profile.level || 'undergraduate';
    document.getElementById('profField').value = profile.field_of_study || '';
    document.getElementById('profSkills').value = (profile.skills || []).join(', ');
    document.getElementById('profInterests').value = (profile.interests || []).join(', ');
  } catch (err) {
    console.error('Failed to load profile', err);
  }
}

function closeSettingsModal() {
  document.getElementById('settingsModalBackdrop').classList.remove('active');
}

async function saveSettings() {
  const saveBtn = document.getElementById('settingsSaveBtn');
  saveBtn.disabled = true;
  saveBtn.textContent = 'Saving...';

  const payload = {
    name: document.getElementById('profName').value.trim(),
    country: document.getElementById('profCountry').value.trim(),
    university: document.getElementById('profUniversity').value.trim(),
    level: document.getElementById('profLevel').value,
    field_of_study: document.getElementById('profField').value.trim(),
    skills: document.getElementById('profSkills').value.split(',').map(s => s.trim()).filter(Boolean),
    interests: document.getElementById('profInterests').value.split(',').map(i => i.trim()).filter(Boolean),
  };

  try {
    const res = await fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      closeSettingsModal();
      showToast('Profile and preferences updated successfully');
      loadOpportunities();
    } else {
      showToast('Failed to save profile preferences');
    }
  } catch (err) {
    showToast('Failed to save profile preferences');
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = 'Save Preferences';
  }
}

async function triggerScan() {
  const scanBtn = document.getElementById('scanBtn');
  const scanText = document.getElementById('scanBtnText');
  scanBtn.disabled = true;
  scanText.textContent = 'Scanning...';

  try {
    await fetch('/api/scan', { method: 'POST' });
    showToast('Scan started in background. New matches will populate shortly.');
  } catch (err) {
    showToast('Failed to start scan.');
  } finally {
    setTimeout(() => {
      scanBtn.disabled = false;
      scanText.textContent = 'Scan Sources';
      loadStats();
      loadOpportunities();
    }, 2500);
  }
}

// ──────────────────────────────────────────────────────────────────────────
// Toast Notifications
// ──────────────────────────────────────────────────────────────────────────

function showToast(message) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `
    <span style="color: var(--accent-sage-text); display: flex; align-items: center;">${ICONS.check}</span>
    <span>${escapeHtml(message)}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => toast.classList.add('visible'), 10);

  setTimeout(() => {
    toast.classList.remove('visible');
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
