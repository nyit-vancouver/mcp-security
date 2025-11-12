from flask import Flask, render_template, request, jsonify
from detector import MCPToolDetector
from storage import DetectionStorage
import os

app = Flask(__name__)

# Initialize detector and storage
detector = MCPToolDetector('detection_rules.yaml')
storage = DetectionStorage('detection_results.json')


@app.route('/')
def index():
    """Main page showing detection results"""
    results = storage.get_recent_results(limit=100)
    stats = storage.get_statistics()
    return render_template('index.html', results=results, stats=stats)


@app.route('/api/detect', methods=['POST'])
def api_detect():
    """
    API endpoint for tool detection
    
    Accepts JSON:
    {
        "tool_name": "example_tool",
        "description": "Tool description text"
    }
    
    Returns JSON:
    {
        "success": true,
        "result": {
            "tool_name": "example_tool",
            "description": "Tool description text",
            "result": "Normal" or "Injection" or "Warning",
            "severity": "low" or "medium" or "critical",
            "risk_score": 0,
            "detected_patterns": [...],
            "timestamp": "2025-01-01T00:00:00"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        tool_name = data.get('tool_name', '')
        description = data.get('description', '')
        
        if not tool_name or not description:
            return jsonify({
                'success': False,
                'error': 'Both tool_name and description are required'
            }), 400
        
        # Run detection
        result = detector.detect(tool_name, description)
        
        # Save result
        storage.save_result(result)
        
        return jsonify({
            'success': True,
            'result': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/results', methods=['GET'])
def api_get_results():
    """Get all detection results"""
    try:
        limit = request.args.get('limit', 50, type=int)
        results = storage.get_recent_results(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    """Get detection statistics"""
    try:
        stats = storage.get_statistics()
        detector_stats = detector.get_stats()
        
        return jsonify({
            'success': True,
            'storage_stats': stats,
            'detector_stats': detector_stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/test', methods=['GET', 'POST'])
def test_page():
    """Test page for manual tool detection"""
    if request.method == 'POST':
        tool_name = request.form.get('tool_name', '')
        description = request.form.get('description', '')
        
        if tool_name and description:
            result = detector.detect(tool_name, description)
            storage.save_result(result)
            return render_template('test.html', result=result)
    
    return render_template('test.html', result=None)


@app.route('/clear', methods=['POST'])
def clear_results():
    """Clear all detection results"""
    storage.clear_all_results()
    return jsonify({'success': True, 'message': 'All results cleared'})


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)
