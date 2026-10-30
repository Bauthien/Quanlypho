"""Illustrative catalog data; quantities are for a medium bowl or one drink."""


INGREDIENTS = [
    ('noodle','Bánh phở tươi','kg','PHO','20','5',()),
    ('broth','Nước hầm xương','lit','PHO','100','20',('Nước dùng',)),
    ('beef','Thịt bò tươi','kg','PHO','20','5',('Thịt bò',)),
    ('herbs','Hành lá, rau thơm','kg','PHO','3','.5',()),
    ('tea','Trà lài','kg','DRINK','5','1',()),
    ('coffee','Cà phê','kg','DRINK','5','1',()),
    ('ice','Đá','kg','DRINK','50','10',('Đá viên',)),
    ('egg','Trứng','quả','PHO','100','20',('Trứng gà',)),
    ('quay','Quẩy chiên','đĩa','PHO','50','10',()),
    ('brisket','Thịt bò nạm chín','gram','PHO','5000','1000',()),
    ('fatty_beef','Thịt bò gầu chín','gram','PHO','5000','1000',()),
    ('meatball','Bò viên','gram','PHO','4000','800',()),
    ('chicken','Thịt gà chín','gram','PHO','5000','1000',()),
    ('blood','Tiết luộc','gram','PHO','3000','500',()),
    ('fried_onion','Hành phi','gram','PHO','1000','200',()),
    ('water','Nước lọc','ml','DRINK','100000','20000',()),
    ('sugar','Đường cát','gram','DRINK','10000','2000',('Đường',)),
    ('milk','Sữa đặc','ml','DRINK','5000','1000',()),
    ('orange','Cam tươi','gram','DRINK','15000','3000',()),
    ('peach_syrup','Si rô đào','ml','DRINK','5000','1000',()),
    ('peach','Đào ngâm','gram','DRINK','3000','500',()),
    ('lemongrass','Sả tươi','gram','DRINK','2000','300',()),
    ('soda','Nước ngọt lon','lon','DRINK','100','20',()),
]


PHO_BASE = [('noodle','200','g'),('broth','650','ml'),('herbs','10','g')]
MENU = [
    {'name':'Phở Bò Tái','category':'PHO','price':55000,'photo':'pho-tai','rows':PHO_BASE+[('beef','80','g')]},
    {'name':'Phở Bò Nạm','category':'PHO','price':60000,'photo':'pho-nam','rows':PHO_BASE+[('brisket','80','g')]},
    {'name':'Phở Bò Đặc Biệt (Tái + Nạm + Trứng)','category':'PHO','price':75000,'photo':'pho-dac-biet',
     'aliases':['Phở Bò Đặc Biệt'],'rows':[('noodle','250','g'),('broth','750','ml'),('herbs','10','g'),('beef','100','g'),('brisket','80','g'),('egg','1','quả')]},
    {'name':'Phở Bò Viên','category':'PHO','price':55000,'photo':'pho-bo-vien','rows':PHO_BASE+[('meatball','100','g')]},
    {'name':'Phở Tái Nạm','category':'PHO','price':65000,'photo':'pho-tai-nam','rows':PHO_BASE+[('beef','40','g'),('brisket','40','g')]},
    {'name':'Phở Bò Gầu','category':'PHO','price':65000,'photo':'pho-gau','rows':PHO_BASE+[('fatty_beef','80','g')]},
    {'name':'Phở Gà','category':'PHO','price':55000,'photo':'pho-ga','rows':PHO_BASE+[('chicken','90','g')]},
    {'name':'Trà Đá Hà Nội','category':'DRINK','price':5000,'photo':'tra-da','rows':[('tea','10','g'),('water','250','ml'),('ice','80','g')]},
    {'name':'Nước Ngọt Lon','category':'DRINK','price':15000,'photo':'nuoc-ngot-lon','mode':'DIRECT','rows':[('soda','1','lon')]},
    {'name':'Cà Phê Sữa Đá','category':'DRINK','price':25000,'photo':'ca-phe-sua-da','rows':[('coffee','20','g'),('milk','30','ml'),('water','60','ml'),('ice','100','g')]},
    {'name':'Nước Cam Tươi','category':'DRINK','price':30000,'photo':'nuoc-cam','rows':[('orange','250','gram'),('sugar','15','gram'),('water','50','ml'),('ice','80','g')]},
    {'name':'Trà Đào Cam Sả','category':'DRINK','price':30000,'photo':'tra-dao-cam-sa','rows':[('tea','10','g'),('water','200','ml'),('peach_syrup','20','ml'),('peach','40','gram'),('orange','30','gram'),('lemongrass','5','gram'),('ice','100','g')]},
]


TOPPINGS = [
    {'name':'Trứng chần nước béo','price':5000,'photo':'trung-chan','aliases':['Trứng chần'],'rows':[('egg','1','quả')]},
    {'name':'Thịt bò tái thêm','price':25000,'photo':'bo-tai-them','rows':[('beef','50','g')]},
    {'name':'Bò nạm thêm','price':25000,'photo':'bo-nam-them','rows':[('brisket','50','gram')]},
    {'name':'Tiết luộc','price':10000,'photo':'tiet-luoc','rows':[('blood','50','gram')]},
    {'name':'Quẩy giòn (1 đĩa)','price':10000,'photo':'quay-gion','aliases':['Quẩy giòn'],'rows':[('quay','1','đĩa')]},
    {'name':'Bò viên thêm','price':15000,'photo':'bo-vien-them','rows':[('meatball','50','gram')]},
    {'name':'Hành phi','price':5000,'photo':'hanh-phi','rows':[('fried_onion','10','gram')]},
]

PHOTO_SLUGS = [item['photo'] for item in MENU+TOPPINGS]
