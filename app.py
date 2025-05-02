import os
import cv2
import numpy as np
from flask import Flask, request, send_from_directory, render_template_string, redirect
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# ========== CSS ==========
CSS_STYLE = """
body {
  font-family: 'Arial', sans-serif;
  background: #f0f2f5;
  margin: 0;
  padding: 20px;
  min-height: 100vh;
}
.container {
  background: white;
  width: 95%;
  max-width: 800px;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  text-align: center;
  margin: 0 auto;
}
h1, h3 {
  color: #333;
  margin-bottom: 20px;
}
.upload-area {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 15px;
  cursor: pointer;
}
.upload-area:hover {
  border-color: #4285f4;
  background-color: #f8f9fa;
}
input[type="file"] {
  display: none;
}
.control-panel {
  margin: 15px 0;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}
.button {
  padding: 8px 16px;
  background: #4285f4;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  text-decoration: none;
  display: inline-block;
  margin: 8px 5px;
}
.button:hover {
  background: #3367d6;
}
.button.download {
  background: #34a853;
}
.select-container {
  margin: 10px 0;
  text-align: left;
}
.select-container label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  color: #555;
}
.select-container select {
  width: 100%;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #ddd;
  background-color: white;
}
.image-container {
  margin-top: 20px;
}
.image-wrapper {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  margin-bottom: 15px;
}
.image-box {
  margin: 8px;
  text-align: center;
}
img {
  max-width: 300px;
  max-height: 300px;
  border-radius: 4px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
hr {
  margin: 20px 0; 
  border: 0; 
  border-top: 1px solid #eee;
}
@media (max-width: 600px) {
  .container {
    padding: 15px;
  }
  img {
    max-width: 100%;
    height: auto;
  }
  .image-wrapper {
    flex-direction: column;
    align-items: center;
  }
}
"""

# ========== INDEX HTML ==========
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Image Segmentation</title>
  <style>{{ css }}</style>
</head>
<body>
  <div class="container">
    <h1>🔍 Simple Image Segmentation</h1>
    <form id="upload-form" action="/" method="POST" enctype="multipart/form-data">
      <div class="upload-area" id="drop-area" onclick="document.getElementById('file-input').click()">
        <div style="font-size: 36px; color: #4285f4; margin-bottom: 8px;">📁</div>
        <p>Click to select or drag and drop an image</p>
      </div>
      <input type="file" id="file-input" name="image" accept="image/*" required>
      <div class="control-panel">
        <div class="select-container">
          <label for="algorithm">Segmentation Algorithm:</label>
          <select id="algorithm" name="algorithm">
            <option value="kmeans">K-Means (Simple)</option>
            <option value="quantize">Color Quantization</option>
            <option value="threshold">Basic Thresholding</option>
            <option value="cartoon">Cartoon Effect</option>
          </select>
        </div>
        <div style="margin: 15px 0; text-align: left;">
          <label for="intensity" style="display: block; margin-bottom: 5px; font-weight: 600; color: #555;">
            Effect Intensity: <span id="intensity-value">5</span>
          </label>
          <input type="range" id="intensity" name="intensity" min="1" max="10" value="5" 
                 style="width: 100%; height: 5px; border-radius: 5px; -webkit-appearance: none; background: #ddd; outline: none;">
        </div>
        <button type="submit" class="button">Upload & Process</button>
      </div>
    </form>
  </div>
  
  <script>
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const intensitySlider = document.getElementById('intensity');
    const intensityValue = document.getElementById('intensity-value');
    
    // Update intensity value display when slider is moved
    intensitySlider.addEventListener('input', function() {
      intensityValue.textContent = this.value;
    });
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
      dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
      dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
      dropArea.style.borderColor = '#4285f4';
      dropArea.style.backgroundColor = '#f0f7ff';
    }
    
    function unhighlight() {
      dropArea.style.borderColor = '#ccc';
      dropArea.style.backgroundColor = 'transparent';
    }
    
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length) {
        fileInput.files = files;
      }
    }
  </script>
</body>
</html>
"""

# ========== RESULT HTML ==========
RESULT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Segmentation Result</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{{ css }}</style>
</head>
<body>
    <div class="container">
        <h1>✨ Segmentation Result</h1>
        
        <div class="image-container">
            <div class="image-wrapper">
                <div class="image-box">
                    <h3>Original</h3>
                    <img src="{{ url_for('uploaded_file', filename=filename) }}" alt="Original">
                </div>
                <div class="image-box">
                    <h3>Processed</h3>
                    <img src="{{ url_for('processed_file', filename=filename) }}" alt="Processed">
                </div>
            </div>
        </div>
        
        <div class="action-buttons">
            <a href="{{ url_for('download_file', filename=filename) }}" class="button download">Download Processed Image</a>
            <a href="/" class="button">Process Another Image</a>
        </div>
    </div>
</body>
</html>
"""

# ========== SIMPLIFIED IMAGE PROCESSING ==========
def process_image(input_path, output_path, algorithm='kmeans', intensity=5):
    """
    Apply lightweight image processing with the specified algorithm
    
    Parameters:
    - input_path: Path to the input image
    - output_path: Path to save the processed image
    - algorithm: Processing algorithm ('kmeans', 'quantize', 'threshold', 'cartoon')
    - intensity: Effect intensity (1-10), higher values create stronger effects
    """
    try:
        # Read the image
        image = cv2.imread(input_path)
        
        if image is None:
            raise ValueError(f"Failed to load image from {input_path}")
        
        # Optimize for performance: Resize large images
        max_dimension = 600  # Reduced from 800 for better performance
        height, width = image.shape[:2]
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Apply selected algorithm with intensity control
        if algorithm == 'kmeans':
            # Calculate number of clusters based on intensity (2-8)
            num_clusters = max(2, min(8, 1 + intensity))
            
            # Very simplified K-means with variable clusters based on intensity
            pixels = image.reshape((-1, 3))
            pixels = np.float32(pixels)
            
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 5, 1.0)
            _, labels, centers = cv2.kmeans(pixels, num_clusters, None, criteria, 1, cv2.KMEANS_RANDOM_CENTERS)
            
            centers = np.uint8(centers)
            result = centers[labels.flatten()]
            result = result.reshape(image.shape)
            
        elif algorithm == 'quantize':
            # Color quantization with variable reduction based on intensity
            # Higher intensity = more aggressive quantization
            divisor = max(8, 128 - intensity * 10)  # Range from 128 (mild) to 8 (strong)
            result = (image // divisor) * divisor
            
        elif algorithm == 'threshold':
            # Thresholding with variable threshold based on intensity
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Adjust threshold value based on intensity
            threshold_value = 100 + (intensity * 10)  # Range from 110 to 200
            _, result = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
            result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
            
        elif algorithm == 'cartoon':
            # Simplified cartoon effect with intensity control
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 5)
            
            # Adjust block size based on intensity (odd numbers only)
            block_size = 3 + (2 * intensity)  # 5, 7, 9, 11, etc.
            if block_size % 2 == 0:
                block_size += 1
                
            c_value = 5 + intensity  # Threshold constant increases with intensity
            
            edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                         cv2.THRESH_BINARY, block_size, c_value)
            
            # Reduce color palette, intensity controls the level of reduction
            divisor = max(8, 40 - intensity * 3)  # More colors at low intensity, fewer at high
            color = (image // divisor) * divisor
            
            # Combine edge mask with color image
            result = cv2.bitwise_and(color, color, mask=edges)
        
        else:
            # Fallback to simple color reduction
            result = (image // 32) * 32
        
        # Save the processed image
        cv2.imwrite(output_path, result)
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        # If processing fails, copy the original to the output
        if os.path.exists(input_path):
            import shutil
            shutil.copy(input_path, output_path)

# ========== ROUTES ==========
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if image file was uploaded
        if 'image' not in request.files:
            return redirect(request.url)
        
        file = request.files['image']
        
        # If user doesn't select a file, browser submits an empty file
        if file.filename == '':
            return redirect(request.url)
        
        # Process the image if it exists
        if file:
            # Secure the filename to prevent directory traversal attacks
            filename = secure_filename(file.filename)
            
            # Define file paths
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
            
            # Save the uploaded file
            file.save(input_path)
            
            # Get image processing parameters
            algorithm = request.form.get('algorithm', 'kmeans')
            intensity = int(request.form.get('intensity', 5))
            
            # Process the image
            process_image(input_path, output_path, algorithm, intensity)
            
            # Render the result page
            return render_template_string(RESULT_HTML, filename=filename, css=CSS_STYLE)
    
    # Render the index page for GET requests
    return render_template_string(INDEX_HTML, css=CSS_STYLE)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve original uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/processed/<filename>')
def processed_file(filename):
    """Serve processed files"""
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

@app.route('/download/<filename>')
def download_file(filename):
    """Download processed files as attachments"""
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    # Configure for Render deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
