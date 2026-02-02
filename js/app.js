// UK Business Directory - Main Application

class BusinessDirectory {
    constructor() {
        this.businesses = [];
        this.filteredBusinesses = [];
        this.currentView = 'grid';
        
        // DOM Elements
        this.searchInput = document.getElementById('searchInput');
        this.clearSearchBtn = document.getElementById('clearSearch');
        this.categoryFilter = document.getElementById('categoryFilter');
        this.countyFilter = document.getElementById('countyFilter');
        this.resetFiltersBtn = document.getElementById('resetFilters');
        this.resultsGrid = document.getElementById('resultsGrid');
        this.resultsList = document.getElementById('resultsList');
        this.resultsCount = document.getElementById('resultsCount');
        this.loading = document.getElementById('loading');
        this.noResults = document.getElementById('noResults');
        this.gridViewBtn = document.getElementById('gridView');
        this.listViewBtn = document.getElementById('listView');
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        await this.loadData();
        this.populateFilters();
        this.render();
    }
    
    setupEventListeners() {
        // Search
        this.searchInput.addEventListener('input', () => {
            this.clearSearchBtn.style.display = this.searchInput.value ? 'flex' : 'none';
            this.filter();
        });
        
        this.clearSearchBtn.addEventListener('click', () => {
            this.searchInput.value = '';
            this.clearSearchBtn.style.display = 'none';
            this.filter();
        });
        
        // Filters
        this.categoryFilter.addEventListener('change', () => this.filter());
        this.countyFilter.addEventListener('change', () => this.filter());
        
        // Reset
        this.resetFiltersBtn.addEventListener('click', () => this.resetFilters());
        
        // View Toggle
        this.gridViewBtn.addEventListener('click', () => this.setView('grid'));
        this.listViewBtn.addEventListener('click', () => this.setView('list'));
    }
    
    async loadData() {
        try {
            const response = await fetch('data/directory-data.json');
            this.businesses = await response.json();
            this.filteredBusinesses = [...this.businesses];
        } catch (error) {
            console.error('Error loading data:', error);
            this.loading.innerHTML = '<p>Error loading directory data. Please refresh.</p>';
        }
    }
    
    populateFilters() {
        // Get unique categories and counties
        const categories = [...new Set(this.businesses.map(b => b.category))].sort();
        const counties = [...new Set(this.businesses.map(b => b.county))].sort();
        
        // Populate category filter
        categories.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat;
            this.categoryFilter.appendChild(option);
        });
        
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
        const category = this.categoryFilter.value;
        const county = this.countyFilter.value;
        
        this.filteredBusinesses = this.businesses.filter(business => {
            // Search filter
            const matchesSearch = !searchTerm || 
                (business.company && business.company.toLowerCase().includes(searchTerm)) ||
                (business.address && business.address.toLowerCase().includes(searchTerm)) ||
                (business.county && business.county.toLowerCase().includes(searchTerm)) ||
                (business.category && business.category.toLowerCase().includes(searchTerm)) ||
                (business.email && business.email.toLowerCase().includes(searchTerm)) ||
                (business.phone && business.phone.toLowerCase().includes(searchTerm));
            
            // Category filter
            const matchesCategory = !category || business.category === category;
            
            // County filter
            const matchesCounty = !county || business.county === county;
            
            return matchesSearch && matchesCategory && matchesCounty;
        });
        
        this.render();
    }
    
    resetFilters() {
        this.searchInput.value = '';
        this.clearSearchBtn.style.display = 'none';
        this.categoryFilter.value = '';
        this.countyFilter.value = '';
        this.filteredBusinesses = [...this.businesses];
        this.render();
    }
    
    setView(view) {
        this.currentView = view;
        this.gridViewBtn.classList.toggle('active', view === 'grid');
        this.listViewBtn.classList.toggle('active', view === 'list');
        this.resultsGrid.style.display = view === 'grid' ? 'grid' : 'none';
        this.resultsList.style.display = view === 'list' ? 'flex' : 'none';
    }
    
    render() {
        this.loading.style.display = 'none';
        
        const count = this.filteredBusinesses.length;
        this.resultsCount.textContent = count.toLocaleString();
        
        if (count === 0) {
            this.noResults.style.display = 'block';
            this.resultsGrid.innerHTML = '';
            this.resultsList.innerHTML = '';
            return;
        }
        
        this.noResults.style.display = 'none';
        
        if (this.currentView === 'grid') {
            this.renderGrid();
        } else {
            this.renderList();
        }
    }
    
    renderGrid() {
        this.resultsGrid.innerHTML = this.filteredBusinesses.map(business => this.createCardHTML(business)).join('');
    }
    
    renderList() {
        this.resultsList.innerHTML = this.filteredBusinesses.map(business => this.createListItemHTML(business)).join('');
    }
    
    createCardHTML(business) {
        const categoryClass = this.getCategoryClass(business.category);
        const qualityClass = this.getQualityClass(business.quality);
        
        const links = [];
        if (business.website) links.push(this.createLinkHTML(business.website, 'Website', 'globe'));
        if (business.email) links.push(this.createLinkHTML(`mailto:${business.email}`, 'Email', 'mail'));
        if (business.linkedin) links.push(this.createLinkHTML(business.linkedin, 'LinkedIn', 'linkedin'));
        if (business.instagram) links.push(this.createLinkHTML(business.instagram, 'Instagram', 'instagram'));
        if (business.facebook) links.push(this.createLinkHTML(business.facebook, 'Facebook', 'facebook'));
        
        return `
            <article class="business-card">
                <div class="card-header">
                    <div>
                        <h3 class="card-title">${this.escapeHtml(business.company)}</h3>
                        <span class="card-category ${categoryClass}">${this.escapeHtml(business.category)}</span>
                    </div>
                </div>
                <p class="card-county">📍 ${this.escapeHtml(business.county)}</p>
                <div class="card-links">${links.join('')}</div>
                <div class="card-contact">
                    ${business.phone ? `<p>📞 ${this.escapeHtml(business.phone)}</p>` : ''}
                    ${business.address ? `<p>📍 ${this.escapeHtml(business.address)}</p>` : ''}
                </div>
            </article>
        `;
    }
    
    createListItemHTML(business) {
        const categoryClass = this.getCategoryClass(business.category);
        const qualityClass = this.getQualityClass(business.quality);
        
        const links = [];
        if (business.website) links.push(`<a href="${business.website}" target="_blank" class="card-link">🌐 Website</a>`);
        if (business.email) links.push(`<a href="mailto:${business.email}" class="card-link">✉️ Email</a>`);
        if (business.linkedin) links.push(`<a href="${business.linkedin}" target="_blank" class="card-link">💼 LinkedIn</a>`);
        if (business.instagram) links.push(`<a href="${business.instagram}" target="_blank" class="card-link">📷 Instagram</a>`);
        if (business.facebook) links.push(`<a href="${business.facebook}" target="_blank" class="card-link">👤 Facebook</a>`);
        
        return `
            <article class="business-list-item">
                <div class="list-item-main">
                    <div class="list-item-header">
                        <h3 class="card-title">${this.escapeHtml(business.company)}</h3>
                        <span class="card-category ${categoryClass}">${this.escapeHtml(business.category)}</span>
                    </div>
                    <p class="card-county">📍 ${this.escapeHtml(business.county)}</p>
                    <div class="card-links">${links.join('')}</div>
                </div>
                <div class="list-item-actions">
                    ${business.phone ? `<a href="tel:${business.phone}" class="card-link">📞 ${this.escapeHtml(business.phone)}</a>` : ''}
                </div>
            </article>
        `;
    }
    
    createLinkHTML(url, label, icon) {
        const icons = {
            globe: '🌐',
            mail: '✉️',
            linkedin: '💼',
            instagram: '📷',
            facebook: '👤'
        };
        return `<a href="${url}" target="_blank" class="card-link">${icons[icon]} ${label}</a>`;
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
    
    getQualityClass(quality) {
        if (quality >= 8) return 'quality-high';
        if (quality >= 6) return 'quality-medium';
        return 'quality-low';
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new BusinessDirectory();
});
