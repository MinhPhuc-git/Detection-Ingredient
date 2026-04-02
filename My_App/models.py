from django.db import models
import csv
from random import randint

import os
from dotenv import load_dotenv
from roboflow import Roboflow

load_dotenv()

class RoboFlowService:
    def __init__(self):
        self.api_key = os.getenv("ROBOFLOW_API_KEY")
        
        if not self.api_key:
            raise ValueError("Không tìm thấy API Key trong file .env!")
            
        self.rf = Roboflow(api_key=self.api_key)
        self.project = self.rf.workspace("lmp").project("ingredient-zrsop")
        self.model = self.project.version(2).model
    def predict_image(self, image_path):
        try:
            result = self.model.predict(image_path, confidence=60).json()
            names = []
            for prediction in result.get('predictions', []):
                names.append(prediction['class'].capitalize())
            return names
        except Exception as e:
            print(f"Error calling Roboflow API: {e}")
            return []
class Recipe:
    def __init__(self, ma, name_recipe, kind, ingredient, spice, difficulty, minute, name_img):
        self.id = ma
        self.tenMonAn = name_recipe
        self.loaiMonAn = kind
        self.thanhPhan= [x.strip().capitalize() for x in ingredient.split(",")]
        self.giaVi = spice.split(",")
        self.doKho = difficulty
        self.thoiGian = int(minute)
        self.tenAnh = name_img
        
class RecipeManager:
    def __init__(self,path_csv):
        self.dsMonAn = []
        self.csv_path = path_csv
        
    def load_data(self):
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                monAn = Recipe(
                    row['STT'],row['Tên Món Ăn'],row['Loại Món'],
                    row['Nguyên Liệu Chính'], row['Gia vị & Nguyên liệu tăng hương vị'],
                    row['Độ Khó'], row['Thời Gian (Phút)'], row['Hình ảnh'],
                    )
                self.dsMonAn.append(monAn)
        return self.dsMonAn
        
    def random_Recipe(self):
        return self.dsMonAn[randint(0,len(self.dsMonAn) - 1)]
    
    def getRecipe_AI(self,aI_labels):
        ds_goi_Y = {}
        for i in self.dsMonAn:
            count = 0
            for j in aI_labels:
                if j in i.thanhPhan:
                    count += 1
            if count > 0:
                phanTram = (count / len(i.thanhPhan)) * 100
                ds_goi_Y[i] = round(phanTram, 2)
        sorted_item = sorted(ds_goi_Y.items(), key=lambda item:item[1], reverse=True) 
        return [item[0] for item in sorted_item]
                    
            
            
        