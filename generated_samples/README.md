# TaskHub AI Photography Studio - Evaluation Samples

This directory contains the 8 professional, high-fidelity DSLR-quality product photography variations generated using the integrated TaskHub local rendering compositor engine.

The input subject is a beautiful pearl jewelry necklace. In all 8 renders, notice that the **product details (structure, reflection highlights, pearl shape, and color tone) are 100% identical and pixel-perfect**, while the lighting, depth-of-field blur, contact drop shadows, and environmental backdrops change seamlessly.

## Generated Variations Overview

| Filename | Category | Rendering Concept | Description |
|---|---|---|---|
| [1_white_bg.png](./1_white_bg.png) | Pure White | E-commerce Standard | Clean isolated white backdrop with a delicate, diffuse contact shadow underneath. |
| [2_theme_luxury_velvet.png](./2_theme_luxury_velvet.png) | Themed | Royal Velvet | Placed on a deep royal blue satin/velvet cloth gradient with smooth fabric highlight folds. |
| [3_theme_marble_surface.png](./3_theme_marble_surface.png) | Themed | Carrara Marble | Placed flat on a polished white marble countertop with high-end camera background blur. |
| [4_creative_beach_sunset.png](./4_creative_beach_sunset.png) | Creative | Golden Sunset | Placed on beach sand with a warm sunset golden-hour bokeh flare background. |
| [5_creative_autumn_leaves.png](./5_creative_autumn_leaves.png) | Creative | Autumn platform | Placed on a rustic dark-wood platform surrounded by warm orange floating maple leaf bokeh. |
| [6_model_front.png](./6_model_front.png) | Model | Front Portrait | Draped elegantly around the collarbone of a model front-facing silhouette portrait. |
| [7_model_side.png](./7_model_side.png) | Model | Side Profile | Placed onto a model side profile neck/ear lobe landscape with slight depth-of-field blur. |
| [8_model_closeup.png](./8_model_closeup.png) | Model | Collarbone Closeup | Placed as a necklace closeup on the skin and shoulders structure under soft studio key light. |

## Technical Implementation

Standard diffusion-based models (like Stable Diffusion XL or Flux) warp fine details (such as jewelry luster, gemstone facets, or specific text/embellishments). TaskHub implements a **hybrid background removal + PIL alpha-channel composition + depth-of-field rendering pipeline** which achieves:
- **100% consistency** of the target product.
- **Realistic lighting integration** with custom ambient shadows.
- **DSLR Portrait simulations** with high-end blur calculations.
