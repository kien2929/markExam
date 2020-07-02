from flask import Flask
import os
import time
from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename
import cv2
import json
from main_process import get_final_result


###########################################


UPLOAD_FOLDER = './uploads'
RESULT_FOLDER = './static/results'

if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

if not os.path.exists(RESULT_FOLDER):
    os.mkdir(RESULT_FOLDER)

os.system("rm -rf {}/*".format(UPLOAD_FOLDER))
os.system("rm -rf {}/*".format(RESULT_FOLDER))

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['newest_filename']  = ''


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
	
@app.route('/')
def upload_form():
	return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part, try again')
            return redirect("/")
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            app.config['newest_filename'] = filename
            return redirect('/result')
        else:
            flash('Allowed file types are  png, jpg, jpeg')
            return redirect(request.url)

@app.route('/result')
def process_image():
    resutl_path = os.path.join(app.config['RESULT_FOLDER'], app.config['newest_filename'])
    
    image = cv2.imread(os.path.join(app.config["UPLOAD_FOLDER"], app.config['newest_filename']))

    start = time.time()
    draw_img, student_answer, exam_answer, answer = get_final_result(image)
 
    results = {}
    results["Student ID"] = student_answer
    results["Exam ID"] = exam_answer

    for i in range(50):
        results[str(i+1)] = answer[str(i+1)][0]

    cv2.imwrite(resutl_path, draw_img)
    return render_template('result.html', img_path = resutl_path, results = results)

if __name__ == "__main__":
    app.run()
