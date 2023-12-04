from pdf2image import convert_from_path

from spire.presentation.common import *
from spire.presentation import *



def extract_ppt_files(input_path):

    inputFile = input_path

    #Create PPT document
    presentation = Presentation()

    #Load PPT file from disk
    presentation.LoadFromFile(inputFile)

    #Save PPT document to images
    for i, slide in enumerate(presentation.Slides):
        fileName ="ToImage_img_"+str(i)+".png"
        image = slide.SaveAsImage()
        image.Save(fileName)
        image.Dispose()

    presentation.Dispose()





