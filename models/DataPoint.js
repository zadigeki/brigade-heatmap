const mongoose = require('mongoose');

const dataPointSchema = new mongoose.Schema({
    latitude: {
        type: Number,
        required: true,
        min: -90,
        max: 90,
        index: true
    },
    longitude: {
        type: Number,
        required: true,
        min: -180,
        max: 180,
        index: true
    },
    timestamp: {
        type: Date,
        required: true,
        index: true
    },
    location: {
        type: String,
        required: false,
        trim: true,
        maxlength: 200
    },
    value: {
        type: Number,
        required: false,
        default: 1,
        min: 0
    },
    additionalInfo: {
        type: String,
        required: false,
        trim: true,
        maxlength: 500
    },
    category: {
        type: String,
        required: false,
        trim: true,
        maxlength: 100,
        index: true
    },
    source: {
        type: String,
        required: false,
        trim: true,
        maxlength: 100
    },
    metadata: {
        type: mongoose.Schema.Types.Mixed,
        required: false
    }
}, {
    timestamps: true, // Adds createdAt and updatedAt fields
    collection: 'datapoints'
});

// Compound indexes for better query performance
dataPointSchema.index({ timestamp: 1, latitude: 1, longitude: 1 });
dataPointSchema.index({ timestamp: 1, category: 1 });
dataPointSchema.index({ location: 1, timestamp: 1 });

// 2dsphere index for geospatial queries
dataPointSchema.index({
    location: "2dsphere"
});

// Virtual for coordinate array (useful for geospatial queries)
dataPointSchema.virtual('coordinates').get(function() {
    return [this.longitude, this.latitude];
});

// Instance method to get distance from another point
dataPointSchema.methods.distanceFrom = function(lat, lng) {
    const R = 6371; // Earth's radius in kilometers
    const dLat = (lat - this.latitude) * Math.PI / 180;
    const dLon = (lng - this.longitude) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(this.latitude * Math.PI / 180) * Math.cos(lat * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
};

// Static method to find points within a date range
dataPointSchema.statics.findByDateRange = function(startDate, endDate, options = {}) {
    const query = {
        timestamp: {
            $gte: new Date(startDate),
            $lte: new Date(endDate)
        }
    };
    
    // Add optional filters
    if (options.category) {
        query.category = options.category;
    }
    
    if (options.location) {
        query.location = new RegExp(options.location, 'i');
    }
    
    if (options.minValue !== undefined) {
        query.value = { $gte: options.minValue };
    }
    
    return this.find(query).sort({ timestamp: -1 });
};

// Static method to find points within a geographic bounding box
dataPointSchema.statics.findByBounds = function(southWest, northEast, dateFilter = {}) {
    const query = {
        latitude: { $gte: southWest.lat, $lte: northEast.lat },
        longitude: { $gte: southWest.lng, $lte: northEast.lng }
    };
    
    if (dateFilter.start && dateFilter.end) {
        query.timestamp = {
            $gte: new Date(dateFilter.start),
            $lte: new Date(dateFilter.end)
        };
    }
    
    return this.find(query);
};

// Pre-save middleware to validate coordinates
dataPointSchema.pre('save', function(next) {
    // Ensure latitude is within valid range
    if (this.latitude < -90 || this.latitude > 90) {
        return next(new Error('Latitude must be between -90 and 90 degrees'));
    }
    
    // Ensure longitude is within valid range
    if (this.longitude < -180 || this.longitude > 180) {
        return next(new Error('Longitude must be between -180 and 180 degrees'));
    }
    
    next();
});

// Transform output to match frontend expectations
dataPointSchema.set('toJSON', {
    transform: function(doc, ret) {
        delete ret.__v;
        delete ret._id;
        return ret;
    }
});

module.exports = mongoose.model('DataPoint', dataPointSchema);