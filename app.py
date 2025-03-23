from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import sqlite3
import json
import os
from datetime import datetime, timedelta
import random
import math
from werkzeug.security import generate_password_hash, check_password_hash
from db_init import init_db

app = Flask(__name__)
app.secret_key = 'your_secret_key'  
# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database setup
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn


init_db()
# Simulated device data
def generate_mock_data():
    devices = [
        {"id": 1, "name": "Refrigerator", "location": "Kitchen", "status": "Always on", 
         "consumption": 0.8, "running_time": 24, "efficiency": 85},
        {"id": 2, "name": "TV", "location": "Living Room", "status": "On", 
         "consumption": 0.5, "running_time": 4, "efficiency": 92},
        {"id": 3, "name": "AC Unit", "location": "Bedroom", "status": "On", 
         "consumption": 0.6, "running_time": 3, "efficiency": 64},
        {"id": 4, "name": "Washing Machine", "location": "Laundry Room", "status": "Off", 
         "consumption": 0.4, "running_time": 1, "efficiency": 88},
        {"id": 5, "name": "Computer", "location": "Office", "status": "On", 
         "consumption": 0.3, "running_time": 5, "efficiency": 95}
    ]
    
    # Generate 7 days of history
    today = datetime.now()
    history = []
    for i in range(7):
        day = today - timedelta(days=6-i)
        history.append({
            "date": day.strftime("%a"),
            "consumption": round(random.uniform(2.5, 3.5), 1)
        })
    
    return {"devices": devices, "history": history, "total": sum(d["consumption"] for d in devices)}

@app.route('/appliances')
def appliances():
    return render_template('appliances.html')

@app.route('/api/data')
def get_data():
    return jsonify(generate_mock_data())

# User model
class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['email'], user['password'])
    return None

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                         (username, email, password))
            conn.commit()
            flash('Account created successfully! Please log in.', 'success')
        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different email.', 'danger')
        finally:
            conn.close()
        return redirect(url_for('login'))
    return render_template('auth.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and user['password'] == password:
            login_user(User(user['id'], user['username'], user['email'], user['password']))
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('auth.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# Routes
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user data and energy stats
    conn = get_db_connection()
    user_id = 1  # In a real app, get from session
    
    # Get user profile
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    # Get home details
    home = conn.execute('SELECT * FROM homes WHERE user_id = ?', (user_id,)).fetchone()
    
    # Get appliances
    appliances = conn.execute('SELECT * FROM appliances WHERE home_id = ?', (home['id'],)).fetchall()
    
    # Get energy usage history
    usage_history = conn.execute('''
        SELECT date, amount 
        FROM energy_usage 
        WHERE home_id = ? 
        ORDER BY date DESC 
        LIMIT 12
    ''', (home['id'],)).fetchall()
    
    # Calculate energy distribution
    energy_distribution = {}
    total_energy = 0
    for appliance in appliances:
        total_energy += appliance['avg_daily_usage']
    
    for appliance in appliances:
        category = appliance['category']
        if category in energy_distribution:
            energy_distribution[category] += appliance['avg_daily_usage']
        else:
            energy_distribution[category] = appliance['avg_daily_usage']
    
    # Convert to percentages
    for category in energy_distribution:
        energy_distribution[category] = round((energy_distribution[category] / total_energy) * 100, 1)
    
    # Get recommendations
    recommendations = conn.execute('''
        SELECT * FROM recommendations 
        WHERE home_id = ? 
        ORDER BY potential_savings DESC
        LIMIT 4
    ''', (home['id'],)).fetchall()
    
    # Calculate solar potential
    solar_potential = calculate_solar_potential(home['location'], home['roof_area'])
    
    # Get applicable electricity tariff
    tariff = get_electricity_tariff(home['location'])
    
    # Calculate current bill based on usage and tariff
    monthly_usage = sum([row['amount'] for row in usage_history]) / len(usage_history)
    bill_details = calculate_electricity_bill(monthly_usage, tariff)
    
    conn.close()
    
    return render_template('dashboard.html',
                          user=user,
                          home=home,
                          appliances=appliances,
                          usage_history=usage_history,
                          energy_distribution=energy_distribution,
                          recommendations=recommendations,
                          solar_potential=solar_potential,
                          tariff=tariff,
                          bill_details=bill_details)



@app.route('/add_appliance', methods=['GET', 'POST'])
def add_appliance():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        power_rating = float(request.form['power_rating'])
        usage_hours = float(request.form['usage_hours'])
        efficiency = float(request.form['efficiency'])
        
        avg_daily_usage = calculate_daily_usage(power_rating, usage_hours, efficiency)
        
        conn = get_db_connection()
        user_id = 1  # In a real app, get from session
        home = conn.execute('SELECT id FROM homes WHERE user_id = ?', (user_id,)).fetchone()
        
        conn.execute('''
            INSERT INTO appliances (home_id, name, category, power_rating, avg_daily_usage, 
                                   efficiency, status, last_maintenance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (home['id'], name, category, power_rating, avg_daily_usage, 
              efficiency, 'active', datetime.now().strftime('%Y-%m-%d')))
        
        conn.commit()
        conn.close()
        
        flash('Appliance added successfully!', 'success')
        return redirect(url_for('appliances'))
    
    return render_template('add_appliance.html', categories=[
        'Lighting', 'Cooling', 'Heating', 'Kitchen', 'Entertainment', 'Laundry', 'Other'
    ])

@app.route('/update_appliance/<int:appliance_id>', methods=['GET', 'POST'])
def update_appliance(appliance_id):
    conn = get_db_connection()
    appliance = conn.execute('SELECT * FROM appliances WHERE id = ?', (appliance_id,)).fetchone()
    
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        power_rating = float(request.form['power_rating'])
        usage_hours = float(request.form['usage_hours'])
        efficiency = float(request.form['efficiency'])
        status = request.form['status']
        
        avg_daily_usage = calculate_daily_usage(power_rating, usage_hours, efficiency)
        
        conn.execute('''
            UPDATE appliances 
            SET name = ?, category = ?, power_rating = ?, avg_daily_usage = ?, 
                efficiency = ?, status = ?
            WHERE id = ?
        ''', (name, category, power_rating, avg_daily_usage, efficiency, status, appliance_id))
        
        conn.commit()
        conn.close()
        
        flash('Appliance updated successfully!', 'success')
        return redirect(url_for('appliances'))
    
    conn.close()
    return render_template('update_appliance.html', 
                          appliance=appliance,
                          categories=[
                              'Lighting', 'Cooling', 'Heating', 'Kitchen', 
                              'Entertainment', 'Laundry', 'Other'
                          ])

@app.route('/solar_calculator')
def solar_calculator():
    conn = get_db_connection()
    user_id = 1  # In a real app, get from session
    
    home = conn.execute('SELECT * FROM homes WHERE user_id = ?', (user_id,)).fetchone()
    
    # Get energy usage history for average consumption
    usage_history = conn.execute('''
        SELECT date, amount 
        FROM energy_usage 
        WHERE home_id = ? 
        ORDER BY date DESC 
        LIMIT 12
    ''', (home['id'],)).fetchall()
    
    avg_monthly_usage = sum([row['amount'] for row in usage_history]) / len(usage_history)
    
    # Calculate solar potential
    solar_potential = calculate_solar_potential(home['location'], home['roof_area'])
    
    # Get solar panel options available in India
    solar_panels = conn.execute('SELECT * FROM solar_panels ORDER BY efficiency DESC').fetchall()
    
    # Calculate ROI for different solar setups
    solar_setups = []
    for panel in solar_panels:
        num_panels = min(
            math.floor(home['roof_area'] / panel['area_per_panel']),
            math.ceil(avg_monthly_usage * 1000 / (panel['wattage'] * 30 * 5)) # Assuming 5 hours of sunlight
        )
        
        if num_panels < 1:
            continue
            
        setup = {
            'panel_name': panel['name'],
            'efficiency': panel['efficiency'],
            'num_panels': num_panels,
            'total_capacity': round(num_panels * panel['wattage'] / 1000, 2),  # in kW
            'estimated_generation': round(num_panels * panel['wattage'] * 5 * 30 / 1000, 2),  # monthly in kWh
            'installation_cost': round(num_panels * panel['cost_per_panel'] + 50000, 2),  # additional 50k for installation
            'payback_period': 0,
            'annual_savings': 0
        }
        
        # Get tariff to calculate savings
        tariff = get_electricity_tariff(home['location'])
        monthly_bill_before = calculate_electricity_bill(avg_monthly_usage, tariff)
        
        remaining_usage = max(0, avg_monthly_usage - setup['estimated_generation'])
        monthly_bill_after = calculate_electricity_bill(remaining_usage, tariff)
        
        setup['annual_savings'] = round((monthly_bill_before['total'] - monthly_bill_after['total']) * 12, 2)
        
        if setup['annual_savings'] > 0:
            setup['payback_period'] = round(setup['installation_cost'] / setup['annual_savings'], 1)
            solar_setups.append(setup)
    
    conn.close()
    
    return render_template('solar_calculator.html',
                         home=home,
                         avg_monthly_usage=avg_monthly_usage,
                         solar_potential=solar_potential,
                         solar_setups=solar_setups)

@app.route('/recommendations')
def recommendations():
    conn = get_db_connection()
    user_id = 1  # In a real app, get from session
    
    # Get home details
    home = conn.execute('SELECT * FROM homes WHERE user_id = ?', (user_id,)).fetchone()
    
    # Get appliances
    appliances = conn.execute('SELECT * FROM appliances WHERE home_id = ?', (home['id'],)).fetchall()
    
    # Get energy usage history
    usage_history = conn.execute('''
        SELECT date, amount 
        FROM energy_usage 
        WHERE home_id = ? 
        ORDER BY date DESC 
        LIMIT 12
    ''', (home['id'],)).fetchall()
    
    # Get recommendations
    recommendations = conn.execute('''
        SELECT * FROM recommendations 
        WHERE home_id = ? 
        ORDER BY potential_savings DESC
    ''', (home['id'],)).fetchall()
    
    # Generate new recommendations if we have less than 5
    if len(recommendations) < 5:
        generate_recommendations(home['id'], appliances, usage_history)
        recommendations = conn.execute('''
            SELECT * FROM recommendations 
            WHERE home_id = ? 
            ORDER BY potential_savings DESC
        ''', (home['id'],)).fetchall()
    
    conn.close()
    
    return render_template('recommendations.html',
                         home=home,
                         recommendations=recommendations)

@app.route('/implement_recommendation/<int:recommendation_id>')
def implement_recommendation(recommendation_id):
    conn = get_db_connection()
    
    # Mark recommendation as implemented
    conn.execute('''
        UPDATE recommendations
        SET implemented = 1, implementation_date = ?
        WHERE id = ?
    ''', (datetime.now().strftime('%Y-%m-%d'), recommendation_id))
    
    # Get recommendation details to update appliance if needed
    recommendation = conn.execute('SELECT * FROM recommendations WHERE id = ?', (recommendation_id,)).fetchone()
    
    if recommendation['type'] == 'appliance_replacement' and recommendation['appliance_id']:
        # Update appliance efficiency
        conn.execute('''
            UPDATE appliances
            SET efficiency = efficiency * 1.25, 
                power_rating = power_rating * 0.8,
                last_maintenance = ?
            WHERE id = ?
        ''', (datetime.now().strftime('%Y-%m-%d'), recommendation['appliance_id']))
    
    conn.commit()
    conn.close()
    
    flash('Recommendation implemented successfully!', 'success')
    return redirect(url_for('recommendations'))

@app.route('/simulate')
def simulator():
    return render_template("sim.html")
@app.route('/usage_patterns')
def usage_patterns():
    conn = get_db_connection()
    user_id = 1  # In a real app, get from session
    
    # Get home details
    home = conn.execute('SELECT * FROM homes WHERE user_id = ?', (user_id,)).fetchone()
    
    # Get hourly usage patterns for the last 7 days
    hourly_usage = conn.execute('''
        SELECT date, hour, amount 
        FROM hourly_energy_usage 
        WHERE home_id = ?
        AND date >= ?
        ORDER BY date, hour
    ''', (home['id'], (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))).fetchall()
    
    # Format data for charts
    daily_patterns = {}
    for row in hourly_usage:
        date = row['date']
        if date not in daily_patterns:
            daily_patterns[date] = [0] * 24
        
        daily_patterns[date][row['hour']] = row['amount']
    
    # Calculate average hourly usage
    avg_hourly_usage = [0] * 24
    for date in daily_patterns:
        for hour in range(24):
            avg_hourly_usage[hour] += daily_patterns[date][hour]
    
    for hour in range(24):
        avg_hourly_usage[hour] = round(avg_hourly_usage[hour] / len(daily_patterns), 2)
    
    # Get peak usage times
    peak_hours = []
    for hour in range(24):
        if avg_hourly_usage[hour] > sum(avg_hourly_usage) / 24 * 1.25:  # 25% above average
            peak_hours.append(hour)
    
    # Get energy usage by weekday vs weekend
    weekday_usage = conn.execute('''
        SELECT SUM(amount) as total
        FROM energy_usage 
        WHERE home_id = ?
        AND strftime('%w', date) NOT IN ('0', '6')
        AND date >= ?
    ''', (home['id'], (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))).fetchone()
    
    weekend_usage = conn.execute('''
        SELECT SUM(amount) as total
        FROM energy_usage 
        WHERE home_id = ?
        AND strftime('%w', date) IN ('0', '6')
        AND date >= ?
    ''', (home['id'], (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))).fetchone()
    
    # Get current tariff
    tariff = get_electricity_tariff(home['location'])
    
    # Potential savings by shifting usage
    potential_savings = 0
    if tariff.get('time_of_day_pricing'):
        # Calculate potential savings by shifting peak usage to off-peak times
        peak_usage = sum([avg_hourly_usage[hour] for hour in peak_hours])
        peak_cost = peak_usage * tariff['peak_rate'] * 30  # monthly
        off_peak_cost = peak_usage * tariff['off_peak_rate'] * 30  # monthly
        potential_savings = peak_cost - off_peak_cost
    
    conn.close()
    
    return render_template('usage_patterns.html',
                         home=home,
                         daily_patterns=daily_patterns,
                         avg_hourly_usage=avg_hourly_usage,
                         peak_hours=peak_hours,
                         weekday_usage=weekday_usage['total'],
                         weekend_usage=weekend_usage['total'],
                         tariff=tariff,
                         potential_savings=potential_savings)

@app.route('/community_comparison')
def community_comparison():
    conn = get_db_connection()
    user_id = 1  # In a real app, get from session
    
    # Get home details
    home = conn.execute('SELECT * FROM homes WHERE user_id = ?', (user_id,)).fetchone()
    
    # Get usage for current home
    current_usage = conn.execute('''
        SELECT AVG(amount) as avg_usage
        FROM energy_usage 
        WHERE home_id = ? 
        AND date >= ?
    ''', (home['id'], (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))).fetchone()
    
    # Get similar homes in the area
    similar_homes = conn.execute('''
        SELECT id FROM homes 
        WHERE location = ? 
        AND size BETWEEN ? AND ?
        AND id != ?
    ''', (home['location'], home['size'] * 0.8, home['size'] * 1.2, home['id'])).fetchall()
    
    similar_home_ids = [h['id'] for h in similar_homes]
    
    # If we have similar homes, get their usage
    community_data = {}
    if similar_home_ids:
        placeholders = ','.join(['?' for _ in similar_home_ids])
        
        # Get average usage for similar homes
        community_avg = conn.execute(f'''
            SELECT AVG(amount) as avg_usage
            FROM energy_usage 
            WHERE home_id IN ({placeholders})
            AND date >= ?
        ''', similar_home_ids + [(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')]).fetchone()
        
        # Get percentage ranking
        homes_with_higher_usage = conn.execute(f'''
            SELECT COUNT(DISTINCT home_id) as count
            FROM energy_usage 
            WHERE home_id IN ({placeholders})
            AND date >= ?
            GROUP BY home_id
            HAVING AVG(amount) > ?
        ''', similar_home_ids + 
            [(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'), current_usage['avg_usage']]).fetchone()
        
        total_similar_homes = len(similar_home_ids)
        percentile = round((1 - (homes_with_higher_usage['count'] / total_similar_homes)) * 100, 1) if homes_with_higher_usage else 0
        
        community_data = {
            'avg_usage': community_avg['avg_usage'],
            'your_usage': current_usage['avg_usage'],
            'percentile': percentile,
            'total_homes': total_similar_homes
        }
    
    conn.close()
    
    return render_template('community_comparison.html',
                         home=home,
                         community_data=community_data)

# Helper functions
def calculate_daily_usage(power_rating, usage_hours, efficiency):
    # Power rating in watts, returns kWh
    return round((power_rating * usage_hours * (1 / efficiency)) / 1000, 2)

def calculate_solar_potential(location, roof_area):
    # Simple calculation based on location and roof area
    # In a real app, this would use more sophisticated models and APIs
    solar_irradiance = {
        'Mumbai': 5.5,
        'Delhi': 5.8,
        'Bangalore': 5.4,
        'Chennai': 5.7,
        'Kolkata': 4.9,
        'Hyderabad': 5.6,
        'Pune': 5.5,
        'Ahmedabad': 5.9,
        'Jaipur': 6.0,
        'Lucknow': 5.3
    }
    
    # Default value if location not in our list
    irradiance = solar_irradiance.get(location, 5.5)
    
    # Assuming 15% panel efficiency and 80% system efficiency
    daily_potential = round(roof_area * irradiance * 0.15 * 0.8, 2)  # in kWh
    monthly_potential = daily_potential * 30
    annual_potential = daily_potential * 365
    
    return {
        'daily': daily_potential,
        'monthly': monthly_potential,
        'annual': annual_potential,
        'roof_utilization': min(1, roof_area / 25) * 100  # assuming minimum 25 sq m needed
    }

def get_electricity_tariff(location):
    # Simplified tariff structure based on location
    # In a real app, this would come from a database or API
    tariffs = {
        'Mumbai': {
            'provider': 'Adani Electricity Mumbai',
            'base_rate': 7.5,  # Rs per kWh
            'fixed_charge': 100,  # Rs per month
            'slabs': [
                {'limit': 100, 'rate': 5.5},
                {'limit': 300, 'rate': 7.5},
                {'limit': 500, 'rate': 10.0},
                {'limit': float('inf'), 'rate': 12.5}
            ],
            'time_of_day_pricing': True,
            'peak_hours': [9, 10, 11, 18, 19, 20, 21, 22],
            'peak_rate': 11.0,
            'off_peak_rate': 6.0
        },
        'Delhi': {
            'provider': 'BSES Rajdhani',
            'base_rate': 6.0,
            'fixed_charge': 130,
            'slabs': [
                {'limit': 200, 'rate': 4.5},
                {'limit': 400, 'rate': 6.0},
                {'limit': 800, 'rate': 8.5},
                {'limit': float('inf'), 'rate': 10.0}
            ],
            'time_of_day_pricing': False
        },
        'Bangalore': {
            'provider': 'BESCOM',
            'base_rate': 6.5,
            'fixed_charge': 70,
            'slabs': [
                {'limit': 100, 'rate': 4.0},
                {'limit': 200, 'rate': 5.5},
                {'limit': 500, 'rate': 7.0},
                {'limit': float('inf'), 'rate': 8.5}
            ],
            'time_of_day_pricing': False
        }
    }
    
    # Default tariff if location not in our list
    default_tariff = {
        'provider': 'Local Electricity Board',
        'base_rate': 6.0,
        'fixed_charge': 100,
        'slabs': [
            {'limit': 100, 'rate': 4.5},
            {'limit': 300, 'rate': 6.0},
            {'limit': 500, 'rate': 7.5},
            {'limit': float('inf'), 'rate': 9.0}
        ],
        'time_of_day_pricing': False
    }
    
    return tariffs.get(location, default_tariff)

def calculate_electricity_bill(usage, tariff):
    # Calculate bill based on usage and tariff structure
    total = tariff['fixed_charge']
    remaining = usage
    
    for slab in tariff['slabs']:
        if remaining <= 0:
            break
        
        units_in_slab = min(remaining, slab['limit'])
        total += units_in_slab * slab['rate']
        remaining -= units_in_slab
    
    # Add taxes (assuming 5% tax)
    tax = total * 0.05
    
    return {
        'provider': tariff['provider'],
        'usage': usage,
        'fixed_charge': tariff['fixed_charge'],
        'energy_charge': round(total - tariff['fixed_charge'], 2),
        'tax': round(tax, 2),
        'total': round(total + tax, 2)
    }

def generate_recommendations(home_id, appliances, usage_history):
    conn = get_db_connection()
    
    # Clear existing non-implemented recommendations
    conn.execute('''
        DELETE FROM recommendations
        WHERE home_id = ? AND implemented = 0
    ''', (home_id,))
    
    # 1. Identify inefficient appliances
    for appliance in appliances:
        if appliance['efficiency'] < 0.7:  # Low efficiency
            # Check for better alternatives
            alternatives = conn.execute('''
                SELECT * FROM alternative_appliances
                WHERE category = ? AND energy_efficiency > ?
                ORDER BY energy_efficiency DESC
                LIMIT 1
            ''', (appliance['category'], appliance['efficiency'])).fetchone()
            
            if alternatives:
                # Calculate potential savings
                current_daily_usage = appliance['avg_daily_usage']
                potential_daily_usage = current_daily_usage * (appliance['efficiency'] / alternatives['energy_efficiency'])
                annual_savings = (current_daily_usage - potential_daily_usage) * 365
                
                conn.execute('''
                    INSERT INTO recommendations 
                    (home_id, appliance_id, type, description, potential_savings, implemented)
                    VALUES (?, ?, ?, ?, ?, 0)
                ''', (
                    home_id,
                    appliance['id'],
                    'appliance_replacement',
                    f"Replace your {appliance['name']} with a {alternatives['name']} (BEE {alternatives['bee_star_rating']} star rated) to save energy",
                    annual_savings
                ))
    
    # 2. Check for usage patterns and suggest optimizations
    # (This would use more sophisticated analysis in a real app)
    avg_monthly_usage = sum([row['amount'] for row in usage_history]) / len(usage_history)
    
    # 2.1 Solar recommendation if usage is high
    if avg_monthly_usage > 300:  # High usage
        home = conn.execute('SELECT * FROM homes WHERE id = ?', (home_id,)).fetchone()
        solar_potential = calculate_solar_potential(home['location'], home['roof_area'])
        
        if solar_potential['roof_utilization'] > 60:  # Good roof for solar
            potential_savings = solar_potential['annual'] * 7  # Assuming Rs 7 per kWh
            
            conn.execute('''
                INSERT INTO recommendations 
                (home_id, type, description, potential_savings, implemented)
                VALUES (?, ?, ?, ?, 0)
            ''', (
                home_id,
                'renewable_energy',
                f"Install solar panels to generate approximately {solar_potential['monthly']} kWh monthly",
                potential_savings
            ))
    
    # 2.2 General recommendations
    general_recommendations = [
        {
            'type': 'behavior_change',
            'description': "Set your AC to 24°C instead of 20°C to save up to 20% on cooling costs",
            'savings': avg_monthly_usage * 0.1 * 12  # Assuming AC is 50% of usage and 20% savings
        },
        {
            'type': 'maintenance',
            'description': "Clean your AC filters monthly to improve efficiency by up to 15%",
            'savings': avg_monthly_usage * 0.075 * 12
        },
        {
            'type': 'behavior_change',
            'description': "Unplug electronics when not in use to reduce phantom power consumption",
            'savings': avg_monthly_usage * 0.05 * 12
        },
        {
            'type': 'upgrading',
            'description': "Switch all lighting to LED bulbs to reduce lighting energy use by 75%",
            'savings': avg_monthly_usage * 0.1 * 12  # Assuming lighting is 15% of usage
        }
    ]
    
    for rec in general_recommendations:
        conn.execute('''
            INSERT INTO recommendations 
            (home_id, type, description, potential_savings, implemented)
            VALUES (?, ?, ?, ?, 0)
        ''', (
            home_id,
            rec['type'],
            rec['description'],
            rec['savings']
        ))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
  
    app.run(debug=True)