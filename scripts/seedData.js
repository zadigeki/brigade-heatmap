require('dotenv').config();
const mongoose = require('mongoose');
const DataPoint = require('../models/DataPoint');

// Sample locations around major cities
const locations = [
    // New York City area
    { name: "Times Square, NYC", lat: 40.7589, lng: -73.9851 },
    { name: "Central Park, NYC", lat: 40.7831, lng: -73.9712 },
    { name: "Brooklyn Bridge, NYC", lat: 40.7061, lng: -74.0087 },
    { name: "Staten Island Ferry, NYC", lat: 40.6892, lng: -74.0445 },
    { name: "Queens Center, NYC", lat: 40.7282, lng: -73.7949 },
    
    // Los Angeles area
    { name: "Hollywood, LA", lat: 34.0928, lng: -118.3287 },
    { name: "Santa Monica, LA", lat: 34.0195, lng: -118.4912 },
    { name: "Downtown LA", lat: 34.0522, lng: -118.2437 },
    { name: "Beverly Hills, LA", lat: 34.0736, lng: -118.4004 },
    { name: "Venice Beach, LA", lat: 33.9850, lng: -118.4695 },
    
    // Chicago area
    { name: "Millennium Park, Chicago", lat: 41.8826, lng: -87.6226 },
    { name: "Navy Pier, Chicago", lat: 41.8917, lng: -87.6086 },
    { name: "Willis Tower, Chicago", lat: 41.8789, lng: -87.6359 },
    { name: "Lincoln Park, Chicago", lat: 41.9278, lng: -87.6389 },
    { name: "Wicker Park, Chicago", lat: 41.9089, lng: -87.6773 },
    
    // San Francisco area
    { name: "Golden Gate Bridge, SF", lat: 37.8199, lng: -122.4783 },
    { name: "Fisherman's Wharf, SF", lat: 37.8080, lng: -122.4177 },
    { name: "Union Square, SF", lat: 37.7880, lng: -122.4074 },
    { name: "Lombard Street, SF", lat: 37.8021, lng: -122.4187 },
    { name: "Alcatraz Island, SF", lat: 37.8267, lng: -122.4230 },
];

const categories = [
    'Traffic Incident',
    'Emergency Service',
    'Public Event',
    'Construction',
    'Weather Alert',
    'Tourist Activity',
    'Business Activity',
    'Transportation Hub',
    'Social Gathering',
    'Maintenance Work'
];

const sources = [
    'Traffic Sensors',
    'Emergency Services',
    'Event Management',
    'Weather Station',
    'Mobile App',
    'Social Media',
    'Public Reports',
    'Government Agency'
];

async function generateSampleData(numDays = 30, pointsPerDay = 200) {
    const dataPoints = [];
    const today = new Date();
    
    console.log(`Generating ${numDays * pointsPerDay} sample data points...`);
    
    for (let day = 0; day < numDays; day++) {
        const currentDate = new Date(today);
        currentDate.setDate(today.getDate() - day);
        
        for (let point = 0; point < pointsPerDay; point++) {
            // Select a base location (80% chance) or generate random coordinates (20% chance)
            let latitude, longitude, locationName;
            
            if (Math.random() < 0.8) {
                // Use predefined location with some scatter
                const baseLocation = locations[Math.floor(Math.random() * locations.length)];
                const scatterRadius = 0.02; // ~2km radius
                
                latitude = baseLocation.lat + (Math.random() - 0.5) * scatterRadius;
                longitude = baseLocation.lng + (Math.random() - 0.5) * scatterRadius;
                locationName = baseLocation.name;
            } else {
                // Generate random coordinates in continental US
                latitude = 25 + Math.random() * 24; // 25-49 degrees north
                longitude = -125 + Math.random() * 50; // -125 to -75 degrees west
                locationName = 'Random Location';
            }
            
            // Generate random time within the day
            const timestamp = new Date(currentDate);
            timestamp.setHours(Math.floor(Math.random() * 24));
            timestamp.setMinutes(Math.floor(Math.random() * 60));
            timestamp.setSeconds(Math.floor(Math.random() * 60));
            
            // Create data point
            const dataPoint = {
                latitude: Math.round(latitude * 10000) / 10000, // 4 decimal precision
                longitude: Math.round(longitude * 10000) / 10000,
                timestamp: timestamp,
                location: locationName,
                value: Math.floor(Math.random() * 100) + 1, // 1-100
                category: categories[Math.floor(Math.random() * categories.length)],
                source: sources[Math.floor(Math.random() * sources.length)],
                additionalInfo: `Generated data point for ${locationName}`,
                metadata: {
                    generated: true,
                    dayOfWeek: timestamp.getDay(),
                    hour: timestamp.getHours(),
                    isWeekend: timestamp.getDay() === 0 || timestamp.getDay() === 6
                }
            };
            
            dataPoints.push(dataPoint);
        }
        
        // Progress indicator
        if (day % 5 === 0) {
            console.log(`Generated data for ${day + 1}/${numDays} days...`);
        }
    }
    
    return dataPoints;
}

async function seedDatabase() {
    try {
        console.log('🔗 Connecting to MongoDB...');
        await mongoose.connect(process.env.MONGODB_URI);
        console.log('✅ Connected to MongoDB');
        
        // Clear existing data (optional - comment out if you want to keep existing data)
        console.log('🗑️ Clearing existing data...');
        await DataPoint.deleteMany({});
        console.log('✅ Existing data cleared');
        
        // Generate sample data
        const sampleData = await generateSampleData(30, 200); // 30 days, 200 points per day
        
        // Insert data in batches for better performance
        const batchSize = 1000;
        let totalInserted = 0;
        
        console.log('📥 Inserting data into database...');
        for (let i = 0; i < sampleData.length; i += batchSize) {
            const batch = sampleData.slice(i, i + batchSize);
            await DataPoint.insertMany(batch);
            totalInserted += batch.length;
            console.log(`Inserted ${totalInserted}/${sampleData.length} data points...`);
        }
        
        console.log(`✅ Successfully seeded database with ${totalInserted} data points`);
        
        // Show some statistics
        const stats = await DataPoint.aggregate([
            {
                $group: {
                    _id: null,
                    totalPoints: { $sum: 1 },
                    averageValue: { $avg: '$value' },
                    uniqueLocations: { $addToSet: '$location' },
                    categories: { $addToSet: '$category' },
                    dateRange: {
                        $push: {
                            min: { $min: '$timestamp' },
                            max: { $max: '$timestamp' }
                        }
                    }
                }
            }
        ]);
        
        if (stats.length > 0) {
            console.log('\n📊 Database Statistics:');
            console.log(`   Total Points: ${stats[0].totalPoints}`);
            console.log(`   Average Value: ${stats[0].averageValue.toFixed(2)}`);
            console.log(`   Unique Locations: ${stats[0].uniqueLocations.length}`);
            console.log(`   Categories: ${stats[0].categories.length}`);
        }
        
    } catch (error) {
        console.error('❌ Error seeding database:', error);
        process.exit(1);
    } finally {
        await mongoose.connection.close();
        console.log('🔌 Database connection closed');
        process.exit(0);
    }
}

// Command line options
const args = process.argv.slice(2);
const daysArg = args.find(arg => arg.startsWith('--days='));
const pointsArg = args.find(arg => arg.startsWith('--points='));

const numDays = daysArg ? parseInt(daysArg.split('=')[1]) : 30;
const pointsPerDay = pointsArg ? parseInt(pointsArg.split('=')[1]) : 200;

console.log('🌱 Starting database seeding...');
console.log(`📅 Days: ${numDays}`);
console.log(`📍 Points per day: ${pointsPerDay}`);
console.log(`📊 Total points to generate: ${numDays * pointsPerDay}`);

seedDatabase();