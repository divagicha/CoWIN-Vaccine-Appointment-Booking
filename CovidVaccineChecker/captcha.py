# from svglib.svglib import svg2rlg
# from reportlab.graphics import renderPM
import PySimpleGUI as simpleGUI
import re
from PIL import Image
from cairosvg import svg2png
# from anticaptchaofficial.imagecaptcha import imagecaptcha

captcha_svgFile = './captcha/captcha.svg'
captcha_pngFile = './captcha/captcha.png'
captcha_gifFile = './captcha/captcha.gif'


def captcha_builder(resp):
    # with open(captcha_svgFile, 'w') as f:
    #     f.write(re.sub('(<path d=)(.*?)(fill="none"/>)', '', resp['captcha']))
    #
    # drawing = svg2rlg(captcha_svgFile)
    # renderPM.drawToFile(drawing, captcha_pngFile, fmt="PNG")
    #
    # im = Image.open(captcha_pngFile)
    # im = im.convert('RGB').convert('P', palette=Image.ADAPTIVE)
    # im.save(captcha_gifFile)

    captcha_svg_code = re.sub('(<path d=)(.*?)(fill="none"/>)', '', resp['captcha'])
    svg2png(bytestring=captcha_svg_code, write_to=captcha_pngFile)

    im = Image.open(captcha_pngFile)
    white_bg = Image.new("RGB", im.size, (255, 255, 255))
    white_bg.paste(im, im)
    white_bg.save(captcha_gifFile)

    layout = [[simpleGUI.Image(captcha_gifFile)],
              [simpleGUI.Text("Enter Captcha Below")],
              [simpleGUI.Input(key='input')],
              [simpleGUI.Button('Submit', bind_return_key=True)]]

    window = simpleGUI.Window('Enter Captcha', layout, finalize=True)
    window.TKroot.focus_force()         # focus on window
    window.Element('input').SetFocus()    # focus on field
    event, values = window.read()
    window.close()
    return values['input'] if values else " "


# def captcha_builder_auto(resp, api_key):
#     with open('captcha.svg', 'w') as f:
#         f.write(re.sub('(<path d=)(.*?)(fill=\"none\"/>)', '', resp['captcha']))
#
#     drawing = svg2rlg('captcha.svg')
#     renderPM.drawToFile(drawing, "captcha.png", fmt="PNG")
#
#
#     solver = imagecaptcha()
#     solver.set_verbose(1)
#     solver.set_key(api_key)
#     captcha_text = solver.solve_and_return_solution("captcha.png")
#
#     if captcha_text != 0:
#         print(f"Captcha text: {captcha_text}")
#     else:
#         print(f"Task finished with error: {solver.error_code}")
#
#     return captcha_text
