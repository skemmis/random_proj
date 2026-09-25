// One-off asset generator. Run once with GEMINI_API_KEY set; outputs are committed,
// so the key is never needed at runtime.
//
//   GEMINI_API_KEY=... node tools/gen-images.mjs [name ...]
//
// Style references (the picture-book spreads) are read from REF_DIR.
import fs from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';

const KEY = process.env.GEMINI_API_KEY;
if (!KEY) { console.error('GEMINI_API_KEY is required'); process.exit(1); }
const MODEL = process.env.GEMINI_IMAGE_MODEL || 'gemini-3.1-flash-image';
const REF_DIR = process.env.REF_DIR || '/tmp/claude-0/-home-user-random-proj/f34305d2-2a92-5feb-a3bc-43161fa6f1a6/images';
const OUT = path.resolve('public/img');

const STYLE = `Illustration style: children's picture-book gouache and colored pencil, flat shapes with soft grainy texture, visible pencil hatching, slightly wobbly hand-drawn outlines, no gradients, no photorealism, no 3D. Warm, cozy, old-timey. Palette strictly: cream paper (#F6EBD3), butter yellow (#F3D172), sage green (#7FA37A), deep teal green (#2F6B62), coral orange (#E9673F), terracotta (#C9714A), warm brown (#6B4F3A), muted blue-grey (#8AA3A6). Characters (when present) have simple dot eyes, round rosy cheeks, small smiles, no visible teeth. No text, no letters, no words, no logos, no watermark anywhere in the image.`;

const MANIFEST = {
  hero: {
    aspect: '16:9',
    prompt: `Wide establishing scene of a small family medicine clinic in Ojai, California: a cozy one-story Spanish-style cottage with cream stucco walls, a terracotta tile roof, a sage green front door with a small brass bell, potted herbs and lavender by the entrance, a wooden bench under a big California live oak. Behind it rolling hills with orange groves and the Topatopa mountains glowing soft pink in late-afternoon light. A gravel path leads to the door. A bicycle leans on the fence. Peaceful, inviting, no people, no text.`,
  },
  waiting_room: {
    aspect: '4:3',
    prompt: `Interior of a warm, homey doctor's waiting room: mismatched wooden chairs with yellow and green cushions, a woven rug over a patterned green-and-cream tile floor, lots of hanging and potted plants (pothos, fern, a lemon tree in a pot), a bookshelf with picture books and a basket of wooden toys for children, a window with a view of oak trees and hills, morning light, a small side table with a teapot and cups. No people, no text.`,
  },
  visit: {
    aspect: '4:3',
    prompt: `A kind family doctor, a woman in her forties with long wavy auburn-red hair worn in a loose braid, wearing a sage green cardigan over a cream blouse with a stethoscope around her neck, sitting at a wooden table across from a parent and a small red-haired child who is holding a stuffed rabbit. The doctor is leaning in, listening warmly, notebook open. Cozy exam room with plants on the windowsill, a framed botanical print, a woven basket. Warm afternoon light. No text.`,
  },
  home_visit: {
    aspect: '4:3',
    prompt: `Evening scene: the same family doctor (long auburn braid, sage green cardigan) walking up a garden path carrying a worn brown leather doctor's bag toward a small cottage whose porch light glows warm yellow. A crescent moon and a few stars in a deep teal sky, silhouettes of oak trees and hills, lavender and rosemary bushes lining the path, a cat sitting on the porch step. Gentle and reassuring. No text.`,
  },
  garden: {
    aspect: '3:2',
    prompt: `A sunny kitchen-garden and herb table still life: a wooden table with a bowl of oranges, a jar of honey, sprigs of rosemary, sage, chamomile and lavender, a mortar and pestle, a ceramic teapot, a folded linen cloth, and an open notebook (blank pages). Behind it, a window with light streaming in and a view of Ojai hills. No people, no text.`,
  },
  ojai_banner: {
    aspect: '21:9',
    prompt: `Very wide, simple, quiet landscape banner: Ojai valley at dusk, rows of orange trees in the foreground, rolling hills, the Topatopa mountains in soft pink and lavender light, a few live oaks, a small cottage with one warm lit window, a crescent moon. Minimal, flat, restful composition with lots of calm sky. No people, no text.`,
  },
  // Spot illustrations: single object on plain cream, used as service icons.
  spot_family: { aspect: '1:1', spot: true, prompt: `A parent, a grandparent, and a small child holding hands in a row, seen from the front, simple and friendly.` },
  spot_child: { aspect: '1:1', spot: true, prompt: `A small child in yellow overalls hugging a stuffed rabbit, with a bandage on one knee, smiling.` },
  spot_stethoscope: { aspect: '1:1', spot: true, prompt: `A stethoscope coiled loosely around a sprig of rosemary and a chamomile flower.` },
  spot_bowl: { aspect: '1:1', spot: true, prompt: `A teal ceramic bowl full of oranges, leafy greens, and a wooden spoon, with a jar of honey beside it.` },
  spot_house: { aspect: '1:1', spot: true, prompt: `A small cottage with a terracotta roof and a glowing window, a doctor's leather bag sitting on the doorstep, a crescent moon above.` },
  spot_clock: { aspect: '1:1', spot: true, prompt: `A friendly round wall clock with a small sun peeking over its top edge and a sprig of leaves, suggesting "today".` },
  spot_phone: { aspect: '1:1', spot: true, prompt: `An old-fashioned coral-colored rotary telephone with a small heart floating above the receiver.` },
  spot_heart: { aspect: '1:1', spot: true, prompt: `A coral heart shape made of woven wheat and lavender stems, tied with a small ribbon.` },
  spot_teapot: { aspect: '1:1', spot: true, prompt: `A teal teapot pouring steam that curls into gentle swirls, next to a cup and a sprig of mint.` },
  spot_book: { aspect: '1:1', spot: true, prompt: `An open notebook with a pencil, a few pressed flowers on the page, and a pair of round reading glasses.` },
  spot_moon: { aspect: '1:1', spot: true, prompt: `A crescent moon and a small glowing porch lantern hanging from a hook, a few stars.` },
  spot_calendar: { aspect: '1:1', spot: true, prompt: `A wall calendar page with a single day circled in coral crayon and a small sprig of leaves tucked into the top.` },
};

const SPOT_STYLE = `Single centered spot illustration on a plain, flat, uniform cream background (#F6EBD3) with generous empty margin around the subject, no frame, no border, no shadow, no scene, no ground line.`;

async function refParts() {
  const parts = [];
  for (const f of ['1.webp', '2.webp', '3.webp']) {
    const p = path.join(REF_DIR, f);
    if (!fs.existsSync(p)) continue;
    const png = await sharp(p).png().toBuffer();
    parts.push({ inlineData: { mimeType: 'image/png', data: png.toString('base64') } });
  }
  return parts;
}

async function generate(name, spec, refs) {
  const text = [
    'Use the attached images ONLY as a reference for illustration style, palette, texture, and character design. Do not copy their content.',
    STYLE,
    spec.spot ? SPOT_STYLE : '',
    'Subject: ' + spec.prompt,
  ].filter(Boolean).join('\n\n');

  const body = {
    contents: [{ role: 'user', parts: [...refs, { text }] }],
    generationConfig: {
      responseModalities: ['IMAGE'],
      imageConfig: { aspectRatio: spec.aspect },
    },
  };
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent`;
  for (let attempt = 1; attempt <= 3; attempt++) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-goog-api-key': KEY },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const t = await res.text();
      console.error(`[${name}] HTTP ${res.status} (attempt ${attempt}): ${t.slice(0, 300)}`);
      await new Promise(r => setTimeout(r, 3000 * attempt));
      continue;
    }
    const json = await res.json();
    const parts = json.candidates?.[0]?.content?.parts || [];
    const img = parts.find(p => p.inlineData);
    if (!img) {
      console.error(`[${name}] no image in response (attempt ${attempt}):`, JSON.stringify(json).slice(0, 300));
      continue;
    }
    const buf = Buffer.from(img.inlineData.data, 'base64');
    fs.mkdirSync(OUT, { recursive: true });
    const raw = path.join(OUT, `${name}.raw.png`);
    fs.writeFileSync(raw, buf);
    const meta = await sharp(buf).metadata();
    console.log(`[${name}] ok ${meta.width}x${meta.height} -> ${raw}`);
    return raw;
  }
  throw new Error(`[${name}] failed after retries`);
}

const names = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(MANIFEST);
const refs = await refParts();
for (const n of names) {
  if (!MANIFEST[n]) { console.error('unknown asset', n); continue; }
  try { await generate(n, MANIFEST[n], refs); } catch (e) { console.error(e.message); }
}
