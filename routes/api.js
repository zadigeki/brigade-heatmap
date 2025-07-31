const express = require('express');
const router = express.Router();
const DataPoint = require('../models/DataPoint');

// GET /api/geographic-data - Retrieve data points with date filtering
router.get('/geographic-data', async (req, res) => {
    try {
        const { start, end, category, location, minValue, limit = 10000 } = req.query;
        
        // Validate required parameters
        if (!start || !end) {
            return res.status(400).json({
                error: 'Start and end date parameters are required',
                example: '/api/geographic-data?start=2025-01-01&end=2025-01-31'
            });
        }
        
        // Validate date format
        const startDate = new Date(start);
        const endDate = new Date(end);
        
        if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
            return res.status(400).json({
                error: 'Invalid date format. Use YYYY-MM-DD format'
            });
        }
        
        if (startDate > endDate) {
            return res.status(400).json({
                error: 'Start date must be before or equal to end date'
            });
        }
        
        // Build query options
        const options = {};
        if (category) options.category = category;
        if (location) options.location = location;
        if (minValue !== undefined) options.minValue = parseFloat(minValue);
        
        // Query database
        const dataPoints = await DataPoint.findByDateRange(start, end, options)
            .limit(parseInt(limit))
            .lean(); // Use lean() for better performance
        
        res.json(dataPoints);
        
    } catch (error) {
        console.error('Error fetching geographic data:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: error.message
        });
    }
});

// GET /api/geographic-data/bounds - Retrieve data points within geographic bounds
router.get('/geographic-data/bounds', async (req, res) => {
    try {
        const { swLat, swLng, neLat, neLng, start, end } = req.query;
        
        // Validate required parameters
        if (!swLat || !swLng || !neLat || !neLng) {
            return res.status(400).json({
                error: 'Bounding box parameters are required: swLat, swLng, neLat, neLng'
            });
        }
        
        const southWest = { lat: parseFloat(swLat), lng: parseFloat(swLng) };
        const northEast = { lat: parseFloat(neLat), lng: parseFloat(neLng) };
        
        const dateFilter = {};
        if (start && end) {
            dateFilter.start = start;
            dateFilter.end = end;
        }
        
        const dataPoints = await DataPoint.findByBounds(southWest, northEast, dateFilter)
            .lean();
        
        res.json(dataPoints);
        
    } catch (error) {
        console.error('Error fetching data by bounds:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: error.message
        });
    }
});

// POST /api/geographic-data - Create new data point(s)
router.post('/geographic-data', async (req, res) => {
    try {
        const data = req.body;
        
        // Handle both single object and array of objects
        const dataArray = Array.isArray(data) ? data : [data];
        
        // Validate required fields for each data point
        const requiredFields = ['latitude', 'longitude', 'timestamp'];
        for (const point of dataArray) {
            for (const field of requiredFields) {
                if (point[field] === undefined || point[field] === null) {
                    return res.status(400).json({
                        error: `Missing required field: ${field}`,
                        required: requiredFields
                    });
                }
            }
            
            // Ensure timestamp is a valid date
            if (isNaN(new Date(point.timestamp).getTime())) {
                return res.status(400).json({
                    error: 'Invalid timestamp format',
                    example: '2025-01-15T10:30:00Z'
                });
            }
        }
        
        // Insert data points
        const result = await DataPoint.insertMany(dataArray);
        
        res.status(201).json({
            message: `Successfully created ${result.length} data point(s)`,
            count: result.length,
            data: result
        });
        
    } catch (error) {
        console.error('Error creating data points:', error);
        
        if (error.name === 'ValidationError') {
            return res.status(400).json({
                error: 'Validation error',
                details: error.message
            });
        }
        
        res.status(500).json({
            error: 'Internal server error',
            message: error.message
        });
    }
});

// GET /api/geographic-data/stats - Get data statistics
router.get('/geographic-data/stats', async (req, res) => {
    try {
        const { start, end } = req.query;
        
        const matchStage = {};
        if (start && end) {
            matchStage.timestamp = {
                $gte: new Date(start),
                $lte: new Date(end)
            };
        }
        
        const stats = await DataPoint.aggregate([
            { $match: matchStage },
            {
                $group: {
                    _id: null,
                    totalPoints: { $sum: 1 },
                    averageValue: { $avg: '$value' },
                    maxValue: { $max: '$value' },
                    minValue: { $min: '$value' },
                    uniqueLocations: { $addToSet: '$location' },
                    categories: { $addToSet: '$category' },
                    dateRange: {
                        $push: {
                            min: { $min: '$timestamp' },
                            max: { $max: '$timestamp' }
                        }
                    }
                }
            },
            {
                $addFields: {
                    uniqueLocationCount: { $size: '$uniqueLocations' },
                    categoryCount: { $size: '$categories' }
                }
            }
        ]);
        
        if (stats.length === 0) {
            return res.json({
                totalPoints: 0,
                message: 'No data points found'
            });
        }
        
        res.json(stats[0]);
        
    } catch (error) {
        console.error('Error fetching stats:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: error.message
        });
    }
});

// DELETE /api/geographic-data - Delete data points (with filters)
router.delete('/geographic-data', async (req, res) => {
    try {
        const { start, end, category, location, confirm } = req.query;
        
        if (!confirm || confirm !== 'true') {
            return res.status(400).json({
                error: 'Deletion requires confirmation',
                message: 'Add ?confirm=true to confirm deletion'
            });
        }
        
        const deleteQuery = {};
        
        if (start && end) {
            deleteQuery.timestamp = {
                $gte: new Date(start),
                $lte: new Date(end)
            };
        }
        
        if (category) deleteQuery.category = category;
        if (location) deleteQuery.location = new RegExp(location, 'i');
        
        const result = await DataPoint.deleteMany(deleteQuery);
        
        res.json({
            message: `Successfully deleted ${result.deletedCount} data point(s)`,
            deletedCount: result.deletedCount
        });
        
    } catch (error) {
        console.error('Error deleting data points:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: error.message
        });
    }
});

module.exports = router;