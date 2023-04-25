import xml.etree.ElementTree as ET
import csv
import re
import png
import networkx as nx
import itertools
import yaml
import glob
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance
import random
import operator
import math
import os

import pprint # for debugging

# TODO investigate why The Work (Sky) isn't included for Hell Slime

# TODO check for other material sources
#
# Entities: 
#   PhysicsImageShapeComponent.material     as bodyOf lookup
#   ExplodeOnDamageComponent/config_explosion.spark_material      as hitting lookup
#   ParticleEmitterComponent.emitted_material_name      as emittedFrom lookup
#   DamageModelComponent.ragdoll_material     as corpseOf lookup
#   DamageModelComponent.blood_material       as bloodOf
#   DamageModelComponent.blood_spray_material       as sprayedBy
#   MagicConvertMaterialComponent.to_material       as convertedToBy
#   MaterialInventoryComponent/count_per_material_type/Material.material      as containedIn
#   PixelSpriteComponent.material     as bodyOf lookup
#   

mod_prefix = "Mod GT-"
os.makedirs("zout_potions", exist_ok=True)
os.makedirs("zout_mats/finished", exist_ok=True)
os.makedirs("zout_mats/unfinished", exist_ok=True)

####################################################################
## Data
####################################################################

effect_lookup = {
  "FROZEN": "frozen",
  "ON_FIRE": "on fire!",
  "POISONED": "poisoned",
  "BERSERK": "berserk",
  "CHARM": "charmed",
  "POLYMORPH": "polymorph",
  "POLYMORPH_RANDOM": "chaos polymorph",
  "POLYMORPH_UNSTABLE": "unstable polymorph",
  "BLINDNESS": "blinded",
  "TELEPORTATION": "teleportitis",
  "UNSTABLE_TELEPORTATION": "unstable teleportitis",
  "HP_REGENERATION": "regeneration",
  "LEVITATION": "faster levitation",
  "MOVEMENT_SLOWER": "clumsy movement",
  "FARTS": "gassy",
  "TRIP": "tripping",
  "INGESTION_DRUNK": "drunk",
  "RADIOACTIVE": "toxic",
  "ALCOHOLIC": "alcoholic",
  "WET": "wet",
  "OILED": "oiled",
  "BLOODY": "bloody",
  "SLIMY": "slimy",
  "CONFUSION": "confused",
  "FOOD_POISONING": "food poisoning",
  "INGESTION_ON_FIRE": "internal fire",
  "INGESTION_FREEZING": "chilly",
  "JARATE": "jarated",
  "MOVEMENT_FASTER_2X": "greased lightning",
  "FASTER_LEVITATION": "faster levitation",
  "WORM_ATTRACTOR": "worm food",
  "PROTECTION_ALL": "protection from all",
  "INVISIBILITY": "invisible",
  "MANA_REGENERATION": "mana regeneration",
  "PROTECTION_POLYMORPH": "polymorph immunity",
  "RAINBOW_FARTS": "rainbow farts",
  "CURSE_CLOUD": "rain curse",
  "NIGHTVISION": "wormy vision",
}


####################################################################
## Parse translations
####################################################################

translations = {}
with open('common.csv', 'r') as f:
  reader = csv.reader(f)
  for row in reader:
    translations['$' + row[0]] = row[1]


####################################################################
## Parse materials.xml
####################################################################

def effect_to_wiki(effect_str, duration = None):
  if effect_str in effect_lookup:
    if duration:
      return "{{status|" + effect_lookup[effect_str] + f"|{float(duration)*100:g}" + "}}"
    return "{{status|" + effect_lookup[effect_str] + "}}"
  return effect_str 

def extract_status_effect(elem):
  effect = elem.attrib.get('type')
  duration = elem.attrib.get('amount')
  return effect_to_wiki(effect, duration)

def get_stain_effects(elem):
  effect_tags = elem.findall('./StatusEffects/Stains/StatusEffect')
  return '<br/>'.join(map(extract_status_effect, effect_tags))

def get_ingest_effects(elem):
  effect_tags = elem.findall('./StatusEffects/Ingestion/StatusEffect')
  return '<br/>'.join(map(extract_status_effect, effect_tags))

tree = ET.parse('materials.xml')
root = tree.getroot()

materials = {}
valid_colours = set()

def get_translated_ui_name(child):
  uiname = child.attrib.get('ui_name', child.attrib['name'])
  return translations.get(uiname, uiname).lstrip('$').title()

def convert_attrib_data(child):
  attr = child.attrib
  colour = int(attr.get('wang_color', '0'), base=16) & 0xFFFFFF

  result = {
    "name": get_translated_ui_name(child),
    "id": attr["name"],
    "colour": colour,
    "wang_color": attr.get('wang_color', '0'),
  }

  if 'cell_type' in attr: result['cell_type'] = attr['cell_type']
  if 'liquid_static' in attr: result['liquid_static'] = attr['liquid_static']
  if 'liquid_sand' in attr: result['liquid_sand'] = attr['liquid_sand']

  tags = set(re.findall('\w+', attr.get('tags', '')))
  result['tags'] = tags

  if 'density' in attr: result['density'] = attr['density']
  if 'hp' in attr: result['hardness'] = attr['hp']
  if 'durability' in attr: result['durability'] = attr['durability']
  if 'lifetime' in attr: result['lifetime'] = attr['lifetime']
  if '_parent' in attr: result['parent'] = attr['_parent']
  if '_inherit_reactions' in attr: result['inheritsReactions'] = attr['_inherit_reactions']
  if 'status_effects' in attr: result['submergeEffect'] = effect_to_wiki(attr['status_effects'])
  
  stains = get_stain_effects(child)
  ingestion = get_ingest_effects(child)
  
  if stains != '': result['stainEffect'] = stains
  if ingestion != '': result['ingestEffect'] = ingestion

  if 'electrical_conductivity' in attr: result['conductive'] = attr['electrical_conductivity']
  if 'burnable' in attr: result['burnable'] = attr['burnable']
  if 'cold_freezes_to_material' in attr: result['freezes'] = attr['cold_freezes_to_material']
  if 'warmth_melts_to_material' in attr: result['melts'] = attr['warmth_melts_to_material']

  break_into = set()
  if 'solid_break_to_type' in attr: break_into.add(attr['solid_break_to_type'])
  if 'solid_on_collision_material' in attr: break_into.add(attr['solid_on_collision_material'])
  if 'convert_to_box2d_material' in attr: break_into.add(attr['convert_to_box2d_material'])
  if len(break_into) > 0: result['breakInto'] = ','.join(break_into)

  if 'slippery' in attr: result['slippery'] = attr['slippery']
  if 'fire_hp' in attr: result['fuel'] = attr['fire_hp']
  if 'platforming_type' in attr: result['playerCollision'] = attr['platforming_type'] == '1'

  if 'gfx_glow' in attr:
    result['glow'] = int(attr['gfx_glow'])
  if 'gfx_glow_color' in attr:
    result['glow_color'] = attr['gfx_glow_color']

  graphics = child.find('Graphics')
  if graphics != None:
    result['has_gfx'] = True
    gfxattr = graphics.attrib

    if 'color' in gfxattr: result['gfx_color'] = gfxattr['color']
    if 'texture_file' in gfxattr: result['gfx_texture_file'] = gfxattr['texture_file'].removeprefix('data/')
    
    gfx_border = {}
    if 'pixel_all_around' in gfxattr: gfx_border['gfx_pixel_all_around'] = gfxattr['pixel_all_around']
    if 'pixel_top_right' in gfxattr: gfx_border['gfx_pixel_top_right'] = gfxattr['pixel_top_right']
    if 'pixel_top_left' in gfxattr: gfx_border['gfx_pixel_top_left'] = gfxattr['pixel_top_left']
    if 'pixel_bottom_right' in gfxattr: gfx_border['gfx_pixel_bottom_right'] = gfxattr['pixel_bottom_right']
    if 'pixel_bottom_left' in gfxattr: gfx_border['gfx_pixel_bottom_left'] = gfxattr['pixel_bottom_left']
    if 'pixel_left' in gfxattr: gfx_border['gfx_pixel_left'] = gfxattr['pixel_left']
    if 'pixel_top' in gfxattr: gfx_border['gfx_pixel_top'] = gfxattr['pixel_top']
    if 'pixel_right' in gfxattr: gfx_border['gfx_pixel_right'] = gfxattr['pixel_right']
    if 'pixel_bottom' in gfxattr: gfx_border['gfx_pixel_bottom'] = gfxattr['pixel_bottom']
    if len(gfx_border) > 0:
      result['gfx_border'] = gfx_border

    edge = child.find('Graphics/Edge/EdgeGraphics')
    if edge != None:
      result['gfx_edge_type'] = edge.attrib['type']

      sides = [dict(side.items()) for side in edge.findall('Images/Image')]
      if len(sides) > 0:
        result['gfx_sides'] = sides

  return result


def process_celldata(child):
  material = convert_attrib_data(child)
  
  valid_colours.add(material['colour'])
  materials[material['id']] = material


for child in root.findall("CellData"):
  process_celldata(child)

for child in root.findall("CellDataChild"):
  process_celldata(child)

#valid_colours.update(special_mapping.keys())

####################################################################
## Inherit values and populate biomes
####################################################################
def merge_material_values(material, spaces=''):
  if 'parent' in material and material['parent'] in materials:
    merge_material_values(materials[material['parent']], spaces + '  ')

    new_mat = materials[material['parent']].copy()
    tags = new_mat.get('tags', set())
    #
    #if material.get('inheritsReactions', '0') == '1':
    #  tags = tags.union(material.get('tags', set()))

    old_gfx_edge_type = material.get('gfx_edge_type', None)
    old_gfx_sides = material.get('gfx_sides', None)
    old_gfx_border = material.get('gfx_border', None)
    
    new_mat.update(material)
    
    if old_gfx_edge_type != None:
      new_mat['gfx_edge_type'] = old_gfx_edge_type
    else:
      new_mat.pop('gfx_edge_type', '')

    if old_gfx_sides != None:
      new_mat['gfx_sides'] = old_gfx_sides
    else:
      new_mat.pop('gfx_sides', '')

    if old_gfx_border != None:
      new_mat['gfx_border'] = old_gfx_border
    else:
      new_mat.pop('gfx_border', '')

    
    if len(new_mat.get('tags', set())) == 0:
      new_mat['tags'] = tags

    materials[material['id']] = new_mat


for mat_key in materials.keys():
  merge_material_values(materials[mat_key])


def get_material_type(elem):
  cell_type = elem.get('cell_type', '')

  if cell_type == 'fire': return 'Fire'
  if cell_type == 'solid': return 'Solid'
  if cell_type == 'gas': return 'Gas'

  if cell_type == 'liquid':
    if elem.get('liquid_static', '0') == '1': return 'Solid'
    if elem.get('liquid_sand', '0') == '1': return 'Powder'
    return 'Liquid'

  return ''


for mat in materials.values():
  mat_type = get_material_type(mat)
  if mat_type != '': mat['type'] = mat_type

  # Get the list of biomes this material is found in
  #biomes = set()
  #if mat['colour'] in pixel_biome_locations:
  #  biomes.update(pixel_biome_locations[mat['colour']]['biomes'])

  #if mat['id'] in biome_mat_mapping:
  #  biomes.update(biome_mat_mapping[mat['id']])

  #if len(biomes) > 0: mat['biomes'] = ','.join(biomes)

####################################################################
## Process Material Graphics
####################################################################
powder_mask = Image.new("RGBA", (42, 42))
liquid_mask = Image.new("RGBA", (42, 42))
gas_mask = Image.open("gas_mask.png")
#ImageDraw.Draw(powder_mask).ellipse([1, 1, powder_mask.width-1, powder_mask.height-1], fill='white')
ImageDraw.Draw(powder_mask).pieslice([-powder_mask.width, -powder_mask.height, powder_mask.width*2, powder_mask.height*1.5], 45, 135, fill='white')

ImageDraw.Draw(liquid_mask).rectangle([0, 16, liquid_mask.width, liquid_mask.height], fill='white')
ImageDraw.Draw(liquid_mask).line([6, 15, 13, 15], fill='white')
ImageDraw.Draw(liquid_mask).line([22, 15, 35, 15], fill='white')
#ImageDraw.Draw(liquid_mask).line([34, 15, 37, 15], fill='white')

def make_gas_mask_copy(mat_alpha):
  a_low = mat_alpha * 3 // 4

  result = gas_mask.copy()
  for y in range(result.height):
    for x in range(result.width):
      r,g,b,a = result.getpixel((x, y))
      if a == 128:
        a = a_low
      elif a == 255:
        a = mat_alpha
      else:
        continue
      result.putpixel((x, y), (r, g, b, a))
  return result


potion_base = Image.open('ui_gfx/items/potion.png')
powder_base = Image.open('ui_gfx/items/material_pouch.png')


def gl_mix(x, y, a):
  return tuple(i*(1.0-a) + j*a for i,j in zip(x, y))


def create_potion_graphic(base, basename, material_name, colour):
  pot = base.copy()

  for x in range(0, pot.width):
    for y in range(0, 3):
      r,g,b,a = pot.getpixel((x,y))
      r,g,b = tuple(int(round(i * 0.85)) for i in [r,g,b])
      pot.putpixel((x,y), (r, g, b, a))

    for y in range(3, pot.height):
      r,g,b,a = pot.getpixel((x,y))
      r,g,b = tuple((i / 255.0) * (j / 255.0) for i,j in zip([r,g,b], colour[:3]))
      r,g,b = tuple(int(round(i * 0.85 * 255.0)) for i in [r,g,b])
      pot.putpixel((x,y), (r, g, b, a))
  
  pot.save(f"zout_potions/{mod_prefix}material{basename}_{material_name}.png", optimize=True)


def RGBAfromInt(v):
  b =  v & 255
  g = (v >> 8) & 255
  r =   (v >> 16) & 255
  a = (v >> 24) & 255
  return (r, g, b, a)

def get_colour(s):
  return RGBAfromInt(int(s, base=16))

def blit_tiled(dst, src, mat_type):
  temp_img = Image.new("RGBA", dst.size)
  for y in range(0, dst.height, src.height):
    for x in range(0, dst.width, src.width):
        temp_img.paste(src, (x, y))

  if mat_type == 'Powder':
    dst.paste(temp_img, (0, 0), powder_mask)
  elif mat_type == 'Liquid':
    dst.paste(temp_img, (0, 0), liquid_mask)
  elif mat_type == 'Gas':
    dst.paste(temp_img, (0, 0), gas_mask)
  else:
    dst.paste(temp_img, (0, 0))

def count_empty(img, x):
  result = 0
  for y in range(0, img.height):
    if img.getpixel((x, img.height - y - 1))[3] != 0:
      return result
    result += 1
  return result

def settle_powder(img):
  result = Image.new("RGBA", img.size)

  # Shift everything down
  for x in range(0, img.width):
    shift = count_empty(img, x)
    line = img.crop((x, 0, x+1, img.height))
    result.paste(line, (x, shift))

  # Rotate random pixels
  for i in range(0, 1500):
    rx1 = random.randint(1, result.width-2)
    ry1 = random.randint(1, result.height-2)

    px1 = result.getpixel((rx1, ry1))
    if px1[3] == 0: continue

    rx2 = rx1 + (random.randint(0, 1)*2 - 1)
    ry2 = ry1 + random.randint(-1, 1)
    px2 = result.getpixel((rx2, ry2))
    if px2[3] == 0: continue

    result.putpixel((rx1, ry1), px2)
    result.putpixel((rx2, ry2), px1)

  return result

def settle_liquid(img):
  # Rotate random pixels
  for i in range(0, 3000):
    rx1 = random.randint(1, img.width-2)
    ry1 = random.randint(1, img.height-2)

    px1 = img.getpixel((rx1, ry1))
    if px1[3] == 0: continue

    rx2 = rx1 + (random.randint(0, 1)*2 - 1)
    ry2 = ry1 + random.randint(-1, 1)
    px2 = img.getpixel((rx2, ry2))
    if px2[3] == 0: continue

    img.putpixel((rx1, ry1), px2)
    img.putpixel((rx2, ry2), px1)

def decimal_range(start, stop, increment):
  while start < stop:
    yield start
    start += increment

def apply_glow(img, glow_amount, glow_colour):
  # TODO still wrong
  #color = max ( color + glow * 0.6 - 0.6 * lights, clamp((color + glow) - ( color * sky_light_modulation * glow), 0.0, 1.0));

  tex_glow_source = img.copy()

  for imgy in range(0, img.height):
    for imgx in range(0, img.width):
      px = tex_glow_source.getpixel((imgx, imgy))

      r,g,b,a = tuple((i / 255.0) * (glow_amount / 255.0) for i in glow_colour)
      px = tuple(i / 255.0 for i in px)
      color = r, g, b, px[3]
      #r,g,b,a = glow

      #smoothing_amount = 1.0 - (r + g + b) * 0.3333
      #glow = gl_mix(glow, glow, smoothing_amount)

      color = tuple(max(0, i - 0.008) for i in color)

      color = tuple(int(round((c + g * 0.6) * 255.0)) for c, g in zip(px, color))
      img.putpixel((imgx, imgy), color)


  # TODO: this is wrong, needs fixing
  #BLUR_RADIUS = 5.0
#
  #tex_glow_source = img.copy()
#
  #for imgy in range(0, img.height):
  #  for imgx in range(0, img.width):
  #    new_tap = tex_glow_source.getpixel((imgx, imgy))
  #    new_tap = tuple(i / 255.0 for i in new_tap)
#
  #    #new_glow = tuple((i / 255.0) * (glow / 255.0) * 2.5 for i in glow_colour)
  #    #new_tap = tuple(map(operator.add, new_tap, new_glow))
#
  #    decayed = (0.0, 0.0, 0.0, 0.0)
  #    for x in decimal_range(-BLUR_RADIUS+0.005, BLUR_RADIUS+0.005, 1.0):
  #      if x + imgx < 0 or x + imgx >= img.width: continue
  #      for y in decimal_range(-BLUR_RADIUS, BLUR_RADIUS, 1.0):
  #        if y + imgy < 0 or y + imgy >= img.height: continue
#
  #        #px = tex_glow_source.getpixel((x + imgx, y + imgy))
  #        px = tuple(i / 255.0 for i in glow_colour)
  #        decayed = tuple(map(operator.add, decayed, px))
#
  #    # potentially 1/121 * 3.3
  #    decayed = tuple(i / 121.0 for i in decayed)
#
  #    new_decayed = gl_mix(decayed, new_tap, 0.05)
  #    new_tap = tuple(i*0.125 for i in new_tap)
  #    new_px = tuple(map(operator.add, new_tap, new_decayed))
  #    new_px = tuple(int(i * 255) for i in new_px)
  #    img.putpixel((imgx, imgy), new_px)


def process_material_graphic(material):
  mat_id = material['id']
  colour = get_colour(material['wang_color'])
  glow = material.get('glow', 0)
  mat_type = material.get('type', '')

  img = Image.new("RGBA", (42, 42))
  draw = ImageDraw.Draw(img)

  texture_file = None
  fin_dir = "finished"

  # Get colour and texture
  if 'has_gfx' in material:    
    if 'gfx_color' in material:
      colour = get_colour(material['gfx_color'])

    texture_filename = material.get('gfx_texture_file', None)
    if texture_filename:
      path_components = texture_filename.split("/")
      for i in range(len(path_components)):
        try:
          texture_file = Image.open("/".join(path_components[-i:]))
          break
        except:
          print("Failed on " + "/".join(path_components[-i:]))

  # Blit texture/colour
  if texture_file:
    blit_tiled(img, texture_file, mat_type)
    texture_file.close()
  else:
    if mat_type == 'Powder':
      draw.bitmap([0, 0], powder_mask, fill=colour)
    elif mat_type == 'Liquid':
      draw.bitmap([0, 0], liquid_mask, fill=colour)
    elif mat_type == 'Gas':
      mask = make_gas_mask_copy(colour[3])
      draw.bitmap([0, 0], mask, fill=colour)
    elif mat_id == 'air':
      draw.rectangle([0, 0, img.width, img.height], fill=RGBAfromInt(0))
    else:
      draw.rectangle([0, 0, img.width, img.height], fill=colour)

  if 'gfx_border' in material and mat_type == 'Solid':
    border = material['gfx_border']
    if 'gfx_pixel_all_around' in border:
      draw.rectangle([0, 0, img.width-1, img.height-1], outline=get_colour(border['gfx_pixel_all_around']))
    if 'gfx_pixel_top_right' in border:
      img.putpixel((img.width-1, 0), get_colour(border['gfx_pixel_top_right']))
    if 'gfx_pixel_top_left' in border:
      img.putpixel((0, 0), get_colour(border['gfx_pixel_top_left']))
    if 'gfx_pixel_bottom_right' in border:
      img.putpixel((img.width-1, img.height-1), get_colour(border['gfx_pixel_bottom_right']))
    if 'gfx_pixel_bottom_left' in border:
      img.putpixel((0, img.height-1), get_colour(border['gfx_pixel_bottom_left']))
    if 'gfx_pixel_left' in border:
      draw.line([0, 1, 0, img.height-2], get_colour(border['gfx_pixel_left']))
    if 'gfx_pixel_top' in border:
      draw.line([1, 0, img.width-2, 0], get_colour(border['gfx_pixel_top']))
    if 'gfx_pixel_right' in border:
      draw.line([img.width-1, 1, img.width-1, img.height-2], get_colour(border['gfx_pixel_right']))
    if 'gfx_pixel_bottom' in border:
      draw.line([1, img.height-1, img.width-2, img.height-1], get_colour(border['gfx_pixel_bottom']))

  # Create edges
  if 'gfx_edge_type' in material:
    edge_type = material['gfx_edge_type']

    if edge_type == 'EVERYWHERE':
      print(f'Edge type not supported: EVERYWHERE {mat_id}')
      fin_dir = "unfinished"
    elif edge_type == 'CARDINAL_DIRECTIONS' or edge_type == 'NORMAL_BASED':
      # ANGLES:
      #   45-135:   Bottom
      #   135-245:  Right
      #   235-315:  Top
      #   315-360:  Left
      #   0-45:     Left
      #
      for side in material['gfx_sides']:
        min_angle = int(side['min_angle'])
        max_angle = int(side['max_angle'])
        only_vertical = side['do_only_vertical_stripe'] == '1'
        only_horizontal = side['do_only_horizontal_stripe'] == '1'
        edge_filename = side['filename'].removeprefix('data/')
        edge_img = Image.open(edge_filename).convert("RGBA")

        if only_vertical:
          if min_angle <= 0 < max_angle:
            # left
            left_img = edge_img.crop((edge_img.width/2, 0, edge_img.width, edge_img.height))
            for y in range(0, img.height, left_img.height):
              img.paste(left_img, (0, y), left_img)
          elif min_angle <= 180 < max_angle:
            # right
            right_img = edge_img.crop((0, 0, edge_img.width/2, edge_img.height))
            for y in range(0, img.height, right_img.height):
              img.paste(right_img, (img.width - right_img.width, y), right_img)
        elif only_horizontal:
          if min_angle <= 90 < max_angle:
            # bottom
            bottom_img = edge_img.crop((0, 0, edge_img.width, edge_img.height/2))
            for x in range(0, img.width, bottom_img.width):
              img.paste(bottom_img, (x, img.height - bottom_img.height), bottom_img)
          elif min_angle <= 270 < max_angle:
            # top
            top_img = edge_img.crop((0, edge_img.height/2, edge_img.width, edge_img.height))
            for x in range(0, img.width, top_img.width):
              img.paste(top_img, (x, 0), top_img)

  if glow > 0:
    print(f"{mat_id} - Glow: {glow}, Type: {mat_type}")
    fin_dir = "unfinished"

  if mat_type == 'Powder':
    img = settle_powder(img)
  elif mat_type == 'Liquid' or mat_type == 'Fire':
    settle_liquid(img)

  if mat_type == 'Powder' or mat_type == 'Liquid':
    create_potion_graphic(potion_base, 'potion', mat_id, colour)
  
  if mat_type == 'Powder':
    create_potion_graphic(powder_base, 'pouch', mat_id, colour)

  img = img.resize((252, 252), Image.NEAREST)

  if glow > 0:
    glow_colour = colour
    if 'glow_color' in material:
      glow_colour = get_colour(material['glow_color'])

    apply_glow(img, glow, glow_colour)

  img.save(f"zout_mats/{fin_dir}/{mod_prefix}material_{mat_id}.png", optimize=True)


for mat in materials.values():
  process_material_graphic(mat)
#for child in root.findall("CellData"):
#  process_material_graphic(child)

#for child in root.findall("CellDataChild"):
#  process_material_graphic(child)


####################################################################
## Create Similar Material Clusters (same-page tabs)
####################################################################
G = nx.Graph()
G.add_nodes_from(materials.keys())

def add_melts(mat, id):
  if 'melts' in mat and mat['melts'] != id:
    print(f"{mat['id']} ALREADY HAS MELTS: {mat['melts']} (adding {id})")
  mat['melts'] = id

same_name_nodes = {}
for mat in materials.values():
  same_name_nodes.setdefault(mat['name'], []).append(mat['id'])

  #if 'freezes' in mat: G.add_edge(mat['id'], mat['freezes'])
  #if 'melts' in mat: G.add_edge(mat['id'], mat['melts'])

  molten_id = mat['id'] + "_molten"
  if ('meltable' in mat['tags'] or 'meltable_metal' in mat['tags']) and molten_id in materials:
    add_melts(mat, molten_id)
    G.add_edge(mat['id'], molten_id)

  vapour_id = mat['id'] + "_vapour"
  if 'evaporable_custom' in mat['tags'] and vapour_id in materials:
    add_melts(mat, vapour_id)
    G.add_edge(mat['id'], vapour_id)

  if 'rust_box2d' in mat['tags']: G.add_edge(mat['id'], mat['id'] + '_rust')
  if 'rust_oxide' in mat['tags']: G.add_edge(mat['id'], mat['id'] + '_oxide')

  if 'meltable_metal_generic' in mat['tags']: add_melts(mat, 'metal_sand_molten')
  if 'meltable_to_poison' in mat['tags']: add_melts(mat, 'poison')
  if 'meltable_to_radioactive' in mat['tags']: add_melts(mat, 'radioactive_liquid')
  if 'meltable_to_cold' in mat['tags']: add_melts(mat, 'blood_cold')
  if 'meltable_to_acid' in mat['tags']: add_melts(mat, 'acid')
  if 'meltable_to_water' in mat['tags']: add_melts(mat, 'water')

for same_name_list in same_name_nodes.values():
  if len(same_name_list) > 1:
    G.add_edges_from(itertools.combinations(same_name_list, 2))

# Custom associations
#G.add_edges_from([
#  ('poison_gas', 'poison'),
#  ('concrete_static', 'cement'),
#  ('cloud_blood', 'blood'),
#  ('bone_box2d', 'bone'),
#  ('bone_static', 'bone'),
#  ('coal_static', 'coal'),
#  ('fungi_creeping', 'fungi_creeping_secret'),
#  ('bloodgold_box2d', 'gold'),
#  ('gold_static', 'gold_static_dark'),
#  ('sand_blue', 'sand'),
#  ('sodium_unstable', 'sodium'),
#  ('alcohol_gas', 'alcohol'),
#  ('bush_seed', 'ceiling_plant_material'),
#  ('plant_seed', 'ceiling_plant_material'),
#  ('rock_static_wet', 'rock_static'),
#  ('wood_static_wet', 'wood_static'),
#  ('wood_static_gas', 'wood_static'),
#  ('lavasand', 'sand'),
#  ('rotten_meat', 'meat'),
#  #('meat_slime_orange', 'meat'),
#  ('rotten_meat_radioactive', 'meat'),
#  ('meat_slime_green', 'meat_slime_orange'),
#  #('meat_worm', 'meat'),
#  ('meat_helpless', 'meat_worm'),
#  #('meat_trippy', 'meat'),
#  ('meat_frog', 'meat_trippy'),
#  #('meat_cursed', 'meat'),
#  ('meat_slime_cursed', 'meat_cursed'),
#  ('meat_teleport', 'meat_worm'),
#  ('meat_fast', 'meat_worm'),
#  ('meat_polymorph', 'meat_worm'),
#  ('meat_polymorph_protection', 'meat_worm'),
#  ('meat_confusion', 'meat_worm'),
#  #('meat_warm', 'meat'),
#  ('meat_hot', 'meat_warm'),
#  ('meat_done', 'meat_warm'),
#  ('meat_burned', 'meat_warm'),
#  ('templebrick_static_ruined', 'brick'),
#  ('wizardstone', 'templebrick_static'),
#  ('templebrick_diamond_static', 'templebrick_static'),
#  ('templebrick_moss_static', 'templebrick_static'),
#  ('ice_poison_static', 'poison'),
#  ('ice_acid_static', 'acid'),
#  ('ice_radioactive_static', 'radioactive_liquid'),
#  ('glass_brittle', 'glass'),
#  ('water_ice', 'water'),
#  ('cloud_slime', 'slime'),
#  ('snow', 'snow_static'),
#  ('blood_fading_slow', 'blood'),
#])
#
#G.remove_edges_from([
#  ('steel_molten', 'steel'),
#  ('aluminium_robot_molten', 'aluminium_robot'),
#  ('aluminium_molten', 'aluminium'),
#  ('aluminium_oxide_molten', 'aluminium_oxide'),
#  ('meat_confusion', 'meat'),
#  ('plastic_molten', 'plastic'),
#  ('plastic_red_molten', 'plastic_red'),
#  ('plastic_prop_molten', 'plastic_prop'),
#  ('shock_powder', 'fungisoil'),
#])

#pprint.pprint(G.edges())

clusters = list(nx.connected_components(G))

####################################################################
## Create Wiki Text
####################################################################
def stringify_material_data(mat, num = 0):
  n = ''
  if num > 0: n = str(num+1)

  result = ''
  if 'name' in mat: result += f"| name{n} = {mat['name']}\n"
  if 'type' in mat: result += f"| type{n} = {mat['type']}\n"
  result += f"| id{n} = {mat['id']}\n"
  if 'tags' in mat: result += f"| tags{n} = {','.join(mat['tags'])}\n"
  if 'density' in mat: result += f"| density{n} = {mat['density']}\n"
  if 'hardness' in mat: result += f"| hardness{n} = {mat['hardness']}\n"
  if 'durability' in mat: result += f"| durability{n} = {mat['durability']}\n"
  if 'lifetime' in mat: result += f"| lifetime{n} = {mat['lifetime']}\n"
  if 'biomes' in mat: result += f"| biomes{n} = {mat['biomes']}\n"
  if 'parent' in mat: result += f"| parent{n} = {mat['parent']}\n"
  if 'inheritsReactions' in mat: result += f"| inheritsReactions{n} = {mat['inheritsReactions']}\n"
  if 'submergeEffect' in mat: result += f"| submergeEffect{n} = {mat['submergeEffect']}\n"
  if 'stainEffect' in mat: result += f"| stainEffect{n} = {mat['stainEffect']}\n"
  if 'ingestEffect' in mat: result += f"| ingestEffect{n} = {mat['ingestEffect']}\n"
  if 'conductive' in mat: result += f"| conductive{n} = {mat['conductive']}\n"
  if 'burnable' in mat: result += f"| burnable{n} = {mat['burnable']}\n"
  if 'freezes' in mat: result += f"| freezes{n} = {mat['freezes']}\n"
  if 'melts' in mat: result += f"| melts{n} = {mat['melts']}\n"
  if 'breakInto' in mat: result += f"| breakInto{n} = {mat['breakInto']}\n"
  if 'slippery' in mat: result += f"| slippery{n} = {mat['slippery']}\n"
  if 'flaming' in mat: result += f"| flaming{n} = {mat['flaming']}\n"
  if 'fuel' in mat: result += f"| fuel{n} = {mat['fuel']}\n"
  if 'playerCollision' in mat: result += f"| playerCollision{n} = {mat['playerCollision']}\n"
  
  if 'bloodOf' in mat: result += f"| bloodOf{n} = {','.join(mat['bloodOf'])}\n"
  if 'corpseOf' in mat: result += f"| corpseOf{n} = {','.join(mat['corpseOf'])}\n"
  if 'bodyOf' in mat: result += f"| bodyOf{n} = {','.join(mat['bodyOf'])}\n"
  if 'explodesFrom' in mat: result += f"| explodesFrom{n} = {','.join(mat['explodesFrom'])}\n"
  if 'emittedBy' in mat: result += f"| emittedBy{n} = {','.join(mat['emittedBy'])}\n"
  if 'containedIn' in mat: result += f"| containedIn{n} = {','.join(mat['containedIn'])}\n"
  if 'convertedToBy' in mat: result += f"| convertedToBy{n} = {','.join(mat['convertedToBy'])}\n"

  return result

mats_list = open('matlist.csv', 'wt')
for m in materials.values():
  mats_list.write(f"#{m['wang_color'][2:]},vanilla,material,{m['id']}\n")
mats_list.close()

# Create the wiki text
materials_output_file = open('materials.txt', 'wt')

densities = []

for group in clusters:
  materials_output_file.write('{{Mod infobox material\n')
  
  mats = [materials[m] for m in list(group)]
  mats.sort(key=lambda m: -len(m.get('biomes', '')))

  material_strings = [stringify_material_data(mat, i) for i, mat in enumerate(mats)]

  materials_output_file.write('\n'.join(material_strings))
  materials_output_file.write('}}\n\n')

materials_output_file.close()


density_mats_by_name = {}
for mat in materials.values():
  if not 'density' in mat: continue
  density_mats_by_name.setdefault(mat['name'], []).append(mat['id'])

densities = []
for group in density_mats_by_name.values():
  mats = [materials[m] for m in list(group)]

  if len(mats) > 0:
    last_density = float(mats[0]['density'])
    all_same_density = all(float(mat['density']) == last_density for mat in mats)
    if all_same_density:
      densities.append({ 'name': mats[0]['name'], 'variant': 'All Variants' if len(mats) > 1 else '', 'type': mats[0]['type'], 'cell_type': mats[0]['cell_type'], 'density': last_density })
    else:
      for mat in mats:
        densities.append({ 'name': mat['name'], 'variant': f"<code>{mat['id']}</code>", 'type': mat['type'], 'cell_type': mat['cell_type'], 'density': float(mat['density']) })

densities.sort(key=lambda m: m['density'])

liquid_density_out = open('liquid_density.txt', 'wt')
density_out = open('density.txt', 'wt')
for mat in densities:
  if mat['type'] == 'Liquid':
    liquid_density_out.write(f"|-\n| [[{mat['name']}]] || {mat['variant']} || {mat['density']}\n")
  if mat['cell_type'] != 'solid' and mat['cell_type'] != '':
    density_out.write(f"|-\n| [[{mat['name']}]] || {mat['variant']} || {mat['density']}\n")

liquid_density_out.close()
density_out.close
