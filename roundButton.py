import PySimpleGUI as sg
from PIL import Image, ImageDraw, ImageFont



def roundButtonImg(text, key, color, highlight, disabled):
    def hexToRgb(hex):
        """
        hex: hex string
        """
        hex = hex.replace("#", "")
        r, g, b = [int(hex[i: i + 2], 16) for i in range(0, len(hex), 2)]

        return r, g, b

    def replaceColor(image, colorToReplace, replaceColor):
        """
        Replace a present color with another, applied on all image
        This method is extremely precise, only corrisponding pixels
        will be replaced with no threshold
        """
        import numpy as np

        if "#" in colorToReplace:
            colorToReplace, replaceColor = [[*hexToRgb(each), 255]
                for each in [colorToReplace, replaceColor]]
        
        def parser(color):
            color = str(color)
            rgbNumber = ""
            rgb = []
            for char in color:
                if char.isdigit():
                    rgbNumber += char
                if char == "," or char == ")":
                    rgb.append(int(rgbNumber))
                    rgbNumber = ""
            r, g, b = rgb[0], rgb[1], rgb[2]
            return r, g, b

        data = np.array(image)
        r, g, b, a = data.T
        if colorToReplace is None:  # replace all pixels
            data[..., :-1] = parser(replaceColor)
            image = Image.fromarray(data)
        else:  # replace single color
            rr, gg, bb = parser(colorToReplace)
            colorToReplace = (r == rr) & (g == gg) & (b == bb)
            data[..., :-1][colorToReplace.T] = parser(replaceColor)
            image = Image.fromarray(data)

        return image

    def roundCorners(im, rad):
        """
        Rounds the corners of an image to given radius
        """
        mask = Image.new("L", im.size)
        if rad > min(*im.size) // 2:
            rad = min(*im.size) // 2
        draw = ImageDraw.Draw(mask)

        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        draw.ellipse((0, im.height - rad * 2 -2, rad * 2, im.height-1) , fill=255)
        draw.ellipse((im.width - rad * 2, 1, im.width, rad * 2), fill=255)
        draw.ellipse(
            (im.width - rad * 2, im.height - rad * 2, im.width-1, im.height-1), fill=255
        )
        draw.rectangle([rad, 0, im.width - rad, im.height], fill=255)
        draw.rectangle([0, rad, im.width, im.height - rad], fill=255)
        
        mask,_ = superSample(mask, 8)
        im.putalpha(mask)
        

        return im

    def superSample(image, sample):
        """
        Supersample an image for better edges
        image: image object
        sample: sampling multiplicator int(suggested: 2, 4, 8)
        """
        w, h = image.size

        image = image.resize((int(w * sample), int(h * sample)), resample=Image.LANCZOS)
        image = image.resize((image.width // sample, image.height // sample), resample=Image.ANTIALIAS)

        
        return image, ImageDraw.Draw(image)

    def image_to_data(im):
        """
        This is for Pysimplegui library
        Converts image into data to be used inside GUIs
        """
        from io import BytesIO

        with BytesIO() as output:
            im.save(output, format="PNG")
            data = output.getvalue()
        return data

    def getSize(text_string, font):
        ascent, descent = font.getmetrics()
        text_width, text_height = font.getsize(text_string)

        return (text_width, text_height-descent)

    # !! IMPORTANT !!
    # CHANGE THIS PATH FOR OTHER OS
    fontPath = 'C:\\Windows\\Fonts\Arial.ttf'
    w, h = getSize(text, ImageFont.truetype(fontPath, size=20))
    w += 10; h += 20

    OUT = [Image.new("RGBA", (w*5, h*5), color)]
    OUT.append(ImageDraw.Draw(OUT[0]))
    
    OUT[0] = roundCorners(OUT[0], 5*5)
    IN = replaceColor(OUT[0], color, highlight).resize((w,h), resample=Image.ANTIALIAS)
    DISABLED = replaceColor(OUT[0], color, disabled).resize((w,h), resample=Image.ANTIALIAS)
    OUT = OUT[0].resize((w,h), resample=Image.ANTIALIAS)
    OUT, IN, DISABLED = [image_to_data(each) for each in [OUT, IN, DISABLED]]

    button = sg.Button(text, border_width=0, button_color=sg.theme_background_color(),
                       disabled_button_color=sg.theme_background_color(), 
                       image_data=OUT, key=key)

    return button, IN, OUT, DISABLED


def in_out(window, event):
    if "+IN+" in event:
        element = event.replace('+IN+', "")
        if window[element].Disabled == 'ignore': return False
        window[element].Update(button_color=(color, sg.theme_background_color()), image_data=buttons[element][1])
    elif "+OUT+" in event:
        element = event.replace('+OUT+', "")
        if window[element].Disabled == 'ignore': return False
        window[element].Update(button_color=(highlight, sg.theme_background_color()), image_data=buttons[element][2])
    window.refresh()
    return True
    
def disable(window, element, disabled):
    if disabled:
        state, index = sg.BUTTON_DISABLED_MEANS_IGNORE, 3
    else:
        state, index = False, 2

    window[element].Update(button_color=(highlight, sg.theme_background_color()),
        disabled=state,
        image_data=buttons[element][index]
        )
    window.refresh()

# Defining button colors (IN and OUT switch colors for button and text)
color, highlight, disabled = '#3369ff', '#FFFFFF', '#4a4a4a'

# Creating button before layout disposing
buttons = {
    # Example of what this dict will become 
    # images are ready to be used as image_data
    # key : [ 0=sg.Button, 1=noMouseOverImage, 2=mouseOverImage, 3=disabledImage]
    "ONE" : [*roundButtonImg("YES", "ONE", color, highlight, disabled)],
    "TWO": [*roundButtonImg("NO", "TWO", color, highlight, disabled)],
    "DISABLE" : [*roundButtonImg("DISABLE", "DISABLE", color, highlight, disabled)],
    }

layout = [
    [sg.Push(), buttons['ONE'][0], buttons['TWO'][0], sg.Push()],
    [sg.Push(), buttons['DISABLE'][0], sg.Push()]
]

window = sg.Window('Round', layout, use_default_focus=False, finalize=True)

# Binding buttons after window creation
for button in buttons.keys():
    [window[button].bind(*each) for each in [('<Enter>', "+IN+"),('<Leave>', "+OUT+")]]


while True:
    event, value = window.read()

    if event == sg.WINDOW_CLOSED or event == 'Quit':
        break

    # Here buttons are checked for IN or OUT
    # and change state accordingly, while
    # Disabled button are ignored with continue

    if not in_out(window, event):
        continue

    # You can ignore this block
    if event in ['ONE', 'TWO']:
        if window['ONE'].ButtonText == 'YES':
            window['ONE'].Update('NO')
            window['TWO'].Update('YES')
        elif window['ONE'].ButtonText == 'NO':
            window['ONE'].Update('YES')
            window['TWO'].Update('NO')

    # This is a way to control disabling buttons
    # Disabled attribute carries 'ignore' instead
    # of True

    if event == "DISABLE":
        if window['ONE'].Disabled == 'ignore':
            shouldDisable = False
        elif window['ONE'].Disabled == False:
            shouldDisable = True
        [disable(window, each, shouldDisable) for each in ['ONE', "TWO"]]
    
    
window.close()
