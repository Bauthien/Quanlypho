"""
Domain-specific Semantic NLP & Heuristic Engine for Auto-BOM (Bill of Materials) Generation.

Phân tích ngữ nghĩa tên món ăn, trích xuất thực thể ẩm thực (Food Entity Extraction),
và áp dụng khung định lượng chuẩn ẩm thực (Vietnamese Culinary Heuristic Framework)
để tự động sinh công thức tiêu hao nguyên liệu trong kho quán phở.
"""

import re
import unicodedata
from decimal import Decimal


def remove_accents(input_str: str) -> str:
    """Chuẩn hóa chuỗi tiếng Việt về dạng không dấu để so khớp linh hoạt."""
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Thay thế d/D gạch ngang tiếng Việt
    return only_ascii.replace('đ', 'd').replace('Đ', 'D').lower().strip()


def find_ingredient_by_keywords(ingredients, keywords):
    """
    Tìm nguyên liệu trong danh mục kho phù hợp nhất với danh sách từ khóa.
    Ưu tiên so khớp chính xác cụm từ trước, sau đó so khớp từng từ.
    """
    for kw in keywords:
        kw_norm = remove_accents(kw)
        for ing in ingredients:
            ing_norm = remove_accents(ing['name'])
            if kw_norm == ing_norm or kw_norm in ing_norm:
                return ing
    return None


def get_input_unit(base_unit: str) -> str:
    """Chuyển đổi đơn vị kho lớn sang đơn vị nhập khẩu phần thông dụng (kg -> g, lit -> ml)."""
    unit = (base_unit or '').strip().lower()
    if unit in ('kg', 'kilogram'):
        return 'g'
    if unit in ('l', 'lit', 'lít', 'liter'):
        return 'ml'
    return base_unit


def suggest_recipe_bom(product_name: str, category: str = 'PHO', target_kind: str = 'MENU', available_ingredients: list = None) -> dict:
    """
    Thuật toán cốt lõi: Domain-specific Semantic NLP & Heuristic Engine.
    
    Đầu vào:
    - product_name: Tên món ăn / nước uống / topping (VD: 'Phở Bò Đặc Biệt', 'Phở Bò Tái', 'Trà Đào')
    - category: Nhóm sản phẩm ('PHO', 'DRINK')
    - target_kind: 'MENU' (Món chính), 'DRINK' (Nước uống), 'TOPPING' (Topping gọi thêm)
    - available_ingredients: Danh sách nguyên liệu kho có sẵn [{'id': 1, 'name': 'Thịt bò tươi', 'unit': 'kg', 'usage': 'PHO'}, ...]
    
    Đầu ra:
    - dict chứa 'ok', 'mode' ('BOM' | 'DIRECT'), 'explanation', 'rows': [{'ingredient_id', 'quantity', 'input_unit', 'reason'}]
    """
    if available_ingredients is None:
        available_ingredients = []

    name_raw = (product_name or '').strip()
    name_norm = remove_accents(name_raw)

    rows = []
    explanation_parts = []
    mode = 'BOM'

    # Kiểm tra các cờ ngữ nghĩa đặc trưng (Semantic Modifier Flags)
    is_special = any(k in name_norm for k in ['dac biet', 'thuong hang', 'dac biet lon', 'to lon', 'khong lo', 'vip', 'nhieu thit'])
    is_pho = 'pho' in name_norm or category == 'PHO' or target_kind == 'MENU'
    
    # =========================================================================
    # 1. NHÓM MÓN CHÍNH: PHỞ (VIETNAMESE PHO DOMAIN RULES)
    # =========================================================================
    if target_kind == 'MENU' and category == 'PHO':
        explanation_parts.append(f"Nhận diện món chính thuộc chuyên mục Phở truyền thống ({name_raw})")
        if is_special:
            explanation_parts.append("Phát hiện hậu tố 'Đặc biệt / Thượng hạng' -> Tăng định lượng thịt và bổ sung trứng gà")

        # 1.1 Khung cơ sở: Bánh phở tươi
        noodle_ing = find_ingredient_by_keywords(available_ingredients, ['bánh phở tươi', 'bánh phở', 'bánh phở khô', 'phở'])
        if noodle_ing:
            qty = '250' if is_special else '200'
            unit = get_input_unit(noodle_ing['unit'])
            rows.append({
                'ingredient_id': noodle_ing['id'],
                'name': noodle_ing['name'],
                'quantity': qty,
                'input_unit': unit,
                'reason': f"Khung bánh phở cơ sở ({qty}{unit})"
            })

        # 1.2 Khung cơ sở: Nước dùng hầm xương
        broth_ing = find_ingredient_by_keywords(available_ingredients, ['nước hầm xương', 'nước hầm', 'nước dùng', 'cốt phở', 'xương'])
        if broth_ing:
            qty = '750' if is_special else '650'
            unit = get_input_unit(broth_ing['unit'])
            rows.append({
                'ingredient_id': broth_ing['id'],
                'name': broth_ing['name'],
                'quantity': qty,
                'input_unit': unit,
                'reason': f"Khung nước hầm xương đậm đà ({qty}{unit})"
            })

        # 1.3 Phân tích Nhân thịt (Protein Semantic Extraction)
        # Bò (Tái, Nạm, Gầu, Gân, Bò viên, Bò tươi)
        has_beef = any(k in name_norm for k in ['bo', 'tai', 'nam', 'gau', 'gan', 'vien']) or ('ga' not in name_norm and 'xa xiu' not in name_norm)
        has_chicken = 'ga' in name_norm
        has_pork = 'xa xiu' in name_norm or 'heo' in name_norm or 'lon' in name_norm

        if has_chicken and not ('bo' in name_norm and not has_beef):
            chicken_ing = find_ingredient_by_keywords(available_ingredients, ['thịt gà', 'gà xé', 'thịt gà ta', 'gà'])
            if chicken_ing:
                qty = '180' if is_special else '100'
                unit = get_input_unit(chicken_ing['unit'])
                rows.append({
                    'ingredient_id': chicken_ing['id'],
                    'name': chicken_ing['name'],
                    'quantity': qty,
                    'input_unit': unit,
                    'reason': f"Nhân thịt gà xé ({qty}{unit})"
                })
        elif has_pork and not has_beef:
            pork_ing = find_ingredient_by_keywords(available_ingredients, ['thịt xá xíu', 'xá xíu', 'thịt heo'])
            if pork_ing:
                qty = '160' if is_special else '90'
                unit = get_input_unit(pork_ing['unit'])
                rows.append({
                    'ingredient_id': pork_ing['id'],
                    'name': pork_ing['name'],
                    'quantity': qty,
                    'input_unit': unit,
                    'reason': f"Nhân thịt xá xíu ({qty}{unit})"
                })
        else:
            # Mặc định dòng phở bò
            beef_ing = find_ingredient_by_keywords(available_ingredients, ['thịt bò tươi', 'thịt bò', 'thịt nạm', 'thịt tái', 'bò'])
            if beef_ing:
                # Nếu là Phở bò đặc biệt theo chuẩn đề xuất: 280g thịt (hoặc 120g nếu bình thường)
                qty = '280' if is_special else ('100' if any(k in name_norm for k in ['tai nam', 'tai gau', 'thap cam']) else '80')
                unit = get_input_unit(beef_ing['unit'])
                rows.append({
                    'ingredient_id': beef_ing['id'],
                    'name': beef_ing['name'],
                    'quantity': qty,
                    'input_unit': unit,
                    'reason': f"Nhân thịt bò chuẩn vị ({qty}{unit})"
                })

        # 1.4 Suất đặc biệt hoặc có từ khóa Trứng: Thêm trứng gà
        if is_special or 'trung' in name_norm:
            egg_ing = find_ingredient_by_keywords(available_ingredients, ['trứng gà', 'trứng chần', 'trứng'])
            if egg_ing:
                unit = egg_ing['unit']
                rows.append({
                    'ingredient_id': egg_ing['id'],
                    'name': egg_ing['name'],
                    'quantity': '1',
                    'input_unit': unit,
                    'reason': "Bổ sung 1 quả trứng gà cho suất đặc biệt / tô lớn"
                })

        # 1.5 Hành lá / Rau thơm (Gia vị cơ bản) nếu chưa có quá 4 dòng
        if not is_special:
            herb_ing = find_ingredient_by_keywords(available_ingredients, ['hành lá', 'rau thơm', 'hành'])
            if herb_ing:
                unit = get_input_unit(herb_ing['unit'])
                rows.append({
                    'ingredient_id': herb_ing['id'],
                    'name': herb_ing['name'],
                    'quantity': '15',
                    'input_unit': unit,
                    'reason': f"Hành lá rau mùi ăn kèm ({15}{unit})"
                })

    # =========================================================================
    # 2. NHÓM NƯỚC UỐNG (BEVERAGES DOMAIN RULES)
    # =========================================================================
    elif target_kind == 'DRINK' or category == 'DRINK':
        explanation_parts.append(f"Nhận diện sản phẩm đồ uống ({name_raw})")
        
        # Đồ đóng chai/lon sẵn: Bán trực tiếp (DIRECT mode)
        direct_tokens = ['coca', 'pepsi', 'sting', '7up', 'aquafina', 'suoi', 'khoang', 'lon', 'chai', 'redbull', 'bo huc', 'twister']
        is_direct = any(t in name_norm for t in direct_tokens)
        
        if is_direct:
            mode = 'DIRECT'
            explanation_parts.append("Đồ uống đóng lon/chai đóng gói sẵn -> Chuyển sang chế độ xuất kho trực tiếp (DIRECT)")
            packaged_ing = find_ingredient_by_keywords(available_ingredients, ['nước ngọt', 'nước suối', 'nước giải khát', name_raw])
            if packaged_ing:
                rows.append({
                    'ingredient_id': packaged_ing['id'],
                    'name': packaged_ing['name'],
                    'quantity': '1',
                    'input_unit': packaged_ing['unit'],
                    'reason': "Xuất kho 1 đơn vị lon/chai khi bán"
                })
        else:
            # Đồ uống pha chế (BOM mode)
            mode = 'BOM'
            if any(k in name_norm for k in ['ca phe', 'cafe']):
                coffee_ing = find_ingredient_by_keywords(available_ingredients, ['cà phê hạt', 'cà phê', 'cafe'])
                sugar_ing = find_ingredient_by_keywords(available_ingredients, ['đường', 'đường cát'])
                if coffee_ing:
                    unit = get_input_unit(coffee_ing['unit'])
                    rows.append({
                        'ingredient_id': coffee_ing['id'],
                        'name': coffee_ing['name'],
                        'quantity': '25',
                        'input_unit': unit,
                        'reason': f"Cốt cà phê pha phin/máy ({25}{unit})"
                    })
                if sugar_ing:
                    unit = get_input_unit(sugar_ing['unit'])
                    rows.append({
                        'ingredient_id': sugar_ing['id'],
                        'name': sugar_ing['name'],
                        'quantity': '15',
                        'input_unit': unit,
                        'reason': f"Đường định lượng ly ({15}{unit})"
                    })
            elif any(k in name_norm for k in ['tra', 'tea']):
                tea_ing = find_ingredient_by_keywords(available_ingredients, ['cốt trà', 'trà', 'chè'])
                sugar_ing = find_ingredient_by_keywords(available_ingredients, ['đường'])
                if tea_ing:
                    unit = get_input_unit(tea_ing['unit'])
                    rows.append({
                        'ingredient_id': tea_ing['id'],
                        'name': tea_ing['name'],
                        'quantity': '150',
                        'input_unit': unit,
                        'reason': f"Cốt trà ủ lạnh/nóng ({150}{unit})"
                    })
                if sugar_ing:
                    unit = get_input_unit(sugar_ing['unit'])
                    rows.append({
                        'ingredient_id': sugar_ing['id'],
                        'name': sugar_ing['name'],
                        'quantity': '20',
                        'input_unit': unit,
                        'reason': f"Đường pha chế ({20}{unit})"
                    })

    # =========================================================================
    # 3. NHÓM TOPPING GỌI THÊM (ADD-ON DOMAIN RULES)
    # =========================================================================
    elif target_kind == 'TOPPING':
        explanation_parts.append(f"Nhận diện Topping gọi thêm ({name_raw})")
        
        if 'trung' in name_norm:
            egg_ing = find_ingredient_by_keywords(available_ingredients, ['trứng gà', 'trứng chần', 'trứng'])
            if egg_ing:
                rows.append({
                    'ingredient_id': egg_ing['id'],
                    'name': egg_ing['name'],
                    'quantity': '1',
                    'input_unit': egg_ing['unit'],
                    'reason': "1 quả trứng phục vụ gọi thêm"
                })
        elif any(k in name_norm for k in ['bo', 'tai', 'nam', 'gau', 'gan', 'vien']):
            beef_ing = find_ingredient_by_keywords(available_ingredients, ['thịt bò tươi', 'thịt bò', 'bò'])
            if beef_ing:
                unit = get_input_unit(beef_ing['unit'])
                rows.append({
                    'ingredient_id': beef_ing['id'],
                    'name': beef_ing['name'],
                    'quantity': '50',
                    'input_unit': unit,
                    'reason': f"1 phần thịt bò gọi thêm ({50}{unit})"
                })
        elif 'ga' in name_norm:
            chicken_ing = find_ingredient_by_keywords(available_ingredients, ['thịt gà', 'gà'])
            if chicken_ing:
                unit = get_input_unit(chicken_ing['unit'])
                rows.append({
                    'ingredient_id': chicken_ing['id'],
                    'name': chicken_ing['name'],
                    'quantity': '50',
                    'input_unit': unit,
                    'reason': f"1 phần thịt gà gọi thêm ({50}{unit})"
                })
        elif any(k in name_norm for k in ['rau', 'ngap', 'hanh']):
            herb_ing = find_ingredient_by_keywords(available_ingredients, ['rau thơm', 'hành lá', 'hành'])
            if herb_ing:
                unit = get_input_unit(herb_ing['unit'])
                rows.append({
                    'ingredient_id': herb_ing['id'],
                    'name': herb_ing['name'],
                    'quantity': '30',
                    'input_unit': unit,
                    'reason': f"1 đĩa rau/hành thêm ({30}{unit})"
                })

    # =========================================================================
    # 4. FALLBACK THÔNG MINH (KHI TÊN MỚI LẠ CHƯA CÓ TRONG QUY TẮC)
    # =========================================================================
    if not rows and available_ingredients:
        explanation_parts.append("Tên món mới chưa có mẫu cụ thể -> Áp dụng khung tiêu chuẩn của nhóm")
        if category == 'PHO' or target_kind == 'MENU':
            # Khung phở tối thiểu
            noodle = find_ingredient_by_keywords(available_ingredients, ['bánh phở', 'phở'])
            broth = find_ingredient_by_keywords(available_ingredients, ['nước hầm', 'nước dùng', 'xương'])
            beef = find_ingredient_by_keywords(available_ingredients, ['thịt bò', 'thịt'])
            if noodle:
                rows.append({'ingredient_id': noodle['id'], 'name': noodle['name'], 'quantity': '200', 'input_unit': get_input_unit(noodle['unit']), 'reason': 'Bánh phở chuẩn'})
            if broth:
                rows.append({'ingredient_id': broth['id'], 'name': broth['name'], 'quantity': '650', 'input_unit': get_input_unit(broth['unit']), 'reason': 'Nước dùng chuẩn'})
            if beef:
                rows.append({'ingredient_id': beef['id'], 'name': beef['name'], 'quantity': '80', 'input_unit': get_input_unit(beef['unit']), 'reason': 'Thịt chính chuẩn'})

    return {
        'ok': bool(rows),
        'mode': mode,
        'product_name': name_raw,
        'explanation': ". ".join(explanation_parts) + ".",
        'rows': rows
    }

