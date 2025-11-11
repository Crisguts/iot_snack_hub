# blueprints/dashboard/routes.py - DATABASE VERSION
from flask import Blueprint, render_template, jsonify, request
from datetime import datetime
from services.db_service import (
    get_latest_temperature_reading,
    get_temperature_history,
    get_fridge_threshold,
    update_fridge_threshold
)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Fan states (stored in memory for now, could be in DB)
fan_states = {1: False, 2: False}

@dashboard_bp.route('/')
def dashboard():
    """Main dashboard page - fetch real data from database"""
    fridge_data = {}
    historical_data = {}
    
    # Get data for both fridges
    for fridge_id in [1, 2]:
        # Get latest reading
        latest = get_latest_temperature_reading(fridge_id)
        threshold = get_fridge_threshold(fridge_id)
        
        if latest:
            fridge_data[fridge_id] = {
                'temperature': float(latest.get('temperature', 0)),
                'humidity': float(latest.get('humidity', 0)),
                'fan_on': fan_states[fridge_id],
                'threshold': threshold
            }
        else:
            # No data in DB yet
            fridge_data[fridge_id] = {
                'temperature': 0.0,
                'humidity': 0.0,
                'fan_on': fan_states[fridge_id],
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
def api_latest():
    """API endpoint for real-time fridge data updates from database"""
    data = {}
    
    for fridge_id in [1, 2]:
        latest = get_latest_temperature_reading(fridge_id)
        if latest:
            data[fridge_id] = {
                'temperature': float(latest.get('temperature', 0)),
                'humidity': float(latest.get('humidity', 0)),
                'fan_on': fan_states[fridge_id]
            }
        else:
            data[fridge_id] = {
                'temperature': 0.0,
                'humidity': 0.0,
                'fan_on': fan_states[fridge_id]
            }
    
    return jsonify({'success': True, 'data': data})

@dashboard_bp.route('/fan/states')
def fan_states_endpoint():
    """Get all fan states"""
    return jsonify({'success': True, 'fan_states': fan_states})

@dashboard_bp.route('/fan/<int:fridge_id>', methods=['POST'])
def toggle_fan(fridge_id):
    """Toggle fan for a specific fridge"""
    if fridge_id not in fan_states:
        return jsonify({'success': False, 'error': 'Invalid fridge ID'}), 400
    
    try:
        # Toggle state
        fan_states[fridge_id] = not fan_states[fridge_id]
        new_state = fan_states[fridge_id]
        
        # Control actual fan hardware (mocked)
        try:
            from services.gpio_service import turn_fan_on, turn_fan_off
            if new_state:
                turn_fan_on(fridge_id)
            else:
                turn_fan_off(fridge_id)
        except:
            print(f"[MOCK] Fan {fridge_id} -> {'ON' if new_state else 'OFF'}")
        
        return jsonify({
            'success': True,
            'fan_state': new_state,
            'fridge_id': fridge_id
        })
    except Exception as e:
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
def check_email_signals():
    """Check for email reply signals (YES to activate fan)"""
    try:
        from services.email_service import email_service
        state = email_service.get_and_clear_state()
        
        if state and state.get('action') == 'activate_fan':
            fridge_id = state.get('fridge_id', 1)
            
            try:
                from services.gpio_service import turn_fan_on
                fan_states[fridge_id] = True
                turn_fan_on(fridge_id)
                
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
