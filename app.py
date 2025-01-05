import io
import zipfile
from pathlib import Path

import gpxpy
import qrcode
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

st.markdown("# GPX waypoints to QR codes")

with st.sidebar:
    url_template = st.text_input(
        "URL template", "http://maps.google.com/?q={wp.latitude},{wp.longitude}"
    )
    title_template = st.text_input("Image title template", "{wp.name}")
    img_stem_template = st.text_input(
        "Image file stem template", "{gpx_stem}_{wp.name}"
    )

    st.write("Use `{wp}` as `gpxpy.gpx.GPXWaypoint` in templates")
    st.write("`{gpx_stem}` as GPX file stem")

    img_format = st.text_input("Image format", "png")
    img_width = st.number_input("Image width", value=78)
    img_height = st.number_input("Image height", value=78)
    font_size = st.number_input("Title font size", value=15)
    title_padding = st.number_input("Title padding (pixels)", value=10)


def create_zip(images_tuples_list):
    """
    Create a ZIP file in memory

    :param images_tuples_list: List of tuples of Pillow images and associated path string
    :type images_tuples_list: list[tuple[PIL.Image, str]]
    :returns: in memory zip
    """
    # In-memory ZIP creation
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for img, filename in images_tuples_list:
            buffer = io.BytesIO()
            img.save(buffer, format=img_format)
            buffer.seek(0)
            zipf.writestr(filename, buffer.read())

    # Reset buffer pointer
    zip_buffer.seek(0)
    return zip_buffer


def create_links_and_images(waypoints):
    """
    Display google maps links and return

    :param images_tuples_list: List of tuples of Pillow images and associated path string
    :type images_tuples_list: list[tuple[PIL.Image, str]]
    :returns: in memory zip
    """
    pass


qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=2,
    border=1,
)

font = ImageFont.load_default()
font.size = font_size


uploaded_file = st.file_uploader("Choose a GPX file")
if uploaded_file is not None:
    gpx = gpxpy.parse(uploaded_file)
    gpx_stem = Path(uploaded_file.name).stem

    images_list = []

    with st.expander("Google map links"):

        for wp in gpx.waypoints:
            url = url_template.format(wp=wp, gpx_stem=gpx_stem)
            title = title_template.format(wp=wp, gpx_stem=gpx_stem)
            img_stem = img_stem_template.format(wp=wp, gpx_stem=gpx_stem)

            st.markdown(
                f'{title}: <a href="{url}" target="_blank">{url}</a>',
                unsafe_allow_html=True,
            )

            # create qr code image
            qr.add_data(url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert(
                "RGB"
            )
            qr_img = qr_img.resize((img_width, img_height))

            # size of the text
            text_bbox = font.getbbox(title)
            title_width = text_bbox[2] - text_bbox[0]
            title_height = text_bbox[3] - text_bbox[1]

            qr_width, qr_height = qr_img.size

            # Add padding
            new_height = qr_height + title_height + title_padding
            new_img = Image.new("RGB", (qr_width, new_height), "white")
            # Paste the QR code into the new image
            new_img.paste(qr_img, (0, 0))

            # Add the text
            draw = ImageDraw.Draw(new_img)
            # Center the text horizontally
            text_x = (qr_width - title_width) // 2
            # Place the text below the QR code with padding
            text_y = qr_height + title_padding // 2
            draw.text((text_x, text_y), title, fill="black", font=font)

            images_list.append((new_img, f"{img_stem}.{img_format}"))

            qr.clear()

    with st.expander("QR codes"):
        st.image([img for img, _ in images_list], output_format=img_format)

    # Generate the ZIP file on the fly
    zip_file = create_zip(images_list)

    # Prompt download
    st.download_button(
        label="Download ZIP of QR codes",
        data=zip_file,
        file_name="qr_codes.zip",
        mime="application/zip",
    )
