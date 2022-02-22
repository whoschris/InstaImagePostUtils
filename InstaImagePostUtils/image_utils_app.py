from flask import render_template, request, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest, InternalServerError
import os
import InstaImagePostUtils
from .util import create_fill, COLOR_DICT, MAX_AR, MIN_AR, split_pano, calculate_dimensions
from PIL import Image


@InstaImagePostUtils.app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@InstaImagePostUtils.app.route("/settings", methods=["POST"])
def settings():
    if "img" not in request.files :
        return "No image submitted", 400
    img = request.files["img"]
    ext = os.path.splitext(img.filename)[1]
    if not img.filename or ext.lower() not in InstaImagePostUtils.ALLOWED_EXTENSIONS:
        return "No image submitted", 400

    if img:
        uuid = InstaImagePostUtils.calculate_uuid(img.stream)
        img_dir = InstaImagePostUtils.get_img_dir(uuid)

        try:
            os.mkdir(img_dir)
        except FileExistsError:
            raise InternalServerError
        s_filename = secure_filename(img.filename)
        new_filepath = os.path.join(img_dir, s_filename)
        img.save(new_filepath)
        pil_img = Image.open(new_filepath)
        width = pil_img.width
        height = pil_img.height

        # Create thumbnail
        s_filename_parts = os.path.splitext(s_filename)
        s_filename_thumbnail = f"{s_filename_parts[0]}-thumbnail{s_filename_parts[1]}"
        pil_img.thumbnail((600, 600), Image.ANTIALIAS)
        pil_img.save(os.path.join(img_dir, s_filename_thumbnail))
        InstaImagePostUtils.app.logger.info(f"Uploaded {s_filename} to {uuid}")

    try:
        if request.form["option"] == "Split Panorama":
            option = InstaImagePostUtils.ImageOption.SPLIT
        elif request.form["option"] == "Crop and Fill":
            option = InstaImagePostUtils.ImageOption.FILL
    except KeyError:
        raise BadRequest

    return render_template("settings.html",
                           uuid=uuid,
                           filename=s_filename,
                           filename_thumbnail=s_filename_thumbnail,
                           option=option.name,
                           im_width=width,
                           im_height=height,
                           min_ar=MIN_AR,
                           max_ar=MAX_AR,
                           thumbnail_width=pil_img.width)


@InstaImagePostUtils.app.route("/results", methods=["POST"])
def get_results():
    try:
        uuid = request.form["uuid"]
        filename = request.form["filename"]
        img_dir = os.path.join(InstaImagePostUtils.get_img_dir(uuid))
        filename_parts = os.path.splitext(filename)
        option = request.form["option"]
    except KeyError:
        raise BadRequest

    output_images = []
    if option == "FILL":
        try:
            s = request.form["output-ar"].split("-")
            output_ar = float(s[0])/float(s[1])
            bg_type = request.form["background"]
            blur_pt = int(request.form["blur-pt"])
        except (KeyError, ValueError, IndexError, ZeroDivisionError):
            raise BadRequest
        if bg_type == "bg-white":
            new_filename = f"{filename_parts[0]}-{s[0]}_{s[1]}-white{filename_parts[1]}"
            create_fill(
                os.path.join(img_dir, filename),
                output_ar,
                os.path.join(img_dir, new_filename),
                color=COLOR_DICT["white"]
            )
        elif bg_type == "bg-black":
            new_filename = f"{filename_parts[0]}-{s[0]}_{s[1]}-black{filename_parts[1]}"
            create_fill(
                os.path.join(img_dir, filename),
                output_ar,
                os.path.join(img_dir, new_filename),
                color=COLOR_DICT["black"]
            )
        elif bg_type == "bg-blur":
            new_filename = f"{filename_parts[0]}-{s[0]}_{s[1]}-blur-{blur_pt}{filename_parts[1]}"
            create_fill(
                os.path.join(img_dir, filename),
                output_ar,
                os.path.join(img_dir, new_filename),
                blur=blur_pt/100.0
            )
        output_images.append(new_filename)
    elif option == "SPLIT":
        try:
            num_output = int(request.form["n-split"])
            lb_type = request.form["letterbox"]
        except(ValueError, KeyError):
            raise BadRequest

        for i in range(1, num_output+1):
            output_images.append(f"{filename_parts[0]}-split-pano-{i}{filename_parts[1]}")

        dim = split_pano(os.path.join(img_dir, filename), num_output, img_dir, output_images)
        split_ar = dim["split_width"]/dim["height"]

        if lb_type == "lb-black":
            new_filename = f"{filename_parts[0]}-pano-box-black{filename_parts[1]}"
            create_fill(
                os.path.join(img_dir, filename),
                split_ar,
                os.path.join(img_dir, new_filename),
                color=COLOR_DICT["black"]
            )
            output_images.append(new_filename)
        elif lb_type == "lb-white":
            new_filename = f"{filename_parts[0]}-pano-box-white{filename_parts[1]}"
            create_fill(
                os.path.join(img_dir, filename),
                split_ar,
                os.path.join(img_dir, new_filename),
                color=COLOR_DICT["white"]
            )
            output_images.append(new_filename)

    InstaImagePostUtils.app.logger.info(f"Creating output images for {uuid}")
    return render_template("results.html", uuid=uuid, output_images=output_images)

# Handled by nginx in production
@InstaImagePostUtils.app.route("/display/<uuid>/<filename>")
def display_image(uuid, filename):
    return send_from_directory(
        InstaImagePostUtils.app.config["UPLOAD_FOLDER"], uuid + "/" + filename
    )