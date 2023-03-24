import xml.etree.ElementTree as ET
import csv
import re
import png
import networkx as nx
import itertools
import glob
from pathlib import Path

import pprint # for debugging

####################################################################
## Parse translations
####################################################################

translations = {}
with open('common.csv', 'r') as f:
  reader = csv.DictReader(f)
  for row in reader:
    translations['$' + row['t']] = row['en']

####################################################################
## Mappings
####################################################################

prop_biomes = {
'altar_torch': {'Mines', 'Snowy Depths'},
'banner': { 'Ancient Laboratory' },
'banner_01': { 'Snowy Wasteland' },
'banner_02': { 'Snowy Wasteland' },
'banner_03': { 'Snowy Wasteland' },
'base_coalmine_structure': {},
'base_music_machine': {},
'boss_arena_statue_1': {'The Laboratory'},
'boss_arena_statue_2': {'The Laboratory'},
'boss_arena_statue_3': {'The Laboratory'},
'boss_arena_statue_4': {'The Laboratory'},
'boss_arena_statues': {'The Laboratory'},
'bridge_spawner': {},
'candle_1': {}, # Used to decorate area where Apparition spawns
'candle_2': {},
'candle_3': {},
'chain_torch': {'Temple of the Art', "Wizards' Den", 'Mountain'},
'chain_torch_blue': {'Pyramid'},
'coalmine_i_structure_01': {'Mines', 'The Tower'},
'coalmine_i_structure_02': {'Mines', 'The Tower'},
'coalmine_large_structure_01': {'Mines', 'Collapsed Mines', 'The Tower'},
'coalmine_large_structure_02': {'Mines', 'Collapsed Mines', 'The Tower'},
'coalmine_structure_01': {'Mines', 'Collapsed Mines', 'The Tower'},
'crystal_green': {'Temple of the Art'},
'crystal_pink': {'Temple of the Art'},
'crystal_red': {'Temple of the Art'},
'dripping_acid_gas': {'Snowy Depths'},
'dripping_oil': {'Power Plant', 'Frozen Vault', 'The Vault'},
'dripping_radioactive': {'Power Plant', 'Frozen Vault', 'The Vault'},
'dripping_water': {'Power Plant', 'Frozen Vault', 'The Vault', 'Mountain'},
'dripping_water_heavy': {'Power Plant', 'Frozen Vault', 'The Vault', 'Mountain'},
'excavationsite_machine_3b': {'Coal Pits'},
'excavationsite_machine_3c': {'Coal Pits'},
'forcefield_generator': {'Hiisi Base'},
'furniture_bed': {'Kammi'},
'furniture_bunk': {'Hiisi Base'},
'furniture_castle_chair': {},
'furniture_castle_divan': {},
'furniture_castle_statue': {},
'furniture_castle_table': {},
'furniture_castle_wardrobe': {},
'furniture_cryopod': {'Hiisi Base'},
'furniture_dresser': {},
'furniture_footlocker': {'Hiisi Base'},
'furniture_locker': {'Hiisi Base'},
'furniture_rocking_chair': {},
'furniture_stool': {'Hiisi Base'},
'furniture_table': {'Hiisi Base'},
'furniture_tombstone_01': {},
'furniture_tombstone_02': {},
'furniture_tombstone_03': {},
'furniture_wardrobe': {},
'furniture_wood_chair': {},
'furniture_wood_table': {'Kammi'},
'ladder_long': {},
'lantern_small': {'Kammi'},
'minecart': {'Mines', 'Collapsed Mines'},
'mountain_left_entrance_grass': {'Mountain'},
'music_machine_00': {},
'music_machine_01': {},
'music_machine_02': {},
'music_machine_03': {},
'physics_barrel_burning': {'Snowy Depths'},
'physics_barrel_oil': {'Mines', 'Collapsed Mine' },
'physics_barrel_radioactive': {'Mines', 'Collapsed Mines'},
'physics_barrel_water': {},
'physics_bed': {},
'physics_bone_01': {},
'physics_bone_02': {},
'physics_bone_03': {},
'physics_bone_04': {},
'physics_bone_05': {},
'physics_bone_06': {},
'physics_bottle_blue': {},
'physics_bottle_green': {},
'physics_bottle_red': {},
'physics_bottle_yellow': {},
'physics_box_explosive': {'Mines', 'Collapsed Mines'},
'physics_box_harmless': {},
'physics_box_harmless_small': {},
'physics_brewing_stand': {'Mines', 'Collapsed Mines'},
'physics_bucket': {},
'physics_campfire': {},
'physics_candle_1': {},
'physics_candle_2': {},
'physics_candle_3': {},
'physics_cart': {'Mines', 'Collapsed Mines'},
'physics_chain_torch': {},
'physics_chain_torch_blue': {},
'physics_chain_torch_ghostly': {},
'physics_chair_1': {},
'physics_chair_2': {},
'physics_chandelier': {},
'physics_crane_tank_spawner': {},
'physics_crate': {},
'physics_darksun_rock': {},
'physics_electricity_source': {},
'physics_fungus': {},
'physics_fungus_acid': {},
'physics_fungus_acid_big': {},
'physics_fungus_acid_huge': {},
'physics_fungus_acid_hugeish': {},
'physics_fungus_acid_small': {},
'physics_fungus_big': {},
'physics_fungus_big_delayed_spawner': {},
'physics_fungus_delayed_spawner': {},
'physics_fungus_huge': {},
'physics_fungus_hugeish': {},
'physics_fungus_small': {},
'physics_fungus_small_delayed_spawner': {},
'physics_fungus_trap': {},
'physics_gem': {},
'physics_glass_shard_01': {},
'physics_glass_shard_02': {},
'physics_glass_shard_03': {},
'physics_glass_shard_04': {},
'physics_grass_01': {},
'physics_grass_02': {},
'physics_hanging_wire': {},
'physics_lantern': {},
'physics_lantern_small': {},
'physics_logo': {},
'physics_logo_1': {},
'physics_logo_2': {},
'physics_logo_3': {},
'physics_minecart': {},
'physics_mining_lamp': {},
'physics_pata': {},
'physics_pressure_tank': {},
'physics_propane_tank': {},
'physics_ragdoll_part': {},
'physics_ragdoll_part_electrified': {},
'physics_ragdoll_part_exploding': {},
'physics_sandbag': {},
'physics_seamine': {},
'physics_skateboard': {},
'physics_skull_01': {},
'physics_skull_02': {},
'physics_skull_03': {},
'physics_statue': {},
'physics_stone_01': {},
'physics_stone_02': {},
'physics_stone_03': {},
'physics_stone_04': {},
'physics_sun_rock': {},
'physics_suspension_bridge_spawner': {},
'physics_table': {},
'physics_temple_rubble_01': {},
'physics_temple_rubble_02': {},
'physics_temple_rubble_03': {},
'physics_temple_rubble_04': {},
'physics_temple_rubble_05': {},
'physics_temple_rubble_06': {},
'physics_templedoor': {},
'physics_templedoor2': {},
'physics_torch_stand': {},
'physics_torch_stand_blue': {},
'physics_torch_stand_intro': {},
'physics_trap_circle_acid': {},
'physics_trap_electricity': {},
'physics_trap_electricity_enabled': {},
'physics_trap_ignite': {},
'physics_trap_ignite_a': {},
'physics_trap_ignite_b': {},
'physics_trap_ignite_enabled': {},
'physics_tubelamp': {},
'physics_vase': {},
'physics_vase_longleg': {},
'physics_wheel': {},
'physics_wheel_small': {},
'physics_wheel_stand_01': {},
'physics_wheel_stand_02': {},
'physics_wheel_stand_03': {},
'physics_wheel_tiny': {},
'pressure_plate': {},
'pumpkin_01': {},
'pumpkin_02': {},
'pumpkin_03': {},
'pumpkin_04': {},
'pumpkin_05': {},
'rainforest_tree_01': {},
'rainforest_tree_02': {},
'rainforest_tree_03': {},
'rainforest_tree_04': {},
'rainforest_tree_05': {},
'rainforest_tree_06': {},
'root_grower': {},
'root_grower_branch': {},
'root_grower_fruit': {},
'root_grower_leaf': {},
'sand_pile_01': {},
'sand_pile_02': {},
'sarcophagus': {},
'sarcophagus_evil': {},
'snow_pile_01': {},
'snow_pile_02': {},
'snowy_rock_01': {},
'snowy_rock_02': {},
'snowy_rock_03': {},
'snowy_rock_04': {},
'snowy_rock_05': {},
'statue': {},
'statue_back': {},
'statue_rock_01': {},
'statue_rock_02': {},
'statue_rock_03': {},
'statue_rock_04': {},
'statue_rock_05': {},
'statue_rock_06': {},
'statue_rock_07': {},
'statue_rock_08': {},
'statue_rock_09': {},
'statue_rock_10': {},
'statue_rock_11': {},
'statue_rock_12': {},
'stonepile': {},
'suspended_container': {},
'suspended_seamine': {},
'suspended_tank_acid': {},
'suspended_tank_radioactive': {},
'temple_lantern': {},
'temple_pressure_plate': {},
'temple_statue_01': {},
'temple_statue_01_green': {},
'temple_statue_02': {},
'trap_circle_acid': {},
'trap_electricity': {},
'trap_electricity_enabled': {},
'trap_electricity_suspended': {},
'trap_ignite': {},
'trap_ignite_enabled': {},
'trap_laser': {},
'trap_laser_enabled': {},
'trap_laser_enabled_left': {},
'trap_laser_toggling': {},
'trap_laser_toggling_left': {},
'vault_apparatus_01': {},
'vault_apparatus_02': {},
'vault_machine_1': {},
'vault_machine_2': {},
'vault_machine_3': {},
'vault_machine_4': {},
'vault_machine_5': {},
'vault_machine_6': {},
'winter_prop_spawner': {},
'winter_ruins_spawner': {},
}


####################################################################
## Process props
####################################################################

props = {}

def parse_PhysicsImageShapeComponent(prop, child):
  attr = child.attrib
  id = attr.get('body_id', '0')

  component = prop.setdefault('components', {}).setdefault(id, {})
  if 'material' in attr: component['material'] = attr['material']
  if 'image_file' in attr: component['image'] = attr['image_file']


def parse_PhysicsBodyComponent(prop, child):
  attr = child.attrib
  id = attr.get('uid', '0')

  component = prop.setdefault('components', {}).setdefault(id, {})
  component['is_static'] = attr.get('is_static', '0')
  component['buoyancy'] = attr.get('buoyancy', '0.7')
  component['fixed_rotation'] = attr.get('fixed_rotation', '0')
  component['fixed_rotation'] = attr.get('fixed_rotation', '0')


def parse_ParticleEmitterComponent(prop, child):
  attr = child.attrib

  if attr.get('emit_cosmetic_particles', '0') == '0' and 'emitted_material_name' in attr:
    mats = prop.setdefault('emits_materials', set())
    mats.add(attr['emitted_material_name'])


def parse_LifetimeComponent(prop, child):
  attr = child.attrib
  if attr.get('lifetime', '-1') != '-1':
    prop['lifetime'] = attr['lifetime']


def parse_ExplodeOnDamageComponent(prop, child):
  attr = child.attrib
  conf = child.find('config_explosion').attrib
  
  prop['explosion_chance_on_death'] = attr.get('explode_on_death_percent', '1')
  prop['explosion_chance_on_damage'] = attr.get('explode_on_damage_percent', '1')
  prop['explosion_chance_on_movement'] = attr.get('physics_body_modified_death_probability', '0')
  prop['explosion_on_body_loss'] = attr.get('physics_body_destruction_required', '0.5')

  prop['explosion_radius'] = conf.get('explosion_radius', '20')
  prop['explosion_damage'] = conf.get('damage', '5')
  if 'load_this_entity' in conf: prop['explosion_entity_loaded'] = conf['load_this_entity']
  if 'electricity_count' in conf: prop['explosion_electricity_amount'] = conf['electricity_count']
  prop['explosion_knockback_force'] = conf.get('knockback_force', '1')
  if 'material_sparks_real' in conf and 'spark_material' in conf: prop.setdefault('explosion_spark_material', set()).add(conf['spark_material'])
  if 'material_sparks_enabled' in conf: prop.setdefault('material_sparks_enabled', set()).add('fire')


def parse_DamageModelComponent(prop, child):
  attr = child.attrib
  
  prop['hp'] = attr.get('hp', '1')
  prop['resists_critical_damage'] = attr.get('critical_damage_resistance', '0')
  prop['fall_damage'] = attr.get('falling_damages', '1')
  if 'materials_that_damage' in attr:
    mats = list(attr['materials_that_damage'].split(','))
    damages = ['0.1'] * len(mats)
    if 'materials_how_much_damage' in attr:
      damages = list(attr['materials_how_much_damage'].split(','))

    prop['damaged_by_materials'] = dict(zip(mats, damages))

  prop['ragdoll_material'] = attr.get('ragdoll_material', 'meat')
  prop['blood_material'] = attr.get('blood_material', 'blood_fading')
  if 'blood_spray_material' in attr: prop['blood_spray_material'] = attr['blood_spray_material']
  prop['blood_multiplier'] = attr.get('blood_multiplier', '1')
  prop['chance_of_catching_fire'] = attr.get('fire_probability_of_ignition', '0.5')
  prop['damage_received_from_fire'] = attr.get('fire_damage_amount', '0.2')

  for damage_multipliers in child.find('damage_multipliers') or []:
    prop['damage_multipliers'] = damage_multipliers.attrib


def parse_MagicConvertMaterialComponent(prop, child):
  attr = child.attrib

  prop['material_convert_radius'] = attr.get('radius', 256)

  from_mats = attr.get('from_material_array', [])
  to_mats = attr.get('to_material_array', [])

  conversions = list(zip(from_mats, to_mats))

  if 'from_material_tag' in attr:
    conversions.append((attr['from_material_tag'], attr['to_material']))

  if 'from_material' in attr:
    conversions.append((attr['from_material'], attr['to_material']))

  if 'from_any_material' in attr:
    conversions.append(('[any]', attr['to_material']))

  if 'extinguish_fire' in attr: prop['extinguishes_fire'] = attr['extinguish_fire']

  prop['material_conversions'] = conversions


def parse_MaterialInventoryComponent(prop, child):
  attr = child.attrib

  prop['leaks_on_damage_percent'] = attr.get('leak_on_damage_percent', '0')
  
  inventory = {}
  for mat in child.findall('count_per_material_type/Material'):
    inventory[mat.attrib['material']] = mat.attrib['count']

  prop['material_inventory'] = inventory


def parse_PixelSpriteComponent(prop, child):
  prop['material'] = child.attrib.get('material', 'wood_loose')


tag_fns = {
  'PhysicsImageShapeComponent': parse_PhysicsImageShapeComponent,
  'PhysicsBodyComponent': parse_PhysicsBodyComponent,
  'ParticleEmitterComponent': parse_ParticleEmitterComponent,
  'LifetimeComponent': parse_LifetimeComponent,
  'ExplodeOnDamageComponent': parse_ExplodeOnDamageComponent,
  'DamageModelComponent': parse_DamageModelComponent,
  'MagicConvertMaterialComponent': parse_MagicConvertMaterialComponent,
  'MaterialInventoryComponent': parse_MaterialInventoryComponent,
  'PixelSpriteComponent': parse_PixelSpriteComponent,
}

def parse_tags(prop, root):
  for tagname, fn in tag_fns.items():
    for child in root.findall(tagname):
      fn(prop, child)


def process_prop_xml(filename):
  tree = ET.parse(filename)
  root = tree.getroot()

  name = Path(filename).resolve().stem
  prop = {}

  for child in root.findall('Base'):
    prop['base'] = child.attrib['file']
    parse_tags(prop, child)

  parse_tags(prop, root)
  props[name] = prop


for filename in glob.glob("./entities/vegetation/**/*.xml", recursive=True):
  process_prop_xml(filename)

print(f'{len(props)} PROPS FOUND')
pprint.pprint(props)

