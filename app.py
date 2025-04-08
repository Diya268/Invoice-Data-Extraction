import streamlit as st
import cv2
import numpy as np
import pytesseract
import pandas as pd
import os
from ultralytics import YOLO
from PIL import Image

# Load YOLOv8 Model
model_path = "yolov8n.pt"  # Make sure this file exists
model = YOLO(model_path)

model.info() # Check if the model is loaded correctly

# Configure Tesseract path (For Windows Users)
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Streamlit UI
def main():
    st.title("Invoice Data Extraction System 🧾")
    st.write("Upload an invoice image and extract data automatically.")
    
    uploaded_file = st.file_uploader("Upload Invoice (JPG, PNG, PDF)", type=["jpg", "png", "pdf"])
    

    if uploaded_file is not None:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Uploaded Invoice", use_column_width=True)
        
        if st.button("Extract Data"):  
            extracted_data = process_invoice(image)
            
            if extracted_data:
                st.success("✅ Data Extracted Successfully!")
                df = pd.DataFrame([extracted_data])
                st.dataframe(df)
                
                # Provide Excel Download Option
                excel_file = "Extracted_Invoice_Data.xlsx"
                df.to_excel(excel_file, index=False)
                with open(excel_file, "rb") as file:
                    st.download_button(label="Download Excel", data=file, file_name=excel_file, mime="application/vnd.ms-excel")

# Function to Process Invoice
def process_invoice(image):
    try:
        # Convert PIL image to NumPy array (BGR format for OpenCV)
        image = np.array(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Run YOLOv8 Model to detect invoice fields
        results = model(image)
        
        extracted_data = {}
        
        for result in results:
            for box in result.boxes.data:
                x1, y1, x2, y2, conf, cls = map(int, box[:6])  # Convert values to integers
                cropped_img = image[y1:y2, x1:x2]
                
                # Ensure the cropped image is valid
                if cropped_img.size == 0:
                    continue
                
                text = pytesseract.image_to_string(cropped_img, config='--psm 6').strip()
                extracted_data[f"Field_{cls}"] = text  # Placeholder field names
                
        return extracted_data if extracted_data else {"Error": "No text detected"}
    
    except Exception as e:
        st.error(f"Error: {e}")
        return None

if __name__ == "__main__":
    main()
