from foundation_platform.core.generator import SiliconFlowGenerator
import os

gen = SiliconFlowGenerator()
# Test generation with FLUX.1-schnell, guidance scale and negative prompt to see if API throws 400
output = "d:/Desktop/workk/test_flux.png"
success = gen.generate(
    description="masterpiece, best quality, ultra-detailed scenery, beautiful sunset over snow mountains",
    output_path=output,
    negative_prompt="nsfw, watermark",
    guidance_scale=7.5
)
if success and os.path.exists(output):
    print(f"Success! Image saved to {output}")
else:
    print("Generation failed.")
