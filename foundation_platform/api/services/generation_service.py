import os
import json
import asyncio
from typing import Optional, Dict, Any

from foundation_platform.core.generator import GeneratorRegistry
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foundation_platform.api.models import AssetStatus
from foundation_platform.core.nar import NarrativeAttentionResidual
from foundation_platform.core.llm_service import enhance_prompt_via_llm

# Shared state
from foundation_platform.api.state import (
    tasks_kv, task_logs, asset_registry,
    extractor, refiner, attention_mgr, feedback_lock, manager
)
import time
import shutil
from foundation_platform.api.services.db_service import insert_asset_variant

# Global rate limiting semaphore (Phase 34)
generation_semaphore = asyncio.Semaphore(3)

async def run_generation_v5(provider_name: str, path: str, description: str, asset_type: str, entropy: float, 
                           relationships: Optional[Dict[str, Any]] = None, refinement_passes: int = 1,
                           seed: int = -1, guidance_scale: float = 7.5, negative_prompt: str = ""):
    # Phase 16: Track status in registry
    target_status = None
    for atype, items in asset_registry.items():
        if path in items:
            target_status = items[path]
            if isinstance(target_status, AssetStatus):
                target_status.task_status = "IN_PROGRESS"
            break

    full_path = os.path.join(PROJECT_ROOT, path.replace('/', os.sep))
    logs = task_logs.get(path, [])
    
    async def log_update(msg: str):
        logs.append(msg)
        await manager.broadcast({
            "event": "log_update",
            "path": path,
            "log": msg
        })
        
    async def status_update(status: str, prompt: str = ""):
        tasks_kv[path]["status"] = status
        if prompt:
            tasks_kv[path]["prompt"] = prompt
        
        if isinstance(target_status, AssetStatus):
            target_status.task_status = status
            if prompt:
                target_status.last_prompt = prompt
        
        await manager.broadcast({
            "event": "status_update",
            "path": path,
            "status": status,
            "prompt": prompt
        })
    
    # Indicate queuing state before acquiring semaphore
    await status_update("QUEUED")
    await log_update("Waiting in queue... (Max 3 concurrent tasks)")
    
    async with generation_semaphore:
        await status_update("IN_PROGRESS")
        
        # ──────────────── Phase 14: NAR Initialization ────────────────
        nar = NarrativeAttentionResidual(temperature=0.4)
        
        # 1. Pipeline NAR: Push Global Context
        global_ctx = f"Theme: {attention_mgr.global_context['theme']}, Era: {attention_mgr.global_context['era']}"
        nar.push(global_ctx, metadata={"stage": "global_config"})

        # Look up rejected reasons and historical context (Temporal NAR)
        feedback_file = os.path.join(PROJECT_ROOT, "feedback.jsonl")
        rejected_reasons = []
        if os.path.exists(feedback_file):
            with open(feedback_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        fb = json.loads(line.strip())
                        if fb.get('asset_path') == path:
                            # Push previous attempts to NAR stack for selective retrieval
                            status_tag = "[LIKED]" if fb.get('status') == 'LIKED' else "[DISLIKED]"
                            history_item = f"{status_tag} Prompt: {fb.get('prompt')} | Reason: {fb.get('reason', 'N/A')}"
                            nar.push(history_item, metadata={"stage": "history"})
                            
                            if fb.get('status') == 'DISLIKED' and fb.get('reason'):
                                rejected_reasons.append(fb['reason'])
                    except:
                        pass
        
        try:
            # Stage 1: Attention-driven Refinement with Entropy
            await log_update(f"Stage 1/3: Deep Refinement (Entropy={entropy})...")
            await asyncio.sleep(1)
            
            attention = attention_mgr.get_focus_tokens(path, description, rejected_reasons)
            
            # Pipeline NAR: Push Stage 1 Output (Focus Tokens) to NAR stack
            pos_str = ", ".join(attention.get("positive", []))
            nar.push(f"Focus Tokens: {pos_str}", metadata={"stage": "attention_stage"})
            
            # Pipeline NAR: Get context hint from prior stages and history
            nar_context = nar.get_context_hint(description)
            await log_update(f"NAR Contextual retrieval: {nar_context}")

            refinement_result = refiner.refine(
                asset_type=asset_type, 
                raw_description=description, 
                attention=attention, 
                entropy=entropy, 
                relationships=relationships, 
                refinement_passes=refinement_passes, 
                rejected_reasons=rejected_reasons,
                nar_context=nar_context  # Level 1 NAR Input
            )
            
            prompt = refinement_result["prompt"]
            neg_prompt = refinement_result["negative_prompt"]
            tasks_kv[path]["prompt"] = prompt
            if "snapshots" in refinement_result:
                tasks_kv[path]["snapshots"] = refinement_result["snapshots"]
            
            # Log visual vibe for future BGM resonance
            if asset_type in ["背景图", "人物立绘"]:
                attention_mgr.update_resonance(path, description)
                await log_update(f"Visual Atmosphere cached for resonance.")
                
            await log_update(f"Attention Spotlight: {', '.join(attention['positive'])}")
            await log_update(f"Refined Prompt: {prompt}")
            if neg_prompt:
                await log_update(f"Negative Attention: {neg_prompt}")
            
            # Stage 2: AI Generation
            # Phase 41: Modality Router — prevent audio assets from being sent to image generators
            AUDIO_ASSET_TYPES = {"BGM", "音效"}
            if asset_type in AUDIO_ASSET_TYPES:
                await log_update(f"⚠️ Modality Router: '{asset_type}' is an audio asset. Image generation skipped.")
                await log_update(f"Writing audio placeholder metadata for future audio AI integration...")
                
                # Write a structured placeholder JSON instead of a corrupted image file
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                placeholder_path = full_path  # e.g. assets/sfx/xxx.wav or assets/bgm/xxx.mp3
                meta_path = os.path.splitext(full_path)[0] + ".meta.json"
                
                import json as _json
                audio_meta = {
                    "asset_type": asset_type,
                    "name": os.path.basename(full_path),
                    "description": description,
                    "prompt": prompt,
                    "status": "AWAITING_AUDIO_MODEL",
                    "note": "This is a placeholder. Connect a real audio AI provider (Suno/StableAudio/MusicGen) to generate actual audio."
                }
                with open(meta_path, 'w', encoding='utf-8') as mf:
                    _json.dump(audio_meta, mf, ensure_ascii=False, indent=2)
                
                # Also create a minimal placeholder file so the asset shows as "FOUND" in status checks
                with open(placeholder_path, 'w', encoding='utf-8') as pf:
                    pf.write(f"# Audio Placeholder: {asset_type} - {description[:80]}\n")
                
                await status_update("COMPLETED_PLACEHOLDER", prompt=prompt)
                await log_update(f"✅ Audio metadata saved to {os.path.basename(meta_path)}. Awaiting real audio model integration.")
                return {"status": "success", "asset_path": path, "modality": "audio_placeholder"}

            # Phase 26: LLM prompt enhancement for real models
            if negative_prompt:
                # If user explicitly passed negative prompt, combine it with refiner's
                neg_prompt = f"{neg_prompt}, {negative_prompt}".strip(", ")

            if provider_name in ['siliconflow'] and prompt:
                await log_update("Stage 2/3: LLM Prompt Enhancement (DeepSeek)...")
                enhanced = enhance_prompt_via_llm(asset_type, prompt, nar_context)
                if enhanced and enhanced != prompt:
                    await log_update(f"Enhanced SD Prompt: {enhanced[:100]}...")
                    prompt = enhanced
                    
                    # Broadcast the enhanced prompt
                    await status_update("IN_PROGRESS", prompt=prompt)
            
            await log_update(f"Stage 2/3: Generating via {provider_name}...")
            await asyncio.sleep(0.5)
            generator = GeneratorRegistry.get_generator(provider_name)
            if not generator:
                raise Exception(f"Provider {provider_name} not found")
            
            # Phase 36: Pass negative_prompt, seed, guidance_scale for quality control
            gen_kwargs = {}
            if neg_prompt:
                gen_kwargs["negative_prompt"] = neg_prompt
            if seed >= 0:
                gen_kwargs["seed"] = seed
            if guidance_scale != 7.5:
                gen_kwargs["guidance_scale"] = guidance_scale
                
            # Phase 34: Variant Storage (Save to unique file first)
            base, ext = os.path.splitext(full_path)
            timestamp_str = str(int(time.time() * 1000))
            variant_full_path = f"{base}_{timestamp_str}{ext}"
            
            try:
                success = generator.generate(prompt, variant_full_path, **gen_kwargs)
            except TypeError:
                # Fallback for generators that don't support extra kwargs (e.g. MockGenerator)
                success = generator.generate(prompt, variant_full_path)
                
            # If successful, overwrite the canonical location to keep the project structure clean
            if success and os.path.exists(variant_full_path):
                shutil.copy(variant_full_path, full_path)
                
            # Insert to DB
            variant_rel_url = variant_full_path.replace(PROJECT_ROOT, "").replace("\\", "/")
            try:
                insert_asset_variant(
                    node_id=path,  # the relative path is used as the node ID
                    image_url=variant_rel_url if success else "",
                    status="SUCCESS" if success else "FAILED",
                    prompt=prompt,
                    negative_prompt=neg_prompt if 'neg_prompt' in locals() else None,
                    seed=seed,
                    guidance_scale=guidance_scale
                )
            except Exception as db_err:
                await log_update(f"DB Save Warning: {str(db_err)}")
            
            # Phase 16: Metadata Finalization & Status Sync
            status_text = "COMPLETED" if success else "FAILED"
            await status_update(status_text, prompt=prompt)
            
            if success:
                await log_update("Stage 3/3: Finalizing production assets...")
                await asyncio.sleep(0.5)
                await log_update("Task successfully completed.")
            else:
                await log_update("Error: Model generation failed.")
                
        except Exception as e:
            await status_update("FAILED")
            await log_update(f"Critical System Error: {str(e)}")

    return {"status": "success", "asset_path": path}
