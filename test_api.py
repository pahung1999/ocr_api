from fastapi import FastAPI, UploadFile, File
from typing import List
from ocr import *
from fastapi.responses import StreamingResponse
import os
import pandas as pd
import uvicorn
app = FastAPI()


out_file_folder="./saved"


@app.post("/uploadfile/doctr_vietocr")
# async def create_upload_file(file: Union[UploadFile, None] = None):
async def upload(file: UploadFile = File(...)):
    
    if not file:
        return {"message": "No upload file sent"}
    else:
        # out_file_path=os.path.join(out_file_folder,file.filename)
        # with open(out_file_path, "wb+") as file_object:
        #     file_object.write(file.file.read())
        # return {"info": f"file '{file.filename}' saved at '{out_file_path}'"}
        all_row={}
        detect_model=get_model_doctr()
        bboxes,image,h,w=detection_doctr(file.file.read(),detect_model)

        recognize_model=get_model_vietocr()
        raw_text=recognition_vietocr(image,bboxes,recognize_model)

        g=arrange_bbox(bboxes)
        rows=arrange_row(g=g)

        new_text=[]
        new_box=[]
        for i in range(len(rows)):
            for j in rows[i]:
                new_text.append(raw_text[j])
                new_box.append(bboxes[j])
        
        return new_text,new_box,h,w
        # for i in range(len(rows)):
        #     x=""
        #     for j in rows[i]:
        #         x=x+" - "+raw_text[j]
        #     all_row[f"{i}"]=x
        # return all_row
        # return StreamingResponse(original_image, media_type="image/jpeg")
        # return {"filename": file.filename}

@app.post("/uploadfolder/doctr_vietocr")
# async def create_upload_files(files: List[UploadFile] = File(...)):
async def create_upload_files(files: List[UploadFile]):

    data=pd.DataFrame(columns=['img_id',"img_texts","img_bboxes"])

    detect_model=get_model_doctr()
    recognize_model=get_model_vietocr()
    img_id=[]
    img_texts=[]
    img_bboxes=[]
    for file in files:
        img_id.append(file.filename)
        bboxes,image=detection_doctr(file.file.read(),detect_model)
        raw_text=recognition_vietocr(image,bboxes,recognize_model)

        g=arrange_bbox(bboxes)
        rows=arrange_row(g=g)

        new_text=[]
        new_box=[]
        for i in range(len(rows)):
            for j in rows[i]:
                new_text.append(raw_text[j])
                new_box.append(bboxes[j])

        img_texts.append(new_text)
        img_bboxes.append(new_box)
            # all_row[f"{i}"]=x
        
        print(f"{file.filename}")

    data['img_id']=img_id
    data['img_texts']=img_texts
    data['img_bboxes']=img_bboxes
    data.to_csv(os.path.join(out_file_folder,"data.csv"),index=False)

    return data
        # return StreamingResponse(original_image, media_type="image/jpeg")
        # return {"filename": file.filename}

if __name__ == "__main__":
    uvicorn.run("test_api:app", host="127.0.0.1", port=8000,  reload=True)