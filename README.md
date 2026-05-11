<h1 align="center">
    🌐 Civitai Visual Browser Nodes by LX
    <br>
    <sub><sup><i>Get your Models and LoRAs visible, organised and sorted!</i></sup></sub>
    <br>
</h1>
<p align="center">
    <a href="#the-nodes">The Nodes</a> &nbsp; | &nbsp; <a href="#features">Features</a> &nbsp; | &nbsp; <a href="#installation">Installation</a> &nbsp; | &nbsp; <a href="#how-to-use">How to Use</a> &nbsp;
</p>
<hr>

## 📖 Description

**The ultimate visual browser for your local LoRAs and models!** Enjoy a deep Civitai data integration. Take full control of your local library by automatically showing Civitai preview images, loading trigger words, and diving into detailed metadata inspection. 

Stay organized with intelligent filtering, searching, and the ability to add personal notes to your favorite models. Perfect for content creators, it includes separated SFW and NSFW views to guarantee a safe interface for working, creating videos, or live streaming. 

*Finally, your `.safetensors` files become visible, saving you from scrolling through a dead and unfriendly endless list of models and LoRAs in the default loaders.*

---

<p> This is how the Visual Browser Nodes looks like, when you open them up, they are all similar:</p>

<img width="2048" height="1150" alt="Civitai Visual Lora Loader and Browser by LX" src="https://github.com/user-attachments/assets/21caf9e2-0162-483a-8340-f2de451dbb1d" />
<br>

---
## The Nodes

### 📦 What's included?
This suite provides 3 separate nodes:
- 🌐 **Civitai Visual LoRA Loader**
- 🌐 **Civitai Visual Checkpoint Model Loader**
- 🌐 **Civitai Visual Diffusion Model Loader**

<img width="1516" height="735" alt="The Nodes Civitai Visual Loaders and Browsers by LX" src="https://github.com/user-attachments/assets/fc1e2066-a4a2-4de1-a286-8a266b660c2e" />

<br>

---

Say goodbye to endless, confusing dropdown menus and hello to a sleek visual interface that lets you see exactly what you are loading:

<img width="1193" height="812" alt="image" src="https://github.com/user-attachments/assets/40272c1a-47e2-484f-9d38-013a0df95a0c" />

<br>

---

## Features

* **🖼️ Visual Grid Interface:** View your local models as a clean, responsive grid of thumbnails instead of text lists.
* **🔍 Quick Search:** Instantly filter your models by file name or folder.
* **🌐 Basic Civitai Integration:** Fetch the primary preview image, Base Model & LoRA info, and Trigger Words directly from Civitai.

<br>

* **📋 Advanced Hover Menus for preview image:** Copy Positive/Negative Prompts straight from preview images, download Civitai images directly, or instantly open local folders.
* **🖼️ Set your Own Cover:** Set your own preview image as cover for the Grid Interface.
* **➕ Add local image:** Easily add your own local images/videos and you can also set them as cover.

<br>

* **🗂️ View:** You can select the View by: File Name, Base Model Name, Preview Image.
* **🗃️ Filtering:** Filter by Base Models. You can seleu one or more to view.
* **🛑 NSFW Filter:** Basic toggle to hide or show NSFW content, it will not be reset by reset button or restart.

* **🙈 Global Individual Media Hiding:** Permanently blur out specific NSFW or annoying preview images with one click.

<br>

* **🎬 Full Media Gallery** View all preview images, videos, aimated webpics, GIFs and more.
* **🎬 Video Control:** Features a global Play/Pause "Zen Mode" that resets preview videos to Frame 0 to reduce visual clutter.
* **⌨️ Lightning-Fast Keyboard Navigation:** Surf through your models using the Arrow Keys or `W`, `A`, `S`, `D`.

---

## Installation

* **Method 1: ComfyUI Manager**<br>
  1. Open the "Manager".<br>
  2. Click on "Custom Nodes Manager".<br>
  3. Search for **"Civitai Visual Browser & Loader by LX"**.<br>
  4. Click Install and restart ComfyUI.

<img width="1892" height="938" alt="Preview_Video_Search_4" src="https://github.com/user-attachments/assets/6e1c84fe-7126-4728-bc19-15888ede376c" />

<br>

* **Method 2: Manual Installation**
  Navigate to your ComfyUI custom_nodes folder in your terminal/command prompt:

  ```bash
  #cd ComfyUI/custom_nodes
  #Clone my repository:
  git clone https://github.com/LX-ComfyUI/VisualBrowserNodes-by-LX.git

<br>

Restart ComfyUI!

---

## How to Use

Once installed, you can find the new nodes in your ComfyUI menu:

Right-click on the ComfyUI canvas (or double-click to search).

Search for any of the loaders:

🌐 Civitai Visual LoRA Loader by LX

🌐 Civitai Visual Checkpoint Model Loader by LX

🌐 Civitai Visual Diffusion Model Loader by LX

<img width="1892" height="938" alt="Preview_Video_Search" src="https://github.com/user-attachments/assets/554d9cd4-b731-4fae-8433-5569e5c84a6e" />

<br>

Click the big "🌐 Open Visual LoRA Browser" button on the node to launch the visual interface!

<img width="1892" height="938" alt="Preview_Video_Open_Browser_3" src="https://github.com/user-attachments/assets/8b09cbe9-9c43-4f9a-a614-c1ae60dd13a9" />

---

## First opening and loading data from Civitai:

<br>

1. Select a model by clicking on one of the boxes on the left side:

<br>

<img width="2524" height="1220" alt="image" src="https://github.com/user-attachments/assets/3a9cb993-a2e9-42f5-bfb8-f1f4bb258bb4" />

---

<br>

2. Once selected, the model is highlighted in blue. On the right side, you will see the model information panel, which is empty at first:

<br>

<img width="1618" height="1202" alt="image" src="https://github.com/user-attachments/assets/688bc75a-e4a0-4be6-b39a-efc81480fa96" />

---

<br>

3. Click the **Load Data from Civitai** Button:

<br>

<img width="1106" height="454" alt="image" src="https://github.com/user-attachments/assets/f47cdc96-c4f0-4f96-9b9c-6fd9ea875629" />

---

<br>

4. The data is successfully loaded! You can now see all the details for this specific model fetched directly from Civitai:

<br>

<img width="1892" height="948" alt="Preview_Video" src="https://github.com/user-attachments/assets/6d36ea33-d978-4f67-be6c-2b373e9e6c4d" />

---

<br>

5. Hover over the preview images to reveal detailed generation data (prompts, settings, etc.) showing exactly how each image or video was created:

<br>

<img width="1084" height="843" alt="image" src="https://github.com/user-attachments/assets/b832c53b-86c2-4040-9313-80d683e6a172" />

---

## Support & Feedback:

If you run into any issues or have feature requests, feel free to open an issue on GitHub.

If you enjoy this project, consider supporting development by simply leaving a ⭐ on this GitHub repository!

---
