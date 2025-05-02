import os
import cv2
import numpy as np
from flask import Flask, request, send_from_directory, render_template_string, url_for, redirect
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
h1 {
  color: #333;
  margin-bottom: 20px;
  font-size: 1.8rem;
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
.upload-icon {
  font-size: 36px;
  color: #4285f4;
  margin-bottom: 8px;
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
.button.download:hover {
  background: #2d9249;
}
.slider-container {
  margin: 15px 0;
  text-align: left;
}
.slider-container label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  color: #555;
}
.slider {
  width: 100%;
  height: 5px;
  border-radius: 5px;
  -webkit-appearance: none;
  background: #ddd;
  outline: none;
}
.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 15px;
  height: 15px;
  border-radius: 50%;
  background: #4285f4;
  cursor: pointer;
}
.image-container {
  margin-top: 20px;
}
.image-wrapper {
  display: flex;
  justify-content: space-around;
  width: 100%;
  margin-bottom: 15px;
  flex-wrap: wrap;
}
.image-box {
  margin: 8px;
  text-align: center;
}
.image-box h3 {
  margin-bottom: 8px;
  color: #555;
}
img {
  max-width: 300px;
  max-height: 300px;
  border-radius: 4px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.back-link {
  display: block;
  margin-top: 15px;
  color: #4285f4;
  text-decoration: none;
  font-weight: 600;
}
.action-buttons {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 15px;
  flex-wrap: wrap;
}
.checkbox-container {
  display: flex;
  align-items: center;
  margin: 10px 0;
}
.checkbox-container input[type="checkbox"] {
  width: 16px;
  height: 16px;
  margin-right: 8px;
  cursor: pointer;
}
.checkbox-container label {
  font-weight: 600;
  color: #555;
  cursor: pointer;
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
    <h1>🔍 Professional Image Segmentation</h1>
    <form id="upload-form" action="/" method="POST" enctype="multipart/form-data">
      <div class="upload-area" id="drop-area" onclick="document.getElementById('file-input').click()">
        <div class="upload-icon">📁</div>
        <p>Click to select or drag and drop an image</p>
      </div>
      <input type="file" id="file-input" name="image" accept="image/*" required>
      <div class="control-panel">
        <div class="select-container">
          <label for="algorithm">Segmentation Algorithm:</label>
          <select id="algorithm" name="algorithm">
            <option value="kmeans">K-Means Clustering</option>
            <option value="threshold">Simple Thresholding</option>
            <option value="canny">Edge Detection</option>
            <option value="simple">Color Quantization</option>
          </select>
        </div>
        <div class="slider-container">
          <label for="segments">Number of Segments: <span id="segments-value">5</span></label>
          <input type="range" id="segments" name="segments" class="slider" min="2" max="10" value="5">
        </div>
        <div class="checkbox-container">
          <input type="checkbox" id="colorful" name="colorful" value="yes">
          <label for="colorful">Use Colorful Segments</label>
        </div>
        <button type="submit" class="button">Upload & Segment</button>
      </div>
    </form>
  </div>
  <script>
    const segmentsSlider = document.getElementById('segments');
    const segmentsValue = document.getElementById('segments-value');
    segmentsSlider.addEventListener('input', function() {
      segmentsValue.textContent = this.value;
    });
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
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
        
        <hr>

        <div class="image-container">
            <h3>🖼️ Side by Side

# ========== IMAGE PROCESSING ==========
def segment_image(input_path, output_path, algorithm='kmeans', segments=5, colorful=False):
    """
    Apply lightweight image segmentation with the specified algorithm
    
    Parameters:
    - input_path: Path to the input image
    - output_path: Path to save the processed image
    - algorithm: Segmentation algorithm ('kmeans', 'threshold', 'canny', 'simple')
    - segments: Number of segments/clusters for K-means
    - colorful: Whether to use random colors for segments
    """
    try:
        # Read the image
        image = cv2.imread(input_path)
        
        if image is None:
            raise ValueError(f"Failed to load image from {input_path}")
        
        # Optimize for performance: Resize large images
        max_dimension = 800
        height, width = image.shape[:2]
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Convert to RGB for processing (OpenCV loads as BGR)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Prepare result image
        result = None
        
        # Apply selected segmentation algorithm
        if algorithm == 'kmeans':
            # Performance optimization: Reduce color depth to speed up clustering
            image_small = cv2.resize(image_rgb, (image_rgb.shape[1]//2, image_rgb.shape[0]//2), interpolation=cv2.INTER_AREA)
            
            # Further reduce complexity by quantizing colors
            Z = image_small.reshape((-1, 3))
            Z = np.float32(Z)
            
            # Define criteria and apply K-means with fewer iterations
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(Z, segments, None, criteria, 1, cv2.KMEANS_PP_CENTERS)
            
            # Convert back to 8-bit values
            centers = np.uint8(centers)
            
            # Map labels to colors
            res = centers[labels.flatten()]
            
            # Reshape back and resize to original dimensions
            result_small = res.reshape(image_small.shape)
            result = cv2.resize(result_small, (image_rgb.shape[1], image_rgb.shape[0]), interpolation=cv2.INTER_NEAREST)
            
            # Simple colorful option
            if colorful:
                # Create simplified colormap
                colormap = np.zeros((segments, 3), dtype=np.uint8)
                for i in range(segments):
                    colormap[i] = [
                        (i * 255 // segments),
                        (255 - i * 255 // segments),
                        ((i * 140) % 255)
                    ]
                
                # Apply colormap (simplified approach)
                for i in range(segments):
                    result[np.all(result == centers[i], axis=2)] = colormap[i]
            
        elif algorithm == 'threshold':
            # Convert to grayscale and blur slightly to reduce noise
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply simple thresholding
            _, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)
            
            # Create basic result
            if colorful:
                # Create a simple 2-color result (blue background, yellow foreground)
                result = np.zeros_like(image_rgb)
                result[binary == 255] = [255, 255, 0]  # Yellow for foreground
                result[binary == 0] = [0, 0, 255]      # Blue for background
            else:
                # Just use the binary result
                result = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
        
        elif algorithm == 'canny':
            # Simple edge detection based segmentation
            # Convert to grayscale
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply Canny edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Dilate edges to make them more visible
            kernel = np.ones((3, 3), np.uint8)
            dilated_edges = cv2.dilate(edges, kernel, iterations=1)
            
            if colorful:
                # Create colorful visualization
                result = image_rgb.copy()
                # Overlay edges in bright green
                result[dilated_edges > 0] = [0, 255, 0]
            else:
                # Invert edges for better visibility
                inverted_edges = cv2.bitwise_not(dilated_edges)
                result = cv2.cvtColor(inverted_edges, cv2.COLOR_GRAY2RGB)
        
        else:  # 'simple' as fallback
            # Most basic segmentation: just quantize colors
            # This is very efficient and still gives segmentation-like results
            
            # Reduce colors with a simple method
            div = 32
            result = image_rgb // div * div + div // 2
            
            if colorful:
                # Apply a simple color shift
                r, g, b = cv2.split(result)
                result = cv2.merge([b, r, g])  # BGR to RBG color shift for a funky look
        
        # Convert result back to BGR for OpenCV
        if result is not None:
            result = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
        else:
            # Fallback to original image if processing failed
            result = image
        
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
            segments = int(request.form.get('segments', 5))
            colorful = request.form.get('colorful') == 'yes'
            
            # Process the image
            segment_image(input_path, output_path, algorithm, segments, colorful)
            
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
    app.run(debug=True)
