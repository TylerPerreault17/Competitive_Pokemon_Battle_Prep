
"""
Pokemon legal move list - Showdown
"""
import pandas as pd
import json
from pathlib import Path
import subprocess
import pickle

hazards = {"stealthrock", "spikes", "toxicspikes", "stickyweb"}
cleric = {"healbell", "aromatherapy"}
set_up = {"swordsdance", "dragondance", "nastyplot", 
          "calmmind","bulkup", "quiverdance", "shellsmash"}
phasing = {"roar", "whirlwind"}
removal = {"defog", "rapidspin"}
recovery = {"recover", "roost", "slackoff", "softboiled",
            "moonlight", "synthesis", "shoreup"}
passive_death_triggers = PASSIVE_DEATH_TRIGGERS = [
    ## weather 
    "sandstorm","hail","snow",
    ## status
    "burn","poison","badly poisoned","afflicted by the curse",
    "perish count fell to 0","nightmare",
    ## hazards
    "spikes","pointed stones","toxic spikes","sticky web",
    ## trap
    "bind","wrap","whirlpool","sand tomb","fire spin",
    "magma storm","infestation","clamp","snap trap",
    ## items
    "flame orb","toxic orb","rocky helmet",
    "sticky barb","black sludge","life orb",
    ## abilities
    "aftermath","dry skin","iron barbs","rough skin",
    "solar power","liquid ooze","gulp missile","bad dreams",
    ## residuals
    "leech seed","salt cure",
    ## self-ko
    "explosion","self-destruct","memento",
    "lunar dance","final gambit","healing wish",
    ## generic 
    "recoil","lost some of its hp"]

global type_order
type_order =[
    "Normal", "Fire", "Water", "Grass", "Electric", "Ice",
    "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug",
    "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"]

## competitive tags 
def move_based_tags(mon, learnsets):
    entry = learnsets.get(mon, {})
    if not isinstance(entry, dict):
        return {
        "hazard_setter": False,
        "cleric": False,
        "setup_sweeper": False,
        "phazer": False,
        "hazard_removal": False,
        "recovery": False }

    learnset = entry.get("learnset", {})
    if not isinstance(learnset, dict):
        learned = set()
    else:
        learned = set(learnset.keys())
    return {
        "hazard_setter": True if learned & hazards else False,
        "cleric": True if learned & cleric else False,
        "setup_sweeper": True if learned & set_up else False,
        "phazer": True if learned & phasing else False,
        "hazard_removal": True if learned & removal else False,
        "recovery": True if learned & recovery else False,
    }
   
## mon strength
def bst_bucket(bst):
    if bst < 400:
        return "Low"
    if bst < 500:
        return "Mid"
    if bst < 600:
        return "High"
    if bst == 600:
        return "Pseudo-Legendary"
    if bst < 700:
        return "Legendary"
    return "Mythical"

## define role type
def classify_role(stats):
    hp, atk, defe, spa, spd, spe = (
        stats["hp"], stats["atk"], stats["def"],
        stats["spa"], stats["spd"], stats["spe"])

    return {
        ## Offensive
        "physical_sweeper": True if atk >= 100 and spe >= 100 else False,
        "special_sweeper": True if spa >= 100 and spe >= 100 else False,
        "mixed_attacker": True if atk >= 90 and spa >= 90 and spe >= 90 else False,
        ## Defensive
        "physical_wall": True if defe >= 100 and hp >= 90 else False,
        "special_wall": True if spd >= 100 and hp >= 90 else False,
        "tank": True if hp >= 100 and (atk >= 100 or spa >= 100) else False,
        ## Pivot
        "pivot": True if spe >= 100 and (defe >= 70 or spd >= 70) else False,
    }

## finds all mon info, puts in dataframe
def get_mon_info():
    rows = [] 
    for mon, data in pokedex.items():
        stats = data.get("baseStats", {})
        
        raw_types = data.get("types", [])
        raw_types = [t if t != "Bird" else "Flying" for t in raw_types]
        
        sorted_types = sorted(raw_types, 
                              key=lambda t: type_order.index(t))
        type1 = sorted_types[0] if len(sorted_types) > 0 else None
        type2 = sorted_types[1] if len(sorted_types) > 1 else None
        
        hp = stats.get("hp", None)
        atk = stats.get("atk", None)
        defe = stats.get("def", None)
        spa = stats.get("spa", None)
        spd = stats.get("spd", None)
        spe =  stats.get("spe", None)
        if None in (hp, atk, defe, spa, spd, spe):
            continue

        
        bst = sum([v for v in 
                   [hp, atk, defe, spa, spd, spe] 
                   if v is not None])
        weight = data.get("weightkg", None)
        role = classify_role({
            "hp": hp, "atk": atk, "def": defe, 
            "spa": spa, "spd": spd, "spe": spe })
        move_tags = move_based_tags(mon, learnsets)
        
        abilities = data.get("abilities", {})
        ability1 = abilities.get("0")
        ability2 = abilities.get("1")
        abilityh = abilities.get("H")
        
        rows.append({
            "dex": data.get("num", None),
            "pokemon": mon.capitalize(),
            "form": data.get("forme", None),
            "type1": type1,
            "type2": type2, 
            "ability1": ability1,
            "ability2": ability2,
            "hidden_ability": abilityh,
            "weight": weight, 
            # Expanded stats
            "hp": hp,
            "atk": atk,
            "def": defe,
            "spa": spa,
            "spd": spd,
            "spe": spe,
            "bst": bst,
            **role,
            **move_tags
        })
    return pd.DataFrame(rows)
    
## get move info + mons legally learn
def get_move_info(move_id):
    
    # Get move data
    move_data = effects.get(move_id, {})
    ## move metadata
    effect = move_data.get("shortDesc", "No effect listed")
    move_type = move_data.get("type", None)
    category = move_data.get("category", None)
    power = move_data.get("basePower", None)
    accuracy = move_data.get("accuracy", None)
    priority = move_data.get("priority", None)
    target = move_data.get("target", None)
    pp = move_data.get("pp",None)

    ## get move flag
    flags_dict = move_data.get("flags", {})
    flags = ", ".join([flag for flag, val in flags_dict.items() if val])
    
    is_contact = "yes" if flags_dict.get("contact",False) else "no"
    
    ## Secondary Effects
    status = None
    status_chance = None
    volatile_status = None
    volatile_chance = None
    target_stat_changes = None
    target_stat_chance = None
    self_stat_changes = None
    self_stat_chance = None
    side_condition = None
    
    ##process single secondary dictonary
    def parse_secondary(sec):
        nonlocal status, status_chance
        nonlocal volatile_status, volatile_chance
        nonlocal target_stat_changes, target_stat_chance

        if "status" in sec:
            status = sec["status"]
            status_chance = sec.get("chance", None)

        if "volatileStatus" in sec:
            volatile_status = sec["volatileStatus"]
            volatile_chance = sec.get("chance", None)

        if "boosts" in sec:
            target_stat_changes = sec["boosts"]
            target_stat_chance = sec.get("chance", None)

    if "secondary" in move_data and move_data["secondary"]:
        parse_secondary(move_data["secondary"])
    if "secondaries" in move_data and move_data["secondaries"]:
        for sec in move_data["secondaries"]:
            parse_secondary(sec)
    if "self" in move_data and move_data["self"]:
        self_stat_changes = move_data["self"].get("boosts", None)
        self_stat_chance = move_data["self"].get("chance", None)
    if "selfBoost" in move_data and move_data["selfBoost"]:
        self_stat_changes = move_data["selfBoost"].get("boosts", None)
        self_stat_chance = move_data["selfBoost"].get("chance", None)
    if "sideCondition" in move_data:
        side_condition = move_data["sideCondition"]
    chance = (status_chance or volatile_chance
        or target_stat_chance or self_stat_chance
        or None)
    # Find Pokémon that learn the move
    learners = []
    for mon, data in learnsets.items():
        learnset = data.get("learnset", {})
        if move_id in learnset:
            learners.append(mon)
    # print(str(learners))
    # Filter NatDex AG legality
    legal_learners = []
    for mon in learners:
        legal_info = formats.get(mon, {})
        is_legal = legal_info.get("natdexag", True)
        if is_legal:
            legal_learners.append(mon)

    return {  
        "effect": effect,
        "type": move_type,
        "category": category,
        "power": power,
        "accuracy": accuracy,
        "pp": pp, 
        "is_contact": is_contact,
        "priority": priority,
        "target": target,
        "flags": flags,
        ##secondary effects
        "status": status,
        "volatile_status": volatile_status,
        "target_stat_changes": target_stat_changes,
        "self_stat_changes": self_stat_changes,
        "side_condition": side_condition,
        "chance": chance,
        "num_learners": len(legal_learners),
        "learners": legal_learners
        }

#tag abilities
def tag_abilities(desc):
    d = desc.lower() if isinstance(desc, str) else ""
    return {
        "immunity": any(x in d for x in [
            "immune", "immunity", "cannot be hit", "negates"]),
        "damage_boost": any(x in d for x in [
            "boosts", "power is increased", "stronger", "raises damage",
            "higher damage", "super effective"]),
        "speed_control": any(x in d for x in [
            "speed", "priority", "faster", "slower"]),
        "weather_synergy": any(x in d for x in [
            "rain", "sun", "hail", "snow", "sand", "weather"]),
        "hazard_control": any(x in d for x in [
            "hazard", "spikes", "stealth rock", "toxic spikes", "sticky web"]),
        "pivoting": any(x in d for x in [
            "switch", "switches out", "pivot"]),
        "stall_tool": any(x in d for x in [
            "heals", "restores", "recovers", "damage reduction", "takes less"]),
        "status_spread": any(x in d for x in [
            "burn", "poison", "paralyze", "sleep", "status"]),
        "passive_damage": any(x in d for x in [
            "damages attackers", "chip damage", "contact damage" ]),
        "item_synergy": any(x in d for x in [
            "item", "berry", "held item"]),
        "rng_modifier": any(x in d for x in [
            "chance", "accuracy", "critical hit", "random"]),
        "niche": any(x in d for x in [
            "sometimes", "rarely", "situational", "gimmick"])}

## competitive category
def categorize_ability(desc):
    d = desc.lower() if isinstance(desc, str) else ""

    if any(x in d for x in ["boosts", "power", "damage", "critical", "attack"]):
        return "Offensive"
    if any(x in d for x in ["immune", "reduces", "less damage", "defense", "resist"]):
        return "Defensive"
    if any(x in d for x in ["switch", "weather", "item", "hazard", "utility"]):
        return "Utility"
    if any(x in d for x in ["status", "burn", "poison", "chip", "contact damage"]):
        return "Status / Passive"
    return "Niche / Conditional"

## abilities info 
def abilities_info():
    rows = []

    for ability_id, data in abilities.items():
        name = data.get("name", ability_id)
        short_desc = data.get("shortDesc", "")
        long_desc = data.get("desc", "")
        full_desc = f"{short_desc} {long_desc}".strip()
        rating = data.get("rating", None)

        # Apply your helper functions
        tags_dict = tag_abilities(full_desc)
        category = categorize_ability(full_desc)

        # Convert tag dict → comma-separated list of active tags
        active_tags = [k for k, v in tags_dict.items() if v]

        rows.append({
            "ability": name,
            "ability_id": ability_id,
            "short_desc": short_desc,
            "long_desc": long_desc,
            "rating": rating,
            "category": category,
            "is_competitive": category != "Niche / Conditional",
            "tags": ", ".join(active_tags) if active_tags else None
            })

    # Convert to DataFrame
    df = pd.DataFrame(rows)
    return df
    
## items info 
def items_info():
    illegal_items = set()
    for item_id, entry in formats.items():
        if item_id in items and "natdexag" in entry:
            nd = entry["natdexag"]
            # Illegal if marked Past or Unobtainable
            if nd.get("isNonstandard") in ("Past", "Unobtainable"):
                illegal_items.add(item_id)
            # Illegal if explicitly tiered as Illegal
            if nd.get("tier") == "Illegal":
                illegal_items.add(item_id)
    legal_items = {
        item_id: data
        for item_id, data in items.items()
        if item_id not in illegal_items
    }
    df = pd.DataFrame.from_dict(legal_items, orient="index")
    df.reset_index(names="item_id", inplace=True)
    return df

    rows = []
    
    for key, data in abilities.items():
        desc = data.get("desc","") or data.get("shortDesc","")
        tags = tag_abilities(desc)
        category = categorize_ability(desc)
        rows.append({
            "ability_key": key,                          # internal ID
            "ability": data.get("name"),                 # display name
            "shortDesc": data.get("shortDesc", None),
            "desc": data.get("desc", None),
            "rating": data.get("rating", None),
            "num": data.get("num", None),
            "gen": data.get("gen", None),
            **tags,
            "category":category
        })
    return pd.DataFrame(rows)

## showdown code to multiplyer for typings
def code_to_multiplier(code):
    if code == 0:
        return 0
    if code == 1:
        return 1
    if code == 2:
        return 2
    if code == 3:
        return 0.5
    return 1

def type_effectiveness(move_type, defender_types):
    move_type = move_type.lower()
    total = 1.0

    for t in defender_types:
        if t is None:
            continue
        t = t.lower()
        damage_taken = type_chart[t]["damageTaken"]
        code = damage_taken.get(move_type.capitalize(), 1)
        total *= code_to_multiplier(code)
        
    return total

## category of text
def cat_text_keys(key, entry):
    fields = entry.keys()
    battle_fields = {"activate", "start", "end", "damage", "block", "fail", "immune"}
    
    ## move description
    if any(f.startswith("descGen") for f in fields):
        category = "move"
    ## item description
    elif any(f.startswith("shortDescGen") for f in fields):
        category = "item"
    ## battle message description
    elif any(f in battle_fields for f in fields):
        category = "battle_message"
    ## stat labels
    elif "statName" in fields:
        category = "stat"
    else:
        category = "other"
    
    return category
    
## user or opponent text
def user_opp(entry):
    text = " ".join(str(v).lower() for v in entry.values())

    user_markers = ["[pokemon]", "[source]", "its "]
    opp_markers = ["[target]", "opposing", "foe"]

    user = any(m in text for m in user_markers)
    opp = any(m in text for m in opp_markers)

    if user and opp:
        return "both"
    if user:
        return "user"
    if opp:
        return "opponent"
    return "other"

## effect of text
def get_effect(category, entry):
    fields = entry.keys()
    text = " ".join(entry.values()).lower()
    ## battle message 
    battle_map = {
        "activate": "activation","start": "start_effect",
        "end": "end_effect","damage": "damage",
        "block": "block_effect","fail": "fail_effect",
        "immune": "immune_effect"}
    
    ## move descript
    if category == "move":
        if "lower" in text:
            return "lower_stat"
        if "raise" in text:
            return "raise_stat"
        if "recover" in text:
            return "heal"
        if "confuse" in text:
            return "confuse"
        if "paraly" in text:
            return "paralyze"
        if "burn" in text:
            return "burn"
        return "move_effect"
    
    ## item descript
    if category == "item":
        if "restore" in text:
            return "heal"
        if "boost" in text:
            return "boost_stat"
        return "item_effect"
    
    for f in fields:
        if f in battle_map:
            return battle_map[f]
    
    ## stat labels
    if "statName" in fields:
        return "stat_label"
    return "misc"

## passive detector 
def is_passive(message: str) -> bool:
    m = message.lower()
    return any(trigger in m for trigger in passive_death_triggers)

## split up text into categories
def split_text(text_dict):
    enriched = []

    for key, entry in text_dict.items():
        category = cat_text_keys(key, entry)
        effect = get_effect(category, entry)
        who = user_opp(entry)

        enriched.append({
            "id": key,
            "category" : category,
            "effect": effect,
            "user_or_opponent": who,
            #"raw": entry
            })
    return enriched

## check for trainer mentions
def mention_trainer(message: str) -> bool:
    return "[trainer]" in message.lower()
def count_trainer(message: str) -> int:
    return message.lower().count("[trainer]")

## check for opponent mon mentions
def mention_opp(message: str) -> bool:
    return "[target]" in message.lower()
def count_opp(message: str) -> int:
    m = message.lower()
    return( m.count("[target]") +
        m.count("opposing") + m.count("foe"))

## check for user mon mentions
def mention_user(message: str) -> bool:
    return "[pokemon]" in message.lower()
def count_user(message: str) -> int:
    m = message.lower()
    return ( m.count("[pokemon]") +
        m.count("[source]") + m.count("its "))
    
def kill_message(message: str) -> bool:
    m = message.lower()
    
    if "fainted" in m:
        return True
    if "one-hit ko" in m or "ohko" in m:
        return True
    self_ko = ["explosion", "self-destruct", "final gambit",
        "memento", "lunar dance", "healing wish"]
    if any(term in m for term in self_ko):
        return True
    return False


## get battle keys - non move
def build_message(text_dict):
    rows = []
    raw = text_dict["default"]
    
    for key, message in raw.items():
        category = "battle_message"
        effect = get_effect(category, {key: message})
        who = user_opp({key: message})
        
        rows.append({
            "message_key": key,
            "effect": effect,
            "user_or_opponent": who,
            "passive_death": is_passive(message),
            "kill_message": kill_message(message),
            "user_mon": mention_user(message),
            "user_count": count_user(message),
            "opp_mon": mention_opp(message),
            "opp_count": count_opp(message),
            "trainer_mon": mention_trainer(message),
            "trainer_count": count_trainer(message),
            #"message_text": message -- breaks excel for some reason?
            })
    return rows

## changes .js file to working file
def safe_url(path: str | Path) -> dict:
    path = Path(path).resolve()

    # If it's already JSON, parse normally
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))

    result = subprocess.run(
        [r"C:\Program Files\nodejs\node.exe",
         r"C:\Users\typer\OneDrive\Documents\Pokemon\extract.js",
         str(path)],
        capture_output=True,
        text=False,
        check=True
    )
    output = result.stdout.decode("utf-8")

    return json.loads(output)

def strip_form(row):
    name = row["pokemon"].lower()
    suffix = row["form_clean"]
    
    if suffix and name.endswith(suffix):
        return row["pokemon"][: -len(suffix)]
    return row["pokemon"]
    
def legal_form(row):
    name = row["monform"]
    form = row["form"]
    if form:
        return (name + " " + form)
    return name
def type_mix(row):
    type1 = row["type1"]
    type2 = row["type2"]
    if type2:
        return (type1 + "-" + type2)
    return type1

def strip_mega(row):
    name = row["pokemon_lower"]
    suffix = row["form_clean"]
    
    if suffix and name.endswith(suffix):
        return row["pokemon_lower"][: -len(suffix)]
    return row["pokemon_lower"]

def merge_move_lists(base, form):
    if pd.isna(base) and pd.isna(form):
        return None
    if pd.isna(base):
        return form
    if pd.isna(form):
        return base

    base_set = set(base.split(", "))
    form_set = set(form.split(", "))

    merged = sorted(base_set | form_set)
    return ", ".join(merged)

##load learnsets
global learnsets, formats, effects, pokedex, abilities, items, type_chart, text
learnsets = safe_url("learnsets.js")['BattleLearnsets']

##load legality
formats = safe_url("formats-data.js")["BattleFormatsData"]

##load move effects 
effects = safe_url("moves.js")['BattleMovedex']

##load pokedex 
pokedex = safe_url("pokedex.js")["BattlePokedex"]
 
abilities = safe_url("abilities.js")["BattleAbilities"]

items = safe_url("items.js")["BattleItems"]
 
type_chart = safe_url("typechart.js")["BattleTypeChart"]
 
text = safe_url("text.js")["BattleText"]

## finds all pokemon
df_all_mons = get_mon_info()

## find all abilities
df_abilities = abilities_info()

##finds all items 
df_items = items_info()

## finds legal moves for the pokemon
move_rows = []
rows = []
for move_id, move_data in effects.items():
    #print(move_id)
    move_name = move_data.get("name", move_id)
    info = get_move_info(move_id)
    #print(info.keys())
    learners = info.get("learners")
    #print(learners)
    if not isinstance(info, dict):
        print("BAD INFO (not dict):", move_name, info)
        continue
    if not learners:
        continue
    for mon in learners:
        rows.append({"pokemon_lower": mon, "move": move_name})
    # Add move name
    info["move"] = move_name

    # Sort and format learners
    info["learners"] = sorted(info["learners"])
    info["learners"] = ", ".join(info["learners"])

    move_rows.append(info)

df_moves = pd.DataFrame(move_rows)
cols = ["move"] + [c for c in df_moves.columns if c != "move"]
df_moves = df_moves[cols]

single_types = [[t, None] for t in type_order]
dual_types = [
    [type_order[i], type_order[j]]
    for i in range(len(type_order))
    for j in range(i+1, len(type_order))
    ]
types = single_types + dual_types
matrix = []


for atk in type_order:
    row = []
    for df in types:
        eff = type_effectiveness(atk, df)
        row.append(eff)
    matrix.append(row)

colnames = colnames = [
    f"{t1}" if t2 is None else f"{t1}-{t2}"
    for (t1, t2) in types]

df_type_chart = pd.DataFrame(matrix, index=type_order, columns=colnames)
df_type_chart = df_type_chart.T

text_cat = split_text(text)
text_categories = pd.DataFrame(text_cat)

message_table = build_message(text)
messages = pd.DataFrame(message_table) 
df_mon_moves = pd.DataFrame(rows)
df_moves_list = (
    df_mon_moves.groupby("pokemon_lower")["move"]
    .apply(lambda x: ", ".join(sorted(x)))
    .reset_index().rename(columns={"move": "moves_learned"}))

df_all_mons = df_all_mons[df_all_mons["form"]!= "Gmax"]
df_all_mons["pokemon_lower"] = df_all_mons["pokemon"].str.lower()

df_all_mons = df_all_mons.merge(
    df_moves_list, on = "pokemon_lower", how="left")

df_all_mons = df_all_mons[df_all_mons["dex"]>0]

df_all_mons["form_clean"] = df_all_mons["form"].str.lower().str.replace(" ", "", regex = False).str.replace("-","", regex=False).str.replace("'","", regex=False)
df_all_mons["pokemon_form"] = df_all_mons.apply(strip_mega, axis = 1)

df_all_mons = df_all_mons.merge(
    df_moves_list.rename(columns = {"pokemon_lower": "pokemon_form", "moves_learned": "moves_learned_form"}),
    on = "pokemon_form", how = "left")
df_all_mons["moves_learned"] = df_all_mons.apply(
    lambda row: merge_move_lists(row["moves_learned"], row["moves_learned_form"]), axis = 1)
df_all_mons = df_all_mons[df_all_mons["moves_learned"].notna()]
df_all_mons["monform"] = df_all_mons.apply(strip_form, axis = 1)
df_all_mons["legal name"] = df_all_mons.apply(legal_form, axis = 1)
df_all_mons["mix"] = df_all_mons.apply(type_mix, axis = 1)
df_all_mon = df_all_mons.drop(columns = ["form_clean", "pokemon_lower", "pokemon_form", "moves_learned_form"])

df_all_mon = df_all_mon.rename(columns = {
    "physical_sweeper": "Physical Sweeper", "special_sweeper":"Special Sweeper", "mixed_attacker":"Mixed Attacker",
    "physical_wall": "Physical Wall", "special_wall": "Special Wall", "tank": "Tank", "pivot":"Pivot",
    "hazard_setter": "Hazard Setter", "cleric": "Cleric", "setup_sweeper": "Setup Sweeper", "phazer": "Phazer", 
    "hazard_removal": "Hazard Removal", "recovery": "Recovery"})
sorted_cols = ["dex","pokemon","legal name","form","monform","type1","type2",
                        "mix","ability1","ability2","hidden_ability","weight","hp","atk",
                        "def","spa","spd","spe","bst","Physical Sweeper","Special Sweeper",
                        "Mixed Attacker","Physical Wall","Special Wall","Tank","Pivot",
                        "Hazard Setter","Cleric","Setup Sweeper","Phazer","Hazard Removal",
                        "Recovery","moves_learned"]
df_all_mon = df_all_mon[sorted_cols]
with pd.ExcelWriter("pokemon_data_view.xlsx") as writer:
    df_all_mon.to_excel(writer, sheet_name="Pokemon", index=False)
    df_moves.to_excel(writer, sheet_name="Moves", index=False)
    df_abilities.to_excel(writer, sheet_name="Abilities", index=False)
    df_items.to_excel(writer, sheet_name="Items", index=False)
    df_type_chart.to_excel(writer, sheet_name="Type Map", index=True)
    #text_categories.to_excel(writer, sheet_name="Text", index=False) 
        ## found not useful - keys do not match replay text
    #messages.to_excel(writer, sheet_name="Battle Messages", index=False)
        ## found not useful - keys do not match replay text 
  