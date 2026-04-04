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

# Dictionary mapping remains for UI display if needed, but logic uses English keys
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

ingredient_list = [
    'Beef', 'Bell pepper', 'Bok choy', 'Broccoli', 'Cabbage',
    'Carrot', 'Crab', 'Cucumber', 'Egg', 'Fish',
    'Garlic', 'Ginger', 'Green bean', 'Onion', 'Potato',
    'Pumpkin', 'Rice', 'Shrimp', 'Squid', 'Tofu',
    'Tomato', 'Winter_melon', 'Winter melon'
]

vietnamese_list = [
    'Thịt bò', 'Ớt chuông', 'Cải thìa', 'Bông cải xanh', 'Bắp cải',
    'Cà rốt', 'Cua', 'Dưa chuột', 'Trứng', 'Cá',
    'Tỏi', 'Gừng', 'Đậu cô ve', 'Hành tây', 'Khoai tây',
    'Bí đỏ', 'Cơm', 'Tôm', 'Mực', 'Đậu phụ',
    'Cà chua', 'Bí đao', 'Bí đao'
]

def index_view(request):
    return render(request,"index.html")

def login_view(request):
    return render(request,"login.html")

def recipe_view(request):
    return render(request,"recipe.html")

roboflow_service = models.RoboFlowService()

def predict_model(request):
    list_recipe = view_recipe.dsMonAn
    count_ingredient = {} 
    suggest_recipe = []
    first = second = third = None
    
    # Avoid empty page
    if request.method == "GET":
        action = request.GET.get('action')
        name_ingredient_action = request.GET.get('name')
        ai_ingredients = request.session.get('dict_ingredient', dict())         
        
        if not action: 
            first = view_recipe.random_Recipe()
            second = view_recipe.random_Recipe()
            third = view_recipe.random_Recipe()
            return render(request, 'recipe.html', {
                "suggest_recipe": [],
                "count_ingredient": {translate_dict.get(k, k): v for k, v in ai_ingredients.items()},
                "recipe_Number": len(view_recipe.dsMonAn),
                "first": first, "second": second, "third": third,
                "ingredient_list": ingredient_list

            })
        else:
            # Map ngược từ Tiếng Việt sang Tiếng Anh để xử lý logic xóa/sửa nếu cần
            reverse_translate = {v: k for k, v in translate_dict.items()}
            eng_name = reverse_translate.get(name_ingredient_action, name_ingredient_action)

            if eng_name in ai_ingredients:
                if action == "plus":
                    ai_ingredients[eng_name] += 1
                elif action == "minus":
                    if ai_ingredients[eng_name] == 1:
                        del ai_ingredients[eng_name]
                    else:
                        ai_ingredients[eng_name] -= 1
                else:
                    del ai_ingredients[eng_name]
                    
                request.session['dict_ingredient'] = ai_ingredients
                # Use English keys for AI Label logic
                request.session['ai_label'] = list(ai_ingredients.keys())
                request.session.modified = True

            if not ai_ingredients:
                first = view_recipe.random_Recipe()
                second = view_recipe.random_Recipe()
                third = view_recipe.random_Recipe()
                return render(request, 'recipe.html', {
                    "suggest_recipe": [],
                    "count_ingredient": {},
                    "recipe_Number": len(view_recipe.dsMonAn),
                    "first": first, "second": second, "third": third,
                    "ingredient_list": ingredient_list

                })
            
            # Suggest Recipe based on English labels
            suggest_recipe,full_list_Recipe = view_recipe.getRecipe_AI(list(ai_ingredients.keys()))
            request.session['suggested_ids'] = [str(r.id) for r in suggest_recipe]
            
            first = suggest_recipe[0] if len(suggest_recipe) >= 1 else None
            second = suggest_recipe[1] if len(suggest_recipe) >= 2 else None
            third = suggest_recipe[2] if len(suggest_recipe) >= 3 else None
            
            return render(request, 'recipe.html', {
                "count_ingredient": {translate_dict.get(k, k): v for k, v in ai_ingredients.items()}, 
                "numberOf_ingredient": len(ai_ingredients),
                "suggest_recipe": suggest_recipe,
                "recipe_Number": len(suggest_recipe),
                "first": first, 
                "second": second, 
                "third": third,
                "ingredient_list": ingredient_list

            })

    # Xử lý
    if request.method == "POST" and request.FILES.get('image_upload'):
        try:
            file = request.FILES.get('image_upload')
            img = Image.open(file)
            # Standardize image -> RGB
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            temp_path = f"temp_{file.name.split('.')[0]}.jpg"
            img.save(temp_path, "JPEG")
            
            # Call API Roboflow 
            raw_ingredients = roboflow_service.predict_image(temp_path)

            # Delete file save after predict
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            # Avoid empty page
            if not raw_ingredients:
                suggest_recipe = list_recipe
                first = view_recipe.random_Recipe()
                second = view_recipe.random_Recipe()
                third = view_recipe.random_Recipe()
                translate = {}
            else:
                # Capitalize after predict
                capitalized_ingredients = [name.strip().capitalize() for name in raw_ingredients]
                
                # Collect data
                count_ingredient = Counter(capitalized_ingredients)
                unique_ingredients = list(count_ingredient.keys())
                
                # Translate vietnamese
                # translate = dict(count_ingredient)
                translate = {translate_dict.get(i, i) : count for i, count in count_ingredient.items()}
                
                
                request.session['dict_ingredient'] = dict(count_ingredient)
                # Push AI_Label to Session (English & Capitalized)
                request.session['ai_label'] = unique_ingredients
                
                #Suggest Recipe
                suggest_recipe,full_list_Recipe = view_recipe.getRecipe_AI(unique_ingredients)
                request.session['suggested_ids'] = [str(r.id) for r in suggest_recipe]
                
                if len(suggest_recipe) >= 1: first = suggest_recipe[0]
                if len(suggest_recipe) >= 2: second = suggest_recipe[1]
                if len(suggest_recipe) >= 3: third = suggest_recipe[2]
                 
        except Exception as e:
            print(f"Error during prediction: {e}")
            
        return render(request, 'recipe.html', {
            "count_ingredient": translate, 
            "numberOf_ingredient": len(count_ingredient) if 'count_ingredient' in locals() else 0,
            "suggest_recipe": suggest_recipe,
            "recipe_Number": len(suggest_recipe),
            "first": first, 
            "second": second, 
            "third": third,
            "ingredient_list": ingredient_list
            
            })
    # Avoid error from reload page
    return redirect('predict_model')


def food_view(request):
    list_Recipe = view_recipe.dsMonAn        
    
    # Pull AI_Label from session
    ai_ingredients = request.session.get('ai_label', [])
    suggested_ids = request.session.get('suggested_ids', [])
    
    # Reconstruct suggest list from IDs
    if suggested_ids:
        suggest_objs = [r for r in list_Recipe if str(r.id) in suggested_ids]
    else:
        suggest_objs = list_Recipe
    
    # Receive the main ID after click see details 
    get_Id = request.GET.get('id')
    main_recipe = next(filter(lambda r: r.id == str(get_Id), list_Recipe), None)
            
    if not main_recipe:
        main_recipe = suggest_objs[0] if suggest_objs else list_Recipe[0]

    # Get Ingredient from main ID
    recipe_ingredient = [i.strip().capitalize() for i in main_recipe.thanhPhan]
    ai_detected = [i.strip().capitalize() for i in ai_ingredients]
    
    # Caculate the omission
    missing = [translate_dict.get(item, item) for item in recipe_ingredient if item not in ai_detected]
    
    # Paginator with the list 8/page and get page number after change page
    paginator = Paginator(suggest_objs, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    main_recipe.thanhPhan = [translate_dict.get(i.strip().capitalize(), i.strip().capitalize()) for i in main_recipe.thanhPhan]

    return render(request, 'food.html', {
        "page_obj": page_obj,
        "main_recipe": main_recipe,
        "current_id": get_Id,
        "missing": missing, 
        "recipe_Number": len(suggest_objs),
    })

def translate_recipe_data(recipe_list):
    for recipe in recipe_list:
        if hasattr(recipe, 'thanhPhan'):
            recipe.thanhPhan = [translate_dict.get(item.strip().capitalize(), item.strip().capitalize()) for item in recipe.thanhPhan]
    return recipe_list

def add_ingredient(request):

    if request.method == "POST":
        selected = request.POST.getlist("ingredients")

        current_dict = request.session.get('dict_ingredient', {})

        for item in selected:
            item = item.strip().capitalize()
            if item in current_dict:
                current_dict[item] += 1
            else:
                current_dict[item] = 1

        request.session['dict_ingredient'] = current_dict
        request.session['ai_label'] = list(current_dict.keys())
        request.session.modified = True

        return redirect('predict_model')

    return render(request, "recipe.html", {
        "ingredient_list": ingredient_list
    })