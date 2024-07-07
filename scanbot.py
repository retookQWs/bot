#НЕОБХОДИМЫЕ БИБИЛИОТЕКИ
# !pip install PyPDF2
# !pip install pytesseract
# !apt install tesseract-ocr
# !apt install tesseract-ocr-rus
# # !pip install easyocr
# !pip install  pdf2image
# !apt-get install poppler-utils
# !pip install paddlepaddle
# !pip install paddleocr
# !pip install IPython
# !pip install  telebot

import pytesseract

import os
import re
import cv2
import numpy as np
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image
from IPython.display import display
from paddleocr import PaddleOCR, draw_ocr
import telebot
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

folder_path = 'output'
ocr = PaddleOCR(use_angle_cls=False, lang='en')
# Проверяем, существует ли папка, если нет, то создаем её
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
else:
    print("Папка 'output' уже существует.")

bot = telebot.TeleBot("622034566:AAHE5mrR9Rpu1p4daxp1-4desy7iaf9W_k8")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "Привет! Я бот для обработки PDF-сканов.\n"
        "Вот что я умею:\n"
        "1. Отправьте мне PDF-файл, и я распознаю текст из него.\n"
        "2. Разобью на части по триггеру 'Акт...№....'\n"
        "3. Отправлю вам отдельные файлы для каждого уникального идентификатора.\n"
        "Для наилучшенго результата используйте цветной режим\n"
        "Команды:\n"
        "/help - Показать эту помощь.\n"

    )
    bot.send_message(message.chat.id, help_text)



@bot.message_handler(content_types=['document'])

def handle_document(message):
    # Проверяем, что сообщение содержит документ типа PDF
    if message.document.mime_type == 'application/pdf':
        # Скачиваем PDF-файл
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        # Сохраняем PDF-файл на сервере
        with open("downloaded_pdf.pdf", 'wb') as new_file:
            new_file.write(downloaded_file)
        # Отправляем сообщение о успешном сохранении
        bot.send_message(message.chat.id, "PDF-файл успешно получен.")
        clear_directory(directory_to_clear)
        main("downloaded_pdf.pdf", message)  # Передаем message в main
    else:
        # Отправляем сообщение об ошибке, если полученный документ не является PDF
        bot.send_message(message.chat.id, "Пожалуйста, отправьте PDF-файл.")

def clear_directory(directory):
    # Получаем список файлов в каталоге
    files = os.listdir(directory)
    # Удаляем каждый файл из каталога
    for file in files:
        file_path = os.path.join(directory, file)
        # Проверяем, что это файл, а не директория, и удаляем его
        if os.path.isfile(file_path):
            os.remove(file_path)

directory_to_clear = 'output'

def extract_identifier(image, image2):
    text = pytesseract.image_to_string(image, lang='rus')



    print(text)



    match = re.search(r'Акт.*?при.', text)
    if match:
        print(text)
        new_st = re.sub(r'^9', '', re.search(r'\d+', text).group())
        return new_st # Возвращаем найденную последовательность цифр
    else:
        if has_blue_pixels(image2): #если есть синий цвет то..
            result = ocr.ocr("cropped_image2.jpg")
            if result[0] is not None:
                txt2 = '\n'.join([line[1][0] for line in result[0]])
                print(result)
                print(txt2)
                txt3 = max(txt2.split(), key=len)
                print(txt3)
                return txt3
            else:
                print("result[0] is None, cannot iterate.")

            # match = re.search(r'\d+', text)
            # print(text)
            # return match.group()
        else:
            match = re.search(r'ниверсал.*?фактур.', text)
            if match:
                match = re.search(r'\d+', text)
                print('УПД_' + match.group())
                return 'УПД_' + match.group()

        return None

def main(pdf_path, message):
    os.makedirs("output", exist_ok=True)
    current_identifier = None
    current_pdf_writer = None
    files_sent = 0  # Счетчик отправленных файлов

    pdf_reader = PdfReader(open(pdf_path, "rb"))

    for page_num in range(len(pdf_reader.pages)):
        images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1)
        image = images[0]

        width, height = image.size
        cropped_height = int(height * 0.12)
        cropped_image = image.crop((0, int(height * 0.04), int(width * 0.8), cropped_height))
        cropped_image2 = image.crop((int(width * 0.94), 0, width, int(height * 0.4)))
        cropped_image2r = cropped_image2.rotate(90, expand=True)
        cropped_image.save("cropped_image.jpg")
        cropped_image2r.save("cropped_image2.jpg")

        display(cropped_image)
        display(cropped_image2r)

        identifier = extract_identifier(cropped_image, cropped_image2)

        if identifier:
            if current_pdf_writer:
                output_pdf_path = f"output/{current_identifier}.pdf"
                with open(output_pdf_path, "wb") as output_pdf:
                    current_pdf_writer.write(output_pdf)
                send_file(output_pdf_path, message)
                files_sent += 1  # Увеличиваем счетчик отправленных файлов

            current_pdf_writer = PdfWriter()
            current_pdf_writer.add_page(pdf_reader.pages[page_num])
            current_identifier = identifier
        else:
            if current_pdf_writer:
                current_pdf_writer.add_page(pdf_reader.pages[page_num])

    if current_pdf_writer:
        output_pdf_path = f"output/{current_identifier}.pdf"
        with open(output_pdf_path, "wb") as output_pdf:
            current_pdf_writer.write(output_pdf)
        send_file(output_pdf_path, message)
        files_sent += 1  # Увеличиваем счетчик отправленных файлов

    # Отправляем сообщение с количеством отправленных файлов
    bot.send_message(message.chat.id, f"Отправлено файлов: {files_sent}		")

def send_file(file_path, message):
    with open(file_path, 'rb') as f:
        bot.send_document(message.chat.id, f)
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_message(message.chat.id, "жду ваших сканов 😊")


def has_blue_pixels(image_path, threshold=50):
    img = image_path
    width, height = img.size
    pixels = img.load()

    for x in range(width):
        for y in range(height):
            r, g, b = pixels[x, y]
            if b > threshold and b > r and b > g:
                return True
    return False

# Загрузка изображения
# image_path = '/content/Снимок экрана 2024-06-14 022804.jpg'
# if has_blue_pixels(image_path):
#     print("Изображение содержит синие пиксели")
# else:
#     print("Изображение не содержит синие пиксели")
# функция для выбора самой длинной последовательности из распознанных


bot.polling(none_stop=True, interval=0)


