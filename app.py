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
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  margin: 0;
  padding: 0;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}
.container {
  background: white;
  width: 90%;
  max-width: 1000px;
  padding: 40px;
  border-radius: 15px;
  box-shadow: 0 15px 30px rgba(0,0,0,0.1);
  text-align: center;
}
h1 {
  color: #333;
  margin-bottom: 30px;
  font-weight: 700;
  font-size: 2.2rem;
}
.upload-area {
  border: 2px dashed #ccc;
  border-radius: 10px;
  padding: 30px;
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.upload-area:hover {
  border-color: #4285f4;
  background-color: #f8f9fa;
}
.upload-icon {
  font-size: 48px;
  color: #4285f4;
  margin-bottom: 10px;
}
input[type="file"] {
  display: none;
}
.control-panel {
  margin: 20px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
}
.button {
  padding: 12px 24px;
  background: #4285f4;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-block;
  margin: 10px 5px;
}
.button:hover {
  background: #3367d6;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}
.button.download {
  background: #34a853;
}
.button.download:hover {
  background: #2d9249;
}
.slider-container {
  margin: 20px 0;
  text-align: left;
}
.slider-container label {
  display: block;
  margin-bottom: 8px;
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
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #4285f4;
  cursor: pointer;
}
.image-container {
  margin-top: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.image-wrapper {
  display: flex;
  justify-content: space-around;
  width: 100%;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.image-box {
  margin: 10px;
  text-align: center;
}
.image-box h3 {
  margin-bottom: 10px;
  color: #555;
}
img {
  max-width: 350px;
  max-height: 350px;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
  transition: transform 0.3s ease;
}
img:hover {
  transform: scale(1.03);
}
.back-link {
  display: block;
  margin-top: 20px;
  color: #4285f4;
  text-decoration: none;
  font-weight: 600;
}
.action-buttons {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-top: 20px;
}
.checkbox-container {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin: 15px 0;
  padding: 5px;
}
.checkbox-container input[type="checkbox"] {
  display: inline-block;
  width: 18px;
  height: 18px;
  margin-right: 10px;
  cursor: pointer;
}
.checkbox-container label {
  font-weight: 600;
  color: #555;
  cursor: pointer;
}
.select-container {
  margin: 15px 0;
  text-align: left;
}
.select-container label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #555;
}
.select-container select {
  width: 100%;
  padding: 10px;
  border-radius: 5px;
  border: 1px solid #ddd;
  background-color: white;
  font-size: 16px;
}
.twentytwenty-container {
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 0 15px rgba(0,0,0,0.1);
}
.twentytwenty-container img {
  width: 100%;
  display: block;
}
hr {
  margin: 40px 0; 
  border: 0; 
  border-top: 1px solid #ccc;
}
.comparison-slider {
  width: 100%;
  max-width: 700px;
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
  margin: 20px auto;
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
            <option value="watershed">Watershed</option>
            <option value="grabcut">GrabCut</option>
            <option value="threshold">Adaptive Thresholding</option>
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
    <style>{{ css }}</style>

    <!-- jQuery + twentytwenty -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twentytwenty/1.0.0/css/twentytwenty.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.event.move/2.0.0/jquery.event.move.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/twentytwenty/1.0.0/js/jquery.twentytwenty.js"></script>
</head>
<body>
    <div class="container">
        <h1>✨ Segmentation Result</h1>
        
        <hr>

        <div class="image-container">
            <h3>🖼️ Side by Side View</h3>
            <div class="image-wrapper">
                <div class="image-box">
                    <h3>Original</h3>
                    <img src="{{ url_for('uploaded_file', filename=filename) }}" alt="Original Image">
                </div>
                <div class="image-box">
                    <h3>Segmented</h3>
                    <img src="{{ url_for('processed_file', filename=filename) }}" alt="Segmented Image">
                </div>
            </div>

            <div class="action-buttons">
                <a href="{{ url_for('download_file', filename=filename) }}" class="button download">⬇️ Download Segmented</a>
                <a href="{{ url_for('index') }}" class="button">⏪ Process Another Image</a>
            </div>
        </div>
    </div>

    <script>
      $(function(){
        $(".twentytwenty-container").twentytwenty({
          default_offset_pct: 0.5
        });
      });
    </script>
</body>
</html>
"""

# ========== IMAGE PROCESSING ==========
def segment_image(input_path, output_path, algorithm='kmeans', segments=5, colorful=False):
    """
    Apply image segmentation with the specified algorithm
    
    Parameters:
    - input_path: Path to the input image
    - output_path: Path to save the processed image
    - algorithm: Segmentation algorithm ('kmeans', 'watershed', 'grabcut', 'threshold')
    - segments: Number of segments/clusters for K-means
    - colorful: Whether to use random colors for segments
    """
    try:
        # Read the image
        image = cv2.imread(input_path)
        
        if image is None:
            raise ValueError(f"Failed to load image from {input_path}")
        
        # Convert to RGB for processing (OpenCV loads as BGR)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Prepare result image
        result = None
        
        # Apply selected segmentation algorithm
        if algorithm == 'kmeans':
            # Reshape image for K-means
            pixel_values = image_rgb.reshape((-1, 3))
            pixel_values = np.float32(pixel_values)
            
            # Define criteria and apply K-means
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
            _, labels, centers = cv2.kmeans(pixel_values, segments, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert back to 8-bit values
            centers = np.uint8(centers)
            
            # Map labels to colors
            segmented_image = centers[labels.flatten()]
            
            # Reshape back to original image dimensions
            result = segmented_image.reshape(image_rgb.shape)
            
            # If colorful option is selected, use random colors for visualization
            if colorful:
                # Create a colormap for visualization
                colormap = np.zeros((segments, 3), dtype=np.uint8)
                for i in range(segments):
                    colormap[i] = np.random.randint(0, 255, 3)
                
                # Create colored segmentation result
                colored_result = np.zeros_like(image_rgb)
                labels_2d = labels.reshape(image_rgb.shape[0], image_rgb.shape[1])
                
                for i in range(segments):
                    colored_result[labels_2d == i] = colormap[i]
                
                result = colored_result
                
        elif algorithm == 'watershed':
            # Convert to grayscale
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            
            # Apply Otsu's thresholding
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Noise removal
            kernel = np.ones((3, 3), np.uint8)
            opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
            
            # Sure background area
            sure_bg = cv2.dilate(opening, kernel, iterations=3)
            
            # Finding sure foreground area
            dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
            _, sure_fg = cv2.threshold(dist_transform, 0.7 * dist_transform.max(), 255, 0)
            
            # Finding unknown region
            sure_fg = np.uint8(sure_fg)
            unknown = cv2.subtract(sure_bg, sure_fg)
            
            # Marker labelling
            _, markers = cv2.connectedComponents(sure_fg)
            
            # Add one to all labels so that background is not 0, but 1
            markers = markers + 1
            
            # Mark the region of unknown with zero
            markers[unknown == 255] = 0
            
            # Apply watershed
            markers = cv2.watershed(image, markers.copy())
            
            # Create visualization
            if colorful:
                # Create random colors
                colors = []
                for i in range(np.max(markers) + 1):
                    colors.append(np.random.randint(0, 255, 3))
                
                # Create colored result
                result = np.zeros_like(image_rgb)
                for i in range(1, np.max(markers) + 1):
                    result[markers == i] = colors[i]
            else:
                # Create grayscale result
                result = np.zeros_like(gray)
                for i in range(1, np.max(markers) + 1):
                    result[markers == i] = 255 * i // np.max(markers)
                result = cv2.cvtColor(result, cv2.COLOR_GRAY2RGB)
            
        elif algorithm == 'grabcut':
            # Create initial mask
            mask = np.zeros(image.shape[:2], np.uint8)
            
            # Set rectangular area for foreground
            rect = (50, 50, image.shape[1]-100, image.shape[0]-100)
            
            # Create temporary arrays for GrabCut
            bgdModel = np.zeros((1, 65), np.float64)
            fgdModel = np.zeros((1, 65), np.float64)
            
            # Apply GrabCut
            cv2.grabCut(image, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
            
            # Modify mask: 0 and 2 for background, 1 and 3 for foreground
            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
            
            # Apply the mask to get foreground
            result = image_rgb * mask2[:, :, np.newaxis]
            
            # Create background in white
            background = np.ones_like(image_rgb) * 255
            result = result + background * (1 - mask2[:, :, np.newaxis])
            
            if colorful:
                # Create colorful foreground
                colored_mask = np.zeros_like(image_rgb)
                colored_mask[mask2 == 1] = np.random.randint(50, 255, 3)
                
                # Blend with original
                blend_ratio = 0.7
                result = (blend_ratio * colored_mask + (1 - blend_ratio) * image_rgb * mask2[:, :, np.newaxis]).astype(np.uint8)
                
                # Add white background
                result = result + background * (1 - mask2[:, :, np.newaxis])
            
        elif algorithm == 'threshold':
            # Convert to grayscale
            gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                          cv2.THRESH_BINARY, 11, 2)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            # Create result image
            if colorful:
                # Create colored contours
                result = np.ones_like(image_rgb) * 255  # White background
                for i, contour in enumerate(contours):
                    # Skip very small contours
                    if cv2.contourArea(contour) < 100:
                        continue
                    # Random color for each contour
                    color = np.random.randint(0, 255, 3).tolist()
                    cv2.drawContours(result, [contour], -1, color, 2)
                    # Fill contour with lighter version of the color
                    mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)
                    cv2.fillPoly(mask, [contour], 255)
                    light_color = [(c + 255) // 2 for c in color]  # Lighter color
                    result[mask == 255] = light_color
            else:
                # Create grayscale result with contours
                result = np.ones_like(image_rgb) * 255  # White background
                cv2.drawContours(result, contours, -1, (0, 0, 0), 1)
        
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
