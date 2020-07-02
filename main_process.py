
import numpy as np
import cv2
import imutils
import math

def dis_point(a,b):
    x1, y1 = a
    x2, y2 = b
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

def rotate_img(img, left_mark, right_mark):
    # left_mark: x1, y1
    # right_mark: x2, y2

    p1 = left_mark
    p2 = right_mark

 
    p3 = (p2[0], p1[1])
    dis_p12 = dis_point(p1, p2)
    # dis_p13 = dis_point(p1, p3)
    dis_p23 = dis_point(p2, p3)

    sin_alpha = dis_p23/dis_p12
  
    alpha = math.asin(sin_alpha)*180/math.pi
    if p1[1] > p2[1]:
        alpha = - alpha
  
    rotated = imutils.rotate(img, alpha)

    return rotated
       
def getBoxes(img):
    img_h, img_w, _ = img.shape
    imgray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
    _, thresh = cv2.threshold(imgray, 200, 255, 0) # convert to binary image
    _,contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    boxes = []
    # filter boxes
    for c in contours:
        # get the bounding rect
        x, y, w, h = cv2.boundingRect(c) #
        if w < 10 or h < 10 or w == img_w or h == img_h:
            continue
        # if w*h < 100:
        #     continue
        
        boxes.append([x,y,w,h])
      
    return boxes, thresh
    

def get_mask_score(img, x_center, y_center, mask_size = 30):
    
    xmin, ymin, xmax, ymax = int(x_center - mask_size/2), int(y_center - mask_size/2), int(x_center + mask_size/2) , int(y_center+mask_size/2)
    
    mask = img[ymin:ymax, xmin:xmax]
    mask = mask.reshape(-1)
    return mask.mean()

def get_abcd(img, y_row_center, colum_marks):
    # row_center: (x_center, y_center)
    # return 4 value for the answer at the row
    answer = []
    
    for i in range(4):
        answer_id = -1
        answer_box = None
        mean_min = 999

        for idx, box in enumerate(colum_marks[i*4: (i+1)*4]):
            x, y, w, h = box
            x_center = x + w/2
             
            mean = get_mask_score(img.copy(), x_center, y_row_center)
            
            # print(idx,mean)
            if mean < mean_min:
                answer_id = idx
                answer_box = [ x_center, y_row_center]
                mean_min = mean
    
        if answer_id == 0:
            answer.append(["A", answer_box])
        elif answer_id == 1:
            answer.append(["B", answer_box])
        elif answer_id == 2:
            answer.append(["C", answer_box])
        elif answer_id == 3:
            answer.append(["D", answer_box])
        else:
            answer.append(["Unknow", None])
    return answer
            

def get_answer_list(img, row_marks, colum_marks):
    answer = {}
    for i in range(120):
        answer[str(i+1)] = "-1"
    
    row_marks = sorted(row_marks, key=lambda x: x[1])[11:-1]
    colum_marks = sorted(colum_marks, key=lambda x: x[0])[1:-1]
    init_index = [0,30,60,90]
    for row in row_marks:
        x,y,w,h = row
        y_center = y+h/2
        
        row_answer = get_abcd(img, y_center, colum_marks)
        answer[str(init_index[0]+1)] = row_answer[0]
        answer[str(init_index[1]+1)] = row_answer[1]
        answer[str(init_index[2]+1)] = row_answer[2]
        answer[str(init_index[3]+1)] = row_answer[3]

        init_index[0] += 1
        init_index[1] += 1
        init_index[2] += 1
        init_index[3] += 1

    # for k, v in answer.items():
        
    #     v = answer[k]

    #     x_center, y_center = int(v[1][0]), int(v[1][1])
    #     cv2.rectangle(img, (x_center, y_center), (x_center+20, y_center+20), (0,255,0), 2)
    
    # cv2.imwrite("answer.jpg", img)

    return answer



def get_exam_info(img, x_center, row_marks):
    # row_marks len: 9 (0-9)
    mean_min = 999
    idx_answer = -1
    y_answer = -1
    for idx, row in enumerate(row_marks):
        _,y,_,h = row
        y_center = y + h//2
        mean = get_mask_score(img, x_center, y_center)
        
        if mean < mean_min:
            mean_min = mean
            y_answer = y_center
            idx_answer = idx

    
    return idx_answer, y_answer


def get_student_id_exam_id_score(img, student_id_box, exam_id_box, row_marks):
    # row_marks len: 9 (0-9)
    # get student id

    student_id = {}
    xmin,_,w,_ = student_id_box
    offset = w//6
   
    for i in range(6):
      
        x_center = xmin + offset*(i+0.5)

        idx_answer, y_center = get_exam_info(img, x_center, row_marks)

        student_id[i+1] = [idx_answer, [x_center, y_center]]
        
    
    # get exam id

    exam_id = {}
    xmin,_,w,_ = exam_id_box

    offset = w//3
    
    for i in range(3):
      
        x_center = xmin + offset*(i+0.5)

        idx_answer, y_center = get_exam_info(img, x_center, row_marks)

        exam_id[i+1] = [idx_answer, [x_center, y_center]]

    
    return student_id, exam_id
   

def find_student_id_exam_id(boxes, colum_marks, row_marks):
    # print(colum_marks)
    # print(row_marks)
    x_mark = colum_marks[-5][0]
    y_mask = row_marks[11][1]
    
    # for box in  [colum_marks[-5], row_marks[11]]:
    #     x,y,w,h = box
    #     cv2.rectangle(img, (x,y), (x+w, y+h), (0,0,255), 2)

    # cv2.imwrite("out.jpg", img)
    # assert False
    
    candiante_boxes = []
    for box in boxes:
        x,y,w,h = box
        if x < x_mark and x + w > x_mark and y+h < y_mask:
            candiante_boxes.append([box, w*h])
            # cv2.rectangle(img, (x,y), (x+w, y+h), (0,0,255), 2)

    student_id_box = sorted(candiante_boxes, key=lambda x: x[1])[-1][0]

    x_mark = colum_marks[-3][0]
    candiante_boxes = []
    for box in boxes:
        x,y,w,h = box
        if x > x_mark and y+h < y_mask:
            candiante_boxes.append([box, w*h])
            # cv2.rectangle(img, (x,y), (x+w, y+h), (0,0,255), 2)
    
    exam_id_box = sorted(candiante_boxes, key=lambda x: x[1])[-1][0]

    return student_id_box, exam_id_box  


def get_final_result(image):
    img = image.copy()
    # rotate_img(img)
    
    boxes_ro, _ = getBoxes(img.copy())

    colum_marks = sorted(boxes_ro, key=lambda x: x[1])[-18:][::-1]
    colum_marks = sorted(colum_marks, key=lambda x: x[0])
    # row_marks = sorted(boxes, key=lambda x: x[0])[-42:][::-1]

    img = rotate_img(img.copy(), (colum_marks[0][0],colum_marks[0][1]), (colum_marks[-1][0],colum_marks[-1][1]))
    #######################################
    boxes, thres_img = getBoxes(img.copy())

    colum_marks = sorted(boxes, key=lambda x: x[1])[-18:][::-1]
    row_marks = sorted(boxes, key=lambda x: x[0])[-42:][::-1]

    colum_marks = sorted(colum_marks, key=lambda x: x[0])
    row_marks = sorted(row_marks, key=lambda x: x[1])

    student_id_box, exam_id_box = find_student_id_exam_id(boxes, colum_marks, row_marks)
 
    
    answer = get_answer_list(thres_img.copy(), row_marks, colum_marks)

    student, exam=  get_student_id_exam_id_score(thres_img.copy(), student_id_box, exam_id_box, row_marks[1:11])

    for k, v in answer.items():
        if int(k) > 50:
            continue
        v = answer[k]

        x_center, y_center = int(v[1][0]), int(v[1][1])
        cv2.rectangle(img, (x_center-10, y_center-10), (x_center+10, y_center+10), (0,255,0), 2)
    
    student_answer = ""
    for k, v in student.items():
        v = student[k]
        student_answer += str(v[0])
        x_center, y_center = int(v[1][0]), int(v[1][1])
        cv2.rectangle(img, (x_center-10, y_center-10), (x_center+10, y_center+10), (255,0,0), 2)

    exam_answer = ""
    for k, v in exam.items():
        v = exam[k]
        exam_answer += str(v[0])
        x_center, y_center = int(v[1][0]), int(v[1][1])
        cv2.rectangle(img, (x_center-10, y_center-10), (x_center+10, y_center+10), (0,0,255), 2)


    return img, student_answer, exam_answer, answer

