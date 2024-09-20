# Requirements
``pip install requests pillow reportlab``

## To Run 
``python pnp-maker.py``

### Options;

Print in Duplux (front then back) <br>
``--duplex`` 

Specify a non-default json file to read from <br>
``--json``

Specify the colour of the cut lines <br>
``--cut_line_colour``

Options are black,white,blue,red,green,yellow,orange

Specify the name of the output PDF file using <br> 
``--output_pdf``

_Full Example_ <br>
``python pnp-maker.py --duplex --json tts_json.json --cut_line_colour green --output_pdf my_deck.pdf``


## Credits
Used this lovely site to generate me TTS json for testing, tts_json.json example is generated from there.
https://geckotown.me/
