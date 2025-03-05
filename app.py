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

# Load environment variables from .env file for local development
load_dotenv()

# Try to get the token from either Streamlit secrets or environment variables
replicate_api_token = os.getenv('REPLICATE_API_TOKEN') or st.secrets.get('REPLICATE_API_TOKEN')

if not replicate_api_token:
    raise ValueError("No REPLICATE_API_TOKEN found in environment")

os.environ['REPLICATE_API_TOKEN'] = replicate_api_token

# Create a directory for saving videos if it doesn't exist
if os.getenv("STREAMLIT_SHARING"):
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
    # Set page config with a more modern layout
    st.set_page_config(
        page_title="Kling AI Video Generator",
        page_icon="🎬",
        layout="wide"
    )

    # Add custom CSS for better styling
    st.markdown("""
        <style>
        /* Main content area */
        .main {
            padding: 2rem;
        }
        
        /* Fix sidebar width and remove collapse functionality */
        [data-testid="stSidebar"] {
            min-width: 25% !important;
            width: 25% !important;
            height: 100vh !important;
            position: relative !important;
        }
        
        [data-testid="stSidebarContent"] {
            height: 100vh !important;
        }
        
        /* Remove sidebar navigation and collapse button */
        [data-testid="stSidebarNavItems"] {
            display: none !important;
        }
        
        section[data-testid="stSidebarUserContent"] {
            height: 100%;
            padding-top: 1.5rem;
        }
        
        /* Adjust main content area */
        .main .block-container {
            padding: 2rem 1rem 1rem 2rem !important;
            max-width: 75% !important;
        }
        
        /* Rest of your existing button and grid styles */
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            height: 3em;
            background-color: #FF4B4B;
            color: white;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #FF6B6B;
            border-color: #FF4B4B;
        }
        .video-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            padding: 1rem 0;
        }
        .video-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 0.5rem;
            background: white;
        }
        .video-timestamp {
            font-size: 0.8em;
            color: #666;
            margin-top: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Main content area with better organization
    st.title("🎬 Kling AI Video Generator")
    st.markdown("""
        Transform your images into amazing videos using AI technology.
        Upload an image and customize your generation parameters to get started!
    """)

    # Organize sidebar with clear sections
    with st.sidebar:
        tab1, tab2 = st.tabs(["Generator", "History"])
        
        with tab1:
            st.header("🎮 Generation Controls")
            
            uploaded_file = st.file_uploader(
                "Upload Start Image",
                type=['png', 'jpg', 'jpeg'],
                help="Upload a clear, high-quality image to start with"
            )
            
            start_image_url = None
            if uploaded_file is not None:
                try:
                    # Convert the uploaded file to bytes
                    image_bytes = uploaded_file.getvalue()
                    image = Image.open(BytesIO(image_bytes))
                    
                    # Convert image to RGB if it's in RGBA mode
                    if image.mode == 'RGBA':
                        image = image.convert('RGB')
                    
                    # Display the preview
                    st.image(image, caption="Preview", use_container_width=True)
                    
                    # Convert to base64
                    start_image_url = image_to_base64(image)
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")
                    return
            
            prompt = st.text_area(
                "✨ Prompt",
                placeholder="Describe what you want to generate...",
                help="Be specific and detailed in your description"
            )

            duration = st.selectbox(
                "⏱️ Duration",
                options=[5, 10],
                index=0,
                help="Select video duration in seconds"
            )
            
            cfg_scale = st.slider(
                "🎯 CFG Scale",
                min_value=0.1,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="Controls how closely the AI follows your prompt"
            )
            
            aspect_ratio = st.selectbox(
                "📐 Aspect Ratio",
                options=["16:9", "9:16", "1:1"],
                index=0
            )
            
            negative_prompt = st.text_area(
                "❌ Negative Prompt",
                placeholder="What should the AI avoid?",
                help="Specify elements you don't want in the video"
            )

            generate_button = st.button(
                "🚀 Generate Video",
                use_container_width=True,
                type="primary"
            )

        with tab2:
            st.header("📚 Generation History")
            if os.path.exists(SAVE_DIR):
                videos = [f for f in os.listdir(SAVE_DIR) if f.endswith('.mp4')]
                videos.sort(reverse=True)  # Sort by timestamp descending
                
                if videos:
                    st.markdown('<div class="video-grid">', unsafe_allow_html=True)
                    cols = st.columns(3)
                    for idx, video in enumerate(videos):
                        col = cols[idx % 3]
                        with col:
                            video_path = os.path.join(SAVE_DIR, video)
                            timestamp = datetime.datetime.strptime(
                                video.replace('kling_video_', '').replace('.mp4', ''),
                                "%Y%m%d_%H%M%S"
                            )
                            
                            st.video(video_path)
                            st.markdown(f"<div class='video-timestamp'>{timestamp.strftime('%B %d, %Y %H:%M:%S')}</div>",
                                      unsafe_allow_html=True)
                else:
                    st.info("🎬 No previous generations found")

    # Main content area for results
    if generate_button:
        if not uploaded_file:
            st.error("⚠️ Please upload an image to continue")
            return
            
        with st.status("🎥 Generating your video...") as status:
            status.update(label="🤖 AI is processing your request...")
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
                
                if output:
                    status.update(label="✅ Generation complete!", state="complete")
                    
                    if isinstance(output, str) and (output.startswith('http://') or output.startswith('https://')):
                        saved_path = save_video(output)
                        
                        if saved_path:
                            # Create a container for the result
                            result_container = st.container()
                            
                            with result_container:
                                st.success("🎉 Your video has been generated successfully!")
                                
                                # Create columns for preview and details
                                preview_col, details_col = st.columns([3, 1])
                                
                                with preview_col:
                                    st.subheader("📺 Preview")
                                    st.video(saved_path)
                                
                                with details_col:
                                    st.subheader("📊 Details")
                                    st.markdown(f"**Duration:** {duration} seconds")
                                    st.markdown(f"**Aspect Ratio:** {aspect_ratio}")
                                    st.markdown(f"**CFG Scale:** {cfg_scale}")
                                    
                                    # Download button
                                    with open(saved_path, "rb") as file:
                                        st.download_button(
                                            label="📥 Download Video",
                                            data=file,
                                            file_name=os.path.basename(saved_path),
                                            mime="video/mp4",
                                            use_container_width=True
                                        )
                                
                                # Show prompts used
                                st.subheader("🎯 Generation Parameters")
                                st.markdown(f"**Prompt:** {prompt}")
                                if negative_prompt:
                                    st.markdown(f"**Negative Prompt:** {negative_prompt}")
                    else:
                        st.write("Output:", output)
                
            except Exception as e:
                st.error(f"🚫 An error occurred: {str(e)}")
                status.update(label="Generation failed", state="error")

if __name__ == "__main__":
    main() 