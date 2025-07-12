from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # Changed default port from 5000 to 5001
    app.run(debug=True, host='0.0.0.0', port=port)