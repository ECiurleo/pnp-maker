import json
import requests
import argparse
from io import BytesIO
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import black, white, blue, red, green, yellow, orange  # Import additional colours

def mm_to_points(mm_value):
    return mm_value * mm

def download_image(url):
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful
    return Image.open(BytesIO(response.content)).convert('RGB')

def create_card_with_bleed(face_image, card_width, card_height, bleed_size):
    # Convert mm to pixels at 300 DPI
    card_width_px = int(card_width / 25.4 * 300)
    card_height_px = int(card_height / 25.4 * 300)
    bleed_size_px = int(bleed_size / 25.4 * 300)

    # Resize the face image to the card size
    face_image = face_image.resize((card_width_px, card_height_px), Image.LANCZOS)

    # Create a new image with bleed
    total_width_px = card_width_px + 2 * bleed_size_px
    total_height_px = card_height_px + 2 * bleed_size_px
    card_with_bleed = Image.new('RGB', (total_width_px, total_height_px))

    # Paste the face image onto the center
    card_with_bleed.paste(face_image, (bleed_size_px, bleed_size_px))

    # Create bleed by mirroring edges
    # Top edge
    top_edge = face_image.crop((0, 0, card_width_px, bleed_size_px))
    top_edge = ImageOps.flip(top_edge)
    card_with_bleed.paste(top_edge, (bleed_size_px, 0))
    # Bottom edge
    bottom_edge = face_image.crop((0, card_height_px - bleed_size_px, card_width_px, card_height_px))
    bottom_edge = ImageOps.flip(bottom_edge)
    card_with_bleed.paste(bottom_edge, (bleed_size_px, bleed_size_px + card_height_px))
    # Left edge
    left_edge = face_image.crop((0, 0, bleed_size_px, card_height_px))
    left_edge = ImageOps.mirror(left_edge)
    card_with_bleed.paste(left_edge, (0, bleed_size_px))
    # Right edge
    right_edge = face_image.crop((card_width_px - bleed_size_px, 0, card_width_px, card_height_px))
    right_edge = ImageOps.mirror(right_edge)
    card_with_bleed.paste(right_edge, (bleed_size_px + card_width_px, bleed_size_px))
    # Corners
    # Top-left
    tl_corner = face_image.crop((0, 0, bleed_size_px, bleed_size_px))
    tl_corner = tl_corner.transpose(Image.ROTATE_180)
    card_with_bleed.paste(tl_corner, (0, 0))
    # Top-right
    tr_corner = face_image.crop((card_width_px - bleed_size_px, 0, card_width_px, bleed_size_px))
    tr_corner = tr_corner.transpose(Image.ROTATE_180)
    card_with_bleed.paste(tr_corner, (bleed_size_px + card_width_px, 0))
    # Bottom-left
    bl_corner = face_image.crop((0, card_height_px - bleed_size_px, bleed_size_px, card_height_px))
    bl_corner = bl_corner.transpose(Image.ROTATE_180)
    card_with_bleed.paste(bl_corner, (0, bleed_size_px + card_height_px))
    # Bottom-right
    br_corner = face_image.crop((card_width_px - bleed_size_px, card_height_px - bleed_size_px, card_width_px, card_height_px))
    br_corner = br_corner.transpose(Image.ROTATE_180)
    card_with_bleed.paste(br_corner, (bleed_size_px + card_width_px, bleed_size_px + card_height_px))

    return card_with_bleed

def arrange_cards_from_json(json_data, duplex=False, cut_line_colour='black', output_pdf=None):
    # Parse the JSON data
    data = json.loads(json_data)
    object_states = data['objectStates'][0]
    custom_deck = object_states['customDeck']
    contained_objects = object_states['containedObjects']

    # Map cardIDs to face and back URLs
    card_id_to_urls = {}
    for card_id_str, deck_info in custom_deck.items():
        deck_number = int(card_id_str)
        face_url = deck_info['faceURL']
        back_url = deck_info['backURL']
        card_id_to_urls[deck_number] = {'faceURL': face_url, 'backURL': back_url}

    # Collect all cards with their face and back URLs
    cards = []
    for obj in contained_objects:
        card_id = obj['cardID']
        # Extract the deck number from cardID (cardID = deck_number * 100 + card_number)
        deck_number = card_id // 100
        card_urls = card_id_to_urls.get(deck_number)
        if card_urls:
            cards.append({
                'cardID': card_id,
                'faceURL': card_urls['faceURL'],
                'backURL': card_urls['backURL'],
                'nickname': obj.get('nickname', '')
            })

    # Download images (avoid duplicates)
    downloaded_faces = {}
    downloaded_backs = {}
    for card in cards:
        face_url = card['faceURL']
        back_url = card['backURL']
        if face_url not in downloaded_faces:
            downloaded_faces[face_url] = download_image(face_url)
        if back_url not in downloaded_backs:
            downloaded_backs[back_url] = download_image(back_url)

    # Prepare the lists of face and back images for arranging
    face_images = []
    back_images = []
    for card in cards:
        face_url = card['faceURL']
        back_url = card['backURL']
        face_images.append(downloaded_faces[face_url])
        back_images.append(downloaded_backs[back_url])

    # Determine output file name based on duplex option and output_pdf parameter
    if output_pdf is None:
        if duplex:
            output_pdf = "playing_cards_duplex.pdf"
        else:
            output_pdf = "playing_cards.pdf"

    # Now arrange the cards
    c = canvas.Canvas(output_pdf, pagesize=A4)
    page_width, page_height = A4

    # Page margin in mm
    page_margin = 5  # Adjust as needed

    # Card dimensions in mm
    card_width = 63  # Original card width
    card_height = 88  # Original card height (standard poker card height)
    bleed_size = 3    # Bleed size on all sides in mm

    # Total card dimensions including bleed
    total_card_width_mm = card_width + 2 * bleed_size
    total_card_height_mm = card_height + 2 * bleed_size

    # Convert dimensions to points
    total_card_width_pt = mm_to_points(total_card_width_mm)
    total_card_height_pt = mm_to_points(total_card_height_mm)

    # Calculate positions for 3 cards across and 3 cards down
    positions = []
    start_x = mm_to_points(page_margin)
    start_y = page_height - mm_to_points(page_margin)  # Start from top-left corner

    for row in range(3):  # 3 rows
        for col in range(3):  # 3 columns
            x = start_x + col * total_card_width_pt
            y = start_y - row * total_card_height_pt - total_card_height_pt
            positions.append((x, y))

    # Number of cards per page
    cards_per_page = 9

    # Map colour names to reportlab colour objects
    colour_map = {
        'black': black,
        'white': white,
        'blue': blue,
        'red': red,
        'green': green,
        'yellow': yellow,
        'orange': orange,
        # Add more colours if needed
    }

    # Get the cut line colour from the colour map
    try:
        cut_line_colour_obj = colour_map[cut_line_colour.lower()]
    except KeyError:
        print(f"Invalid cut line colour '{cut_line_colour}'. Defaulting to black.")
        cut_line_colour_obj = black

    # Function to draw a page
    def draw_page(images):
        num_pages = (len(images) + cards_per_page - 1) // cards_per_page
        for page in range(num_pages):
            start = page * cards_per_page
            end = start + cards_per_page
            page_images = images[start:end]
            for i, img in enumerate(page_images):
                x, y = positions[i]
                # Create card with bleed
                card_with_bleed = create_card_with_bleed(img, card_width, card_height, bleed_size)
                # Draw the image
                c.drawInlineImage(card_with_bleed, x, y, width=total_card_width_pt, height=total_card_height_pt)

                # Draw dotted cut line with specified colour
                border_x = x + mm_to_points(bleed_size)
                border_y = y + mm_to_points(bleed_size)
                border_width = mm_to_points(card_width)
                border_height = mm_to_points(card_height)

                c.setStrokeColor(cut_line_colour_obj)
                c.setLineWidth(0.5)
                c.setDash(2, 2)  # Dotted line pattern
                c.rect(border_x, border_y, border_width, border_height, stroke=1, fill=0)
                c.setDash()  # Reset dash
            c.showPage()

    # Function to draw duplex pages
    def draw_duplex_pages(face_images, back_images):
        total_cards = len(face_images)
        num_pages = (total_cards + cards_per_page - 1) // cards_per_page
        for page in range(num_pages):
            # Draw front page
            start = page * cards_per_page
            end = start + cards_per_page
            page_faces = face_images[start:end]
            for i, img in enumerate(page_faces):
                x, y = positions[i]
                # Create card with bleed
                card_with_bleed = create_card_with_bleed(img, card_width, card_height, bleed_size)
                # Draw the image
                c.drawInlineImage(card_with_bleed, x, y, width=total_card_width_pt, height=total_card_height_pt)

                # Draw dotted cut line with specified colour
                border_x = x + mm_to_points(bleed_size)
                border_y = y + mm_to_points(bleed_size)
                border_width = mm_to_points(card_width)
                border_height = mm_to_points(card_height)

                c.setStrokeColor(cut_line_colour_obj)
                c.setLineWidth(0.5)
                c.setDash(2, 2)  # Dotted line pattern
                c.rect(border_x, border_y, border_width, border_height, stroke=1, fill=0)
                c.setDash()  # Reset dash
            c.showPage()

            # Draw corresponding back page
            page_backs = back_images[start:end]
            for i, img in enumerate(page_backs):
                x, y = positions[i]
                # Create card with bleed
                card_with_bleed = create_card_with_bleed(img, card_width, card_height, bleed_size)
                # Draw the image
                c.drawInlineImage(card_with_bleed, x, y, width=total_card_width_pt, height=total_card_height_pt)

                # Draw dotted cut line with specified colour
                border_x = x + mm_to_points(bleed_size)
                border_y = y + mm_to_points(bleed_size)
                border_width = mm_to_points(card_width)
                border_height = mm_to_points(card_height)

                c.setStrokeColor(cut_line_colour_obj)
                c.setLineWidth(0.5)
                c.setDash(2, 2)  # Dotted line pattern
                c.rect(border_x, border_y, border_width, border_height, stroke=1, fill=0)
                c.setDash()  # Reset dash
            c.showPage()

    if duplex:
        # Draw duplex pages interleaving fronts and backs
        draw_duplex_pages(face_images, back_images)
    else:
        # Front pages
        draw_page(face_images)
        # Back pages
        draw_page(back_images)

    c.save()

# Main execution
if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description='Generate playing cards PDF.')
    parser.add_argument('--duplex', action='store_true', help='Arrange pages for duplex printing')
    parser.add_argument('--json', type=str, default='tt_json.json', help='Path to JSON file')
    parser.add_argument('--cut_line_colour', type=str, default='black', help='Colour of the cut lines (black, white, blue, red, etc.)')
    parser.add_argument('--output_pdf', type=str, default=None, help='Name of the output PDF file')
    args = parser.parse_args()

    # Read JSON data from file
    with open(args.json, 'r') as f:
        json_data = f.read()

    arrange_cards_from_json(json_data, duplex=args.duplex, cut_line_colour=args.cut_line_colour, output_pdf=args.output_pdf)
