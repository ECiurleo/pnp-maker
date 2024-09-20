Requirements
pip install requests pillow reportlab

To Run 
python pnp-maker.py

Options;

Print in Duplux (front then back)
--duplex 

Specify a non-default json file to read from
--json

Specify the colour of the cut lines
--cut_line_colour

black,white,blue,red,green,yellow,orange

Specify the name of the output PDF file using --output_pdf

python pnp-maker.py --duplex --cut_line_colour green --output_pdf my_deck.pdf


Credits
Used this lovely site to generate me TTS json for testing, tts_json.json example is generated from there.
https://geckotown.me/
