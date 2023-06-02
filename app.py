import streamlit as st
from PIL import Image
import os
from streamlit_drawable_canvas import st_canvas
import base64
from io import BytesIO
from google.cloud import aiplatform

PROJECT_ID = os.environ.get("ENDPOINT_PROJECT_ID")
REGION = os.environ.get("ENDPOINT_REGION") 
ENDPOINT_ID = os.environ.get("ENDPOINT_ID")

def image_to_base64(image, format="JPEG"):
    buffer = BytesIO()
    image.save(buffer, format=format)
    image_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return image_str


def base64_to_image(image_str):
    image = Image.open(BytesIO(base64.b64decode(image_str)))
    return image


def run_inference(image, mask, prompt,endpoint_id):

    init_image = image
    mask_image = mask

    aiplatform.init(project=PROJECT_ID, location=REGION)
    endpoint = aiplatform.Endpoint(endpoint_id)

    instances = [
        {
            "prompt": prompt,
            "image": image_to_base64(init_image),
            "mask_image": image_to_base64(mask_image),
        },
    ]
    response = endpoint.predict(instances=instances)
    images = [base64_to_image(image) for image in response.predictions]

    return images


def run():
    print(f"-PROJECT_ID{PROJECT_ID}")
    print(f"ENDPOINT_REGION-{REGION}")
    print(f"ENDPOINT_ID-{ENDPOINT_ID}")
   
    st.title("Stable Diffusion Inpainting Demo")

    image = st.file_uploader("Image", ["jpg", "png"])
    if image:
        image = Image.open(image)
        w, h = image.size
        print(f"loaded input image of size ({w}, {h})")
        width, height = map(lambda x: x - x % 64, (w, h))  # resize to integer multiple of 32
        image = image.resize((width, height))

        prompt = st.text_input("Prompt")

        fill_color = "rgba(255, 255, 255, 0.0)"
        stroke_width = st.number_input("Brush Size",
                                       value=64,
                                       min_value=1,
                                       max_value=100)
        stroke_color = "rgba(255, 255, 255, 1.0)"
        bg_color = "rgba(0, 0, 0, 1.0)"
        drawing_mode = "freedraw"

        st.write("Canvas")
        st.caption(
            "Draw a mask to inpaint, then click the 'Send to Streamlit' button (bottom left, with an arrow on it).")
        canvas_result = st_canvas(
            fill_color=fill_color,
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_color=bg_color,
            background_image=image,
            update_streamlit=False,
            height=height,
            width=width,
            drawing_mode=drawing_mode,
            key="canvas",
        )
        if canvas_result:
            mask = canvas_result.image_data
            mask = mask[:, :, -1] > 0
            if mask.sum() > 0:
                mask = Image.fromarray(mask)

                result = run_inference(
                    image=image,
                    mask=mask,
                    prompt=prompt,
                    endpoint_id=ENDPOINT_ID
                )
                st.write("Inpainted")
                for image in result:
                    st.image(image, output_format='PNG')


if __name__ == "__main__":
    run()