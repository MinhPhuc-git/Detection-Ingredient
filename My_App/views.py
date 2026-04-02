from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import loader
from ultralytics import YOLO
from collections import Counter
from PIL import Image
from My_App import models
import csv
from django.core.paginator import Paginator
import os
model_path = r"C:\Users\ASUS RogStrix\OneDrive\Desktop\ML-Recognize_Object-AI\model\best_Ver2.pt"
csv_path = r"C:\Users\ASUS RogStrix\OneDrive\Desktop\ML-Recognize_Object-AI\model\Dishes.csv"
# model = YOLO(model_path)
view_recipe = models.RecipeManager(csv_path)
view_recipe.load_data()
translate_dict = {
    'Beef': 'Thịt bò',
    'Bell pepper': 'Ớt chuông',
    'Bok choy': 'Cải thìa',
    'Broccoli': 'Bông cải xanh',
    'Cabbage': 'Bắp cải',
    'Carrot': 'Cà rốt',
    'Crab': 'Cua',
    'Cucumber': 'Dưa chuột',
    'Egg': 'Trứng', 
    'Fish': 'Cá',
    'Garlic': 'Tỏi',
    'Ginger': 'Gừng',
    'Green bean': 'Đậu cô ve',
    'Onion': 'Hành tây',
    'Potato': 'Khoai tây',
    'Pumpkin': 'Bí đỏ',
    'Rice': 'Cơm',
    'Shrimp': 'Tôm',
    'Squid': 'Mực',
    'Tofu': 'Đậu phụ',
    'Tomato': 'Cà chua',
    'Winter_melon': 'Bí đao',
    'Winter melon': 'Bí đao'
}

def index_view(request):
    return render(request,"index.html")

def login_view(request):
    return render(request,"login.html")

def recipe_view(request):
    return render(request,"recipe.html")

roboflow_service = models.RoboFlowService()

def predict_model(request):
    list_recipe = view_recipe.dsMonAn
    count_ingredient_vn = {} 
    suggest_recipe = []
    first = second = third = None
    
    if request.method == "GET":
        first = view_recipe.random_Recipe()
        second = view_recipe.random_Recipe()
        third = view_recipe.random_Recipe()
        return render(request, 'recipe.html', {
            "suggest_recipe": [],
            "recipe_Number": len(view_recipe.dsMonAn),
            "first": first, "second": second, "third": third,
        })
        
    if request.method == "POST" and request.FILES.get('image_upload'):
        try:
            file = request.FILES.get('image_upload')
            img = Image.open(file)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            temp_path = f"temp_{file.name.split('.')[0]}.jpg"
            img.save(temp_path, "JPEG")

            raw_ingredients = roboflow_service.predict_image(temp_path)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if not raw_ingredients:
                suggest_recipe = list_recipe
                first = view_recipe.random_Recipe()
                second = view_recipe.random_Recipe()
                third = view_recipe.random_Recipe()
            else:
                translated_ingredients = [translate_dict.get(name.strip(), name.strip()) for name in raw_ingredients]
                
                count_ingredient_vn = Counter(translated_ingredients)

                unique_raw_ingredients = list(Counter(raw_ingredients).keys())
                suggest_recipe = view_recipe.getRecipe_AI(unique_raw_ingredients)
                
                if len(suggest_recipe) >= 1: first = suggest_recipe[0]
                if len(suggest_recipe) >= 2: second = suggest_recipe[1]
                if len(suggest_recipe) >= 3: third = suggest_recipe[2]
            
        except Exception as e:
            print(f"Error during prediction: {e}")
            return redirect('predict_model')

        return render(request, 'recipe.html', {
            "count_ingredient": dict(count_ingredient_vn), 
            "numberOf_ingredient": len(count_ingredient_vn),
            "suggest_recipe": suggest_recipe,
            "recipe_Number": len(suggest_recipe),
            "first": first, 
            "second": second, 
            "third": third,
        })
        
def food_view(request):

    list_Recipe = view_recipe.dsMonAn        
    
    list_Recipe = translate_recipe_data(list_Recipe)
    
    get_Id = request.GET.get('id')    
    main_recipe = next(filter(lambda r: r.id == str(get_Id), list_Recipe ),None)
    
    if not main_recipe:
        main_recipe = list_Recipe[0]
         
    paginator = Paginator(list_Recipe,8)
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    return render(request, 'food.html',{
        "page_obj": page_obj,
        "main_recipe" : main_recipe,
        "current_id": get_Id
    })
    
def translate_recipe_data(recipe_list):
    for recipe in recipe_list:
        if hasattr(recipe, 'thanhPhan'):
            recipe.thanhPhan = [translate_dict.get(item, item) for item in recipe.thanhPhan]
            
    return recipe_list