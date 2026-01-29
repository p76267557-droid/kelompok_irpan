from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from datetime import datetime
import math
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter app

# Database configuration
DB_CONFIG = {
    'host': os.getenv('MYSQLHOST'),
    'user': os.getenv('MYSQLUSER'),
    'password': os.getenv('MYSQLPASSWORD'),
    'database': os.getenv('MYSQLDATABASE'),
    'port': int(os.getenv('MYSQLPORT', 3306))
}

def get_db_connection():
    """Create and return database connection"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None

def normalize_value(value, min_val, max_val):
    """Normalize value between 0 and 1"""
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)

def calculate_earthquake_risk(magnitude, depth, distance):
    """
    Calculate earthquake risk based on parameters
    Formula: Risk = (W1*M + W2*(1-D) + W3*(1-dist)) * 100
    
    Where:
    - W1, W2, W3 are weights (0.5, 0.3, 0.2)
    - M: Normalized magnitude (higher = more risk)
    - D: Normalized depth (deeper = less risk)
    - dist: Normalized distance (closer = more risk)
    """
    
    # Normalize parameters
    norm_magnitude = normalize_value(magnitude, 1.0, 10.0)
    norm_depth = normalize_value(depth, 0, 700)  # Deeper is safer
    norm_distance = normalize_value(distance, 0, 1000)  # Closer is more dangerous
    
    # Weights for each parameter
    w_magnitude = 0.5  # Magnitude weight
    w_depth = 0.3      # Depth weight (inverse relationship)
    w_distance = 0.2   # Distance weight (inverse relationship)
    
    # Calculate risk score (0-1)
    risk_score = (
        w_magnitude * norm_magnitude +
        w_depth * (1 - norm_depth) +  # Inverse: deeper = less risk
        w_distance * (1 - norm_distance)  # Inverse: closer = more risk
    )
    
    # Convert to percentage (0-100%)
    risk_percentage = min(risk_score * 100, 100)
    
    # Determine category
    if risk_percentage < 40:
        category = "Rendah"
    elif risk_percentage < 70:
        category = "Sedang"
    else:
        category = "Tinggi"
    
    # Generate explanation
    explanation_parts = []
    if norm_magnitude > 0.7:
        explanation_parts.append(f"Magnitudo {magnitude} SR tergolong tinggi")
    elif norm_magnitude > 0.4:
        explanation_parts.append(f"Magnitudo {magnitude} SR sedang")
    else:
        explanation_parts.append(f"Magnitudo {magnitude} SR rendah")
    
    if norm_depth < 0.3:
        explanation_parts.append("kedalaman gempa dangkal")
    elif norm_depth < 0.7:
        explanation_parts.append("kedalaman gempa sedang")
    else:
        explanation_parts.append("kedalaman gempa dalam")
    
    if norm_distance < 0.3:
        explanation_parts.append("jarak dari pusat gempa dekat")
    elif norm_distance < 0.7:
        explanation_parts.append("jarak dari pusat gempa sedang")
    else:
        explanation_parts.append("jarak dari pusat gempa jauh")
    
    explanation = f"Berdasarkan parameter: {', '.join(explanation_parts)}."
    
    return {
        "skor_risiko": round(risk_percentage, 2),
        "kategori_risiko": category,
        "penjelasan": explanation
    }

def calculate_flood_risk(rainfall, altitude, drainage_condition):
    """
    Calculate flood risk based on parameters
    Formula: Risk = (W1*R + W2*(1-A) + W3*D) * 100
    
    Where:
    - W1, W2, W3 are weights (0.4, 0.3, 0.3)
    - R: Normalized rainfall (higher = more risk)
    - A: Normalized altitude (higher = less risk)
    - D: Drainage condition score (bad = higher risk)
    """
    
    # Normalize parameters
    norm_rainfall = normalize_value(rainfall, 0, 500)
    norm_altitude = normalize_value(altitude, 0, 3000)  # Higher is safer
    
    # Convert drainage condition to numerical value
    drainage_scores = {"baik": 0.2, "sedang": 0.5, "buruk": 0.8}
    drainage_score = drainage_scores.get(drainage_condition.lower(), 0.5)
    
    # Weights for each parameter
    w_rainfall = 0.4
    w_altitude = 0.3
    w_drainage = 0.3
    
    # Calculate risk score (0-1)
    risk_score = (
        w_rainfall * norm_rainfall +
        w_altitude * (1 - norm_altitude) +  # Inverse: higher altitude = less risk
        w_drainage * drainage_score
    )
    
    # Convert to percentage (0-100%)
    risk_percentage = min(risk_score * 100, 100)
    
    # Determine category
    if risk_percentage < 40:
        category = "Rendah"
    elif risk_percentage < 70:
        category = "Sedang"
    else:
        category = "Tinggi"
    
    # Generate explanation
    explanation_parts = []
    if norm_rainfall > 0.7:
        explanation_parts.append(f"curah hujan {rainfall} mm/jam sangat tinggi")
    elif norm_rainfall > 0.4:
        explanation_parts.append(f"curah hujan {rainfall} mm/jam tinggi")
    else:
        explanation_parts.append(f"curah hujan {rainfall} mm/jam normal")
    
    if norm_altitude > 0.7:
        explanation_parts.append("ketinggian wilayah cukup tinggi")
    elif norm_altitude > 0.4:
        explanation_parts.append("ketinggian wilayah sedang")
    else:
        explanation_parts.append("ketinggian wilayah rendah")
    
    explanation_parts.append(f"kondisi drainase {drainage_condition}")
    
    explanation = f"Berdasarkan parameter: {', '.join(explanation_parts)}."
    
    return {
        "skor_risiko": round(risk_percentage, 2),
        "kategori_risiko": category,
        "penjelasan": explanation
    }

def calculate_fire_risk(area, material_type, wind_speed):
    """
    Calculate fire risk based on parameters
    Formula: Risk = (W1*Ar + W2*M + W3*W) * 100
    
    Where:
    - W1, W2, W3 are weights (0.4, 0.3, 0.3)
    - Ar: Normalized area (larger = more risk)
    - M: Material flammability score
    - W: Normalized wind speed (faster = more risk)
    """
    
    # Normalize parameters
    norm_area = normalize_value(area, 0, 10000)
    norm_wind = normalize_value(wind_speed, 0, 100)
    
    # Convert material type to numerical value
    material_scores = {"sulit": 0.2, "sedang": 0.5, "mudah": 0.8}
    material_score = material_scores.get(material_type.lower(), 0.5)
    
    # Weights for each parameter
    w_area = 0.4
    w_material = 0.3
    w_wind = 0.3
    
    # Calculate risk score (0-1)
    risk_score = (
        w_area * norm_area +
        w_material * material_score +
        w_wind * norm_wind
    )
    
    # Convert to percentage (0-100%)
    risk_percentage = min(risk_score * 100, 100)
    
    # Determine category
    if risk_percentage < 40:
        category = "Rendah"
    elif risk_percentage < 70:
        category = "Sedang"
    else:
        category = "Tinggi"
    
    # Generate explanation
    explanation_parts = []
    if norm_area > 0.7:
        explanation_parts.append(f"luas area {area} m² sangat luas")
    elif norm_area > 0.4:
        explanation_parts.append(f"luas area {area} m² cukup luas")
    else:
        explanation_parts.append(f"luas area {area} m² terbatas")
    
    explanation_parts.append(f"material {material_type} terbakar")
    
    if norm_wind > 0.7:
        explanation_parts.append(f"kecepatan angin {wind_speed} km/jam tinggi")
    elif norm_wind > 0.4:
        explanation_parts.append(f"kecepatan angin {wind_speed} km/jam sedang")
    else:
        explanation_parts.append(f"kecepatan angin {wind_speed} km/jam rendah")
    
    explanation = f"Berdasarkan parameter: {', '.join(explanation_parts)}."
    
    return {
        "skor_risiko": round(risk_percentage, 2),
        "kategori_risiko": category,
        "penjelasan": explanation
    }

def save_simulation_result(disaster_type, parameters, result):
    """Save simulation result to database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Prepare data for insertion
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if disaster_type == 'gempa':
            sql = """
            INSERT INTO simulasi_gempa 
            (magnitude, depth, distance, skor_risiko, kategori_risiko, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (
                parameters['magnitude'],
                parameters['depth'],
                parameters['distance'],
                result['skor_risiko'],
                result['kategori_risiko'],
                timestamp
            )
        elif disaster_type == 'banjir':
            sql = """
            INSERT INTO simulasi_banjir 
            (rainfall, altitude, drainage_condition, skor_risiko, kategori_risiko, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (
                parameters['rainfall'],
                parameters['altitude'],
                parameters['drainageCondition'],
                result['skor_risiko'],
                result['kategori_risiko'],
                timestamp
            )
        else:  # kebakaran
            sql = """
            INSERT INTO simulasi_kebakaran 
            (area, material_type, wind_speed, skor_risiko, kategori_risiko, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            values = (
                parameters['area'],
                parameters['materialType'],
                parameters['windSpeed'],
                result['skor_risiko'],
                result['kategori_risiko'],
                timestamp
            )
        
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving to database: {e}")
        if conn:
            conn.close()
        return False

@app.route('/api/calculate/<disaster_type>', methods=['POST'])
def calculate_risk(disaster_type):
    """API endpoint to calculate disaster risk"""
    try:
        data = request.get_json()
        
        if disaster_type == 'gempa':
            magnitude = float(data.get('magnitude', 5.0))
            depth = float(data.get('depth', 10.0))
            distance = float(data.get('distance', 50.0))
            
            result = calculate_earthquake_risk(magnitude, depth, distance)
            
        elif disaster_type == 'banjir':
            rainfall = float(data.get('rainfall', 50.0))
            altitude = float(data.get('altitude', 50.0))
            drainage_condition = data.get('drainageCondition', 'sedang')
            
            result = calculate_flood_risk(rainfall, altitude, drainage_condition)
            
        elif disaster_type == 'kebakaran':
            area = float(data.get('area', 100.0))
            material_type = data.get('materialType', 'sedang')
            wind_speed = float(data.get('windSpeed', 10.0))
            
            result = calculate_fire_risk(area, material_type, wind_speed)
            
        else:
            return jsonify({
                "success": False,
                "message": "Jenis bencana tidak valid"
            }), 400
        
        # Save to database
        save_simulation_result(disaster_type, data, result)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@app.route('/api/history/<disaster_type>', methods=['GET'])
def get_history(disaster_type):
    """API endpoint to get simulation history"""
    conn = get_db_connection()
    if not conn:
        return jsonify({
            "success": False,
            "message": "Database connection failed"
        }), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        if disaster_type == 'gempa':
            cursor.execute("SELECT * FROM simulasi_gempa ORDER BY timestamp DESC LIMIT 10")
        elif disaster_type == 'banjir':
            cursor.execute("SELECT * FROM simulasi_banjir ORDER BY timestamp DESC LIMIT 10")
        elif disaster_type == 'kebakaran':
            cursor.execute("SELECT * FROM simulasi_kebakaran ORDER BY timestamp DESC LIMIT 10")
        else:
            return jsonify({
                "success": False,
                "message": "Jenis bencana tidak valid"
            }), 400
        
        history = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "data": history
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Disaster Simulation API",
        "version": "1.0.0"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
