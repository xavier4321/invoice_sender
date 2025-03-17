from flask import Flask, render_template, jsonify, request
from send_invoice import process_invoices

app = Flask(__name__)

# Add this new route for Vercel's health check
@app.route('/_vercel/deploy/health-check')
def health_check():
    return jsonify({"status": "ok"})

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send-invoices', methods=['POST'])
def send_invoices():
    try:
        data = request.json
        test_email = data.get('email')
        if not test_email:
            return jsonify({'error': 'Email is required'}), 400
            
        output = process_invoices(test_email)
        return jsonify({'message': 'Invoices sent successfully', 
                       'output': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Change this to handle both local and Vercel environments
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)