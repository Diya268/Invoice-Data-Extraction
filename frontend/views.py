import os, json, cv2, numpy as np, pytesseract, pandas as pd
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from ultralytics import YOLO
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

# Add this line to tell where Tesseract is installed:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Load your trained YOLOv8 model only once
MODEL_PATH = os.path.join("yolov8model", "weights", "best.pt")
model = YOLO(MODEL_PATH)

# Class labels dictionary
class_names = {
    0: 'BA', 1: 'BAID', 2: 'INV', 3: 'INV_DATE', 4: 'INV_DATE_ID',
    5: 'INV_ID', 6: 'ORD_DATE', 7: 'ORD_DATE_ID', 8: 'SA', 9: 'SAID',
    10: 'SLR', 11: 'SLR_ID', 12: 'TOTAL', 13: 'TOTAL_ID', 14: 'CN'
}


def extract_invoice_data(file_path):
    try:
        img = cv2.imread(file_path)
        if img is None:
            return {"error": "Failed to load image."}

        results = model.predict(source=img, device='cpu')
        if not results or not results[0].boxes:
            return {"error": "No fields detected."}

        boxes = results[0].boxes.data.cpu().numpy()
        data = {}
        for b in boxes:
            x1,y1,x2,y2,conf,cls = map(int, b[:6])
            crop = img[y1:y2, x1:x2]
            if crop.size == 0: continue
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            txt = pytesseract.image_to_string(gray, config='--psm 6').strip()
            label = class_names.get(cls, f"Field_{cls}")
            data[label] = txt

        return data or {"error": "No text extracted."}
    except Exception as e:
        return {"error": f"Extraction failed: {e}"}

@login_required(login_url='user-login')
def main_page(request):
    ctx = {}
    if request.method == 'POST':
        fs = FileSystemStorage()
        f = request.FILES.get('invoice_file')
        if not f:
            ctx['error'] = "No file uploaded."
            return render(request, 'frontend/main_page.html', ctx)

        fname = fs.save(f.name, f)
        fpath = fs.path(fname)
        # run extraction
        extracted = extract_invoice_data(fpath)
        ctx['extracted_json'] = json.dumps(extracted, indent=4)
        ctx['uploaded_file'] = fs.url(fname)

        # if success, write Excel into MEDIA_ROOT and expose link
        if 'error' not in extracted:
            df = pd.DataFrame([extracted])
            out_name = 'Extracted_Invoice_Data.xlsx'
            out_path = os.path.join(settings.MEDIA_ROOT, out_name)
            df.to_excel(out_path, index=False)
            ctx['excel_file_url'] = settings.MEDIA_URL + out_name

    return render(request, 'frontend/main_page.html', ctx)

def user_login(request):
    """
    User login view.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome, {username}!")
                return redirect('main-page')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'frontend/login.html', {'form': form})

def register_user(request):
    """
    User registration view.
    """
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful! Please log in.")
            return redirect('user-login')
        else:
            messages.error(request, "Registration failed. Please correct the errors.")
    else:
        form = UserCreationForm()
    return render(request, 'frontend/register.html', {'form': form})

def user_profile(request):
    """
    User profile view.
    If the user is not authenticated, redirect to login.
    Otherwise, display the user's basic information.
    """
    if not request.user.is_authenticated:
        return redirect('user-login')
    
    user_info = {
        "username": request.user.username,
        "email": request.user.email,
    }
    return render(request, 'frontend/profile.html', {'user_info': user_info})


def user_logout(request):
    logout(request)
    return redirect('user-login')