const mongoose = require('mongoose');

const deviceSchema = new mongoose.Schema({
    // Primary device identification
    terid: {
        type: String,
        required: true,
        unique: true,
        trim: true,
        index: true
    },
    carlicense: {
        type: String,
        required: true,
        trim: true,
        index: true
    },
    
    // Device information
    sim: {
        type: String,
        required: false,
        trim: true
    },
    channel: {
        type: Number,
        required: false,
        min: 0
    },
    platecolor: {
        type: Number,
        required: false,
        min: 1,
        max: 5,
        default: 1 // 1: blue, 2: yellow, 3: black, 4: white, 5: green
    },
    groupid: {
        type: Number,
        required: false,
        index: true
    },
    cname: {
        type: String,
        required: false,
        trim: true
    },
    devicetype: {
        type: String,
        required: false,
        trim: true,
        enum: ['1', '4'], // 1: MDR, 4: N9M
        default: '4'
    },
    linktype: {
        type: String,
        required: false,
        trim: true
    },
    
    // Device authentication
    deviceusername: {
        type: String,
        required: false,
        trim: true
    },
    devicepassword: {
        type: String,
        required: false,
        trim: true
    },
    
    // Network configuration
    registerip: {
        type: String,
        required: false,
        trim: true,
        validate: {
            validator: function(v) {
                if (!v) return true;
                return /^(\d{1,3}\.){3}\d{1,3}$/.test(v);
            },
            message: 'Invalid IP address format'
        }
    },
    registerport: {
        type: Number,
        required: false,
        min: 1,
        max: 65535
    },
    transmitip: {
        type: String,
        required: false,
        trim: true,
        validate: {
            validator: function(v) {
                if (!v) return true;
                return /^(\d{1,3}\.){3}\d{1,3}$/.test(v);
            },
            message: 'Invalid IP address format'
        }
    },
    transmitport: {
        type: Number,
        required: false,
        min: 1,
        max: 65535
    },
    
    // Channel permissions
    en: {
        type: Number,
        required: false,
        default: -1 // -1 represents all channel permissions
    },
    
    // Company information
    companybranch: {
        type: String,
        required: false,
        trim: true,
        maxlength: 200
    },
    companyname: {
        type: String,
        required: false,
        trim: true,
        maxlength: 200
    },
    
    // Status tracking
    onlineStatus: {
        type: String,
        enum: ['online', 'offline', 'unknown'],
        default: 'unknown',
        index: true
    },
    lastSeen: {
        type: Date,
        required: false
    },
    lastGPSUpdate: {
        type: Date,
        required: false
    },
    
    // GPS information (latest)
    currentLocation: {
        latitude: {
            type: Number,
            min: -90,
            max: 90
        },
        longitude: {
            type: Number,
            min: -180,
            max: 180
        },
        altitude: Number,
        speed: Number,
        direction: Number,
        gpstime: Date,
        address: String
    },
    
    // API sync metadata
    lastApiSync: {
        type: Date,
        default: Date.now,
        index: true
    },
    apiSyncStatus: {
        type: String,
        enum: ['success', 'failed', 'pending'],
        default: 'pending'
    },
    apiSyncError: {
        type: String,
        required: false
    },
    
    // Additional metadata
    metadata: {
        type: mongoose.Schema.Types.Mixed,
        required: false
    }
}, {
    timestamps: true,
    collection: 'devices'
});

// Compound indexes for better query performance
deviceSchema.index({ groupid: 1, onlineStatus: 1 });
deviceSchema.index({ lastApiSync: 1, apiSyncStatus: 1 });
deviceSchema.index({ terid: 1, lastSeen: -1 });
deviceSchema.index({ carlicense: 1, platecolor: 1 });

// 2dsphere index for geospatial queries on current location
deviceSchema.index({
    "currentLocation.latitude": 1,
    "currentLocation.longitude": 1
});

// Virtual for formatted license plate with color
deviceSchema.virtual('formattedLicense').get(function() {
    const colors = {
        1: 'Blue',
        2: 'Yellow', 
        3: 'Black',
        4: 'White',
        5: 'Green'
    };
    const colorName = colors[this.platecolor] || 'Unknown';
    return `${this.carlicense} (${colorName})`;
});

// Virtual for device type description
deviceSchema.virtual('deviceTypeDescription').get(function() {
    const types = {
        '1': 'MDR',
        '4': 'N9M'
    };
    return types[this.devicetype] || 'Unknown';
});

// Instance method to update online status
deviceSchema.methods.updateOnlineStatus = function(status, timestamp = new Date()) {
    this.onlineStatus = status;
    this.lastSeen = timestamp;
    return this.save();
};

// Instance method to update GPS location
deviceSchema.methods.updateLocation = function(locationData) {
    this.currentLocation = {
        latitude: locationData.gpslat ? parseFloat(locationData.gpslat) : this.currentLocation?.latitude,
        longitude: locationData.gpslng ? parseFloat(locationData.gpslng) : this.currentLocation?.longitude,
        altitude: locationData.altitude || this.currentLocation?.altitude,
        speed: locationData.speed || this.currentLocation?.speed,
        direction: locationData.direction || this.currentLocation?.direction,
        gpstime: locationData.gpstime ? new Date(locationData.gpstime) : this.currentLocation?.gpstime,
        address: locationData.address || this.currentLocation?.address
    };
    this.lastGPSUpdate = new Date();
    return this.save();
};

// Static method to find devices by group
deviceSchema.statics.findByGroup = function(groupId) {
    return this.find({ groupid: groupId }).sort({ carlicense: 1 });
};

// Static method to find online devices
deviceSchema.statics.findOnline = function() {
    return this.find({ onlineStatus: 'online' }).sort({ lastSeen: -1 });
};

// Static method to find devices that need sync update
deviceSchema.statics.findNeedingSync = function(maxAge = 10 * 60 * 1000) { // 10 minutes
    const cutoff = new Date(Date.now() - maxAge);
    return this.find({
        $or: [
            { lastApiSync: { $lt: cutoff } },
            { apiSyncStatus: 'failed' },
            { apiSyncStatus: 'pending' }
        ]
    });
};

// Static method to get device statistics
deviceSchema.statics.getStatistics = async function() {
    const stats = await this.aggregate([
        {
            $group: {
                _id: null,
                totalDevices: { $sum: 1 },
                onlineDevices: {
                    $sum: { $cond: [{ $eq: ['$onlineStatus', 'online'] }, 1, 0] }
                },
                offlineDevices: {
                    $sum: { $cond: [{ $eq: ['$onlineStatus', 'offline'] }, 1, 0] }
                },
                unknownDevices: {
                    $sum: { $cond: [{ $eq: ['$onlineStatus', 'unknown'] }, 1, 0] }
                },
                deviceTypes: { $addToSet: '$devicetype' },
                companies: { $addToSet: '$companyname' },
                lastSyncTime: { $max: '$lastApiSync' }
            }
        }
    ]);
    
    return stats[0] || {
        totalDevices: 0,
        onlineDevices: 0,
        offlineDevices: 0,
        unknownDevices: 0,
        deviceTypes: [],
        companies: [],
        lastSyncTime: null
    };
};

// Pre-save middleware to validate data
deviceSchema.pre('save', function(next) {
    // Ensure terid and carlicense are not empty
    if (!this.terid || !this.carlicense) {
        return next(new Error('Device terminal ID and car license are required'));
    }
    
    // Validate GPS coordinates if provided
    if (this.currentLocation) {
        if (this.currentLocation.latitude && 
            (this.currentLocation.latitude < -90 || this.currentLocation.latitude > 90)) {
            return next(new Error('Latitude must be between -90 and 90 degrees'));
        }
        if (this.currentLocation.longitude && 
            (this.currentLocation.longitude < -180 || this.currentLocation.longitude > 180)) {
            return next(new Error('Longitude must be between -180 and 180 degrees'));
        }
    }
    
    next();
});

// Transform output to clean format
deviceSchema.set('toJSON', {
    virtuals: true,
    transform: function(doc, ret) {
        delete ret._id;
        delete ret.__v;
        delete ret.devicepassword; // Don't expose passwords in JSON
        return ret;
    }
});

module.exports = mongoose.model('Device', deviceSchema);