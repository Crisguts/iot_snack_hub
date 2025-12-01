# blueprints/dashboard/routes.py - DATABASE VERSION
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash
from datetime import datetime
from functools import wraps
from services.db_service import (
    get_latest_temperature_reading,
    get_temperature_history,
    get_fridge_threshold,
    update_fridge_threshold
)
from services.gpio_service import (
    turn_fan_on,
    turn_fan_off,
    get_fan_state
)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def admin_required(f):
    """Decorator to require admin access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@dashboard_bp.route('/')
@admin_required
def dashboard():
    """Main dashboard page - fetch real data from database"""
    fridge_data = {}
    historical_data = {}
    
    # Get current fan states from GPIO service
    current_fan_states = get_fan_state()
    
    # Get data for both fridges
    for fridge_id in [1, 2]:
        # Get latest reading
        latest = get_latest_temperature_reading(fridge_id)
        threshold = get_fridge_threshold(fridge_id)
        
        if latest:
            fridge_data[fridge_id] = {
                'temperature': float(latest.get('temperature', 0)),
                'humidity': float(latest.get('humidity', 0)),
                'fan_on': current_fan_states[fridge_id],
                'threshold': threshold
            }
        else:
            # No data in DB yet
            fridge_data[fridge_id] = {
                'temperature': 0.0,
                'humidity': 0.0,
                'fan_on': current_fan_states[fridge_id],
                'threshold': threshold
            }
        
        # Get historical data for charts
        history = get_temperature_history(fridge_id, limit=50)
        history.reverse()  # Oldest first for chart
        
        timestamps = []
        temperatures = []
        humidities = []
        
        for record in history:
            created_at = record.get('created_at', '')
            # Parse timestamp: "2025-10-28 08:34:20.63841+00"
            try:
                dt = datetime.fromisoformat(created_at.replace('+00', ''))
                timestamps.append(dt.strftime('%H:%M'))
            except:
                timestamps.append('')
            
            temperatures.append(float(record.get('temperature', 0)))
            humidities.append(float(record.get('humidity', 0)))
        
        historical_data[fridge_id] = {
            'timestamps': timestamps,
            'temperature': temperatures,
            'humidity': humidities
        }
    
    return render_template(
        'dashboard.html',
        fridge_data=fridge_data,
        historical_data=historical_data
    )

@dashboard_bp.route('/api/latest')
@admin_required
def api_latest():
    """API endpoint for real-time fridge data updates from database"""
    data = {}
    current_fan_states = get_fan_state()
    
    for fridge_id in [1, 2]:
        latest = get_latest_temperature_reading(fridge_id)
        if latest:
            temp = float(latest.get('temperature', 0))
            data[fridge_id] = {
                'temperature': temp,
                'humidity': float(latest.get('humidity', 0)),
                'fan_on': current_fan_states[fridge_id]
            }
            
            # Check threshold and send alert if exceeded
            threshold = get_fridge_threshold(fridge_id)
            print(f"Dashboard: Fridge {fridge_id} - Temp: {temp}°C, Threshold: {threshold}°C")
            if temp > threshold:
                print(f"Dashboard: 🚨 THRESHOLD EXCEEDED for Fridge {fridge_id}")
                try:
                    from services.email_service import email_service
                    from services.db_service import supabase
                    
                    # Get fridge name
                    resp = supabase.table("refrigerators").select("name").eq("fridge_id", fridge_id).execute()
                    fridge_name = resp.data[0].get("name") if resp.data else f"Refrigerator {fridge_id}"
                    
                    # Send alert (email service handles its own duplicate prevention)
                    result = email_service.send_temperature_alert(
                        fridge_id=fridge_id,
                        current_temp=temp,
                        threshold=threshold,
                        fridge_name=fridge_name
                    )
                    if result:
                        print(f"Dashboard: ✅ Alert email sent for Fridge {fridge_id}")
                    elif result is False:
                        print(f"Dashboard: ⏱️ Alert on cooldown for Fridge {fridge_id}")
                    else:
                        print(f"Dashboard: ❌ Alert email failed for Fridge {fridge_id}")
                except Exception as e:
                    print(f"Dashboard: Error sending threshold alert: {e}")
            else:
                print(f"Dashboard: ✅ Fridge {fridge_id} within threshold")
        else:
            data[fridge_id] = {
                'temperature': 0.0,
                'humidity': 0.0,
                'fan_on': current_fan_states[fridge_id]
            }
    
    return jsonify({'success': True, 'data': data})

@dashboard_bp.route('/fan/states')
@admin_required
def fan_states_endpoint():
    """Get all fan states"""
    current_fan_states = get_fan_state()
    return jsonify({'success': True, 'fan_states': current_fan_states})

@dashboard_bp.route('/fan/<int:fridge_id>', methods=['POST'])
@admin_required
def toggle_fan(fridge_id):
    """Toggle fan for a specific fridge"""
    if fridge_id not in [1, 2]:
        return jsonify({'success': False, 'error': 'Invalid fridge ID'}), 400
    
    try:
        # Get current state from GPIO service
        current_state = get_fan_state(fridge_id)
        new_state = not current_state
        
        # Control fan hardware
        if new_state:
            turn_fan_on(fridge_id)
        else:
            turn_fan_off(fridge_id)
        
        return jsonify({
            'success': True,
            'fan_state': new_state,
            'fridge_id': fridge_id
        })
    except Exception as e:
        print(f"Error toggling fan {fridge_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/threshold/<int:fridge_id>', methods=['POST'])
def update_threshold_route(fridge_id):
    """Update temperature threshold for a fridge in database"""
    if fridge_id not in [1, 2]:
        return jsonify({'success': False, 'error': 'Invalid fridge ID'}), 400
    
    try:
        data = request.get_json()
        new_threshold = float(data.get('threshold', 0))
        
        if new_threshold < 0 or new_threshold > 50:
            return jsonify({'success': False, 'error': 'Threshold must be between 0-50°C'}), 400
        
        # Update in database
        success = update_fridge_threshold(fridge_id, new_threshold)
        
        if success:
            return jsonify({
                'success': True,
                'fridge_id': fridge_id,
                'threshold': new_threshold
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update threshold in database'}), 500
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid threshold value'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/api/email/test', methods=['POST'])
@admin_required
def test_email():
    """Send test email"""
    try:
        from services.email_service import email_service
        success = email_service.send_test()
        if success:
            return jsonify({'success': True, 'message': 'Test email sent successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to send email - check email service credentials'}), 500
    except Exception as e:
        error_msg = str(e)
        if 'AUTHENTICATIONFAILED' in error_msg or 'Invalid credentials' in error_msg:
            error_msg = 'Email authentication failed. Please configure app password in email service.'
        print(f"[MOCK] Test email error: {error_msg}")
        return jsonify({'success': False, 'error': error_msg}), 500

@dashboard_bp.route('/api/email/check-signals')
@admin_required
def check_email_signals():
    """Check for email reply signals (YES to activate fan)"""
    try:
        from services.email_service import email_service
        state = email_service.get_and_clear_state()
        
        if state and state.get('action') == 'activate_fan':
            fridge_id = state.get('fridge_id', 1)
            print(f"🔔 Dashboard detected fan activation signal for fridge {fridge_id}")
            
            try:
                # Turn on fan via GPIO service (tracks state automatically)
                print(f"🌀 Turning on fan for fridge {fridge_id}...")
                turn_fan_on(fridge_id)
                print(f"✅ Fan activated successfully")
                
                # Send success confirmation
                email_service.send_confirmation(fridge_id)
                
                return jsonify({
                    'success': True,
                    'fan_activated': True,
                    'fridge_id': fridge_id
                })
            except Exception as fan_error:
                # Fan activation failed - notify user via email
                print(f"Failed to activate fan: {fan_error}")
                
                try:
                    email_service.send_fan_error(fridge_id, str(fan_error))
                except:
                    print("Failed to send error notification email")
                
                return jsonify({
                    'success': False,
                    'error': f'Fan activation failed: {str(fan_error)}'
                }), 500
        
        return jsonify({'success': True, 'fan_activated': False})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
