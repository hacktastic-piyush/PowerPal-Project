import sqlite3
import os
from datetime import datetime, timedelta

def init_db():
    # Check if database already exists
    db_exists = os.path.exists('users.db')
    
    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript('''
    -- Create users table
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );

    -- Create homes table
    CREATE TABLE IF NOT EXISTS homes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        location TEXT NOT NULL,
        size REAL NOT NULL,  -- in square meters
        roof_area REAL NOT NULL,  -- in square meters
        num_occupants INTEGER NOT NULL,
        construction_year INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    -- Create appliances table
    CREATE TABLE IF NOT EXISTS appliances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        home_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        power_rating REAL NOT NULL,  -- in watts
        avg_daily_usage REAL NOT NULL,  -- in kWh
        efficiency REAL NOT NULL,  -- as a decimal (0.0-1.0)
        status TEXT NOT NULL,  -- 'active', 'inactive', 'maintenance'
        last_maintenance TEXT,  -- date in YYYY-MM-DD format
        FOREIGN KEY (home_id) REFERENCES homes(id)
    );

    -- Create energy_usage table
    CREATE TABLE IF NOT EXISTS energy_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        home_id INTEGER NOT NULL,
        date TEXT NOT NULL,  -- in YYYY-MM-DD format
        amount REAL NOT NULL,  -- in kWh
        FOREIGN KEY (home_id) REFERENCES homes(id)
    );

    -- Create hourly_energy_usage table
    CREATE TABLE IF NOT EXISTS hourly_energy_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        home_id INTEGER NOT NULL,
        date TEXT NOT NULL,  -- in YYYY-MM-DD format
        hour INTEGER NOT NULL,  -- 0-23
        amount REAL NOT NULL,  -- in kWh
        FOREIGN KEY (home_id) REFERENCES homes(id)
    );

    -- Create recommendations table
    CREATE TABLE IF NOT EXISTS recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        home_id INTEGER NOT NULL,
        appliance_id INTEGER,  -- can be NULL if not appliance-specific
        type TEXT NOT NULL,  -- 'appliance_replacement', 'behavior_change', 'renewable_energy', 'maintenance', 'upgrading'
        description TEXT NOT NULL,
        potential_savings REAL NOT NULL,  -- annual savings in rupees
        implemented INTEGER NOT NULL DEFAULT 0,  -- 0 for not implemented, 1 for implemented
        implementation_date TEXT,  -- date in YYYY-MM-DD format, can be NULL
        FOREIGN KEY (home_id) REFERENCES homes(id),
        FOREIGN KEY (appliance_id) REFERENCES appliances(id)
    );

    -- Create alternative_appliances table
    CREATE TABLE IF NOT EXISTS alternative_appliances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        energy_efficiency REAL NOT NULL,  -- as a decimal (0.0-1.0)
        bee_star_rating INTEGER NOT NULL,  -- 1-5
        power_rating REAL NOT NULL,  -- in watts
        estimated_cost REAL NOT NULL  -- in rupees
    );

    -- Create solar_panels table
    CREATE TABLE IF NOT EXISTS solar_panels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        manufacturer TEXT NOT NULL,
        wattage REAL NOT NULL,  -- in watts
        efficiency REAL NOT NULL,  -- as a decimal (0.0-1.0)
        area_per_panel REAL NOT NULL,  -- in square meters
        cost_per_panel REAL NOT NULL,  -- in rupees
        warranty_years INTEGER NOT NULL
    );
    ''')
    
    # Only insert sample data if this is a new database
    if not db_exists:
        # Insert sample data
        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                      ('test_user', 'krishnashish2@gmail.com', 'KRISHNASHISH'))
        
        # Get the user ID
        user_id = cursor.lastrowid
        
        # Insert home
        cursor.execute('''
            INSERT INTO homes (user_id, location, size, roof_area, num_occupants, construction_year) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, 'Mumbai', 120, 80, 4, 2010))
        
        # Get the home ID
        home_id = cursor.lastrowid
        
        # Insert appliances
        appliances_data = [
            (home_id, 'AC - Living Room', 'Cooling', 1500, 6.0, 0.65, 'active', '2023-10-15'),
            (home_id, 'Refrigerator', 'Kitchen', 200, 2.4, 0.8, 'active', '2023-08-10'),
            (home_id, 'Washing Machine', 'Laundry', 500, 0.8, 0.75, 'active', '2023-11-05'),
            (home_id, 'TV - Living Room', 'Entertainment', 120, 0.6, 0.9, 'active', '2023-07-20'),
            (home_id, 'Microwave Oven', 'Kitchen', 800, 0.4, 0.85, 'active', '2023-09-30'),
            (home_id, 'Water Heater', 'Heating', 2000, 1.5, 0.6, 'active', '2023-11-15')
        ]
        
        cursor.executemany('''
            INSERT INTO appliances (home_id, name, category, power_rating, avg_daily_usage, 
                                   efficiency, status, last_maintenance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', appliances_data)
        
        # Insert energy usage data for last 12 months
        energy_usage_data = [
            (home_id, '2023-03-15', 310),
            (home_id, '2023-04-15', 320),
            (home_id, '2023-05-15', 340),
            (home_id, '2023-06-15', 380),
            (home_id, '2023-07-15', 420),
            (home_id, '2023-08-15', 450),
            (home_id, '2023-09-15', 410),
            (home_id, '2023-10-15', 380),
            (home_id, '2023-11-15', 350),
            (home_id, '2023-12-15', 340),
            (home_id, '2024-01-15', 330),
            (home_id, '2024-02-15', 320)
        ]
        
        cursor.executemany('''
            INSERT INTO energy_usage (home_id, date, amount) VALUES (?, ?, ?)
        ''', energy_usage_data)
        
        # Insert hourly energy usage for a week
        # First day pattern
        day1_pattern = [
            0.2, 0.2, 0.2, 0.2, 0.2, 0.3, 0.4, 0.7, 0.8, 0.5, 0.4, 0.4,
            0.5, 0.5, 0.5, 0.5, 0.6, 0.7, 1.2, 1.3, 1.2, 1.0, 0.6, 0.3
        ]
        
        # Second day pattern
        day2_pattern = [
            0.2, 0.2, 0.2, 0.2, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.7, 0.8,
            0.8, 0.8, 0.7, 0.7, 0.8, 0.9, 1.1, 1.2, 1.1, 0.9, 0.6, 0.3
        ]
        
        # Generate hourly data for 7 days
        hourly_usage_data = []
        start_date = datetime.now() - timedelta(days=7)
        
        for day in range(7):
            current_date = (start_date + timedelta(days=day)).strftime('%Y-%m-%d')
            pattern = day1_pattern if day % 2 == 0 else day2_pattern
            
            for hour in range(24):
                hourly_usage_data.append((home_id, current_date, hour, pattern[hour]))
        
        cursor.executemany('''
            INSERT INTO hourly_energy_usage (home_id, date, hour, amount) VALUES (?, ?, ?, ?)
        ''', hourly_usage_data)
        
        # Insert alternative appliances
        alt_appliances_data = [
            ('Daikin 5 Star Inverter AC', 'Cooling', 0.9, 5, 1200, 45000),
            ('LG 5 Star Refrigerator', 'Kitchen', 0.92, 5, 180, 35000),
            ('Samsung 5 Star Washing Machine', 'Laundry', 0.88, 5, 450, 32000),
            ('Sony Energy Efficient TV', 'Entertainment', 0.95, 4, 100, 40000),
            ('IFB Microwave Oven', 'Kitchen', 0.9, 4, 750, 15000),
            ('Racold 5 Star Water Heater', 'Heating', 0.85, 5, 1800, 12000),
            ('Philips LED Bulb', 'Lighting', 0.98, 5, 9, 250),
            ('Havells Energy Efficient Fan', 'Cooling', 0.85, 5, 60, 3500)
        ]
        
        cursor.executemany('''
            INSERT INTO alternative_appliances (name, category, energy_efficiency, 
                                              bee_star_rating, power_rating, estimated_cost)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', alt_appliances_data)
        
        # Insert solar panels
        solar_panels_data = [
            ('Tata Solar 440W', 'Tata Power Solar', 440, 0.21, 2.0, 18000, 25),
            ('Waaree 550W Mono PERC', 'Waaree Energies', 550, 0.23, 2.2, 22000, 25),
            ('Adani 400W', 'Adani Solar', 400, 0.20, 1.9, 16000, 20),
            ('Vikram 500W', 'Vikram Solar', 500, 0.22, 2.1, 20000, 25),
            ('Microtek 350W', 'Microtek', 350, 0.19, 1.8, 14000, 15)
        ]
        
        cursor.executemany('''
            INSERT INTO solar_panels (name, manufacturer, wattage, efficiency, 
                                    area_per_panel, cost_per_panel, warranty_years)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', solar_panels_data)
        
        # Get the appliance IDs
        cursor.execute("SELECT id FROM appliances WHERE home_id = ? AND name = ?", (home_id, 'AC - Living Room'))
        ac_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM appliances WHERE home_id = ? AND name = ?", (home_id, 'Water Heater'))
        heater_id = cursor.fetchone()[0]
        
        # Insert recommendations
        recommendations_data = [
            (home_id, ac_id, 'appliance_replacement', 'Replace your AC - Living Room with a Daikin 5 Star Inverter AC to save energy', 7500, 0),
            (home_id, heater_id, 'appliance_replacement', 'Replace your Water Heater with a Racold 5 Star Water Heater to save energy', 5000, 0),
            (home_id, None, 'renewable_energy', 'Install solar panels to generate approximately 350 kWh monthly', 29400, 0),
            (home_id, None, 'behavior_change', 'Set your AC to 24°C instead of 20°C to save up to 20% on cooling costs', 9600, 0),
            (home_id, None, 'maintenance', 'Clean your AC filters monthly to improve efficiency by up to 15%', 7200, 0)
        ]
        
        cursor.executemany('''
            INSERT INTO recommendations (home_id, appliance_id, type, description, potential_savings, implemented)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', recommendations_data)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database initialized successfully!")

# Run the initialization if this script is executed directly
if __name__ == "__main__":
    init_db()