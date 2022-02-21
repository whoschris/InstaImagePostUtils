from PIL import Image, ImageFilter
import click
import os
from math import isclose
from typing import List, Tuple, Any, Dict

# Max and minimum aspect ratios for Instagram
MAX_AR = 1.91  # 16:9
MIN_AR = 0.8  # 4:5

# Maximum image size on Instagram
MAX_IMAGE_SIZE = (1080, 1350)

AR_DICT = {
    1: 4 / 5,
    2: 1,
    3: 5 / 4,
    4: 3 / 2,
    5: 16 / 9,
}

COLOR_DICT = {
    "black": (0, 0, 0),
    "white": (255, 255, 255)
}


def confirm_existing_files(files: List) -> None:
    click.echo("Waring: The following files already exist in the directory:")
    for file in sorted(files):
        click.echo("\t" + file)
    click.confirm("Do you want to continue?", abort=True)


def list_output_dir(dir: str) -> List:
    return [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]


def create_output_filename(input_image_path: str, output_suffix: str) -> str:
    _, input_image_filename_ext = os.path.split(input_image_path)
    filename, ext = os.path.splitext(input_image_filename_ext)
    output_file = f"{filename}{output_suffix}{ext}"
    return output_file

def create_blur_background(im: Image, size_bg: Tuple, blur_pt: float) -> Image:
    w_bg = size_bg[0]
    h_bg = size_bg[1]
    ar_bg = w_bg / h_bg
    ar_im = im.width / im.height

    # Crop input image to match the output image size
    if ar_bg < ar_im:
        # Crop sides if the input is wider than the background
        crop_tot = round(im.width - ar_bg * im.height)
        crop_l = crop_tot // 2
        im2 = im.resize(size_bg, box=(
            crop_l,
            0,
            crop_l + ar_bg * im.height,
            im.height
        ))
    else:
        # Crop top and bottom if the input is taller than the background
        crop_tot = round(im.height - (im.width / ar_bg))
        crop_top = crop_tot // 2
        im2 = im.resize(size_bg, box=(
            0,
            crop_top,
            im.width,
            crop_top + im.width / ar_bg
        ))

    # Apply blur
    max_blur = max(im.height, im.width) / 10
    blur_radius = round(max_blur * blur_pt)
    print(f"Using blur radius of {blur_radius}.")
    bg = im2.filter(filter=ImageFilter.GaussianBlur(radius=blur_radius))

    return bg


def create_fill(input_image_path: str, ar_output: float, output_image_path: str, color: Tuple = (255, 255, 255),
                blur: float = None) -> None:
    # Output image is written to the same directory

    im = Image.open(input_image_path)
    ar_input = im.width / im.height

    # Use input image width if the output is "taller" than the input
    # Use input image height if the output is "wider" than the input
    if isclose(ar_output, ar_input, rel_tol=0.01):
        print("Input and output aspect ratios are witin 1% of each other. Exiting...")
        exit(0)
    elif ar_output < ar_input:
        # output image is  taller, use input width for canvas width
        w_output = im.width
        h_output = round(im.width / ar_output)
    else:
        # output image is wider, use input height for canvas height
        h_output = im.height
        w_output = round(ar_output * im.height)

    if blur is None:
        bg = Image.new("RGB", (w_output, h_output), color=color)
    elif 0 < blur <= 1:
        bg = create_blur_background(im, (w_output, h_output), blur)
    else:
        raise ValueError("Invalid blur amount. Must be between 0 and 1.")

    # past image in center
    if ar_output < ar_input:
        border_tot = h_output - im.height
        border_top = border_tot // 2
        bg.paste(im, box=(
            0,
            border_top,
            im.width,
            border_top + im.height,
        ))
    else:
        border_tot = w_output - im.width
        border_l = border_tot // 2
        bg.paste(im, box=(
            border_l,
            0,
            border_l + im.width,
            im.height
        ))

    bg.save(output_image_path, quality=95, icc_profile=im.info.get('icc_profile'))


def calculate_dimensions(width: int, n: int) -> Dict[str, Any]:
    offset = width % n
    left_trim = offset // 2
    right_trim = offset // 2
    if offset % 2:
        right_trim += 1
    new_width = width - offset
    assert(left_trim + right_trim == offset)
    assert(new_width % n == 0)
    return {
        "width": new_width,
        "left_trim": left_trim,
        "right_trim": right_trim,
        "split_width": new_width / n
    }


def split_pano(input_image_path: str, num_output_images: int, output_image_dir: str, output_image_filenames: List) \
        -> Dict[str, Any]:
    assert(len(output_image_filenames) == num_output_images)
    # This assumes that output AR has been checked already
    img = Image.open(input_image_path)
    dim = calculate_dimensions(img.width, num_output_images)
    split_width = dim["split_width"]
    left_trim = dim["left_trim"]
    split_ar = split_width/ img.height

    for i in range(0, num_output_images):
        x = left_trim + i * split_width
        box = (x, 0, x + split_width, img.height)
        img_section = img.crop(box)
        img_section.save(os.path.join(output_image_dir, output_image_filenames[i]),
                         quality=95,
                         icc_profile=img.info.get('icc_profile'))

    dim["height"] = img.height
    return dim
