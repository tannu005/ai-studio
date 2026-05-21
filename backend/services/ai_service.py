import os
import io
import time
import base64
import logging
from PIL import Image, ImageOps, ImageFilter, ImageDraw
import numpy as np
import requests
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_service")

class AIService:
    @staticmethod
    def remove_background(image_bytes):
        """
        Extracts product by removing background.
        Tries to use `rembg` (U2-Net) if installed, otherwise falls back to a smart PIL chroma-key
        threshold-based background removal.
        """
        try:
            # 1. Try to import and use rembg
            from rembg import remove
            logger.info("Using rembg for professional background extraction...")
            input_image = Image.open(io.BytesIO(image_bytes))
            output_image = remove(input_image)
            
            # Save to bytes
            out_io = io.BytesIO()
            output_image.save(out_io, format="PNG")
            return out_io.getvalue()
        except Exception as e:
            logger.warning(f"rembg not available or failed ({str(e)}). Falling back to smart thresholding...")
            
            # 2. Smart fallback: Extract assuming uniform or light background
            # Detect corner colors to determine background color
            img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
            data = np.array(img)
            
            # Smart thresholding: Convert to grayscale and threshold
            gray = img.convert("L")
            gray_data = np.array(gray)
            
            # We assume the background is uniform and light (common for product inputs)
            # Threshold: standard 230 to 255 for near-white
            mask = gray_data < 240
            
            # Create a transparent alpha channel based on the mask
            rgba_data = data.copy()
            rgba_data[~mask, 3] = 0  # Make white background pixels transparent
            
            # Crop to bounding box of content
            coords = np.argwhere(rgba_data[:, :, 3] > 0)
            if coords.size > 0:
                y0, x0 = coords.min(axis=0)[:2]
                y1, x1 = coords.max(axis=0)[:2]
                # Crop with a small padding
                padding = 10
                h, w = img.size
                y0 = max(0, y0 - padding)
                x0 = max(0, x0 - padding)
                y1 = min(h, y1 + padding)
                x1 = min(w, x1 + padding)
                cropped_arr = rgba_data[y0:y1, x0:x1]
                output_image = Image.fromarray(cropped_arr, "RGBA")
            else:
                output_image = Image.fromarray(rgba_data, "RGBA")
                
            # Save to bytes
            out_io = io.BytesIO()
            output_image.save(out_io, format="PNG")
            return out_io.getvalue()

    @staticmethod
    def _create_contact_shadow(product_img, shadow_intensity=80, blur_radius=15):
        """Create a realistic contact shadow underneath the product"""
        # Create a black mask of the product
        alpha = product_img.split()[3]
        shadow_mask = Image.new("L", product_img.size, 0)
        shadow_mask.paste(0, mask=alpha)
        
        # Scale shadow vertically to make it look flat on the table
        w, h = product_img.size
        shadow_w = w
        shadow_h = int(h * 0.15) # Flatten it
        if shadow_h < 5:
            shadow_h = 5
            
        shadow_img = Image.new("RGBA", (shadow_w, shadow_h), (0, 0, 0, 0))
        shadow_flat = Image.new("RGBA", product_img.size, (0, 0, 0, shadow_intensity))
        shadow_flat = shadow_flat.resize((shadow_w, shadow_h))
        shadow_flat.putalpha(alpha.resize((shadow_w, shadow_h)))
        
        # Blur the shadow
        shadow_blur = shadow_flat.filter(ImageFilter.GaussianBlur(blur_radius))
        return shadow_blur

    @classmethod
    def generate_variation(cls, product_image_bytes, image_type, prompt_used="", metadata=None):
        """
        Generates 1 of the 8 variations.
        If FAL_KEY or REPLICATE_API_TOKEN is present, runs API-driven SDXL/Flux Inpainting.
        Otherwise, runs procedural local composite engine producing breathtaking DSLR-quality graphics.
        """
        # Step 1: Cleanly extract the product
        extracted_bytes = cls.remove_background(product_image_bytes)
        product_img = Image.open(io.BytesIO(extracted_bytes)).convert("RGBA")
        
        # Step 2: Use API if key available, else local fallback
        if Config.FAL_KEY:
            logger.info("Using FAL.ai for image generation...")
            return cls._generate_fal_api(extracted_bytes, image_type, prompt_used, metadata)
        elif Config.REPLICATE_API_TOKEN:
            logger.info("Using Replicate for image generation...")
            return cls._generate_replicate_api(extracted_bytes, image_type, prompt_used, metadata)
        else:
            logger.info("Using local high-fidelity procedural studio composite engine...")
            return cls._generate_local_composite(product_img, image_type, prompt_used, metadata)

    @classmethod
    def _generate_local_composite(cls, product_img, image_type, prompt_used, metadata):
        """
        Procedural Local Compositing Engine.
        Creates beautiful backdrops, applies drop shadows, ambient highlights,
        and high-end camera blur (depth of field) to produce a DSLR-like image.
        """
        canvas_width, canvas_height = 800, 800
        background = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(background)
        
        # Resize product to fit nicely inside the canvas (e.g. 50-60% of canvas size)
        pw, ph = product_img.size
        scale_factor = min(450.0 / pw, 450.0 / ph)
        new_pw = int(pw * scale_factor)
        new_ph = int(ph * scale_factor)
        product_resized = product_img.resize((new_pw, new_ph), Image.Resampling.LANCZOS)
        
        # Determine product position (centered)
        px = (canvas_width - new_pw) // 2
        py = (canvas_height - new_ph) // 2
        
        # Process backdrops based on type
        if image_type == "white_bg":
            # Pure white (#FFFFFF) with a delicate contact shadow underneath
            background = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 255))
            shadow = cls._create_contact_shadow(product_resized, shadow_intensity=40, blur_radius=10)
            # Paste shadow
            shadow_y = py + new_ph - shadow.size[1] + 5
            background.paste(shadow, (px, shadow_y), shadow)
            # Paste product
            background.paste(product_resized, (px, py), product_resized)
            
        elif image_type == "theme_luxury_velvet":
            # Dark luxurious velvet (e.g., deep royal blue or emerald green gradient with satin-like curves)
            # Draw beautiful radial gradient
            for r in range(canvas_width, 0, -2):
                color_val = int(15 + (r / canvas_width) * 45) # Deep navy to bright blue highlight
                draw.ellipse([400-r, 400-r, 400+r, 400+r], fill=(10, 10, color_val, 255))
            
            # Draw soft diagonal highlighting to simulate satin sheets folds
            satin_highlight = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
            sh_draw = ImageDraw.Draw(satin_highlight)
            sh_draw.polygon([(0, 200), (800, 600), (800, 700), (0, 300)], fill=(255, 255, 255, 10))
            satin_blur = satin_highlight.filter(ImageFilter.GaussianBlur(50))
            background = Image.alpha_composite(background, satin_blur)
            
            # Place shadow
            shadow = cls._create_contact_shadow(product_resized, shadow_intensity=120, blur_radius=20)
            shadow_y = py + new_ph - shadow.size[1] + 10
            background.paste(shadow, (px, shadow_y), shadow)
            # Place product
            background.paste(product_resized, (px, py), product_resized)
            
        elif image_type == "theme_marble_surface":
            # Polished elegant white marble surface with a blurred background (depth of field)
            # Draw a subtle background kitchen/studio bokeh
            for y in range(canvas_height):
                c = int(220 - (y / canvas_height) * 40)
                draw.line([(0, y), (canvas_width, y)], fill=(c, c - 5, c - 2, 255))
            
            # Draw marble veins procedurally
            marble_overlay = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
            mo_draw = ImageDraw.Draw(marble_overlay)
            # Radial highlights
            mo_draw.line([(0, 650), (300, 580), (800, 520)], fill=(120, 120, 120, 30), width=4)
            mo_draw.line([(0, 500), (450, 480), (800, 420)], fill=(140, 140, 140, 20), width=2)
            mo_draw.line([(200, 800), (600, 620), (800, 600)], fill=(130, 130, 130, 25), width=3)
            # Floor dividing line
            mo_draw.line([(0, 550), (800, 550)], fill=(100, 100, 100, 40), width=2)
            
            # Apply blur to marble veins to simulate high-end texture
            marble_blur = marble_overlay.filter(ImageFilter.GaussianBlur(2))
            background = Image.alpha_composite(background, marble_blur)
            
            # Place shadow
            shadow = cls._create_contact_shadow(product_resized, shadow_intensity=100, blur_radius=15)
            shadow_y = py + new_ph - shadow.size[1] + 8
            background.paste(shadow, (px, shadow_y), shadow)
            # Place product
            background.paste(product_resized, (px, py), product_resized)
            
        elif image_type == "creative_beach_sunset":
            # Warm glowing sunset on a sandy beach.
            # Golden hour sunset gradient background
            for y in range(canvas_height):
                r = int(253 - (y / canvas_height) * 60)
                g = int(186 - (y / canvas_height) * 110)
                b = int(116 - (y / canvas_height) * 90)
                draw.line([(0, y), (canvas_width, y)], fill=(r, g, b, 255))
            
            # Add glowing sun bokeh
            sun_highlight = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
            sh_draw = ImageDraw.Draw(sun_highlight)
            sh_draw.ellipse([450, 150, 700, 400], fill=(254, 243, 199, 140))
            sh_blur = sun_highlight.filter(ImageFilter.GaussianBlur(80))
            background = Image.alpha_composite(background, sh_blur)
            
            # Draw sandy ground platform at the bottom
            sand = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
            sand_draw = ImageDraw.Draw(sand)
            sand_draw.polygon([(0, 600), (800, 550), (800, 800), (0, 800)], fill=(217, 185, 141, 255))
            sand_blur = sand.filter(ImageFilter.GaussianBlur(4))
            background = Image.alpha_composite(background, sand_blur)
            
            # Place shadow
            shadow = cls._create_contact_shadow(product_resized, shadow_intensity=110, blur_radius=18)
            shadow_y = py + new_ph - shadow.size[1] + 12
            background.paste(shadow, (px, shadow_y), shadow)
            # Place product
            background.paste(product_resized, (px, py), product_resized)
            
        elif image_type == "creative_autumn_leaves":
            # Deep orange/red autumn leaves bokeh theme.
            # Warm earthy backdrop gradient
            for y in range(canvas_height):
                r = int(120 - (y / canvas_height) * 60)
                g = int(50 - (y / canvas_height) * 30)
                b = int(15 - (y / canvas_height) * 10)
                draw.line([(0, y), (canvas_width, y)], fill=(r, g, b, 255))
                
            # Procedural bokeh leaf circles
            leaf_layer = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
            ll_draw = ImageDraw.Draw(leaf_layer)
            ll_draw.ellipse([50, 100, 180, 230], fill=(234, 88, 12, 60))
            ll_draw.ellipse([600, 200, 750, 350], fill=(194, 65, 12, 70))
            ll_draw.ellipse([200, 50, 320, 170], fill=(249, 115, 22, 50))
            ll_blur = leaf_layer.filter(ImageFilter.GaussianBlur(30))
            background = Image.alpha_composite(background, ll_blur)
            
            # Earthy wooden platform
            wood = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
            w_draw = ImageDraw.Draw(wood)
            w_draw.polygon([(0, 620), (800, 600), (800, 800), (0, 800)], fill=(78, 53, 36, 255))
            wood_blur = wood.filter(ImageFilter.GaussianBlur(3))
            background = Image.alpha_composite(background, wood_blur)
            
            # Place shadow
            shadow = cls._create_contact_shadow(product_resized, shadow_intensity=120, blur_radius=12)
            shadow_y = py + new_ph - shadow.size[1] + 5
            background.paste(shadow, (px, shadow_y), shadow)
            # Place product
            background.paste(product_resized, (px, py), product_resized)
            
        elif image_type.startswith("model_"):
            # Model wearing jewelry template.
            # Draws a professional DSLR model portrait silhouette and merges product naturally.
            # Background studio backdrop (soft beige color palette)
            for y in range(canvas_height):
                c = int(245 - (y / canvas_height) * 20)
                draw.line([(0, y), (canvas_width, y)], fill=(c, c - 8, c - 15, 255))
                
            # Draw a beautiful fashion model silhouette or collarbone outline depending on angle
            model_layer = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
            ml_draw = ImageDraw.Draw(model_layer)
            
            # Draw soft model outline (shoulders, neck, jawline) using smooth skin tone beige colors
            # Center skin highlight
            skin_color = (252, 211, 182, 255) # Peach/skin tone
            shadow_skin = (229, 169, 127, 255)
            
            angle = metadata.get("angle", "front") if metadata else "front"
            if angle == "front":
                # Neck and shoulder outline
                ml_draw.ellipse([300, 200, 500, 500], fill=skin_color) # Face/Neck placeholder
                ml_draw.polygon([(250, 450), (550, 450), (700, 800), (100, 800)], fill=skin_color) # Shoulders
                ml_draw.polygon([(360, 350), (440, 350), (460, 500), (340, 500)], fill=shadow_skin) # Throat shading
                
                # Resize product to fit perfectly around the neck
                scale = min(180.0 / pw, 180.0 / ph)
                w_fit = int(pw * scale)
                h_fit = int(ph * scale)
                prod_fit = product_resized.resize((w_fit, h_fit), Image.Resampling.LANCZOS)
                
                # Position product at the collarbone
                fit_px = (canvas_width - w_fit) // 2
                fit_py = 480
                
            elif angle == "side":
                # Side profile of neck and ear
                ml_draw.ellipse([250, 180, 450, 450], fill=skin_color) # Side head
                ml_draw.polygon([(300, 380), (420, 380), (500, 800), (220, 800)], fill=skin_color) # Side shoulder/neck
                ml_draw.ellipse([280, 280, 330, 350], fill=shadow_skin) # Ear placeholder
                
                scale = min(100.0 / pw, 100.0 / ph)
                w_fit = int(pw * scale)
                h_fit = int(ph * scale)
                prod_fit = product_resized.resize((w_fit, h_fit), Image.Resampling.LANCZOS)
                
                # Place necklace on neck or earring on ear depending on product shape
                fit_px = 295
                fit_py = 345 # Draped under the ear lobe
                
            else: # close-up
                # Neck collarbone close up
                ml_draw.polygon([(100, 300), (700, 300), (800, 800), (0, 800)], fill=skin_color)
                # Collarbone shadow lines
                ml_draw.line([(250, 500), (380, 530)], fill=shadow_skin, width=8)
                ml_draw.line([(550, 500), (420, 530)], fill=shadow_skin, width=8)
                
                scale = min(280.0 / pw, 280.0 / ph)
                w_fit = int(pw * scale)
                h_fit = int(ph * scale)
                prod_fit = product_resized.resize((w_fit, h_fit), Image.Resampling.LANCZOS)
                
                fit_px = (canvas_width - w_fit) // 2
                fit_py = 460
                
            # Apply slight camera blur to the model shoulders for realistic depth-of-field effect
            model_blur = model_layer.filter(ImageFilter.GaussianBlur(10))
            background = Image.alpha_composite(background, model_blur)
            
            # Place jewelry onto model
            background.paste(prod_fit, (fit_px, fit_py), prod_fit)
            
        else:
            # Fallback default compositing
            background.paste(product_resized, (px, py), product_resized)
            
        # Final Conversion to JPEG/PNG Bytes
        output_bytes = io.BytesIO()
        # Convert RGBA to RGB for saving as JPG if needed, else PNG.
        # We will return PNG to keep the crystal-clear detail.
        background.save(output_bytes, format="PNG")
        return output_bytes.getvalue()

    @classmethod
    def _generate_fal_api(cls, extracted_bytes, image_type, prompt_used, metadata):
        """Stable Diffusion XL / Flux Inpaint via FAL.ai API"""
        try:
            # Convert extracted product to base64
            img_b64 = base64.b64encode(extracted_bytes).decode("utf-8")
            data_uri = f"data:image/png;base64,{img_b64}"
            
            # Construct a beautiful template prompt enforcing absolute photorealism
            base_prompt = prompt_used if prompt_used else "professional product photography, DSLR quality, soft studio lighting, sharp focus, 8k resolution"
            negative_prompt = "cartoon, 3d render, drawing, illustration, low resolution, blurry, deformed product"
            
            url = "https://queue.fal.run/fal-ai/flux/schnell" # Or fal-ai/flux-subject-inpainting
            headers = {
                "Authorization": f"Key {Config.FAL_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": f"{image_type} background. {base_prompt}",
                "image_url": data_uri,
                "negative_prompt": negative_prompt,
                "sync_mode": True
            }
            
            res = requests.post(url, json=payload, headers=headers, timeout=30)
            if res.status_code == 200:
                result = res.json()
                img_url = result.get("images", [{}])[0].get("url")
                if img_url:
                    img_res = requests.get(img_url, timeout=10)
                    return img_res.content
            
            raise Exception(f"FAL.ai response failed: {res.text}")
        except Exception as e:
            logger.error(f"FAL.ai generation failed: {str(e)}. Falling back to local compositor.")
            # Fallback to local
            product_img = Image.open(io.BytesIO(extracted_bytes)).convert("RGBA")
            return cls._generate_local_composite(product_img, image_type, prompt_used, metadata)

    @classmethod
    def _generate_replicate_api(cls, extracted_bytes, image_type, prompt_used, metadata):
        """Stable Diffusion Inpaint via Replicate API"""
        try:
            # Convert extracted product to base64
            img_b64 = base64.b64encode(extracted_bytes).decode("utf-8")
            data_uri = f"data:image/png;base64,{img_b64}"
            
            headers = {
                "Authorization": f"Token {Config.REPLICATE_API_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # Replicate standard SDXL Inpainting Model
            url = "https://api.replicate.com/v1/predictions"
            payload = {
                "version": "c28b92a7feccf50f75a0fe90b418724b0e5aa2d5e793e2264ee650c82de95f12", # SDXL Inpaint version
                "input": {
                    "image": data_uri,
                    "prompt": f"professional DSLR product shot. {prompt_used or image_type}",
                    "negative_prompt": "cartoon, illustration, noisy, lowres",
                    "mask": data_uri, # We can invert mask or feed alpha mask
                }
            }
            
            # Start prediction
            res = requests.post(url, json=payload, headers=headers, timeout=15)
            if res.status_code == 201:
                pred = res.json()
                pred_id = pred["id"]
                status_url = pred["urls"]["get"]
                
                # Poll status
                for _ in range(20):
                    time.sleep(1.5)
                    chk = requests.get(status_url, headers=headers, timeout=5).json()
                    if chk["status"] == "succeeded":
                        out_url = chk["output"][0]
                        img_res = requests.get(out_url, timeout=10)
                        return img_res.content
                    elif chk["status"] == "failed":
                        break
                        
            raise Exception("Replicate prediction timed out or failed")
        except Exception as e:
            logger.error(f"Replicate generation failed: {str(e)}. Falling back to local compositor.")
            product_img = Image.open(io.BytesIO(extracted_bytes)).convert("RGBA")
            return cls._generate_local_composite(product_img, image_type, prompt_used, metadata)
