// Training Catalog JavaScript
document.addEventListener('DOMContentLoaded', () => {
    let allTrainings = [];
    let currentFilter = 'all';

    // DOM Elements
    const trainingsGrid = document.getElementById('trainingsGrid');
    const searchInput = document.getElementById('searchInput');
    const filterButtons = document.querySelectorAll('.filter-btn');
    const totalTrainingsEl = document.getElementById('totalTrainings');
    const noResultsEl = document.getElementById('noResults');
    const loadingEl = document.getElementById('loading');
    const toastEl = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');

    // Utility function to escape HTML and prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Load trainings from JSON
    async function loadTrainings() {
        try {
            const response = await fetch('training-data.json');
            allTrainings = await response.json();
            
            // Hide loading, show grid
            loadingEl.style.display = 'none';
            
            // Update stats
            totalTrainingsEl.textContent = allTrainings.length;
            animateNumber(totalTrainingsEl, 0, allTrainings.length, 1000);
            
            // Display all trainings
            displayTrainings(allTrainings);
        } catch (error) {
            console.error('Error loading trainings:', error);
            loadingEl.innerHTML = '<p style="color: var(--accent-pink);">Error loading trainings. Please try again later.</p>';
        }
    }

    // Animate number counter
    function animateNumber(element, start, end, duration) {
        const range = end - start;
        const increment = range / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= end) {
                element.textContent = end;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current);
            }
        }, 16);
    }

    // Display trainings
    function displayTrainings(trainings) {
        trainingsGrid.innerHTML = '';
        
        if (trainings.length === 0) {
            noResultsEl.style.display = 'flex';
            noResultsEl.style.flexDirection = 'column';
            noResultsEl.style.alignItems = 'center';
            return;
        }
        
        noResultsEl.style.display = 'none';
        
        trainings.forEach((training, index) => {
            const card = createTrainingCard(training);
            trainingsGrid.appendChild(card);
            
            // Stagger animation
            setTimeout(() => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                
                requestAnimationFrame(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                });
            }, index * 50);
        });
    }

    // Create training card
    function createTrainingCard(training) {
        const card = document.createElement('div');
        card.className = 'training-card';
        
        const levelClass = training.level.toLowerCase();
        // Calculate seats percentage based on a dynamic scale (showing 100% at 50+ seats for better UX)
        const maxSeatsForDisplay = 50;
        const seatsPercentage = Math.min((training.availableSeats / maxSeatsForDisplay) * 100, 100);
        const initials = training.instructor.split(' ').map(n => n[0]).join('');
        
        // Format date
        const startDate = new Date(training.startDate);
        const formattedDate = startDate.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
        });
        
        card.innerHTML = `
            <div class="card-header">
                <span class="level-badge ${levelClass}">${training.level}</span>
                <span class="card-category">${training.category}</span>
            </div>
            
            <h3 class="card-title">${training.title}</h3>
            <p class="card-description">${training.description}</p>
            
            <div class="card-meta">
                <div class="meta-item">
                    <svg class="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <span>${training.duration}</span>
                </div>
                <div class="meta-item">
                    <svg class="meta-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                    </svg>
                    <span>${formattedDate}</span>
                </div>
            </div>
            
            <div class="seats-info">
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/>
                </svg>
                <span>${training.availableSeats} seats available</span>
            </div>
            <div class="seats-indicator">
                <div class="seats-fill" style="width: ${Math.min(seatsPercentage, 100)}%"></div>
            </div>
            
            <div class="tags">
                ${training.tags.map(tag => `<span class="tag">#${tag}</span>`).join('')}
            </div>
            
            <div class="card-footer">
                <div class="instructor">
                    <div class="instructor-avatar">${initials}</div>
                    <span class="instructor-name">${training.instructor}</span>
                </div>
                <button class="enroll-btn" data-training-id="${training.id}" data-training-title="${escapeHtml(training.title)}">
                    Enroll Now
                </button>
            </div>
        `;
        
        // Add event listener for enroll button
        const enrollBtn = card.querySelector('.enroll-btn');
        enrollBtn.addEventListener('click', () => {
            enrollInTraining(training.id, training.title);
        });
        
        return card;
    }

    // Filter trainings
    function filterTrainings() {
        const searchTerm = searchInput.value.toLowerCase();
        
        let filtered = allTrainings;
        
        // Apply level filter
        if (currentFilter !== 'all') {
            filtered = filtered.filter(t => t.level === currentFilter);
        }
        
        // Apply search filter
        if (searchTerm) {
            filtered = filtered.filter(t => 
                t.title.toLowerCase().includes(searchTerm) ||
                t.description.toLowerCase().includes(searchTerm) ||
                t.category.toLowerCase().includes(searchTerm) ||
                t.instructor.toLowerCase().includes(searchTerm) ||
                t.tags.some(tag => tag.toLowerCase().includes(searchTerm))
            );
        }
        
        displayTrainings(filtered);
    }

    // Event Listeners
    searchInput.addEventListener('input', filterTrainings);

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Update active state
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update current filter
            currentFilter = button.dataset.filter;
            
            // Filter trainings
            filterTrainings();
        });
    });

    // Enroll in training
    function enrollInTraining(trainingId, trainingTitle) {
        toastMessage.textContent = `Successfully enrolled in "${trainingTitle}"!`;
        toastEl.classList.add('show');
        
        setTimeout(() => {
            toastEl.classList.remove('show');
        }, 3000);
        
        console.log(`Enrolled in training ID: ${trainingId}`);
    }

    // Initialize
    loadTrainings();
});

// Add smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Focus search with Ctrl/Cmd + K
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('searchInput').focus();
    }
    
    // Clear search with Escape
    if (e.key === 'Escape') {
        const searchInput = document.getElementById('searchInput');
        if (searchInput.value) {
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input'));
        }
    }
});
