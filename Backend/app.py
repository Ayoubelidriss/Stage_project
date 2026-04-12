from flask import Flask, jsonify
from donut.donut_extractor import DonutExtractor
from pipeline.data_processor import DataProcessor

app = Flask(__name__)

@app.route('/donuts', methods=['GET'])
def get_donuts():
    try:
        extractor = DonutExtractor('donut/donut_config.json', 'donut/donut_data.csv')
        donuts = extractor.extract_donuts()
        
        # Process the donut data
        processor = DataProcessor('donut/donut_data.csv', 'data/processed_donuts.csv')
        processor.process_data()
        
        return jsonify(donuts)
    except (FileNotFoundError, ValueError) as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
