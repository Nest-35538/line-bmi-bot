from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
from PIL import Image, ImageOps
import numpy as np
import os
import tensorflow as tf

app = Flask(__name__)

line_bot_api = LineBotApi("fkzpG65r65ziCzYSFVzgYTkUkHcEY9kA2g+Q0AEQXyedgFeVIYEDSalRQoPblZlIHFqWTla6zTucQm226FAt6/vhTXqVuUxa/1Ebpjoq7T65QhkoadXnmcobyyR3IXqQwiJdi2xX8j6vz0s7u8tspgdB04t89/1O/w1cDnyilFU=") [cite: 1]
handler = WebhookHandler("703a0d03e0a710133195e50703972a2e") [cite: 1]

model = None

def load_model():
    global model
    if model is None:
        model = tf.keras.models.load_model("keras_model.h5") [cite: 1]

with open("labels.txt", "r", encoding="utf-8") as f:
    labels = [line.strip() for line in f.readlines()] [cite: 1, 2]

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['x-line-signature'] [cite: 1]
    body = request.get_data(as_text=True) [cite: 1]
    try:
        handler.handle(body, signature) [cite: 1]
    except InvalidSignatureError:
        abort(400) [cite: 1]
    return 'OK' [cite: 1]

@handler.add(MessageEvent, message=TextMessage) 
def handler_text_message(event):
    text = event.message.text [cite: 1]
    if "น้ำหนัก" in text and "ส่วนสูง" in text: [cite: 1]
         try:
             parts = text.split() [cite: 1]
             w = float(parts[1]) [cite: 1]
             h = float(parts[3]) [cite: 1]
             h = h / 100 [cite: 1]
             bmi = w / (h**2) [cite: 1]
             result = f"BMI ของคุณ {bmi:.2f}\n" [cite: 1]
             if bmi < 18.5:
                 advice = "ค่า BMI ของคุณต่ำกว่าเกณฑ์นะคะ ควรเน้นโปรตีนและคาร์โบไฮเดรตค่ะ เช่น ข้าวผัดหมู แซนวิชไข่ เนื่องจากอาหารเหล่านี้มี คาร์โบไฮเดรตให้พลังงาน(ข้าว และ ขนมปัง) และมีโปรตีนช่วยให้ได้รับพลังงาน(ไข่ และ หมู)" [cite: 1]
             elif bmi < 23:
                 advice = "ค่า BMI ของคุณอยู่ในเกณฑ์ปกตินะคะ รักษามาตรฐานนี้ไว้นะคะ" [cite: 1]
             else:
                 advice = "ค่า BMI ของคุณสูงกว่าเกณฑ์นะคะ ควรเลี่ยงของทอดและของหวาน แนะนำอาหารที่ควรทาน เช่น ข้าวกับต้มจืด เนื่องจากเมนูนี้ให้พลังงานพอดีและเป็นอาหารไขมันต่ำค่ะ" [cite: 1]
             line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result + advice)) [cite: 1]
         except:
             line_bot_api.reply_message(event.reply_token, TextSendMessage(text="กรุณาพิมพ์ในรูปแบบ: น้ำหนัก 70 ส่วนสูง 170")) [cite: 1]

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    try:
        message_content = line_bot_api.get_message_content(event.message.id) [cite: 1]
        with open("temp_image.jpg", "wb") as f:
            for chunk in message_content.iter_content():
                f.write(chunk) [cite: 1]
        
        image = Image.open("temp_image.jpg").convert("RGB") [cite: 1]
        size = (224, 224) [cite: 1]
        image = ImageOps.fit(image, size, Image.Resampling.LANCZOS) [cite: 1]
        image_array = np.asarray(image) [cite: 1]
        normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1 [cite: 1]
        
        data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32) [cite: 1]
        data[0] = normalized_image_array [cite: 1]
        
        load_model() [cite: 1]
        prediction = model.predict(data) [cite: 1]
        index = np.argmax(prediction) [cite: 1]
        food_name = labels[index].strip() [cite: 1, 2]
        
        calories_db = {
             "0 ก๋วยเตี๋ยว": "330-350", 
             "1 ข้าวมันไก่ต้ม": "539-619", 
             "2 ข้าวมันไก่ทอด": "693-800", 
             "3 ข้าวกะเพรา": "580-630", 
             "4 ข้าวต้ม": "200-300"
        } [cite: 1, 2]
        
        cal = calories_db.get(food_name, "ไม่ทราบข้อมูล") [cite: 1]
        display_name = food_name.split(' ', 1)[-1] if ' ' in food_name else food_name [cite: 1]
        
        reply = f"นี่คือ: {display_name}\nพลังงานโดยประมาณ: {cal} kcal" [cite: 1]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply)) [cite: 1]
    except Exception as e:
        print(e)

if __name__ == "__main__":
     port = int(os.environ.get("PORT", 5000)) [cite: 1]
     app.run(host='0.0.0.0', port=port) [cite: 1]
