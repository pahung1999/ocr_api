from matplotlib.transforms import Bbox
import numpy as np
from doctr.io import DocumentFile
from doctr.models import detection_predictor
from PIL import Image
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg



#Sắp xếp box theo thứ tự trái -> phải, trên -> dưới
# g=arrange_bbox(df["img_bboxes"][i])
# rows=arrange_row(g=g)
def arrange_bbox(bboxes, type="XXYY"):
    n = len(bboxes)
    if type == "XXYY": #x1,x2,y1,y2
        xcentres = [(b[0] + b[1]) // 2 for b in bboxes]
        ycentres = [(b[2] + b[3]) // 2 for b in bboxes]
        heights = [abs(b[2] - b[3]) for b in bboxes]
        width = [abs(b[1] - b[0]) for b in bboxes]
    elif type == "XYXY": #x1,y1,x2,y2
        xcentres = [(b[0] + b[2]) // 2 for b in bboxes]
        ycentres = [(b[1] + b[3]) // 2 for b in bboxes]
        heights = [abs(b[1] - b[3]) for b in bboxes]
        width = [abs(b[2] - b[0]) for b in bboxes]

    def is_top_to(i, j):
        result = (ycentres[j] - ycentres[i]) > ((heights[i] + heights[j]) / 3)
        return result

    def is_left_to(i, j):
        return (xcentres[i] - xcentres[j]) > ((width[i] + width[j]) / 3)

    # <L-R><T-B>
    # +1: Left/Top
    # -1: Right/Bottom
    g = np.zeros((n, n), dtype='int')
    for i in range(n):
        for j in range(n):
            if is_left_to(i, j):
                g[i, j] += 10
            if is_left_to(j, i):
                g[i, j] -= 10
            if is_top_to(i, j):
                g[i, j] += 1
            if is_top_to(j, i):
                g[i, j] -= 1
    return g


def arrange_row(bboxes=None, g=None, i=None, visited=None):
    if visited is not None and i in visited:
        return []
    if g is None:
        g = arrange_bbox(bboxes)
    if i is None:
        visited = []
        rows = []
        for i in range(g.shape[0]):
            if i not in visited:
                indices = arrange_row(g=g, i=i, visited=visited)
                visited.extend(indices)
                rows.append(indices)
        return rows
    else:
        indices = [j for j in range(g.shape[0]) if j not in visited]
        indices = [j for j in indices if abs(g[i, j]) == 10 or i == j]
        indices = np.array(indices)
        g_ = g[np.ix_(indices, indices)]
        order = np.argsort(np.sum(g_, axis=1))
        indices = indices[order].tolist()
        indices = [int(i) for i in indices]
        return indices

def split_row(rows,bboxes,type="XYXY"):
    if type == "XYXY":
        xcentres = [(b[0] + b[2]) // 2 for b in bboxes]
        x1x2= [ [b[0],b[2]] for b in bboxes]    
    if type == "XXYY":
        xcentres = [(b[0] + b[1]) // 2 for b in bboxes]
        x1x2= [ [b[0],b[1]] for b in bboxes]    
    new_rows=[]

    max_width= 15
    print("max_width: ",max_width)
    for row in rows:
        new_row=[row[0]]
        for i in range(1,len(row)):
            if abs(x1x2[row[i]][0]-x1x2[row[i-1]][1]) > max_width:
                new_rows.append(new_row)
                new_row=[row[i]]
            else:
                new_row.append(row[i])
        new_rows.append(new_row)
    
    print("new_rows: ",new_rows)
    return new_rows

                


#Detect
def get_model_doctr(arch='db_resnet50'):
    model = detection_predictor(arch='db_resnet50', pretrained=True,assume_straight_pages=True)
    return model
def detection_doctr(image,model):
    
    single_img_doc=DocumentFile.from_images(image)
    result = model(single_img_doc)
    
    h,w,c=single_img_doc[0].shape
    bboxes=[]
    for box in result[0]:
        x1=int(box[0]*w)
        y1=int(box[1]*h)
        x2=int(box[2]*w)
        y2=int(box[3]*h)
        bboxes.insert(0,[x1,y1,x2,y2])

    return bboxes, single_img_doc[0],h,w


#Recognition
#input box: x1,y1,x2,y2
def get_model_vietocr():
    config = Cfg.load_config_from_name('vgg_seq2seq')
    # config['weights'] = 'https://drive.google.com/uc?id=13327Y1tz1ohsm5YZMyXVMPIOjoOA0OaA'
    config['weights'] = 'https://drive.google.com/uc?id=1nTKlEog9YFK74kPyX0qLwCWi60_YHHk4'
    config['cnn']['pretrained']=False
    config['device'] = 'cuda:0'
    config['predictor']['beamsearch']=False
    model = Predictor(config)
    return model

def recognition_vietocr(image,bboxes,model):
    raw_text=[]
    # image = np.frombuffer(image, np.uint8)
    # image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    for box in bboxes:
        # print("image.shape: ",image.shape)
        # print("box: ",box)
        img_box=image[box[1]:box[3],box[0]:box[2]]
        # print("img_box.shape: ",img_box.shape)
        img_box=Image.fromarray(img_box)
        text=model.predict(img_box)
        if text==[]:
            raw_text.append("?")
            continue
        raw_text.append(str(text))
    return raw_text