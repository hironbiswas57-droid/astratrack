/**
 * AstraTrack AI - Main Application Controller
 * Synchronizes views, millennial timeline scrubbing, API communication,
 * multi-tier cache memories, cosmos databases, HTML search engine parsing,
 * and Agentic AI interactive dialogues with Novice Guidance.
 */

document.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('mainCanvas');
  
  // High-DPI Canvas Resizing
  function resizeCanvas() {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;
  }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  // Instantiate Sub-Views
  const planetarium = new PlanetariumView(canvas);
  const orbitalView = new OrbitalSentinelView(canvas);

  // Client Memory & Session Tracking
  let clientId = localStorage.getItem('astratrack_client_id');
  if (!clientId) {
    clientId = 'observer_' + Math.random().toString(36).substring(2, 10);
    localStorage.setItem('astratrack_client_id', clientId);
  }
  let clientProfile = { experience_level: 'novice', novice_mode_active: true };

  // Application State
  let currentViewMode = 'planetarium'; // 'planetarium' | 'orbital' | 'stellar3d'
  let currentEpochYear = 2026;
  let currentDayOfYear = 80;
  let isPlayingTimeline = false;
  let playSpeed = 50; // Years per frame
  let activeData = { sky: null, seasons: null, trajectories: null };
  let currentTour = null; // Active guided tour object

  // DOM Elements
  const epochSlider = document.getElementById('epochSlider');
  const epochValueDisplay = document.getElementById('epochValue');
  const epochContextDisplay = document.getElementById('epochContext');
  const playBtn = document.getElementById('playTimelineBtn');
  const viewModeButtons = document.querySelectorAll('.view-btn');
  const quickEpochPills = document.querySelectorAll('.epoch-pill');
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const chatHistory = document.getElementById('chatHistory');
  const suggestionContainer = document.getElementById('suggestionContainer');

  // Novice & Client Profile Controls
  const btnToggleNovice = document.getElementById('btnToggleNovice');
  const clientBadge = document.getElementById('clientBadge');
  const hudClientLevel = document.getElementById('hudClientLevel');
  const noviceWelcomeCard = document.getElementById('noviceWelcomeCard');
  const tourOverlay = document.getElementById('tourOverlay');
  const tourTitle = document.getElementById('tourTitle');
  const tourProgress = document.getElementById('tourProgress');
  const tourStepTitle = document.getElementById('tourStepTitle');
  const tourStepText = document.getElementById('tourStepText');
  const tourStepTip = document.getElementById('tourStepTip');
  const tourPrevBtn = document.getElementById('tourPrevBtn');
  const tourNextBtn = document.getElementById('tourNextBtn');
  const tourCloseBtn = document.getElementById('tourCloseBtn');

  // Cosmos Search & Database Elements
  const cosmosSearchInput = document.getElementById('cosmosSearchInput');
  const cosmosSearchBtn = document.getElementById('cosmosSearchBtn');
  const cosmosCategoryFilter = document.getElementById('cosmosCategoryFilter');
  const checkWebSearch = document.getElementById('checkWebSearch');
  const cosmosSearchResults = document.getElementById('cosmosSearchResults');
  const cosmosBookmarksContainer = document.getElementById('cosmosBookmarksContainer');
  const btnViewCatalog = document.getElementById('btnViewCatalog');
  const btnViewBookmarks = document.getElementById('btnViewBookmarks');
  const catalogCountBadge = document.getElementById('catalogCountBadge');
  const bookmarkCountBadge = document.getElementById('bookmarkCountBadge');

  // HUD Elements
  const hudPoleStar = document.getElementById('hudPoleStar');
  const hudObliquity = document.getElementById('hudObliquity');
  const hudZodiacAge = document.getElementById('hudZodiacAge');
  const hudSeasonStage = document.getElementById('hudSeasonStage');
  const seasonHeroTag = document.getElementById('seasonHeroTag');
  const seasonHeroDesc = document.getElementById('seasonHeroDesc');
  const daysTransitionBadge = document.getElementById('daysTransitionBadge');
  const rulesContainer = document.getElementById('stellarRulesList');
  const trajectoriesContainer = document.getElementById('trajectoriesList');
  const starInspector = document.getElementById('starInspector');
  const starInspectorTitle = document.getElementById('starInspectorTitle');
  const starInspectorContent = document.getElementById('starInspectorContent');
  const closeStarInspector = document.getElementById('closeStarInspector');

  canvas.addEventListener('astratrack:starselected', (event) => loadStarResearch(event.detail));
  if (closeStarInspector) closeStarInspector.addEventListener('click', () => {
    if (starInspector) starInspector.hidden = true;
    planetarium.selectedStar = null;
  });

  // ============================================================================
  //  1. CLIENT MEMORY & PROFILE SYNC
  // ============================================================================
  async function syncClientProfile() {
    try {
      const res = await fetch(`/api/client/profile?client_id=${clientId}`);
      const data = await res.json();
      if (data && data.client) {
        clientProfile = data.client;
        updateClientUI();
      }
    } catch (e) {
      console.warn('Profile sync fallback:', e);
    }
  }

  function updateClientUI() {
    const isNovice = clientProfile.experience_level === 'novice' || clientProfile.novice_mode_active;
    if (hudClientLevel) {
      hudClientLevel.innerText = isNovice ? 'Novice 🌟' : 'Expert 🛰️';
    }
    if (btnToggleNovice) {
      btnToggleNovice.classList.toggle('active', isNovice);
      btnToggleNovice.innerHTML = isNovice ? '🌟 Novice Guide: ON' : '🛰️ Expert Mode';
    }
    if (noviceWelcomeCard) {
      noviceWelcomeCard.style.display = isNovice ? 'flex' : 'none';
    }
  }

  async function toggleNoviceMode() {
    const currentIsNovice = clientProfile.experience_level === 'novice' || clientProfile.novice_mode_active;
    const newLevel = currentIsNovice ? 'expert' : 'novice';
    const newActive = !currentIsNovice;

    try {
      const res = await fetch('/api/client/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          client_id: clientId,
          experience_level: newLevel,
          novice_mode_active: newActive
        })
      });
      const data = await res.json();
      if (data && data.client) {
        clientProfile = data.client;
        updateClientUI();
        appendMessage('assistant', `
          <div style="font-size: 12px; color: var(--accent-gold);">
            ⚡ <strong>Client Profile Updated</strong>: Mode set to <strong>${newLevel.toUpperCase()}</strong>. Memory synchronized with cosmic database.
          </div>
        `);
      }
    } catch (err) {
      console.error('Error toggling novice profile:', err);
    }
  }

  if (btnToggleNovice) btnToggleNovice.addEventListener('click', toggleNoviceMode);
  if (clientBadge) clientBadge.addEventListener('click', toggleNoviceMode);

  // ============================================================================
  //  2. NOVICE GUIDED TOURS ENGINE
  // ============================================================================
  async function launchTour(tourId) {
    try {
      const res = await fetch(`/api/tours/${tourId}`);
      if (!res.ok) return;
      const tour = await res.json();
      currentTour = { ...tour, currentStepIdx: 0 };
      renderTourStep();
      if (tourOverlay) tourOverlay.style.display = 'flex';
    } catch (err) {
      console.error('Failed to launch tour:', err);
    }
  }

  function renderTourStep() {
    if (!currentTour || !currentTour.steps) return;
    const step = currentTour.steps[currentTour.currentStepIdx];
    const totalSteps = currentTour.steps.length;

    if (tourTitle) tourTitle.innerHTML = `${currentTour.icon || '🧭'} ${currentTour.title}`;
    if (tourProgress) tourProgress.innerText = `Step ${currentTour.currentStepIdx + 1} of ${totalSteps}`;
    if (tourStepTitle) tourStepTitle.innerText = step.title;
    if (tourStepText) tourStepText.innerText = step.explanation;
    if (tourStepTip) tourStepTip.innerHTML = `💡 <strong>Navigator Tip:</strong> ${step.tip || 'Observe the coordinate shifts.'}`;

    if (tourPrevBtn) tourPrevBtn.disabled = currentTour.currentStepIdx === 0;
    if (tourNextBtn) {
      tourNextBtn.innerText = currentTour.currentStepIdx === totalSteps - 1 ? 'Finish Tour ✓' : 'Next Step ▶';
    }

    // Execute step UI directive automatically
    if (step.ui_action) {
      executeUIAction(step.ui_action);
    }
  }

  function nextTourStep() {
    if (!currentTour) return;
    if (currentTour.currentStepIdx < currentTour.steps.length - 1) {
      currentTour.currentStepIdx++;
      renderTourStep();
    } else {
      exitTour();
      appendMessage('assistant', `
        <div style="font-size: 12px; color: var(--accent-green);">
          🎉 <strong>Tour Completed</strong>: You've mastered <em>${currentTour.title}</em>! Ask Nova any questions to continue exploring.
        </div>
      `);
    }
  }

  function prevTourStep() {
    if (!currentTour || currentTour.currentStepIdx <= 0) return;
    currentTour.currentStepIdx--;
    renderTourStep();
  }

  function exitTour() {
    if (tourOverlay) tourOverlay.style.display = 'none';
    currentTour = null;
  }

  if (tourNextBtn) tourNextBtn.addEventListener('click', nextTourStep);
  if (tourPrevBtn) tourPrevBtn.addEventListener('click', prevTourStep);
  if (tourCloseBtn) tourCloseBtn.addEventListener('click', exitTour);

  // Attach quick tour pills
  document.querySelectorAll('.tour-pill-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tourId = btn.dataset.tour;
      if (tourId) launchTour(tourId);
    });
  });

  // ============================================================================
  //  3. COSMOS DATABASE & HTML SEARCH ENGINE
  // ============================================================================
  async function searchCosmos(query = '', category = 'all', includeWeb = true) {
    if (cosmosSearchResults) {
      cosmosSearchResults.innerHTML = '<div style="font-size:12px; color:var(--text-dim); padding:10px;">⚡ Parsing cosmic databases and astronomical HTML engines...</div>';
    }

    try {
      const res = await fetch('/api/search/html', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query || (category !== 'all' ? category : 'space'),
          search_web: includeWeb,
          max_results: 15
        })
      });
      const data = await res.json();
      renderCosmosResults(data.results || [], data.from_cache);
      if (catalogCountBadge) catalogCountBadge.innerText = (data.results || []).length;
    } catch (err) {
      console.error('Cosmos search failed:', err);
      if (cosmosSearchResults) {
        cosmosSearchResults.innerHTML = '<div style="color:var(--accent-danger); font-size:12px; padding:10px;">Search request failed. Please retry.</div>';
      }
    }
  }

  function renderCosmosResults(results, fromCache = false) {
    if (!cosmosSearchResults) return;
    cosmosSearchResults.innerHTML = '';

    if (!results || results.length === 0) {
      cosmosSearchResults.innerHTML = '<div style="font-size:12px; color:var(--text-dim); padding:10px;">No cosmic bodies found. Try searching for "nebula", "Apophis", or "Andromeda".</div>';
      return;
    }

    results.forEach(item => {
      const card = document.createElement('div');
      card.className = 'cosmos-card';

      // Badge style
      const category = (item.subtitle || item.type || 'star').toLowerCase();
      let badgeClass = 'badge-cluster';
      if (category.includes('galaxy')) badgeClass = 'badge-galaxy';
      else if (category.includes('nebula')) badgeClass = 'badge-nebula';
      else if (category.includes('exoplanet')) badgeClass = 'badge-exoplanet';
      else if (category.includes('asteroid') || category.includes('comet')) badgeClass = 'badge-asteroid';
      else if (category.includes('black_hole')) badgeClass = 'badge-black_hole';
      else if (item.type === 'parsed_html_engine') badgeClass = 'badge-web';

      const isWeb = item.type === 'parsed_html_engine';

      card.innerHTML = `
        <div class="cosmos-card-header">
          <span class="cosmos-card-title">${item.title}</span>
          <span class="cosmos-badge ${badgeClass}">${isWeb ? 'WEB HTML' : (item.subtitle ? item.subtitle.split(' • ')[0] : 'CATALOG')}</span>
        </div>
        <div class="cosmos-card-meta">
          <span>🔭 ${item.difficulty ? item.difficulty.replace('_', ' ').toUpperCase() : 'ASTRONOMY'}</span>
          <span>📜 ${item.source ? item.source.split(' / ')[0] : 'NASA / SIMBAD'}</span>
        </div>
        <div class="cosmos-card-desc">${item.description}</div>
        <div class="cosmos-card-actions">
          <button class="cosmos-action-btn" data-action="${isWeb ? 'external' : 'inspect'}" data-target="${item.action ? (item.action.target_id || '') : ''}" data-url="${isWeb ? item.url : ''}">
            ${isWeb ? '🔗 View Source Article' : '🔭 Inspect in Observatory'}
          </button>
          ${!isWeb ? `<button class="cosmos-bookmark-btn" data-id="${item.action ? item.action.target_id : ''}" title="Save to Personal Notebook">★ Save</button>` : ''}
        </div>
      `;

      // Event listeners on card buttons
      const actionBtn = card.querySelector('.cosmos-action-btn');
      if (actionBtn) {
        actionBtn.onclick = () => {
          if (isWeb && item.url) {
            window.open(item.url, '_blank');
          } else if (item.action && item.action.target_id) {
            inspectCosmosTarget(item.action.target_id, item.action.view_mode);
          }
        };
      }

      const bookmarkBtn = card.querySelector('.cosmos-bookmark-btn');
      if (bookmarkBtn) {
        bookmarkBtn.onclick = () => saveBookmark(item.action ? item.action.target_id : '');
      }

      cosmosSearchResults.appendChild(card);
    });
  }

  function inspectCosmosTarget(targetId, viewMode = 'planetarium') {
    if (viewMode === 'orbital' || ['apophis', 'halley', 'bennu'].includes(targetId.toLowerCase())) {
      orbitalView.selectTarget(targetId);
      switchViewMode('orbital');
    } else {
      switchViewMode('planetarium');
    }
  }

  async function saveBookmark(objectId) {
    if (!objectId) return;
    try {
      const res = await fetch('/api/client/bookmarks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id: clientId, object_id: objectId })
      });
      const data = await res.json();
      if (data.status === 'saved') {
        loadBookmarks();
        appendMessage('assistant', `
          <div style="font-size:12px; color:var(--accent-gold);">
            ★ <strong>Notebook Saved</strong>: <em>${data.object_name}</em> added to your client memory database.
          </div>
        `);
      }
    } catch (err) {
      console.error('Error saving bookmark:', err);
    }
  }

  async function loadBookmarks() {
    try {
      const res = await fetch(`/api/client/bookmarks?client_id=${clientId}`);
      const data = await res.json();
      const bookmarks = data.bookmarks || [];
      if (bookmarkCountBadge) bookmarkCountBadge.innerText = bookmarks.length;
      renderBookmarks(bookmarks);
    } catch (err) {
      console.error('Error loading bookmarks:', err);
    }
  }

  function renderBookmarks(bookmarks) {
    if (!cosmosBookmarksContainer) return;
    cosmosBookmarksContainer.innerHTML = '';

    if (!bookmarks || bookmarks.length === 0) {
      cosmosBookmarksContainer.innerHTML = '<div style="font-size:12px; color:var(--text-dim); padding:10px;">Your notebook is empty. Click "★ Save" on any cosmic object to remember it!</div>';
      return;
    }

    bookmarks.forEach(b => {
      const card = document.createElement('div');
      card.className = 'cosmos-card';
      card.innerHTML = `
        <div class="cosmos-card-header">
          <span class="cosmos-card-title">${b.object_name}</span>
          <span class="cosmos-badge badge-cluster">${b.category.toUpperCase()}</span>
        </div>
        <div class="cosmos-card-desc">${b.description || 'Saved celestial anchor in personal observation notebook.'}</div>
        <div class="cosmos-card-actions">
          <button class="cosmos-action-btn" onclick="inspectCosmosTarget('${b.object_id}')">🔭 Inspect</button>
          <button class="tour-close-btn" style="padding:2px 6px; font-size:10px;" data-remove="${b.object_id}">Remove ✕</button>
        </div>
      `;
      const removeBtn = card.querySelector('[data-remove]');
      if (removeBtn) {
        removeBtn.onclick = () => deleteBookmark(b.object_id);
      }
      cosmosBookmarksContainer.appendChild(card);
    });
  }

  async function deleteBookmark(objectId) {
    try {
      await fetch(`/api/client/bookmarks/${objectId}?client_id=${clientId}`, { method: 'DELETE' });
      loadBookmarks();
    } catch (err) {
      console.error('Error deleting bookmark:', err);
    }
  }

  // Hook up Cosmos Search Box
  if (cosmosSearchBtn && cosmosSearchInput) {
    cosmosSearchBtn.addEventListener('click', () => {
      searchCosmos(cosmosSearchInput.value, cosmosCategoryFilter ? cosmosCategoryFilter.value : 'all', checkWebSearch ? checkWebSearch.checked : true);
    });
    cosmosSearchInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        searchCosmos(cosmosSearchInput.value, cosmosCategoryFilter ? cosmosCategoryFilter.value : 'all', checkWebSearch ? checkWebSearch.checked : true);
      }
    });
  }
  if (cosmosCategoryFilter) {
    cosmosCategoryFilter.addEventListener('change', () => {
      searchCosmos(cosmosSearchInput ? cosmosSearchInput.value : '', cosmosCategoryFilter.value, checkWebSearch ? checkWebSearch.checked : true);
    });
  }

  // Switch between Catalog Results and Saved Notebook
  if (btnViewCatalog && btnViewBookmarks) {
    btnViewCatalog.addEventListener('click', () => {
      btnViewCatalog.classList.add('active');
      btnViewBookmarks.classList.remove('active');
      if (cosmosSearchResults) cosmosSearchResults.style.display = 'flex';
      if (cosmosBookmarksContainer) cosmosBookmarksContainer.style.display = 'none';
    });
    btnViewBookmarks.addEventListener('click', () => {
      btnViewBookmarks.classList.add('active');
      btnViewCatalog.classList.remove('active');
      if (cosmosSearchResults) cosmosSearchResults.style.display = 'none';
      if (cosmosBookmarksContainer) cosmosBookmarksContainer.style.display = 'flex';
      loadBookmarks();
    });
  }

  // ============================================================================
  //  4. FETCH ASTRONOMICAL DATASETS
  // ============================================================================
  async function loadSkyData(year) {
    try {
      const res = await fetch(`/api/astronomy/sky?year=${year}`);
      const data = await res.json();
      activeData.sky = data;
      planetarium.setData(data);
      updateSkyHUD(data);
    } catch (e) {
      console.error('Error fetching sky data:', e);
    }
  }

  function formatResearchValue(value, suffix = '', decimals = 2) {
    if (value === null || value === undefined || value === '' || !Number.isFinite(Number(value))) return 'Not reported';
    return `${Number(value).toLocaleString(undefined, { maximumFractionDigits: decimals })}${suffix}`;
  }

  async function loadStarResearch(star) {
    if (!starInspector || !starInspectorContent || !star) return;
    starInspector.hidden = false;
    if (starInspectorTitle) starInspectorTitle.textContent = star.name.split(' (')[0];
    const constellation = (activeData.sky?.constellations || []).find(c => c.id === star.constellation);
    starInspectorContent.innerHTML = `
      <div class="inspector-meta">${escapeHtml(star.constellation || 'Star')} · RA ${escapeHtml(star.ra)}° · Dec ${escapeHtml(star.dec)}°</div>
      <div class="inspector-distance">${formatResearchValue(star.dist_ly, ' light-years')} <span>·</span> ${formatResearchValue(star.distance_au, ' AU', 0)}</div>
      ${constellation ? `<section class="inspector-section"><h3>${escapeHtml(constellation.name)}</h3><p>${escapeHtml(constellation.seasonal_marker || '')}</p></section>` : ''}
      <div class="inspector-loading">Looking up Gaia DR3, NASA's confirmed planet archive, and NASA image records…</div>`;
    try {
      const response = await fetch(`/api/astronomy/stars/${encodeURIComponent(star.id)}/research`);
      if (!response.ok) throw new Error(`Archive lookup returned ${response.status}`);
      const research = await response.json();
      const gaia = research.gaia_dr3;
      const gaiaSection = gaia ? `
        <section class="inspector-section">
          <div class="source-kicker">ESA GAIA DR3 · EPOCH ${formatResearchValue(gaia.reference_epoch, '', 0)}</div>
          <p>Source ${escapeHtml(gaia.source_id)} · G ${formatResearchValue(gaia.g_magnitude)}</p>
          <p>RA ${formatResearchValue(gaia.ra_deg, '°', 5)} · Dec ${formatResearchValue(gaia.dec_deg, '°', 5)}</p>
          <p>Parallax ${formatResearchValue(gaia.parallax_mas, ' mas')} · Proper motion ${formatResearchValue(gaia.proper_motion_ra_mas_yr, ' / ')} ${formatResearchValue(gaia.proper_motion_dec_mas_yr, ' mas/yr')}</p>
          <a href="${escapeHtml(research.sources.gaia_dr3)}" target="_blank" rel="noreferrer">Open Gaia Archive ↗</a>
        </section>` : `<section class="inspector-section"><div class="source-kicker">ESA GAIA DR3</div><p>No Gaia match returned for this catalog position. The map still uses the epoch-propagated AstraTrack catalog coordinates.</p></section>`;

      const planetSection = research.confirmed_planets?.length ? `
        <section class="inspector-section">
          <div class="source-kicker">CONFIRMED PLANETS · NASA EXOPLANET ARCHIVE</div>
          <div class="system-orbit" aria-label="Illustrative orbital sequence">
            <span class="system-star" title="Host star">✦</span>
            ${research.confirmed_planets.map((planet, index) => `<span class="system-planet planet-${index % 5}" title="${escapeHtml(planet.name)}"></span>`).join('')}
            <small>sequence only · spacing not to scale</small>
          </div>
          ${research.confirmed_planets.map(planet => `
            <article class="planet-record">
              <h4>${escapeHtml(planet.name)}</h4>
              <p>${escapeHtml(planet.discovery_method || 'Discovery method not reported')} · ${formatResearchValue(planet.discovery_year, '', 0)}</p>
              <p>Period ${formatResearchValue(planet.orbital_period_days, ' days')} · Semi-major axis ${formatResearchValue(planet.semi_major_axis_au, ' AU')}</p>
              <p>Radius ${formatResearchValue(planet.radius_earth, ' Earth radii')} · Mass ${formatResearchValue(planet.mass_earth, ' Earth masses')}</p>
            </article>`).join('')}
          <a href="${escapeHtml(research.sources.nasa_exoplanet_archive)}" target="_blank" rel="noreferrer">Open NASA Exoplanet Archive ↗</a>
        </section>` : `<section class="inspector-section"><div class="source-kicker">NASA EXOPLANET ARCHIVE</div><p>No confirmed planet record was returned for this host-name query. An empty result does not establish that the star has no planets.</p><a href="${escapeHtml(research.sources.nasa_exoplanet_archive)}" target="_blank" rel="noreferrer">Search the archive ↗</a></section>`;

      const imageSection = research.nasa_images?.length ? `
        <section class="inspector-section">
          <div class="source-kicker">NASA IMAGE AND VIDEO LIBRARY</div>
          <p class="image-caveat">Archive media may include artist concepts. Descriptions below are the NASA asset captions; these are not assumed to be direct images of exoplanets.</p>
          <div class="nasa-image-list">${research.nasa_images.map(image => `
            <a class="nasa-image-card" href="${escapeHtml(image.page_url)}" target="_blank" rel="noreferrer">
              ${image.preview_url ? `<img src="${escapeHtml(image.preview_url)}" alt="${escapeHtml(image.title || 'NASA archive image')}" loading="lazy" onerror="this.hidden=true">` : ''}
              <strong>${escapeHtml(image.title || 'NASA image asset')}</strong>
              <span>${escapeHtml((image.description || '').slice(0, 210))}</span>
              <small>${escapeHtml(image.center || 'NASA')} · ${escapeHtml(image.date_created || '')}</small>
            </a>`).join('')}</div>
        </section>` : `<section class="inspector-section"><div class="source-kicker">NASA IMAGE AND VIDEO LIBRARY</div><p>No related image assets were returned for this search.</p></section>`;

      starInspectorContent.innerHTML = `
        <div class="inspector-meta">${escapeHtml(star.constellation || 'Star')} · RA ${escapeHtml(star.ra)}° · Dec ${escapeHtml(star.dec)}°</div>
        <div class="inspector-distance">${formatResearchValue(star.dist_ly, ' light-years')} <span>·</span> ${formatResearchValue(star.distance_au, ' AU', 0)}</div>
        ${constellation ? `<section class="inspector-section"><h3>${escapeHtml(constellation.name)}</h3><p>${escapeHtml(constellation.seasonal_marker || '')}</p><p>${escapeHtml(constellation.millennial_morph || '')}</p></section>` : ''}
        ${gaiaSection}${planetSection}${imageSection}
        <div class="inspector-footer">Sky position uses AstraTrack's epoch-propagated catalog. Gaia DR3 values are shown separately at their stated reference epoch.</div>`;
    } catch (error) {
      console.warn('Star archive lookup failed:', error);
      starInspectorContent.insertAdjacentHTML('beforeend', '<div class="inspector-error">Open archives are unavailable right now. The local star position remains visible; try inspecting this star again later.</div>');
    }
  }

  async function loadSeasonData(year, day) {
    try {
      const res = await fetch(`/api/astronomy/seasons?year=${year}&day_of_year=${day}`);
      const data = await res.json();
      activeData.seasons = data;
      updateSeasonsUI(data);
    } catch (e) {
      console.error('Error fetching season data:', e);
    }
  }

  async function loadTrajectoryData() {
    try {
      const res = await fetch('/api/astronomy/trajectories?time_offset_yr=0');
      const data = await res.json();
      activeData.trajectories = data;
      orbitalView.setData(data);
      updateTrajectoriesUI(data);
    } catch (e) {
      console.error('Error fetching trajectories:', e);
    }
  }

  // ============================================================================
  //  5. UI UPDATES
  // ============================================================================
  function updateSkyHUD(sky) {
    if (!sky || !sky.pole_telemetry) return;
    const pole = sky.pole_telemetry;
    const closest = pole.closest_pole_star;

    if (hudPoleStar && closest) {
      hudPoleStar.innerText = `${closest.name.split(' (')[0]} (sep ${closest.separation_degrees}°)`;
    }
    if (hudObliquity) {
      hudObliquity.innerText = `${pole.obliquity_degrees}°`;
    }
    if (hudZodiacAge && pole.zodiac_age) {
      hudZodiacAge.innerText = `${pole.zodiac_age.age} (${pole.zodiac_age.symbol})`;
    }
  }

  function updateSeasonsUI(seasons) {
    if (!seasons) return;
    if (hudSeasonStage) hudSeasonStage.innerText = seasons.current_season;
    if (seasonHeroTag) seasonHeroTag.innerHTML = `${seasons.solar_telemetry.season_icon} ${seasons.current_season}`;
    if (seasonHeroDesc) seasonHeroDesc.innerText = seasons.summary;
    if (daysTransitionBadge) daysTransitionBadge.innerText = `${seasons.days_until_next_transition}d to ${seasons.next_season}`;

    if (rulesContainer && seasons.stellar_predictions) {
      rulesContainer.innerHTML = '';
      seasons.stellar_predictions.forEach(rule => {
        const isActive = rule.relevance_score > 0;
        const card = document.createElement('div');
        card.className = 'stellar-rule-card';
        card.innerHTML = `
          <div class="rule-header">
            <span class="rule-star">★ ${rule.star_name}</span>
            <span class="rule-status ${isActive ? 'active' : 'inactive'}">
              ${isActive ? 'ACTIVE ALIGNMENT' : 'DORMANT'}
            </span>
          </div>
          <div class="rule-phenomenon">${rule.phenomenon} • ${rule.culture}</div>
          <div class="rule-prediction"><strong>Prediction:</strong> ${rule.prediction}</div>
          <div class="rule-lore">${rule.scientific_basis}</div>
        `;
        rulesContainer.appendChild(card);
      });
    }
  }

  function updateTrajectoriesUI(trajectories) {
    if (!trajectories || !trajectories.tracked_bodies || !trajectoriesContainer) return;
    trajectoriesContainer.innerHTML = '';

    trajectories.tracked_bodies.forEach(body => {
      const isCritical = body.is_close_approach;
      const card = document.createElement('div');
      card.className = `trajectory-card ${body.id === orbitalView.selectedTargetId ? 'selected' : ''}`;
      card.onclick = () => {
        document.querySelectorAll('.trajectory-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        orbitalView.selectTarget(body.id);
        if (currentViewMode !== 'orbital') {
          switchViewMode('orbital');
        }
      };

      card.innerHTML = `
        <div class="target-title-row">
          <span class="target-name" style="color: ${body.color}">● ${body.name}</span>
          <span class="hazard-badge ${isCritical ? 'hazard-critical' : 'hazard-safe'}">
            ${isCritical ? 'CRITICAL WATCH' : 'TRACKED'}
          </span>
        </div>
        <div class="target-metrics">
          <div>Earth Dist: <strong>${body.distance_earth_ld} LD</strong></div>
          <div>Speed: <strong>${body.position.speed_kms} km/s</strong></div>
          <div>Distance AU: <strong>${body.distance_earth_au} AU</strong></div>
          <div>Diameter: <strong>${body.diameter_m}m</strong></div>
        </div>
        <div class="sat-tracking-badge">
          🛰️ Satellites Linked: ${body.tracking_satellites.length ? body.tracking_satellites.map(s => s.name.split(' ')[0]).join(', ') : 'Ground Radar'}
        </div>
      `;
      trajectoriesContainer.appendChild(card);
    });
  }

  // ============================================================================
  //  6. VIEW & TAB SWITCHERS
  // ============================================================================
  function switchViewMode(mode) {
    currentViewMode = mode;
    viewModeButtons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.mode === mode);
    });
    const legend1 = document.getElementById('legendPlanetarium');
    const legend2 = document.getElementById('legendOrbital');
    const legend3 = document.getElementById('legendStellar3d');
    const distanceNote = document.getElementById('distanceMapNote');
    if (legend1) legend1.style.display = mode === 'planetarium' ? 'flex' : 'none';
    if (legend2) legend2.style.display = mode === 'orbital' ? 'flex' : 'none';
    if (legend3) legend3.style.display = mode === 'stellar3d' ? 'flex' : 'none';
    if (distanceNote) distanceNote.hidden = mode !== 'stellar3d';
    planetarium.distanceMapMode = mode === 'stellar3d';
  }

  viewModeButtons.forEach(btn => {
    btn.addEventListener('click', () => switchViewMode(btn.dataset.mode));
  });

  // Left sidebar tab switcher (Seasons, Astral Radar, Cosmos & Search)
  const sideTabBtns = document.querySelectorAll('.side-tab-btn[data-target]');
  sideTabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      sideTabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const targetId = btn.dataset.target;
      document.querySelectorAll('.side-tab-content').forEach(content => {
        content.style.display = content.id === targetId ? 'block' : 'none';
      });

      // If opening Cosmos tab, load initial search if empty
      if (targetId === 'sectionCosmos' && (!cosmosSearchResults || cosmosSearchResults.children.length === 0)) {
        searchCosmos('', 'all', true);
        loadBookmarks();
      }
    });
  });

  // ============================================================================
  //  7. TIMELINE SLIDER INTERACTION
  // ============================================================================
  function setEpoch(year, triggerChange = true) {
    currentEpochYear = parseFloat(year);
    epochSlider.value = currentEpochYear;
    epochValueDisplay.innerText = currentEpochYear < 0 
      ? `${Math.abs(Math.round(currentEpochYear))} BCE` 
      : `${Math.round(currentEpochYear)} CE`;

    // Epoch context label
    if (currentEpochYear <= -10000) epochContextDisplay.innerText = '• Late Pleistocene / Ice Age (Vega North Star)';
    else if (currentEpochYear <= -2500) epochContextDisplay.innerText = '• Ancient Egypt / Pyramid Era (Thuban North Star)';
    else if (currentEpochYear <= 0) epochContextDisplay.innerText = '• Classical Antiquity / Bronze-Iron Ages';
    else if (currentEpochYear <= 2100) epochContextDisplay.innerText = '• Present Space Age (Polaris North Star)';
    else if (currentEpochYear <= 5000) epochContextDisplay.innerText = '• Early Transhuman Epoch (Errai North Star)';
    else if (currentEpochYear <= 9000) epochContextDisplay.innerText = '• Mid-Millennium (Alderamin North Star)';
    else epochContextDisplay.innerText = '• Cosmic Return Cycle (Vega North Star)';

    quickEpochPills.forEach(pill => {
      pill.classList.toggle('active', Math.abs(parseFloat(pill.dataset.year) - currentEpochYear) < 300);
    });

    if (triggerChange) {
      loadSkyData(currentEpochYear);
      loadSeasonData(currentEpochYear, currentDayOfYear);
    }
  }

  epochSlider.addEventListener('input', (e) => setEpoch(e.target.value, false));
  epochSlider.addEventListener('change', (e) => setEpoch(e.target.value, true));

  quickEpochPills.forEach(pill => {
    pill.addEventListener('click', () => setEpoch(pill.dataset.year, true));
  });

  playBtn.addEventListener('click', () => {
    isPlayingTimeline = !isPlayingTimeline;
    playBtn.innerText = isPlayingTimeline ? '⏸' : '▶';
  });

  // ============================================================================
  //  8. AGENTIC AI DIALOGUE & MEMORY INTERACTION
  // ============================================================================
  function executeUIAction(action) {
    if (!action) return;
    if (action.action === 'set_epoch') {
      setEpoch(action.value, true);
    } else if (action.action === 'switch_view') {
      switchViewMode(action.value);
    } else if (action.action === 'focus_orbital_body') {
      orbitalView.selectTarget(action.value);
      switchViewMode('orbital');
    } else if (action.action === 'suggest_tour') {
      launchTour(action.value);
    } else if (action.action === 'set_client_level') {
      clientProfile.experience_level = action.value;
      clientProfile.novice_mode_active = action.value === 'novice';
      updateClientUI();
    }
  }

  async function submitQuery(queryText) {
    if (!queryText || !queryText.trim()) return;

    appendMessage('user', queryText);
    chatInput.value = '';

    const thinkingId = appendMessage('assistant', `
      <div class="agent-thought-pill">⚡ Multi-Agent Sentinel: Consulting celestial database, memory cache & astrometry vectors...</div>
    `);

    try {
      const res = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: queryText,
          year: currentEpochYear,
          day_of_year: currentDayOfYear,
          client_id: clientId
        })
      });
      if (!res.ok) throw new Error(`Chat service returned ${res.status}`);
      const data = await res.json();

      const thinkingEl = document.getElementById(thinkingId);
      if (thinkingEl) thinkingEl.remove();

      let responseHtml = '';
      if (data.agentic_workflow && data.agentic_workflow.length) {
        const stages = data.agentic_workflow.map(stage =>
          `<span class="agent-stage"><b>${stage.stage}</b> ${escapeHtml(stage.name)}</span>`
        ).join('');
        const synthesis = data.llm_enriched ? 'Model synthesis' : 'Local specialist response';
        responseHtml += `<div class="agentic-stage-row" aria-label="Five-stage agent workflow">${stages}<span class="agent-stage agent-synthesis">${synthesis}</span></div>`;
      }
      if (data.agent_thoughts && data.agent_thoughts.length) {
        responseHtml += `<div style="margin-bottom: 8px;">`;
        data.agent_thoughts.forEach(t => {
          responseHtml += `<div class="agent-thought-pill">${escapeHtml(t.avatar)} <strong>${escapeHtml(t.agent)}</strong>: ${escapeHtml(t.thought)}</div>`;
        });
        responseHtml += `</div>`;
      }

      let formattedText = escapeHtml(data.response || '')
        .replace(/### (.*?)\n/g, '<h3>$1</h3>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/- (.*?)\n/g, '<li>$1</li>')
        .replace(/\n\n/g, '<br>');

      responseHtml += `<div>${formattedText}</div>`;
      appendMessage('assistant', responseHtml);

      // Execute UI actions returned by agents
      if (data.ui_actions) {
        data.ui_actions.forEach(executeUIAction);
      }

      // Update client level state if changed
      if (data.client_level) {
        clientProfile.experience_level = data.client_level;
        updateClientUI();
      }

      // Update prompt suggestion pills
      if (data.suggestions && suggestionContainer) {
        suggestionContainer.innerHTML = '';
        data.suggestions.slice(0, 3).forEach(s => {
          const pill = document.createElement('button');
          pill.className = 'suggestion-pill';
          pill.innerText = s;
          pill.onclick = () => submitQuery(s);
          suggestionContainer.appendChild(pill);
        });
      }
    } catch (err) {
      console.error('Chat error:', err);
      const thinkingEl = document.getElementById(thinkingId);
      if (thinkingEl) thinkingEl.innerHTML = `<span style="color: var(--accent-danger)">Error connecting to AstraTrack AI Brain.</span>`;
    }
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[ch]);
  }

  function appendMessage(role, content) {
    const id = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`;
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role}`;
    bubble.id = id;
    bubble.innerHTML = content;
    chatHistory.appendChild(bubble);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return id;
  }

  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    submitQuery(chatInput.value);
  });

  document.querySelectorAll('.suggestion-pill').forEach(btn => {
    btn.addEventListener('click', () => submitQuery(btn.innerText));
  });

  // ============================================================================
  //  9. MASTER RENDER LOOP (60 FPS)
  // ============================================================================
  function renderLoop() {
    if (isPlayingTimeline) {
      let nextYear = currentEpochYear + playSpeed;
      if (nextYear > 15000) nextYear = -15000;
      setEpoch(nextYear, true);
    }

    if (currentViewMode === 'planetarium' || currentViewMode === 'stellar3d') {
      planetarium.render();
    } else {
      orbitalView.render();
    }

    requestAnimationFrame(renderLoop);
  }

  // ============================================================================
  //  10. INITIAL BOOT
  // ============================================================================
  syncClientProfile();
  setEpoch(2026, true);
  loadTrajectoryData();
  renderLoop();
});
