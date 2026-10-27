// UK Business Directory - Main Application

class BusinessDirectory {
    constructor() {
        this.businesses = [];
        this.filteredBusinesses = [];
        this.selectedBusinesses = new Set();
        this.selectedCategories = new Set();
        this.currentView = 'grid';
        this.map = null;
        this.markers = [];
        this.customerMatches = null;
        this.customerEvidence = new Map();
        this.activeDataset = 'signs';
        this.datasetStates = new Map();
        this.datasetData = new Map();
        this.overlayAttempted = new Set();
        this.overlayGeneration = new Map();
        this.overlayInFlight = new Map();
        this.switchSequence = 0;
        this.pendingDataset = null;
        this.globalSupplement = null;
        this.globalSupplementPromise = null;
        this.datasetFiles = {signs: 'data/directory-data.json', wayfinding: 'data/wayfinding-directory-data.json', 'global-wayfinding': 'data/global-wayfinding-directory-data.json'};
        this.datasetLabels = {signs: 'UK signs', wayfinding: 'UK wayfinding', 'global-wayfinding': 'Global wayfinding'};
        
        // DOM Elements
        this.searchInput = document.getElementById('searchInput');
        this.clearSearchBtn = document.getElementById('clearSearch');
        this.categoryCheckboxes = document.getElementById('categoryCheckboxes');
        this.countyFilter = document.getElementById('countyFilter');
        this.sortBy = document.getElementById('sortBy');
        this.resetFiltersBtn = document.getElementById('resetFilters');
        this.resultsGrid = document.getElementById('resultsGrid');
        this.resultsList = document.getElementById('resultsList');
        this.mapContainer = document.getElementById('mapContainer');
        this.resultsCount = document.getElementById('resultsCount');
        this.loading = document.getElementById('loading');
        this.noResults = document.getElementById('noResults');
        this.gridViewBtn = document.getElementById('gridView');
        this.listViewBtn = document.getElementById('listView');
        this.mapViewBtn = document.getElementById('mapView');
        this.selectAllBtn = document.getElementById('selectAllBtn');
        this.deselectAllBtn = document.getElementById('deselectAllBtn');
        this.downloadCsvBtn = document.getElementById('downloadCsvBtn');
        this.selectedCountSpan = document.getElementById('selectedCount');
        this.selectAllCatsBtn = document.getElementById('selectAllCats');
        this.clearCatsBtn = document.getElementById('clearCats');
        this.customerOverlayFile = document.getElementById('customerOverlayFile');
        this.customerOverlaySummary = document.getElementById('customerOverlaySummary');
        this.customerStatusFilter = document.getElementById('customerStatusFilter');
        this.clearCustomerOverlayBtn = document.getElementById('clearCustomerOverlay');
        this.saveCustomerOverlayBtn = document.getElementById('saveCustomerOverlay');
        this.selectCustomersBtn = document.getElementById('selectCustomersBtn');
        this.deselectCustomersBtn = document.getElementById('deselectCustomersBtn');
        this.datasetButtons = {signs: document.getElementById('signsDataset'), wayfinding: document.getElementById('wayfindingDataset'), 'global-wayfinding': document.getElementById('globalWayfindingDataset')};
        this.datasetSwitchStatus = document.getElementById('datasetSwitchStatus');
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        if (!await this.loadData()) return;
        this.datasetData.set(this.activeDataset, this.businesses);
        this.populateCategoryCheckboxes();
        this.populateFilters();
        this.sort();
        this.render();
        await this.loadLocalCustomerOverlay();
    }
    
    setupEventListeners() {
        for (const [dataset, button] of Object.entries(this.datasetButtons)) {
            if (button) button.addEventListener('click', () => this.switchDataset(dataset));
        }
        // Search
        if (this.searchInput) {
            this.searchInput.addEventListener('input', () => {
                this.clearSearchBtn.style.display = this.searchInput.value ? 'flex' : 'none';
                this.filter();
            });
        }
        
        if (this.clearSearchBtn) {
            this.clearSearchBtn.addEventListener('click', () => {
                this.searchInput.value = '';
                this.clearSearchBtn.style.display = 'none';
                this.filter();
            });
        }
        
        // Filters
        if (this.countyFilter) {
            this.countyFilter.addEventListener('change', () => this.filter());
        }
        if (this.sortBy) {
            this.sortBy.addEventListener('change', () => {
                this.sort();
                this.render();
            });
        }
        
        // Plaque toggle
        const plaquesOnly = document.getElementById('plaquesOnly');
        if (plaquesOnly) {
            plaquesOnly.addEventListener('change', () => this.filter());
        }
        
        // Has email toggle
        const hasEmail = document.getElementById('hasEmail');
        if (hasEmail) {
            hasEmail.addEventListener('change', () => this.filter());
        }
        for (const id of ['hasLinkedIn', 'hasInstagram', 'recentlyAdded', 'latestResearch']) {
            document.getElementById(id)?.addEventListener('change', () => this.filter());
        }

        if (this.customerStatusFilter) this.customerStatusFilter.addEventListener('change', () => this.filter());
        if (this.customerOverlayFile) this.customerOverlayFile.addEventListener('change', () => this.loadCustomerOverlay());
        if (this.clearCustomerOverlayBtn) this.clearCustomerOverlayBtn.addEventListener('click', () => this.clearCustomerOverlay());
        if (this.saveCustomerOverlayBtn) this.saveCustomerOverlayBtn.addEventListener('click', () => this.saveCustomerOverlay());
        if (this.selectCustomersBtn) this.selectCustomersBtn.addEventListener('click', () => this.setCustomerSelection(true));
        if (this.deselectCustomersBtn) this.deselectCustomersBtn.addEventListener('click', () => this.setCustomerSelection(false));
        for (const container of [this.resultsGrid, this.resultsList]) {
            container.addEventListener('click', event => {
                const button = event.target.closest('[data-review-id]');
                if (!button) return;
                const id = Number(button.dataset.reviewId);
                if (!this.customerMatches || !this.customerMatches.has(id)) return;
                this.customerMatches.set(id, button.dataset.reviewStatus);
                this.updateCustomerSummary();
                this.filter();
            });
        }

        // Reset
        if (this.resetFiltersBtn) {
            this.resetFiltersBtn.addEventListener('click', () => this.resetFilters());
        }
        
        // View Toggle
        if (this.gridViewBtn) {
            this.gridViewBtn.addEventListener('click', () => this.setView('grid'));
        }
        if (this.listViewBtn) {
            this.listViewBtn.addEventListener('click', () => this.setView('list'));
        }
        if (this.mapViewBtn) {
            this.mapViewBtn.addEventListener('click', () => this.setView('map'));
        }
        
        // Selection Actions
        if (this.selectAllBtn) {
            this.selectAllBtn.addEventListener('click', () => this.selectAll());
        }
        if (this.deselectAllBtn) {
            this.deselectAllBtn.addEventListener('click', () => this.deselectAll());
        }
        if (this.downloadCsvBtn) {
            this.downloadCsvBtn.addEventListener('click', () => this.downloadCsv());
        }
        if (this.selectAllCatsBtn) {
            this.selectAllCatsBtn.addEventListener('click', () => this.selectAllCategories());
        }
        if (this.clearCatsBtn) {
            this.clearCatsBtn.addEventListener('click', () => this.clearCategories());
        }
    }
    
    saveDatasetState() {
        this.datasetStates.set(this.activeDataset, {
            selectedBusinesses: new Set(this.selectedBusinesses),
            selectedCategories: new Set(this.selectedCategories),
            customerMatches: this.customerMatches ? new Map(this.customerMatches) : null,
            customerEvidence: new Map(this.customerEvidence),
            search: this.searchInput.value,
            county: this.countyFilter.value,
            sort: this.sortBy.value,
            customerStatus: this.customerStatusFilter?.value || 'all',
            quickFilters: Object.fromEntries(['plaquesOnly', 'hasEmail', 'hasLinkedIn', 'hasInstagram', 'recentlyAdded', 'latestResearch'].map(id => [id, !!document.getElementById(id)?.checked]))
        });
    }

    async switchDataset(dataset) {
        if (!this.datasetButtons[dataset] || !this.datasetFiles[dataset]) return;
        this.datasetSwitchStatus.classList.remove('is-error');
        if (dataset === this.activeDataset) {
            if (this.pendingDataset) {
                ++this.switchSequence;
                this.pendingDataset = null;
                this.cancelPendingOverlay(dataset);
                this.loadLocalCustomerOverlay();
            }
            this.datasetSwitchStatus.textContent = '';
            return;
        }
        const sequence = ++this.switchSequence;
        this.pendingDataset = dataset;
        this.datasetSwitchStatus.textContent = `Loading ${this.datasetLabels[dataset]}…`;
        let businesses = this.datasetData.get(dataset);
        try {
            if (!businesses) {
                const response = await fetch(this.datasetFiles[dataset]);
                if (!response.ok) throw new Error(`Directory request returned ${response.status}`);
                businesses = await response.json();
                if (!Array.isArray(businesses)) throw new Error('Invalid directory data');
                this.datasetData.set(dataset, businesses);
            }
            if (sequence !== this.switchSequence) return;
            if (dataset === 'global-wayfinding') {
                await this.loadGlobalSupplement(businesses);
                if (sequence !== this.switchSequence) return;
            }
            this.pendingDataset = null;
            this.cancelPendingOverlay(this.activeDataset);
            this.saveDatasetState();
            this.activeDataset = dataset;
            this.businesses = businesses;
            const state = this.datasetStates.get(dataset);
            this.selectedBusinesses = state?.selectedBusinesses || new Set();
            this.selectedCategories = state?.selectedCategories || new Set();
            this.customerMatches = state?.customerMatches || null;
            this.customerEvidence = state?.customerEvidence || new Map();
            this.searchInput.value = state?.search || '';
            this.clearSearchBtn.style.display = this.searchInput.value ? 'flex' : 'none';
            this.sortBy.value = state?.sort || 'name-asc';
            for (const id of ['plaquesOnly', 'hasEmail', 'hasLinkedIn', 'hasInstagram', 'recentlyAdded', 'latestResearch']) {
                const checkbox = document.getElementById(id);
                if (checkbox) checkbox.checked = !!state?.quickFilters[id];
            }
            this.populateCategoryCheckboxes();
            this.populateFilters();
            this.countyFilter.value = state?.county || '';
            if (this.customerStatusFilter) this.customerStatusFilter.value = state?.customerStatus || 'all';
            for (const [name, button] of Object.entries(this.datasetButtons)) {
                button.classList.toggle('active', name === dataset);
                button.setAttribute('aria-pressed', String(name === dataset));
            }
            document.getElementById('directoryKicker').textContent = dataset === 'signs' ? 'UK SIGNS DIRECTORY' : dataset === 'wayfinding' ? 'UK WAYFINDING DIRECTORY' : 'GLOBAL WAYFINDING DIRECTORY';
            document.getElementById('directoryHeading').innerHTML = dataset === 'signs' ? 'Businesses <span class="results-heading-dot">.</span>' : 'Wayfinding studios <span class="results-heading-dot">.</span>';
            document.getElementById('heroEyebrow').textContent = dataset === 'global-wayfinding' ? 'WAYFINDING STUDIOS AROUND THE WORLD' : 'THE UK SIGN INDUSTRY, ALL IN ONE PLACE';
            document.getElementById('heroDescription').textContent = dataset === 'signs'
                ? 'Discover sign makers, engravers and creative businesses across the UK.'
                : dataset === 'wayfinding' ? 'Discover UK wayfinding consultancies, signage strategists and design studios.'
                : 'Discover wayfinding consultancies and environmental design studios around the world.';
            document.title = `${this.datasetLabels[dataset]} Directory | Find your next connection`;
            const isGlobal = dataset === 'global-wayfinding';
            this.countyFilter.options[0].textContent = isGlobal ? 'All countries' : 'All counties';
            this.sortBy.querySelector('option[value="county-asc"]').textContent = isGlobal ? 'Country A–Z' : 'County A–Z';
            this.sortBy.querySelector('option[value="county-desc"]').textContent = isGlobal ? 'Country Z–A' : 'County Z–A';
            document.getElementById('locationSourceNote').hidden = !isGlobal;
            document.getElementById('mapUnavailableNotice').hidden = !isGlobal;
            const contactNotice = document.getElementById('globalContactNotice');
            contactNotice.hidden = !isGlobal;
            if (isGlobal) {
                const unavailable = this.globalSupplement?.unavailable;
                const withheld = this.globalSupplement?.withheld;
                contactNotice.textContent = unavailable
                    ? 'Some imported contacts or outreach details could not be loaded. The directory remains available.'
                    : `Contact and outreach details are imported research and may be out of date; check them before use.${withheld ? ' Some records are hidden because their company names do not match.' : ''}`;
            }
            this.mapViewBtn.disabled = isGlobal;
            this.mapViewBtn.title = isGlobal ? 'Map unavailable: global locations are incomplete or inconsistent' : 'Map view';
            if (isGlobal && this.currentView === 'map') this.setView('grid');
            this.refreshOverlayControls();
            this.filter();
            this.datasetSwitchStatus.textContent = `${this.datasetLabels[dataset]} directory selected.`;
            await this.loadLocalCustomerOverlay();
        } catch (error) {
            if (sequence !== this.switchSequence) return;
            this.pendingDataset = null;
            console.error('Error switching directory:', error);
            this.datasetSwitchStatus.classList.add('is-error');
            this.datasetSwitchStatus.textContent = `Could not load ${this.datasetLabels[dataset]}. Your current list is unchanged.`;
        }
    }

    refreshOverlayControls() {
        if (!this.customerOverlaySummary) return;
        const hasOverlay = this.customerMatches !== null;
        this.clearCustomerOverlayBtn.disabled = !hasOverlay;
        this.saveCustomerOverlayBtn.disabled = !hasOverlay;
        this.selectCustomersBtn.disabled = !hasOverlay;
        this.deselectCustomersBtn.disabled = !hasOverlay;
        if (hasOverlay) this.updateCustomerSummary();
        else this.customerOverlaySummary.textContent = `No ${this.datasetLabels[this.activeDataset]} comparison loaded — all businesses are unchecked.`;
    }

    // Contact and outreach material is historical source data. Its IDs are
    // scoped to the global list and are accepted only when the company names
    // also agree; some older source IDs no longer identify the same company.
    globalCompanyKey(value) {
        return String(value || '').normalize('NFKD').toLowerCase()
            .replace(/&/g, ' and ').replace(/[^a-z0-9]+/g, ' ').trim()
            .replace(/\b(?:limited|ltd|llp|plc)\s*$/i, '').trim();
    }

    async loadGlobalSupplement(businesses) {
        if (this.globalSupplement && !this.globalSupplement.unavailable) return;
        if (!this.globalSupplementPromise) {
            this.globalSupplementPromise = (async () => {
                const files = ['data/global-wayfinding-contacts.json', 'data/global-wayfinding-outreach.json'];
                const loaded = await Promise.allSettled(files.map(async path => {
                    const response = await fetch(path);
                    if (!response.ok) throw new Error(`Supplement returned ${response.status}`);
                    const rows = await response.json();
                    if (!Array.isArray(rows)) throw new Error('Invalid supplement');
                    return rows;
                }));
                const companies = new Map(businesses.map(b => [b.id, b]));
                const contacts = new Map();
                const outreach = new Map();
                // These four source IDs were audited against company names and
                // public sources. The source file's original IDs point at a
                // different company, so never attach them at those IDs.
                const contactRemaps = new Map([[46, 47], [47, 48], [49, 50], [52, 53]]);
                let withheld = 0;
                loaded.forEach((result, index) => {
                    if (result.status !== 'fulfilled') return;
                    for (const row of result.value) {
                        const companyId = index === 0 && contactRemaps.has(row.companyId) ? contactRemaps.get(row.companyId) : row.companyId;
                        const company = companies.get(companyId);
                        if (!company || !this.globalCompanyKey(company.company) || this.globalCompanyKey(company.company) !== this.globalCompanyKey(row.company)) {
                            withheld++;
                            continue;
                        }
                        if (index === 0 && Array.isArray(row.contacts)) {
                            const prior = contacts.get(companyId) || [];
                            const signature = contact => [contact?.name, contact?.email, contact?.linkedin].map(v => String(v || '').trim().toLowerCase()).join('|');
                            const seen = new Set(prior.map(signature));
                            for (const contact of row.contacts) {
                                if (!contact || typeof contact !== 'object') continue;
                                const key = signature(contact);
                                if (!seen.has(key)) { prior.push(contact); seen.add(key); }
                            }
                            contacts.set(companyId, prior);
                        }
                        if (index === 1) outreach.set(companyId, row);
                    }
                });
                this.globalSupplement = {contacts, outreach, withheld, unavailable: loaded.some(r => r.status !== 'fulfilled')};
            })().finally(() => { this.globalSupplementPromise = null; });
        }
        await this.globalSupplementPromise;
    }

    cancelPendingOverlay(dataset) {
        if (!this.overlayInFlight.has(dataset)) return;
        this.overlayGeneration.set(dataset, (this.overlayGeneration.get(dataset) || 0) + 1);
        this.overlayInFlight.delete(dataset);
        this.overlayAttempted.delete(dataset);
    }

    async loadData() {
        try {
            const dataFile = document.body?.dataset?.dataFile || 'data/directory-data.json';
            const response = await fetch(dataFile);
            if (!response.ok) throw new Error(`Directory request returned ${response.status}`);
            this.businesses = await response.json();
            if (!Array.isArray(this.businesses)) throw new Error('Invalid directory data');
            this.filteredBusinesses = [...this.businesses];
            return true;
        } catch (error) {
            console.error('Error loading data:', error);
            this.loading.innerHTML = '<p>Error loading directory data. Please refresh.</p>';
            return false;
        }
    }
    
    async loadCustomerOverlay() {
        const file = this.customerOverlayFile.files[0];
        if (!file) return;
        const dataset = this.activeDataset;
        const sequence = this.switchSequence;
        const generation = (this.overlayGeneration.get(dataset) || 0) + 1;
        this.overlayGeneration.set(dataset, generation);
        if (this.overlayInFlight.has(dataset)) {
            this.overlayInFlight.delete(dataset);
            this.overlayAttempted.delete(dataset);
        }
        try {
            const overlay = JSON.parse(await file.text());
            if (dataset !== this.activeDataset || sequence !== this.switchSequence || this.overlayGeneration.get(dataset) !== generation) return;
            this.applyCustomerOverlay(overlay);
        } catch (error) {
            if (dataset !== this.activeDataset || sequence !== this.switchSequence || this.overlayGeneration.get(dataset) !== generation) return;
            this.customerOverlaySummary.textContent = `Could not load comparison: ${error.message} ${this.customerMatches ? 'The previous comparison is still active.' : 'All businesses remain unchecked.'}`;
        } finally {
            this.customerOverlayFile.value = '';
        }
    }

    async loadLocalCustomerOverlay() {
        // Only the explicitly local directory is allowed to ask the loopback
        // helper for the user's private comparison. Published pages never do.
        if (!this.customerOverlayFile || window.location.origin !== 'http://127.0.0.1:8767') return;
        const dataset = this.activeDataset;
        const sequence = this.switchSequence;
        if (this.overlayAttempted.has(dataset) || this.customerMatches) return;
        const generation = (this.overlayGeneration.get(dataset) || 0) + 1;
        this.overlayGeneration.set(dataset, generation);
        this.overlayAttempted.add(dataset);
        this.overlayInFlight.set(dataset, generation);
        try {
            const endpoint = dataset === 'signs' ? '/comparison' : `/comparison?dataset=${encodeURIComponent(dataset)}`;
            const response = await fetch(`http://127.0.0.1:8766${endpoint}`, {cache: 'no-store'});
            if (dataset !== this.activeDataset || sequence !== this.switchSequence || this.overlayGeneration.get(dataset) !== generation) {
                if (this.overlayGeneration.get(dataset) === generation) this.overlayAttempted.delete(dataset);
                return;
            }
            if (!response.ok) { this.overlayAttempted.delete(dataset); return; }
            if (this.customerMatches) return;
            const overlay = await response.json();
            if (dataset !== this.activeDataset || sequence !== this.switchSequence || this.overlayGeneration.get(dataset) !== generation) {
                if (this.overlayGeneration.get(dataset) === generation) this.overlayAttempted.delete(dataset);
                return;
            }
            if (!this.customerMatches) this.applyCustomerOverlay(overlay);
        } catch (error) {
            // The helper is optional; manual file loading still works.
            if (this.overlayGeneration.get(dataset) === generation) this.overlayAttempted.delete(dataset);
            console.warn('Local comparison unavailable:', error.message);
        } finally {
            if (this.overlayInFlight.get(dataset) === generation) this.overlayInFlight.delete(dataset);
        }
    }

    applyCustomerOverlay(overlay) {
        if (!overlay || !Array.isArray(overlay.matches)) throw new Error('Expected a matches array.');
        const overlayDataset = overlay.dataset || 'signs';
        if (overlayDataset !== this.activeDataset) throw new Error(`This comparison is for ${overlayDataset}, not the selected directory.`);
        const knownIds = new Set(this.businesses.map(b => b.id));
        const matches = new Map();
        const evidence = new Map();
        for (const entry of overlay.matches) {
            if (!entry || !Number.isInteger(entry.id) || !knownIds.has(entry.id) ||
                !['confirmed', 'possible', 'rejected'].includes(entry.status) || matches.has(entry.id)) {
                throw new Error('Each match must have a unique directory ID and a confirmed, possible or rejected status.');
            }
            matches.set(entry.id, entry.status);
            evidence.set(entry.id, {customer: typeof entry.customer === 'string' ? entry.customer : '', reason: typeof entry.reason === 'string' ? entry.reason : ''});
        }
        this.customerMatches = matches;
        this.customerEvidence = evidence;
        this.overlayAttempted.add(this.activeDataset);
        this.updateCustomerSummary();
        this.refreshOverlayControls();
        this.filter();
    }

    clearCustomerOverlay() {
        this.overlayGeneration.set(this.activeDataset, (this.overlayGeneration.get(this.activeDataset) || 0) + 1);
        this.overlayInFlight.delete(this.activeDataset);
        this.overlayAttempted.add(this.activeDataset);
        this.customerMatches = null;
        this.customerEvidence.clear();
        this.refreshOverlayControls();
        this.customerStatusFilter.value = 'all';
        this.filter();
    }

    customerStatus(business) {
        if (!this.customerMatches) return 'unchecked';
        return this.customerMatches.get(business.id) || 'unmatched';
    }

    saveCustomerOverlay() {
        if (!this.customerMatches) return;
        const matches = [...this.customerMatches].map(([id, status]) => ({id, status, ...this.customerEvidence.get(id)}));
        const blob = new Blob([JSON.stringify({dataset: this.activeDataset, matches}, null, 2)], {type: 'application/json'});
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `reviewed-${this.activeDataset}-customer-comparison.json`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(link.href);
    }

    customerStatusBadge(business) {
        if (!this.customerStatusFilter) return '';
        const status = this.customerStatus(business);
        const labels = {confirmed: 'Strong customer match', possible: 'Possible customer — review', rejected: 'Rejected match', unmatched: 'No match found', unchecked: 'Unchecked'};
        const evidence = this.customerEvidence.get(business.id);
        const detail = evidence ? [evidence.customer && `SUPATED: ${evidence.customer}`, evidence.reason].filter(Boolean).map(value => `<p>${this.escapeHtml(value)}</p>`).join('') : '';
        const actions = evidence ? `<details class="customer-review">
            <summary class="customer-review-summary" aria-label="Review customer match for ${this.escapeHtml(business.company || 'business')}">Review match</summary>
            ${detail ? `<div class="customer-evidence">${detail}</div>` : ''}
            <div class="customer-review-actions">
            ${status !== 'confirmed' ? `<button type="button" data-review-id="${business.id}" data-review-status="confirmed">Confirm customer</button>` : ''}
            ${status !== 'rejected' ? `<button type="button" data-review-id="${business.id}" data-review-status="rejected">Reject match</button>` : ''}
            ${status !== 'possible' ? `<button type="button" data-review-id="${business.id}" data-review-status="possible">Mark for review</button>` : ''}
            </div>
        </details>` : '';
        return `<span class="customer-badge customer-${status}">${labels[status]}</span>${actions}`;
    }

    updateCustomerSummary() {
        const values = [...this.customerMatches.values()];
        const count = status => values.filter(value => value === status).length;
        this.customerOverlaySummary.textContent = `Comparison loaded: ${count('confirmed')} strong matches, ${count('possible')} possible, ${count('rejected')} rejected. Reviews last only until this tab reloads. No match found does not guarantee a new customer.`;
    }

    setCustomerSelection(selected) {
        if (!this.customerMatches) return;
        this.customerMatches.forEach((status, id) => {
            if (status === 'rejected') return;
            if (selected) this.selectedBusinesses.add(id);
            else this.selectedBusinesses.delete(id);
        });
        this.updateSelectionUI();
    }

    populateCategoryCheckboxes() {
        const categories = [...new Set(this.businesses.map(b => b.category))].sort();
        
        this.categoryCheckboxes.innerHTML = categories.map(cat => `
            <label class="category-checkbox">
                <input type="checkbox" value="${this.escapeHtml(cat)}" ${this.selectedCategories.has(cat) ? 'checked' : ''}>
                <span>${this.escapeHtml(cat)}</span>
            </label>
        `).join('');
        
        // Add event listeners to new checkboxes
        this.categoryCheckboxes.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.addEventListener('change', () => {
                if (cb.checked) {
                    this.selectedCategories.add(cb.value);
                } else {
                    this.selectedCategories.delete(cb.value);
                }
                this.filter();
            });
        });
    }
    
    populateFilters() {
        // Get unique counties
        const counties = [...new Set(this.businesses.map(b => b.county).filter(Boolean))].sort();
        // Keep the page's first option ("All counties" or "All countries")
        // but remove options from the previously selected directory.
        while (this.countyFilter.options.length > 1) this.countyFilter.remove(1);
        
        // Populate county filter
        counties.forEach(county => {
            const option = document.createElement('option');
            option.value = county;
            option.textContent = county;
            this.countyFilter.appendChild(option);
        });
    }
    
    filter() {
        const searchTerm = this.searchInput.value.toLowerCase().trim();
        const county = this.countyFilter.value;
        const customerStatus = this.customerStatusFilter?.value || 'all';
        const showPlaquesOnly = document.getElementById('plaquesOnly')?.checked || false;
        const hasEmailOnly = document.getElementById('hasEmail')?.checked || false;
        const hasLinkedInOnly = document.getElementById('hasLinkedIn')?.checked || false;
        const hasInstagramOnly = document.getElementById('hasInstagram')?.checked || false;
        const recentlyAddedOnly = document.getElementById('recentlyAdded')?.checked || false;
        const latestResearchOnly = document.getElementById('latestResearch')?.checked || false;
        const latestBatch = latestResearchOnly ? this.businesses.reduce((latest, business) => typeof business.researchBatch === 'string' && business.researchBatch > latest ? business.researchBatch : latest, '') : '';
        
        this.filteredBusinesses = this.businesses.filter(business => {
            // Search filter
            const matchesSearch = !searchTerm || 
                (business.company && business.company.toLowerCase().includes(searchTerm)) ||
                (business.address && business.address.toLowerCase().includes(searchTerm)) ||
                (business.county && business.county.toLowerCase().includes(searchTerm)) ||
                (business.category && business.category.toLowerCase().includes(searchTerm)) ||
                (this.activeDataset !== 'global-wayfinding' && business.notes && business.notes.toLowerCase().includes(searchTerm)) ||
                (business.email && business.email.toLowerCase().includes(searchTerm)) ||
                (business.phone && business.phone.toLowerCase().includes(searchTerm));
            
            // Category filter (multi-select)
            const matchesCategory = this.selectedCategories.size === 0 || 
                this.selectedCategories.has(business.category);
            
            // County filter
            const matchesCounty = !county || business.county === county;
            
            // Plaque filter
            const matchesPlaque = !showPlaquesOnly || business.sellsPlaques === true;
            
            // Has email filter
            const matchesEmail = !hasEmailOnly || (business.email && business.email.trim() !== '');
            const matchesLinkedIn = !hasLinkedInOnly || !!this.socialUrl(business.linkedin, 'linkedin');
            const matchesInstagram = !hasInstagramOnly || !!this.socialUrl(business.instagram, 'instagram');
            const matchesRecentlyAdded = !recentlyAddedOnly || this.isRecentlyAdded(business);
            const matchesLatestResearch = !latestResearchOnly || (!!latestBatch && business.researchBatch === latestBatch);

            const matchesCustomerStatus = customerStatus === 'all' || this.customerStatus(business) === customerStatus;
            return matchesSearch && matchesCategory && matchesCounty && matchesPlaque && matchesEmail && matchesLinkedIn && matchesInstagram && matchesRecentlyAdded && matchesLatestResearch && matchesCustomerStatus;
        });
        
        this.sort();
        this.render();
    }
    
    selectAllCategories() {
        this.categoryCheckboxes.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = true;
            this.selectedCategories.add(cb.value);
        });
        this.filter();
    }
    
    clearCategories() {
        this.categoryCheckboxes.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = false;
        });
        this.selectedCategories.clear();
        this.filter();
    }
    
    sort() {
        const sortValue = this.sortBy.value;
        
        this.filteredBusinesses.sort((a, b) => {
            switch (sortValue) {
                case 'name-asc':
                    return (a.company || '').localeCompare(b.company || '');
                case 'name-desc':
                    return (b.company || '').localeCompare(a.company || '');
                case 'county-asc':
                    return (a.county || '').localeCompare(b.county || '');
                case 'county-desc':
                    return (b.county || '').localeCompare(a.county || '');
                case 'category-asc':
                    return (a.category || '').localeCompare(b.category || '');
                default:
                    return 0;
            }
        });
    }
    
    resetFilters() {
        this.searchInput.value = '';
        this.clearSearchBtn.style.display = 'none';
        this.countyFilter.value = '';
        this.sortBy.value = 'name-asc';
        if (this.customerStatusFilter) this.customerStatusFilter.value = 'all';
        const plaquesOnly = document.getElementById('plaquesOnly');
        if (plaquesOnly) plaquesOnly.checked = false;
        const hasEmail = document.getElementById('hasEmail');
        if (hasEmail) hasEmail.checked = false;
        for (const id of ['hasLinkedIn', 'hasInstagram', 'recentlyAdded', 'latestResearch']) {
            const checkbox = document.getElementById(id);
            if (checkbox) checkbox.checked = false;
        }
        // Filtering and selection are independent: clearing filters must not
        // discard a prospect list the user has already built.
        this.clearCategories();
    }
    
    setView(view) {
        this.currentView = view;
        this.gridViewBtn.classList.toggle('active', view === 'grid');
        this.listViewBtn.classList.toggle('active', view === 'list');
        this.mapViewBtn.classList.toggle('active', view === 'map');
        this.gridViewBtn.setAttribute('aria-pressed', String(view === 'grid'));
        this.listViewBtn.setAttribute('aria-pressed', String(view === 'list'));
        this.mapViewBtn.setAttribute('aria-pressed', String(view === 'map'));
        this.resultsGrid.style.display = view === 'grid' ? 'grid' : 'none';
        this.resultsList.style.display = view === 'list' ? 'flex' : 'none';
        this.mapContainer.style.display = view === 'map' ? 'block' : 'none';
        
        if (view === 'map') {
            this.renderMap();
        }
    }
    
    render() {
        this.loading.style.display = 'none';
        
        const count = this.filteredBusinesses.length;
        this.resultsCount.textContent = count.toLocaleString();
        
        if (count === 0) {
            this.noResults.style.display = 'block';
            this.resultsGrid.innerHTML = '';
            this.resultsList.innerHTML = '';
            if (this.currentView === 'map' && this.map) this.renderMap();
            this.updateSelectionUI();
            return;
        }
        
        this.noResults.style.display = 'none';
        this.renderGrid();
        this.renderList();
        
        if (this.currentView === 'map') {
            this.renderMap();
        }
        
        // Update selection UI after rendering
        this.updateSelectionUI();
    }
    
    renderGrid() {
        this.resultsGrid.innerHTML = this.filteredBusinesses.map(business => this.createCardHTML(business)).join('');
        
        // Add event listeners to checkboxes
        this.resultsGrid.querySelectorAll('.business-checkbox').forEach(cb => {
            cb.addEventListener('change', (e) => {
                const id = parseInt(e.target.dataset.id);
                if (e.target.checked) {
                    this.selectedBusinesses.add(id);
                } else {
                    this.selectedBusinesses.delete(id);
                }
                this.updateSelectionUI();
            });
        });
    }
    
    renderList() {
        this.resultsList.innerHTML = this.filteredBusinesses.map(business => this.createListItemHTML(business)).join('');
        
        // Add event listeners to checkboxes
        this.resultsList.querySelectorAll('.business-checkbox').forEach(cb => {
            cb.addEventListener('change', (e) => {
                const id = parseInt(e.target.dataset.id);
                if (e.target.checked) {
                    this.selectedBusinesses.add(id);
                } else {
                    this.selectedBusinesses.delete(id);
                }
                this.updateSelectionUI();
            });
        });
    }
    
    updateSelectionUI() {
        const count = this.selectedBusinesses.size;
        this.selectedCountSpan.textContent = count;
        this.downloadCsvBtn.disabled = count === 0;
        
        // Update all checkbox states
        document.querySelectorAll('.business-checkbox').forEach(cb => {
            const id = parseInt(cb.dataset.id);
            cb.checked = this.selectedBusinesses.has(id);
            cb.closest('.business-card, .business-list-item')?.classList.toggle('selected', cb.checked);
        });
    }
    
    selectAll() {
        this.filteredBusinesses.forEach(b => this.selectedBusinesses.add(b.id));
        this.updateSelectionUI();
    }
    
    deselectAll() {
        this.selectedBusinesses.clear();
        this.updateSelectionUI();
    }
    
    downloadCsv() {
        const selected = this.businesses.filter(b => this.selectedBusinesses.has(b.id));
        
        if (selected.length === 0) return;
        
        const isGlobal = this.activeDataset === 'global-wayfinding';
        const headers = ['Company', 'Website', 'Email', 'Phone', 'Address', isGlobal ? 'Country (source data)' : 'County', 'Category', 'LinkedIn', 'Instagram', 'Sells Plaques', 'Quality', 'Customer status', isGlobal ? 'Source notes (unverified)' : 'Notes', 'Source'];
        if (this.datasetButtons.signs) headers.push('Added on');
        if (isGlobal) headers.push('Suggested contact name (unverified)', 'Suggested contact role (unverified)', 'Suggested primary email (unverified)', 'Suggested backup email (unverified)', 'Suggested contact LinkedIn (unverified)', 'Source confidence (unverified)', 'Imported contacts (unverified)');
        const rows = selected.map(b => {
            const row = [
            String(b.company || ''),
            String(b.website || ''),
            String(b.email || ''),
            String(b.phone || ''),
            String(b.address || ''),
            String(b.county || ''),
            String(b.category || ''),
            this.socialUrl(b.linkedin, 'linkedin'),
            this.socialUrl(b.instagram, 'instagram'),
            b.sellsPlaques === true ? 'Yes' : b.sellsPlaques === false ? 'No' : 'Unknown',
            String(b.quality || 0),
            ({confirmed: 'Strong customer match', possible: 'Possible customer - review', rejected: 'Rejected match', unmatched: 'No match found', unchecked: 'Unchecked'})[this.customerStatus(b)],
            String(b.notes || ''),
                String(b.source || '')
            ];
            if (this.datasetButtons.signs) row.push(this.isRecentlyAdded(b) ? b.addedOn : '');
            if (isGlobal) {
                const route = this.globalSupplement?.outreach.get(b.id) || {};
                const contacts = this.globalSupplement?.contacts.get(b.id) || [];
                row.push(...['primaryContactName', 'primaryContactRole', 'primaryEmail', 'backupEmail', 'contactLinkedIn', 'confidence'].map(key => String(route[key] || '')));
                row.push(contacts.map(contact => [contact.name, contact.title, contact.email, contact.linkedin, contact.source].filter(value => typeof value === 'string' && value.trim()).join(' | ')).filter(Boolean).join('; '));
            }
            return row;
        });
        
        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(','))
        ].join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        const label = this.datasetButtons.signs ? ({signs: 'uk-business-directory', wayfinding: 'uk-wayfinding-directory', 'global-wayfinding': 'global-wayfinding-directory'})[this.activeDataset] : 'nordic-business-directory';
        link.download = `${label}-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    }
    
    renderMap() {
        // The global source has inconsistent country/location entries and no
        // coordinates. Do not place companies at misleading guessed locations.
        if (this.activeDataset === 'global-wayfinding') return;
        // County coordinates (approximate centers)
        const countyCoords = {
            'Greater London': [51.5074, -0.1278],
            'Greater Manchester': [53.4808, -2.2426],
            'West Midlands': [52.4862, -1.8904],
            'West Yorkshire': [53.8008, -1.5491],
            'Merseyside': [53.4084, -2.9916],
            'South Yorkshire': [53.3811, -1.4701],
            'Tyne and Wear': [54.9783, -1.6178],
            'Hampshire': [51.0577, -1.3081],
            'Kent': [51.2787, 0.5217],
            'Essex': [51.7343, 0.4691],
            'Lancashire': [53.8175, -2.5556],
            'Surrey': [51.2538, -0.4473],
            'Hertfordshire': [51.8098, -0.2377],
            'Norfolk': [52.6140, 0.8864],
            'Devon': [50.7156, -3.5309],
            'Nottinghamshire': [53.1000, -1.0000],
            'Staffordshire': [52.8793, -2.0572],
            'Suffolk': [52.1872, 0.9708],
            'Oxfordshire': [51.7520, -1.2577],
            'Cambridgeshire': [52.2053, 0.1218],
            'Derbyshire': [53.1000, -1.5000],
            'Leicestershire': [52.6369, -1.1398],
            'Northamptonshire': [52.2405, -0.9027],
            'Warwickshire': [52.2819, -1.5849],
            'Somerset': [51.1051, -2.9262],
            'Dorset': [50.7488, -2.3445],
            'Gloucestershire': [51.8642, -2.2382],
            'Wiltshire': [51.3492, -1.9927],
            'Cheshire': [53.2000, -2.5000],
            'Cornwall': [50.2660, -5.0527],
            'Cumbria': [54.5772, -2.7975],
            'Bristol': [51.4545, -2.5879],
            'East Sussex': [50.9097, 0.2494],
            'West Sussex': [50.9364, -0.4614],
            'Berkshire': [51.4540, -0.9781],
            'Buckinghamshire': [51.8137, -0.8095],
            'Bedfordshire': [52.1356, -0.4667],
            'North Yorkshire': [54.1551, -1.3832],
            'East Riding of Yorkshire': [53.8439, -0.4275],
            'Lincolnshire': [53.2344, -0.5382],
            'Durham': [54.7761, -1.5733],
            'Northumberland': [55.2083, -2.0784],
            'Shropshire': [52.7080, -2.7540],
            'Herefordshire': [52.0765, -2.6544],
            'Worcestershire': [52.1920, -2.2216],
            'Rutland': [52.6583, -0.6396],
            'Isle of Wight': [50.6938, -1.3047],
            'Northern Ireland': [54.6079, -5.9264],
            'Wales': [52.1307, -3.7837],
            'Scotland': [56.4907, -4.2026],
            'Denmark': [56.2639, 9.5018],
            'Sweden': [60.1282, 18.6435],
            'Norway': [60.4720, 8.4689],
            'Finland': [61.9241, 25.7482],
            'Unidentified': [54.0, -2.0],
        };
        
        if (!this.map) {
            this.map = L.map('map').setView([53.5, -2.0], 6);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(this.map);
        }
        
        // Clear existing markers
        this.markers.forEach(m => this.map.removeLayer(m));
        this.markers = [];
        
        // Count businesses per county
        const countyCounts = {};
        this.filteredBusinesses.forEach(b => {
            countyCounts[b.county] = (countyCounts[b.county] || 0) + 1;
        });
        
        // Add markers for each county
        Object.entries(countyCounts).forEach(([county, count]) => {
            const coords = countyCoords[county];
            if (coords) {
                const marker = L.circleMarker(coords, {
                    radius: Math.min(8 + count * 0.5, 25),
                    fillColor: '#3b82f6',
                    color: '#1e40af',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.7
                }).addTo(this.map);
                
                marker.bindPopup(`<h4>${this.escapeHtml(county)}</h4><p><strong>${count}</strong> businesses</p>`);
                this.markers.push(marker);
            }
        });
        
        // Invalidate size in case container was hidden
        setTimeout(() => this.map.invalidateSize(), 100);
    }
    
    createCardHTML(business) {
        const categoryClass = this.getCategoryClass(business.category);
        const isSelected = this.selectedBusinesses.has(business.id) ? 'checked' : '';
        const name = this.escapeHtml(business.company || 'Unnamed business');
        const links = this.businessLinks(business);
        const location = this.escapeHtml(business.county || 'Location not listed');
        
        return `
            <article class="business-card ${isSelected ? 'selected' : ''}">
                <div class="card-header">
                    <label class="select-checkbox">
                        <input type="checkbox" class="business-checkbox" data-id="${business.id}" aria-label="Select ${name}" ${isSelected}>
                        <span class="checkmark" aria-hidden="true"></span>
                    </label>
                    <div class="card-title-area">
                        <h3 class="card-title">${name}</h3>
                        <div class="card-meta">
                            <span class="card-category ${categoryClass}">${this.escapeHtml(business.category || 'Other')}</span>
                            ${this.recentlyAddedBadge(business)}
                            ${business.sellsPlaques ? '<span class="card-feature">Plaques</span>' : ''}
                        </div>
                    </div>
                </div>
                <div class="card-status">${this.customerStatusBadge(business)}</div>
                <p class="card-county card-location">${this.icon('pin')}<span>${location}</span></p>
                ${this.wayfindingNote(business)}
                ${this.globalContactHTML(business)}
                <div class="card-contact">
                    ${business.phone ? `<p class="card-contact-row">${this.icon('phone')}<span>${this.escapeHtml(business.phone)}</span></p>` : ''}
                    ${business.address ? `<p class="card-contact-row">${this.icon('address')}<span>${this.escapeHtml(business.address)}</span></p>` : ''}
                </div>
                <div class="card-links card-actions">${links.join('')}</div>
            </article>
        `;
    }
    
    createListItemHTML(business) {
        const categoryClass = this.getCategoryClass(business.category);
        const isSelected = this.selectedBusinesses.has(business.id) ? 'checked' : '';
        const name = this.escapeHtml(business.company || 'Unnamed business');
        const links = this.businessLinks(business);
        const phone = typeof business.phone === 'string' ? business.phone.trim() : '';
        const phoneTarget = phone.replace(/[^\d+]/g, '');
        
        return `
            <article class="business-list-item ${isSelected ? 'selected' : ''}">
                <label class="select-checkbox">
                    <input type="checkbox" class="business-checkbox" data-id="${business.id}" aria-label="Select ${name}" ${isSelected}>
                    <span class="checkmark" aria-hidden="true"></span>
                </label>
                <div class="list-item-main">
                    <div class="list-item-header">
                        <h3 class="card-title">${name}</h3>
                        <span class="card-category ${categoryClass}">${this.escapeHtml(business.category || 'Other')}</span>
                        ${this.recentlyAddedBadge(business)}
                        ${business.sellsPlaques ? '<span class="card-feature">Plaques</span>' : ''}
                        <span class="card-county card-location">${this.icon('pin')}<span>${this.escapeHtml(business.county || 'Location not listed')}</span></span>
                    </div>
                    <div class="card-status">${this.customerStatusBadge(business)}</div>
                    ${this.wayfindingNote(business)}
                    ${this.globalContactHTML(business)}
                    <div class="card-links card-actions">${links.join('')}</div>
                </div>
                <div class="list-item-actions">
                    ${phone && /^\+?\d{7,15}$/.test(phoneTarget) ? `<a href="tel:${phoneTarget}" class="card-link card-contact-row">${this.icon('phone')}<span>${this.escapeHtml(phone)}</span></a>` : phone ? `<span class="card-contact-row">${this.icon('phone')}<span>${this.escapeHtml(phone)}</span></span>` : ''}
                </div>
            </article>
        `;
    }

    isRecentlyAdded(business) {
        if (typeof business.addedOn !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(business.addedOn)) return false;
        const date = new Date(`${business.addedOn}T00:00:00Z`);
        return !Number.isNaN(date.getTime()) && date.toISOString().slice(0, 10) === business.addedOn;
    }

    recentlyAddedBadge(business) {
        if (!this.isRecentlyAdded(business)) return '';
        const date = new Date(`${business.addedOn}T00:00:00Z`).toLocaleDateString('en-GB', {day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC'});
        return `<span class="recent-badge">Added ${this.escapeHtml(date)}</span>`;
    }

    wayfindingNote(business) {
        if (this.activeDataset !== 'wayfinding' || typeof business.notes !== 'string') return '';
        const note = business.notes
            .replace(/^Extracted from UK directory;\s*/i, '')
            .replace(/^Direct site reached from Applied Wayfinding and contains\s+/i, '')
            .replace(/^Direct article and site evidence for\s+/i, '')
            .replace(/^Direct (?:site|service page|work page|about page|product page|discipline page|project page|page) (?:states|describes|has|covers|offers|includes)\s+/i, '')
            .replace(/\s+(?:project )?evidence\.$/i, '.')
            .trim();
        if (!note) return '';
        return `<p class="wayfinding-note">${this.escapeHtml(note.charAt(0).toUpperCase() + note.slice(1))}</p>`;
    }

    globalContactHTML(business) {
        if (this.activeDataset !== 'global-wayfinding' || !this.globalSupplement) return '';
        const route = this.globalSupplement.outreach.get(business.id);
        const contacts = this.globalSupplement.contacts.get(business.id) || [];
        if (!route && !contacts.length) return '';
        const safe = value => this.escapeHtml(typeof value === 'string' ? value.trim() : '');
        const emailLink = (value, label) => {
            const email = typeof value === 'string' ? value.trim() : '';
            return /^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(email) ? this.createLinkHTML(`mailto:${email}`, this.escapeHtml(label || email), 'mail') : '';
        };
        const profileLink = (value, label) => {
            const url = this.socialUrl(value, 'linkedin');
            return url ? this.createLinkHTML(url, label, 'linkedin') : '';
        };
        const sourceLink = value => {
            const url = this.webUrl(value);
            return url ? this.createLinkHTML(url, 'Source', 'globe') : '';
        };
        const title = route && [safe(route.primaryContactName), safe(route.primaryContactRole)].filter(Boolean).join(' · ');
        const routeLinks = route ? [emailLink(route.primaryEmail, 'Primary email'), emailLink(route.backupEmail, 'Backup email'), profileLink(route.contactLinkedIn, 'Contact LinkedIn')].filter(Boolean).join('') : '';
        const confidence = route && safe(route.confidence);
        const contactRows = contacts.map(contact => {
            const heading = [safe(contact.name), safe(contact.title)].filter(Boolean).join(' · ');
            const links = [emailLink(contact.email), profileLink(contact.linkedin, 'LinkedIn'), sourceLink(contact.source)].filter(Boolean).join('');
            return heading || links ? `<li><span>${heading}</span>${links ? `<div class="global-contact-links">${links}</div>` : ''}</li>` : '';
        }).filter(Boolean).join('');
        return `<details class="global-contact-details"><summary>Outreach & contacts${contacts.length ? ` <span>${contacts.length}</span>` : ''}</summary>
            <p class="global-contact-caution">Imported research · check details before use</p>
            ${route && (title || routeLinks) ? `<div class="global-route"><strong>Suggested route</strong>${title ? `<p>${title}</p>` : ''}${confidence ? `<small>Source confidence: ${confidence}</small>` : ''}${routeLinks ? `<div class="global-contact-links">${routeLinks}</div>` : ''}</div>` : ''}
            ${contactRows ? `<ul class="global-contact-list">${contactRows}</ul>` : ''}
        </details>`;
    }

    businessLinks(business) {
        const links = [];
        const website = this.webUrl(business.website);
        const email = typeof business.email === 'string' ? business.email.trim() : '';
        const linkedin = this.socialUrl(business.linkedin, 'linkedin');
        const instagram = this.socialUrl(business.instagram, 'instagram');
        const facebook = this.webUrl(business.facebook);
        if (website) links.push(this.createLinkHTML(website, 'Website', 'globe'));
        if (/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(email)) links.push(this.createLinkHTML(`mailto:${email}`, 'Email', 'mail'));
        if (linkedin) links.push(this.createLinkHTML(linkedin, 'LinkedIn', 'linkedin'));
        if (instagram) links.push(this.createLinkHTML(instagram, 'Instagram', 'instagram'));
        if (facebook) links.push(this.createLinkHTML(facebook, 'Facebook', 'facebook'));
        return links;
    }

    webUrl(value) {
        if (typeof value !== 'string' || !value.trim()) return '';
        try {
            const raw = value.trim();
            const url = new URL(/^https?:\/\//i.test(raw) ? raw : `https://${raw}`);
            if (!['http:', 'https:'].includes(url.protocol) || !url.hostname.includes('.')) return '';
            return url.href;
        } catch {
            return '';
        }
    }
    
    // Directory imports include placeholders, wrong-platform links and handles
    // alongside URLs. Count only values that actually describe this platform.
    socialUrl(value, platform) {
        if (typeof value !== 'string') return '';
        const raw = value.trim();
        if (!raw || /^(?:n\/?a|none|unknown|null|not available)$/i.test(raw)) return '';

        const prefix = platform === 'instagram' ? 'IG' : 'LI';
        const tagged = raw.match(new RegExp(`(?:^|[,;]\\s*)${prefix}:\\s*@?([a-z0-9._-]+)`, 'i'));
        if (tagged) {
            const handle = tagged[1];
            return platform === 'instagram'
                ? `https://www.instagram.com/${encodeURIComponent(handle)}/`
                : `https://www.linkedin.com/company/${encodeURIComponent(handle)}/`;
        }
        if (platform === 'instagram' && /^@?[a-z0-9_][a-z0-9._]{0,28}[a-z0-9_]$/i.test(raw)
            && /[a-z_]/i.test(raw)) {
            return `https://www.instagram.com/${encodeURIComponent(raw.replace(/^@/, ''))}/`;
        }
        try {
            const url = new URL(/^[a-z][a-z\d+.-]*:\/\//i.test(raw) ? raw : `https://${raw}`);
            const host = url.hostname.toLowerCase();
            if (!['https:', 'http:'].includes(url.protocol) ||
                !(host === `${platform}.com` || host.endsWith(`.${platform}.com`)) ||
                url.pathname === '/') return '';
            return url.href;
        } catch {
            return '';
        }
    }

    icon(name) {
        const paths = {
            globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/>',
            mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 7 8 6 8-6"/>',
            linkedin: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 10v7M8 7.5v.1M12 17v-7m0 3a3 3 0 0 1 6 0v4"/>',
            instagram: '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><path d="M17.5 6.5h.01"/>',
            facebook: '<path d="M15.5 4H14a3 3 0 0 0-3 3v3H8v3h3v7h3v-7h3l.5-3H14V7.5c0-.8.4-1.5 1.5-1.5H17V4z"/>',
            pin: '<path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
            phone: '<path d="M6.4 3.8 9 7.6 7.3 9.3a14 14 0 0 0 7.4 7.4l1.7-1.7 3.8 2.6-1 2.6c-.3.7-1 1.1-1.8 1-7.6-1-13.8-7.2-14.8-14.8-.1-.8.3-1.5 1-1.8z"/>',
            address: '<path d="M4 20V8l8-5 8 5v12M8 20v-7h8v7M9 8h.01M15 8h.01"/>'
        };
        return `<svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || ''}</svg>`;
    }

    createLinkHTML(url, label, icon) {
        const external = !url.startsWith('mailto:');
        return `<a href="${this.escapeHtml(url)}" ${external ? 'target="_blank" rel="noopener noreferrer"' : ''} class="card-link">${this.icon(icon)}<span>${label}</span></a>`;
    }
    
    getCategoryClass(category) {
        const map = {
            'Signage': 'category-signage',
            'Architects': 'category-architects',
            'Engraving': 'category-engraving',
            'Trophies': 'category-trophies'
        };
        return map[category] || '';
    }

    escapeHtml(text) {
        return String(text ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        })[character]);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new BusinessDirectory();
});
