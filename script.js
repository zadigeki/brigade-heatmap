class GeographicHeatMapApp {
    constructor() {
        this.map = null;
        this.heatLayer = null;
        this.data = [];
        this.filteredData = [];
        this.currentRadius = 25;
        this.currentIntensity = 1;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupDateDefaults();
        this.initializeMap();
        this.loadData();
    }
    
    setupEventListeners() {
        document.getElementById('apply-filter').addEventListener('click', () => {
            this.applyDateFilter();
        });
        
        const radiusSlider = document.getElementById('heat-radius');
        const intensitySlider = document.getElementById('heat-intensity');
        
        radiusSlider.addEventListener('input', (e) => {
            this.currentRadius = parseInt(e.target.value);
            document.getElementById('radius-value').textContent = this.currentRadius;
            this.updateHeatMap();
        });
        
        intensitySlider.addEventListener('input', (e) => {
            this.currentIntensity = parseFloat(e.target.value);
            document.getElementById('intensity-value').textContent = this.currentIntensity;
            this.updateHeatMap();
        });
        
        window.addEventListener('resize', () => {
            if (this.map) {
                this.map.invalidateSize();
            }
        });
    }
    
    setupDateDefaults() {
        const today = new Date();
        const thirtyDaysAgo = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
        
        document.getElementById('end-date').value = today.toISOString().split('T')[0];
        document.getElementById('start-date').value = thirtyDaysAgo.toISOString().split('T')[0];
    }
    
    initializeMap() {
        // Initialize map centered on a default location (you can change this)
        this.map = L.map('map').setView([40.7128, -74.0060], 10); // New York City
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a> contributors',
            maxZoom: 18,
        }).addTo(this.map);
        
        // Add map click handler for debugging
        this.map.on('click', (e) => {
            console.log(`Clicked at: ${e.latlng.lat}, ${e.latlng.lng}`);
        });
    }
    
    async loadData() {
        this.showLoading(true);
        this.hideError();
        
        try {
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            
            // Use local API endpoint
            const apiUrl = `http://localhost:3000/api/geographic-data?start=${startDate}&end=${endDate}`;
            
            const response = await fetch(apiUrl);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            this.data = await response.json();
            
            // If API is not available, use mock data for demonstration
            if (this.data.length === 0) {
                this.data = this.generateMockGeographicData();
            }
            
            this.filteredData = [...this.data];
            this.updateHeatMap();
            this.updateDataInfo();
            this.fitMapToBounds();
            
        } catch (error) {
            console.error('Error loading data:', error);
            // Use mock data if API fails
            this.data = this.generateMockGeographicData();
            this.filteredData = [...this.data];
            this.updateHeatMap();
            this.updateDataInfo();
            this.fitMapToBounds();
            this.showError('Using mock data - API not available');
        } finally {
            this.showLoading(false);
        }
    }
    
    generateMockGeographicData() {
        const mockData = [];
        const startDate = new Date(document.getElementById('start-date').value);
        const endDate = new Date(document.getElementById('end-date').value);
        
        // Define some hotspot areas (you can modify these coordinates)
        const hotspots = [
            { lat: 40.7589, lng: -73.9851, name: "Times Square" },
            { lat: 40.7505, lng: -73.9934, name: "Herald Square" },
            { lat: 40.7421, lng: -74.0018, name: "Greenwich Village" },
            { lat: 40.7282, lng: -73.7949, name: "Queens Center" },
            { lat: 40.6892, lng: -74.0445, name: "Brooklyn Heights" },
            { lat: 40.8176, lng: -73.9482, name: "Bronx Park" },
            { lat: 40.7831, lng: -73.9712, name: "Central Park" },
            { lat: 40.7061, lng: -74.0087, name: "Financial District" }
        ];
        
        // Generate data points for each day in the range
        for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
            const currentDate = new Date(d).toISOString().split('T')[0];
            
            // Generate varying number of points per hotspot
            hotspots.forEach(hotspot => {
                const numPoints = Math.floor(Math.random() * 50) + 10; // 10-60 points per hotspot
                
                for (let i = 0; i < numPoints; i++) {
                    // Add some random scatter around each hotspot
                    const latOffset = (Math.random() - 0.5) * 0.02; // ~1km radius
                    const lngOffset = (Math.random() - 0.5) * 0.02;
                    
                    mockData.push({
                        latitude: hotspot.lat + latOffset,
                        longitude: hotspot.lng + lngOffset,
                        timestamp: currentDate,
                        location: hotspot.name,
                        value: Math.floor(Math.random() * 100) + 1,
                        additionalInfo: `Data point near ${hotspot.name}`
                    });
                }
            });
            
            // Add some random scattered points
            const randomPoints = Math.floor(Math.random() * 20) + 5;
            for (let i = 0; i < randomPoints; i++) {
                mockData.push({
                    latitude: 40.4774 + Math.random() * 0.6, // NYC area
                    longitude: -74.2591 + Math.random() * 0.5,
                    timestamp: currentDate,
                    location: "Random Location",
                    value: Math.floor(Math.random() * 50) + 1,
                    additionalInfo: "Random data point"
                });
            }
        }
        
        return mockData;
    }
    
    applyDateFilter() {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        if (!startDate || !endDate) {
            alert('Please select both start and end dates');
            return;
        }
        
        if (new Date(startDate) > new Date(endDate)) {
            alert('Start date must be before end date');
            return;
        }
        
        this.loadData();
    }
    
    updateHeatMap() {
        // Remove existing heat layer
        if (this.heatLayer) {
            this.map.removeLayer(this.heatLayer);
        }
        
        if (this.filteredData.length === 0) {
            return;
        }
        
        // Convert data to heat map format: [lat, lng, intensity]
        const heatData = this.processDataForHeatMap();
        
        // Create heat layer
        this.heatLayer = L.heatLayer(heatData, {
            radius: this.currentRadius,
            blur: 15,
            maxZoom: 17,
            max: this.currentIntensity,
            gradient: {
                0.0: 'blue',
                0.2: 'cyan',
                0.4: 'lime',
                0.6: 'yellow',
                0.8: 'orange',
                1.0: 'red'
            }
        }).addTo(this.map);
        
        // Add markers for individual points (optional, can be toggled)
        this.addDataPointMarkers();
    }
    
    processDataForHeatMap() {
        // Group points by location to create density
        const locationGroups = new Map();
        
        this.filteredData.forEach(point => {
            // Round coordinates to group nearby points
            const roundedLat = Math.round(point.latitude * 1000) / 1000;
            const roundedLng = Math.round(point.longitude * 1000) / 1000;
            const key = `${roundedLat},${roundedLng}`;
            
            if (!locationGroups.has(key)) {
                locationGroups.set(key, {
                    lat: point.latitude,
                    lng: point.longitude,
                    count: 0,
                    totalValue: 0,
                    points: []
                });
            }
            
            const group = locationGroups.get(key);
            group.count++;
            group.totalValue += point.value || 1;
            group.points.push(point);
        });
        
        // Convert to heat map format with density-based intensity
        const heatData = [];
        locationGroups.forEach(group => {
            // Intensity based on count of points at this location
            const intensity = Math.min(group.count / 10, 1); // Normalize to 0-1
            heatData.push([group.lat, group.lng, intensity]);
        });
        
        return heatData;
    }
    
    addDataPointMarkers() {
        // Only show markers if there are fewer than 100 points to avoid cluttering
        if (this.filteredData.length > 100) {
            return;
        }
        
        this.filteredData.forEach(point => {
            const marker = L.circleMarker([point.latitude, point.longitude], {
                radius: 3,
                fillColor: '#ff0000',
                color: '#ffffff',
                weight: 1,
                opacity: 0.8,
                fillOpacity: 0.6
            });
            
            // Add popup with point information
            const popupContent = `
                <strong>Location:</strong> ${point.location || 'Unknown'}<br/>
                <strong>Date:</strong> ${point.timestamp}<br/>
                <strong>Coordinates:</strong> ${point.latitude.toFixed(4)}, ${point.longitude.toFixed(4)}<br/>
                <strong>Value:</strong> ${point.value || 'N/A'}<br/>
                ${point.additionalInfo ? `<strong>Info:</strong> ${point.additionalInfo}` : ''}
            `;
            
            marker.bindPopup(popupContent);
            marker.addTo(this.map);
        });
    }
    
    fitMapToBounds() {
        if (this.filteredData.length === 0) {
            return;
        }
        
        const lats = this.filteredData.map(point => point.latitude);
        const lngs = this.filteredData.map(point => point.longitude);
        
        const bounds = L.latLngBounds(
            [Math.min(...lats), Math.min(...lngs)],
            [Math.max(...lats), Math.max(...lngs)]
        );
        
        this.map.fitBounds(bounds, { padding: [20, 20] });
    }
    
    updateDataInfo() {
        const pointCount = this.filteredData.length;
        document.getElementById('point-count').textContent = 
            `${pointCount} data point${pointCount !== 1 ? 's' : ''}`;
    }
    
    showLoading(show) {
        const loadingElement = document.getElementById('loading');
        if (show) {
            loadingElement.classList.remove('hidden');
        } else {
            loadingElement.classList.add('hidden');
        }
    }
    
    showError(message) {
        const errorElement = document.getElementById('error');
        if (message) {
            errorElement.textContent = message;
            errorElement.classList.remove('hidden');
            // Auto-hide error after 5 seconds
            setTimeout(() => {
                this.hideError();
            }, 5000);
        } else {
            this.hideError();
        }
    }
    
    hideError() {
        document.getElementById('error').classList.add('hidden');
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new GeographicHeatMapApp();
});