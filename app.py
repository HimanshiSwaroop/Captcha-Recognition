# -*- coding: utf-8 -*-

from __future__ import division, print_function
import sys
import os
import glob
import re
import numpy as np
import tensorflow as tf
import cv2
import os.path
import imutils
import pickle
import os.path
import numpy as np
from imutils import paths

def resize_to_fit(image, width, height):
    """
    A helper function to resize an image to fit within a given size
    :param image: image to resize
    :param width: desired width in pixels
    :param height: desired height in pixels
    :return: the resized image
    """

    # grab the dimensions of the image, then initialize
    # the padding values
    (h, w) = image.shape[:2]

    # if the width is greater than the height then resize along
    # the width
    if w > h:
        image = imutils.resize(image, width=width)

    # otherwise, the height is greater than the width so resize
    # along the height
    else:
        image = imutils.resize(image, height=height)

    # determine the padding values for the width and height to
    # obtain the target dimensions
    padW = int((width - image.shape[1]) / 2.0)
    padH = int((height - image.shape[0]) / 2.0)

    # pad the image then apply one more resizing to handle any
    # rounding issues
    image = cv2.copyMakeBorder(image, padH, padH, padW, padW,cv2.BORDER_REPLICATE)
    image = cv2.resize(image, (width, height))

    # return the pre-processed image
    return image

from tensorflow.keras.models import load_model
#from tensorflow.keras.preprocessing import image

# Flask utils
from flask import Flask, redirect, url_for, request, render_template
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer

# Define a flask app
app = Flask(__name__, template_folder='templates')

MODEL_PATH = '/Users/himanshi/Desktop/AML_Proj/captcha.h5'


from tensorflow.keras.models import load_model
model = load_model('/Users/himanshi/Desktop/AML_Proj/captcha.h5')

MODEL_FILENAME = "/Users/himanshi/Desktop/AML_Proj/captcha.h5"
MODEL_LABELS_FILENAME = "/Users/himanshi/Desktop/AML_Proj/model_labels.dat"
CAPTCHA_IMAGE_FOLDER = "/Users/himanshi/Desktop/AML_Proj/generated_captcha_images"


with open(MODEL_LABELS_FILENAME, "rb") as f:lb = pickle.load(f)



def model_predict(img_path,model):
    
    
    # Load the image and convert it to grayscale
    image = cv2.imread(img_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Add some extra padding around the image
    image = cv2.copyMakeBorder(image, 100, 100, 100, 100, cv2.BORDER_REPLICATE)

    # threshold the image (convert it to pure black and white)
    thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    # find the contours (continuous blobs of pixels) the image
    contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Hack for compatibility with different OpenCV versions
    contours = contours[0] if imutils.is_cv2() else contours[1]
    contours = contours[0]
    letter_image_regions = []

    for contour in contours:
            # Get the rectangle that contains the contour
            (x, y, w, h) = cv2.boundingRect(contour)

            if (w / (h + 0.0001)) > 1.25:
                      # This contour is too wide to be a single letter!
                      # Split it in half into two letter regions!
                      half_width = int(w / 2)
                      letter_image_regions.append((x, y, half_width, h))
                      letter_image_regions.append((x + half_width, y, half_width, h))
            else:
                   # This is a normal letter by itself
                      letter_image_regions.append((x, y, w, h))

    #if len(letter_image_regions) != 4:       
                                #continue

    # Sort the detected letter images based on the x coordinate to make sure
    # we are processing them from left-to-right so we match the right image
    # with the right letter
    letter_image_regions = sorted(letter_image_regions, key=lambda x: x[0])

    # Create an output image and a list to hold our predicted letters
    output = cv2.merge([image] * 3)
    predictions = []

    # loop over the lektters
    for letter_bounding_box in letter_image_regions:
        # Grab the coordinates of the letter in the image
        x, y, w, h = letter_bounding_box

        # Extract the letter from the original image with a 2-pixel margin around the edge
        letter_image = image[y - 2:y + h + 2, x - 2:x + w + 2]

        # Re-size the letter image to 20x20 pixels to match training data
        letter_image = resize_to_fit(letter_image, 20, 20)

        # Turn the single image into a 4d list of images to make Keras happy
        letter_image = np.expand_dims(letter_image, axis=2)
        letter_image = np.expand_dims(letter_image, axis=0)

        # Ask the neural network to make a prediction
        prediction = model.predict(letter_image)

        # Convert the one-hot-encoded prediction back to a normal letter
        letter = lb.inverse_transform(prediction)[0]
        predictions.append(letter)

        # draw the prediction on the output image
        cv2.rectangle(output, (x - 2, y - 2), (x + w + 4, y + h + 4), (0, 255, 0), 1)
        cv2.putText(output, letter, (x - 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
    
    
    # Print the captcha's text
    captcha_text = "".join(predictions)
    print("CAPTCHA text is: {}".format(captcha_text))
    window_name = 'image'
    # Show the annotated image
    cv2.imshow(window_name,output)
    cv2.waitKey()
    return captcha_text
    



#q = model_predict('/Users/himanshi/Desktop/AML_Proj/generated_captcha_images/2AQ7.png',model)

#q







@app.route('/', methods=['GET','POST'])
def index():
    # Main page
    return render_template('index.html')
    if request.method == 'POST':
        # Get the file from post request
        f = request.files['file']

        # Save the file to ./uploads
        basepath = os.path.dirname(__file__)
        file_path = os.path.join(
            basepath, 'uploads', secure_filename(f.filename))
        f.save(file_path)
        preds = model_predict(file_path,model)
        output = preds
    return render_template('result.html', result=output)




if __name__ == '__main__':
    app.run(port=5000,debug=True)

     

