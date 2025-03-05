import streamlit as st
import replicate
import os
from dotenv import load_dotenv
from PIL import Image
import requests
from io import BytesIO
import base64
import tempfile
import datetime

# Load environment variables from .env file in development
if os.path.exists(".env"):
    load_dotenv()

# Get API token from environment
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
if not REPLICATE_API_TOKEN:
    raise ValueError("No REPLICATE_API_TOKEN found in environment")

# Modify the SAVE_DIR logic
if os.getenv("STREAMLIT_SHARING") or os.getenv("RAILWAY_STATIC_URL"):
    # Use temporary directory for cloud deployment
    SAVE_DIR = tempfile.mkdtemp()
else:
    # Local development
    SAVE_DIR = "generated_videos"
    os.makedirs(SAVE_DIR, exist_ok=True)

def load_image(image_url):
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None

def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def save_video(video_url):
    try:
        # Download the video
        response = requests.get(video_url)
        if response.status_code == 200:
            # Generate unique filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"kling_video_{timestamp}.mp4"
            filepath = os.path.join(SAVE_DIR, filename)
            
            # Save the video
            with open(filepath, "wb") as f:
                f.write(response.content)
            return filepath
        return None
    except Exception as e:
        st.error(f"Error saving video: {e}")
        return None

def main():
    # Set page config
    st.set_page_config(
        page_title="Kling AI Interface",
        layout="wide"
    )

    # Sidebar inputs
    st.sidebar.title("Input Parameters")
    
    prompt = st.sidebar.text_area(
        "Prompt",
        "Reflections in crystal mirrors, rainbow light, geometric world"
    )
    
    duration = st.sidebar.slider(
        "Duration",
        min_value=1,
        max_value=10,
        value=5
    )
    
    cfg_scale = st.sidebar.slider(
        "CFG Scale",
        min_value=0.1,
        max_value=1.0,
        value=0.5,
        step=0.1
    )
    
    # Replace text input with file uploader
    st.sidebar.markdown("### Upload Start Image")
    uploaded_file = st.sidebar.file_uploader("Choose an image...", type=['png', 'jpg', 'jpeg'])
    start_image_url = None
    
    # Preview uploaded image
    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            st.sidebar.image(image, caption="Uploaded Image", use_column_width=True)
            start_image_url = image_to_base64(image)
        except Exception as e:
            st.sidebar.error(f"Error processing image: {e}")
    else:
        # Default image URL as fallback
        start_image_url = "https://replicate.delivery/pbxt/MNRLOqN0ASEzIG3YPuv9R1JSVGsSOQQzE3rgtVD9Qk230Lgt/image_fx_%20%285%29.jpg"
    
    aspect_ratio = st.sidebar.selectbox(
        "Aspect Ratio",
        ["16:9", "4:3", "1:1"]
    )
    
    negative_prompt = st.sidebar.text_area(
        "Negative Prompt",
        ""
    )

    # Main content area
    st.title("Kling AI Generator")

    if st.sidebar.button("Generate"):
        if not uploaded_file and start_image_url == "":
            st.error("Please upload an image or provide an image URL")
            return
            
        with st.spinner("Generating video... Please wait"):
            try:
                output = replicate.run(
                    "kwaivgi/kling-v1.6-pro",
                    input={
                        "prompt": prompt,
                        "duration": duration,
                        "cfg_scale": cfg_scale,
                        "start_image": start_image_url,
                        "aspect_ratio": aspect_ratio,
                        "negative_prompt": negative_prompt
                    }
                )
                
                # Display the result
                if output:
                    st.success("Generation complete!")
                    
                    # If output is a URL, save and display the video
                    if isinstance(output, str) and (output.startswith('http://') or output.startswith('https://')):
                        # Save the video
                        saved_path = save_video(output)
                        
                        if saved_path:
                            st.success(f"Video saved to: {saved_path}")
                            
                            # Display the video
                            st.video(saved_path)
                            
                            # Add download button
                            with open(saved_path, "rb") as file:
                                btn = st.download_button(
                                    label="Download Video",
                                    data=file,
                                    file_name=os.path.basename(saved_path),
                                    mime="video/mp4"
                                )
                    else:
                        st.write("Output:", output)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # Display list of previously generated videos
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Previously Generated Videos")
    if os.path.exists(SAVE_DIR):
        videos = [f for f in os.listdir(SAVE_DIR) if f.endswith('.mp4')]
        if videos:
            selected_video = st.sidebar.selectbox(
                "Select a previous video",
                videos,
                format_func=lambda x: x.replace('kling_video_', '').replace('.mp4', '')
            )
            if selected_video:
                video_path = os.path.join(SAVE_DIR, selected_video)
                st.sidebar.video(video_path)
        else:
            st.sidebar.info("No previously generated videos found")

if __name__ == "__main__":
    main() 